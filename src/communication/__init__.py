"""
Module de Communication Naturelle HOPPER
Permet à HOPPER d'expliquer ses actions de manière transparente

Exports:
    - ActionNarrator: Narrateur d'actions synchrone
    - AsyncActionNarrator: Narrateur d'actions asynchrone (avec callbacks)
    - Action, ActionType, Urgency: Types de données
    - Helpers synchrones: narrate_*
    - Helpers asynchrones: narrate_*_async
"""

__version__ = "1.0.0"

from .action_narrator import (
    ActionNarrator,
    Action,
    ActionType,
    Urgency,
    narrate_file_scan,
    narrate_file_modification,
    narrate_system_command,
    narrate_learning,
    narrate_reasoning
)

from .async_narrator import (
    AsyncActionNarrator,
    narrate_file_scan_async,
    narrate_file_modification_async,
    narrate_system_command_async,
    narrate_data_analysis_async
)

__all__ = [
    # Classes principales
    "ActionNarrator",
    "AsyncActionNarrator",
    
    # Types de données
    "Action",
    "ActionType",
    "Urgency",
    
    # Helpers synchrones
    "narrate_file_scan",
    "narrate_file_modification",
    "narrate_system_command",
    "narrate_learning",
    "narrate_reasoning",
    
    # Helpers asynchrones
    "narrate_file_scan_async",
    "narrate_file_modification_async",
    "narrate_system_command_async",
    "narrate_data_analysis_async",
]

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
