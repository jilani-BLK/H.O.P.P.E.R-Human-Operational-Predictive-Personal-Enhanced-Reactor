"""
HOPPER - Error Tracker
Système de suivi des erreurs avec catégorisation et alertes
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from loguru import logger


class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Catégories d'erreurs"""
    NETWORK = "network"
    DATABASE = "database"
    LLM = "llm"
    STT = "stt"
    TTS = "tts"
    CONNECTOR = "connector"
    AUTHENTICATION = "authentication"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorReport:
    """Rapport d'erreur structuré"""
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    service: str
    error_type: str
    message: str
    traceback: Optional[str] = None
    context: Optional[Dict] = None
    count: int = 1
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = self.timestamp
        if self.last_seen is None:
            self.last_seen = self.timestamp
        if self.context is None:
            self.context = {}


class ErrorTracker:
    """
    Système de suivi des erreurs
    
    Features:
    - Catégorisation automatique
    - Détection de patterns
    - Alertes configurables
    - Agrégation des erreurs similaires
    - Génération de rapports
    """
    
    def __init__(self, storage_path: str = "data/errors"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.errors_file = self.storage_path / "errors.json"
        self.alerts_file = self.storage_path / "alerts.json"
        
        self.errors: Dict[str, ErrorReport] = {}
        self.alerts: List[Dict] = []
        
        # Configuration des seuils d'alerte
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,  # Alerte immédiate
            ErrorSeverity.ERROR: 5,     # Alerte après 5 occurrences
            ErrorSeverity.WARNING: 20,   # Alerte après 20 occurrences
        }
        
        self._load_errors()
        logger.info("🔍 ErrorTracker initialisé")
    
    def _load_errors(self):
        """Charger les erreurs depuis le stockage"""
        if self.errors_file.exists():
            try:
                with open(self.errors_file, 'r') as f:
                    data = json.load(f)
                    for key, error_data in data.items():
                        # Reconvertir en ErrorReport
                        error_data['severity'] = ErrorSeverity(error_data['severity'])
                        error_data['category'] = ErrorCategory(error_data['category'])
                        self.errors[key] = ErrorReport(**error_data)
            except Exception as e:
                logger.error(f"Erreur chargement errors: {e}")
    
    def _save_errors(self):
        """Sauvegarder les erreurs"""
        try:
            data = {}
            for key, error in self.errors.items():
                error_dict = asdict(error)
                error_dict['severity'] = error.severity.value
                error_dict['category'] = error.category.value
                data[key] = error_dict
            
            with open(self.errors_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde errors: {e}")
    
    def _error_key(self, service: str, error_type: str) -> str:
        """Générer clé unique pour une erreur"""
        return f"{service}:{error_type}"
    
    def track_error(
        self,
        service: str,
        error_type: str,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        traceback: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> ErrorReport:
        """
        Enregistrer une erreur
        
        Args:
            service: Service concerné (llm, stt, orchestrator, etc.)
            error_type: Type d'erreur (ConnectionError, TimeoutError, etc.)
            message: Message d'erreur
            severity: Niveau de sévérité
            category: Catégorie d'erreur
            traceback: Stack trace (optionnel)
            context: Contexte additionnel (optionnel)
        
        Returns:
            ErrorReport créé ou mis à jour
        """
        timestamp = datetime.now().isoformat()
        key = self._error_key(service, error_type)
        
        if key in self.errors:
            # Erreur déjà vue, incrémenter count
            error = self.errors[key]
            error.count += 1
            error.last_seen = timestamp
            error.message = message  # Mettre à jour message
            logger.debug(f"Erreur connue {key}: count={error.count}")
        else:
            # Nouvelle erreur
            error = ErrorReport(
                timestamp=timestamp,
                severity=severity,
                category=category,
                service=service,
                error_type=error_type,
                message=message,
                traceback=traceback,
                context=context or {}
            )
            self.errors[key] = error
            logger.info(f"Nouvelle erreur trackée: {key}")
        
        self._save_errors()
        
        # Vérifier si alerte nécessaire
        self._check_alert(error)
        
        return error
    
    def _check_alert(self, error: ErrorReport):
        """Vérifier si une alerte doit être déclenchée"""
        threshold = self.alert_thresholds.get(error.severity, float('inf'))
        
        if error.count >= threshold:
            self._send_alert(error)
    
    def _send_alert(self, error: ErrorReport):
        """Envoyer une alerte"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "error_key": f"{error.service}:{error.error_type}",
            "severity": error.severity.value,
            "category": error.category.value,
            "count": error.count,
            "message": error.message
        }
        
        self.alerts.append(alert)
        
        # Sauvegarder alerts
        try:
            with open(self.alerts_file, 'w') as f:
                json.dump(self.alerts, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde alert: {e}")
        
        # Log l'alerte
        logger.warning(f"🚨 ALERTE: {error.service} - {error.error_type} "
                      f"({error.count} occurrences)")
    
    def get_errors(
        self,
        service: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        min_count: int = 1
    ) -> List[ErrorReport]:
        """
        Récupérer les erreurs filtrées
        
        Args:
            service: Filtrer par service
            severity: Filtrer par sévérité
            category: Filtrer par catégorie
            min_count: Nombre minimum d'occurrences
        
        Returns:
            Liste des erreurs correspondantes
        """
        errors = list(self.errors.values())
        
        if service:
            errors = [e for e in errors if e.service == service]
        
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        if category:
            errors = [e for e in errors if e.category == category]
        
        errors = [e for e in errors if e.count >= min_count]
        
        # Trier par count décroissant
        errors.sort(key=lambda x: x.count, reverse=True)
        
        return errors
    
    def get_top_errors(self, limit: int = 10) -> List[ErrorReport]:
        """Récupérer les erreurs les plus fréquentes"""
        errors = list(self.errors.values())
        errors.sort(key=lambda x: x.count, reverse=True)
        return errors[:limit]
    
    def get_critical_errors(self) -> List[ErrorReport]:
        """Récupérer les erreurs critiques"""
        return self.get_errors(severity=ErrorSeverity.CRITICAL)
    
    def get_stats(self) -> Dict:
        """Générer statistiques sur les erreurs"""
        total_errors = len(self.errors)
        total_occurrences = sum(e.count for e in self.errors.values())
        
        # Par sévérité
        by_severity = {}
        for severity in ErrorSeverity:
            errors = self.get_errors(severity=severity)
            by_severity[severity.value] = {
                "count": len(errors),
                "occurrences": sum(e.count for e in errors)
            }
        
        # Par catégorie
        by_category = {}
        for category in ErrorCategory:
            errors = self.get_errors(category=category)
            by_category[category.value] = {
                "count": len(errors),
                "occurrences": sum(e.count for e in errors)
            }
        
        # Par service
        services = set(e.service for e in self.errors.values())
        by_service = {}
        for service in services:
            errors = self.get_errors(service=service)
            by_service[service] = {
                "count": len(errors),
                "occurrences": sum(e.count for e in errors)
            }
        
        return {
            "total_unique_errors": total_errors,
            "total_occurrences": total_occurrences,
            "by_severity": by_severity,
            "by_category": by_category,
            "by_service": by_service,
            "alerts_sent": len(self.alerts)
        }
    
    def clear_old_errors(self, days: int = 30):
        """Nettoyer les erreurs anciennes"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        errors_to_remove = []
        for key, error in self.errors.items():
            if error.last_seen and error.last_seen < cutoff_str:
                errors_to_remove.append(key)
        
        for key in errors_to_remove:
            del self.errors[key]
        
        self._save_errors()
        logger.info(f"🧹 {len(errors_to_remove)} erreurs anciennes supprimées")
    
    def generate_report(self) -> str:
        """Générer rapport textuel des erreurs"""
        stats = self.get_stats()
        top_errors = self.get_top_errors(10)
        
        report = []
        report.append("=" * 60)
        report.append("📊 RAPPORT D'ERREURS HOPPER")
        report.append("=" * 60)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("📈 STATISTIQUES GLOBALES:")
        report.append(f"  - Total erreurs uniques: {stats['total_unique_errors']}")
        report.append(f"  - Total occurrences: {stats['total_occurrences']}")
        report.append(f"  - Alertes envoyées: {stats['alerts_sent']}")
        report.append("")
        
        report.append("🔴 PAR SÉVÉRITÉ:")
        for severity, data in stats['by_severity'].items():
            if data['count'] > 0:
                report.append(f"  - {severity.upper()}: {data['count']} erreurs "
                            f"({data['occurrences']} occurrences)")
        report.append("")
        
        report.append("📂 PAR CATÉGORIE:")
        for category, data in stats['by_category'].items():
            if data['count'] > 0:
                report.append(f"  - {category}: {data['count']} erreurs "
                            f"({data['occurrences']} occurrences)")
        report.append("")
        
        report.append("🔧 PAR SERVICE:")
        for service, data in stats['by_service'].items():
            report.append(f"  - {service}: {data['count']} erreurs "
                        f"({data['occurrences']} occurrences)")
        report.append("")
        
        report.append("🏆 TOP 10 ERREURS:")
        for i, error in enumerate(top_errors, 1):
            report.append(f"  {i}. [{error.service}] {error.error_type}")
            report.append(f"     Occurrences: {error.count}")
            report.append(f"     Sévérité: {error.severity.value}")
            report.append(f"     Message: {error.message[:80]}...")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


# Instance globale
_error_tracker = None

def get_error_tracker() -> ErrorTracker:
    """Obtenir l'instance globale du tracker"""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker


if __name__ == "__main__":
    # Test du tracker
    tracker = ErrorTracker()
    
    # Simuler quelques erreurs
    tracker.track_error(
        service="llm",
        error_type="ConnectionError",
        message="Cannot connect to Ollama",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.NETWORK
    )
    
    tracker.track_error(
        service="neo4j",
        error_type="TimeoutError",
        message="Query timeout after 30s",
        severity=ErrorSeverity.WARNING,
        category=ErrorCategory.DATABASE
    )
    
    # Simuler erreur récurrente
    for _ in range(6):
        tracker.track_error(
            service="stt",
            error_type="AudioProcessingError",
            message="Failed to process audio file",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.STT
        )
    
    # Erreur critique
    tracker.track_error(
        service="orchestrator",
        error_type="SystemCriticalError",
        message="Main orchestrator crashed",
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.SYSTEM,
        traceback="Traceback (most recent call last):\\n  File main.py..."
    )
    
    # Afficher rapport
    print(tracker.generate_report())
    
    # Afficher stats
    print("\\n📊 Stats JSON:")
    import json
    print(json.dumps(tracker.get_stats(), indent=2))
