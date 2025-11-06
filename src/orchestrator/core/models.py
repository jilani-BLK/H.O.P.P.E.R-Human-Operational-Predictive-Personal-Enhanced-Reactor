"""
Architecture LLM-first - Modèles de données fondamentaux
Normalisation de toutes les interactions via enveloppes typées
"""

from pydantic import BaseModel, Field, validator
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class InteractionType(str, Enum):
    """Types d'interactions normalisées"""
    VOICE = "voice"
    TEXT = "text"
    EVENT = "event"
    SENSOR = "sensor"
    CONNECTOR = "connector"
    SYSTEM = "system"


class RiskLevel(str, Enum):
    """Niveaux de risque pour actions"""
    SAFE = "safe"           # Lecture seule, pas d'effet de bord
    LOW = "low"             # Modifications mineures (créer fichier temp)
    MEDIUM = "medium"       # Modifications significatives (delete, email)
    HIGH = "high"           # Actions critiques (sudo, network)
    CRITICAL = "critical"   # Irréversible (format, shutdown)


class ToolStatus(str, Enum):
    """Status d'exécution d'un outil"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"     # Par permission ou confirmation


class ConsentMode(str, Enum):
    """Modes de consentement"""
    MANUAL = "manual"       # Demande à chaque fois
    AUTO_SESSION = "auto_session"  # Auto pendant la session
    AUTO_24H = "auto_24h"   # Auto 24h puis redemande
    ALWAYS = "always"       # Toujours autorisé


# ==================== CORE MODELS ====================

class InteractionEnvelope(BaseModel):
    """
    Enveloppe normalisée pour toutes les entrées système
    Uniformise voix, événements, capteurs, flux connecteurs
    """
    type: InteractionType
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str = "default"
    session_id: Optional[str] = None
    permissions: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ToolCall(BaseModel):
    """
    Appel d'outil demandé par le LLM
    Structure normalisée pour l'exécution
    """
    tool_name: str = Field(..., description="Nom de l'outil (system_executor, email_connector, etc.)")
    action: str = Field(..., description="Action spécifique (create_file, send_email, etc.)")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    narration: Optional[str] = None  # Texte de narration pour l'utilisateur
    
    # Execution state
    status: ToolStatus = ToolStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class SystemPlan(BaseModel):
    """
    Plan d'action généré par le LLM
    Décrit la séquence d'outils à exécuter et le message utilisateur
    """
    intent: str = Field(..., description="Intention détectée (question, action_system, email, etc.)")
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    
    # Tools à exécuter séquentiellement
    tools: List[ToolCall] = Field(default_factory=list)
    
    # Message pour l'utilisateur (généré par LLM, pas codé en dur)
    user_message: str = Field(..., description="Réponse naturelle pour l'utilisateur")
    
    # Narration temps réel des actions
    narration_steps: List[str] = Field(default_factory=list)
    
    # Metadata
    reasoning: Optional[str] = None  # Pensée du LLM (ReAct "Thought")
    requires_more_info: bool = False
    suggested_followup: Optional[str] = None
    
    @validator('tools')
    def validate_tools_not_empty_for_actions(cls, v, values):
        """Si ce n'est pas juste une question, il faut des outils"""
        intent = values.get('intent', '')
        if intent not in ['question', 'conversation', 'clarification'] and len(v) == 0:
            # C'est ok, peut-être que le LLM a décidé de ne rien faire
            pass
        return v


class PerceptionEvent(BaseModel):
    """
    Événement de perception publié par STT, connecteurs, capteurs
    Flux event-driven normalisé
    """
    source: str = Field(..., description="Source de l'événement (stt, email_connector, sensor_temp)")
    event_type: str = Field(..., description="Type d'événement (transcription, new_email, threshold_exceeded)")
    data: Dict[str, Any]
    priority: int = Field(ge=0, le=10, default=5)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Routing
    requires_immediate_response: bool = False
    target_user: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ToolSummary(BaseModel):
    """
    Résumé de l'exécution des outils
    Utilisé pour reprompting au LLM (ReAct "Observe")
    """
    tools_executed: int
    tools_succeeded: int
    tools_failed: int
    
    results: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    total_execution_time_ms: float = 0.0
    
    def add_tool_result(self, tool_call: ToolCall):
        """Ajoute le résultat d'un tool call"""
        if tool_call.status == ToolStatus.SUCCESS:
            self.tools_succeeded += 1
            if tool_call.result:
                self.results.append({
                    "tool": tool_call.tool_name,
                    "action": tool_call.action,
                    "result": tool_call.result
                })
        elif tool_call.status == ToolStatus.FAILED:
            self.tools_failed += 1
            if tool_call.error:
                self.errors.append(f"{tool_call.tool_name}.{tool_call.action}: {tool_call.error}")
        
        self.tools_executed += 1
        if tool_call.execution_time_ms:
            self.total_execution_time_ms += tool_call.execution_time_ms


class ConsentPolicy(BaseModel):
    """
    Politique de consentement pour une action/scope
    Stocké dans SQLite pour persistence
    """
    user_id: str
    scope: str = Field(..., description="Scope de permission (file_operations, email_send, system_command)")
    mode: ConsentMode = ConsentMode.MANUAL
    
    # TTL pour modes auto
    granted_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Metadata
    granted_for_actions: List[str] = Field(default_factory=list)  # Actions spécifiques autorisées
    max_risk_level: RiskLevel = RiskLevel.LOW
    
    def is_valid(self) -> bool:
        """Vérifie si le consentement est toujours valide"""
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditEntry(BaseModel):
    """
    Entrée d'audit pour traçabilité complète
    Toutes les actions loggées dans SQLite
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str
    session_id: str
    
    # Action
    tool_name: str
    action: str
    parameters: Dict[str, Any]
    
    # Contexte décision
    risk_level: RiskLevel
    consent_mode: ConsentMode
    required_confirmation: bool
    user_confirmed: bool
    
    # Résultat
    status: ToolStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== PROMPT CONTEXT ====================

class PromptContext(BaseModel):
    """
    Contexte complet injecté dans les prompts LLM
    Assemblé dynamiquement par PromptAssembler
    """
    # Historique conversationnel
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    
    # Mémoire vectorielle pertinente (RAG)
    relevant_knowledge: List[str] = Field(default_factory=list)
    
    # État des tâches actives
    active_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Consentements actifs
    active_consents: List[str] = Field(default_factory=list)
    
    # Traces d'audit récentes (pour contexte)
    recent_actions: List[str] = Field(default_factory=list)
    
    # Variables de session
    session_variables: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    user_id: str = "default"
    session_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


# ==================== LLM RESPONSE SCHEMAS ====================

class LlmPlanSchema(BaseModel):
    """
    Schema pour function calling - format attendu du LLM
    Utilisé pour valider et parser les réponses structurées
    """
    reasoning: str = Field(..., description="Explication du raisonnement (ReAct Thought)")
    intent: str = Field(..., description="Intention détectée")
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Actions à effectuer
    actions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Liste des actions [{tool, action, params, narration}]"
    )
    
    # Réponse utilisateur
    response: str = Field(..., description="Message naturel pour l'utilisateur")
    
    # Flags
    needs_confirmation: bool = False
    needs_more_info: bool = False
    followup_question: Optional[str] = None


class SafeTemplate(BaseModel):
    """
    Template de fallback si LLM échoue
    Réponse minimale sécurisée
    """
    message: str = "Je suis désolé, je rencontre une difficulté technique. Pouvez-vous reformuler ?"
    log_level: str = "critical"
    retry_possible: bool = True
    suggested_action: Optional[str] = None


# ==================== HELPERS ====================

def create_interaction_envelope(
    type: InteractionType,
    payload: Dict[str, Any],
    user_id: str = "default",
    **kwargs
) -> InteractionEnvelope:
    """Helper pour créer une InteractionEnvelope"""
    return InteractionEnvelope(
        type=type,
        payload=payload,
        user_id=user_id,
        **kwargs
    )


def create_tool_call(
    tool_name: str,
    action: str,
    parameters: Dict[str, Any],
    risk_level: RiskLevel = RiskLevel.LOW,
    narration: Optional[str] = None
) -> ToolCall:
    """Helper pour créer un ToolCall"""
    return ToolCall(
        tool_name=tool_name,
        action=action,
        parameters=parameters,
        risk_level=risk_level,
        requires_confirmation=(risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]),
        narration=narration
    )


# ==================== EXPORT ====================

__all__ = [
    # Enums
    'InteractionType',
    'RiskLevel',
    'ToolStatus',
    'ConsentMode',
    
    # Core Models
    'InteractionEnvelope',
    'ToolCall',
    'SystemPlan',
    'PerceptionEvent',
    'ToolSummary',
    'ConsentPolicy',
    'AuditEntry',
    
    # Prompt
    'PromptContext',
    'LlmPlanSchema',
    'SafeTemplate',
    
    # Helpers
    'create_interaction_envelope',
    'create_tool_call',
]
