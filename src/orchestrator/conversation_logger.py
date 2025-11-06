"""
HOPPER - Conversation Logger (Phase 4)
Enregistre toutes les interactions user ↔ LLM pour:
- Analyse qualité réponses
- Fine-tuning futur
- Débogage
- Métriques

Format: JSONL (une conversation par ligne)
Stockage: data/conversations/{date}.jsonl
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger


class ConversationLogger:
    """Logger pour toutes les interactions conversationnelles"""
    
    def __init__(self, base_dir: str = "data/conversations"):
        """
        Initialise le logger
        
        Args:
            base_dir: Répertoire de stockage des conversations
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichier du jour
        self.current_file = self._get_current_file()
        
        logger.info(f"📝 ConversationLogger initialisé: {self.current_file}")
    
    def _get_current_file(self) -> Path:
        """Obtenir le fichier de log du jour"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.base_dir / f"conversations_{date_str}.jsonl"
    
    def log_interaction(
        self,
        user_input: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: str = "default",
        session_id: Optional[str] = None,
        type_: str = "conversation"  # conversation, system, voice
    ) -> None:
        """
        Enregistrer une interaction
        
        Args:
            user_input: Entrée utilisateur (texte ou commande)
            response: Réponse du système
            metadata: Métadonnées additionnelles (tokens, duration, etc.)
            user_id: ID utilisateur
            session_id: ID de session (pour grouper conversations)
            type_: Type d'interaction
        """
        try:
            # Vérifier si on change de jour
            current_file = self._get_current_file()
            if current_file != self.current_file:
                self.current_file = current_file
                logger.info(f"📝 Nouveau fichier de log: {self.current_file}")
            
            # Construire l'entrée
            entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "session_id": session_id,
                "type": type_,
                "user_input": user_input,
                "response": response,
                "metadata": metadata or {}
            }
            
            # Écrire en JSONL (append)
            with open(self.current_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
            logger.debug(f"✅ Interaction logged: {type_} - {len(user_input)} chars")
            
        except Exception as e:
            logger.error(f"❌ Erreur log interaction: {e}")
    
    def log_feedback(
        self,
        user_input: str,
        response: str,
        feedback: str,  # "positive", "negative", "neutral"
        comment: Optional[str] = None,
        user_id: str = "default"
    ) -> None:
        """
        Enregistrer un feedback utilisateur
        
        Args:
            user_input: Entrée originale
            response: Réponse donnée
            feedback: Type de feedback (positive/negative/neutral)
            comment: Commentaire optionnel
            user_id: ID utilisateur
        """
        metadata = {
            "feedback": feedback,
            "comment": comment,
            "is_feedback": True
        }
        
        self.log_interaction(
            user_input=user_input,
            response=response,
            metadata=metadata,
            user_id=user_id,
            type_="feedback"
        )
        
        logger.info(f"👍/👎 Feedback enregistré: {feedback}")
    
    def get_today_conversations(self) -> List[Dict[str, Any]]:
        """Récupérer les conversations du jour"""
        try:
            if not self.current_file.exists():
                return []
            
            conversations = []
            with open(self.current_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        conversations.append(json.loads(line))
            
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture conversations: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du jour"""
        conversations = self.get_today_conversations()
        
        if not conversations:
            return {
                "total": 0,
                "by_type": {},
                "users": set(),
                "feedbacks": {"positive": 0, "negative": 0, "neutral": 0}
            }
        
        # Statistiques
        by_type = {}
        users = set()
        feedbacks = {"positive": 0, "negative": 0, "neutral": 0}
        
        for conv in conversations:
            # Par type
            type_ = conv.get("type", "unknown")
            by_type[type_] = by_type.get(type_, 0) + 1
            
            # Utilisateurs
            users.add(conv.get("user_id", "unknown"))
            
            # Feedbacks
            if conv.get("type") == "feedback":
                fb = conv.get("metadata", {}).get("feedback", "neutral")
                if fb in feedbacks:
                    feedbacks[fb] += 1
        
        return {
            "total": len(conversations),
            "by_type": by_type,
            "users": list(users),
            "user_count": len(users),
            "feedbacks": feedbacks,
            "file": str(self.current_file)
        }
    
    def export_for_finetuning(
        self,
        output_file: str = "data/training/finetune_dataset.jsonl",
        min_quality: float = 0.0,
        types: List[str] = ["conversation"]
    ) -> int:
        """
        Exporter conversations pour fine-tuning
        
        Args:
            output_file: Fichier de sortie
            min_quality: Score qualité minimum (TODO: implémenter scoring)
            types: Types d'interactions à exporter
            
        Returns:
            Nombre d'entrées exportées
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Collecter tous les fichiers de conversations
            all_conversations = []
            for conv_file in self.base_dir.glob("conversations_*.jsonl"):
                with open(conv_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            conv = json.loads(line)
                            if conv.get("type") in types:
                                all_conversations.append(conv)
            
            # Convertir au format fine-tuning
            count = 0
            with open(output_path, "w", encoding="utf-8") as f:
                for conv in all_conversations:
                    # Format: {"instruction": "...", "input": "...", "output": "..."}
                    entry = {
                        "instruction": "Tu es HOPPER, un assistant IA personnel. Réponds de manière utile et concise.",
                        "input": conv["user_input"],
                        "output": conv["response"]
                    }
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    count += 1
            
            logger.success(f"✅ {count} conversations exportées vers {output_file}")
            return count
            
        except Exception as e:
            logger.error(f"❌ Erreur export fine-tuning: {e}")
            return 0


# Instance globale (singleton)
_logger: Optional[ConversationLogger] = None


def get_conversation_logger() -> ConversationLogger:
    """Obtenir l'instance singleton du logger"""
    global _logger
    if _logger is None:
        _logger = ConversationLogger()
    return _logger
