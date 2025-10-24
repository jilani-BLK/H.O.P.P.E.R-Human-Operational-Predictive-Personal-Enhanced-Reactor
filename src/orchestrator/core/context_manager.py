"""
Gestionnaire de contexte conversationnel
Maintient l'historique et l'état des conversations par utilisateur
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
from loguru import logger


class ContextManager:
    """Gère le contexte conversationnel pour chaque utilisateur"""
    
    def __init__(self, max_history: int = 50):
        """
        Args:
            max_history: Nombre maximum d'échanges à conserver en mémoire
        """
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.max_history = max_history
        
    def get_context(self, user_id: str) -> Dict[str, Any]:
        """
        Récupère le contexte d'un utilisateur
        
        Args:
            user_id: Identifiant de l'utilisateur
            
        Returns:
            Contexte complet de l'utilisateur
        """
        if user_id not in self.contexts:
            self.contexts[user_id] = self._create_empty_context()
        
        return self.contexts[user_id]
    
    def _create_empty_context(self) -> Dict[str, Any]:
        """Crée un contexte vide"""
        return {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "conversation_history": deque(maxlen=self.max_history),
            "user_preferences": {},
            "active_tasks": [],
            "variables": {}
        }
    
    def update_context(self, user_id: str, updates: Dict[str, Any]) -> None:
        """
        Met à jour le contexte d'un utilisateur
        
        Args:
            user_id: Identifiant de l'utilisateur
            updates: Dictionnaire de mises à jour
        """
        context = self.get_context(user_id)
        
        for key, value in updates.items():
            if key == "conversation_history":
                # Gestion spéciale de l'historique
                continue
            context[key] = value
        
        context["last_updated"] = datetime.now().isoformat()
        logger.debug(f"Contexte mis à jour pour {user_id}")
    
    def add_to_history(
        self,
        user_id: str,
        user_input: str,
        assistant_response: str,
        actions_taken: Optional[List[str]] = None
    ) -> None:
        """
        Ajoute un échange à l'historique
        
        Args:
            user_id: Identifiant de l'utilisateur
            user_input: Message de l'utilisateur
            assistant_response: Réponse de l'assistant
            actions_taken: Liste des actions effectuées
        """
        # Get or create context
        _ = self.get_context(user_id)
        
        # Store exchange data
        _exchange: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "assistant_response": assistant_response,
            "actions_taken": actions_taken or []
        }
    
    def get_conversation_history(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère l'historique de conversation
        
        Args:
            user_id: Identifiant de l'utilisateur
            limit: Nombre d'échanges à retourner (None = tous)
            
        Returns:
            Liste des échanges
        """
        context = self.get_context(user_id)
        history = list(context["conversation_history"])
        
        if limit:
            return history[-limit:]
        return history
    
    def clear_context(self, user_id: str) -> None:
        """
        Efface le contexte d'un utilisateur
        
        Args:
            user_id: Identifiant de l'utilisateur
        """
        if user_id in self.contexts:
            del self.contexts[user_id]
            logger.info(f"Contexte effacé pour {user_id}")
    
    def set_variable(self, user_id: str, key: str, value: Any) -> None:
        """
        Définit une variable dans le contexte
        
        Args:
            user_id: Identifiant de l'utilisateur
            key: Nom de la variable
            value: Valeur
        """
        context = self.get_context(user_id)
        context["variables"][key] = value
        context["last_updated"] = datetime.now().isoformat()
    
    def get_variable(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Récupère une variable du contexte
        
        Args:
            user_id: Identifiant de l'utilisateur
            key: Nom de la variable
            default: Valeur par défaut si non trouvée
            
        Returns:
            Valeur de la variable
        """
        context = self.get_context(user_id)
        return context["variables"].get(key, default)
    
    def format_history_for_llm(
        self,
        user_id: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Formate l'historique pour être envoyé au LLM
        
        Args:
            user_id: Identifiant de l'utilisateur
            max_tokens: Limite approximative de tokens
        Returns:
            Historique formaté en texte
        """
        history = self.get_conversation_history(user_id)
        
        formatted: List[str] = []
        total_length = 0
        
        # Parcours inverse pour prendre les messages les plus récents
        for exchange in reversed(history):
            msg = f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n"
            msg_length = len(msg.split())  # Approximation grossière
            
            if total_length + msg_length > max_tokens:
                break
            
            formatted.insert(0, msg)
            total_length += msg_length
        
        return "\n".join(formatted)
    
    def get_history_for_prompt(self, user_id: str, max_exchanges: int = 10) -> List[Dict[str, str]]:
        """
        Retourne historique formaté pour PromptBuilder
        
        Args:
            user_id: Identifiant utilisateur
            max_exchanges: Nombre max d'échanges
            
        Returns:
            Liste [{"role": "user"/"assistant", "content": "..."}]
        """
        history = self.get_conversation_history(user_id, limit=max_exchanges)
        
        formatted_history: List[Dict[str, Any]] = []
        for exchange in history:
            # Ajouter message utilisateur
            formatted_history.append({
                "role": "user",
                "content": exchange['user'],
                "timestamp": exchange['timestamp']
            })
            # Ajouter réponse assistant
            formatted_history.append({
                "role": "assistant",
                "content": exchange['assistant'],
                "timestamp": exchange['timestamp']
            })
        
        return formatted_history
    
    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Statistiques sur le contexte utilisateur
        
        Returns:
            Dict avec stats
        """
        if user_id not in self.contexts:
            return {"exists": False}
        
        context = self.get_context(user_id)
        history = list(context['conversation_history'])
        
        return {
            "exists": True,
            "created_at": context['created_at'],
            "last_updated": context['last_updated'],
            "total_exchanges": len(history),
            "variables_count": len(context['variables']),
            "active_tasks": len(context['active_tasks']),
            "first_exchange": history[0]['timestamp'] if history else None,
            "last_exchange": history[-1]['timestamp'] if history else None
        }
