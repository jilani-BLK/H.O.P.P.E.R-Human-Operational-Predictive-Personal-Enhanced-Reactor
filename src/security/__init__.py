"""
HOPPER - Module de Sécurité
Gestion des permissions, confirmations, audit et détection de malwares
"""

from .permissions import (
    PermissionLevel,
    ActionRisk,
    SecurityPolicy,
    AuditLogger,
    PermissionManager,
    permission_manager
)

from .confirmation import (
    ConfirmationRequest,
    ConfirmationEngine,
    confirmation_engine
)

from .malware_detector import (
    MalwareDetector,
    ThreatReport,
    ThreatLevel,
    DetectionMethod,
    MalwareSignature,
    SignatureDatabase,
    MLMalwareDetector,
    HeuristicAnalyzer
)

__all__ = [
    "PermissionLevel",
    "ActionRisk",
    "SecurityPolicy",
    "AuditLogger",
    "PermissionManager",
    "permission_manager",
    "ConfirmationRequest",
    "ConfirmationEngine",
    "confirmation_engine",
    "MalwareDetector",
    "ThreatReport",
    "ThreatLevel",
    "DetectionMethod",
    "MalwareSignature",
    "SignatureDatabase",
    "MLMalwareDetector",
    "HeuristicAnalyzer"
]
