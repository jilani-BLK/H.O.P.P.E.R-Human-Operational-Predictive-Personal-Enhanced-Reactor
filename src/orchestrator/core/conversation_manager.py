"""
HOPPER - Conversation Manager
Gère l'historique des conversations en mémoire (Phase 2)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


@dataclass
class Message:
    """Message d'une conversation"""
    role: str  # "user" ou "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tokens: int = 0


@dataclass
class Conversation:
    """Conversation complète avec historique"""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    max_history: int = 10  # Limiter historique pour économiser tokens
    
    def add_message(self, role: str, content: str, tokens: int = 0):
        """Ajoute un message à l'historique"""
        msg = Message(role=role, content=content, tokens=tokens)
        self.messages.append(msg)
        
        # Limiter l'historique
        if len(self.messages) > self.max_history * 2:  # *2 car user + assistant
            # Garder toujours les 2 premiers messages (contexte initial)
            if len(self.messages) > 2:
                self.messages = self.messages[:2] + self.messages[-(self.max_history * 2):]
    
    def get_history(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Retourne l'historique formaté pour le LLM"""
        recent_messages = self.messages[-max_messages:]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]
    
    def get_total_tokens(self) -> int:
        """Calcule le nombre total de tokens"""
        return sum(msg.tokens for msg in self.messages)
    
    def clear(self):
        """Efface l'historique"""
        self.messages = []


class ConversationManager:
    """Gestionnaire de conversations (en mémoire Phase 2)"""
    
    def __init__(self):
        """Initialise le gestionnaire"""
        self.conversations: Dict[str, Conversation] = {}
        logger.info("💬 ConversationManager initialisé (en mémoire)")
    
    def create_conversation(self, conversation_id: str) -> Conversation:
        """
        Crée une nouvelle conversation
        
        Args:
            conversation_id: ID unique de la conversation
            
        Returns:
            Conversation créée
        """
        conv = Conversation(id=conversation_id)
        self.conversations[conversation_id] = conv
        logger.info(f"📝 Nouvelle conversation: {conversation_id}")
        return conv
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Récupère une conversation existante
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Conversation ou None
        """
        return self.conversations.get(conversation_id)
    
    def get_or_create(self, conversation_id: str) -> Conversation:
        """
        Récupère ou crée une conversation
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Conversation
        """
        conv = self.get_conversation(conversation_id)
        if conv is None:
            conv = self.create_conversation(conversation_id)
        return conv
    
    def add_user_message(self, conversation_id: str, content: str):
        """Ajoute un message utilisateur"""
        conv = self.get_or_create(conversation_id)
        conv.add_message("user", content)
    
    def add_assistant_message(
        self,
        conversation_id: str,
        content: str,
        tokens: int = 0
    ):
        """Ajoute un message assistant"""
        conv = self.get_or_create(conversation_id)
        conv.add_message("assistant", content, tokens)
    
    def get_history(
        self,
        conversation_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """Retourne l'historique d'une conversation"""
        conv = self.get_conversation(conversation_id)
        if conv is None:
            return []
        return conv.get_history(max_messages)
    
    def clear_conversation(self, conversation_id: str):
        """Efface une conversation"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].clear()
            logger.info(f"🗑️  Conversation effacée: {conversation_id}")
    
    def delete_conversation(self, conversation_id: str):
        """Supprime une conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"🗑️  Conversation supprimée: {conversation_id}")
    
    def list_conversations(self) -> List[str]:
        """Liste toutes les conversations actives"""
        return list(self.conversations.keys())
    
    def get_stats(self) -> Dict:
        """Statistiques des conversations"""
        total_messages = sum(
            len(conv.messages)
            for conv in self.conversations.values()
        )
        
        return {
            "total_conversations": len(self.conversations),
            "total_messages": total_messages,
            "conversation_ids": self.list_conversations()
        }


# Instance globale (singleton pour Phase 2)
_conversation_manager = None


def get_conversation_manager() -> ConversationManager:
    """Récupère l'instance globale du ConversationManager"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


# Test standalone
if __name__ == "__main__":
    cm = ConversationManager()
    
    # Créer conversation
    conv_id = "test-001"
    
    # Simuler échange
    cm.add_user_message(conv_id, "Bonjour!")
    cm.add_assistant_message(conv_id, "Bonjour! Comment puis-je vous aider?", tokens=15)
    
    cm.add_user_message(conv_id, "Qui es-tu?")
    cm.add_assistant_message(conv_id, "Je suis HOPPER, votre assistant local.", tokens=20)
    
    # Afficher historique
    history = cm.get_history(conv_id)
    print("\n📜 Historique:")
    for msg in history:
        print(f"  {msg['role']}: {msg['content']}")
    
    # Stats
    stats = cm.get_stats()
    print(f"\n📊 Stats: {stats}")
