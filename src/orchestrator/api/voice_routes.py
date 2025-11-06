"""
Routes vocales pour l'orchestrateur HOPPER Phase 2
Intégration STT/TTS pour workflows audio
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import httpx
import logging
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/v1", tags=["voice"])
logger = logging.getLogger(__name__)

# Configuration services
STT_SERVICE_URL = "http://stt:5003"
TTS_SERVICE_URL = "http://tts:5004"
LLM_SERVICE_URL = "http://llm:5001"

class SynthesizeRequest(BaseModel):
    """Requête de synthèse vocale"""
    text: str
    language: str = "fr"
    voice: Optional[str] = None


class VoiceCommandResponse(BaseModel):
    """Réponse workflow vocal complet"""
    transcription: str
    response: str
    audio_url: Optional[str] = None
    language: str = "fr"
    duration_ms: int = 0


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Transcription audio → texte via service STT
    
    Args:
        audio: Fichier audio (WAV, MP3, etc.)
    
    Returns:
        {
            "text": str,           # Texte transcrit
            "language": str,       # Langue détectée
            "confidence": float    # Score confiance
        }
    """
    try:
        logger.info(f"Transcription audio: {audio.filename}")
        
        # Lecture fichier audio
        audio_data = await audio.read()
        
        # Appel service STT
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"audio": (audio.filename, audio_data, audio.content_type)}
            response = await client.post(f"{STT_SERVICE_URL}/transcribe", files=files)
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"Transcription réussie: {result['text'][:100]}...")
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"Erreur STT service: {e}")
        raise HTTPException(500, f"Service STT indisponible: {e}")
    except Exception as e:
        logger.error(f"Erreur transcription: {e}")
        raise HTTPException(500, f"Erreur transcription: {e}")


@router.post("/synthesize")
async def synthesize_text(request: SynthesizeRequest) -> Dict[str, Any]:
    """
    Synthèse texte → audio via service TTS
    
    Args:
        request: {text, language, voice}
    
    Returns:
        {
            "audio_file": str,     # Chemin fichier audio généré
            "audio_base64": str,   # Audio encodé base64
            "duration_ms": int,    # Durée audio millisecondes
            "format": str          # Format audio (wav, mp3)
        }
    """
    try:
        logger.info(f"Synthèse vocale: {request.text[:100]}...")
        
        # Appel service TTS - construire le payload correct
        payload = {
            "text": request.text,
            "language": request.language or "fr"
        }
        if request.voice:
            payload["voice"] = request.voice
        
        # Appel service TTS
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TTS_SERVICE_URL}/synthesize",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"Synthèse réussie: {result.get('audio_file', 'inline')}")
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"Erreur TTS service: {e}")
        raise HTTPException(500, f"Service TTS indisponible: {e}")
    except Exception as e:
        logger.error(f"Erreur synthèse: {e}")
        raise HTTPException(500, f"Erreur synthèse: {e}")


@router.post("/voice/command", response_model=VoiceCommandResponse)
async def voice_command(audio: UploadFile = File(...)) -> VoiceCommandResponse:
    """
    Workflow vocal complet: Audio → STT → Orchestrator → LLM → TTS → Audio
    
    Args:
        audio: Fichier audio commande vocale
    
    Returns:
        VoiceCommandResponse avec transcription, réponse texte et audio
    """
    import time
    start_time = time.time()
    
    try:
        logger.info("=== Workflow Vocal Complet ===")
        
        # 1. Transcription audio → texte
        logger.info("Étape 1: Transcription STT")
        transcription_result = await transcribe_audio(audio)
        transcription_text = transcription_result["text"]
        language = transcription_result.get("language", "fr")
        
        logger.info(f"Transcription: {transcription_text}")
        
        # 2. Traitement commande via orchestrator
        logger.info("Étape 2: Traitement commande")
        async with httpx.AsyncClient(timeout=30.0) as client:
            command_response = await client.post(
                "http://localhost:5050/api/v1/command",
                json={"command": transcription_text}
            )
            command_response.raise_for_status()
            command_result = command_response.json()
        
        response_text = command_result.get("response", "")
        logger.info(f"Réponse: {response_text[:100]}...")
        
        # 3. Synthèse vocale réponse
        logger.info("Étape 3: Synthèse TTS")
        synthesis_result = await synthesize_text(
            SynthesizeRequest(text=response_text, language=language)
        )
        # Le TTS retourne "audio_file" pas "audio_url"
        audio_url = synthesis_result.get("audio_file") or synthesis_result.get("audio_url")
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Workflow complet: {duration_ms}ms")
        
        return VoiceCommandResponse(
            transcription=transcription_text,
            response=response_text,
            audio_url=audio_url,
            language=language,
            duration_ms=duration_ms
        )
        
    except Exception as e:
        logger.error(f"Erreur workflow vocal: {e}")
        raise HTTPException(500, f"Erreur workflow vocal: {e}")


@router.get("/voice/status")
async def voice_services_status() -> Dict[str, Any]:
    """
    Status services vocaux (STT + TTS)
    
    Returns:
        {
            "stt": {"status": "healthy/unhealthy", ...},
            "tts": {"status": "healthy/unhealthy", ...}
        }
    """
    status = {}
    
    # Check STT
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{STT_SERVICE_URL}/health")
            status["stt"] = response.json() if response.status_code == 200 else {"status": "unhealthy"}
    except Exception as e:
        status["stt"] = {"status": "unhealthy", "error": str(e)}
    
    # Check TTS
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{TTS_SERVICE_URL}/health")
            status["tts"] = response.json() if response.status_code == 200 else {"status": "unhealthy"}
    except Exception as e:
        status["tts"] = {"status": "unhealthy", "error": str(e)}
    
    return status
