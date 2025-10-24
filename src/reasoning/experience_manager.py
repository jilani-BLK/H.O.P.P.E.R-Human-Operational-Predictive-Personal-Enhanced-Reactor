"""
Système d'apprentissage par expérience HOPPER
Mémorise les solutions et améliore les performances
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from collections import defaultdict


class LearningStrategy(Enum):
    """Stratégies d'apprentissage"""
    MEMORIZATION = "memorization"  # Mémoriser toutes les solutions
    PATTERN_EXTRACTION = "pattern_extraction"  # Extraire des patterns
    INCREMENTAL = "incremental"  # Apprentissage incrémental
    REINFORCEMENT = "reinforcement"  # Renforcement basé sur succès


@dataclass
class Experience:
    """Une expérience d'apprentissage"""
    id: str
    problem_type: str
    problem_description: str
    solution_approach: str
    success: bool
    execution_time: float
    complexity: int
    context: Dict[str, Any] = field(default_factory=dict)
    patterns_found: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    reuse_count: int = 0
    success_rate: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'problem_type': self.problem_type,
            'problem_description': self.problem_description,
            'solution_approach': self.solution_approach,
            'success': self.success,
            'execution_time': self.execution_time,
            'complexity': self.complexity,
            'context': self.context,
            'patterns_found': self.patterns_found,
            'lessons_learned': self.lessons_learned,
            'timestamp': self.timestamp.isoformat(),
            'reuse_count': self.reuse_count,
            'success_rate': self.success_rate
        }


@dataclass
class Pattern:
    """Un pattern de solution réutilisable"""
    id: str
    name: str
    problem_category: str
    approach: str
    conditions: List[str]
    steps: List[str]
    success_rate: float
    usage_count: int = 0
    average_time: float = 0.0
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'problem_category': self.problem_category,
            'approach': self.approach,
            'conditions': self.conditions,
            'steps': self.steps,
            'success_rate': self.success_rate,
            'usage_count': self.usage_count,
            'average_time': self.average_time,
            'examples': self.examples
        }


class ExperienceManager:
    """
    Gestionnaire d'expériences et d'apprentissage
    Mémorise les solutions et améliore les performances
    """
    
    def __init__(self, strategy: LearningStrategy = LearningStrategy.PATTERN_EXTRACTION):
        self.strategy = strategy
        self.experiences: Dict[str, Experience] = {}
        self.patterns: Dict[str, Pattern] = {}
        self.problem_type_index: Dict[str, List[str]] = defaultdict(list)
        self.success_patterns: List[Pattern] = []
        self.failure_patterns: List[str] = []
        
    async def record_experience(
        self,
        problem_type: str,
        problem_description: str,
        solution_approach: str,
        success: bool,
        execution_time: float,
        complexity: int,
        context: Optional[Dict[str, Any]] = None,
        lessons: Optional[List[str]] = None
    ) -> Experience:
        """
        Enregistre une nouvelle expérience
        
        Args:
            problem_type: Type de problème
            problem_description: Description
            solution_approach: Approche utilisée
            success: Succès ou échec
            execution_time: Temps d'exécution
            complexity: Complexité du problème
            context: Contexte additionnel
            lessons: Leçons apprises
            
        Returns:
            Experience créée
        """
        exp_id = f"exp_{len(self.experiences) + 1}_{datetime.now().timestamp()}"
        
        experience = Experience(
            id=exp_id,
            problem_type=problem_type,
            problem_description=problem_description,
            solution_approach=solution_approach,
            success=success,
            execution_time=execution_time,
            complexity=complexity,
            context=context or {},
            lessons_learned=lessons or []
        )
        
        # Extraire des patterns
        patterns = await self._extract_patterns(experience)
        experience.patterns_found = patterns
        
        # Sauvegarder
        self.experiences[exp_id] = experience
        self.problem_type_index[problem_type].append(exp_id)
        
        # Apprendre selon la stratégie
        if self.strategy == LearningStrategy.PATTERN_EXTRACTION:
            await self._learn_from_patterns(experience)
        elif self.strategy == LearningStrategy.REINFORCEMENT:
            await self._reinforce_learning(experience)
        
        return experience
    
    async def _extract_patterns(self, experience: Experience) -> List[str]:
        """Extrait des patterns d'une expérience"""
        patterns = []
        
        # Pattern de succès
        if experience.success:
            patterns.append(f"SUCCESS_{experience.problem_type}_{experience.solution_approach}")
        else:
            patterns.append(f"FAILURE_{experience.problem_type}_{experience.solution_approach}")
        
        # Patterns de complexité
        if experience.complexity <= 3:
            patterns.append("LOW_COMPLEXITY")
        elif experience.complexity <= 6:
            patterns.append("MEDIUM_COMPLEXITY")
        else:
            patterns.append("HIGH_COMPLEXITY")
        
        # Patterns de performance
        if experience.execution_time < 1.0:
            patterns.append("FAST_EXECUTION")
        elif experience.execution_time < 10.0:
            patterns.append("NORMAL_EXECUTION")
        else:
            patterns.append("SLOW_EXECUTION")
        
        return patterns
    
    async def _learn_from_patterns(self, experience: Experience):
        """Apprend à partir des patterns extraits"""
        if not experience.success:
            # Enregistrer les échecs pour les éviter
            self.failure_patterns.append(
                f"{experience.problem_type}_{experience.solution_approach}"
            )
            return
        
        # Chercher ou créer un pattern
        pattern_id = f"pattern_{experience.problem_type}_{experience.solution_approach}"
        
        if pattern_id in self.patterns:
            # Mettre à jour le pattern existant
            pattern = self.patterns[pattern_id]
            pattern.usage_count += 1
            
            # Recalculer le taux de succès
            total = pattern.usage_count
            pattern.success_rate = (
                (pattern.success_rate * (total - 1) + (1.0 if experience.success else 0.0)) / total
            )
            
            # Recalculer le temps moyen
            pattern.average_time = (
                (pattern.average_time * (total - 1) + experience.execution_time) / total
            )
            
        else:
            # Créer un nouveau pattern
            pattern = Pattern(
                id=pattern_id,
                name=f"{experience.problem_type} avec {experience.solution_approach}",
                problem_category=experience.problem_type,
                approach=experience.solution_approach,
                conditions=self._extract_conditions(experience),
                steps=self._extract_steps(experience),
                success_rate=1.0 if experience.success else 0.0,
                usage_count=1,
                average_time=experience.execution_time,
                examples=[experience.problem_description]
            )
            
            self.patterns[pattern_id] = pattern
            
            if pattern.success_rate >= 0.8:
                self.success_patterns.append(pattern)
    
    def _extract_conditions(self, experience: Experience) -> List[str]:
        """Extrait les conditions d'application d'un pattern"""
        conditions = []
        
        conditions.append(f"Type de problème: {experience.problem_type}")
        conditions.append(f"Complexité: {experience.complexity}")
        
        if experience.context:
            for key, value in experience.context.items():
                conditions.append(f"{key}: {value}")
        
        return conditions
    
    def _extract_steps(self, experience: Experience) -> List[str]:
        """Extrait les étapes d'un pattern"""
        # Par défaut, utiliser l'approche de solution
        steps = [
            "Analyser le problème",
            f"Appliquer l'approche: {experience.solution_approach}",
            "Valider le résultat"
        ]
        
        return steps
    
    async def _reinforce_learning(self, experience: Experience):
        """Renforcement basé sur le succès"""
        # Augmenter le score des approches réussies
        if experience.success:
            pattern_key = f"{experience.problem_type}_{experience.solution_approach}"
            if pattern_key in self.patterns:
                self.patterns[pattern_key].success_rate *= 1.1  # Boost de 10%
    
    async def find_similar_experiences(
        self,
        problem_type: str,
        complexity: Optional[int] = None,
        min_success_rate: float = 0.7
    ) -> List[Experience]:
        """
        Trouve des expériences similaires
        
        Args:
            problem_type: Type de problème
            complexity: Complexité (optionnel)
            min_success_rate: Taux de succès minimum
            
        Returns:
            Liste d'expériences similaires triées par pertinence
        """
        candidates = []
        
        # Chercher dans l'index
        exp_ids = self.problem_type_index.get(problem_type, [])
        
        for exp_id in exp_ids:
            exp = self.experiences[exp_id]
            
            # Filtrer par succès
            if not exp.success:
                continue
            
            if exp.success_rate < min_success_rate:
                continue
            
            # Filtrer par complexité si spécifiée
            if complexity is not None:
                complexity_diff = abs(exp.complexity - complexity)
                if complexity_diff > 2:
                    continue
                
                # Score de pertinence
                score = exp.success_rate - (complexity_diff * 0.1)
            else:
                score = exp.success_rate
            
            candidates.append((score, exp))
        
        # Trier par score décroissant
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        return [exp for score, exp in candidates]
    
    async def recommend_approach(
        self,
        problem_type: str,
        complexity: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Recommande une approche basée sur l'expérience
        
        Args:
            problem_type: Type de problème
            complexity: Complexité
            context: Contexte
            
        Returns:
            Recommandation avec approche et confiance
        """
        # Chercher les patterns applicables
        applicable_patterns = []
        
        for pattern in self.patterns.values():
            if pattern.problem_category != problem_type:
                continue
            
            if pattern.success_rate < 0.7:
                continue
            
            # Vérifier les conditions
            conditions_met = True
            for condition in pattern.conditions:
                if 'Complexité:' in condition:
                    # Extraire la complexité du pattern
                    try:
                        pattern_complexity = int(condition.split(':')[1].strip())
                        if abs(pattern_complexity - complexity) > 2:
                            conditions_met = False
                            break
                    except:
                        pass
            
            if conditions_met:
                applicable_patterns.append(pattern)
        
        if not applicable_patterns:
            return None
        
        # Choisir le meilleur pattern
        best_pattern = max(
            applicable_patterns,
            key=lambda p: p.success_rate * (1 + 0.1 * p.usage_count)
        )
        
        return {
            'approach': best_pattern.approach,
            'confidence': best_pattern.success_rate,
            'steps': best_pattern.steps,
            'estimated_time': best_pattern.average_time,
            'based_on_experiences': best_pattern.usage_count,
            'pattern_id': best_pattern.id
        }
    
    async def get_best_practices(self, problem_type: str) -> List[str]:
        """Retourne les meilleures pratiques pour un type de problème"""
        practices = []
        
        # Patterns réussis
        for pattern in self.success_patterns:
            if pattern.problem_category == problem_type:
                practices.append(
                    f"Utiliser {pattern.approach} "
                    f"(succès: {pattern.success_rate:.0%}, "
                    f"utilisé {pattern.usage_count} fois)"
                )
        
        # Leçons apprises
        exp_ids = self.problem_type_index.get(problem_type, [])
        for exp_id in exp_ids:
            exp = self.experiences[exp_id]
            if exp.success and exp.lessons_learned:
                practices.extend(exp.lessons_learned)
        
        # Dédupliquer et trier par pertinence
        practices = list(set(practices))
        
        return practices
    
    async def get_failure_insights(self, problem_type: str) -> List[str]:
        """Retourne les insights sur les échecs"""
        insights = []
        
        exp_ids = self.problem_type_index.get(problem_type, [])
        for exp_id in exp_ids:
            exp = self.experiences[exp_id]
            if not exp.success:
                insights.append(
                    f"Éviter {exp.solution_approach} "
                    f"(échoué avec complexité {exp.complexity})"
                )
                
                if exp.lessons_learned:
                    insights.extend(exp.lessons_learned)
        
        return list(set(insights))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Statistiques d'apprentissage"""
        total_exp = len(self.experiences)
        if total_exp == 0:
            return {
                'total_experiences': 0,
                'success_rate': 0,
                'patterns_discovered': 0,
                'problem_types': 0
            }
        
        successes = sum(1 for exp in self.experiences.values() if exp.success)
        
        return {
            'total_experiences': total_exp,
            'success_rate': successes / total_exp,
            'patterns_discovered': len(self.patterns),
            'successful_patterns': len(self.success_patterns),
            'problem_types': len(self.problem_type_index),
            'most_common_type': max(
                self.problem_type_index.keys(),
                key=lambda k: len(self.problem_type_index[k])
            ) if self.problem_type_index else None,
            'average_complexity': sum(
                exp.complexity for exp in self.experiences.values()
            ) / total_exp
        }
    
    def save(self, filepath: Path):
        """Sauvegarde les expériences"""
        data = {
            'strategy': self.strategy.value,
            'experiences': {
                k: v.to_dict() for k, v in self.experiences.items()
            },
            'patterns': {
                k: v.to_dict() for k, v in self.patterns.items()
            },
            'problem_type_index': dict(self.problem_type_index),
            'failure_patterns': self.failure_patterns
        }
        
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def load(self, filepath: Path):
        """Charge des expériences sauvegardées"""
        if not filepath.exists():
            return
        
        data = json.loads(filepath.read_text())
        
        self.strategy = LearningStrategy(data.get('strategy', 'pattern_extraction'))
        self.problem_type_index = defaultdict(list, data.get('problem_type_index', {}))
        self.failure_patterns = data.get('failure_patterns', [])
        
        # Note: Reconstruction complète nécessiterait une désérialisation plus complexe
        # Pour l'instant, on charge juste les structures de base
