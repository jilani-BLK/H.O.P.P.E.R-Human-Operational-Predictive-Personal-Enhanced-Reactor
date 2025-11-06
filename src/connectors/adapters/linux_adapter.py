"""
HOPPER - Linux System Adapter
Implémentation pour environnements Linux (notamment Docker containers)

Commandes utilisées:
- xdg-open: ouvrir fichiers/URLs
- ps: lister processus
- pkill: fermer applications
- dpkg/which: scanner applications installées
"""

import os
import subprocess
import platform
from typing import Dict, Any, List
from pathlib import Path
from loguru import logger

from .base import SystemAdapter


class LinuxAdapter(SystemAdapter):
    """Adapter pour Linux (Docker containers, servers, desktops)"""
    
    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """
        Ouvrir une application sous Linux
        Utilise xdg-open si disponible, sinon commande directe
        """
        try:
            # Essayer xdg-open d'abord (standard freedesktop)
            result = subprocess.run(
                ["xdg-open", app_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Application '{app_name}' ouverte via xdg-open",
                    "app_name": app_name
                }
            
            # Sinon essayer commande directe
            subprocess.Popen([app_name], start_new_session=True)
            return {
                "success": True,
                "message": f"Application '{app_name}' lancée en arrière-plan",
                "app_name": app_name
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Application '{app_name}' non trouvée",
                "app_name": app_name
            }
        except Exception as e:
            logger.error(f"Erreur ouverture {app_name}: {e}")
            return {
                "success": False,
                "message": str(e),
                "app_name": app_name
            }
    
    async def close_application(self, app_name: str) -> Dict[str, Any]:
        """Fermer une application avec pkill"""
        try:
            result = subprocess.run(
                ["pkill", "-f", app_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return {
                "success": result.returncode == 0,
                "message": f"Application '{app_name}' fermée" if result.returncode == 0 else "Aucun processus trouvé"
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def list_applications(self) -> List[str]:
        """
        Lister applications installées
        Stratégie: scanner /usr/bin, /usr/local/bin, dpkg si disponible
        """
        apps = set()
        
        # Scanner binaires communs
        for bin_dir in ["/usr/bin", "/usr/local/bin", "/bin"]:
            if Path(bin_dir).exists():
                try:
                    for item in Path(bin_dir).iterdir():
                        if item.is_file() and os.access(item, os.X_OK):
                            apps.add(item.name)
                except Exception as e:
                    logger.debug(f"Erreur scan {bin_dir}: {e}")
        
        # Essayer dpkg si Debian/Ubuntu
        try:
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("ii "):
                        parts = line.split()
                        if len(parts) >= 2:
                            apps.add(parts[1])
        except FileNotFoundError:
            pass  # dpkg non disponible
        except Exception as e:
            logger.debug(f"Erreur dpkg: {e}")
        
        return sorted(list(apps))[:100]  # Limiter pour éviter flood
    
    async def list_running_apps(self) -> List[Dict[str, Any]]:
        """Lister processus en cours avec ps"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            processes = []
            for line in result.stdout.split("\n")[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 11:
                    processes.append({
                        "name": parts[10],
                        "pid": int(parts[1]) if parts[1].isdigit() else 0,
                        "cpu": float(parts[2]) if parts[2].replace(".", "").isdigit() else 0.0,
                        "memory": float(parts[3]) if parts[3].replace(".", "").isdigit() else 0.0
                    })
            
            return processes[:50]  # Top 50
            
        except Exception as e:
            logger.error(f"Erreur listage processus: {e}")
            return []
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Informations système Linux"""
        import psutil
        
        try:
            disk = psutil.disk_usage("/")
            memory = psutil.virtual_memory()
            
            return {
                "os": "Linux",
                "os_version": platform.release(),
                "architecture": platform.machine(),
                "hostname": platform.node(),
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "ram_total": f"{memory.total / (1024**3):.1f} GB",
                "ram_available": f"{memory.available / (1024**3):.1f} GB",
                "disk_total": f"{disk.total / (1024**3):.1f} GB",
                "disk_used": f"{disk.used / (1024**3):.1f} GB"
            }
        except Exception as e:
            logger.error(f"Erreur system info: {e}")
            return {
                "os": "Linux",
                "error": str(e)
            }
    
    async def read_file(self, file_path: str, max_lines: int = 50) -> Dict[str, Any]:
        """Lire un fichier Linux (simple)"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Fichier non trouvé: {file_path}"
                }
            
            if not path.is_file():
                return {
                    "success": False,
                    "error": f"Pas un fichier: {file_path}"
                }
            
            # Lire avec limite
            lines = []
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())
            
            return {
                "success": True,
                "content": "\n".join(lines),
                "lines": len(lines),
                "truncated": len(lines) == max_lines
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_directory(self, path: str) -> Dict[str, Any]:
        """Lister contenu d'un répertoire"""
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return {"success": False, "error": f"Répertoire non trouvé: {path}"}
            
            if not dir_path.is_dir():
                return {"success": False, "error": f"Pas un répertoire: {path}"}
            
            items = []
            for item in dir_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return {
                "success": True,
                "path": str(dir_path),
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def find_files(self, pattern: str, directory: str = ".") -> Dict[str, Any]:
        """Rechercher fichiers par pattern"""
        try:
            dir_path = Path(directory)
            matches = list(dir_path.glob(f"**/{pattern}"))[:100]  # Limiter à 100
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "matches": [str(m) for m in matches],
                "count": len(matches)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_script(self, script: str, shell: bool = True) -> Dict[str, Any]:
        """Exécuter un script shell"""
        try:
            result = subprocess.run(
                script if shell else script.split(),
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    async def focus_application(self, app_name: str) -> Dict[str, Any]:
        """Focus app (nécessite wmctrl ou xdotool - pas dispo en Docker headless)"""
        return {
            "success": False,
            "message": "Focus application non supporté en environnement headless"
        }
    
    async def minimize_application(self, app_name: str) -> Dict[str, Any]:
        """Minimize app (idem)"""
        return {
            "success": False,
            "message": "Minimize application non supporté en environnement headless"
        }
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Infos fichier"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"Fichier non trouvé: {file_path}"}
            
            stat = path.stat()
            return {
                "success": True,
                "name": path.name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_directory": path.is_dir(),
                "extension": path.suffix
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
