"""
LlmAgent - Pipeline ReAct complet
Thought → Act → Observe → Answer avec planification via LLM
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
import aiohttp

from core.models import (
    SystemPlan,
    ToolCall,
    ToolSummary,
    ToolStatus,
    RiskLevel,
    LlmPlanSchema
)
from core.prompt_assembler import PromptAssembler


class LlmAgent:
    """
    Agent LLM avec pipeline ReAct complet
    Génère des plans d'action structurés et gère l'exécution
    """
    
    def __init__(
        self,
        llm_service_url: str,
        prompt_assembler: PromptAssembler,
        tool_executor=None,
        permission_manager=None
    ):
        self.llm_service_url = llm_service_url
        self.prompt_assembler = prompt_assembler
        self.tool_executor = tool_executor
        self.permission_manager = permission_manager
        
        # Configuration LLM
        self.default_params = {
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "stop": ["</s>", "USER:", "ASSISTANT:"]
        }
    
    async def process(
        self,
        user_input: str,
        user_id: str = "default",
        session_id: str = ""
    ) -> Dict[str, Any]:
        """
        Pipeline ReAct complet:
        1. THOUGHT: Assembler prompt avec contexte
        2. ACT: LLM génère SystemPlan
        3. OBSERVE: Exécuter les tools et collecter résultats
        4. ANSWER: Reformuler avec les résultats
        
        Args:
            user_input: Entrée utilisateur
            user_id: ID utilisateur
            session_id: ID session
            
        Returns:
            Réponse structurée avec plan et résultats
        """
        
        logger.info(f"🧠 ReAct Pipeline - Input: '{user_input[:50]}...'")
        
        try:
            # ==================== THOUGHT ====================
            logger.debug("Step 1: THOUGHT - Assemblage contexte")
            prompt_data = self.prompt_assembler.assemble_prompt(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id
            )
            
            # ==================== ACT (Plan) ====================
            logger.debug("Step 2: ACT - Génération plan LLM")
            system_plan = await self._generate_plan(prompt_data)
            
            if not system_plan:
                # Fallback si échec LLM
                return self.prompt_assembler.create_fallback_response(
                    error="LLM génération failed",
                    user_input=user_input
                )
            
            # ==================== OBSERVE (Execute) ====================
            logger.debug(f"Step 3: OBSERVE - Exécution {len(system_plan.tools)} outils")
            tool_summary = await self._execute_tools(
                system_plan.tools,
                user_id=user_id,
                session_id=session_id
            )
            
            # ==================== ANSWER (Reformulate) ====================
            logger.debug("Step 4: ANSWER - Reformulation avec résultats")
            final_response = await self._reformulate_with_results(
                original_input=user_input,
                system_plan=system_plan,
                tool_summary=tool_summary,
                user_id=user_id
            )
            
            logger.success(f"✅ ReAct Pipeline completed - {tool_summary.tools_executed} outils exécutés")
            
            return final_response
            
        except Exception as e:
            logger.error(f"❌ ReAct Pipeline error: {e}")
            return self.prompt_assembler.create_fallback_response(
                error=str(e),
                user_input=user_input
            )
    
    async def _generate_plan(
        self,
        prompt_data: Dict[str, Any]
    ) -> Optional[SystemPlan]:
        """
        Génère un SystemPlan via LLM (function calling)
        
        Args:
            prompt_data: Données assemblées par PromptAssembler
            
        Returns:
            SystemPlan ou None si échec
        """
        
        try:
            # Construire le prompt complet
            full_prompt = self._build_full_prompt(prompt_data)
            
            # Appel au service LLM
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_service_url}/generate",
                    json={
                        "prompt": full_prompt,
                        **self.default_params,
                        "response_format": "json"  # Demander JSON structuré
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.error(f"LLM service error: {response.status}")
                        return None
                    
                    result = await response.json()
                    llm_text = result.get('text', '')
                    
                    # Parser la réponse JSON du LLM
                    return self._parse_llm_response(llm_text)
        
        except asyncio.TimeoutError:
            logger.error("LLM timeout")
            return None
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None
    
    def _build_full_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Construit le prompt complet pour le LLM"""
        
        parts = []
        
        # System prompt
        parts.append(prompt_data['system_prompt'])
        parts.append("\n=== CONVERSATION ===")
        
        # Messages historiques
        for msg in prompt_data['messages']:
            role = msg['role'].upper()
            content = msg['content']
            parts.append(f"{role}: {content}")
        
        # Instruction finale
        parts.append("\nASSISTANT: ")
        
        return "\n".join(parts)
    
    def _parse_llm_response(self, llm_text: str) -> Optional[SystemPlan]:
        """
        Parse la réponse JSON du LLM en SystemPlan
        
        Args:
            llm_text: Texte brut du LLM
            
        Returns:
            SystemPlan validé ou None
        """
        
        try:
            # Extraire JSON (le LLM peut ajouter du texte avant/après)
            json_start = llm_text.find('{')
            
            if json_start == -1:
                logger.warning("Pas de JSON trouvé dans réponse LLM")
                return None
            
            # Parser de manière progressive pour gérer les multi-objets
            decoder = json.JSONDecoder()
            json_str = llm_text[json_start:]
            llm_data, idx = decoder.raw_decode(json_str)
            
            # Log si du texte supplémentaire existe
            remaining = json_str[idx:].strip()
            if remaining:
                logger.debug(f"Texte ignoré après JSON: {remaining[:100]}...")
            
            # Valider avec Pydantic
            plan_schema = LlmPlanSchema(**llm_data)
            
            # Convertir en SystemPlan
            system_plan = self._schema_to_system_plan(plan_schema)
            
            logger.debug(f"✅ Plan parsé: intent={system_plan.intent}, {len(system_plan.tools)} outils")
            
            return system_plan
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"LLM text: {llm_text[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Plan parsing error: {e}")
            return None
    
    def _schema_to_system_plan(self, schema: LlmPlanSchema) -> SystemPlan:
        """Convertit LlmPlanSchema en SystemPlan"""
        
        # Convertir actions en ToolCalls
        tool_calls = []
        for action in schema.actions:
            tool_call = ToolCall(
                tool_name=action.get('tool', 'unknown'),
                action=action.get('action', 'unknown'),
                parameters=action.get('params', {}),
                risk_level=self._assess_risk_level(action),
                narration=action.get('narration')
            )
            tool_calls.append(tool_call)
        
        return SystemPlan(
            intent=schema.intent,
            confidence=schema.confidence,
            tools=tool_calls,
            user_message=schema.response,
            reasoning=schema.reasoning,
            requires_more_info=schema.needs_more_info,
            suggested_followup=schema.followup_question
        )
    
    def _assess_risk_level(self, action: Dict[str, Any]) -> RiskLevel:
        """Évalue le niveau de risque d'une action"""
        
        tool = action.get('tool', '')
        action_type = action.get('action', '')
        
        # Règles heuristiques
        if 'delete' in action_type or 'remove' in action_type:
            return RiskLevel.MEDIUM
        
        if 'execute_command' in action_type or 'sudo' in str(action.get('params', {})):
            return RiskLevel.HIGH
        
        if tool in ['llm_knowledge', 'tts']:
            return RiskLevel.SAFE
        
        if 'email' in tool and 'send' in action_type:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    async def _execute_tools(
        self,
        tools: List[ToolCall],
        user_id: str,
        session_id: str
    ) -> ToolSummary:
        """
        Exécute séquentiellement les tools avec vérification permissions
        
        Args:
            tools: Liste de ToolCall à exécuter
            user_id: ID utilisateur
            session_id: ID session
            
        Returns:
            ToolSummary avec résultats
        """
        
        summary = ToolSummary(
            tools_executed=0,
            tools_succeeded=0,
            tools_failed=0
        )
        
        for tool_call in tools:
            logger.debug(f"Exécution: {tool_call.tool_name}.{tool_call.action}")
            
            try:
                # Vérifier permissions
                if self.permission_manager:
                    allowed = await self._check_permissions(
                        tool_call=tool_call,
                        user_id=user_id
                    )
                    
                    if not allowed:
                        tool_call.status = ToolStatus.BLOCKED
                        tool_call.error = "Permission refusée"
                        summary.add_tool_result(tool_call)
                        logger.warning(f"❌ {tool_call.tool_name}.{tool_call.action} - Permission refusée")
                        continue
                
                # Exécuter l'outil
                if self.tool_executor:
                    result = await self.tool_executor.execute(tool_call)
                    
                    tool_call.status = ToolStatus.SUCCESS if result.get('success') else ToolStatus.FAILED
                    tool_call.result = result
                    tool_call.error = result.get('error')
                else:
                    # Simulation si pas d'executor
                    tool_call.status = ToolStatus.SUCCESS
                    tool_call.result = {"simulated": True}
                
                summary.add_tool_result(tool_call)
                
                logger.debug(f"✅ {tool_call.tool_name}.{tool_call.action} - {tool_call.status}")
                
            except Exception as e:
                tool_call.status = ToolStatus.FAILED
                tool_call.error = str(e)
                summary.add_tool_result(tool_call)
                logger.error(f"❌ {tool_call.tool_name}.{tool_call.action} - {e}")
        
        return summary
    
    async def _check_permissions(
        self,
        tool_call: ToolCall,
        user_id: str
    ) -> bool:
        """
        Vérifie les permissions pour un tool call
        
        Args:
            tool_call: Tool à vérifier
            user_id: ID utilisateur
            
        Returns:
            True si autorisé
        """
        
        try:
            # Demander au permission_manager
            result = await self.permission_manager.check(
                user_id=user_id,
                tool_name=tool_call.tool_name,
                action=tool_call.action,
                risk_level=tool_call.risk_level
            )
            
            return result.get('allowed', False)
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            # Fail-safe: refuser par défaut
            return False
    
    async def _reformulate_with_results(
        self,
        original_input: str,
        system_plan: SystemPlan,
        tool_summary: ToolSummary,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Reformule la réponse finale avec les résultats des outils (ReAct Answer)
        
        Args:
            original_input: Entrée utilisateur originale
            system_plan: Plan initial
            tool_summary: Résultats exécution
            user_id: ID utilisateur
            
        Returns:
            Réponse finale structurée
        """
        
        # Si aucun outil exécuté, retourner le message original du plan
        if tool_summary.tools_executed == 0:
            return {
                "success": True,
                "message": system_plan.user_message,
                "data": {
                    "intent": system_plan.intent,
                    "confidence": system_plan.confidence
                },
                "actions_taken": []
            }
        
        # Créer un prompt de reformulation avec observations
        replan_prompt = self.prompt_assembler.create_replan_prompt(
            original_input=original_input,
            tool_summary=tool_summary,
            user_id=user_id
        )
        
        # Générer réponse finale
        final_plan = await self._generate_plan(replan_prompt)
        
        if final_plan:
            final_message = final_plan.user_message
        else:
            # Fallback: construire message manuel
            final_message = self._build_fallback_message(system_plan, tool_summary)
        
        return {
            "success": tool_summary.tools_failed == 0,
            "message": final_message,
            "data": {
                "intent": system_plan.intent,
                "confidence": system_plan.confidence,
                "tools_executed": tool_summary.tools_executed,
                "tools_succeeded": tool_summary.tools_succeeded,
                "tools_failed": tool_summary.tools_failed,
                "results": tool_summary.results,
                "errors": tool_summary.errors
            },
            "actions_taken": [
                f"{t.tool_name}.{t.action}" for t in system_plan.tools
            ]
        }
    
    def _build_fallback_message(
        self,
        plan: SystemPlan,
        summary: ToolSummary
    ) -> str:
        """Construit un message de fallback si reformulation échoue"""
        
        if summary.tools_succeeded == summary.tools_executed:
            return f"✅ J'ai exécuté {summary.tools_executed} action(s) avec succès."
        
        elif summary.tools_failed == summary.tools_executed:
            return f"❌ Les {summary.tools_failed} action(s) ont échoué: {', '.join(summary.errors)}"
        
        else:
            return f"⚠️ {summary.tools_succeeded}/{summary.tools_executed} actions réussies. Erreurs: {', '.join(summary.errors)}"


# ==================== EXPORT ====================

__all__ = ['LlmAgent']
