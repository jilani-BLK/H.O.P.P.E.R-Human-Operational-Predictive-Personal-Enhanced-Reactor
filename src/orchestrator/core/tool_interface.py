"""
Tool Interface - Architecture Modulaire de Plugins

Définit l'interface commune pour tous les outils/connecteurs HOPPER.
Permet au LLM de découvrir et planifier l'usage des tools disponibles.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class AuthMethod(str, Enum):
    """Méthodes d'authentification supportées"""
    NONE = "none"                    # Pas d'auth
    BASIC = "basic"                  # Username/Password
    OAUTH2 = "oauth2"                # OAuth2 flow
    API_KEY = "api_key"              # Clé API
    TOKEN = "token"                  # Bearer token
    CERTIFICATE = "certificate"      # Certificat client
    MFA = "mfa"                      # Multi-factor (TOTP, SMS)
    BIOMETRIC = "biometric"          # Empreinte, Face ID
    KEYCHAIN = "keychain"            # macOS Keychain


class ToolCategory(str, Enum):
    """Catégories de tools"""
    COMMUNICATION = "communication"  # Email, SMS, chat
    CALENDAR = "calendar"            # Calendrier, événements
    FILESYSTEM = "filesystem"        # Fichiers, documents
    SYSTEM = "system"                # Commandes système
    SECURITY = "security"            # Antivirus, firewall
    FINANCE = "finance"              # Banque, cryptomonnaie
    PRODUCTIVITY = "productivity"    # Notes, tâches
    SOCIAL = "social"                # Réseaux sociaux
    IOT = "iot"                      # Domotique, capteurs
    WEB = "web"                      # Navigation, scraping


class ToolCapability(BaseModel):
    """Capacité d'un tool (action disponible)"""
    
    name: str = Field(..., description="Nom technique de l'action (read_email, send_message)")
    display_name: str = Field(..., description="Nom affiché à l'utilisateur")
    description: str = Field(..., description="Description de ce que fait l'action")
    
    parameters: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Paramètres requis/optionnels"
    )
    # Exemple: {
    #   "recipient": {"type": "string", "required": True, "description": "Email destinataire"},
    #   "subject": {"type": "string", "required": True},
    #   "body": {"type": "string", "required": False}
    # }
    
    returns: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structure de retour"
    )
    
    requires_confirmation: bool = Field(
        default=False,
        description="Nécessite confirmation utilisateur avant exécution"
    )
    
    risk_level: str = Field(
        default="safe",
        description="Niveau de risque: safe, low, medium, high, critical"
    )
    
    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Exemples d'utilisation"
    )


class ToolManifest(BaseModel):
    """
    Manifeste déclaratif d'un tool/connecteur
    
    Décrit toutes les métadonnées nécessaires pour que le LLM
    puisse découvrir et utiliser le tool de manière autonome.
    """
    
    # Identification
    tool_id: str = Field(..., description="ID unique du tool (ex: imap_email)")
    name: str = Field(..., description="Nom affiché")
    version: str = Field(..., description="Version sémantique (1.0.0)")
    category: ToolCategory
    
    # Description
    description: str = Field(..., description="Description courte")
    long_description: Optional[str] = Field(None, description="Documentation complète")
    author: Optional[str] = Field(None)
    homepage: Optional[str] = Field(None)
    
    # Capacités
    capabilities: List[ToolCapability] = Field(
        ...,
        description="Liste des actions disponibles"
    )
    
    # Authentification
    auth_method: AuthMethod
    auth_scopes: List[str] = Field(
        default_factory=list,
        description="Scopes/permissions requises"
    )
    credentials_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="Schéma des credentials nécessaires"
    )
    # Exemple: {
    #   "host": {"type": "string", "default": "imap.gmail.com"},
    #   "username": {"type": "string", "required": True},
    #   "password": {"type": "string", "required": True, "secret": True}
    # }
    
    # Configuration
    config_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="Paramètres de configuration optionnels"
    )
    
    # Contraintes
    rate_limits: Optional[Dict[str, int]] = Field(
        None,
        description="Limites de taux (requests_per_minute, etc.)"
    )
    
    requires_internet: bool = Field(default=True)
    requires_system_permissions: List[str] = Field(default_factory=list)
    
    # Métadonnées
    tags: List[str] = Field(default_factory=list)
    is_enabled: bool = Field(default=True)
    is_beta: bool = Field(default=False)


class ToolExecutionContext(BaseModel):
    """Contexte d'exécution d'un tool"""
    
    user_id: str
    session_id: Optional[str] = None
    
    # Consentement
    has_consent: bool = False  # Alias pour consent_given
    consent_given: bool = False
    consent_expires_at: Optional[datetime] = None
    
    # Tracking
    execution_id: Optional[str] = None
    parent_execution_id: Optional[str] = None
    
    # Sécurité
    source: str = Field(default="llm_agent")  # llm_agent, user_command, scheduler
    audit_enabled: bool = Field(default=True)


class ToolExecutionResult(BaseModel):
    """Résultat d'exécution d'un tool"""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Métadonnées
    execution_time_ms: float
    tool_id: str
    capability_name: str
    
    # Audit
    audit_entry_id: Optional[str] = None
    
    # Suggestions
    suggested_next_actions: List[str] = Field(default_factory=list)


class ToolInterface(ABC):
    """
    Interface abstraite que tous les tools doivent implémenter
    
    Permet un chargement dynamique et une découverte automatique
    par le PluginRegistry.
    """
    
    def __init__(self, manifest: ToolManifest, credentials_vault=None):
        self.manifest = manifest
        self.credentials_vault = credentials_vault
        self._is_connected = False
        self._credentials = None
    
    
    @abstractmethod
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Établit la connexion au service externe
        
        Args:
            credentials: Dictionnaire des credentials selon manifest.credentials_schema
            
        Returns:
            True si connexion réussie
            
        Raises:
            AuthenticationError: Si credentials invalides
            ConnectionError: Si service inaccessible
        """
        pass
    
    
    @abstractmethod
    async def disconnect(self):
        """Ferme la connexion proprement"""
        pass
    
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Teste si la connexion est active et valide"""
        pass
    
    
    @abstractmethod
    async def invoke(
        self,
        capability_name: str,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolExecutionResult:
        """
        Invoque une capacité du tool
        
        Args:
            capability_name: Nom de l'action à exécuter
            parameters: Paramètres de l'action
            context: Contexte d'exécution (user, consent, audit)
            
        Returns:
            Résultat de l'exécution
            
        Raises:
            CapabilityNotFoundError: Si capacité inconnue
            ParameterValidationError: Si paramètres invalides
            ExecutionError: Si exécution échoue
        """
        pass
    
    
    def get_manifest(self) -> ToolManifest:
        """Retourne le manifeste du tool"""
        return self.manifest
    
    
    @abstractmethod
    async def validate_parameters(
        self,
        capability_name: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """
        Valide les paramètres avant exécution
        
        Returns:
            True si paramètres valides
            
        Raises:
            ParameterValidationError: Si paramètres invalides
        """
        pass
    
    
    def is_connected(self) -> bool:
        """Vérifie si le tool est connecté"""
        return self._is_connected
    
    
    def get_capabilities_summary(self) -> List[Dict[str, Any]]:
        """
        Retourne résumé des capacités pour le LLM
        
        Format optimisé pour injection dans prompts.
        """
        return [
            {
                "name": cap.name,
                "description": cap.description,
                "parameters": list(cap.parameters.keys()),
                "risk": cap.risk_level,
                "needs_confirmation": cap.requires_confirmation
            }
            for cap in self.manifest.capabilities
        ]


# ============================================
# Exceptions personnalisées
# ============================================

class ToolError(Exception):
    """Exception de base pour erreurs de tools"""
    pass


class AuthenticationError(ToolError):
    """Erreur d'authentification"""
    pass


class ConnectionError(ToolError):
    """Erreur de connexion au service"""
    pass


class CapabilityNotFoundError(ToolError):
    """Capacité inconnue"""
    pass


class ParameterValidationError(ToolError):
    """Paramètres invalides"""
    pass


class ExecutionError(ToolError):
    """Erreur lors de l'exécution"""
    pass


class ConsentRequiredError(ToolError):
    """Consentement utilisateur requis"""
    pass
