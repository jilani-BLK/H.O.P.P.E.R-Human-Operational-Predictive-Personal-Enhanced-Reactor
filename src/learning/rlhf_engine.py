"""
Système RLHF (Reinforcement Learning from Human Feedback)
Apprentissage par renforcement basé sur le feedback humain
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RewardType(Enum):
    """Types de récompense"""
    QUALITY = "quality"  # Qualité de la réponse
    RELEVANCE = "relevance"  # Pertinence
    ACCURACY = "accuracy"  # Précision
    HELPFULNESS = "helpfulness"  # Utilité
    CLARITY = "clarity"  # Clarté
    COMPLETENESS = "completeness"  # Complétude


@dataclass
class RewardSignal:
    """Signal de récompense"""
    id: str
    context: str
    action: str  # Réponse de HOPPER
    reward_type: RewardType
    score: float  # -1.0 à 1.0
    user_rating: Optional[int] = None  # 1-5
    human_feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyUpdate:
    """Mise à jour de politique"""
    id: str
    context_pattern: str
    old_action: str
    new_action: str
    expected_reward: float
    confidence: float
    validation_required: bool = True
    validated: bool = False
    applied: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningSession:
    """Session d'apprentissage"""
    id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    interactions: int = 0
    total_reward: float = 0.0
    average_reward: float = 0.0
    improvements_detected: int = 0
    policy_updates: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RLHFEngine:
    """
    Moteur RLHF - Apprentissage par renforcement avec feedback humain
    
    Fonctionnalités:
    - Collection de feedback humain
    - Calcul de récompenses
    - Apprentissage de politiques
    - Validation humaine des changements
    - Amélioration continue supervisée
    """
    
    def __init__(
        self,
        storage_dir: Path = Path("data/rlhf"),
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        min_confidence: float = 0.7,
        require_validation: bool = True
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Hyperparamètres
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.min_confidence = min_confidence
        self.require_validation = require_validation
        
        # Stockages
        self.rewards_file = self.storage_dir / "reward_signals.json"
        self.policy_file = self.storage_dir / "policy_updates.json"
        self.sessions_file = self.storage_dir / "learning_sessions.json"
        
        # Données en mémoire
        self.reward_signals: List[RewardSignal] = []
        self.policy_updates: Dict[str, PolicyUpdate] = {}
        self.learning_sessions: Dict[str, LearningSession] = {}
        
        # État d'apprentissage
        self.action_values: Dict[str, float] = {}  # Q-values simplifiés
        self.state_visits: Dict[str, int] = {}
        
        self._load_all()
        
        logger.info("RLHFEngine initialisé")
    
    def start_session(self, user_id: str) -> LearningSession:
        """Démarre une session d'apprentissage"""
        session_id = f"{user_id}_{datetime.now().isoformat()}"
        
        session = LearningSession(
            id=session_id,
            user_id=user_id,
            start_time=datetime.now()
        )
        
        self.learning_sessions[session_id] = session
        
        logger.info(f"Session d'apprentissage démarrée: {session_id}")
        return session
    
    def end_session(self, session_id: str) -> LearningSession:
        """Termine une session d'apprentissage"""
        if session_id not in self.learning_sessions:
            raise ValueError(f"Session inconnue: {session_id}")
        
        session = self.learning_sessions[session_id]
        session.end_time = datetime.now()
        
        if session.interactions > 0:
            session.average_reward = session.total_reward / session.interactions
        
        self._save_sessions()
        
        logger.info(f"Session terminée: {session_id}, reward moyen: {session.average_reward:.3f}")
        return session
    
    def record_reward(
        self,
        session_id: str,
        context: str,
        action: str,
        reward_type: RewardType,
        score: float,
        user_rating: Optional[int] = None,
        human_feedback: Optional[str] = None
    ) -> RewardSignal:
        """Enregistre un signal de récompense"""
        # Valider le score
        score = max(-1.0, min(1.0, score))
        
        reward = RewardSignal(
            id=f"{session_id}_{len(self.reward_signals)}",
            context=context,
            action=action,
            reward_type=reward_type,
            score=score,
            user_rating=user_rating,
            human_feedback=human_feedback
        )
        
        self.reward_signals.append(reward)
        
        # Mettre à jour la session
        if session_id in self.learning_sessions:
            session = self.learning_sessions[session_id]
            session.interactions += 1
            session.total_reward += score
        
        # Mettre à jour les Q-values
        self._update_action_value(context, action, score)
        
        # Vérifier si une mise à jour de politique est nécessaire
        if score < -0.3:  # Récompense négative significative
            self._suggest_policy_update(context, action, score, human_feedback)
        
        self._save_rewards()
        
        logger.info(f"Récompense enregistrée: {reward_type.value} = {score:.2f}")
        return reward
    
    def convert_rating_to_reward(
        self,
        rating: int,
        reward_type: RewardType = RewardType.QUALITY
    ) -> float:
        """Convertit une note (1-5) en signal de récompense (-1.0 à 1.0)"""
        # Mapping: 1→-1.0, 2→-0.5, 3→0.0, 4→0.5, 5→1.0
        reward = (rating - 3) / 2.0
        return max(-1.0, min(1.0, reward))
    
    def _update_action_value(self, context: str, action: str, reward: float):
        """Met à jour la valeur d'action (Q-learning simplifié)"""
        state_action = f"{context}::{action}"
        
        # Initialiser si nécessaire
        if state_action not in self.action_values:
            self.action_values[state_action] = 0.0
            self.state_visits[state_action] = 0
        
        # Incrémenter les visites
        self.state_visits[state_action] += 1
        
        # Mise à jour avec learning rate adaptatif
        adaptive_lr = self.learning_rate / (1 + 0.1 * self.state_visits[state_action])
        
        old_value = self.action_values[state_action]
        self.action_values[state_action] += adaptive_lr * (reward - old_value)
        
        logger.debug(f"Q-value mis à jour: {old_value:.3f} → {self.action_values[state_action]:.3f}")
    
    def _suggest_policy_update(
        self,
        context: str,
        failed_action: str,
        reward: float,
        human_feedback: Optional[str]
    ):
        """Suggère une mise à jour de politique"""
        # Trouver des actions similaires avec de meilleures récompenses
        similar_contexts = [
            (k, v) for k, v in self.action_values.items()
            if k.startswith(context.split()[0])  # Contextes similaires
            and v > 0.5  # Bonne récompense
        ]
        
        if not similar_contexts:
            logger.debug("Aucune action alternative trouvée")
            return
        
        # Meilleure action alternative
        best_state_action, best_value = max(similar_contexts, key=lambda x: x[1])
        _, best_action = best_state_action.split("::", 1)
        
        # Calculer la confiance
        confidence = min(1.0, best_value + 0.3)
        
        # Créer la mise à jour
        update_id = f"policy_{len(self.policy_updates)}"
        
        policy_update = PolicyUpdate(
            id=update_id,
            context_pattern=context,
            old_action=failed_action,
            new_action=best_action,
            expected_reward=best_value,
            confidence=confidence,
            validation_required=self.require_validation
        )
        
        self.policy_updates[update_id] = policy_update
        
        self._save_policy()
        
        logger.info(f"Mise à jour de politique suggérée: {update_id} (confiance: {confidence:.2f})")
    
    def get_pending_validations(self) -> List[PolicyUpdate]:
        """Récupère les mises à jour en attente de validation"""
        return [
            update for update in self.policy_updates.values()
            if update.validation_required and not update.validated
        ]
    
    def validate_policy_update(self, update_id: str, approved: bool) -> PolicyUpdate:
        """Valide ou rejette une mise à jour de politique"""
        if update_id not in self.policy_updates:
            raise ValueError(f"Mise à jour inconnue: {update_id}")
        
        update = self.policy_updates[update_id]
        update.validated = True
        
        if approved:
            update.applied = True
            logger.info(f"Mise à jour approuvée et appliquée: {update_id}")
        else:
            logger.info(f"Mise à jour rejetée: {update_id}")
        
        self._save_policy()
        return update
    
    def get_best_action(
        self,
        context: str,
        candidate_actions: List[str]
    ) -> Tuple[str, float]:
        """Sélectionne la meilleure action pour un contexte"""
        if not candidate_actions:
            raise ValueError("Aucune action candidate")
        
        # Calculer les valeurs pour chaque action
        action_scores = []
        for action in candidate_actions:
            state_action = f"{context}::{action}"
            value = self.action_values.get(state_action, 0.0)
            action_scores.append((action, value))
        
        # Sélectionner la meilleure
        best_action, best_value = max(action_scores, key=lambda x: x[1])
        
        return best_action, best_value
    
    def analyze_learning_progress(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyse les progrès d'apprentissage"""
        # Filtrer les sessions
        if user_id:
            sessions = [
                s for s in self.learning_sessions.values()
                if s.user_id == user_id
            ]
        else:
            sessions = list(self.learning_sessions.values())
        
        if not sessions:
            return {
                "sessions": 0,
                "average_reward": 0.0,
                "improvement_trend": "no_data"
            }
        
        # Calculer les métriques
        total_interactions = sum(s.interactions for s in sessions)
        avg_reward = sum(s.total_reward for s in sessions) / total_interactions if total_interactions > 0 else 0
        
        # Analyser la tendance
        if len(sessions) > 1:
            recent_sessions = sorted(sessions, key=lambda s: s.start_time)[-5:]
            old_sessions = sorted(sessions, key=lambda s: s.start_time)[:5]
            
            recent_avg = sum(s.average_reward for s in recent_sessions) / len(recent_sessions)
            old_avg = sum(s.average_reward for s in old_sessions) / len(old_sessions)
            
            improvement = recent_avg - old_avg
            trend = "improving" if improvement > 0.1 else "stable" if abs(improvement) <= 0.1 else "declining"
        else:
            improvement = 0
            trend = "insufficient_data"
        
        # Analyser les types de récompenses
        reward_by_type = {}
        for reward in self.reward_signals:
            rtype = reward.reward_type.value
            if rtype not in reward_by_type:
                reward_by_type[rtype] = []
            reward_by_type[rtype].append(reward.score)
        
        reward_averages = {
            rtype: sum(scores) / len(scores)
            for rtype, scores in reward_by_type.items()
        }
        
        return {
            "sessions": len(sessions),
            "total_interactions": total_interactions,
            "average_reward": avg_reward,
            "improvement": improvement,
            "trend": trend,
            "reward_by_type": reward_averages,
            "policy_updates": {
                "total": len(self.policy_updates),
                "pending": len(self.get_pending_validations()),
                "applied": sum(1 for u in self.policy_updates.values() if u.applied)
            },
            "learned_actions": len(self.action_values)
        }
    
    def export_learning_model(self) -> Dict[str, Any]:
        """Exporte le modèle d'apprentissage"""
        return {
            "action_values": self.action_values,
            "state_visits": self.state_visits,
            "policy_updates": [
                asdict(u) for u in self.policy_updates.values()
                if u.applied
            ],
            "hyperparameters": {
                "learning_rate": self.learning_rate,
                "discount_factor": self.discount_factor,
                "min_confidence": self.min_confidence
            },
            "exported_at": datetime.now().isoformat()
        }
    
    def import_learning_model(self, model_data: Dict[str, Any]):
        """Importe un modèle d'apprentissage"""
        if "action_values" in model_data:
            self.action_values.update(model_data["action_values"])
        
        if "state_visits" in model_data:
            self.state_visits.update(model_data["state_visits"])
        
        if "policy_updates" in model_data:
            for update_dict in model_data["policy_updates"]:
                update_dict['timestamp'] = datetime.fromisoformat(update_dict['timestamp'])
                update = PolicyUpdate(**update_dict)
                self.policy_updates[update.id] = update
        
        logger.info("Modèle d'apprentissage importé")
    
    def _load_all(self):
        """Charge toutes les données"""
        self._load_rewards()
        self._load_policy()
        self._load_sessions()
    
    def _load_rewards(self):
        """Charge les signaux de récompense"""
        if self.rewards_file.exists():
            try:
                with open(self.rewards_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        entry['reward_type'] = RewardType(entry['reward_type'])
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        self.reward_signals.append(RewardSignal(**entry))
            except Exception as e:
                logger.error(f"Erreur chargement rewards: {e}")
    
    def _save_rewards(self):
        """Sauvegarde les récompenses"""
        try:
            data = []
            for reward in self.reward_signals:
                reward_dict = asdict(reward)
                reward_dict['reward_type'] = reward.reward_type.value
                reward_dict['timestamp'] = reward.timestamp.isoformat()
                data.append(reward_dict)
            
            with open(self.rewards_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde rewards: {e}")
    
    def _load_policy(self):
        """Charge les mises à jour de politique"""
        if self.policy_file.exists():
            try:
                with open(self.policy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        update = PolicyUpdate(**entry)
                        self.policy_updates[update.id] = update
            except Exception as e:
                logger.error(f"Erreur chargement policy: {e}")
    
    def _save_policy(self):
        """Sauvegarde les mises à jour de politique"""
        try:
            data = []
            for update in self.policy_updates.values():
                update_dict = asdict(update)
                update_dict['timestamp'] = update.timestamp.isoformat()
                data.append(update_dict)
            
            with open(self.policy_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde policy: {e}")
    
    def _load_sessions(self):
        """Charge les sessions d'apprentissage"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        entry['start_time'] = datetime.fromisoformat(entry['start_time'])
                        if entry.get('end_time'):
                            entry['end_time'] = datetime.fromisoformat(entry['end_time'])
                        session = LearningSession(**entry)
                        self.learning_sessions[session.id] = session
            except Exception as e:
                logger.error(f"Erreur chargement sessions: {e}")
    
    def _save_sessions(self):
        """Sauvegarde les sessions"""
        try:
            data = []
            for session in self.learning_sessions.values():
                session_dict = asdict(session)
                session_dict['start_time'] = session.start_time.isoformat()
                if session.end_time:
                    session_dict['end_time'] = session.end_time.isoformat()
                else:
                    session_dict['end_time'] = None
                data.append(session_dict)
            
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde sessions: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques globales"""
        return {
            "total_rewards": len(self.reward_signals),
            "total_policy_updates": len(self.policy_updates),
            "total_sessions": len(self.learning_sessions),
            "learned_actions": len(self.action_values),
            "average_reward": sum(r.score for r in self.reward_signals) / len(self.reward_signals) if self.reward_signals else 0
        }
