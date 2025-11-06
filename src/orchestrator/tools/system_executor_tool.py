"""
System Executor Tool - Wrapper vers service C pour exécution système

Standardise l'interface entre l'orchestrateur et le service C system_executor.
Format JSON harmonisé: {command, args[], timeout}
"""

from typing import Dict, Any, List, Optional
import httpx
import json
from loguru import logger


class SystemExecutorTool:
    """
    Tool pour exécution de commandes système via service C
    
    Transforme les appels depuis PlanBasedDispatcher en format
    attendu par le service C system_executor.
    """
    
    def __init__(
        self,
        service_url: str = "http://localhost:5003",
        timeout: int = 30
    ):
        """
        Args:
            service_url: URL du service C system_executor
            timeout: Timeout par défaut des requêtes
        """
        self.service_url = service_url
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        logger.info(f"✅ SystemExecutorTool initialisé ({service_url})")
    
    async def execute_command(
        self,
        command: str,
        args: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Exécute une commande système
        
        Args:
            command: Commande à exécuter (ex: "create_file", "delete_file")
            args: Arguments de la commande
            timeout: Timeout spécifique (override défaut)
            
        Returns:
            {"success": bool, "message": str, "data": Any}
        """
        args = args or []
        timeout = timeout or self.timeout
        
        # Mapper commande générique → format service C
        c_payload = self._translate_to_c_format(command, args)
        
        try:
            logger.debug(f"🚀 Exécution système: {command} {args}")
            
            response = self.client.post(
                f"{self.service_url}/execute",
                json=c_payload,
                timeout=timeout
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Erreur service C: {response.status_code}")
                return {
                    "success": False,
                    "message": f"HTTP {response.status_code}",
                    "data": None
                }
            
            result = response.json()
            logger.info(f"✅ Commande exécutée: {command}")
            return result
            
        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout commande système: {command}")
            return {
                "success": False,
                "message": f"Timeout après {timeout}s",
                "data": None
            }
        except Exception as e:
            logger.error(f"❌ Erreur exécution système: {e}")
            return {
                "success": False,
                "message": str(e),
                "data": None
            }
    
    def _translate_to_c_format(
        self,
        command: str,
        args: List[str]
    ) -> Dict[str, Any]:
        """
        Traduit commande/args génériques en format service C
        
        Format orchestrateur:
          command="create_file", args=["/path/file.txt", "content here"]
          
        Format service C:
          {"action": "create_file", "path": "/path/file.txt", "content": "content here"}
        """
        
        if command == "create_file":
            path = args[0] if len(args) > 0 else "/tmp/hopper_default.txt"
            content = args[1] if len(args) > 1 else "Default content"
            return {
                "action": "create_file",
                "path": path,
                "content": content
            }
        
        elif command == "delete_file":
            path = args[0] if len(args) > 0 else "/tmp/hopper_default.txt"
            return {
                "action": "delete_file",
                "path": path
            }
        
        elif command == "list_directory":
            path = args[0] if len(args) > 0 else "/tmp"
            return {
                "action": "list_directory",
                "path": path
            }
        
        elif command == "read_file":
            path = args[0] if len(args) > 0 else "/tmp/hopper_default.txt"
            return {
                "action": "read_file",
                "path": path
            }
        
        elif command == "execute_shell":
            # Pour commandes shell arbitraires (DANGEREUX - nécessite validation)
            shell_command = args[0] if len(args) > 0 else "echo 'No command'"
            return {
                "action": "execute_shell",
                "command": shell_command
            }
        
        else:
            # Fallback: passer tel quel
            logger.warning(f"⚠️ Commande inconnue, passage brut: {command}")
            return {
                "action": command,
                "args": args
            }
    
    async def create_file(self, path: str, content: str) -> Dict[str, Any]:
        """Crée un fichier avec contenu"""
        return await self.execute_command("create_file", [path, content])
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Supprime un fichier"""
        return await self.execute_command("delete_file", [path])
    
    async def list_directory(self, path: str) -> Dict[str, Any]:
        """Liste le contenu d'un répertoire"""
        return await self.execute_command("list_directory", [path])
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Lit le contenu d'un fichier"""
        return await self.execute_command("read_file", [path])
    
    def health_check(self) -> bool:
        """Vérifie que le service C est disponible"""
        try:
            response = self.client.get(
                f"{self.service_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Service C indisponible: {e}")
            return False
    
    def close(self):
        """Ferme le client HTTP"""
        self.client.close()


# Export pour utilisation comme Tool dans PluginRegistry
async def system_executor_tool_factory(
    config: Dict[str, Any]
) -> SystemExecutorTool:
    """
    Factory pour créer SystemExecutorTool depuis config
    
    Args:
        config: {"service_url": str, "timeout": int}
        
    Returns:
        Instance de SystemExecutorTool
    """
    service_url = config.get("service_url", "http://localhost:5003")
    timeout = config.get("timeout", 30)
    
    tool = SystemExecutorTool(service_url=service_url, timeout=timeout)
    
    # Vérifier disponibilité
    if not tool.health_check():
        logger.warning("⚠️ Service system_executor C non disponible")
    
    return tool
