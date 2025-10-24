"""
HOPPER - macOS System Adapter
Implémentation des opérations système pour macOS
"""

import subprocess
import psutil  # type: ignore[import-untyped,import-not-found]
import platform
import os
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from .base import SystemAdapter


class MacOSAdapter(SystemAdapter):
    """Adaptateur pour macOS utilisant AppleScript et commandes natives"""
    
    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """Ouvrir application via AppleScript"""
        try:
            script = f'tell application "{app_name}" to activate'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Application '{app_name}' lancée",
                    "app_name": app_name
                }
            else:
                return {
                    "success": False,
                    "message": f"Erreur: {result.stderr}",
                    "app_name": app_name
                }
        
        except Exception as e:
            logger.error(f"Erreur open_application: {e}")
            return {"success": False, "message": str(e), "app_name": app_name}
    
    async def close_application(self, app_name: str) -> Dict[str, Any]:
        """Fermer application via AppleScript"""
        try:
            script = f'tell application "{app_name}" to quit'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "success": result.returncode == 0,
                "message": f"Application '{app_name}' fermée" if result.returncode == 0 else result.stderr
            }
        
        except Exception as e:
            logger.error(f"Erreur close_application: {e}")
            return {"success": False, "message": str(e)}
    
    async def list_applications(self) -> List[str]:
        """Lister applications dans /Applications"""
        try:
            apps_dir = Path("/Applications")
            apps = [app.stem for app in apps_dir.glob("*.app")]
            
            # Ajouter aussi ~/Applications
            user_apps = Path.home() / "Applications"
            if user_apps.exists():
                apps.extend([app.stem for app in user_apps.glob("*.app")])
            
            return sorted(set(apps))  # Déduplique et trie
        
        except Exception as e:
            logger.error(f"Erreur list_applications: {e}")
            return []
    
    async def list_running_apps(self) -> List[Dict[str, Any]]:
        """Lister applications en cours via psutil"""
        try:
            running_apps = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    pinfo = proc.info
                    # Filtrer les apps (pas les processus système)
                    if pinfo['name'] and not pinfo['name'].startswith('.'):
                        running_apps.append({
                            "name": pinfo['name'],
                            "pid": pinfo['pid'],
                            "memory": pinfo['memory_info'].rss if pinfo['memory_info'] else 0
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return running_apps
        
        except Exception as e:
            logger.error(f"Erreur list_running_apps: {e}")
            return []
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Informations système via platform + psutil"""
        try:
            import socket
            
            # CPU
            cpu_freq = psutil.cpu_freq()
            
            # RAM
            mem = psutil.virtual_memory()
            
            # Disk
            disk = psutil.disk_usage('/')
            
            return {
                "os": "macOS",
                "os_version": platform.mac_ver()[0],
                "architecture": platform.machine(),  # arm64 ou x86_64
                "hostname": socket.gethostname(),
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A",
                "ram_total": f"{mem.total / 1024**3:.1f} GB",
                "ram_available": f"{mem.available / 1024**3:.1f} GB",
                "disk_total": f"{disk.total / 1024**3:.1f} GB",
                "disk_used": f"{disk.used / 1024**3:.1f} GB"
            }
        
        except Exception as e:
            logger.error(f"Erreur get_system_info: {e}")
            return {"os": "macOS", "error": str(e)}
    
    async def read_file(self, file_path: str, max_lines: int = 50) -> Dict[str, Any]:
        """Lire fichier (standard Python)"""
        try:
            path = Path(file_path).expanduser()
            
            if not path.exists():
                return {
                    "success": False,
                    "message": f"Fichier non trouvé: {file_path}"
                }
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:max_lines]
                content = ''.join(lines)
            
            return {
                "success": True,
                "content": content,
                "lines": len(lines),
                "truncated": len(lines) >= max_lines
            }
        
        except Exception as e:
            logger.error(f"Erreur read_file: {e}")
            return {"success": False, "message": str(e)}
    
    async def list_directory(self, path: str) -> Dict[str, Any]:
        """Lister répertoire"""
        try:
            dir_path = Path(path).expanduser()
            
            if not dir_path.exists():
                return {
                    "success": False,
                    "message": f"Répertoire non trouvé: {path}"
                }
            
            files = [f.name for f in dir_path.iterdir() if f.is_file()]
            directories = [d.name for d in dir_path.iterdir() if d.is_dir()]
            
            return {
                "success": True,
                "files": sorted(files),
                "directories": sorted(directories)
            }
        
        except Exception as e:
            logger.error(f"Erreur list_directory: {e}")
            return {"success": False, "message": str(e)}
    
    async def find_files(self, pattern: str, start_path: str = ".") -> List[str]:
        """Rechercher fichiers par pattern"""
        try:
            path = Path(start_path).expanduser()
            files = [str(f) for f in path.rglob(pattern)]
            return files[:100]  # Limiter à 100 résultats
        
        except Exception as e:
            logger.error(f"Erreur find_files: {e}")
            return []
    
    async def execute_script(self, script: str, shell: bool = True) -> Dict[str, Any]:
        """Exécuter commande shell"""
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
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Timeout (30s)",
                "returncode": -1
            }
        except Exception as e:
            logger.error(f"Erreur execute_script: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    async def focus_application(self, app_name: str) -> Dict[str, Any]:
        """Mettre application au premier plan (= activate)"""
        return await self.open_application(app_name)
    
    async def minimize_application(self, app_name: str) -> Dict[str, Any]:
        """Minimiser application via AppleScript"""
        try:
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
                text=True,
                timeout=10
            )
            
            return {
                "success": result.returncode == 0,
                "message": f"Application '{app_name}' minimisée" if result.returncode == 0 else result.stderr
            }
        
        except Exception as e:
            logger.error(f"Erreur minimize_application: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Informations sur un fichier"""
        try:
            path = Path(file_path).expanduser()
            
            if not path.exists():
                return {
                    "success": False,
                    "message": f"Fichier non trouvé: {file_path}"
                }
            
            stats = path.stat()
            
            return {
                "success": True,
                "name": path.name,
                "size": stats.st_size,
                "created": stats.st_ctime,
                "modified": stats.st_mtime,
                "is_directory": path.is_dir(),
                "extension": path.suffix
            }
        
        except Exception as e:
            logger.error(f"Erreur get_file_info: {e}")
            return {"success": False, "message": str(e)}
