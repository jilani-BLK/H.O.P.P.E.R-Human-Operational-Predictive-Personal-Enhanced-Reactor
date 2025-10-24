"""
Système de planification et résolution de problèmes HOPPER
Décompose les problèmes complexes et élabore des plans d'action
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from enum import Enum
from datetime import datetime
import json
from pathlib import Path


class DecompositionStrategy(Enum):
    """Stratégies de décomposition de problèmes"""
    SEQUENTIAL = "sequential"  # Étapes séquentielles
    PARALLEL = "parallel"  # Sous-problèmes indépendants
    HIERARCHICAL = "hierarchical"  # Décomposition récursive
    DIVIDE_CONQUER = "divide_and_conquer"  # Diviser pour régner
    ITERATIVE = "iterative"  # Raffinement itératif


class PlanStatus(Enum):
    """Statut d'un plan ou d'une étape"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """Une étape dans un plan de résolution"""
    id: str
    description: str
    action: str  # Type d'action à effectuer
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # IDs d'étapes requises
    status: PlanStatus = PlanStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'description': self.description,
            'action': self.action,
            'parameters': self.parameters,
            'dependencies': self.dependencies,
            'status': self.status.value,
            'result': str(self.result) if self.result else None,
            'error': self.error,
            'retry_count': self.retry_count
        }


@dataclass
class Problem:
    """Représentation d'un problème à résoudre"""
    id: str
    description: str
    category: str  # Type de problème
    complexity: int  # 1-10
    constraints: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)
    resources_needed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'description': self.description,
            'category': self.category,
            'complexity': self.complexity,
            'constraints': self.constraints,
            'context': self.context,
            'success_criteria': self.success_criteria,
            'resources_needed': self.resources_needed
        }


@dataclass
class Solution:
    """Solution à un problème"""
    problem_id: str
    plan_steps: List[PlanStep]
    strategy: DecompositionStrategy
    confidence: float  # 0-1
    estimated_time: Optional[float] = None  # En secondes
    actual_time: Optional[float] = None
    success: bool = False
    results: Dict[str, Any] = field(default_factory=dict)
    lessons_learned: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'problem_id': self.problem_id,
            'strategy': self.strategy.value,
            'confidence': self.confidence,
            'estimated_time': self.estimated_time,
            'actual_time': self.actual_time,
            'success': self.success,
            'plan_steps': [step.to_dict() for step in self.plan_steps],
            'results': self.results,
            'lessons_learned': self.lessons_learned
        }


class ProblemSolver:
    """
    Système de planification et résolution de problèmes
    Décompose les problèmes complexes et élabore des plans d'action
    """
    
    def __init__(self, llm_model: Optional[Any] = None):
        self.llm_model = llm_model
        self.problems_solved: Dict[str, Solution] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self.decomposition_templates: Dict[str, List[str]] = self._init_templates()
        
    def _init_templates(self) -> Dict[str, List[str]]:
        """Initialise les templates de décomposition par catégorie"""
        return {
            "data_analysis": [
                "Charger et valider les données",
                "Explorer et visualiser",
                "Nettoyer et transformer",
                "Analyser et modéliser",
                "Interpréter et communiquer"
            ],
            "optimization": [
                "Définir la fonction objectif",
                "Identifier les contraintes",
                "Choisir l'algorithme",
                "Implémenter et tester",
                "Valider et raffiner"
            ],
            "debugging": [
                "Reproduire le problème",
                "Isoler la cause",
                "Proposer des hypothèses",
                "Tester les hypothèses",
                "Implémenter la correction"
            ],
            "automation": [
                "Définir le workflow",
                "Identifier les tâches répétitives",
                "Concevoir l'automatisation",
                "Implémenter les scripts",
                "Tester et déployer"
            ],
            "research": [
                "Définir la question",
                "Collecter les informations",
                "Analyser les sources",
                "Synthétiser les résultats",
                "Documenter les conclusions"
            ]
        }
    
    def register_action_handler(self, action_type: str, handler: Callable):
        """Enregistre un gestionnaire pour un type d'action"""
        self.action_handlers[action_type] = handler
    
    async def analyze_problem(self, problem: Problem) -> Dict[str, Any]:
        """
        Analyse un problème pour déterminer sa complexité et sa nature
        
        Args:
            problem: Le problème à analyser
            
        Returns:
            Analyse complète du problème
        """
        analysis = {
            'problem_id': problem.id,
            'complexity_assessment': self._assess_complexity(problem),
            'recommended_strategy': self._recommend_strategy(problem),
            'sub_problems': self._identify_subproblems(problem),
            'required_resources': problem.resources_needed,
            'estimated_steps': 0,
            'risk_factors': self._identify_risks(problem)
        }
        
        # Estimer le nombre d'étapes
        if problem.category in self.decomposition_templates:
            analysis['estimated_steps'] = len(self.decomposition_templates[problem.category])
        else:
            analysis['estimated_steps'] = max(3, problem.complexity)
        
        return analysis
    
    def _assess_complexity(self, problem: Problem) -> Dict[str, Any]:
        """Évalue la complexité d'un problème"""
        factors = {
            'declared_complexity': problem.complexity,
            'constraints_count': len(problem.constraints),
            'resources_needed': len(problem.resources_needed),
            'success_criteria_count': len(problem.success_criteria)
        }
        
        # Score composé
        total_score = (
            problem.complexity * 0.4 +
            len(problem.constraints) * 0.2 +
            len(problem.resources_needed) * 0.2 +
            len(problem.success_criteria) * 0.2
        )
        
        if total_score < 3:
            level = "simple"
        elif total_score < 6:
            level = "modéré"
        elif total_score < 9:
            level = "complexe"
        else:
            level = "très complexe"
        
        return {
            'factors': factors,
            'total_score': total_score,
            'level': level
        }
    
    def _recommend_strategy(self, problem: Problem) -> DecompositionStrategy:
        """Recommande une stratégie de décomposition"""
        # Basé sur la catégorie et la complexité
        if problem.complexity >= 8:
            return DecompositionStrategy.HIERARCHICAL
        elif problem.category in ["optimization", "debugging"]:
            return DecompositionStrategy.ITERATIVE
        elif len(problem.resources_needed) > 3:
            return DecompositionStrategy.PARALLEL
        elif problem.category in ["data_analysis", "automation"]:
            return DecompositionStrategy.SEQUENTIAL
        else:
            return DecompositionStrategy.DIVIDE_CONQUER
    
    def _identify_subproblems(self, problem: Problem) -> List[str]:
        """Identifie les sous-problèmes"""
        subproblems = []
        
        # Utiliser le template si disponible
        if problem.category in self.decomposition_templates:
            subproblems = self.decomposition_templates[problem.category].copy()
        else:
            # Décomposition générique
            subproblems = [
                "Comprendre le problème et les contraintes",
                "Collecter les informations nécessaires",
                "Concevoir une approche",
                "Implémenter la solution",
                "Valider et optimiser"
            ]
        
        return subproblems
    
    def _identify_risks(self, problem: Problem) -> List[str]:
        """Identifie les facteurs de risque"""
        risks = []
        
        if problem.complexity >= 7:
            risks.append("Complexité élevée nécessitant décomposition fine")
        
        if len(problem.constraints) > 5:
            risks.append("Nombreuses contraintes pouvant créer des conflits")
        
        if not problem.success_criteria:
            risks.append("Critères de succès flous")
        
        if len(problem.resources_needed) > 5:
            risks.append("Dépendances multiples augmentant le risque d'échec")
        
        return risks
    
    async def decompose_problem(
        self,
        problem: Problem,
        strategy: Optional[DecompositionStrategy] = None
    ) -> List[PlanStep]:
        """
        Décompose un problème en étapes planifiées
        
        Args:
            problem: Le problème à décomposer
            strategy: Stratégie de décomposition (auto si None)
            
        Returns:
            Liste d'étapes planifiées
        """
        if strategy is None:
            strategy = self._recommend_strategy(problem)
        
        if strategy == DecompositionStrategy.HIERARCHICAL:
            return await self._decompose_hierarchical(problem)
        elif strategy == DecompositionStrategy.SEQUENTIAL:
            return await self._decompose_sequential(problem)
        elif strategy == DecompositionStrategy.PARALLEL:
            return await self._decompose_parallel(problem)
        elif strategy == DecompositionStrategy.ITERATIVE:
            return await self._decompose_iterative(problem)
        else:
            return await self._decompose_divide_conquer(problem)
    
    async def _decompose_sequential(self, problem: Problem) -> List[PlanStep]:
        """Décomposition séquentielle"""
        steps = []
        subproblems = self._identify_subproblems(problem)
        
        for i, subproblem in enumerate(subproblems):
            step = PlanStep(
                id=f"{problem.id}_step_{i+1}",
                description=subproblem,
                action="execute_subproblem",
                parameters={'subproblem': subproblem, 'index': i},
                dependencies=[f"{problem.id}_step_{i}"] if i > 0 else []
            )
            steps.append(step)
        
        return steps
    
    async def _decompose_parallel(self, problem: Problem) -> List[PlanStep]:
        """Décomposition parallèle pour tâches indépendantes"""
        steps = []
        subproblems = self._identify_subproblems(problem)
        
        # Étape initiale
        init_step = PlanStep(
            id=f"{problem.id}_init",
            description="Initialisation et préparation",
            action="initialize",
            parameters={'problem': problem.to_dict()}
        )
        steps.append(init_step)
        
        # Étapes parallèles
        for i, subproblem in enumerate(subproblems):
            step = PlanStep(
                id=f"{problem.id}_parallel_{i+1}",
                description=subproblem,
                action="execute_parallel",
                parameters={'subproblem': subproblem},
                dependencies=[init_step.id]
            )
            steps.append(step)
        
        # Étape de fusion
        merge_step = PlanStep(
            id=f"{problem.id}_merge",
            description="Fusionner et valider les résultats",
            action="merge_results",
            parameters={},
            dependencies=[s.id for s in steps[1:]]  # Dépend de toutes les étapes parallèles
        )
        steps.append(merge_step)
        
        return steps
    
    async def _decompose_hierarchical(self, problem: Problem) -> List[PlanStep]:
        """Décomposition hiérarchique récursive"""
        steps = []
        
        # Niveau 1: Phases principales
        phases = [
            "Analyse et planification",
            "Exécution et développement",
            "Test et validation",
            "Optimisation et documentation"
        ]
        
        for i, phase in enumerate(phases):
            # Étape de phase
            phase_step = PlanStep(
                id=f"{problem.id}_phase_{i+1}",
                description=phase,
                action="execute_phase",
                parameters={'phase': phase, 'level': 1},
                dependencies=[f"{problem.id}_phase_{i}"] if i > 0 else []
            )
            steps.append(phase_step)
            
            # Sous-étapes (niveau 2)
            substeps = self._generate_substeps(problem, phase, i)
            for j, substep in enumerate(substeps):
                sub = PlanStep(
                    id=f"{problem.id}_phase_{i+1}_sub_{j+1}",
                    description=substep,
                    action="execute_substep",
                    parameters={'substep': substep, 'level': 2},
                    dependencies=[phase_step.id]
                )
                steps.append(sub)
        
        return steps
    
    async def _decompose_iterative(self, problem: Problem) -> List[PlanStep]:
        """Décomposition itérative avec raffinement"""
        steps = []
        iterations = min(problem.complexity, 5)
        
        for i in range(iterations):
            # Étape d'itération
            iter_step = PlanStep(
                id=f"{problem.id}_iter_{i+1}",
                description=f"Itération {i+1}: Raffiner la solution",
                action="iterate",
                parameters={'iteration': i+1, 'total': iterations},
                dependencies=[f"{problem.id}_iter_{i}"] if i > 0 else []
            )
            steps.append(iter_step)
            
            # Évaluation
            eval_step = PlanStep(
                id=f"{problem.id}_iter_{i+1}_eval",
                description=f"Évaluer les résultats de l'itération {i+1}",
                action="evaluate",
                parameters={'iteration': i+1},
                dependencies=[iter_step.id]
            )
            steps.append(eval_step)
        
        # Finalisation
        final_step = PlanStep(
            id=f"{problem.id}_finalize",
            description="Finaliser et valider la solution",
            action="finalize",
            parameters={},
            dependencies=[f"{problem.id}_iter_{iterations}_eval"]
        )
        steps.append(final_step)
        
        return steps
    
    async def _decompose_divide_conquer(self, problem: Problem) -> List[PlanStep]:
        """Décomposition divide-and-conquer"""
        steps = []
        
        # Division
        divide_step = PlanStep(
            id=f"{problem.id}_divide",
            description="Diviser le problème en sous-problèmes",
            action="divide",
            parameters={'problem': problem.to_dict()}
        )
        steps.append(divide_step)
        
        # Conquérir (résoudre chaque partie)
        num_parts = max(2, problem.complexity // 2)
        for i in range(num_parts):
            conquer_step = PlanStep(
                id=f"{problem.id}_conquer_{i+1}",
                description=f"Résoudre la partie {i+1}",
                action="conquer",
                parameters={'part': i+1, 'total': num_parts},
                dependencies=[divide_step.id]
            )
            steps.append(conquer_step)
        
        # Combiner
        combine_step = PlanStep(
            id=f"{problem.id}_combine",
            description="Combiner les solutions partielles",
            action="combine",
            parameters={},
            dependencies=[f"{problem.id}_conquer_{i+1}" for i in range(num_parts)]
        )
        steps.append(combine_step)
        
        return steps
    
    def _generate_substeps(self, problem: Problem, phase: str, phase_idx: int) -> List[str]:
        """Génère des sous-étapes pour une phase"""
        substeps_map = {
            0: ["Analyser les besoins", "Définir les objectifs", "Planifier l'approche"],
            1: ["Implémenter la solution", "Intégrer les composants", "Gérer les erreurs"],
            2: ["Tester unitairement", "Tester l'intégration", "Valider les résultats"],
            3: ["Optimiser les performances", "Documenter la solution", "Préparer le déploiement"]
        }
        
        return substeps_map.get(phase_idx, ["Exécuter les tâches"])
    
    async def execute_plan(
        self,
        problem: Problem,
        plan_steps: List[PlanStep],
        strategy: DecompositionStrategy
    ) -> Solution:
        """
        Exécute un plan de résolution
        
        Args:
            problem: Le problème à résoudre
            plan_steps: Les étapes du plan
            strategy: La stratégie utilisée
            
        Returns:
            Solution avec résultats
        """
        start_time = datetime.now()
        
        solution = Solution(
            problem_id=problem.id,
            plan_steps=plan_steps,
            strategy=strategy,
            confidence=0.0
        )
        
        try:
            # Exécuter les étapes selon la stratégie
            if strategy == DecompositionStrategy.PARALLEL:
                await self._execute_parallel(plan_steps)
            else:
                await self._execute_sequential(plan_steps)
            
            # Vérifier le succès
            solution.success = all(
                step.status == PlanStatus.COMPLETED
                for step in plan_steps
            )
            
            # Calculer la confiance
            completed = sum(1 for s in plan_steps if s.status == PlanStatus.COMPLETED)
            solution.confidence = completed / len(plan_steps) if plan_steps else 0
            
            # Collecter les résultats
            solution.results = {
                step.id: step.result
                for step in plan_steps
                if step.result is not None
            }
            
            # Leçons apprises
            solution.lessons_learned = self._extract_lessons(plan_steps)
            
        except Exception as e:
            solution.success = False
            solution.results['error'] = str(e)
        
        end_time = datetime.now()
        solution.actual_time = (end_time - start_time).total_seconds()
        
        # Sauvegarder la solution
        self.problems_solved[problem.id] = solution
        
        return solution
    
    async def _execute_sequential(self, steps: List[PlanStep]):
        """Exécute les étapes séquentiellement"""
        for step in steps:
            # Vérifier les dépendances
            if not await self._check_dependencies(step, steps):
                step.status = PlanStatus.BLOCKED
                continue
            
            # Exécuter l'étape
            await self._execute_step(step)
    
    async def _execute_parallel(self, steps: List[PlanStep]):
        """Exécute les étapes en parallèle quand possible"""
        # Grouper par niveau de dépendance
        levels = self._group_by_dependency_level(steps)
        
        for level_steps in levels:
            # Exécuter toutes les étapes du même niveau en parallèle
            tasks = [self._execute_step(step) for step in level_steps]
            await asyncio.gather(*tasks)
    
    def _group_by_dependency_level(self, steps: List[PlanStep]) -> List[List[PlanStep]]:
        """Groupe les étapes par niveau de dépendance"""
        levels = []
        remaining = steps.copy()
        completed_ids = set()
        
        while remaining:
            # Trouver les étapes sans dépendances non satisfaites
            current_level = []
            for step in remaining:
                if all(dep in completed_ids for dep in step.dependencies):
                    current_level.append(step)
            
            if not current_level:
                # Deadlock - ajouter le reste
                levels.append(remaining)
                break
            
            levels.append(current_level)
            for step in current_level:
                completed_ids.add(step.id)
                remaining.remove(step)
        
        return levels
    
    async def _check_dependencies(self, step: PlanStep, all_steps: List[PlanStep]) -> bool:
        """Vérifie si les dépendances sont satisfaites"""
        if not step.dependencies:
            return True
        
        for dep_id in step.dependencies:
            dep_step = next((s for s in all_steps if s.id == dep_id), None)
            if not dep_step or dep_step.status != PlanStatus.COMPLETED:
                return False
        
        return True
    
    async def _execute_step(self, step: PlanStep):
        """Exécute une étape individuelle"""
        step.status = PlanStatus.IN_PROGRESS
        step.start_time = datetime.now()
        
        try:
            # Récupérer le handler
            handler = self.action_handlers.get(step.action)
            
            if handler:
                # Exécuter avec le handler
                step.result = await handler(step.parameters)
            else:
                # Exécution simulée
                step.result = {
                    'action': step.action,
                    'description': step.description,
                    'simulated': True
                }
            
            step.status = PlanStatus.COMPLETED
            
        except Exception as e:
            step.error = str(e)
            step.retry_count += 1
            
            if step.retry_count < step.max_retries:
                # Réessayer
                await asyncio.sleep(1)
                await self._execute_step(step)
            else:
                step.status = PlanStatus.FAILED
        
        step.end_time = datetime.now()
    
    def _extract_lessons(self, steps: List[PlanStep]) -> List[str]:
        """Extrait les leçons apprises de l'exécution"""
        lessons = []
        
        # Analyser les échecs
        failed = [s for s in steps if s.status == PlanStatus.FAILED]
        if failed:
            lessons.append(f"{len(failed)} étapes ont échoué - revoir l'approche")
        
        # Analyser les retries
        retried = [s for s in steps if s.retry_count > 0]
        if retried:
            lessons.append(f"{len(retried)} étapes ont nécessité des tentatives multiples")
        
        # Analyser les durées
        durations = [
            (s.end_time - s.start_time).total_seconds()
            for s in steps
            if s.start_time and s.end_time
        ]
        if durations:
            avg_duration = sum(durations) / len(durations)
            lessons.append(f"Durée moyenne par étape: {avg_duration:.2f}s")
        
        return lessons
    
    async def solve_problem(self, problem: Problem) -> Solution:
        """
        Résout un problème de bout en bout
        
        Args:
            problem: Le problème à résoudre
            
        Returns:
            Solution complète
        """
        # 1. Analyser le problème
        analysis = await self.analyze_problem(problem)
        
        # 2. Décomposer
        strategy = analysis['recommended_strategy']
        plan_steps = await self.decompose_problem(problem, strategy)
        
        # 3. Exécuter
        solution = await self.execute_plan(problem, plan_steps, strategy)
        
        return solution
    
    def get_solution(self, problem_id: str) -> Optional[Solution]:
        """Récupère une solution existante"""
        return self.problems_solved.get(problem_id)
    
    def save_solutions(self, filepath: Path):
        """Sauvegarde les solutions"""
        data = {
            pid: sol.to_dict()
            for pid, sol in self.problems_solved.items()
        }
        
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def load_solutions(self, filepath: Path):
        """Charge des solutions sauvegardées"""
        if not filepath.exists():
            return
        
        data = json.loads(filepath.read_text())
        # Note: Reconstruction complète nécessite désérialisation complexe
        # Pour l'instant, on charge juste les IDs
        self.problems_solved = {}
