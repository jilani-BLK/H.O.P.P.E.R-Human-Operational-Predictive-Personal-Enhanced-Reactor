"""
HOPPER - Système de Permissions et Sécurité
Gestion multi-niveaux des autorisations avec audit complet
"""

import os
import json
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path
from loguru import logger


class PermissionLevel(Enum):
    """Niveaux de permission"""
    READ = "read"              # Lecture seule (safe)
    WRITE = "write"            # Écriture fichiers
    EXECUTE = "execute"        # Exécution commandes/apps
    ADMIN = "admin"            # Actions système sensibles
    DANGER = "danger"          # Actions potentiellement destructives


class ActionRisk(Enum):
    """Niveau de risque d'une action"""
    SAFE = "safe"              # Pas de risque (lecture, list)
    LOW = "low"                # Risque faible (ouvrir app, lire config)
    MEDIUM = "medium"          # Risque moyen (écrire fichier, modifier)
    HIGH = "high"              # Risque élevé (fermer app, exec script)
    CRITICAL = "critical"      # Critique (delete, format, admin)


class SecurityPolicy:
    """
    Politique de sécurité pour HOPPER
    Définit ce qui est autorisé, ce qui nécessite confirmation, etc.
    """
    
    # Actions SAFE - Pas de confirmation nécessaire
    SAFE_ACTIONS = {
        "list_apps", "list_directory", "read_file", "find_files",
        "get_file_info", "get_system_info", "get_running_apps",
        "search", "current"  # Spotify
    }
    
    # Actions nécessitant confirmation
    REQUIRES_CONFIRMATION = {
        "open_app", "close_app", "execute_script", "minimize_app",
        "focus_app", "play", "pause", "skip", "volume"
    }
    
    # Actions DANGER - Toujours confirmées + loggées
    DANGER_ACTIONS = {
        "delete_file", "format_disk", "shutdown", "reboot",
        "kill_process", "modify_system"
    }
    
    # Extensions fichiers safe à lire
    SAFE_FILE_EXTENSIONS = {
        ".txt", ".md", ".json", ".yaml", ".yml", ".toml", ".ini",
        ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go",
        ".rs", ".sh", ".bash", ".zsh", ".fish",
        ".html", ".css", ".scss", ".xml", ".svg",
        ".log", ".conf", ".config", ".env"
    }
    
    # Répertoires système protégés (lecture OK, écriture NON)
    PROTECTED_DIRECTORIES = {
        "/System", "/Library/System", "/private/var/db",
        "/bin", "/sbin", "/usr/bin", "/usr/sbin"
    }
    
    # Commandes shell whitelistées
    SAFE_COMMANDS = [
        "ls", "pwd", "echo", "date", "whoami", "hostname",
        "cat", "head", "tail", "grep", "find", "wc", "sort",
        "df", "du", "ps", "top", "uptime", "uname"
    ]
    
    # Commandes nécessitant confirmation
    MODERATE_COMMANDS = [
        "open", "mkdir", "touch", "cp", "mv", "chmod",
        "git", "npm", "pip", "brew"
    ]
    
    # Commandes INTERDITES
    BANNED_COMMANDS = [
        "rm", "rmdir", "dd", "mkfs", "fdisk", "shutdown",
        "reboot", "halt", "kill", "killall", "pkill",
        "sudo", "su"
    ]


class AuditLogger:
    """
    Logger d'audit pour tracer toutes les actions
    Format: timestamp | user | action | risk | status | details
    """
    
    def __init__(self, log_dir: Path = Path("data/logs/audit")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.json"
    
    def log_action(
        self,
        user_id: str,
        action: str,
        risk: ActionRisk,
        status: str,
        details: Dict[str, Any],
        confirmation_required: bool = False,
        confirmed: bool = False
    ):
        """Enregistre une action dans l'audit"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "risk": risk.value,
            "status": status,
            "confirmation_required": confirmation_required,
            "confirmed": confirmed,
            "details": details
        }
        
        # Append au fichier JSON (une ligne par entrée)
        with open(self.audit_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Logger aussi avec loguru
        emoji = "✅" if status == "success" else "❌"
        risk_emoji = {
            ActionRisk.SAFE: "🟢",
            ActionRisk.LOW: "🟡",
            ActionRisk.MEDIUM: "🟠",
            ActionRisk.HIGH: "🔴",
            ActionRisk.CRITICAL: "💀"
        }
        
        logger.info(
            f"{emoji} {risk_emoji[risk]} [{user_id}] {action} "
            f"| Risk: {risk.value} | Status: {status}"
        )
    
    def get_recent_actions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les dernières actions"""
        if not self.audit_file.exists():
            return []
        
        actions = []
        with open(self.audit_file, "r") as f:
            for line in f:
                actions.append(json.loads(line))
        
        return actions[-limit:]
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Statistiques d'un utilisateur"""
        actions = self.get_recent_actions(1000)
        user_actions = [a for a in actions if a["user_id"] == user_id]
        
        if not user_actions:
            return {"total": 0}
        
        return {
            "total": len(user_actions),
            "by_risk": {
                risk.value: len([a for a in user_actions if a["risk"] == risk.value])
                for risk in ActionRisk
            },
            "success_rate": len([a for a in user_actions if a["status"] == "success"]) / len(user_actions),
            "last_action": user_actions[-1]["timestamp"]
        }


class PermissionManager:
    """
    Gestionnaire de permissions
    Vérifie si une action est autorisée, nécessite confirmation, etc.
    """
    
    def __init__(self):
        self.policy = SecurityPolicy()
        self.audit = AuditLogger()
    
    def check_permission(
        self,
        user_id: str,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Vérifie si une action est autorisée
        
        Returns:
            {
                "allowed": bool,
                "risk": ActionRisk,
                "requires_confirmation": bool,
                "reason": str
            }
        """
        # VÉRIFIER PARAMÈTRES EN PREMIER (commandes bannies dans scripts, etc.)
        param_check = self._check_params_safety(action, params)
        if not param_check["safe"]:
            return {
                "allowed": False,
                "risk": ActionRisk.CRITICAL,
                "requires_confirmation": False,
                "reason": f"⛔ BLOQUÉ: {param_check['reason']}"
            }
        
        # Déterminer le niveau de risque
        risk = self._assess_risk(action, params)
        
        # Actions DANGER complètement interdites
        if action in self.policy.DANGER_ACTIONS:
            return {
                "allowed": False,
                "risk": ActionRisk.CRITICAL,
                "requires_confirmation": False,
                "reason": f"⛔ Action INTERDITE: '{action}' - Trop dangereuse"
            }
        
        # Actions nécessitant confirmation
        if action in self.policy.REQUIRES_CONFIRMATION:
            return {
                "allowed": True,
                "risk": risk,
                "requires_confirmation": True,
                "reason": f"Action '{action}' nécessite confirmation utilisateur"
            }
        
        # Actions SAFE
        if action in self.policy.SAFE_ACTIONS:
            return {
                "allowed": True,
                "risk": ActionRisk.SAFE,
                "requires_confirmation": False,
                "reason": "Action safe, pas de confirmation nécessaire"
            }
        
        # Par défaut: demander confirmation
        return {
            "allowed": True,
            "risk": ActionRisk.MEDIUM,
            "requires_confirmation": True,
            "reason": f"Action inconnue '{action}', confirmation par sécurité"
        }
    
    def _assess_risk(self, action: str, params: Dict[str, Any]) -> ActionRisk:
        """Évalue le niveau de risque d'une action"""
        # CRITICAL
        if action in self.policy.DANGER_ACTIONS:
            return ActionRisk.CRITICAL
        
        # HIGH
        if action in ["execute_script", "close_app", "kill_process"]:
            return ActionRisk.HIGH
        
        # MEDIUM
        if action in self.policy.REQUIRES_CONFIRMATION:
            return ActionRisk.MEDIUM
        
        # LOW
        if action in ["open_app", "read_file"]:
            # Vérifier les paramètres
            if action == "read_file":
                file_path = params.get("file_path", "")
                if any(protected in file_path for protected in self.policy.PROTECTED_DIRECTORIES):
                    return ActionRisk.MEDIUM
            return ActionRisk.LOW
        
        # SAFE par défaut pour les actions de lecture
        if action.startswith("get_") or action.startswith("list_"):
            return ActionRisk.SAFE
        
        return ActionRisk.MEDIUM
    
    def _check_params_safety(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie la sécurité des paramètres"""
        # Lecture de fichiers
        if action == "read_file":
            file_path = params.get("file_path", "")
            
            # Vérifier extension
            ext = Path(file_path).suffix.lower()
            if ext and ext not in self.policy.SAFE_FILE_EXTENSIONS:
                return {
                    "safe": False,
                    "reason": f"Extension '{ext}' non autorisée pour lecture automatique"
                }
            
            # Vérifier répertoires système
            for protected in self.policy.PROTECTED_DIRECTORIES:
                if file_path.startswith(protected):
                    return {
                        "safe": False,
                        "reason": f"Répertoire système protégé: {protected}"
                    }
        
        # Exécution de scripts
        if action == "execute_script":
            script = params.get("script", "")
            script_lower = script.lower()
            
            # Vérifier commandes bannies (détection comme mot séparé, pas substring)
            import re
            for banned in self.policy.BANNED_COMMANDS:
                # Chercher comme mot complet: début de ligne, espace, pipe, semicolon, etc.
                pattern = rf"(^|\s|;|\||&){banned}(\s|;|\||&|$)"
                if re.search(pattern, script_lower):
                    return {
                        "safe": False,
                        "reason": f"⛔ Commande interdite: '{banned}' dans script"
                    }
        
        return {"safe": True, "reason": "Paramètres OK"}
    
    def log_action_result(
        self,
        user_id: str,
        action: str,
        risk: ActionRisk,
        status: str,
        params: Dict[str, Any],
        result: Any = None,
        error: Optional[str] = None
    ):
        """Log le résultat d'une action"""
        details = {
            "params": params,
            "result": str(result)[:200] if result else None,
            "error": error
        }
        
        self.audit.log_action(
            user_id=user_id,
            action=action,
            risk=risk,
            status=status,
            details=details
        )
    
    def get_security_report(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Génère un rapport de sécurité"""
        if user_id:
            return {
                "user_id": user_id,
                "stats": self.audit.get_user_stats(user_id)
            }
        
        # Rapport global
        recent = self.audit.get_recent_actions(1000)
        
        return {
            "total_actions": len(recent),
            "by_risk": {
                risk.value: len([a for a in recent if a["risk"] == risk.value])
                for risk in ActionRisk
            },
            "success_rate": len([a for a in recent if a["status"] == "success"]) / len(recent) if recent else 0,
            "top_users": self._get_top_users(recent)
        }
    
    def _get_top_users(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Top utilisateurs par nombre d'actions"""
        user_counts = {}
        for action in actions:
            user = action["user_id"]
            user_counts[user] = user_counts.get(user, 0) + 1
        
        return [
            {"user_id": user, "actions": count}
            for user, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        ][:10]


# Instance globale
permission_manager = PermissionManager()
