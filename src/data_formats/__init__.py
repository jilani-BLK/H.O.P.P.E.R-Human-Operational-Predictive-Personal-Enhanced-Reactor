"""
Module de gestion des formats de données complexes
Lecture, conversion, édition et génération de documents
"""

from .format_converter import (
    FormatConverter,
    ConversionConfig,
    ConversionResult,
    SupportedFormat
)

from .document_editor import (
    DocumentEditor,
    EditOperation,
    EditResult
)

from .document_generator import (
    DocumentGenerator,
    DocumentTemplate,
    GenerationResult,
    GenerationConfig
)

from .code_manipulator import (
    CodeManipulator,
    CodeAnalysis,
    CodeFormat,
    CodeModification
)

__all__ = [
    "FormatConverter",
    "ConversionConfig",
    "ConversionResult",
    "SupportedFormat",
    "DocumentEditor",
    "EditOperation",
    "EditResult",
    "DocumentGenerator",
    "DocumentTemplate",
    "GenerationResult",
    "GenerationConfig",
    "CodeManipulator",
    "CodeAnalysis",
    "CodeFormat",
    "CodeModification"
]
