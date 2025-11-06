"""
HOPPER - Connectors Client
Client HTTP pour communiquer avec le service Connectors (Phase 5)

Permet à l'orchestrateur d'exécuter des actions système via le service connectors:
- Ouvrir/fermer applications
- Lire/manipuler fichiers
- Contrôle système
- Intégrations tierces (Spotify, etc.)
"""

import os
import httpx
from typing import Dict, Any, List, Optional
from loguru import logger


class ConnectorsClient:
    """Client HTTP pour service Connectors"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialise le client
        
        Args:
            base_url: URL du service connectors (défaut: http://connectors:5006 ou via env)
        """
        self.base_url = base_url or os.getenv("CONNECTORS_URL", "http://connectors:5006")
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        
        logger.info(f"🔌 ConnectorsClient initialisé: {self.base_url}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifier l'état du service connectors"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def list_connectors(self) -> Dict[str, Any]:
        """Lister tous les connectors disponibles"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/connectors")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ List connectors failed: {e}")
            return {"error": str(e)}
    
    async def get_capabilities(self, connector_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtenir les capacités d'un ou tous les connectors
        
        Args:
            connector_name: Nom du connector (None = tous)
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if connector_name:
                    response = await client.get(f"{self.base_url}/connectors/{connector_name}")
                else:
                    response = await client.get(f"{self.base_url}/capabilities")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ Get capabilities failed: {e}")
            return {"error": str(e)}
    
    async def execute(
        self,
        connector: str,
        action: str,
        params: Dict[str, Any],
        user_id: str = "orchestrator"
    ) -> Dict[str, Any]:
        """
        Exécuter une action sur un connector
        
        Args:
            connector: Nom du connector (ex: "local_system", "spotify")
            action: Action à exécuter (ex: "open_app", "read_file")
            params: Paramètres de l'action
            user_id: ID utilisateur pour audit
            
        Returns:
            {"success": bool, "data": Any, "error": Optional[str]}
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "connector": connector,
                    "action": action,
                    "params": params,
                    "user_id": user_id
                }
                
                logger.info(f"🔄 Executing: {connector}.{action}")
                response = await client.post(
                    f"{self.base_url}/execute",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get("success"):
                    logger.success(f"✅ {connector}.{action} succeeded")
                else:
                    logger.warning(f"⚠️ {connector}.{action} failed: {result.get('error')}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error: {e.response.status_code}")
            return {
                "success": False,
                "data": None,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"❌ Execute failed: {e}")
            return {"success": False, "data": None, "error": str(e)}
    
    # === Raccourcis LocalSystem ===
    
    async def open_app(self, app_name: str, user_id: str = "orchestrator") -> Dict[str, Any]:
        """Ouvrir une application"""
        return await self.execute(
            connector="local_system",
            action="open_app",
            params={"app_name": app_name},
            user_id=user_id
        )
    
    async def close_app(self, app_name: str, user_id: str = "orchestrator") -> Dict[str, Any]:
        """Fermer une application"""
        return await self.execute(
            connector="local_system",
            action="close_app",
            params={"app_name": app_name},
            user_id=user_id
        )
    
    async def list_apps(self, user_id: str = "orchestrator") -> Dict[str, Any]:
        """Lister les applications installées"""
        return await self.execute(
            connector="local_system",
            action="list_apps",
            params={},
            user_id=user_id
        )
    
    async def read_file(
        self,
        file_path: str,
        max_lines: int = 50,
        user_id: str = "orchestrator"
    ) -> Dict[str, Any]:
        """Lire un fichier"""
        return await self.execute(
            connector="local_system",
            action="read_file",
            params={"file_path": file_path, "max_lines": max_lines},
            user_id=user_id
        )
    
    async def list_directory(
        self,
        path: str,
        user_id: str = "orchestrator"
    ) -> Dict[str, Any]:
        """Lister contenu d'un répertoire"""
        return await self.execute(
            connector="local_system",
            action="list_directory",
            params={"path": path},
            user_id=user_id
        )
    
    async def find_files(
        self,
        pattern: str,
        directory: str = ".",
        user_id: str = "orchestrator"
    ) -> Dict[str, Any]:
        """Rechercher des fichiers"""
        return await self.execute(
            connector="local_system",
            action="find_files",
            params={"pattern": pattern, "directory": directory},
            user_id=user_id
        )
    
    async def get_file_info(
        self,
        file_path: str,
        user_id: str = "orchestrator"
    ) -> Dict[str, Any]:
        """Obtenir infos sur un fichier"""
        return await self.execute(
            connector="local_system",
            action="get_file_info",
            params={"file_path": file_path},
            user_id=user_id
        )
    
    async def get_system_info(self, user_id: str = "orchestrator") -> Dict[str, Any]:
        """Obtenir informations système"""
        return await self.execute(
            connector="local_system",
            action="get_system_info",
            params={},
            user_id=user_id
        )
    
    async def execute_script(
        self,
        script: str,
        user_id: str = "orchestrator"
    ) -> Dict[str, Any]:
        """Exécuter un script/commande (DANGER - requires permission)"""
        return await self.execute(
            connector="local_system",
            action="execute_script",
            params={"script": script},
            user_id=user_id
        )
    
    # === Raccourcis Spotify ===
    
    async def spotify_play(self, user_id: str = "orchestrator") -> Dict[str, Any]:
        """Lancer la lecture Spotify"""
        return await self.execute(
            connector="spotify",
            action="play",
            params={},
            user_id=user_id
        )
    
    async def spotify_pause(self, user_id: str = "orchestrator") -> Dict[str, Any]:
        """Mettre en pause Spotify"""
        return await self.execute(
            connector="spotify",
            action="pause",
            params={},
            user_id=user_id
        )
    
    async def spotify_next(self, user_id: str = "orchestrator") -> Dict[str, Any]:
        """Piste suivante"""
        return await self.execute(
            connector="spotify",
            action="next_track",
            params={},
            user_id=user_id
        )
    
    async def spotify_search(
        self,
        query: str,
        type_: str = "track",
        user_id: str = "orchestrator"
    ) -> Dict[str, Any]:
        """Rechercher sur Spotify"""
        return await self.execute(
            connector="spotify",
            action="search",
            params={"query": query, "type": type_},
            user_id=user_id
        )


# Instance globale (singleton)
_client: Optional[ConnectorsClient] = None


def get_connectors_client() -> ConnectorsClient:
    """Obtenir l'instance singleton du client"""
    global _client
    if _client is None:
        _client = ConnectorsClient()
    return _client
