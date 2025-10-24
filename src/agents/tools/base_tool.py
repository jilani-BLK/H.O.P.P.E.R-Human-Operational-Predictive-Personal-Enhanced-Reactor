"""
Base class for ReAct Agent tools.
All tools should inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToolMetadata:
    """Métadonnées d'un outil."""
    name: str
    description: str
    schema: Dict[str, Any]
    category: str = "general"
    requires_confirmation: bool = False


class BaseTool(ABC):
    """
    Classe de base pour tous les outils ReAct.
    
    Chaque outil doit implémenter:
    - metadata(): Retourne les métadonnées de l'outil
    - execute(): Exécute l'action de l'outil
    """
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Retourne les métadonnées de l'outil."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        Exécute l'outil avec les arguments fournis.
        
        Returns:
            str: Résultat de l'exécution (message de succès/erreur)
        """
        pass
    
    def validate_args(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Valide les arguments avant exécution.
        
        Returns:
            (is_valid, error_message)
        """
        required_params = self.metadata.schema.get("parameters", {})
        
        for param_name, param_info in required_params.items():
            if param_info.get("required", False) and param_name not in kwargs:
                return False, f"Missing required parameter: {param_name}"
        
        return True, None
    
    def __str__(self) -> str:
        return f"{self.metadata.name}: {self.metadata.description}"
