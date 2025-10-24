"""
FastAPI Middleware d'intégration Phase 4 pour l'Orchestrateur
Applique les préférences et collecte les données d'apprentissage
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import time
from typing import Optional

from ..preferences.preferences_manager import PreferencesManager
from ..fine_tuning.conversation_collector import ConversationCollector
from ..feedback.feedback_manager import FeedbackManager


class LearningMiddleware(BaseHTTPMiddleware):
    """Middleware FastAPI pour l'apprentissage dans l'orchestrateur"""
    
    def __init__(self, app):
        """Initialise les composants d'apprentissage"""
        super().__init__(app)
        
        self.preferences = PreferencesManager()
        self.collector = ConversationCollector()
        self.feedback = FeedbackManager()
        
        # Conversations en cours par user_id
        self.active_conversations = {}
        
        print("✅ Learning Middleware (FastAPI) initialisé")
        print(self.preferences.get_summary())
    
    async def dispatch(self, request: Request, call_next):
        """
        Traite chaque requête
        
        Args:
            request: Requête FastAPI
            call_next: Fonction suivante dans la chaîne
            
        Returns:
            Response avec headers enrichis
        """
        # Timestamp de début
        start_time = time.time()
        
        # Stocker dans request.state pour accès ultérieur
        request.state.start_time = start_time
        request.state.learning = self
        
        # Traiter la requête
        response = await call_next(request)
        
        # Calculer temps de réponse
        response_time_ms = int((time.time() - start_time) * 1000)
        response.headers['X-Response-Time'] = f'{response_time_ms}ms'
        
        # Stocker pour collecte
        request.state.response_time_ms = response_time_ms
        
        return response
    
    def should_notify(self, priority: str = "medium", 
                     contact: Optional[str] = None, 
                     content: Optional[str] = None) -> bool:
        """
        Détermine si une notification doit être envoyée
        
        Args:
            priority: urgent, high, medium, low
            contact: Contact source
            content: Contenu pour détecter mots-clés
            
        Returns:
            True si notification autorisée
        """
        return self.preferences.should_notify(priority, contact, content)
    
    def get_verbosity(self) -> str:
        """Retourne le niveau de verbosité configuré"""
        return self.preferences.get_verbosity_level()
    
    def requires_confirmation(self, command: str) -> bool:
        """Vérifie si une commande nécessite confirmation"""
        return self.preferences.requires_confirmation(command)
    
    def start_conversation(self, user_id: str) -> str:
        """
        Démarre une nouvelle conversation pour un utilisateur
        
        Args:
            user_id: Identifiant utilisateur
            
        Returns:
            ID de conversation
        """
        if user_id not in self.active_conversations:
            conv_id = self.collector.start_conversation()
            self.active_conversations[user_id] = conv_id
        
        return self.active_conversations[user_id]
    
    def collect_interaction(self, 
                           user_id: str,
                           user_input: str, 
                           assistant_response: str,
                           intent: Optional[str] = None, 
                           satisfaction_score: Optional[int] = None,
                           error: Optional[str] = None):
        """
        Collecte une interaction pour le fine-tuning
        
        Args:
            user_id: Identifiant utilisateur
            user_input: Entrée utilisateur
            assistant_response: Réponse de l'assistant
            intent: Intention détectée
            satisfaction_score: Score 1-5
            error: Erreur éventuelle
        """
        if not self.preferences.preferences.collect_conversations:
            return  # Collecte désactivée
        
        # S'assurer qu'une conversation existe
        self.start_conversation(user_id)
        
        # Ajouter au collecteur avec contexte structuré
        context_data = {
            "time_of_day": self._get_current_context(),
            "user_id": user_id
        }
        
        self.collector.add_turn(
            user_input=user_input,
            assistant_response=assistant_response,
            intent=intent,
            satisfaction_score=satisfaction_score,
            context=context_data,
            error=error
        )
    
    def _get_current_context(self) -> str:
        """Détermine le contexte actuel (morning, evening, etc.)"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def add_feedback(self, 
                    score: int, 
                    comment: Optional[str] = None,
                    interaction_type: Optional[str] = None,
                    response_time_ms: Optional[int] = None,
                    error_occurred: bool = False):
        """
        Ajoute un feedback utilisateur
        
        Args:
            score: Score 1-5
            comment: Commentaire
            interaction_type: Type d'interaction
            response_time_ms: Temps de réponse
            error_occurred: Si erreur
        """
        context = self._get_current_context()
        
        self.feedback.add_feedback(
            score=score,
            comment=comment,
            context=context,
            interaction_type=interaction_type,
            response_time_ms=response_time_ms,
            error_occurred=error_occurred
        )
    
    def should_request_feedback(self) -> bool:
        """Vérifie s'il faut demander du feedback"""
        if not self.preferences.preferences.request_daily_feedback:
            return False
        
        return self.feedback.should_request_feedback()
    
    def get_feedback_prompt(self) -> str:
        """Retourne le prompt pour demander du feedback"""
        return self.feedback.get_feedback_prompt()
    
    def get_daily_stats(self) -> dict:
        """Retourne les statistiques du jour"""
        return self.feedback.get_daily_summary()
    
    def get_weekly_stats(self) -> dict:
        """Retourne les statistiques hebdomadaires"""
        return self.feedback.get_weekly_summary()
    
    def export_training_data(self, min_satisfaction: float = 3.0) -> str:
        """
        Exporte les données pour le fine-tuning
        
        Args:
            min_satisfaction: Score minimum
            
        Returns:
            Chemin du fichier exporté
        """
        filepath = self.collector.export_for_finetuning(min_satisfaction=min_satisfaction)
        return str(filepath)
    
    def get_conversation_stats(self) -> dict:
        """Retourne les statistiques des conversations"""
        return self.collector.get_statistics()


# Instance globale (sera initialisée dans main.py)
learning_middleware: Optional[LearningMiddleware] = None


def get_learning_middleware() -> Optional[LearningMiddleware]:
    """Retourne l'instance du middleware d'apprentissage"""
    return learning_middleware
