"""
HOPPER - Antivirus Adapters Package
"""

from .base import AntivirusAdapter, ThreatLevel, ThreatType, ScanType
from .factory import get_antivirus_adapter
from .macos_adapter import MacOSAntivirusAdapter

__all__ = [
    "AntivirusAdapter",
    "ThreatLevel",
    "ThreatType",
    "ScanType",
    "get_antivirus_adapter",
    "MacOSAntivirusAdapter"
]
