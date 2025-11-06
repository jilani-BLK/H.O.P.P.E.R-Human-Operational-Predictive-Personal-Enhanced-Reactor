"""
Plan Schema - Schéma Pydantic pour Plans LLM

Définit la structure des plans JSON générés par le LLM:
- Intent: Intention utilisateur détectée
- Tool Calls: Actions à exécuter via PluginRegistry
- Narration: Message naturel à communiquer
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime


class IntentType(str, Enum):
    """Types d'intentions supportées"""
    QUESTION = "question"                    # Question nécessitant réponse LLM
    SYSTEM_ACTION = "system_action"          # Action système (fichiers, processus)
    EMAIL = "email"                          # Gestion emails
    CALENDAR = "calendar"                    # Gestion agenda
    LEARN = "learn"                          # Mémoriser information
    CONTROL = "control"                      # Contrôle IoT/système
    SEARCH = "search"                        # Recherche information
    GENERAL = "general"                      # Conversation générale
    MULTI_STEP = "multi_step"                # Plusieurs étapes


class RiskLevel(str, Enum):
    """Niveaux de risque des actions"""
    SAFE = "safe"                            # Lecture seule
    LOW = "low"                              # Modifications mineures
    MEDIUM = "medium"                        # Modifications importantes
    HIGH = "high"                            # Suppressions, accès sensible
    CRITICAL = "critical"                    # Actions irréversibles


class ToolCall(BaseModel):
    """
    Appel à un tool dans le plan
    
    Représente une action à exécuter via PluginRegistry
    """
    
    tool_id: str = Field(
        ...,
        description="ID du tool (ex: filesystem, imap_email, caldav)"
    )
    
    capability: str = Field(
        ...,
        description="Nom de la capacité à invoquer (ex: read_file, send_email)"
    )
    
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Paramètres de l'appel"
    )
    
    reasoning: str = Field(
        ...,
        description="Raison de cet appel (pour audit et transparence)"
    )
    
    risk_level: RiskLevel = Field(
        default=RiskLevel.SAFE,
        description="Niveau de risque estimé"
    )
    
    requires_confirmation: bool = Field(
        default=False,
        description="Nécessite confirmation utilisateur explicite"
    )
    
    fallback_if_error: Optional[str] = Field(
        default=None,
        description="Action alternative si échec"
    )
    
    @field_validator('tool_id')
    @classmethod
    def validate_tool_id(cls, v: str) -> str:
        """Valide format tool_id"""
        if not v or not v.replace('_', '').isalnum():
            raise ValueError(f"tool_id invalide: {v}")
        return v
    
    @field_validator('capability')
    @classmethod
    def validate_capability(cls, v: str) -> str:
        """Valide format capability"""
        if not v or not v.replace('_', '').isalnum():
            raise ValueError(f"capability invalide: {v}")
        return v


class Narration(BaseModel):
    """
    Message naturel pour communication utilisateur
    
    Généré par le LLM pour expliquer actions et résultats
    """
    
    message: str = Field(
        ...,
        description="Message principal à communiquer"
    )
    
    tone: str = Field(
        default="neutral",
        description="Ton du message (neutral, friendly, urgent, apologetic)"
    )
    
    should_speak: bool = Field(
        default=False,
        description="Doit être vocalisé via TTS"
    )
    
    urgency: str = Field(
        default="normal",
        description="Urgence (low, normal, high, critical)"
    )
    
    context_hints: List[str] = Field(
        default_factory=list,
        description="Indices contextuels pour améliorer compréhension"
    )
    
    suggested_follow_ups: List[str] = Field(
        default_factory=list,
        description="Questions/actions de suivi suggérées"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Valide que message non vide"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Message ne peut être vide")
        if len(v) > 2000:
            raise ValueError("Message trop long (max 2000 caractères)")
        return v


class ExecutionPlan(BaseModel):
    """
    Plan d'exécution complet généré par le LLM
    
    Structure retournée par LlmFirstDispatcher après analyse
    de la commande utilisateur.
    """
    
    intent: IntentType = Field(
        ...,
        description="Type d'intention détectée"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confiance dans la détection (0-1)"
    )
    
    tool_calls: List[ToolCall] = Field(
        default_factory=list,
        description="Liste des appels tools à exécuter séquentiellement"
    )
    
    narration: Narration = Field(
        ...,
        description="Message à communiquer à l'utilisateur"
    )
    
    requires_context: List[str] = Field(
        default_factory=list,
        description="Éléments de contexte nécessaires (historique, KB, etc.)"
    )
    
    reasoning: str = Field(
        default="",
        description="Raisonnement du LLM (pour debug/audit)"
    )
    
    estimated_duration_seconds: Optional[int] = Field(
        default=None,
        description="Durée estimée d'exécution"
    )
    
    # Métadonnées
    user_id: str = Field(
        default="",
        description="ID utilisateur ayant initié le plan"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de création"
    )
    
    original_query: str = Field(
        default="",
        description="Requête utilisateur originale"
    )
    
    @field_validator('tool_calls')
    @classmethod
    def validate_tool_calls(cls, v: List[ToolCall]) -> List[ToolCall]:
        """Valide liste de tool calls"""
        # Limite raisonnable pour éviter plans trop complexes
        if len(v) > 20:
            raise ValueError("Trop de tool_calls dans le plan (max 20)")
        return v
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Valide confidence entre 0 et 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence doit être entre 0 et 1")
        return v
    
    def has_high_risk_actions(self) -> bool:
        """Vérifie si plan contient actions à haut risque"""
        return any(
            call.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            for call in self.tool_calls
        )
    
    def requires_user_confirmation(self) -> bool:
        """Vérifie si plan nécessite confirmation utilisateur"""
        return any(call.requires_confirmation for call in self.tool_calls)
    
    def get_total_risk_score(self) -> int:
        """
        Calcule score de risque total du plan
        
        Returns:
            Score de 0 (safe) à 4 (critical)
        """
        risk_scores = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        if not self.tool_calls:
            return 0
        
        return max(risk_scores[call.risk_level] for call in self.tool_calls)


class PlanValidationResult(BaseModel):
    """Résultat de validation d'un plan"""
    
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_tools: List[str] = Field(default_factory=list)
    missing_capabilities: List[str] = Field(default_factory=list)
    invalid_parameters: Dict[str, List[str]] = Field(default_factory=dict)


class PlanExecutionResult(BaseModel):
    """Résultat d'exécution d'un plan"""
    
    success: bool
    plan: ExecutionPlan
    
    # Résultats par tool call
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Durée totale
    execution_time_seconds: float = 0.0
    
    # Erreurs
    errors: List[str] = Field(default_factory=list)
    
    # Message final
    final_message: str = ""
    
    # Audit
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def mark_completed(self):
        """Marque l'exécution comme terminée"""
        self.completed_at = datetime.now()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_time_seconds = delta.total_seconds()
