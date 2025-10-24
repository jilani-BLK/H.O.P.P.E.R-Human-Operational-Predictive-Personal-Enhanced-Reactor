"""
HOPPER - System Adapter Factory
Détecte automatiquement l'OS et retourne l'adaptateur approprié
"""

import platform
from loguru import logger

from .base import SystemAdapter, UnsupportedPlatformError
from .macos_adapter import MacOSAdapter


def get_system_adapter() -> SystemAdapter:
    """
    Détecte l'OS et retourne l'adaptateur approprié
    
    Returns:
        Instance de SystemAdapter (MacOSAdapter, WindowsAdapter, LinuxAdapter)
        
    Raises:
        UnsupportedPlatformError: Si l'OS n'est pas supporté
    """
    system = platform.system()
    
    logger.info(f"🔍 Détection OS: {system} ({platform.machine()})")
    
    if system == "Darwin":  # macOS
        logger.success("✅ Utilisation de MacOSAdapter")
        return MacOSAdapter()
    
    elif system == "Windows":
        logger.info("⚠️ WindowsAdapter pas encore implémenté, utilisation du fallback")
        # TODO: Implémenter WindowsAdapter
        # from .windows_adapter import WindowsAdapter
        # return WindowsAdapter()
        raise UnsupportedPlatformError(
            f"WindowsAdapter non implémenté. OS détecté: {system}"
        )
    
    elif system == "Linux":
        logger.info("⚠️ LinuxAdapter pas encore implémenté, utilisation du fallback")
        # TODO: Implémenter LinuxAdapter
        # from .linux_adapter import LinuxAdapter
        # return LinuxAdapter()
        raise UnsupportedPlatformError(
            f"LinuxAdapter non implémenté. OS détecté: {system}"
        )
    
    else:
        raise UnsupportedPlatformError(
            f"OS non supporté: {system}. "
            f"Systèmes supportés: macOS (Darwin), Windows, Linux"
        )


def get_remote_adapter(base_url: str) -> SystemAdapter:
    """
    Retourne un RemoteAdapter pour communication avec un agent système distant
    
    Usage:
        - Docker → Host macOS
        - Client distant → Serveur de contrôle
    
    Args:
        base_url: URL de l'agent système (ex: "http://host.docker.internal:9999")
        
    Returns:
        Instance de RemoteAdapter
    """
    logger.info(f"🌐 Utilisation de RemoteAdapter: {base_url}")
    # TODO: Implémenter RemoteAdapter
    # from .remote_adapter import RemoteAdapter
    # return RemoteAdapter(base_url)
    raise NotImplementedError("RemoteAdapter pas encore implémenté")
