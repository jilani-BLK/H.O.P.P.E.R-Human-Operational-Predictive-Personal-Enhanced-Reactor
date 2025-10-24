"""
HOPPER - Connectors Module
"""

from .base import BaseConnector, ConnectorConfig, ConnectorRegistry, ConnectorCapability, ConnectorStatus
from .spotify import SpotifyConnector

__all__ = [
    'BaseConnector',
    'ConnectorConfig',
    'ConnectorRegistry',
    'ConnectorCapability',
    'ConnectorStatus',
    'SpotifyConnector'
]
