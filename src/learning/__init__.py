"""
Système d'apprentissage adaptatif pour HOPPER
Apprentissage continu sous contrôle humain
"""

# Modules existants
from .preferences.preferences_manager import PreferencesManager, UserPreferences
from .fine_tuning.conversation_collector import ConversationCollector
from .feedback.feedback_manager import FeedbackManager
from .integration.fastapi_middleware import LearningMiddleware, get_learning_middleware

# Nouveaux modules d'apprentissage adaptatif
from .memory_manager import MemoryManager, MemoryType, Memory, MemoryQuery
from .preference_manager import PreferenceManager as AdaptivePreferenceManager, PreferenceCategory, UserPreference, AdaptationLevel
from .feedback_system import FeedbackSystem, FeedbackType, Feedback, RewardSignal
from .adaptation_engine_contextual import AdaptationEngine, ContextType, AdaptationStrategy, ContextSnapshot
from .knowledge_base import KnowledgeBase, KnowledgeType, SourceType, KnowledgeEntry
from .validation_system import ValidationSystem, ValidationType, ValidationStatus, RiskLevel, ValidationRequest
from .adaptive_learning_system import AdaptiveLearningSystem

__all__ = [
    # Modules existants
    'PreferencesManager',
    'UserPreferences',
    'ConversationCollector',
    'FeedbackManager',
    'LearningMiddleware',
    'get_learning_middleware',
    
    # Système adaptatif complet
    'AdaptiveLearningSystem',
    
    # Mémoire
    'MemoryManager',
    'MemoryType',
    'Memory',
    'MemoryQuery',
    
    # Préférences adaptatives
    'AdaptivePreferenceManager',
    'PreferenceCategory',
    'UserPreference',
    'AdaptationLevel',
    
    # Feedback
    'FeedbackSystem',
    'FeedbackType',
    'Feedback',
    'RewardSignal',
    
    # Adaptation
    'AdaptationEngine',
    'ContextType',
    'AdaptationStrategy',
    'ContextSnapshot',
    
    # Connaissances
    'KnowledgeBase',
    'KnowledgeType',
    'SourceType',
    'KnowledgeEntry',
    
    # Validation
    'ValidationSystem',
    'ValidationType',
    'ValidationStatus',
    'RiskLevel',
    'ValidationRequest',
]

__version__ = '1.0.0'

