"""
HOPPER - Pipeline Vocal
Intégration STT → LLM → TTS pour interaction vocale complète
"""

from typing import Optional, Dict, Any
from loguru import logger
import httpx
import asyncio
import time


class VoicePipeline:
    """
    Pipeline complet pour traitement vocal
    
    Flux:
    1. Audio → STT (Whisper) → Texte
    2. Texte → Dispatcher → Intent
    3. Intent → LLM → Réponse
    4. Réponse → TTS (Coqui) → Audio
    """
    
    def __init__(
        self,
        stt_url: str = "http://stt:5003",
        llm_url: str = "http://llm:5001",
        tts_url: str = "http://tts:5004",
        timeout: int = 30,
    ):
        """
        Args:
            stt_url: URL du service STT
            llm_url: URL du service LLM
            tts_url: URL du service TTS
            timeout: Timeout global (secondes)
        """
        self.stt_url = stt_url
        self.llm_url = llm_url
        self.tts_url = tts_url
        self.timeout = timeout
        
        self.client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"VoicePipeline initialisé (timeout: {timeout}s)")
    
    async def process_voice_command(
        self,
        audio_data: bytes,
        user_id: str = "default",
        voice_output: bool = True,
        audio_format: str = "wav",
    ) -> Dict[str, Any]:
        """
        Traite une commande vocale complète
        
        Args:
            audio_data: Données audio brutes (WAV)
            user_id: ID utilisateur
            voice_output: Si True, génère réponse audio
            audio_format: Format audio entrée (wav, mp3, etc.)
            
        Returns:
            Dict avec transcription, réponse texte et audio
        """
        start_time = time.time()
        
        result: Dict[str, Any] = {
            "success": False,
            "transcription": "",
            "response_text": "",
            "response_audio": None,
            "latency": {
                "stt": 0.0,
                "llm": 0.0,
                "tts": 0.0,
                "total": 0.0,
            },
            "error": None,
        }
        
        try:
            # ========================================
            # Étape 1: STT - Audio → Texte
            # ========================================
            logger.info(f"🎤 STT: Transcription audio ({len(audio_data)} bytes)")
            stt_start = time.time()
            
            try:
                transcription = await self._transcribe(audio_data, audio_format)
                result["transcription"] = transcription
                result["latency"]["stt"] = time.time() - stt_start
                
                logger.info(f"📝 Transcription: '{transcription}' ({result['latency']['stt']:.2f}s)")
                
                if not transcription.strip():
                    result["error"] = "Transcription vide"
                    return result
                
            except Exception as e:
                result["error"] = f"Erreur STT: {str(e)}"
                logger.error(result["error"])
                return result
            
            # ========================================
            # Étape 2: LLM - Texte → Réponse
            # ========================================
            logger.info(f"🧠 LLM: Génération réponse")
            llm_start = time.time()
            
            try:
                response_text = await self._generate_response(transcription, user_id)
                result["response_text"] = response_text
                result["latency"]["llm"] = time.time() - llm_start
                
                logger.info(f"💬 Réponse: '{response_text[:100]}...' ({result['latency']['llm']:.2f}s)")
                
            except Exception as e:
                result["error"] = f"Erreur LLM: {str(e)}"
                logger.error(result["error"])
                return result
            
            # ========================================
            # Étape 3: TTS - Texte → Audio (optionnel)
            # ========================================
            if voice_output and response_text:
                logger.info(f"🔊 TTS: Synthèse vocale")
                tts_start = time.time()
                
                try:
                    audio_response = await self._synthesize(response_text)
                    result["response_audio"] = audio_response
                    result["latency"]["tts"] = time.time() - tts_start
                    
                    logger.info(f"🎵 Audio généré: {len(audio_response)} bytes ({result['latency']['tts']:.2f}s)")
                    
                except Exception as e:
                    logger.warning(f"Erreur TTS (non bloquant): {e}")
                    # TTS est optionnel, on continue
            
            result["success"] = True
            result["latency"]["total"] = time.time() - start_time
            
            logger.success(f"✅ Pipeline complet: {result['latency']['total']:.2f}s")
            
        except Exception as e:
            result["error"] = f"Erreur pipeline: {str(e)}"
            logger.error(result["error"])
        
        finally:
            result["latency"]["total"] = time.time() - start_time
        
        return result
    
    async def _transcribe(self, audio_data: bytes, audio_format: str) -> str:
        """
        Transcrit audio en texte via service STT
        
        Args:
            audio_data: Données audio
            audio_format: Format (wav, mp3, etc.)
            
        Returns:
            Texte transcrit
        """
        files = {"audio": ("audio." + audio_format, audio_data, f"audio/{audio_format}")}
        
        response = await self.client.post(
            f"{self.stt_url}/transcribe",
            files=files,
            timeout=30,
        )
        
        if response.status_code != 200:
            raise Exception(f"STT error: {response.status_code} - {response.text}")
        
        data = response.json()
        return data.get("text", "")
    
    async def _generate_response(self, text: str, user_id: str) -> str:
        """
        Génère réponse via LLM
        
        Args:
            text: Texte utilisateur
            user_id: ID utilisateur
            
        Returns:
            Réponse générée
        """
        payload = {
            "prompt": text,
            "user_id": user_id,
            "max_tokens": 150,
            "temperature": 0.7,
        }
        
        response = await self.client.post(
            f"{self.llm_url}/generate",
            json=payload,
            timeout=60,
        )
        
        if response.status_code != 200:
            raise Exception(f"LLM error: {response.status_code} - {response.text}")
        
        data = response.json()
        return data.get("generated_text", "")
    
    async def _synthesize(self, text: str) -> bytes:
        """
        Synthétise texte en audio via TTS
        
        Args:
            text: Texte à synthétiser
            
        Returns:
            Données audio (WAV)
        """
        payload = {"text": text}
        
        response = await self.client.post(
            f"{self.tts_url}/synthesize",
            json=payload,
            timeout=30,
        )
        
        if response.status_code != 200:
            raise Exception(f"TTS error: {response.status_code} - {response.text}")
        
        return response.content
    
    async def close(self):
        """Ferme les connexions"""
        await self.client.aclose()
        logger.info("VoicePipeline fermé")


# Fonction helper pour usage simple
async def voice_command(
    audio_data: bytes,
    user_id: str = "default",
    voice_output: bool = True,
) -> Dict[str, Any]:
    """
    Fonction helper pour traiter une commande vocale
    
    Usage:
        result = await voice_command(audio_data)
        print(result["transcription"])
        print(result["response_text"])
    """
    pipeline = VoicePipeline()
    try:
        return await pipeline.process_voice_command(audio_data, user_id, voice_output)
    finally:
        await pipeline.close()


# Exemple d'utilisation
if __name__ == "__main__":
    import sys
    
    async def test_pipeline():
        """Test du pipeline"""
        # Simuler avec fichier audio
        if len(sys.argv) > 1:
            audio_file = sys.argv[1]
            with open(audio_file, "rb") as f:
                audio_data = f.read()
            
            logger.info(f"Test avec {audio_file}")
            result = await voice_command(audio_data)
            
            print("\n" + "="*60)
            print(f"Transcription: {result['transcription']}")
            print(f"Réponse: {result['response_text']}")
            print(f"Latence: {result['latency']['total']:.2f}s")
            print("="*60)
        else:
            logger.info("Usage: python voice_pipeline.py audio.wav")
    
    asyncio.run(test_pipeline())
