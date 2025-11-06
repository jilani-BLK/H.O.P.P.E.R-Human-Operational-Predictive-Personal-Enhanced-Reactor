"""
HOPPER - Connecteur Système Local
Contrôle total des applications et fichiers de la machine
AVEC SÉCURITÉ: Permissions, Audit, Confirmation

VERSION 2.0: ARCHITECTURE CROSS-PLATFORM
Utilise le pattern Adapter pour supporter macOS / Windows / Linux
"""

import os
import subprocess
import platform
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

from base import BaseConnector, ConnectorConfig, ConnectorCapability
try:
    from src.security import permission_manager, confirmation_engine, ActionRisk
except ImportError:
    permission_manager = None
    confirmation_engine = None
    ActionRisk = None
try:
    from src.connectors.adapters.factory import get_system_adapter
    from src.connectors.adapters.base import SystemAdapter
except ImportError:
    from adapters.factory import get_system_adapter
    from adapters.base import SystemAdapter


class LocalSystemConnector(BaseConnector):
    """
    Connecteur pour contrôler le système local
    
    🌐 CROSS-PLATFORM:
    - ✅ macOS: AppleScript, Automator
    - 🔄 Windows: PowerShell, Win32 API (à venir)
    - 🔄 Linux: D-Bus, xdotool, wmctrl (à venir)
    
    Capacités:
    - Ouvrir/fermer applications
    - Lire fichiers (texte, code, logs)
    - Manipuler fenêtres (focus, resize, minimize)
    - Exécuter scripts/commandes
    - Lister applications installées
    - Explorer filesystem
    - Extraire métadonnées fichiers
    
    Architecture:
        LocalSystemConnector (API publique)
            → SystemAdapter (interface abstraite)
                → MacOSAdapter / WindowsAdapter / LinuxAdapter
    """
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        
        # Détection automatique de l'OS et initialisation de l'adapter
        try:
            self.adapter = get_system_adapter()
            logger.success(f"✅ Adapter initialisé: {self.adapter.__class__.__name__}")
        except Exception as e:
            logger.error(f"❌ Impossible d'initialiser adapter: {e}")
            self.adapter: Optional[SystemAdapter] = None
        
        self.system = platform.system()
        self.applications_dir = self._get_applications_dir()
        self.installed_apps = []
    
    def _get_applications_dir(self) -> Path:
        """Retourne le répertoire des applications selon l'OS"""
        if self.system == "Darwin":  # macOS
            return Path("/Applications")
        elif self.system == "Linux":
            return Path("/usr/share/applications")
        elif self.system == "Windows":
            return Path("C:/Program Files")
        return Path("/")
    
    async def connect(self) -> bool:
        """Initialise la connexion"""
        try:
            # Scanner les applications installées
            self.installed_apps = self._scan_applications()
            
            self.connected = True
            self.clear_error()
            logger.success(f"✅ [{self.name}] Connecté - {len(self.installed_apps)} apps détectées")
            return True
            
        except Exception as e:
            self.set_error(f"Erreur connexion: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Ferme la connexion"""
        self.connected = False
        logger.info(f"🔌 [{self.name}] Déconnecté")
        return True
    
    def _scan_applications(self) -> List[str]:
        """Scanne les applications installées"""
        apps = []
        
        if self.system == "Darwin":  # macOS
            if self.applications_dir.exists():
                apps = [
                    app.stem  # Enlever .app
                    for app in self.applications_dir.glob("*.app")
                ]
        
        logger.info(f"📱 {len(apps)} applications détectées")
        return sorted(apps)
    
    def get_capabilities(self) -> List[ConnectorCapability]:
        """Liste des capacités système"""
        return [
            ConnectorCapability(
                name="open_app",
                description="Ouvrir une application",
                parameters={"app_name": "str"}
            ),
            ConnectorCapability(
                name="close_app",
                description="Fermer une application",
                parameters={"app_name": "str"}
            ),
            ConnectorCapability(
                name="list_apps",
                description="Lister toutes les applications installées"
            ),
            ConnectorCapability(
                name="read_file",
                description="Lire le contenu d'un fichier",
                parameters={"file_path": "str", "max_lines": "Optional[int]"}
            ),
            ConnectorCapability(
                name="list_directory",
                description="Lister le contenu d'un répertoire",
                parameters={"path": "str", "recursive": "bool"}
            ),
            ConnectorCapability(
                name="find_files",
                description="Rechercher des fichiers par nom/extension",
                parameters={"pattern": "str", "directory": "str"}
            ),
            ConnectorCapability(
                name="get_file_info",
                description="Obtenir métadonnées d'un fichier (taille, date, type)",
                parameters={"file_path": "str"}
            ),
            ConnectorCapability(
                name="execute_script",
                description="Exécuter un script shell/AppleScript",
                parameters={"script": "str", "script_type": "shell|applescript"}
            ),
            ConnectorCapability(
                name="get_running_apps",
                description="Lister les applications en cours d'exécution"
            ),
            ConnectorCapability(
                name="focus_app",
                description="Mettre le focus sur une application",
                parameters={"app_name": "str"}
            ),
            ConnectorCapability(
                name="minimize_app",
                description="Minimiser une application",
                parameters={"app_name": "str"}
            ),
            ConnectorCapability(
                name="get_system_info",
                description="Informations système (OS, CPU, RAM, disque)"
            )
        ]
    
    async def execute(self, action: str, params: Dict[str, Any], user_id: str = "default") -> Dict[str, Any]:
        """
        Exécute une action système AVEC SÉCURITÉ
        
        1. Vérifier permissions
        2. Demander confirmation si nécessaire
        3. Logger dans audit
        4. Exécuter action
        5. Logger résultat
        """
        if not self.connected:
            return {"success": False, "error": "Non connecté"}
        
        # 1. CHECK PERMISSION (bypass temporaire si module security non disponible)
        if permission_manager is None:
            logger.warning(f"⚠️ Security module désactivé - action {action} autorisée sans vérification")
            perm_check = {"allowed": True, "requires_confirmation": False, "risk": None, "reason": "dev_mode"}
        else:
            perm_check = permission_manager.check_permission(user_id, action, params)
        
        if not perm_check["allowed"]:
            logger.error(f"🚫 Permission refusée: {action} - {perm_check['reason']}")
            if permission_manager:
                permission_manager.log_action_result(
                    user_id=user_id,
                    action=action,
                    risk=perm_check["risk"],
                    status="denied",
                    params=params,
                    error=perm_check["reason"]
                )
            return {"success": False, "error": f"Permission refusée: {perm_check['reason']}"}
        
        # 2. DEMANDER CONFIRMATION si nécessaire
        if perm_check["requires_confirmation"]:
            logger.warning(f"⚠️ Confirmation requise pour: {action}")
            
            if confirmation_engine:
                confirmed = await confirmation_engine.request_confirmation(
                    action=action,
                    params=params,
                    risk=perm_check["risk"].value,
                    reason=perm_check["reason"],
                    user_id=user_id
                )
            else:
                # En mode dev sans confirmation_engine, autoriser par défaut
                logger.warning("⚠️ Confirmation engine désactivé - action autorisée")
                confirmed = True
            
            if not confirmed:
                logger.error(f"❌ Confirmation refusée: {action}")
                if permission_manager:
                    permission_manager.log_action_result(
                        user_id=user_id,
                        action=action,
                        risk=perm_check["risk"],
                        status="cancelled",
                        params=params,
                        error="Confirmation refusée par utilisateur"
                    )
                return {"success": False, "error": "Action annulée par l'utilisateur"}
        
        # 3. EXÉCUTER L'ACTION
        actions = {
            "open_app": self._open_app,
            "close_app": self._close_app,
            "list_apps": self._list_apps,
            "read_file": self._read_file,
            "list_directory": self._list_directory,
            "find_files": self._find_files,
            "get_file_info": self._get_file_info,
            "execute_script": self._execute_script,
            "get_running_apps": self._get_running_apps,
            "focus_app": self._focus_app,
            "minimize_app": self._minimize_app,
            "get_system_info": self._get_system_info
        }
        
        handler = actions.get(action)
        if not handler:
            if permission_manager:
                permission_manager.log_action_result(
                    user_id=user_id,
                    action=action,
                    risk=ActionRisk.MEDIUM if ActionRisk else None,
                    status="error",
                    params=params,
                    error=f"Action '{action}' inconnue"
                )
            return {"success": False, "error": f"Action '{action}' inconnue"}
        
        # 4. EXÉCUTER
        try:
            logger.info(f"🔄 Exécution: {action} (user: {user_id})")
            result = await handler(params)
            
            # 5. LOGGER SUCCÈS
            if permission_manager:
                permission_manager.log_action_result(
                    user_id=user_id,
                    action=action,
                    risk=perm_check.get("risk"),
                    status="success",
                    params=params,
                    result=result
                )
            
            return {"success": True, "data": result}
            
        except Exception as e:
            self.set_error(str(e))
            
            # 6. LOGGER ÉCHEC
            if permission_manager:
                permission_manager.log_action_result(
                    user_id=user_id,
                    action=action,
                    risk=perm_check.get("risk"),
                    status="error",
                    params=params,
                    error=str(e)
                )
            
            return {"success": False, "error": str(e)}
    
    # === Actions Applications ===
    # REFACTORED: Utilise maintenant l'adapter cross-platform
    
    async def _open_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ouvre une application (via adapter)"""
        app_name = params.get("app_name")
        
        if not app_name:
            return {"success": False, "message": "Nom d'application manquant"}
        
        if not self.adapter:
            raise Exception("Adapter système non disponible")
        
        # Déléguer à l'adapter
        result = await self.adapter.open_application(app_name)
        
        if result["success"]:
            logger.success(f"✅ {result['message']}")
        
        return result
    
    async def _close_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ferme une application"""
        app_name = params.get("app_name")
        
        if self.system == "Darwin":
            script = f'tell application "{app_name}" to quit'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.success(f"✅ Application '{app_name}' fermée")
                return {"message": f"Application '{app_name}' fermée", "status": "closed"}
            else:
                raise Exception(f"Erreur fermeture '{app_name}': {result.stderr}")
        
        raise Exception(f"OS {self.system} non supporté")
    
    async def _list_apps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste les applications installées"""
        return {
            "applications": self.installed_apps,
            "count": len(self.installed_apps)
        }
    
    async def _get_running_apps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste les applications en cours"""
        if self.system == "Darwin":
            script = 'tell application "System Events" to get name of every process whose background only is false'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                apps = result.stdout.strip().split(", ")
                return {"running_apps": apps, "count": len(apps)}
        
        return {"running_apps": [], "count": 0}
    
    async def _focus_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Met le focus sur une app"""
        app_name = params.get("app_name")
        
        if self.system == "Darwin":
            script = f'tell application "{app_name}" to activate'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {"message": f"Focus sur '{app_name}'", "status": "focused"}
            else:
                raise Exception(f"Erreur focus: {result.stderr}")
        
        raise Exception(f"OS {self.system} non supporté")
    
    async def _minimize_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Minimise une application"""
        app_name = params.get("app_name")
        
        if self.system == "Darwin":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set visible to false
                end tell
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {"message": f"'{app_name}' minimisée", "status": "minimized"}
            else:
                raise Exception(f"Erreur: {result.stderr}")
        
        raise Exception(f"OS {self.system} non supporté")
    
    # === Actions Fichiers ===
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lit un fichier"""
        file_path_str = params.get("file_path")
        if not file_path_str:
            return {"success": False, "message": "Chemin de fichier manquant"}
        
        file_path = Path(file_path_str)
        max_lines = params.get("max_lines", 100)
        
        if not file_path.exists():
            raise Exception(f"Fichier '{file_path}' introuvable")
        
        # Vérifier que c'est un fichier texte
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:max_lines]
                content = "".join(lines)
                
                return {
                    "path": str(file_path),
                    "content": content,
                    "lines_read": len(lines),
                    "truncated": len(lines) == max_lines
                }
        except UnicodeDecodeError:
            raise Exception(f"Fichier '{file_path}' n'est pas un fichier texte")
    
    async def _list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Liste un répertoire"""
        path = Path(params.get("path", "."))
        recursive = params.get("recursive", False)
        
        if not path.exists():
            raise Exception(f"Répertoire '{path}' introuvable")
        
        files = []
        dirs = []
        
        if recursive:
            for item in path.rglob("*"):
                if item.is_file():
                    files.append(str(item))
                elif item.is_dir():
                    dirs.append(str(item))
        else:
            for item in path.iterdir():
                if item.is_file():
                    files.append(item.name)
                elif item.is_dir():
                    dirs.append(item.name)
        
        return {
            "path": str(path),
            "files": files,
            "directories": dirs,
            "total_files": len(files),
            "total_dirs": len(dirs)
        }
    
    async def _find_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recherche des fichiers"""
        pattern = params.get("pattern", "*")
        directory = Path(params.get("directory", "."))
        
        if not directory.exists():
            raise Exception(f"Répertoire '{directory}' introuvable")
        
        matches = list(directory.rglob(pattern))
        
        return {
            "pattern": pattern,
            "directory": str(directory),
            "matches": [str(m) for m in matches],
            "count": len(matches)
        }
    
    async def _get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Métadonnées d'un fichier"""
        file_path_str = params.get("file_path")
        if not file_path_str:
            return {"success": False, "message": "Chemin de fichier manquant"}
        
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            raise Exception(f"Fichier '{file_path}' introuvable")
        
        stat = file_path.stat()
        
        return {
            "path": str(file_path),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "is_symlink": file_path.is_symlink()
        }
    
    # === Actions Système ===
    
    async def _execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un script"""
        script = params.get("script")
        if not script:
            return {"success": False, "message": "Script manquant"}
        
        script_type = params.get("script_type", "shell")
        
        if script_type == "applescript" and self.system == "Darwin":
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30
            )
        elif script_type == "shell":
            result = subprocess.run(
                script,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
        else:
            raise Exception(f"Type de script '{script_type}' non supporté")
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    
    async def _get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Informations système"""
        import psutil  # type: ignore[import-untyped,import-not-found]
        
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "disk_used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
            "disk_percent": psutil.disk_usage('/').percent
        }
