"""
HOPPER - Antivirus Adapter Factory
Détection automatique de l'OS et création de l'adapter approprié
"""

import platform
import logging
from typing import Optional

from .base import AntivirusAdapter
from .macos_adapter import MacOSAntivirusAdapter

logger = logging.getLogger(__name__)


def get_antivirus_adapter() -> AntivirusAdapter:
    """
    Crée l'adapter antivirus approprié selon l'OS.
    
    Returns:
        AntivirusAdapter instance pour l'OS détecté
        
    Raises:
        NotImplementedError: Si l'OS n'est pas supporté
    """
    system = platform.system()
    
    logger.info(f"Detecting antivirus adapter for OS: {system}")
    
    if system == "Darwin":  # macOS
        logger.info("Using MacOSAntivirusAdapter")
        return MacOSAntivirusAdapter()
    
    elif system == "Windows":
        logger.error("Windows antivirus adapter not yet implemented")
        raise NotImplementedError(
            "Windows antivirus adapter coming soon. "
            "Will integrate Windows Defender API."
        )
    
    elif system == "Linux":
        logger.error("Linux antivirus adapter not yet implemented")
        raise NotImplementedError(
            "Linux antivirus adapter coming soon. "
            "Will integrate ClamAV + rkhunter."
        )
    
    else:
        logger.error(f"Unsupported OS: {system}")
        raise NotImplementedError(
            f"Antivirus adapter not available for OS: {system}"
        )
