"""
Module de raisonnement et planification HOPPER
Planification, résolution de problèmes, génération et exécution de code
"""

from .problem_solver import (
    ProblemSolver,
    Problem,
    Solution,
    PlanStep,
    DecompositionStrategy
)

from .code_executor import (
    CodeExecutor,
    ExecutionResult,
    ExecutionEnvironment,
    SecurityLevel
)

from .code_generator import (
    CodeGenerator,
    CodeTemplate,
    GenerationConfig,
    CodeQuality
)

from .experience_manager import (
    ExperienceManager,
    Experience,
    Pattern,
    LearningStrategy
)

__all__ = [
    # Problem Solver
    'ProblemSolver',
    'Problem',
    'Solution',
    'PlanStep',
    'DecompositionStrategy',
    
    # Code Executor
    'CodeExecutor',
    'ExecutionResult',
    'ExecutionEnvironment',
    'SecurityLevel',
    
    # Code Generator
    'CodeGenerator',
    'CodeTemplate',
    'GenerationConfig',
    'CodeQuality',
    
    # Experience Manager
    'ExperienceManager',
    'Experience',
    'Pattern',
    'LearningStrategy'
]
