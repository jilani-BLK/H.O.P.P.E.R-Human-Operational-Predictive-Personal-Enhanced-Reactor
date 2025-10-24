"""
Moteur d'adaptation contextuelle pour HOPPER
Ajuste dynamiquement le comportement selon le contexte, l'historique et les préférences
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ContextType(Enum):
    """Types de contexte"""
    TASK = "task"  # Type de tâche en cours
    USER_STATE = "user_state"  # État de l'utilisateur
    CONVERSATION = "conversation"  # Contexte conversationnel
    ENVIRONMENT = "environment"  # Environnement technique
    TEMPORAL = "temporal"  # Contexte temporel


class AdaptationStrategy(Enum):
    """Stratégies d'adaptation"""
    IMMEDIATE = "immediate"  # Appliquer immédiatement
    GRADUAL = "gradual"  # Adapter progressivement
    VALIDATED = "validated"  # Requiert validation
    EXPERIMENTAL = "experimental"  # Mode test


@dataclass
class ContextSnapshot:
    """Instantané du contexte"""
    timestamp: datetime
    task_type: str
    user_expertise: str  # beginner, intermediate, expert
    conversation_depth: int  # Nombre d'échanges
    recent_topics: List[str]
    environment: Dict[str, Any]
    user_sentiment: str  # positive, neutral, frustrated
    time_of_day: str
    session_duration: float  # minutes


@dataclass
class AdaptationRule:
    """Règle d'adaptation"""
    rule_id: str
    name: str
    description: str
    
    # Conditions
    trigger_conditions: Dict[str, Any]
    context_requirements: List[ContextType]
    
    # Adaptations
    adjustments: Dict[str, Any]
    strategy: AdaptationStrategy
    
    # Métriques
    times_triggered: int = 0
    success_rate: float = 0.0
    last_applied: Optional[datetime] = None
    enabled: bool = True


class AdaptationEngine:
    """
    Moteur d'adaptation contextuelle
    - Analyse le contexte en temps réel
    - Applique des adaptations dynamiques
    - Apprend des patterns de succès
    - Valide avec l'utilisateur si nécessaire
    """
    
    def __init__(
        self,
        memory_manager: Optional[Any] = None,
        preference_manager: Optional[Any] = None,
        feedback_system: Optional[Any] = None,
        storage_path: str = "data/adaptation/"
    ):
        self.memory_manager = memory_manager
        self.preference_manager = preference_manager
        self.feedback_system = feedback_system
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Règles d'adaptation
        self.rules: Dict[str, AdaptationRule] = {}
        
        # Contexte actuel
        self.current_context: Optional[ContextSnapshot] = None
        
        # Historique d'adaptations
        self.adaptation_history: List[Dict[str, Any]] = []
        
        # Comportement par défaut
        self.default_behavior = {
            "detail_level": "moderate",
            "tone": "professional",
            "code_style": "clean",
            "explanation_depth": "balanced",
            "proactivity": "medium"
        }
        
        # Comportement actuel (ajusté)
        self.current_behavior = self.default_behavior.copy()
        
        # Statistiques
        self.stats = {
            "total_adaptations": 0,
            "successful_adaptations": 0,
            "context_updates": 0,
            "rules_triggered": 0
        }
        
        # Initialiser règles par défaut
        self._initialize_default_rules()
        
        # Charger état
        self._load_state()
    
    def update_context(
        self,
        task_type: Optional[str] = None,
        user_expertise: Optional[str] = None,
        conversation_depth: Optional[int] = None,
        recent_topics: Optional[List[str]] = None,
        environment: Optional[Dict[str, Any]] = None,
        user_sentiment: Optional[str] = None
    ) -> None:
        """Met à jour le contexte actuel"""
        
        # Créer snapshot
        self.current_context = ContextSnapshot(
            timestamp=datetime.now(),
            task_type=task_type or (self.current_context.task_type if self.current_context else "general"),
            user_expertise=user_expertise or (self.current_context.user_expertise if self.current_context else "intermediate"),
            conversation_depth=conversation_depth or (self.current_context.conversation_depth if self.current_context else 0),
            recent_topics=recent_topics or (self.current_context.recent_topics if self.current_context else []),
            environment=environment or (self.current_context.environment if self.current_context else {}),
            user_sentiment=user_sentiment or (self.current_context.user_sentiment if self.current_context else "neutral"),
            time_of_day=self._get_time_of_day(),
            session_duration=self._calculate_session_duration()
        )
        
        self.stats["context_updates"] += 1
        
        # Analyser et adapter
        self._analyze_and_adapt()
    
    def _get_time_of_day(self) -> str:
        """Détermine le moment de la journée"""
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _calculate_session_duration(self) -> float:
        """Calcule la durée de la session en minutes"""
        if not self.adaptation_history:
            return 0.0
        
        first_adaptation = self.adaptation_history[0]["timestamp"]
        duration = (datetime.now() - datetime.fromisoformat(first_adaptation)).total_seconds() / 60
        return duration
    
    def _analyze_and_adapt(self) -> None:
        """Analyse le contexte et applique des adaptations"""
        
        if not self.current_context:
            return
        
        # Vérifier chaque règle
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if self._check_rule_conditions(rule):
                self._apply_adaptation(rule)
    
    def _check_rule_conditions(self, rule: AdaptationRule) -> bool:
        """Vérifie si les conditions d'une règle sont remplies"""
        
        if not self.current_context:
            return False
        
        conditions = rule.trigger_conditions
        
        # Vérifier chaque condition
        for key, expected_value in conditions.items():
            if key == "task_type":
                if self.current_context.task_type != expected_value:
                    return False
            
            elif key == "user_expertise":
                if self.current_context.user_expertise != expected_value:
                    return False
            
            elif key == "conversation_depth_min":
                if self.current_context.conversation_depth < expected_value:
                    return False
            
            elif key == "user_sentiment":
                if self.current_context.user_sentiment != expected_value:
                    return False
            
            elif key == "time_of_day":
                if self.current_context.time_of_day != expected_value:
                    return False
        
        return True
    
    def _apply_adaptation(self, rule: AdaptationRule) -> None:
        """Applique une adaptation"""
        
        # Enregistrer
        adaptation_record = {
            "timestamp": datetime.now().isoformat(),
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "strategy": rule.strategy.value,
            "adjustments": rule.adjustments,
            "context": {
                "task_type": self.current_context.task_type if self.current_context else None,
                "user_expertise": self.current_context.user_expertise if self.current_context else None,
                "user_sentiment": self.current_context.user_sentiment if self.current_context else None
            }
        }
        
        # Appliquer selon la stratégie
        if rule.strategy == AdaptationStrategy.IMMEDIATE:
            self._apply_immediate(rule.adjustments)
            adaptation_record["applied"] = True
        
        elif rule.strategy == AdaptationStrategy.GRADUAL:
            self._apply_gradual(rule.adjustments)
            adaptation_record["applied"] = True
        
        elif rule.strategy == AdaptationStrategy.VALIDATED:
            # Stocker pour validation
            adaptation_record["applied"] = False
            adaptation_record["requires_validation"] = True
        
        elif rule.strategy == AdaptationStrategy.EXPERIMENTAL:
            # Appliquer avec flag expérimental
            self._apply_immediate(rule.adjustments)
            adaptation_record["applied"] = True
            adaptation_record["experimental"] = True
        
        # Mettre à jour statistiques
        rule.times_triggered += 1
        rule.last_applied = datetime.now()
        self.stats["total_adaptations"] += 1
        self.stats["rules_triggered"] += 1
        
        # Enregistrer
        self.adaptation_history.append(adaptation_record)
        
        # Limiter historique
        if len(self.adaptation_history) > 500:
            self.adaptation_history = self.adaptation_history[-500:]
        
        # Sauvegarder
        self._save_state()
    
    def _apply_immediate(self, adjustments: Dict[str, Any]) -> None:
        """Applique des ajustements immédiatement"""
        for key, value in adjustments.items():
            if key in self.current_behavior:
                self.current_behavior[key] = value
    
    def _apply_gradual(self, adjustments: Dict[str, Any]) -> None:
        """Applique des ajustements graduellement"""
        # Pour l'instant, appliquer directement
        # Une vraie implémentation pourrait ajuster progressivement sur plusieurs interactions
        for key, value in adjustments.items():
            if key in self.current_behavior:
                self.current_behavior[key] = value
    
    def get_current_behavior(self) -> Dict[str, Any]:
        """Retourne le comportement actuellement configuré"""
        
        # Intégrer les préférences utilisateur si disponibles
        if self.preference_manager:
            prefs = self.preference_manager.get_adaptation_config()
            
            # Fusionner avec comportement actuel
            behavior = self.current_behavior.copy()
            
            if "detail_level" in prefs:
                behavior["detail_level"] = prefs["detail_level"]
            
            if "tone" in prefs:
                behavior["tone"] = prefs["tone"]
            
            return behavior
        
        return self.current_behavior.copy()
    
    def add_rule(
        self,
        name: str,
        description: str,
        trigger_conditions: Dict[str, Any],
        adjustments: Dict[str, Any],
        strategy: AdaptationStrategy = AdaptationStrategy.IMMEDIATE,
        context_requirements: Optional[List[ContextType]] = None
    ) -> str:
        """Ajoute une nouvelle règle d'adaptation"""
        
        rule_id = f"rule_{len(self.rules)}"
        
        rule = AdaptationRule(
            rule_id=rule_id,
            name=name,
            description=description,
            trigger_conditions=trigger_conditions,
            context_requirements=context_requirements or [],
            adjustments=adjustments,
            strategy=strategy
        )
        
        self.rules[rule_id] = rule
        self._save_state()
        
        return rule_id
    
    def remove_rule(self, rule_id: str) -> bool:
        """Supprime une règle"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self._save_state()
            return True
        return False
    
    def enable_rule(self, rule_id: str, enabled: bool = True) -> bool:
        """Active/désactive une règle"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = enabled
            self._save_state()
            return True
        return False
    
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """Retourne les règles actives"""
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "times_triggered": rule.times_triggered,
                "success_rate": rule.success_rate,
                "last_applied": rule.last_applied.isoformat() if rule.last_applied else None
            }
            for rule in self.rules.values()
            if rule.enabled
        ]
    
    def reset_to_default(self) -> None:
        """Réinitialise au comportement par défaut"""
        self.current_behavior = self.default_behavior.copy()
        self._save_state()
    
    def _initialize_default_rules(self) -> None:
        """Initialise les règles par défaut"""
        
        # Règle: Utilisateur débutant
        self.add_rule(
            name="Beginner Assistance",
            description="Ajuste le niveau de détail pour les débutants",
            trigger_conditions={"user_expertise": "beginner"},
            adjustments={
                "detail_level": "detailed",
                "explanation_depth": "thorough",
                "code_style": "commented"
            },
            strategy=AdaptationStrategy.IMMEDIATE
        )
        
        # Règle: Utilisateur expert
        self.add_rule(
            name="Expert Mode",
            description="Mode concis pour utilisateurs experts",
            trigger_conditions={"user_expertise": "expert"},
            adjustments={
                "detail_level": "concise",
                "explanation_depth": "minimal",
                "code_style": "clean"
            },
            strategy=AdaptationStrategy.IMMEDIATE
        )
        
        # Règle: Utilisateur frustré
        self.add_rule(
            name="Frustration Handling",
            description="Ajuste le ton si l'utilisateur semble frustré",
            trigger_conditions={"user_sentiment": "frustrated"},
            adjustments={
                "tone": "empathetic",
                "detail_level": "detailed",
                "proactivity": "high"
            },
            strategy=AdaptationStrategy.IMMEDIATE
        )
        
        # Règle: Conversation longue
        self.add_rule(
            name="Long Conversation",
            description="Ajuste pour conversations longues",
            trigger_conditions={"conversation_depth_min": 10},
            adjustments={
                "detail_level": "concise",
                "proactivity": "high"
            },
            strategy=AdaptationStrategy.GRADUAL
        )
        
        # Règle: Tâche de debugging
        self.add_rule(
            name="Debugging Mode",
            description="Mode spécial pour le debugging",
            trigger_conditions={"task_type": "debugging"},
            adjustments={
                "detail_level": "detailed",
                "explanation_depth": "thorough",
                "proactivity": "high"
            },
            strategy=AdaptationStrategy.IMMEDIATE
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        
        return {
            **self.stats,
            "active_rules": len([r for r in self.rules.values() if r.enabled]),
            "total_rules": len(self.rules),
            "recent_adaptations": len([
                a for a in self.adaptation_history
                if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=24)
            ]),
            "current_behavior": self.current_behavior,
            "context": {
                "task_type": self.current_context.task_type if self.current_context else None,
                "user_expertise": self.current_context.user_expertise if self.current_context else None,
                "conversation_depth": self.current_context.conversation_depth if self.current_context else 0
            }
        }
    
    def _save_state(self) -> None:
        """Sauvegarde l'état"""
        
        # Sauvegarder règles
        rules_file = self.storage_path / "rules.json"
        rules_data = {
            rule_id: {
                "name": rule.name,
                "description": rule.description,
                "trigger_conditions": rule.trigger_conditions,
                "context_requirements": [c.value for c in rule.context_requirements],
                "adjustments": rule.adjustments,
                "strategy": rule.strategy.value,
                "times_triggered": rule.times_triggered,
                "success_rate": rule.success_rate,
                "last_applied": rule.last_applied.isoformat() if rule.last_applied else None,
                "enabled": rule.enabled
            }
            for rule_id, rule in self.rules.items()
        }
        
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder historique
        history_file = self.storage_path / "adaptation_history.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.adaptation_history, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder comportement actuel
        behavior_file = self.storage_path / "current_behavior.json"
        with open(behavior_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_behavior, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder stats
        stats_file = self.storage_path / "stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def _load_state(self) -> None:
        """Charge l'état"""
        
        try:
            # Charger règles
            rules_file = self.storage_path / "rules.json"
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                
                for rule_id, rule_data in rules_data.items():
                    # Ne pas recharger les règles par défaut
                    if rule_id in self.rules:
                        continue
                    
                    rule = AdaptationRule(
                        rule_id=rule_id,
                        name=rule_data["name"],
                        description=rule_data["description"],
                        trigger_conditions=rule_data["trigger_conditions"],
                        context_requirements=[ContextType(c) for c in rule_data.get("context_requirements", [])],
                        adjustments=rule_data["adjustments"],
                        strategy=AdaptationStrategy(rule_data["strategy"]),
                        times_triggered=rule_data.get("times_triggered", 0),
                        success_rate=rule_data.get("success_rate", 0.0),
                        last_applied=datetime.fromisoformat(rule_data["last_applied"]) if rule_data.get("last_applied") else None,
                        enabled=rule_data.get("enabled", True)
                    )
                    self.rules[rule_id] = rule
            
            # Charger historique
            history_file = self.storage_path / "adaptation_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.adaptation_history = json.load(f)
            
            # Charger comportement
            behavior_file = self.storage_path / "current_behavior.json"
            if behavior_file.exists():
                with open(behavior_file, 'r', encoding='utf-8') as f:
                    self.current_behavior = json.load(f)
            
            # Charger stats
            stats_file = self.storage_path / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.stats.update(json.load(f))
        
        except Exception as e:
            print(f"Erreur lors du chargement de l'état: {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    engine = AdaptationEngine()
    
    # Mettre à jour le contexte
    engine.update_context(
        task_type="debugging",
        user_expertise="intermediate",
        conversation_depth=5,
        user_sentiment="neutral"
    )
    
    # Récupérer comportement adapté
    behavior = engine.get_current_behavior()
    print(f"\nComportement adapté:")
    print(json.dumps(behavior, indent=2))
    
    # Statistiques
    stats = engine.get_statistics()
    print(f"\nStatistiques:")
    print(json.dumps(stats, indent=2, default=str))
