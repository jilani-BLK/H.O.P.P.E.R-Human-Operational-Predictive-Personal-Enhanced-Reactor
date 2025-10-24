"""
Gestionnaire de préférences utilisateur HOPPER
Apprentissage et adaptation du style, format, niveau de détail
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PreferenceCategory(Enum):
    """Catégories de préférences"""
    RESPONSE_STYLE = "response_style"
    DETAIL_LEVEL = "detail_level"
    FORMAT = "format"
    TONE = "tone"
    LANGUAGE = "language"
    DOMAIN = "domain"
    INTERACTION = "interaction"
    PRIVACY = "privacy"


class AdaptationLevel(Enum):
    """Niveau d'adaptation"""
    NONE = "none"  # Pas d'adaptation
    LOW = "low"  # Adaptation minimale
    MEDIUM = "medium"  # Adaptation modérée
    HIGH = "high"  # Adaptation forte
    FULL = "full"  # Adaptation maximale


@dataclass
class UserPreference:
    """Préférence utilisateur"""
    category: PreferenceCategory
    key: str
    value: Any
    confidence: float = 0.5  # 0-1, confiance dans cette préférence
    observations: int = 0  # Nombre d'observations
    last_updated: datetime = field(default_factory=datetime.now)
    source: str = "inferred"  # inferred, explicit, feedback
    metadata: Dict[str, Any] = field(default_factory=dict)


class PreferenceManager:
    """
    Gestionnaire de préférences utilisateur avec apprentissage continu
    Adapte le comportement selon les observations et retours
    """
    
    def __init__(self, storage_path: str = "data/preferences/user_preferences.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Préférences par catégorie
        self.preferences: Dict[PreferenceCategory, Dict[str, UserPreference]] = {
            cat: {} for cat in PreferenceCategory
        }
        
        # Historique des observations
        self.observation_history: List[Dict[str, Any]] = []
        
        # Paramètres d'apprentissage
        self.learning_rate = 0.1  # Vitesse d'adaptation
        self.confidence_threshold = 0.7  # Seuil pour considérer une préférence établie
        self.min_observations = 3  # Observations minimales avant adaptation
        
        # Statistiques
        self.stats = {
            "total_observations": 0,
            "preferences_learned": 0,
            "preferences_updated": 0,
            "adaptations_applied": 0
        }
        
        # Charger préférences existantes
        self._load_preferences()
    
    def observe_interaction(
        self,
        interaction_data: Dict[str, Any],
        explicit_feedback: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Observe une interaction pour détecter des préférences
        
        Args:
            interaction_data: Données sur l'interaction (prompt, response, context)
            explicit_feedback: Feedback explicite de l'utilisateur (optionnel)
        """
        
        self.stats["total_observations"] += 1
        
        # Enregistrer l'observation
        observation = {
            "timestamp": datetime.now().isoformat(),
            "data": interaction_data,
            "feedback": explicit_feedback
        }
        self.observation_history.append(observation)
        
        # Limiter l'historique (garder les 1000 dernières)
        if len(self.observation_history) > 1000:
            self.observation_history = self.observation_history[-1000:]
        
        # Analyser pour détecter des préférences
        self._analyze_for_preferences(interaction_data, explicit_feedback)
    
    def _analyze_for_preferences(
        self,
        interaction: Dict[str, Any],
        feedback: Optional[Dict[str, Any]]
    ) -> None:
        """Analyse une interaction pour détecter des préférences"""
        
        # Analyser le style de réponse préféré
        if "response_length" in interaction:
            length = interaction["response_length"]
            if length < 200:
                self._update_preference(
                    PreferenceCategory.DETAIL_LEVEL,
                    "preferred_length",
                    "concise",
                    confidence_delta=0.1
                )
            elif length > 500:
                self._update_preference(
                    PreferenceCategory.DETAIL_LEVEL,
                    "preferred_length",
                    "detailed",
                    confidence_delta=0.1
                )
        
        # Analyser le format préféré
        if "format_used" in interaction:
            format_type = interaction["format_used"]
            self._update_preference(
                PreferenceCategory.FORMAT,
                "preferred_format",
                format_type,
                confidence_delta=0.05
            )
        
        # Analyser le feedback explicite
        if feedback:
            self._process_explicit_feedback(feedback)
        
        # Analyser les domaines d'intérêt
        if "topic" in interaction:
            topic = interaction["topic"]
            current_interests = self.get_preference(
                PreferenceCategory.DOMAIN,
                "interests",
                []
            )
            
            if isinstance(current_interests, list) and topic not in current_interests:
                current_interests.append(topic)
                self._update_preference(
                    PreferenceCategory.DOMAIN,
                    "interests",
                    current_interests,
                    confidence_delta=0.05,
                    source="inferred"
                )
    
    def _process_explicit_feedback(self, feedback: Dict[str, Any]) -> None:
        """Traite un feedback explicite de l'utilisateur"""
        
        # Feedback sur le niveau de détail
        if "too_detailed" in feedback and feedback["too_detailed"]:
            self._update_preference(
                PreferenceCategory.DETAIL_LEVEL,
                "preferred_length",
                "concise",
                confidence_delta=0.3,
                source="feedback"
            )
        
        if "too_brief" in feedback and feedback["too_brief"]:
            self._update_preference(
                PreferenceCategory.DETAIL_LEVEL,
                "preferred_length",
                "detailed",
                confidence_delta=0.3,
                source="feedback"
            )
        
        # Feedback sur le ton
        if "preferred_tone" in feedback:
            self._update_preference(
                PreferenceCategory.TONE,
                "style",
                feedback["preferred_tone"],
                confidence_delta=0.5,
                source="feedback"
            )
        
        # Feedback sur le format
        if "preferred_format" in feedback:
            self._update_preference(
                PreferenceCategory.FORMAT,
                "preferred_format",
                feedback["preferred_format"],
                confidence_delta=0.5,
                source="feedback"
            )
    
    def _update_preference(
        self,
        category: PreferenceCategory,
        key: str,
        value: Any,
        confidence_delta: float,
        source: str = "inferred"
    ) -> None:
        """Met à jour ou crée une préférence"""
        
        pref_key = f"{category.value}:{key}"
        
        if key in self.preferences[category]:
            # Mettre à jour
            pref = self.preferences[category][key]
            
            # Si la valeur change, réduire la confiance puis augmenter
            if pref.value != value:
                pref.confidence = max(0, pref.confidence - 0.2)
                pref.value = value
            
            # Augmenter la confiance
            pref.confidence = min(1.0, pref.confidence + confidence_delta)
            pref.observations += 1
            pref.last_updated = datetime.now()
            pref.source = source
            
            self.stats["preferences_updated"] += 1
        else:
            # Créer nouvelle préférence
            pref = UserPreference(
                category=category,
                key=key,
                value=value,
                confidence=confidence_delta,
                observations=1,
                source=source
            )
            self.preferences[category][key] = pref
            self.stats["preferences_learned"] += 1
        
        # Sauvegarder
        self._save_preferences()
    
    def get_preference(
        self,
        category: PreferenceCategory,
        key: str,
        default: Any = None
    ) -> Any:
        """Récupère une préférence"""
        
        if key in self.preferences[category]:
            pref = self.preferences[category][key]
            
            # Ne retourner que si confiance suffisante
            if pref.confidence >= self.confidence_threshold:
                return pref.value
        
        return default
    
    def get_all_preferences(
        self,
        min_confidence: float = 0.0
    ) -> Dict[str, Any]:
        """Retourne toutes les préférences établies"""
        
        result = {}
        
        for category, prefs in self.preferences.items():
            category_prefs = {}
            for key, pref in prefs.items():
                if pref.confidence >= min_confidence:
                    category_prefs[key] = {
                        "value": pref.value,
                        "confidence": pref.confidence,
                        "observations": pref.observations,
                        "source": pref.source
                    }
            
            if category_prefs:
                result[category.value] = category_prefs
        
        return result
    
    def set_explicit_preference(
        self,
        category: PreferenceCategory,
        key: str,
        value: Any
    ) -> None:
        """Définit explicitement une préférence (haute confiance)"""
        
        self._update_preference(
            category,
            key,
            value,
            confidence_delta=0.9,
            source="explicit"
        )
    
    def get_adaptation_config(self) -> Dict[str, Any]:
        """
        Génère une configuration d'adaptation basée sur les préférences
        à utiliser par le système pour ajuster son comportement
        """
        
        config = {
            "detail_level": self.get_preference(
                PreferenceCategory.DETAIL_LEVEL,
                "preferred_length",
                "moderate"
            ),
            "tone": self.get_preference(
                PreferenceCategory.TONE,
                "style",
                "professional"
            ),
            "format": self.get_preference(
                PreferenceCategory.FORMAT,
                "preferred_format",
                "text"
            ),
            "domains_of_interest": self.get_preference(
                PreferenceCategory.DOMAIN,
                "interests",
                []
            ),
            "language": self.get_preference(
                PreferenceCategory.LANGUAGE,
                "primary",
                "fr"
            ),
            "adaptation_level": AdaptationLevel.MEDIUM,
            "confidence_scores": {}
        }
        
        # Ajouter les scores de confiance
        for category in PreferenceCategory:
            for key, pref in self.preferences[category].items():
                config["confidence_scores"][f"{category.value}.{key}"] = pref.confidence
        
        return config
    
    def reset_preference(self, category: PreferenceCategory, key: str) -> bool:
        """Réinitialise une préférence"""
        
        if key in self.preferences[category]:
            del self.preferences[category][key]
            self._save_preferences()
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques d'apprentissage"""
        
        # Compter préférences par catégorie
        prefs_by_category = {}
        for category, prefs in self.preferences.items():
            prefs_by_category[category.value] = len(prefs)
        
        # Préférences les plus confiantes
        all_prefs = []
        for category, prefs in self.preferences.items():
            for key, pref in prefs.items():
                all_prefs.append({
                    "category": category.value,
                    "key": key,
                    "value": pref.value,
                    "confidence": pref.confidence,
                    "observations": pref.observations
                })
        
        all_prefs.sort(key=lambda p: p["confidence"], reverse=True)
        
        return {
            **self.stats,
            "preferences_by_category": prefs_by_category,
            "total_preferences": sum(prefs_by_category.values()),
            "top_confident_preferences": all_prefs[:10],
            "learning_rate": self.learning_rate,
            "confidence_threshold": self.confidence_threshold
        }
    
    def export_preferences(self, output_file: str) -> None:
        """Exporte les préférences"""
        data = {
            "preferences": self.get_all_preferences(min_confidence=0.0),
            "stats": self.get_statistics(),
            "export_date": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_preferences(self) -> None:
        """Sauvegarde les préférences"""
        data = {
            "preferences": {},
            "stats": self.stats,
            "last_updated": datetime.now().isoformat()
        }
        
        # Convertir en dict sérialisable
        for category, prefs in self.preferences.items():
            if prefs:
                data["preferences"][category.value] = {}
                for key, pref in prefs.items():
                    data["preferences"][category.value][key] = {
                        "value": pref.value,
                        "confidence": pref.confidence,
                        "observations": pref.observations,
                        "last_updated": pref.last_updated.isoformat(),
                        "source": pref.source,
                        "metadata": pref.metadata
                    }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_preferences(self) -> None:
        """Charge les préférences"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Charger les préférences
            for category_name, prefs in data.get("preferences", {}).items():
                category = PreferenceCategory(category_name)
                
                for key, pref_data in prefs.items():
                    pref = UserPreference(
                        category=category,
                        key=key,
                        value=pref_data["value"],
                        confidence=pref_data["confidence"],
                        observations=pref_data["observations"],
                        last_updated=datetime.fromisoformat(pref_data["last_updated"]),
                        source=pref_data.get("source", "inferred"),
                        metadata=pref_data.get("metadata", {})
                    )
                    self.preferences[category][key] = pref
            
            # Charger les stats
            if "stats" in data:
                self.stats.update(data["stats"])
            
        except Exception as e:
            print(f"Erreur lors du chargement des préférences: {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    manager = PreferenceManager()
    
    # Observer des interactions
    manager.observe_interaction({
        "response_length": 600,
        "format_used": "markdown",
        "topic": "python"
    })
    
    manager.observe_interaction({
        "response_length": 550,
        "format_used": "markdown",
        "topic": "machine learning"
    }, explicit_feedback={
        "preferred_tone": "professional"
    })
    
    # Récupérer la configuration d'adaptation
    config = manager.get_adaptation_config()
    print(f"\nConfiguration d'adaptation:")
    print(json.dumps(config, indent=2, ensure_ascii=False, default=str))
    
    # Statistiques
    stats = manager.get_statistics()
    print(f"\nStatistiques:")
    print(f"  Total observations: {stats['total_observations']}")
    print(f"  Préférences apprises: {stats['preferences_learned']}")
    print(f"  Total préférences: {stats['total_preferences']}")
