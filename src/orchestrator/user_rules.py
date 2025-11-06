"""
HOPPER - User Rules Manager (Phase 4)
Gestion des règles personnalisées utilisateur

Charge et applique les règles depuis config/user_rules.yaml:
- Heures de silence
- VIP contacts
- Préférences notifications
- Comportement LLM
- Sécurité
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, time as dt_time
from loguru import logger


class UserRulesManager:
    """Gestionnaire des règles utilisateur"""
    
    def __init__(self, config_path: str = "config/user_rules.yaml"):
        """
        Initialise le gestionnaire
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        self.config_path = Path(config_path)
        self.rules: Dict[str, Any] = {}
        self.load_rules()
        
        logger.info(f"⚙️ UserRulesManager initialisé: {self.config_path}")
    
    def load_rules(self) -> None:
        """Charger les règles depuis le fichier YAML"""
        try:
            if not self.config_path.exists():
                logger.warning(f"⚠️ Fichier de règles non trouvé: {self.config_path}")
                self.rules = self._get_default_rules()
                return
            
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.rules = yaml.safe_load(f)
            
            logger.success(f"✅ Règles chargées: {len(self.rules)} sections")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement règles: {e}")
            self.rules = self._get_default_rules()
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """Règles par défaut si fichier absent"""
        return {
            "user": {"name": "User", "language": "fr"},
            "quiet_hours": {"enabled": False},
            "vip_contacts": {"enabled": False},
            "notifications": {"email": {"enabled": False}, "voice": {"enabled": True}},
            "llm_preferences": {"max_response_length": 300, "temperature": 0.7},
            "security": {"dev_mode": True},
            "learning": {"collect_conversations": True}
        }
    
    # === Heures de Silence ===
    
    def is_quiet_hours(self) -> bool:
        """Vérifier si on est en heures de silence"""
        if not self.rules.get("quiet_hours", {}).get("enabled", False):
            return False
        
        now = datetime.now()
        current_time = now.time()
        is_weekend = now.weekday() >= 5  # Samedi=5, Dimanche=6
        
        # Récupérer plage horaire
        quiet_config = self.rules["quiet_hours"]
        schedule = quiet_config.get("weekends" if is_weekend else "weekdays", {})
        
        start_str = schedule.get("start", "22:00")
        end_str = schedule.get("end", "08:00")
        
        # Convertir en time
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        
        # Gérer période minuit (ex: 22h -> 8h)
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        else:
            return start_time <= current_time <= end_time
    
    def is_action_allowed_during_quiet(self, action: str) -> bool:
        """Vérifier si une action est autorisée pendant heures silence"""
        if not self.is_quiet_hours():
            return True
        
        allowed = self.rules.get("quiet_hours", {}).get("allowed_actions", [])
        return action in allowed
    
    # === VIP Contacts ===
    
    def is_vip_contact(self, email: str) -> bool:
        """Vérifier si un email est VIP"""
        if not self.rules.get("vip_contacts", {}).get("enabled", False):
            return False
        
        vip_emails = self.rules["vip_contacts"].get("emails", [])
        return email.lower() in [v.lower() for v in vip_emails]
    
    def contains_vip_keyword(self, text: str) -> bool:
        """Vérifier si le texte contient un mot-clé VIP"""
        if not self.rules.get("vip_contacts", {}).get("enabled", False):
            return False
        
        keywords = self.rules["vip_contacts"].get("keywords", [])
        text_upper = text.upper()
        return any(keyword.upper() in text_upper for keyword in keywords)
    
    # === Préférences Notifications ===
    
    def should_notify_email(self, priority_score: float) -> bool:
        """Décider si on doit notifier un email"""
        if not self.rules.get("notifications", {}).get("email", {}).get("enabled", False):
            return False
        
        threshold = self.rules["notifications"]["email"].get("priority_threshold", 7)
        return priority_score >= threshold
    
    # === Comportement LLM ===
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Obtenir la configuration LLM préférée"""
        return self.rules.get("llm_preferences", {
            "max_response_length": 300,
            "temperature": 0.7,
            "style": "concise"
        })
    
    # === Sécurité ===
    
    def is_dev_mode(self) -> bool:
        """Vérifier si le mode dev est actif"""
        return self.rules.get("security", {}).get("dev_mode", False)
    
    def requires_confirmation(self, action: str) -> bool:
        """Vérifier si une action nécessite confirmation"""
        if self.is_dev_mode():
            return False  # Bypass en mode dev
        
        actions = self.rules.get("security", {}).get("require_confirmation", [])
        return action in actions
    
    def is_command_banned(self, command: str) -> bool:
        """Vérifier si une commande est bannie"""
        banned = self.rules.get("security", {}).get("banned_commands", [])
        command_lower = command.lower()
        return any(banned_cmd.lower() in command_lower for banned_cmd in banned)
    
    def is_directory_protected(self, path: str) -> bool:
        """Vérifier si un répertoire est protégé"""
        protected = self.rules.get("security", {}).get("protected_directories", [])
        return any(path.startswith(protected_dir) for protected_dir in protected)
    
    # === Limites ===
    
    def get_limit(self, limit_name: str, default: Any = None) -> Any:
        """Obtenir une limite configurée"""
        return self.rules.get("limits", {}).get(limit_name, default)
    
    # === Intégrations ===
    
    def is_integration_enabled(self, integration_name: str) -> bool:
        """Vérifier si une intégration est activée"""
        return self.rules.get("integrations", {}).get(integration_name, {}).get("enabled", False)
    
    # === Apprentissage ===
    
    def should_collect_conversations(self) -> bool:
        """Vérifier si on doit collecter les conversations"""
        return self.rules.get("learning", {}).get("collect_conversations", True)
    
    def should_request_feedback(self) -> bool:
        """Vérifier si on doit demander du feedback"""
        return self.rules.get("learning", {}).get("request_feedback", False)
    
    # === Utils ===
    
    def get_rule(self, path: str, default: Any = None) -> Any:
        """
        Obtenir une règle par chemin (dot notation)
        
        Exemple:
            get_rule("notifications.email.enabled") → True/False
        """
        keys = path.split(".")
        value = self.rules
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        
        return value if value is not None else default
    
    def reload(self) -> None:
        """Recharger les règles depuis le fichier"""
        logger.info("🔄 Rechargement des règles...")
        self.load_rules()


# Instance globale (singleton)
_manager: Optional[UserRulesManager] = None


def get_rules_manager() -> UserRulesManager:
    """Obtenir l'instance singleton du gestionnaire"""
    global _manager
    if _manager is None:
        _manager = UserRulesManager()
    return _manager
