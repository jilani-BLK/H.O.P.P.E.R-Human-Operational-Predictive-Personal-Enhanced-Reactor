"""
HOPPER - System Commands Handler
Étend le dispatcher pour détecter et exécuter des commandes système locales
via le service Connectors (Phase 5)

Commandes détectées:
- "ouvre Safari" → open_app
- "ferme Chrome" → close_app
- "lis le fichier README" → read_file
- "liste les applications" → list_apps
- "cherche les fichiers Python" → find_files
- "info système" → get_system_info
"""

import re
from typing import Dict, Any, Optional
from loguru import logger

from connectors_client import get_connectors_client


class SystemCommandsHandler:
    """Détecte et exécute les commandes système via Connectors"""
    
    # Patterns de détection (ordre important: plus spécifique en premier)
    PATTERNS = {
        "system_info": [
            r"info(?:rmations?)?\s+système",
            r"état\s+(?:du\s+)?système",
            r"system\s+info(?:rmations?)?",
            r"show\s+system(?:\s+info)?",
            r"get\s+system\s+info",
        ],
        "list_apps": [
            r"liste\s+(?:les\s+)?applications?",
            r"quelles?\s+applications?",
            r"apps?\s+installées?",
            r"list\s+apps?",
            r"show\s+apps?",
        ],
        "open_app": [
            r"ouvre?\s+(.+)",
            r"lance?\s+(.+)",
            r"démarre?\s+(.+)",
            r"open\s+(.+)",
            r"start\s+(.+)",
        ],
        "close_app": [
            r"ferme?\s+(.+)",
            r"arrête?\s+(.+)",
            r"close\s+(.+)",
            r"quit\s+(.+)",
            r"stop\s+(.+)",
        ],
        "find_files": [
            r"cherche\s+(?:les\s+)?fichiers?\s+(.+)",
            r"trouve\s+(?:les\s+)?fichiers?\s+(.+)",
            r"find\s+files?\s+(.+)",
            r"search\s+files?\s+(.+)",
        ],
        "list_directory": [
            r"liste\s+(?:le\s+)?(?:contenu\s+du\s+)?(?:répertoire\s+)?(.+)",
            r"ls\s+(.+)",
            r"dir\s+(.+)",
            r"list\s+directory\s+(.+)",
        ],
        "read_file": [
            r"lis\s+(?:le\s+)?fichier\s+(.+)",
            r"affiche\s+(?:le\s+)?fichier\s+(.+)",
            r"read\s+(?:file\s+)?(.+)",
            r"cat\s+(.+)",
        ],
    }
    
    def __init__(self):
        self.client = get_connectors_client()
        logger.info("🔧 SystemCommandsHandler initialisé")
    
    def detect(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Détecte si la commande est une commande système locale
        
        Args:
            command: Commande utilisateur
            
        Returns:
            {"action": str, "params": dict} ou None si pas détecté
        """
        command_lower = command.lower().strip()
        
        for action, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, command_lower, re.IGNORECASE)
                if match:
                    params = self._extract_params(action, match)
                    logger.info(f"🎯 Détecté: {action} - {params}")
                    return {
                        "action": action,
                        "params": params
                    }
        
        return None
    
    def _extract_params(self, action: str, match: re.Match) -> Dict[str, Any]:
        """Extraire les paramètres de la regex match"""
        if action in ["open_app", "close_app"]:
            app_name = match.group(1).strip()
            # Nettoyer les articles
            app_name = re.sub(r"^(l'|le |la |les |l )", "", app_name, flags=re.IGNORECASE)
            return {"app_name": app_name}
        
        elif action == "read_file":
            file_path = match.group(1).strip()
            return {"file_path": file_path, "max_lines": 50}
        
        elif action == "list_directory":
            path = match.group(1).strip() if match.groups() else "."
            return {"path": path}
        
        elif action == "find_files":
            pattern = match.group(1).strip()
            return {"pattern": pattern, "directory": "."}
        
        elif action in ["list_apps", "system_info"]:
            return {}
        
        return {}
    
    async def execute(self, action: str, params: Dict[str, Any], user_id: str = "user") -> Dict[str, Any]:
        """
        Exécute une action système via Connectors
        
        Args:
            action: Action à exécuter (open_app, read_file, etc.)
            params: Paramètres de l'action
            user_id: ID utilisateur
            
        Returns:
            {"success": bool, "data": Any, "message": str}
        """
        try:
            logger.info(f"🔄 Exécution: {action} avec {params}")
            
            # Mapping action → méthode client
            method_map = {
                "open_app": self.client.open_app,
                "close_app": self.client.close_app,
                "list_apps": self.client.list_apps,
                "read_file": self.client.read_file,
                "list_directory": self.client.list_directory,
                "find_files": self.client.find_files,
                "system_info": self.client.get_system_info,
            }
            
            method = method_map.get(action)
            if not method:
                return {
                    "success": False,
                    "message": f"Action '{action}' non supportée"
                }
            
            # Exécuter via le client
            result = await method(**params, user_id=user_id)
            
            if result.get("success"):
                # Formater le message de succès
                message = self._format_success_message(action, result.get("data"))
                logger.success(f"✅ {action} réussi")
                return {
                    "success": True,
                    "data": result.get("data"),
                    "message": message
                }
            else:
                error = result.get("error", "Erreur inconnue")
                logger.error(f"❌ {action} échoué: {error}")
                return {
                    "success": False,
                    "message": f"Échec: {error}"
                }
                
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }
    
    def _format_success_message(self, action: str, data: Any) -> str:
        """Formater un message de succès lisible"""
        if action == "open_app":
            return f"✅ Application '{data.get('app_name')}' ouverte"
        
        elif action == "close_app":
            return f"✅ Application fermée"
        
        elif action == "read_file":
            lines = data.get("lines_read", 0)
            truncated = data.get("truncated", False)
            msg = f"✅ Fichier lu ({lines} lignes"
            if truncated:
                msg += ", tronqué"
            msg += ")"
            return msg
        
        elif action == "list_apps":
            count = data.get("count", 0)
            return f"✅ {count} applications trouvées"
        
        elif action == "list_directory":
            count = data.get("count", 0)
            return f"✅ {count} éléments dans le répertoire"
        
        elif action == "find_files":
            count = data.get("count", 0)
            return f"✅ {count} fichiers trouvés"
        
        elif action == "system_info":
            os_info = data.get("os", "Unknown")
            cpu = data.get("cpu_count", 0)
            return f"✅ Système: {os_info}, {cpu} CPU"
        
        return "✅ Action réussie"


# Instance globale
_handler: Optional[SystemCommandsHandler] = None


def get_system_handler() -> SystemCommandsHandler:
    """Obtenir l'instance singleton du handler"""
    global _handler
    if _handler is None:
        _handler = SystemCommandsHandler()
    return _handler
