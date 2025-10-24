"""
Communication Module - Communication Naturelle et Transparente

Ce module fournit des outils pour que HOPPER communique clairement
ses actions et intentions avec l'utilisateur.

Principe clé: "Quand HOPPER fait quelque chose, il le dit de manière naturelle"
"""

from .action_narrator import (
    ActionNarrator,
    Action,
    ActionType,
    Urgency,
    narrate_file_scan,
    narrate_file_modification,
    narrate_system_command,
    narrate_learning,
    narrate_reasoning,
)

__all__ = [
    "ActionNarrator",
    "Action",
    "ActionType",
    "Urgency",
    "narrate_file_scan",
    "narrate_file_modification",
    "narrate_system_command",
    "narrate_learning",
    "narrate_reasoning",
]

__version__ = "1.0.0"
