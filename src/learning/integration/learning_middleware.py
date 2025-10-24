"""
Middleware d'intégration Phase 4 pour l'Orchestrateur (Flask - DEPRECATED)
NOTE: Ce fichier est obsolète. Utilisez fastapi_middleware.py à la place.
Applique les préférences et collecte les données d'apprentissage
"""
# type: ignore

from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime
import time

from ..preferences.preferences_manager import PreferencesManager
from ..fine_tuning.conversation_collector import ConversationCollector
from ..feedback.feedback_manager import FeedbackManager

# Stub pour éviter les erreurs (fichier obsolète)
class _StubG:
    """Stub pour compatibilité"""
    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)
    
    def __getattr__(self, name: str) -> Any:
        return None

class _StubRequest:
    """Stub pour compatibilité"""
    args = {}

g = _StubG()
request = _StubRequest()


class LearningMiddleware:
    """Middleware pour l'apprentissage dans l'orchestrateur"""
    
    def __init__(self):
        """Initialise les composants d'apprentissage"""
        self.preferences = PreferencesManager()
        self.collector = ConversationCollector()
        self.feedback = FeedbackManager()
        
        # Conversation en cours
        self.current_conversation_id = None
        
        print("✅ Learning Middleware initialisé")
        print(self.preferences.get_summary())
    
    def before_request(self):
        """Hook exécuté avant chaque requête"""
        # Stocker le timestamp de début
        g.start_time = time.time()
        
        # Démarrer une nouvelle conversation si nécessaire
        if self.current_conversation_id is None:
            self.current_conversation_id = self.collector.start_conversation()
            g.conversation_id = self.current_conversation_id
    
    def after_request(self, response):
        """Hook exécuté après chaque requête"""
        # Calculer le temps de réponse
        if hasattr(g, 'start_time'):
            response_time_ms = int((time.time() - g.start_time) * 1000)
            response.headers['X-Response-Time'] = f'{response_time_ms}ms'
            
            # Stocker pour collecte
            g.response_time_ms = response_time_ms
        
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
    
    def collect_interaction(self, user_input: str, assistant_response: str,
                           intent: Optional[str] = None, 
                           satisfaction_score: Optional[int] = None,
                           error: Optional[str] = None):
        """
        Collecte une interaction pour le fine-tuning
        
        Args:
            user_input: Entrée utilisateur
            assistant_response: Réponse de l'assistant
            intent: Intention détectée
            satisfaction_score: Score 1-5
            error: Erreur éventuelle
        """
        if not self.preferences.preferences.collect_conversations:
            return  # Collecte désactivée
        
        # Ajouter au collecteur avec contexte structuré
        context_data = {"time_of_day": self._get_current_context()}
        
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
    
    def add_feedback(self, score: int, comment: Optional[str] = None,
                    interaction_type: Optional[str] = None,
                    error_occurred: bool = False):
        """
        Ajoute un feedback utilisateur
        
        Args:
            score: Score 1-5
            comment: Commentaire
            interaction_type: Type d'interaction
            error_occurred: Si erreur
        """
        context = self._get_current_context()
        response_time_ms = getattr(g, 'response_time_ms', None)
        
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
    
    def export_training_data(self, min_satisfaction: float = 3.0) -> str:
        """
        Exporte les données pour le fine-tuning
        
        Args:
            min_satisfaction: Score minimum
            
        Returns:
            Chemin du fichier exporté
        """
        return str(self.collector.export_for_finetuning(min_satisfaction=min_satisfaction))


def require_preferences(f: Callable) -> Callable:
    """
    Décorateur pour appliquer les préférences à une route
    
    Usage:
        @app.route('/api/something')
        @require_preferences
        def something():
            # Les préférences sont appliquées automatiquement
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier si mode nuit actif
        if hasattr(g, 'learning_middleware'):
            middleware = g.learning_middleware
            
            # Appliquer filtres selon préférences
            # (exemple: bloquer certaines actions en mode nuit)
            if middleware.preferences.is_night_mode_active():
                # Autoriser seulement si urgence
                if not request.args.get('priority') == 'urgent':
                    return {'error': 'Mode nuit actif - seulement urgences'}, 503
        
        return f(*args, **kwargs)
    
    return decorated_function


def collect_interaction(f: Callable) -> Callable:
    """
    Décorateur pour collecter automatiquement les interactions
    
    Usage:
        @app.route('/api/chat')
        @collect_interaction
        def chat():
            # L'interaction est automatiquement collectée
            return {'response': '...'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Exécuter la fonction
        result = f(*args, **kwargs)
        
        # Collecter si middleware actif
        if hasattr(g, 'learning_middleware') and hasattr(g, 'user_input'):
            middleware = g.learning_middleware
            
            # Extraire la réponse
            if isinstance(result, tuple):
                response_data = result[0]
            else:
                response_data = result
            
            assistant_response = response_data.get('response', '') if isinstance(response_data, dict) else str(response_data)
            
            # Collecter
            middleware.collect_interaction(
                user_input=g.user_input,
                assistant_response=assistant_response,
                intent=getattr(g, 'intent', None),
                error=getattr(g, 'error', None)
            )
        
        return result
    
    return decorated_function


# Exemple d'intégration dans l'orchestrateur
"""
from src.learning.integration.learning_middleware import LearningMiddleware, collect_interaction

app = Flask(__name__)
learning = LearningMiddleware()

@app.before_request
def before_request():
    g.learning_middleware = learning
    learning.before_request()

@app.after_request
def after_request(response):
    return learning.after_request(response)

@app.route('/api/chat', methods=['POST'])
@collect_interaction
def chat():
    data = request.get_json()
    user_input = data.get('message')
    g.user_input = user_input
    
    # Traitement...
    response = process_message(user_input)
    
    return {'response': response}

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    score = data.get('score')
    comment = data.get('comment')
    
    learning.add_feedback(score, comment)
    
    # Vérifier si demander feedback
    if learning.should_request_feedback():
        return {
            'message': 'Feedback enregistré',
            'request_feedback': True,
            'prompt': learning.get_feedback_prompt()
        }
    
    return {'message': 'Feedback enregistré'}
"""
