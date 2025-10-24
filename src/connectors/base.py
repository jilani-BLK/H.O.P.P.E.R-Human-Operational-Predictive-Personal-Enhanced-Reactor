"""
HOPPER - Base Connector
Architecture de base pour les connecteurs extensibles
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from loguru import logger


class ConnectorConfig(BaseModel):
    """Configuration d'un connecteur"""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = {}


class ConnectorCapability(BaseModel):
    """Capacité offerte par un connecteur"""
    name: str
    description: str
    parameters: Dict[str, Any] = {}


class ConnectorStatus(BaseModel):
    """Statut d'un connecteur"""
    name: str
    enabled: bool
    connected: bool
    last_error: Optional[str] = None
    capabilities: List[ConnectorCapability] = []


class BaseConnector(ABC):
    """
    Classe de base pour tous les connecteurs HOPPER
    
    Chaque connecteur doit hériter de cette classe et implémenter:
    - connect(): Initialiser la connexion
    - disconnect(): Fermer proprement
    - get_capabilities(): Lister ce que le connecteur peut faire
    - execute(): Exécuter une action
    - get_status(): État actuel
    """
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.name = config.name
        self.enabled = config.enabled
        self.connected = False
        self.last_error: Optional[str] = None
        
        logger.info(f"🔌 Connecteur '{self.name}' initialisé")
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Initialise la connexion au service externe
        
        Returns:
            True si succès, False sinon
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Ferme proprement la connexion
        
        Returns:
            True si succès
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[ConnectorCapability]:
        """
        Retourne la liste des capacités du connecteur
        
        Returns:
            Liste des actions possibles
        """
        pass
    
    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une action via le connecteur
        
        Args:
            action: Nom de l'action à exécuter
            params: Paramètres de l'action
            
        Returns:
            Résultat de l'exécution
        """
        pass
    
    def get_status(self) -> ConnectorStatus:
        """
        Retourne le statut actuel du connecteur
        
        Returns:
            ConnectorStatus
        """
        return ConnectorStatus(
            name=self.name,
            enabled=self.enabled,
            connected=self.connected,
            last_error=self.last_error,
            capabilities=self.get_capabilities()
        )
    
    def set_error(self, error: str):
        """Enregistre une erreur"""
        self.last_error = error
        logger.error(f"❌ [{self.name}] {error}")
    
    def clear_error(self):
        """Efface l'erreur"""
        self.last_error = None


class ConnectorRegistry:
    """
    Registre de tous les connecteurs disponibles
    Gère le chargement, l'activation, et la découverte automatique
    """
    
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        logger.info("📋 ConnectorRegistry initialisé")
    
    def register(self, connector: BaseConnector):
        """Enregistre un connecteur"""
        self.connectors[connector.name] = connector
        logger.success(f"✅ Connecteur '{connector.name}' enregistré")
    
    def get(self, name: str) -> Optional[BaseConnector]:
        """Récupère un connecteur par nom"""
        return self.connectors.get(name)
    
    def list_all(self) -> List[str]:
        """Liste tous les connecteurs"""
        return list(self.connectors.keys())
    
    def list_enabled(self) -> List[str]:
        """Liste les connecteurs activés"""
        return [name for name, conn in self.connectors.items() if conn.enabled]
    
    def get_all_capabilities(self) -> Dict[str, List[ConnectorCapability]]:
        """Récupère toutes les capacités de tous les connecteurs"""
        return {
            name: conn.get_capabilities()
            for name, conn in self.connectors.items()
            if conn.enabled and conn.connected
        }
    
    async def connect_all(self):
        """Connecte tous les connecteurs activés"""
        for name, connector in self.connectors.items():
            if connector.enabled:
                try:
                    await connector.connect()
                except Exception as e:
                    logger.error(f"❌ Erreur connexion {name}: {e}")
    
    async def disconnect_all(self):
        """Déconnecte tous les connecteurs"""
        for connector in self.connectors.values():
            try:
                await connector.disconnect()
            except Exception as e:
                logger.error(f"❌ Erreur déconnexion {connector.name}: {e}")
