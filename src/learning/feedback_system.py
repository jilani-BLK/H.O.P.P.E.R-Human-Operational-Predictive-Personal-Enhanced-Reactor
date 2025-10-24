"""
Système de feedback et apprentissage RLHF-like pour HOPPER
Intègre les retours utilisateur pour améliorer continuellement les réponses
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class FeedbackType(Enum):
    """Types de feedback"""
    POSITIVE = "positive"  # Réponse satisfaisante
    NEGATIVE = "negative"  # Réponse insatisfaisante
    CORRECTION = "correction"  # Correction apportée par l'utilisateur
    SUGGESTION = "suggestion"  # Suggestion d'amélioration
    ERROR = "error"  # Erreur détectée
    SAFETY = "safety"  # Problème de sécurité


class RewardSignal(Enum):
    """Signaux de récompense pour apprentissage"""
    STRONG_POSITIVE = 1.0
    POSITIVE = 0.5
    NEUTRAL = 0.0
    NEGATIVE = -0.5
    STRONG_NEGATIVE = -1.0


@dataclass
class Feedback:
    """Feedback utilisateur sur une interaction"""
    id: str
    timestamp: datetime
    feedback_type: FeedbackType
    reward_signal: float  # -1 à +1
    
    # Contexte de l'interaction
    interaction_id: str
    prompt: str
    response: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Détails du feedback
    comment: Optional[str] = None
    correction: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Analyse
    processed: bool = False
    patterns_extracted: List[str] = field(default_factory=list)
    action_taken: Optional[str] = None


@dataclass
class ResponsePattern:
    """Pattern de réponse identifié"""
    pattern_id: str
    pattern_type: str  # error, success, style, format, content
    description: str
    
    # Métriques
    occurrences: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0
    average_reward: float = 0.0
    
    # Détails
    examples: List[Dict[str, Any]] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        total = self.positive_feedback + self.negative_feedback
        return self.positive_feedback / total if total > 0 else 0.5


class FeedbackSystem:
    """
    Système de feedback et apprentissage inspiré de RLHF
    - Collecte et analyse les retours utilisateur
    - Identifie patterns d'erreurs et de succès
    - Génère des corrections et améliorations
    - Ajuste le comportement du système
    """
    
    def __init__(
        self,
        storage_path: str = "data/feedback/",
        memory_manager: Optional[Any] = None,
        preference_manager: Optional[Any] = None
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.memory_manager = memory_manager
        self.preference_manager = preference_manager
        
        # Stockage des feedbacks
        self.feedbacks: Dict[str, Feedback] = {}
        
        # Patterns identifiés
        self.patterns: Dict[str, ResponsePattern] = {}
        
        # Règles de correction apprises
        self.correction_rules: List[Dict[str, Any]] = []
        
        # Statistiques
        self.stats = {
            "total_feedbacks": 0,
            "positive_feedbacks": 0,
            "negative_feedbacks": 0,
            "corrections_applied": 0,
            "patterns_identified": 0,
            "average_reward": 0.0
        }
        
        # Charger l'état
        self._load_state()
    
    def submit_feedback(
        self,
        interaction_id: str,
        prompt: str,
        response: str,
        feedback_type: FeedbackType,
        reward_signal: Optional[float] = None,
        comment: Optional[str] = None,
        correction: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Soumet un feedback sur une interaction
        
        Returns:
            ID du feedback créé
        """
        
        # Calculer reward_signal si non fourni
        if reward_signal is None:
            reward_signal = self._compute_reward(feedback_type)
        
        # Créer le feedback
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        feedback = Feedback(
            id=feedback_id,
            timestamp=datetime.now(),
            feedback_type=feedback_type,
            reward_signal=reward_signal,
            interaction_id=interaction_id,
            prompt=prompt,
            response=response,
            context=context or {},
            comment=comment,
            correction=correction
        )
        
        self.feedbacks[feedback_id] = feedback
        
        # Mettre à jour les statistiques
        self.stats["total_feedbacks"] += 1
        if reward_signal > 0:
            self.stats["positive_feedbacks"] += 1
        elif reward_signal < 0:
            self.stats["negative_feedbacks"] += 1
        
        # Recalculer reward moyen
        total_reward = sum(f.reward_signal for f in self.feedbacks.values())
        self.stats["average_reward"] = total_reward / len(self.feedbacks)
        
        # Traiter le feedback immédiatement
        self._process_feedback(feedback)
        
        # Intégrer avec les autres systèmes
        self._integrate_feedback(feedback)
        
        # Sauvegarder
        self._save_state()
        
        return feedback_id
    
    def _compute_reward(self, feedback_type: FeedbackType) -> float:
        """Calcule un signal de récompense basé sur le type"""
        mapping = {
            FeedbackType.POSITIVE: RewardSignal.POSITIVE.value,
            FeedbackType.NEGATIVE: RewardSignal.NEGATIVE.value,
            FeedbackType.CORRECTION: RewardSignal.NEGATIVE.value,
            FeedbackType.SUGGESTION: RewardSignal.NEUTRAL.value,
            FeedbackType.ERROR: RewardSignal.STRONG_NEGATIVE.value,
            FeedbackType.SAFETY: RewardSignal.STRONG_NEGATIVE.value
        }
        return mapping.get(feedback_type, 0.0)
    
    def _process_feedback(self, feedback: Feedback) -> None:
        """Traite un feedback pour en extraire des insights"""
        
        # Analyser le contenu
        patterns = self._extract_patterns(feedback)
        feedback.patterns_extracted = patterns
        
        # Mettre à jour les patterns
        for pattern_desc in patterns:
            self._update_pattern(pattern_desc, feedback)
        
        # Générer règle de correction si nécessaire
        if feedback.feedback_type in [FeedbackType.CORRECTION, FeedbackType.ERROR]:
            self._generate_correction_rule(feedback)
        
        # Identifier actions à prendre
        actions = self._identify_actions(feedback)
        if actions:
            feedback.action_taken = "; ".join(actions)
            self.stats["corrections_applied"] += len(actions)
        
        feedback.processed = True
    
    def _extract_patterns(self, feedback: Feedback) -> List[str]:
        """Extrait des patterns du feedback"""
        patterns = []
        
        # Pattern de longueur de réponse
        if len(feedback.response) < 100:
            patterns.append("response_too_short")
        elif len(feedback.response) > 2000:
            patterns.append("response_too_long")
        
        # Pattern de correction
        if feedback.correction:
            # Analyser la différence entre response et correction
            if len(feedback.correction) < len(feedback.response) * 0.5:
                patterns.append("correction_shortened")
            elif len(feedback.correction) > len(feedback.response) * 1.5:
                patterns.append("correction_expanded")
            
            # Mots clés dans la correction
            if "précis" in (feedback.comment or "").lower():
                patterns.append("need_more_precision")
            if "détail" in (feedback.comment or "").lower():
                patterns.append("need_more_detail")
        
        # Pattern de feedback négatif
        if feedback.reward_signal < 0:
            if feedback.comment:
                comment_lower = feedback.comment.lower()
                if "erreur" in comment_lower or "faux" in comment_lower:
                    patterns.append("factual_error")
                if "confus" in comment_lower or "clair" in comment_lower:
                    patterns.append("clarity_issue")
                if "incomplet" in comment_lower:
                    patterns.append("incomplete_response")
        
        return patterns
    
    def _update_pattern(self, pattern_desc: str, feedback: Feedback) -> None:
        """Met à jour un pattern avec un nouveau feedback"""
        
        if pattern_desc not in self.patterns:
            # Créer nouveau pattern
            self.patterns[pattern_desc] = ResponsePattern(
                pattern_id=pattern_desc,
                pattern_type=self._classify_pattern(pattern_desc),
                description=pattern_desc
            )
            self.stats["patterns_identified"] += 1
        
        pattern = self.patterns[pattern_desc]
        pattern.occurrences += 1
        pattern.last_seen = datetime.now()
        
        # Mettre à jour métriques
        if feedback.reward_signal > 0:
            pattern.positive_feedback += 1
        elif feedback.reward_signal < 0:
            pattern.negative_feedback += 1
        
        # Recalculer reward moyen
        total = pattern.positive_feedback + pattern.negative_feedback
        if total > 0:
            pattern.average_reward = (
                pattern.positive_feedback - pattern.negative_feedback
            ) / total
        
        # Ajouter exemple
        if len(pattern.examples) < 10:
            pattern.examples.append({
                "feedback_id": feedback.id,
                "prompt": feedback.prompt[:200],
                "response": feedback.response[:200],
                "reward": feedback.reward_signal,
                "comment": feedback.comment
            })
    
    def _classify_pattern(self, pattern_desc: str) -> str:
        """Classifie un pattern"""
        if "error" in pattern_desc or "faux" in pattern_desc:
            return "error"
        elif "success" in pattern_desc or "good" in pattern_desc:
            return "success"
        elif "short" in pattern_desc or "long" in pattern_desc:
            return "format"
        elif "style" in pattern_desc or "tone" in pattern_desc:
            return "style"
        else:
            return "content"
    
    def _generate_correction_rule(self, feedback: Feedback) -> None:
        """Génère une règle de correction basée sur le feedback"""
        
        if not feedback.correction:
            return
        
        rule = {
            "id": f"rule_{len(self.correction_rules)}",
            "created": datetime.now().isoformat(),
            "trigger_pattern": feedback.patterns_extracted,
            "original_context": {
                "prompt_keywords": self._extract_keywords(feedback.prompt),
                "response_length": len(feedback.response)
            },
            "correction": {
                "type": "replacement" if feedback.correction else "addition",
                "content": feedback.correction,
                "reason": feedback.comment
            },
            "confidence": 0.5,  # Basse confiance au début
            "applications": 0,
            "success_rate": 0.0
        }
        
        self.correction_rules.append(rule)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrait des mots-clés d'un texte"""
        # Simple extraction (peut être améliorée)
        words = text.lower().split()
        # Filtrer mots communs
        common_words = {"le", "la", "les", "un", "une", "des", "et", "ou", "de", "du", "pour"}
        keywords = [w for w in words if len(w) > 3 and w not in common_words]
        return list(set(keywords))[:10]
    
    def _identify_actions(self, feedback: Feedback) -> List[str]:
        """Identifie les actions à prendre suite au feedback"""
        actions = []
        
        # Action sur les patterns problématiques
        for pattern_desc in feedback.patterns_extracted:
            if pattern_desc in self.patterns:
                pattern = self.patterns[pattern_desc]
                
                # Si pattern fréquent et négatif, action corrective
                if pattern.occurrences >= 3 and pattern.average_reward < -0.3:
                    actions.append(f"avoid_pattern:{pattern_desc}")
        
        # Action sur correction
        if feedback.correction and feedback.feedback_type == FeedbackType.CORRECTION:
            actions.append("apply_correction_rule")
        
        # Action sur erreur de sécurité
        if feedback.feedback_type == FeedbackType.SAFETY:
            actions.append("flag_safety_issue")
        
        return actions
    
    def _integrate_feedback(self, feedback: Feedback) -> None:
        """Intègre le feedback avec les autres systèmes"""
        
        # Intégration avec MemoryManager
        if self.memory_manager:
            from .memory_manager import MemoryType
            
            # Stocker feedback important en mémoire
            if abs(feedback.reward_signal) > 0.5:
                self.memory_manager.add_memory(
                    content=f"Feedback: {feedback.comment or feedback.feedback_type.value}",
                    memory_type=MemoryType.FEEDBACK,
                    importance=abs(feedback.reward_signal),
                    tags=feedback.patterns_extracted,
                    metadata={
                        "feedback_id": feedback.id,
                        "interaction_id": feedback.interaction_id,
                        "reward": feedback.reward_signal
                    }
                )
        
        # Intégration avec PreferenceManager
        if self.preference_manager:
            # Observer l'interaction avec le feedback
            self.preference_manager.observe_interaction(
                {
                    "response_length": len(feedback.response),
                    "patterns": feedback.patterns_extracted
                },
                explicit_feedback={
                    "rating": feedback.reward_signal,
                    "comment": feedback.comment
                }
            )
    
    def get_correction_suggestions(
        self,
        prompt: str,
        response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggère des corrections basées sur l'historique de feedback
        """
        suggestions = []
        
        # Extraire contexte
        response_length = len(response)
        keywords = self._extract_keywords(prompt)
        
        # Vérifier les règles de correction applicables
        for rule in self.correction_rules:
            # Vérifier si le contexte correspond
            match_score = 0.0
            
            # Correspondance de longueur
            if "response_length" in rule["original_context"]:
                orig_length = rule["original_context"]["response_length"]
                length_diff = abs(response_length - orig_length) / max(response_length, orig_length)
                if length_diff < 0.3:  # Moins de 30% de différence
                    match_score += 0.3
            
            # Correspondance de mots-clés
            if "prompt_keywords" in rule["original_context"]:
                orig_keywords = set(rule["original_context"]["prompt_keywords"])
                current_keywords = set(keywords)
                overlap = len(orig_keywords & current_keywords)
                if overlap > 0:
                    match_score += 0.4 * (overlap / len(orig_keywords))
            
            # Si bonne correspondance, suggérer
            if match_score > 0.5:
                suggestions.append({
                    "rule_id": rule["id"],
                    "confidence": rule["confidence"] * match_score,
                    "correction_type": rule["correction"]["type"],
                    "suggestion": rule["correction"]["content"],
                    "reason": rule["correction"]["reason"]
                })
        
        # Trier par confiance
        suggestions.sort(key=lambda s: s["confidence"], reverse=True)
        
        return suggestions[:5]  # Top 5
    
    def get_problematic_patterns(self, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """Retourne les patterns problématiques à éviter"""
        problematic = []
        
        for pattern_id, pattern in self.patterns.items():
            if (pattern.occurrences >= min_occurrences and 
                pattern.average_reward < -0.3):
                
                problematic.append({
                    "pattern": pattern_id,
                    "type": pattern.pattern_type,
                    "occurrences": pattern.occurrences,
                    "success_rate": pattern.success_rate,
                    "average_reward": pattern.average_reward,
                    "description": pattern.description
                })
        
        problematic.sort(key=lambda p: p["average_reward"])
        return problematic
    
    def get_successful_patterns(self, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """Retourne les patterns ayant du succès à reproduire"""
        successful = []
        
        for pattern_id, pattern in self.patterns.items():
            if (pattern.occurrences >= min_occurrences and 
                pattern.average_reward > 0.3):
                
                successful.append({
                    "pattern": pattern_id,
                    "type": pattern.pattern_type,
                    "occurrences": pattern.occurrences,
                    "success_rate": pattern.success_rate,
                    "average_reward": pattern.average_reward,
                    "description": pattern.description
                })
        
        successful.sort(key=lambda p: p["average_reward"], reverse=True)
        return successful
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du système"""
        
        return {
            **self.stats,
            "correction_rules_count": len(self.correction_rules),
            "patterns_tracked": len(self.patterns),
            "recent_feedbacks": len([
                f for f in self.feedbacks.values()
                if f.timestamp > datetime.now() - timedelta(days=7)
            ]),
            "problematic_patterns": len(self.get_problematic_patterns()),
            "successful_patterns": len(self.get_successful_patterns())
        }
    
    def _save_state(self) -> None:
        """Sauvegarde l'état du système"""
        
        # Sauvegarder feedbacks
        feedbacks_file = self.storage_path / "feedbacks.json"
        feedbacks_data = {
            fb_id: {
                "timestamp": fb.timestamp.isoformat(),
                "feedback_type": fb.feedback_type.value,
                "reward_signal": fb.reward_signal,
                "interaction_id": fb.interaction_id,
                "prompt": fb.prompt,
                "response": fb.response,
                "context": fb.context,
                "comment": fb.comment,
                "correction": fb.correction,
                "tags": fb.tags,
                "processed": fb.processed,
                "patterns_extracted": fb.patterns_extracted,
                "action_taken": fb.action_taken
            }
            for fb_id, fb in self.feedbacks.items()
        }
        
        with open(feedbacks_file, 'w', encoding='utf-8') as f:
            json.dump(feedbacks_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder patterns
        patterns_file = self.storage_path / "patterns.json"
        patterns_data = {
            pat_id: {
                "pattern_type": pat.pattern_type,
                "description": pat.description,
                "occurrences": pat.occurrences,
                "positive_feedback": pat.positive_feedback,
                "negative_feedback": pat.negative_feedback,
                "average_reward": pat.average_reward,
                "examples": pat.examples,
                "last_seen": pat.last_seen.isoformat()
            }
            for pat_id, pat in self.patterns.items()
        }
        
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder règles de correction
        rules_file = self.storage_path / "correction_rules.json"
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(self.correction_rules, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder stats
        stats_file = self.storage_path / "stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def _load_state(self) -> None:
        """Charge l'état du système"""
        
        try:
            # Charger feedbacks
            feedbacks_file = self.storage_path / "feedbacks.json"
            if feedbacks_file.exists():
                with open(feedbacks_file, 'r', encoding='utf-8') as f:
                    feedbacks_data = json.load(f)
                
                for fb_id, fb_data in feedbacks_data.items():
                    fb = Feedback(
                        id=fb_id,
                        timestamp=datetime.fromisoformat(fb_data["timestamp"]),
                        feedback_type=FeedbackType(fb_data["feedback_type"]),
                        reward_signal=fb_data["reward_signal"],
                        interaction_id=fb_data["interaction_id"],
                        prompt=fb_data["prompt"],
                        response=fb_data["response"],
                        context=fb_data.get("context", {}),
                        comment=fb_data.get("comment"),
                        correction=fb_data.get("correction"),
                        tags=fb_data.get("tags", []),
                        processed=fb_data.get("processed", False),
                        patterns_extracted=fb_data.get("patterns_extracted", []),
                        action_taken=fb_data.get("action_taken")
                    )
                    self.feedbacks[fb_id] = fb
            
            # Charger patterns
            patterns_file = self.storage_path / "patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                
                for pat_id, pat_data in patterns_data.items():
                    pat = ResponsePattern(
                        pattern_id=pat_id,
                        pattern_type=pat_data["pattern_type"],
                        description=pat_data["description"],
                        occurrences=pat_data["occurrences"],
                        positive_feedback=pat_data["positive_feedback"],
                        negative_feedback=pat_data["negative_feedback"],
                        average_reward=pat_data["average_reward"],
                        examples=pat_data.get("examples", []),
                        last_seen=datetime.fromisoformat(pat_data["last_seen"])
                    )
                    self.patterns[pat_id] = pat
            
            # Charger règles
            rules_file = self.storage_path / "correction_rules.json"
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    self.correction_rules = json.load(f)
            
            # Charger stats
            stats_file = self.storage_path / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.stats.update(json.load(f))
        
        except Exception as e:
            print(f"Erreur lors du chargement de l'état: {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    system = FeedbackSystem()
    
    # Soumettre feedback positif
    system.submit_feedback(
        interaction_id="int_001",
        prompt="Explique Python",
        response="Python est un langage...",
        feedback_type=FeedbackType.POSITIVE,
        comment="Excellente explication"
    )
    
    # Soumettre feedback avec correction
    system.submit_feedback(
        interaction_id="int_002",
        prompt="Comment installer pip?",
        response="Utilise apt-get",
        feedback_type=FeedbackType.CORRECTION,
        correction="Utilise python -m ensurepip ou télécharge get-pip.py",
        comment="pip n'est pas dans apt-get par défaut"
    )
    
    # Statistiques
    stats = system.get_statistics()
    print(f"\nStatistiques:")
    print(json.dumps(stats, indent=2))
    
    # Patterns problématiques
    problems = system.get_problematic_patterns()
    print(f"\nPatterns problématiques: {len(problems)}")
