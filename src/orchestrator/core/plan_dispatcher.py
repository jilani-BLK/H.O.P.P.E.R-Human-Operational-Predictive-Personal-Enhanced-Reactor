"""
Plan-Based Dispatcher - Architecture JSON-First

Dispatcher qui génère des plans structurés via LLM et les exécute via PluginRegistry.
Remplace le dispatching basé regex par une approche déclarative.

Architecture:
User → LLM (Plan JSON) → Validation → Execution → Narration → Response
"""

import json
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime

from core.plan_schema import (
    ExecutionPlan,
    ToolCall,
    Narration,
    IntentType,
    RiskLevel,
    PlanValidationResult,
    PlanExecutionResult
)
from core.plugin_registry import PluginRegistry
from core.context_manager import ContextManager
from security.credentials_vault import CredentialsVault
from core.service_registry import ServiceRegistry
from core.tool_interface import ToolExecutionContext


class PlanBasedDispatcher:
    """
    Dispatcher centré plan JSON structuré
    
    Remplace l'ancien dispatcher regex par:
    1. Génération plan JSON via LLM
    2. Validation tools/capabilities
    3. Exécution séquentielle via PluginRegistry
    4. Narration enrichie des résultats
    """
    
    def __init__(
        self,
        service_registry: ServiceRegistry,
        plugin_registry: PluginRegistry,
        credentials_vault: CredentialsVault,
        context_manager: ContextManager,
        llm_service_url: str = "http://localhost:5001"
    ):
        self.service_registry = service_registry
        self.plugin_registry = plugin_registry
        self.vault = credentials_vault
        self.context_manager = context_manager
        
        # LLMActionNarrator pour narrations dynamiques (lazy import)
        self.narrator = None
        self.llm_service_url = llm_service_url
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from communication.llm_action_narrator import LLMActionNarrator
            self.narrator = LLMActionNarrator(llm_service_url=llm_service_url)
            logger.info("✅ LLMActionNarrator initialisé")
        except Exception as e:
            logger.warning(f"⚠️ Narrations statiques (LLMActionNarrator indisponible): {e}")
        
        self.stats = {
            "total_requests": 0,
            "successful_plans": 0,
            "failed_validations": 0,
            "execution_errors": 0
        }
        
        logger.info("✅ PlanBasedDispatcher initialisé")
    
    
    async def dispatch(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Point d'entrée principal du dispatcher
        
        Flow:
        1. generate_plan() → Plan JSON via LLM
        2. validate_plan() → Vérifications
        3. execute_plan() → Exécution tools
        4. format_response() → Message final
        
        Returns:
            {
                "message": "Réponse utilisateur",
                "data": {...},
                "actions": ["intent", "tool_x"],
                "plan": ExecutionPlan,
                "execution": PlanExecutionResult
            }
        """
        
        self.stats["total_requests"] += 1
        
        logger.info(f"🔄 Dispatch: '{text[:60]}...'")
        
        try:
            # 1. Générer plan
            plan = await self.generate_plan(text, user_id, context)
            
            if not plan:
                logger.error("❌ Échec génération plan")
                return {
                    "message": "Je n'ai pas pu comprendre votre demande",
                    "data": None,
                    "actions": ["error"]
                }
            
            logger.info(f"📋 Plan: {plan.intent} | {len(plan.tool_calls)} tools | conf={plan.confidence:.2f}")
            
            # 2. Valider
            validation = await self.validate_plan(plan)
            
            if not validation.is_valid:
                self.stats["failed_validations"] += 1
                logger.error(f"❌ Validation: {validation.errors}")
                return {
                    "message": f"Je ne peux pas faire ça: {validation.errors[0] if validation.errors else 'erreur inconnue'}",
                    "data": {"validation": validation.dict()},
                    "actions": ["validation_failed"]
                }
            
            # 3. Exécuter
            execution = await self.execute_plan(plan, user_id)
            
            if execution.success:
                self.stats["successful_plans"] += 1
            else:
                self.stats["execution_errors"] += 1
            
            # 4. Formater réponse
            response = await self.format_response(plan, execution)
            
            # 5. Sauvegarder historique
            self.context_manager.add_to_history(user_id, text, response["message"])
            
            logger.success(f"✅ Dispatch terminé ({execution.execution_time_seconds:.2f}s)")
            
            return response
        
        except Exception as e:
            logger.error(f"❌ Erreur dispatch: {e}", exc_info=True)
            return {
                "message": f"Erreur: {str(e)}",
                "data": None,
                "actions": ["error"]
            }
    
    
    async def generate_plan(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[ExecutionPlan]:
        """
        Génère ExecutionPlan via LLM
        
        Le LLM reçoit:
        - Liste des tools disponibles (PluginRegistry)
        - Historique conversationnel
        - Schéma JSON ExecutionPlan
        
        Returns:
            ExecutionPlan parsé ou None
        """
        
        logger.info("🤖 Génération plan...")
        
        try:
            # Tools disponibles
            tools = self.plugin_registry.get_capabilities_for_llm()
            
            # Historique
            history = self.context_manager.get_history_for_prompt(user_id, max_exchanges=3)
            
            # Prompt
            system_prompt = self._build_system_prompt(tools)
            user_prompt = self._build_user_prompt(text, history)
            
            # LLM call
            result = await self.service_registry.call_service(
                "llm",
                "/generate",
                method="POST",
                data={
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "temperature": 0.1,
                    "max_tokens": 1500
                },
                timeout=30  # Augmenté pour LLM locales plus lentes
            )
            
            # Parser
            response_text = result.get("text", "").strip()
            
            # Nettoyer markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                parts = response_text.split("```")
                if len(parts) >= 2:
                    response_text = parts[1]
            
            response_text = response_text.strip()
            
            # Parse JSON
            plan_data = json.loads(response_text)
            
            # Ajouter métadonnées
            plan_data["user_id"] = user_id
            plan_data["original_query"] = text
            plan_data["created_at"] = datetime.now()
            
            # Créer plan
            plan = ExecutionPlan(**plan_data)
            
            logger.success(f"✅ Plan parsé: {plan.intent}")
            
            return plan
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON error: {e}")
            logger.debug(f"Response: {response_text[:500]}")
            return None
        
        except Exception as e:
            logger.error(f"❌ Erreur: {e}", exc_info=True)
            return None
    
    
    def _build_system_prompt(self, tools: Dict[str, Any]) -> str:
        """Construit prompt système"""
        
        tools_section = "## Tools Disponibles\n\n"
        
        for tool_id, caps in tools.items():
            tools_section += f"### {tool_id}\n"
            for cap in caps:
                tools_section += f"- {cap['name']} ({cap['risk']}): {cap['description']}\n"
        
        return f"""Tu es HOPPER, un assistant IA personnel avec une vraie personnalité.

{tools_section}

## Instructions CRITIQUES:

1. Si la demande nécessite un outil (fichiers, système, etc.): génère "tool_calls"
2. Si c'est une conversation simple (bonjour, question générale, etc.): 
   - Mets "tool_calls": []
   - SURTOUT: dans "narration.message", écris ta VRAIE RÉPONSE conversationnelle
   - Exemple: "Bonjour ! Je suis HOPPER, ravi de t'aider aujourd'hui !"
   - Sois naturel, amical et personnalisé

## Format JSON REQUIS (respecte EXACTEMENT):

{{
  "intent": "question|system_action|email|calendar|control|search|general",
  "confidence": 0.95,
  "tool_calls": [
    {{
      "tool_id": "filesystem",
      "capability": "list_directory", 
      "parameters": {{"directory": "/path"}},
      "reasoning": "Explique pourquoi",
      "risk_level": "safe"
    }}
  ],
  "narration": {{
    "message": "VRAIE réponse conversationnelle ici (pas 'Commande exécutée')",
    "tone": "neutral",
    "should_speak": true,
    "urgency": "normal"
  }},
  "reasoning": "Analyse globale du plan"
}}

## RÈGLES CRITIQUES:
- risk_level doit être: "safe", "low", "medium", "high" ou "critical" (JAMAIS "none")
- intent parmi: question, system_action, email, calendar, control, search, general
- tone parmi: neutral, friendly, formal, urgent, playful
- urgency parmi: low, normal, high, critical
- tool_calls peut être vide [] pour questions simples
- parameters doit contenir les champs requis par la capability

Réponds UNIQUEMENT en JSON valide, sans texte avant/après."""
    
    
    def _build_user_prompt(self, text: str, history: list) -> str:
        """Prompt utilisateur"""
        
        parts = []
        
        if history:
            parts.append("Historique:")
            for ex in history[-2:]:
                parts.append(f"U: {ex.get('user', '')}")
                parts.append(f"A: {ex.get('assistant', '')}")
        
        parts.append(f'\nCommande: "{text}"\n\nPlan JSON:')
        
        return "\n".join(parts)
    
    
    async def validate_plan(self, plan: ExecutionPlan) -> PlanValidationResult:
        """Valide le plan"""
        
        result = PlanValidationResult(is_valid=True)
        
        for call in plan.tool_calls:
            tool = self.plugin_registry.get_tool(call.tool_id)
            
            if not tool:
                result.is_valid = False
                result.missing_tools.append(call.tool_id)
                result.errors.append(f"Tool inconnu: {call.tool_id}")
                continue
            
            cap = next(
                (c for c in tool.manifest.capabilities if c.name == call.capability),
                None
            )
            
            if not cap:
                result.is_valid = False
                result.errors.append(f"Capability inconnue: {call.capability}")
        
        return result
    
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        user_id: str
    ) -> PlanExecutionResult:
        """Exécute le plan"""
        
        logger.info(f"⚙️ Exécution ({len(plan.tool_calls)} actions)...")
        
        result = PlanExecutionResult(
            success=True,
            plan=plan,
            started_at=datetime.now()
        )
        
        for i, call in enumerate(plan.tool_calls):
            logger.info(f"[{i+1}/{len(plan.tool_calls)}] {call.tool_id}.{call.capability}")
            
            try:
                tool = self.plugin_registry.get_tool(call.tool_id)
                
                # Connexion
                if not tool.is_connected():
                    creds = await self.vault.get_credentials(call.tool_id, user_id)
                    if creds:
                        await tool.connect(creds)
                
                # Contexte
                context = ToolExecutionContext(
                    user_id=user_id,
                    execution_id=f"exec_{datetime.now().timestamp()}",
                    source="plan_dispatcher"
                )
                
                # Invoquer
                tool_result = await tool.invoke(
                    capability_name=call.capability,
                    parameters=call.parameters,
                    context=context
                )
                
                result.tool_results.append({
                    "tool_id": call.tool_id,
                    "capability": call.capability,
                    "success": tool_result.success,
                    "data": tool_result.data,
                    "error": tool_result.error
                })
                
                if not tool_result.success:
                    result.success = False
                    result.errors.append(f"{call.capability}: {tool_result.error}")
                    break
            
            except Exception as e:
                result.success = False
                result.errors.append(str(e))
                break
        
        result.mark_completed()
        
        return result
    
    
    async def format_response(
        self,
        plan: ExecutionPlan,
        execution: PlanExecutionResult
    ) -> Dict[str, Any]:
        """Formatte la réponse finale avec narration LLM"""
        
        # Générer narration via LLM si disponible
        if self.narrator:
            try:
                # Préparer contexte pour narration
                if execution.success and execution.tool_results:
                    # Narration de succès
                    message = await self.narrator.generate_narration(
                        action_type=plan.intent.value,
                        action_details={
                            "tool_id": plan.tool_calls[0].tool_id if plan.tool_calls else "",
                            "capability": plan.tool_calls[0].capability if plan.tool_calls else "",
                            "parameters": plan.tool_calls[0].parameters if plan.tool_calls else {},
                            "reasoning": plan.tool_calls[0].reasoning if plan.tool_calls else ""
                        },
                        execution_result={
                            "success": True,
                            "data": execution.tool_results[-1].get("data") if execution.tool_results else None
                        },
                        tone=plan.narration.tone
                    )
                elif not execution.success:
                    # Narration d'erreur
                    error_msg = execution.errors[0] if execution.errors else "erreur inconnue"
                    message = await self.narrator.generate_error_message(
                        error=error_msg,
                        context={
                            "intent": plan.intent.value,
                            "tool": plan.tool_calls[0].tool_id if plan.tool_calls else None
                        },
                        tone="empathetic"
                    )
                else:
                    # Question simple sans tools
                    message = plan.narration.message
                    logger.info(f"💬 Message du plan: '{message}'")
                
                logger.debug(f"Narration LLM: {message}")
            
            except Exception as e:
                logger.error(f"Erreur génération narration: {e}")
                # Fallback sur narration du plan
                message = plan.narration.message
        else:
            # Pas de narrator - fallback sur narration statique du plan
            message = plan.narration.message
            
            # Enrichissement basique
            if execution.success and execution.tool_results:
                last = execution.tool_results[-1]
                if last.get("data"):
                    data = last["data"]
                    if "total" in data:
                        message += f" — {data['total']} résultats"
            elif not execution.success:
                message = f"❌ Échec: {execution.errors[0] if execution.errors else 'erreur inconnue'}"
        
        return {
            "message": message,
            "data": {
                "plan": plan.dict(),
                "execution": {
                    "success": execution.success,
                    "results": execution.tool_results,
                    "time": execution.execution_time_seconds
                }
            },
            "actions": [plan.intent.value] + [
                f"tool_{r['tool_id']}" for r in execution.tool_results if r.get("success")
            ]
        }
