"""
Registre des services
Gère la découverte et la communication avec les microservices
"""

import aiohttp
from typing import Dict, Optional, Any
from loguru import logger

try:
    from ..config import settings
except ImportError:
    from config import settings  # type: ignore[import]


class ServiceRegistry:
    """Gestionnaire centralisé des services"""
    
    def __init__(self):
        self.services: Dict[str, str] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def register_services(self) -> None:
        """Enregistre tous les services disponibles"""
        self.services: Dict[str, str] = {
            "llm": settings.LLM_SERVICE_URL,  # pyright: ignore[reportGeneralTypeIssues]
            "system_executor": settings.SYSTEM_EXECUTOR_URL,  # pyright: ignore[reportGeneralTypeIssues]
            "stt": settings.STT_SERVICE_URL,  # pyright: ignore[reportGeneralTypeIssues]
            "tts": settings.TTS_SERVICE_URL,  # pyright: ignore[reportGeneralTypeIssues]
            "auth": settings.AUTH_SERVICE_URL,  # pyright: ignore[reportGeneralTypeIssues]
            "connectors": settings.CONNECTORS_URL  # pyright: ignore[reportGeneralTypeIssues]
        }
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.SERVICE_TIMEOUT)  # pyright: ignore[reportGeneralTypeIssues]
        )
        
        logger.info(f"Services enregistrés: {list(self.services.keys())}")
    
    async def check_health(self, service_name: str) -> bool:
        """
        Vérifie la santé d'un service
        
        Args:
            service_name: Nom du service
            
        Returns:
            True si le service est accessible
        """
        if service_name not in self.services:
            logger.warning(f"Service inconnu: {service_name}")
            return False
        
        url = f"{self.services[service_name]}/health"
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Erreur de santé pour {service_name}: {str(e)}")
            return False
    
    async def check_all_health(self) -> Dict[str, bool]:
        """
        Vérifie la santé de tous les services
        
        Returns:
            Dictionnaire service -> statut
        """
        results = {}
        for service_name in self.services.keys():
            results[service_name] = await self.check_health(service_name)
        return results
    
    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Appelle un service
        
        Args:
            service_name: Nom du service
            endpoint: Point de terminaison (ex: "/generate")
            method: Méthode HTTP
            data: Données à envoyer
            timeout: Timeout personnalisé
            
        Returns:
            Réponse du service
            
        Raises:
            Exception si le service n'est pas disponible
        """
        if service_name not in self.services:
            raise ValueError(f"Service inconnu: {service_name}")
        
        url = f"{self.services[service_name]}{endpoint}"
        timeout_value = timeout or settings.SERVICE_TIMEOUT
        
        try:
            async with self.session.request(
                method,
                url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout_value)
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"Erreur d'appel à {service_name}{endpoint}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'appel à {service_name}: {str(e)}")
            raise
    
    async def close_all(self) -> None:
        """Ferme toutes les connexions"""
        if self.session:
            await self.session.close()
            logger.info("Connexions des services fermées")
