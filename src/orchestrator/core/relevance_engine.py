"""
Relevance Engine - Filtrage Intelligent d'Événements

Détermine quels événements méritent d'être annoncés à l'utilisateur
via scoring multi-critères (règles + LLM + préférences).
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger

from .models import PerceptionEvent, RiskLevel


class RelevanceScore(str, Enum):
    """Scores de pertinence d'un événement"""
    CRITICAL = "critical"      # Annonce immédiate obligatoire
    HIGH = "high"              # Annonce immédiate recommandée
    MEDIUM = "medium"          # Annonce différée/groupée
    LOW = "low"                # Log uniquement, pas d'annonce
    NOISE = "noise"            # Ignoré complètement


@dataclass
class ScoredEvent:
    """Événement avec score de pertinence"""
    event: PerceptionEvent
    relevance_score: RelevanceScore
    score_value: float  # 0.0-1.0
    reasoning: str
    should_announce: bool
    priority: int  # 1-10 (10 = urgent)
    scored_at: str
    

class RelevanceEngine:
    """
    Moteur de pertinence pour filtrage intelligent d'événements
    
    Pipeline:
    1. Règles heuristiques (rapide, 90% des cas)
    2. Scoring LLM (pour cas ambigus)
    3. Préférences utilisateur (overrides)
    4. Gestion de déduplication/rate limiting
    """
    
    def __init__(
        self,
        llm_service_url: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        rate_limit_window: int = 300  # 5 minutes
    ):
        self.llm_service_url = llm_service_url
        self.user_preferences = user_preferences or {}
        self.rate_limit_window = rate_limit_window
        
        # Cache pour rate limiting
        self._recent_announcements: List[Dict[str, Any]] = []
        
        # Seuils par défaut
        self.thresholds = {
            "email_important_score": 0.7,
            "security_threat_level": "MEDIUM",
            "system_cpu_percent": 90,
            "max_announcements_per_hour": 10,
            "deduplicate_window_seconds": 60
        }
        
        logger.info("✅ RelevanceEngine initialisé")
    
    
    async def score_event(self, event: PerceptionEvent) -> ScoredEvent:
        """
        Score un événement pour déterminer sa pertinence
        
        Args:
            event: Événement à scorer
            
        Returns:
            ScoredEvent avec score et décision d'annonce
        """
        
        # 1. Règles heuristiques rapides
        heuristic_result = self._apply_heuristic_rules(event)
        
        if heuristic_result["confident"]:
            # Règle heuristique est sûre, pas besoin du LLM
            return ScoredEvent(
                event=event,
                relevance_score=heuristic_result["score"],
                score_value=heuristic_result["value"],
                reasoning=heuristic_result["reasoning"],
                should_announce=heuristic_result["announce"],
                priority=heuristic_result["priority"],
                scored_at=datetime.now().isoformat()
            )
        
        # 2. Cas ambigu → demander au LLM
        llm_result = await self._score_with_llm(event)
        
        if llm_result:
            return ScoredEvent(
                event=event,
                relevance_score=llm_result["score"],
                score_value=llm_result["value"],
                reasoning=llm_result["reasoning"],
                should_announce=llm_result["announce"],
                priority=llm_result["priority"],
                scored_at=datetime.now().isoformat()
            )
        
        # 3. Fallback: score neutre
        return ScoredEvent(
            event=event,
            relevance_score=RelevanceScore.LOW,
            score_value=0.3,
            reasoning="Scoring fallback - événement non reconnu",
            should_announce=False,
            priority=3,
            scored_at=datetime.now().isoformat()
        )
    
    
    def _apply_heuristic_rules(self, event: PerceptionEvent) -> Dict[str, Any]:
        """
        Applique règles heuristiques rapides
        
        Returns:
            {
                "confident": bool,  # La règle est-elle sûre?
                "score": RelevanceScore,
                "value": float,
                "reasoning": str,
                "announce": bool,
                "priority": int
            }
        """
        
        source = event.source
        event_type = event.event_type
        data = event.data
        
        # ─────────────────────────────────────────────────────────
        # 🔐 SÉCURITÉ - Toujours critique
        # ─────────────────────────────────────────────────────────
        if source == "malware_detector":
            threat_level = data.get("threat_level", "MEDIUM")
            
            if threat_level in ["HIGH", "CRITICAL"]:
                return {
                    "confident": True,
                    "score": RelevanceScore.CRITICAL,
                    "value": 1.0,
                    "reasoning": f"Menace de sécurité détectée: {threat_level}",
                    "announce": True,
                    "priority": 10
                }
            elif threat_level == "MEDIUM":
                return {
                    "confident": True,
                    "score": RelevanceScore.HIGH,
                    "value": 0.8,
                    "reasoning": "Menace potentielle détectée",
                    "announce": True,
                    "priority": 7
                }
        
        # ─────────────────────────────────────────────────────────
        # 📧 EMAIL - Basé sur importance et expéditeur
        # ─────────────────────────────────────────────────────────
        if source == "email_connector" and event_type == "new_email":
            importance = data.get("importance", "normal")
            sender = data.get("sender", "")
            is_vip = self._is_vip_sender(sender)
            
            if importance == "high" or is_vip:
                return {
                    "confident": True,
                    "score": RelevanceScore.HIGH,
                    "value": 0.85,
                    "reasoning": f"Email important de {sender}",
                    "announce": True,
                    "priority": 8
                }
            elif importance == "normal":
                # Cas ambigu → demander au LLM d'analyser le sujet
                return {
                    "confident": False,
                    "score": RelevanceScore.MEDIUM,
                    "value": 0.5,
                    "reasoning": "Email standard, analyse LLM requise",
                    "announce": False,
                    "priority": 5
                }
        
        # ─────────────────────────────────────────────────────────
        # ⚙️ SYSTÈME - Selon criticité ressources
        # ─────────────────────────────────────────────────────────
        if source == "system_executor" and event_type == "resource_alert":
            cpu_percent = data.get("cpu_percent", 0)
            memory_percent = data.get("memory_percent", 0)
            
            if cpu_percent > 95 or memory_percent > 95:
                return {
                    "confident": True,
                    "score": RelevanceScore.HIGH,
                    "value": 0.9,
                    "reasoning": f"Ressources critiques: CPU {cpu_percent}%, RAM {memory_percent}%",
                    "announce": True,
                    "priority": 9
                }
            elif cpu_percent > 80 or memory_percent > 80:
                return {
                    "confident": True,
                    "score": RelevanceScore.MEDIUM,
                    "value": 0.6,
                    "reasoning": "Ressources élevées mais gérables",
                    "announce": False,
                    "priority": 5
                }
        
        # ─────────────────────────────────────────────────────────
        # 📁 FICHIERS - Modifications importantes uniquement
        # ─────────────────────────────────────────────────────────
        if source == "filesystem_tools":
            if event_type == "file_deleted":
                path = data.get("path", "")
                
                # Documents importants
                if any(ext in path for ext in [".doc", ".pdf", ".key", ".xls"]):
                    return {
                        "confident": True,
                        "score": RelevanceScore.MEDIUM,
                        "value": 0.6,
                        "reasoning": f"Document supprimé: {path}",
                        "announce": True,
                        "priority": 6
                    }
                else:
                    return {
                        "confident": True,
                        "score": RelevanceScore.LOW,
                        "value": 0.2,
                        "reasoning": "Fichier temporaire supprimé",
                        "announce": False,
                        "priority": 2
                    }
        
        # ─────────────────────────────────────────────────────────
        # 🤷 INCONNU - Passer au LLM
        # ─────────────────────────────────────────────────────────
        return {
            "confident": False,
            "score": RelevanceScore.LOW,
            "value": 0.3,
            "reasoning": "Événement non classifié par règles heuristiques",
            "announce": False,
            "priority": 3
        }
    
    
    async def _score_with_llm(self, event: PerceptionEvent) -> Optional[Dict[str, Any]]:
        """
        Score un événement via LLM pour cas ambigus
        
        Returns:
            Dict avec score, reasoning, announce, priority ou None si échec
        """
        
        try:
            import aiohttp
            
            # Construire prompt de scoring
            prompt = self._build_scoring_prompt(event)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_service_url}/generate",
                    json={
                        "prompt": prompt,
                        "max_tokens": 150,
                        "temperature": 0.3,  # Faible pour consistance
                        "stop": ["\n\n"]
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"LLM scoring échec: {response.status}")
                        return None
                    
                    result = await response.json()
                    llm_text = result.get("text", "").strip()
                    
                    # Parser réponse LLM (format attendu: JSON)
                    return self._parse_llm_scoring(llm_text)
        
        except Exception as e:
            logger.error(f"Erreur scoring LLM: {e}")
            return None
    
    
    def _build_scoring_prompt(self, event: PerceptionEvent) -> str:
        """Construit prompt pour scoring LLM"""
        
        return f"""Tu es un assistant qui évalue la pertinence d'événements système.

Événement:
- Source: {event.source}
- Type: {event.event_type}
- Priorité: {event.priority}
- Données: {json.dumps(event.data, indent=2)}

Évalue cet événement selon ces critères:
1. Criticité: Nécessite-t-il une action immédiate?
2. Importance: Est-ce que l'utilisateur veut être informé?
3. Urgence: Peut-on attendre ou faut-il interrompre?

Réponds en JSON:
{{
  "score": "critical|high|medium|low|noise",
  "value": 0.0-1.0,
  "reasoning": "Explication courte",
  "announce": true|false,
  "priority": 1-10
}}

JSON:"""
    
    
    def _parse_llm_scoring(self, llm_text: str) -> Optional[Dict[str, Any]]:
        """Parse réponse JSON du LLM"""
        
        try:
            # Extraire JSON
            json_start = llm_text.find('{')
            json_end = llm_text.rfind('}') + 1
            
            if json_start == -1:
                return None
            
            json_str = llm_text[json_start:json_end]
            data = json.loads(json_str)
            
            # Valider structure
            score_str = data.get("score", "low")
            score = RelevanceScore(score_str) if score_str in RelevanceScore.__members__.values() else RelevanceScore.LOW
            
            return {
                "score": score,
                "value": float(data.get("value", 0.3)),
                "reasoning": data.get("reasoning", "LLM scoring"),
                "announce": bool(data.get("announce", False)),
                "priority": int(data.get("priority", 3))
            }
        
        except Exception as e:
            logger.error(f"Parse LLM scoring échec: {e}")
            return None
    
    
    def should_rate_limit(self, scored_event: ScoredEvent) -> bool:
        """
        Vérifie si l'événement doit être rate-limited
        
        Args:
            scored_event: Événement scoré
            
        Returns:
            True si doit être bloqué par rate limiting
        """
        
        now = datetime.now()
        
        # Nettoyer les anciennes annonces (> 5 minutes)
        self._recent_announcements = [
            ann for ann in self._recent_announcements
            if (now - datetime.fromisoformat(ann["timestamp"])).total_seconds() < self.rate_limit_window
        ]
        
        # Déduplication: même source/type dans dernière minute
        for ann in self._recent_announcements:
            if (
                ann["source"] == scored_event.event.source and
                ann["event_type"] == scored_event.event.event_type and
                (now - datetime.fromisoformat(ann["timestamp"])).total_seconds() < 60
            ):
                logger.debug(f"⏸️  Rate-limited (dédupliqué): {scored_event.event.source}/{scored_event.event.event_type}")
                return True
        
        # Limite d'annonces par fenêtre
        max_per_window = self.thresholds.get("max_announcements_per_hour", 10)
        if len(self._recent_announcements) >= max_per_window:
            logger.warning(f"⏸️  Rate-limited (max {max_per_window} annonces/5min)")
            return True
        
        # Enregistrer cette annonce
        self._recent_announcements.append({
            "source": scored_event.event.source,
            "event_type": scored_event.event.event_type,
            "timestamp": now.isoformat()
        })
        
        return False
    
    
    def _is_vip_sender(self, sender: str) -> bool:
        """Vérifie si l'expéditeur est VIP selon préférences utilisateur"""
        
        vip_senders = self.user_preferences.get("vip_email_senders", [])
        
        # Vérifier domaines VIP aussi
        vip_domains = self.user_preferences.get("vip_email_domains", [])
        sender_domain = sender.split("@")[-1] if "@" in sender else ""
        
        return sender in vip_senders or sender_domain in vip_domains
    
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Met à jour les préférences utilisateur"""
        self.user_preferences.update(preferences)
        logger.info(f"✅ Préférences mises à jour: {list(preferences.keys())}")
