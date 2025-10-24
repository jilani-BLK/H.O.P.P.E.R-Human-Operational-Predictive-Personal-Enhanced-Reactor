"""
Gestionnaire des préférences utilisateur - Phase 4
Charge, valide et applique les préférences de configuration
"""

import yaml
import os
from datetime import datetime, time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import json


@dataclass
class UserPreferences:
    """Classe pour stocker les préférences utilisateur"""
    
    # Informations de base
    user_name: str = "Utilisateur"
    timezone: str = "Europe/Paris"
    language: str = "fr"
    
    # Modes
    night_mode_enabled: bool = True
    night_mode_start: str = "22:00"
    night_mode_end: str = "07:00"
    work_mode_enabled: bool = False
    
    # Notifications
    vip_contacts: List[str] = field(default_factory=list)
    urgent_keywords: List[str] = field(default_factory=list)
    notification_batch_delay: int = 5
    
    # Communication
    verbosity: str = "balanced"  # concise | balanced | detailed
    tone: str = "professional"   # casual | professional | friendly
    
    # Sécurité
    voice_auth_enabled: bool = False
    require_confirmation_commands: List[str] = field(default_factory=list)
    
    # Apprentissage
    collect_conversations: bool = True
    anonymize_data: bool = True
    request_daily_feedback: bool = True
    feedback_time: str = "20:00"
    
    # Limites
    max_llm_requests_per_hour: int = 60
    max_context_messages: int = 20
    
    # Métriques
    track_satisfaction: bool = True
    satisfaction_threshold: float = 3.0


class PreferencesManager:
    """Gestionnaire des préférences utilisateur"""
    
    def __init__(self, config_path: str | None = None):
        """
        Initialise le gestionnaire de préférences
        
        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
        """
        if config_path is None:
            # Chemin par défaut
            project_root = Path(__file__).parent.parent.parent
            config_path_obj = project_root / "config" / "user_preferences" / "default_preferences.yaml"
            self.config_path = config_path_obj
        else:
            self.config_path = Path(config_path)
        self.preferences: Optional[UserPreferences] = None
        self.raw_config: Dict[str, Any] = {}
        
        # Charger les préférences
        self.load_preferences()
    
    def load_preferences(self) -> UserPreferences:
        """
        Charge les préférences depuis le fichier YAML
        
        Returns:
            UserPreferences object
        """
        try:
            if not self.config_path.exists():
                print(f"⚠️  Fichier de préférences non trouvé: {self.config_path}")
                print("📝 Création des préférences par défaut...")
                self.preferences = UserPreferences()
                self.save_preferences()
                return self.preferences
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.raw_config = yaml.safe_load(f)
            
            # Extraire et valider les préférences
            self.preferences = self._parse_config(self.raw_config)
            
            print(f"✅ Préférences chargées depuis {self.config_path}")
            return self.preferences
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des préférences: {e}")
            # Retourner préférences par défaut
            self.preferences = UserPreferences()
            return self.preferences
    
    def _parse_config(self, config: Dict[str, Any]) -> UserPreferences:
        """Parse le fichier YAML en objet UserPreferences"""
        
        return UserPreferences(
            # User info
            user_name=config.get('user', {}).get('name', 'Utilisateur'),
            timezone=config.get('user', {}).get('timezone', 'Europe/Paris'),
            language=config.get('user', {}).get('language', 'fr'),
            
            # Modes
            night_mode_enabled=config.get('modes', {}).get('night_mode', {}).get('enabled', True),
            night_mode_start=config.get('modes', {}).get('night_mode', {}).get('start_time', '22:00'),
            night_mode_end=config.get('modes', {}).get('night_mode', {}).get('end_time', '07:00'),
            work_mode_enabled=config.get('modes', {}).get('work_mode', {}).get('enabled', False),
            
            # Notifications
            vip_contacts=config.get('notifications', {}).get('vip_contacts', []),
            urgent_keywords=config.get('notifications', {}).get('urgent_keywords', []),
            notification_batch_delay=config.get('notifications', {}).get('batch_delay', 5),
            
            # Communication
            verbosity=config.get('communication', {}).get('verbosity', 'balanced'),
            tone=config.get('communication', {}).get('tone', 'professional'),
            
            # Sécurité
            voice_auth_enabled=config.get('security', {}).get('voice_auth', {}).get('enabled', False),
            require_confirmation_commands=config.get('security', {}).get('require_confirmation', []),
            
            # Apprentissage
            collect_conversations=config.get('learning', {}).get('collect_conversations', True),
            anonymize_data=config.get('learning', {}).get('anonymize_data', True),
            request_daily_feedback=config.get('learning', {}).get('request_daily_feedback', True),
            feedback_time=config.get('learning', {}).get('feedback_time', '20:00'),
            
            # Limites
            max_llm_requests_per_hour=config.get('limits', {}).get('max_llm_requests_per_hour', 60),
            max_context_messages=config.get('limits', {}).get('max_context_messages', 20),
            
            # Métriques
            track_satisfaction=config.get('monitoring', {}).get('track_satisfaction', True),
            satisfaction_threshold=config.get('monitoring', {}).get('satisfaction_threshold', 3.0),
        )
    
    def save_preferences(self) -> bool:
        """
        Sauvegarde les préférences dans le fichier YAML
        
        Returns:
            True si succès
        """
        try:
            # Créer le dossier si nécessaire
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Si raw_config vide, créer structure de base
            if not self.raw_config and self.preferences:
                self.raw_config = self._preferences_to_dict()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.raw_config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ Préférences sauvegardées dans {self.config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des préférences: {e}")
            return False
    
    def _preferences_to_dict(self) -> Dict[str, Any]:
        """Convertit UserPreferences en dictionnaire pour YAML"""
        if not self.preferences:
            return {}
        
        return {
            'user': {
                'name': self.preferences.user_name,
                'timezone': self.preferences.timezone,
                'language': self.preferences.language,
            },
            'modes': {
                'night_mode': {
                    'enabled': self.preferences.night_mode_enabled,
                    'start_time': self.preferences.night_mode_start,
                    'end_time': self.preferences.night_mode_end,
                }
            },
            'notifications': {
                'vip_contacts': self.preferences.vip_contacts,
                'urgent_keywords': self.preferences.urgent_keywords,
                'batch_delay': self.preferences.notification_batch_delay,
            },
            'communication': {
                'verbosity': self.preferences.verbosity,
                'tone': self.preferences.tone,
            },
            'learning': {
                'collect_conversations': self.preferences.collect_conversations,
                'anonymize_data': self.preferences.anonymize_data,
                'request_daily_feedback': self.preferences.request_daily_feedback,
                'feedback_time': self.preferences.feedback_time,
            }
        }
    
    def is_night_mode_active(self) -> bool:
        """
        Vérifie si le mode nuit est actif en ce moment
        
        Returns:
            True si mode nuit actif
        """
        if not self.preferences or not self.preferences.night_mode_enabled:
            return False
        
        try:
            now = datetime.now().time()
            start = datetime.strptime(self.preferences.night_mode_start, "%H:%M").time()
            end = datetime.strptime(self.preferences.night_mode_end, "%H:%M").time()
            
            # Gérer le cas où la période traverse minuit
            if start <= end:
                return start <= now <= end
            else:
                return now >= start or now <= end
                
        except Exception as e:
            print(f"⚠️  Erreur vérification mode nuit: {e}")
            return False
    
    def should_notify(self, priority: str = "medium", contact: Optional[str] = None, 
                     content: Optional[str] = None) -> bool:
        """
        Détermine si une notification doit être envoyée
        
        Args:
            priority: Priorité (urgent, high, medium, low)
            contact: Contact source (pour VIP)
            content: Contenu pour détecter mots-clés urgents
            
        Returns:
            True si notification doit être envoyée
        """
        if not self.preferences:
            return True  # Par défaut, toujours notifier
        
        # Mode nuit actif
        if self.is_night_mode_active():
            # Vérifier si urgent ou VIP
            if priority == "urgent":
                return True
            if contact and contact in self.preferences.vip_contacts:
                return True
            if content and any(kw in content.lower() for kw in self.preferences.urgent_keywords):
                return True
            return False  # Bloquer les autres en mode nuit
        
        # Hors mode nuit, vérifier la priorité
        return priority in ["urgent", "high", "medium"]
    
    def get_verbosity_level(self) -> str:
        """Retourne le niveau de verbosité configuré"""
        return self.preferences.verbosity if self.preferences else "balanced"
    
    def requires_confirmation(self, command: str) -> bool:
        """
        Vérifie si une commande nécessite confirmation
        
        Args:
            command: Commande à vérifier
            
        Returns:
            True si confirmation requise
        """
        if not self.preferences:
            return False
        
        # Vérifier si la commande est dans la liste
        for blocked_cmd in self.preferences.require_confirmation_commands:
            if blocked_cmd.lower() in command.lower():
                return True
        
        return False
    
    def update_preference(self, key: str, value: Any) -> bool:
        """
        Met à jour une préférence spécifique
        
        Args:
            key: Clé de la préférence (ex: "night_mode_enabled")
            value: Nouvelle valeur
            
        Returns:
            True si mise à jour réussie
        """
        if not self.preferences:
            return False
        
        try:
            if hasattr(self.preferences, key):
                setattr(self.preferences, key, value)
                self.save_preferences()
                print(f"✅ Préférence '{key}' mise à jour: {value}")
                return True
            else:
                print(f"⚠️  Préférence inconnue: {key}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur mise à jour préférence: {e}")
            return False
    
    def get_summary(self) -> str:
        """Retourne un résumé des préférences actives"""
        if not self.preferences:
            return "Aucune préférence chargée"
        
        summary = f"""
📋 Préférences HOPPER - {self.preferences.user_name}

🌙 Mode nuit: {'✅ Activé' if self.preferences.night_mode_enabled else '❌ Désactivé'}
   {self.preferences.night_mode_start} - {self.preferences.night_mode_end}

🔔 Notifications:
   VIP: {len(self.preferences.vip_contacts)} contacts
   Mots-clés urgents: {len(self.preferences.urgent_keywords)}

💬 Communication:
   Verbosité: {self.preferences.verbosity}
   Ton: {self.preferences.tone}

📚 Apprentissage:
   Collecte: {'✅' if self.preferences.collect_conversations else '❌'}
   Feedback quotidien: {'✅' if self.preferences.request_daily_feedback else '❌'}

🔒 Sécurité:
   Auth vocale: {'✅' if self.preferences.voice_auth_enabled else '❌'}
   Confirmations: {len(self.preferences.require_confirmation_commands)} commandes
        """
        return summary.strip()


# Test du module
if __name__ == "__main__":
    print("="*60)
    print("TEST GESTIONNAIRE DE PRÉFÉRENCES")
    print("="*60)
    
    # Créer gestionnaire
    manager = PreferencesManager()
    
    # Afficher résumé
    print("\n" + manager.get_summary())
    
    # Tester mode nuit
    print("\n🌙 Mode nuit actif:", manager.is_night_mode_active())
    
    # Tester notifications
    print("\n🔔 Tests notifications:")
    print(f"  Medium (normal): {manager.should_notify('medium')}")
    print(f"  Urgent: {manager.should_notify('urgent')}")
    print(f"  VIP contact: {manager.should_notify('medium', contact='famille')}")
    
    # Tester verbosité
    print(f"\n💬 Niveau verbosité: {manager.get_verbosity_level()}")
    
    # Tester confirmation
    print(f"\n🔒 Confirmation 'delete file': {manager.requires_confirmation('delete file')}")
    
    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)
