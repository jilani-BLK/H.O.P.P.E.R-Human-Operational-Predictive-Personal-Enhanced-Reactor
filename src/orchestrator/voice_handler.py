"""
Voice Handler - Phase 3
Gestion du pipeline vocal complet : STT → Orchestrateur → LLM → TTS
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import io
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceHandler:
    """Gestionnaire des interactions vocales"""
    
    def __init__(
        self,
        stt_url: str = "http://whisper:5003",
        tts_url: str = "http://tts_piper:5004",
        voice_auth_url: str = "http://auth_voice:5007",
        orchestrator_url: str = "http://orchestrator:5050"
    ):
        self.stt_url = stt_url
        self.tts_url = tts_url
        self.voice_auth_url = voice_auth_url
        self.orchestrator_url = orchestrator_url
        
        self.activation_keyword = "hopper"
        self.current_user: Optional[str] = None
        
        logger.info("✅ VoiceHandler initialized")
    
    async def detect_activation_keyword(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Détecter le mot-clé d'activation dans l'audio
        
        Args:
            audio_bytes: Audio brut
            
        Returns:
            Dict avec detected: bool, transcribed_text: str
        """
        try:
            files = {"audio": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            data = {"keyword": self.activation_keyword}
            
            response = requests.post(
                f"{self.stt_url}/detect-keyword",
                files=files,
                data=data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("detected"):
                    logger.info(f"🎤 Keyword '{self.activation_keyword}' detected!")
                return result
            else:
                logger.error(f"Keyword detection failed: {response.status_code}")
                return {"detected": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Keyword detection error: {e}")
            return {"detected": False, "error": str(e)}
    
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Transcrire audio en texte
        
        Args:
            audio_bytes: Audio brut
            language: Langue (fr, en)
            
        Returns:
            Dict avec success: bool, text: str
        """
        try:
            files = {"audio": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            data = {"language": language}
            
            response = requests.post(
                f"{self.stt_url}/transcribe",
                files=files,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Transcribed: {result.get('text', '')}")
                return result
            else:
                logger.error(f"Transcription failed: {response.status_code}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_speaker(
        self,
        audio_bytes: bytes,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Vérifier l'identité du locuteur
        
        Args:
            audio_bytes: Audio de la voix
            user_id: ID utilisateur à vérifier
            
        Returns:
            Dict avec verified: bool, confidence: float
        """
        try:
            files = {"audio": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            data = {"user_id": user_id}
            
            response = requests.post(
                f"{self.voice_auth_url}/verify",
                files=files,
                data=data,
                timeout=3
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("verified"):
                    logger.info(f"✅ Speaker verified: {user_id}")
                    self.current_user = user_id
                else:
                    logger.warning(f"⚠️  Speaker NOT verified for {user_id}")
                return result
            else:
                logger.error(f"Speaker verification failed: {response.status_code}")
                return {"verified": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Speaker verification error: {e}")
            return {"verified": False, "error": str(e)}
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "fr_FR-siwis-medium"
    ) -> Optional[bytes]:
        """
        Synthétiser du texte en audio
        
        Args:
            text: Texte à synthétiser
            voice: Voix à utiliser
            
        Returns:
            Audio bytes (WAV) ou None si erreur
        """
        try:
            data = {
                "text": text,
                "voice": voice
            }
            
            response = requests.post(
                f"{self.tts_url}/synthesize",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Synthesized: {text[:50]}...")
                return response.content
            else:
                logger.error(f"Synthesis failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Synthesis error: {e}")
            return None
    
    async def process_voice_command(
        self,
        audio_bytes: bytes,
        user_id: Optional[str] = None,
        verify_speaker: bool = False
    ) -> Dict[str, Any]:
        """
        Pipeline complet : Audio → Texte → LLM → Audio
        
        Args:
            audio_bytes: Audio de la commande
            user_id: ID utilisateur (optionnel)
            verify_speaker: Vérifier identité
            
        Returns:
            Dict avec response_text, response_audio
        """
        logger.info("🎤 Processing voice command...")
        
        # 1. Vérification du locuteur (optionnel)
        if verify_speaker and user_id:
            verification = await self.verify_speaker(audio_bytes, user_id)
            if not verification.get("verified"):
                warning_text = "Je ne reconnais pas votre voix. Veuillez réessayer."
                warning_audio = await self.synthesize_speech(warning_text)
                return {
                    "success": False,
                    "error": "speaker_not_verified",
                    "response_text": warning_text,
                    "response_audio": warning_audio
                }
        
        # 2. Transcription audio → texte
        transcription = await self.transcribe_audio(audio_bytes)
        if not transcription.get("success"):
            error_text = "Je n'ai pas compris. Pouvez-vous répéter ?"
            error_audio = await self.synthesize_speech(error_text)
            return {
                "success": False,
                "error": "transcription_failed",
                "response_text": error_text,
                "response_audio": error_audio
            }
        
        command_text = transcription.get("text", "")
        logger.info(f"📝 Command: {command_text}")
        
        # 3. Envoyer à l'orchestrateur pour traitement (Phase 2 + Phase 5)
        try:
            orchestrator_response = requests.post(
                f"{self.orchestrator_url}/api/v1/command",
                json={"command": command_text},
                timeout=30
            )
            
            if orchestrator_response.status_code == 200:
                result = orchestrator_response.json()
                response_text = result.get("response", result.get("output", "Commande exécutée"))
                logger.info(f"✅ Orchestrator response: {response_text[:100]}")
            else:
                logger.error(f"Orchestrator error: {orchestrator_response.status_code}")
                response_text = "Désolé, une erreur s'est produite lors du traitement de votre commande."
        except Exception as e:
            logger.error(f"❌ Orchestrator call error: {e}")
            response_text = "Désolé, je ne peux pas traiter votre commande actuellement."
        
        # 4. Synthétiser la réponse
        response_audio = await self.synthesize_speech(response_text)
        
        return {
            "success": True,
            "command_text": command_text,
            "response_text": response_text,
            "response_audio": response_audio,
            "duration": transcription.get("duration", 0)
        }
    
    async def listen_and_respond(
        self,
        audio_bytes: bytes,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Mode d'écoute : Détecte activation → Transcrit → Répond
        
        Args:
            audio_bytes: Audio contenant potentiellement le mot-clé + commande
            user_id: ID utilisateur
            
        Returns:
            Dict avec résultat complet
        """
        # 1. Détecter mot-clé
        keyword_result = await self.detect_activation_keyword(audio_bytes)
        
        if not keyword_result.get("detected"):
            return {
                "activated": False,
                "message": "Keyword not detected"
            }
        
        logger.info("✅ Hopper activated!")
        
        # 2. Traiter la commande
        result = await self.process_voice_command(
            audio_bytes,
            user_id=user_id,
            verify_speaker=False  # Optionnel pour Phase 3.1
        )
        
        result["activated"] = True
        return result


# Instance globale
voice_handler = VoiceHandler()


async def main():
    """Test du voice handler"""
    print("VoiceHandler test mode")
    print("Note: Requires STT, TTS, and Voice Auth services running")
    
    # TODO: Tests avec audio réel


if __name__ == "__main__":
    asyncio.run(main())
