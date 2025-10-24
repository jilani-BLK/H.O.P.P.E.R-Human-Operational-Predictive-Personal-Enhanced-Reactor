"""
HOPPER - System Adapters
Interface abstraite pour opérations système cross-platform
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path


class SystemAdapter(ABC):
    """
    Interface abstraite pour opérations système
    
    Implémentations:
    - MacOSAdapter: AppleScript, Automator
    - WindowsAdapter: PowerShell, Win32 API
    - LinuxAdapter: D-Bus, xdotool, wmctrl
    - RemoteAdapter: REST API vers agent sur host (Docker)
    """
    
    @abstractmethod
    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """
        Ouvrir une application
        
        Args:
            app_name: Nom de l'application (ex: "Safari", "notepad.exe", "firefox")
            
        Returns:
            {"success": bool, "message": str, "app_name": str}
        """
        pass
    
    @abstractmethod
    async def close_application(self, app_name: str) -> Dict[str, Any]:
        """
        Fermer une application
        
        Args:
            app_name: Nom de l'application
            
        Returns:
            {"success": bool, "message": str}
        """
        pass
    
    @abstractmethod
    async def list_applications(self) -> List[str]:
        """
        Lister toutes les applications installées
        
        Returns:
            Liste des noms d'applications
        """
        pass
    
    @abstractmethod
    async def list_running_apps(self) -> List[Dict[str, Any]]:
        """
        Lister les applications en cours d'exécution
        
        Returns:
            Liste de dicts: [{"name": str, "pid": int, "memory": int}, ...]
        """
        pass
    
    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        """
        Obtenir informations système
        
        Returns:
            {
                "os": str,
                "os_version": str,
                "architecture": str,
                "hostname": str,
                "cpu_count": int,
                "cpu_freq": float,
                "ram_total": str,
                "ram_available": str,
                "disk_total": str,
                "disk_used": str
            }
        """
        pass
    
    @abstractmethod
    async def read_file(self, file_path: str, max_lines: int = 50) -> Dict[str, Any]:
        """
        Lire un fichier (cross-platform)
        
        Args:
            file_path: Chemin du fichier
            max_lines: Nombre maximum de lignes
            
        Returns:
            {"success": bool, "content": str, "lines": int}
        """
        pass
    
    @abstractmethod
    async def list_directory(self, path: str) -> Dict[str, Any]:
        """
        Lister contenu d'un répertoire
        
        Args:
            path: Chemin du répertoire
            
        Returns:
            {"success": bool, "files": List[str], "directories": List[str]}
        """
        pass
    
    @abstractmethod
    async def find_files(self, pattern: str, start_path: str = ".") -> List[str]:
        """
        Rechercher fichiers par pattern
        
        Args:
            pattern: Pattern de recherche (ex: "*.py", "test*")
            start_path: Répertoire de départ
            
        Returns:
            Liste de chemins de fichiers
        """
        pass
    
    @abstractmethod
    async def execute_script(self, script: str, shell: bool = True) -> Dict[str, Any]:
        """
        Exécuter un script/commande shell
        
        Args:
            script: Commande à exécuter
            shell: Utiliser shell ou non
            
        Returns:
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "returncode": int
            }
        """
        pass
    
    @abstractmethod
    async def focus_application(self, app_name: str) -> Dict[str, Any]:
        """
        Mettre une application au premier plan
        
        Args:
            app_name: Nom de l'application
            
        Returns:
            {"success": bool, "message": str}
        """
        pass
    
    @abstractmethod
    async def minimize_application(self, app_name: str) -> Dict[str, Any]:
        """
        Minimiser une application
        
        Args:
            app_name: Nom de l'application
            
        Returns:
            {"success": bool, "message": str}
        """
        pass
    
    @abstractmethod
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtenir informations sur un fichier
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            {
                "success": bool,
                "name": str,
                "size": int,
                "created": float,
                "modified": float,
                "is_directory": bool,
                "extension": str
            }
        """
        pass


class UnsupportedPlatformError(Exception):
    """Exception levée quand l'OS n'est pas supporté"""
    pass
