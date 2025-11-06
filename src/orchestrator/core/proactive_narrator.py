"""
Proactive Narrator - Génération de Messages Naturels pour Événements

Transforme les événements système en messages naturels via LLM,
permettant à HOPPER d'annoncer proactivement ce qui est pertinent.
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .models import PerceptionEvent
from .relevance_engine import ScoredEvent, RelevanceScore


class ProactiveNarrator:
    """
    Génère des messages naturels pour événements via LLM
    
    Pipeline:
    1. Reçoit ScoredEvent du RelevanceEngine
    2. Construit prompt contextuel (événement + historique + préférences)
    3. LLM génère message naturel + suggestions d'actions
    4. Retourne NarrationResult avec message + plan d'action
    """
    
    def __init__(
        self,
        llm_service_url: str,
        context_manager = None,
        tts_service_url: Optional[str] = None
    ):
        self.llm_service_url = llm_service_url
        self.context_manager = context_manager
        self.tts_service_url = tts_service_url
        
        # Cache des narrations pour éviter répétitions
        self._recent_narrations: list = []
        self._max_cache = 20
        
        logger.info("✅ ProactiveNarrator initialisé")
    
    
    async def narrate_event(
        self,
        scored_event: ScoredEvent,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Génère narration naturelle pour un événement scoré
        
        Args:
            scored_event: Événement avec score de pertinence
            user_id: Utilisateur cible (pour contexte)
            
        Returns:
            {
                "message": str,  # Message naturel
                "should_speak": bool,  # Dire à voix haute?
                "suggested_actions": List[Dict],  # Actions proposées
                "requires_confirmation": bool,  # Demander confirmation?
                "urgency": str  # "immediate"|"normal"|"low"
            }
        """
        
        event = scored_event.event
        
        # Construire prompt avec contexte
        prompt = await self._build_narration_prompt(scored_event, user_id)
        
        # Générer via LLM
        narration = await self._generate_with_llm(prompt)
        
        if not narration:
            # Fallback: message générique
            narration = self._generate_fallback_message(scored_event)
        
        # Stocker dans cache
        self._cache_narration(event, narration)
        
        # Synthèse vocale si nécessaire
        if narration.get("should_speak") and self.tts_service_url:
            await self._synthesize_speech(narration["message"])
        
        return narration
    
    
    async def _build_narration_prompt(
        self,
        scored_event: ScoredEvent,
        user_id: Optional[str]
    ) -> str:
        """Construit prompt contextuel pour narration"""
        
        event = scored_event.event
        
        # Récupérer contexte utilisateur
        user_context = ""
        if self.context_manager and user_id:
            context = await self.context_manager.get_context(user_id)
            
            # Historique récent
            history = context.get("conversation_history", [])
            if history:
                recent = list(history)[-3:]  # 3 derniers échanges
                user_context = "\n".join([
                    f"- User: {ex.user_message}\n  Assistant: {ex.assistant_response}"
                    for ex in recent
                ])
        
        # Templates selon type d'événement
        prompt = f"""Tu es HOPPER, un assistant personnel intelligent.

Tu dois annoncer cet événement à l'utilisateur de façon naturelle et concise.

📊 ÉVÉNEMENT:
- Source: {event.source}
- Type: {event.event_type}
- Priorité: {event.priority}/10
- Données: {json.dumps(event.data, indent=2)}

📈 ANALYSE:
- Score de pertinence: {scored_event.relevance_score.value} ({scored_event.score_value:.2f})
- Raisonnement: {scored_event.reasoning}
- Priorité: {scored_event.priority}/10

{f'📝 CONTEXTE RÉCENT:\\n{user_context}' if user_context else ''}

🎯 TA MISSION:
1. Génère un message naturel et concis (2-3 phrases max)
2. Adapte le ton à l'urgence (calme si LOW, alerte si CRITICAL)
3. Propose des actions pertinentes si nécessaire
4. Demande confirmation si action à risque

Réponds en JSON:
{{
  "message": "Ton message naturel ici...",
  "should_speak": true/false,
  "suggested_actions": [
    {{"action": "read_email", "label": "Lire le mail", "risk": "safe"}},
    {{"action": "delete_file", "label": "Supprimer", "risk": "high"}}
  ],
  "requires_confirmation": true/false,
  "urgency": "immediate|normal|low",
  "tone": "calm|alert|urgent"
}}

JSON:"""
        
        return prompt
    
    
    async def _generate_with_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Appelle le LLM pour générer la narration"""
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_service_url}/generate",
                    json={
                        "prompt": prompt,
                        "max_tokens": 300,
                        "temperature": 0.7,  # Un peu de créativité
                        "stop": ["\n\n", "###"]
                    },
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"LLM narration échec: {response.status}")
                        return None
                    
                    result = await response.json()
                    llm_text = result.get("text", "").strip()
                    
                    # Parser JSON
                    return self._parse_narration_json(llm_text)
        
        except asyncio.TimeoutError:
            logger.error("LLM narration timeout")
            return None
        except Exception as e:
            logger.error(f"Erreur génération narration: {e}")
            return None
    
    
    def _parse_narration_json(self, llm_text: str) -> Optional[Dict[str, Any]]:
        """Parse le JSON de narration du LLM"""
        
        try:
            # Extraire JSON
            json_start = llm_text.find('{')
            json_end = llm_text.rfind('}') + 1
            
            if json_start == -1:
                return None
            
            json_str = llm_text[json_start:json_end]
            data = json.loads(json_str)
            
            # Validation basique
            return {
                "message": data.get("message", "Un événement nécessite votre attention."),
                "should_speak": bool(data.get("should_speak", False)),
                "suggested_actions": data.get("suggested_actions", []),
                "requires_confirmation": bool(data.get("requires_confirmation", False)),
                "urgency": data.get("urgency", "normal"),
                "tone": data.get("tone", "calm")
            }
        
        except Exception as e:
            logger.error(f"Parse narration JSON échec: {e}")
            return None
    
    
    def _generate_fallback_message(self, scored_event: ScoredEvent) -> Dict[str, Any]:
        """Génère message fallback si LLM échoue"""
        
        event = scored_event.event
        score = scored_event.relevance_score
        
        # Messages par type d'événement
        templates = {
            "new_email": "📧 Vous avez reçu un nouveau mail.",
            "malware_detected": "⚠️ Menace de sécurité détectée.",
            "resource_alert": "⚙️ Alerte système: ressources élevées.",
            "file_deleted": "📁 Un fichier a été supprimé.",
            "default": "ℹ️ Un événement nécessite votre attention."
        }
        
        message = templates.get(event.event_type, templates["default"])
        
        # Ajuster selon score
        if score == RelevanceScore.CRITICAL:
            message = f"🚨 URGENT: {message}"
        
        return {
            "message": message,
            "should_speak": score in [RelevanceScore.CRITICAL, RelevanceScore.HIGH],
            "suggested_actions": [],
            "requires_confirmation": False,
            "urgency": "immediate" if score == RelevanceScore.CRITICAL else "normal",
            "tone": "urgent" if score == RelevanceScore.CRITICAL else "calm"
        }
    
    
    async def _synthesize_speech(self, message: str):
        """Synthétise le message en audio via TTS avec voix clonée HOPPER"""
        
        if not self.tts_service_url:
            return
        
        try:
            import aiohttp
            
            # Payload avec configuration de la voix clonée
            payload = {
                "text": message,
                "voice": "hopper",  # Utilise la voix clonée définie dans voices.yaml
                "language": "fr"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.tts_service_url}/synthesize",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)  # Augmenté pour synthèse
                ) as response:
                    if response.status == 200:
                        logger.debug("🔊 Synthèse vocale HOPPER envoyée")
                    else:
                        logger.warning(f"TTS échec: {response.status}")
        
        except Exception as e:
            logger.error(f"Erreur TTS: {e}")
    
    
    def _cache_narration(self, event: PerceptionEvent, narration: Dict[str, Any]):
        """Stocke narration dans cache pour éviter répétitions"""
        
        self._recent_narrations.append({
            "event_type": event.event_type,
            "source": event.source,
            "message": narration["message"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Limiter taille cache
        if len(self._recent_narrations) > self._max_cache:
            self._recent_narrations = self._recent_narrations[-self._max_cache:]
    
    
    def get_recent_narrations(self, limit: int = 10) -> list:
        """Récupère les narrations récentes"""
        return self._recent_narrations[-limit:]
