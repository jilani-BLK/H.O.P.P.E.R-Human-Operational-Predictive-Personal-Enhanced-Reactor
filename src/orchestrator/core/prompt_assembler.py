"""
PromptAssembler - Injection contextuelle complète pour LLM
Assemble dynamiquement: historique, RAG, permissions, audit, état
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from core.models import (
    PromptContext,
    ToolCall,
    ToolSummary,
    RiskLevel,
    ConsentMode,
    LlmPlanSchema
)
from core.context_manager import ContextManager


class PromptAssembler:
    """
    Assembleur de prompts avec injection contextuelle complète
    Remplace l'ancien PromptBuilder avec approche LLM-first
    """
    
    def __init__(
        self,
        context_manager: ContextManager,
        knowledge_base=None,  # FAISS/Chroma
        consent_manager=None,
        audit_store=None
    ):
        self.context_manager = context_manager
        self.knowledge_base = knowledge_base
        self.consent_manager = consent_manager
        self.audit_store = audit_store
        
        # System prompt de base
        self.base_system_prompt = self._load_base_system_prompt()
    
    def _load_base_system_prompt(self) -> str:
        """Charge le system prompt de base"""
        return """Tu es HOPPER, un assistant personnel intelligent et proactif.

CAPACITÉS:
- Compréhension du langage naturel en français et anglais
- Exécution d'actions système (fichiers, applications, commandes)
- Gestion d'emails et calendrier
- Apprentissage et mémorisation de faits
- Conversation contextuelle multi-tour

COMPORTEMENT:
- Toujours répondre en français naturel et professionnel
- Expliquer tes actions de manière transparente
- Demander confirmation pour actions risquées
- Utiliser ta mémoire et le contexte de la conversation
- Générer des plans d'action structurés en JSON

SÉCURITÉ:
- Vérifier les permissions avant chaque action
- Respecter les consentements utilisateur
- Ne jamais exécuter d'actions destructives sans confirmation
- Logger toutes les actions pour audit

FORMAT DE RÉPONSE:
Tu dois TOUJOURS répondre avec un plan structuré en JSON:
{
    "reasoning": "Explication de ton raisonnement",
    "intent": "type_intention (question/action_system/email/etc)",
    "confidence": 0.0-1.0,
    "actions": [
        {
            "tool": "nom_outil",
            "action": "action_specifique",
            "params": {...},
            "narration": "Description action pour utilisateur"
        }
    ],
    "response": "Message naturel pour l'utilisateur",
    "needs_confirmation": false,
    "needs_more_info": false
}
"""
    
    def assemble_prompt(
        self,
        user_input: str,
        user_id: str = "default",
        session_id: str = "",
        include_tools_schema: bool = True
    ) -> Dict[str, Any]:
        """
        Assemble le prompt complet avec injection contextuelle
        
        Args:
            user_input: Message de l'utilisateur
            user_id: ID utilisateur
            session_id: ID session
            include_tools_schema: Inclure le schema des outils disponibles
            
        Returns:
            Dict avec system_prompt, messages, context
        """
        logger.debug(f"Assemblage prompt pour user={user_id}, input='{user_input[:50]}...'")
        
        # 1. Construire le contexte complet
        prompt_context = self._build_prompt_context(user_id, session_id, user_input)
        
        # 2. System prompt enrichi
        system_prompt = self._build_system_prompt(prompt_context, include_tools_schema)
        
        # 3. Messages formatés (historique + nouveau message)
        messages = self._build_messages(prompt_context, user_input)
        
        # 4. Metadata pour le LLM
        metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "context_size": len(str(prompt_context)),
            "has_knowledge": len(prompt_context.relevant_knowledge) > 0,
            "has_history": len(prompt_context.conversation_history) > 0
        }
        
        return {
            "system_prompt": system_prompt,
            "messages": messages,
            "context": prompt_context,
            "metadata": metadata
        }
    
    def _build_prompt_context(
        self,
        user_id: str,
        session_id: str,
        user_input: str
    ) -> PromptContext:
        """Construit le contexte complet à injecter"""
        
        # 1. Historique conversationnel (deque corrigée)
        conversation_history = []
        if self.context_manager:
            history = self.context_manager.get_history_for_prompt(user_id, max_exchanges=10)
            conversation_history = history
        
        # 2. Mémoire vectorielle pertinente (RAG)
        relevant_knowledge = []
        if self.knowledge_base:
            try:
                # Recherche sémantique dans FAISS
                results = self.knowledge_base.search(user_input, top_k=3, min_score=0.5)
                relevant_knowledge = [r['text'] for r in results]
            except Exception as e:
                logger.warning(f"Erreur RAG: {e}")
        
        # 3. État des tâches actives
        active_tasks = []
        if self.context_manager:
            context = self.context_manager.get_context(user_id)
            active_tasks = context.get('active_tasks', [])
        
        # 4. Consentements actifs
        active_consents = []
        if self.consent_manager:
            try:
                consents = self.consent_manager.get_active_consents(user_id)
                active_consents = [
                    f"{c['scope']} (mode: {c['mode']}, expires: {c.get('expires_at', 'never')})"
                    for c in consents
                ]
            except Exception as e:
                logger.warning(f"Erreur consent_manager: {e}")
        
        # 5. Traces d'audit récentes
        recent_actions = []
        if self.audit_store:
            try:
                audit_entries = self.audit_store.get_recent_actions(user_id, limit=5)
                recent_actions = [
                    f"{a['tool_name']}.{a['action']} - {a['status']}"
                    for a in audit_entries
                ]
            except Exception as e:
                logger.warning(f"Erreur audit_store: {e}")
        
        # 6. Variables de session
        session_variables = {}
        if self.context_manager:
            context = self.context_manager.get_context(user_id)
            session_variables = context.get('variables', {})
        
        return PromptContext(
            conversation_history=conversation_history,
            relevant_knowledge=relevant_knowledge,
            active_tasks=active_tasks,
            active_consents=active_consents,
            recent_actions=recent_actions,
            session_variables=session_variables,
            user_id=user_id,
            session_id=session_id
        )
    
    def _build_system_prompt(
        self,
        context: PromptContext,
        include_tools_schema: bool
    ) -> str:
        """Construit le system prompt avec contexte injecté"""
        
        parts = [self.base_system_prompt]
        
        # Injection mémoire vectorielle
        if context.relevant_knowledge:
            parts.append("\n=== CONNAISSANCES PERTINENTES ===")
            for i, knowledge in enumerate(context.relevant_knowledge, 1):
                parts.append(f"{i}. {knowledge}")
        
        # Injection consentements actifs
        if context.active_consents:
            parts.append("\n=== CONSENTEMENTS ACTIFS ===")
            for consent in context.active_consents:
                parts.append(f"- {consent}")
        
        # Injection tâches actives
        if context.active_tasks:
            parts.append("\n=== TÂCHES ACTIVES ===")
            for task in context.active_tasks:
                parts.append(f"- {task.get('description', 'Tâche sans description')}")
        
        # Injection actions récentes (pour contexte)
        if context.recent_actions:
            parts.append("\n=== ACTIONS RÉCENTES ===")
            for action in context.recent_actions[-3:]:  # 3 dernières seulement
                parts.append(f"- {action}")
        
        # Schema des outils disponibles (function calling)
        if include_tools_schema:
            parts.append(self._get_tools_schema())
        
        return "\n".join(parts)
    
    def _build_messages(
        self,
        context: PromptContext,
        user_input: str
    ) -> List[Dict[str, str]]:
        """Construit la liste des messages (historique + nouveau)"""
        
        messages = []
        
        # Ajouter l'historique conversationnel
        for exchange in context.conversation_history:
            # Message utilisateur
            messages.append({
                "role": "user",
                "content": exchange.get('content', exchange.get('user', ''))
            })
            # Réponse assistant
            if exchange.get('role') == 'assistant' or 'assistant' in exchange:
                messages.append({
                    "role": "assistant",
                    "content": exchange.get('content', exchange.get('assistant', ''))
                })
        
        # Ajouter le nouveau message utilisateur
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        return messages
    
    def _get_tools_schema(self) -> str:
        """Retourne le schema des outils disponibles pour function calling"""
        
        return """
=== OUTILS DISPONIBLES ===

1. system_executor
   Actions: create_file, delete_file, list_directory, open_application, execute_command
   Params: path (string), content (string), app_name (string), command (string)
   Risk: LOW à HIGH selon action

2. llm_knowledge
   Actions: learn, search, forget
   Params: text (string), query (string), fact_id (string)
   Risk: SAFE

3. email_connector (à venir)
   Actions: read_inbox, send_email, search_emails
   Params: query (string), to (string), subject (string), body (string)
   Risk: MEDIUM

4. tts
   Actions: speak
   Params: text (string), voice (string), speed (float)
   Risk: SAFE

5. calendar_connector (à venir)
   Actions: list_events, create_event
   Params: date (string), title (string), description (string)
   Risk: LOW

UTILISATION:
Pour chaque action, spécifie:
- tool: nom de l'outil
- action: action spécifique
- params: paramètres requis
- narration: description courte pour l'utilisateur

EXEMPLE:
{
    "tool": "system_executor",
    "action": "create_file",
    "params": {"path": "/tmp/notes.txt", "content": "Hello"},
    "narration": "Je crée le fichier notes.txt"
}
"""
    
    def create_replan_prompt(
        self,
        original_input: str,
        tool_summary: 'ToolSummary',
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Crée un prompt de replanification après exécution des outils
        Pour ReAct: Thought → Act → Observe → Answer
        
        Args:
            original_input: Entrée utilisateur originale
            tool_summary: Résumé de l'exécution des outils
            user_id: ID utilisateur
            
        Returns:
            Prompt assemblé pour reformulation finale
        """
        
        # Observation des résultats
        observation = self._format_tool_summary(tool_summary)
        
        # Prompt de reformulation
        replan_input = f"""CONTEXTE:
L'utilisateur a demandé: "{original_input}"

J'ai exécuté les actions suivantes:
{observation}

TÂCHE:
Formule une réponse naturelle pour l'utilisateur basée sur ces résultats.
Explique ce qui a été fait et les résultats obtenus.
Si certaines actions ont échoué, explique pourquoi et propose des alternatives.

Réponds avec le même format JSON structuré.
"""
        
        return self.assemble_prompt(
            user_input=replan_input,
            user_id=user_id,
            include_tools_schema=False  # Pas besoin du schema pour reformulation
        )
    
    def _format_tool_summary(self, summary: 'ToolSummary') -> str:
        """Formate le résumé des outils pour observation"""
        
        parts = []
        parts.append(f"Total exécuté: {summary.tools_executed}")
        parts.append(f"Succès: {summary.tools_succeeded}, Échecs: {summary.tools_failed}")
        
        if summary.results:
            parts.append("\nRÉSULTATS:")
            for result in summary.results:
                parts.append(f"- {result['tool']}.{result['action']}: {result.get('result', 'OK')}")
        
        if summary.errors:
            parts.append("\nERREURS:")
            for error in summary.errors:
                parts.append(f"- {error}")
        
        return "\n".join(parts)
    
    def create_fallback_response(
        self,
        error: str,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Crée une réponse de fallback en cas d'échec LLM
        Template sécurisé minimal
        """
        
        return {
            "success": False,
            "message": "Je rencontre une difficulté technique. Pouvez-vous reformuler votre demande ?",
            "data": {
                "error": error,
                "original_input": user_input,
                "retry_possible": True,
                "suggested_action": "Essayez de reformuler de manière plus simple"
            },
            "actions_taken": ["fallback"]
        }


# ==================== EXPORT ====================

__all__ = ['PromptAssembler']
