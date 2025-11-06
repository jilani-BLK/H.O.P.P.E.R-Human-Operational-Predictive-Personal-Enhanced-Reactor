"""
Piper TTS Server - Phase 3
Service de synthèse vocale avec Piper (voix naturelles)
"""

import io
import logging
import wave
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Piper TTS Service", version="3.0.0")

# Configuration
VOICE_MODEL = "/app/models/fr_FR-siwis-medium.onnx"
SAMPLE_RATE = 22050

# Global Piper instance
piper_model = None


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "fr_FR-siwis-medium"
    speed: float = 1.0


@app.on_event("startup")
async def load_model():
    """Charger le modèle Piper au démarrage"""
    global piper_model
    logger.info(f"Loading Piper model: {VOICE_MODEL}")
    
    try:
        # Import ici pour éviter erreur si piper pas installé
        from piper import PiperVoice
        
        piper_model = PiperVoice.load(VOICE_MODEL)
        logger.info("✅ Piper model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load Piper model: {e}")
        logger.warning("⚠️  TTS will use fallback mode")
        # Ne pas raise pour permettre fallback


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if piper_model is not None else "degraded",
        "voice": "fr_FR-siwis-medium",
        "sample_rate": SAMPLE_RATE
    }


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    Synthétiser du texte en audio
    
    Args:
        text: Texte à synthétiser
        voice: Voix à utiliser (pour l'instant uniquement fr_FR-siwis-medium)
        speed: Vitesse de parole (0.5 à 2.0)
    
    Returns:
        Audio WAV en streaming
    """
    if piper_model is None:
        # Fallback: Générer silence ou utiliser eSpeak
        logger.warning("Piper not loaded, using fallback")
        return _fallback_synthesis(request.text)
    
    try:
        logger.info(f"Synthesizing: {request.text[:50]}...")
        
        # Générer audio
        audio_data = []
        
        for audio_chunk in piper_model.synthesize_stream_raw(request.text):
            audio_data.extend(audio_chunk)
        
        # Créer WAV
        audio_bytes = bytes(audio_data)
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_bytes)
        
        wav_buffer.seek(0)
        
        logger.info(f"✅ Generated {len(audio_bytes)} bytes")
        
        return StreamingResponse(
            wav_buffer,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _fallback_synthesis(text: str) -> StreamingResponse:
    """
    Fallback: Générer un fichier audio vide ou utiliser eSpeak
    TODO: Intégrer eSpeak si Piper échoue
    """
    logger.warning("Using fallback synthesis (silence)")
    
    # Générer 1 seconde de silence
    duration_sec = 1.0
    num_samples = int(SAMPLE_RATE * duration_sec)
    silence = b"\x00\x00" * num_samples
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(silence)
    
    wav_buffer.seek(0)
    
    return StreamingResponse(
        wav_buffer,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "attachment; filename=fallback.wav"
        }
    )


@app.get("/voices")
async def list_voices():
    """Liste des voix disponibles"""
    return {
        "voices": [
            {
                "id": "fr_FR-siwis-medium",
                "name": "Siwis (French)",
                "language": "fr-FR",
                "quality": "medium",
                "size_mb": 86
            }
        ],
        "default": "fr_FR-siwis-medium"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
