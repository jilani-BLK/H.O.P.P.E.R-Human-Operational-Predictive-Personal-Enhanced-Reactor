"""
HOPPER - Connecteur Spotify
Contrôle de lecture Spotify via l'API Web
"""

import os
from typing import Dict, Any, List, Optional
import httpx
from loguru import logger

from base import BaseConnector, ConnectorConfig, ConnectorCapability


class SpotifyConnector(BaseConnector):
    """
    Connecteur pour l'API Spotify Web
    
    Capacités:
    - Recherche de musique (artistes, albums, titres)
    - Lecture/Pause/Skip
    - Contrôle du volume
    - Gestion des playlists
    - Affichage du morceau en cours
    """
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        
        # Configuration Spotify
        self.client_id = config.config.get("client_id", os.getenv("SPOTIFY_CLIENT_ID"))
        self.client_secret = config.config.get("client_secret", os.getenv("SPOTIFY_CLIENT_SECRET"))
        self.redirect_uri = config.config.get("redirect_uri", "http://localhost:8888/callback")
        
        # Token d'accès (à obtenir via OAuth)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
        # Client HTTP
        self.client: Optional[httpx.AsyncClient] = None
        
        self.api_base = "https://api.spotify.com/v1"
    
    async def connect(self) -> bool:
        """Initialise la connexion Spotify"""
        try:
            # Créer client HTTP
            self.client = httpx.AsyncClient(timeout=10.0)
            
            # Vérifier si on a déjà un token
            if self.access_token:
                # Tester le token
                if await self._test_token():
                    self.connected = True
                    self.clear_error()
                    logger.success(f"✅ [{self.name}] Connecté à Spotify")
                    return True
            
            # Sinon, il faudrait faire le flux OAuth
            logger.warning(f"⚠️ [{self.name}] Token Spotify manquant - OAuth requis")
            logger.info(f"💡 Configurez SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET")
            
            # Pour les tests, on peut fonctionner en mode "simulation"
            self.connected = True
            return True
            
        except Exception as e:
            self.set_error(f"Erreur connexion: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Ferme la connexion"""
        if self.client:
            await self.client.aclose()
            self.client = None
        
        self.connected = False
        logger.info(f"🔌 [{self.name}] Déconnecté")
        return True
    
    async def _test_token(self) -> bool:
        """Teste si le token est valide"""
        if not self.client or not self.access_token:
            return False
        
        try:
            response = await self.client.get(
                f"{self.api_base}/me",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.status_code == 200
        except:
            return False
    
    def get_capabilities(self) -> List[ConnectorCapability]:
        """Liste des capacités Spotify"""
        return [
            ConnectorCapability(
                name="search",
                description="Rechercher musique (artiste, album, titre)",
                parameters={"query": "str", "type": "track|artist|album"}
            ),
            ConnectorCapability(
                name="play",
                description="Lancer la lecture",
                parameters={"uri": "Optional[str]"}
            ),
            ConnectorCapability(
                name="pause",
                description="Mettre en pause"
            ),
            ConnectorCapability(
                name="skip",
                description="Passer au morceau suivant"
            ),
            ConnectorCapability(
                name="previous",
                description="Revenir au morceau précédent"
            ),
            ConnectorCapability(
                name="volume",
                description="Régler le volume (0-100)",
                parameters={"level": "int"}
            ),
            ConnectorCapability(
                name="current",
                description="Afficher le morceau en cours"
            ),
            ConnectorCapability(
                name="create_playlist",
                description="Créer une playlist",
                parameters={"name": "str", "description": "Optional[str]"}
            )
        ]
    
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une action Spotify"""
        if not self.connected:
            return {"success": False, "error": "Non connecté à Spotify"}
        
        # Mode simulation si pas de token
        if not self.access_token:
            return await self._simulate_action(action, params)
        
        # Dispatcher vers la bonne méthode
        actions = {
            "search": self._search,
            "play": self._play,
            "pause": self._pause,
            "skip": self._skip,
            "previous": self._previous,
            "volume": self._set_volume,
            "current": self._get_current,
            "create_playlist": self._create_playlist
        }
        
        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Action '{action}' inconnue"}
        
        try:
            result = await handler(params)
            return {"success": True, "data": result}
        except Exception as e:
            self.set_error(str(e))
            return {"success": False, "error": str(e)}
    
    async def _simulate_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mode simulation pour tests sans token"""
        logger.info(f"🎵 [SIMULATION] Spotify.{action}({params})")
        
        simulations = {
            "search": {"results": [{"name": "Exemple - Artiste", "uri": "spotify:track:123"}]},
            "play": {"status": "playing"},
            "pause": {"status": "paused"},
            "current": {"track": "Exemple - Artiste", "album": "Album Test"},
            "volume": {"level": params.get("level", 50)}
        }
        
        return {
            "success": True,
            "data": simulations.get(action, {"message": f"Action {action} simulée"})
        }
    
    async def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recherche Spotify"""
        query = params.get("query")
        search_type = params.get("type", "track")
        
        response = await self.client.get(
            f"{self.api_base}/search",
            params={"q": query, "type": search_type, "limit": 5},
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        return response.json()
    
    async def _play(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lance la lecture"""
        data = {}
        if "uri" in params:
            data["uris"] = [params["uri"]]
        
        response = await self.client.put(
            f"{self.api_base}/me/player/play",
            json=data,
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        return {"status": "playing"}
    
    async def _pause(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pause"""
        response = await self.client.put(
            f"{self.api_base}/me/player/pause",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        return {"status": "paused"}
    
    async def _skip(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Morceau suivant"""
        response = await self.client.post(
            f"{self.api_base}/me/player/next",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        return {"status": "skipped"}
    
    async def _previous(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Morceau précédent"""
        response = await self.client.post(
            f"{self.api_base}/me/player/previous",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        return {"status": "previous"}
    
    async def _set_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Règle le volume"""
        level = params.get("level", 50)
        
        response = await self.client.put(
            f"{self.api_base}/me/player/volume",
            params={"volume_percent": level},
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        return {"level": level}
    
    async def _get_current(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère le morceau en cours"""
        response = await self.client.get(
            f"{self.api_base}/me/player/currently-playing",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        data = response.json()
        if data.get("item"):
            return {
                "track": data["item"]["name"],
                "artist": data["item"]["artists"][0]["name"],
                "album": data["item"]["album"]["name"]
            }
        
        return {"message": "Aucun morceau en lecture"}
    
    async def _create_playlist(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une playlist"""
        # Récupérer l'ID utilisateur d'abord
        user_response = await self.client.get(
            f"{self.api_base}/me",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        user_id = user_response.json()["id"]
        
        # Créer la playlist
        response = await self.client.post(
            f"{self.api_base}/users/{user_id}/playlists",
            json={
                "name": params.get("name"),
                "description": params.get("description", ""),
                "public": False
            },
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        return response.json()
