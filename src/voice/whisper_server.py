"""
Whisper STT Server - Phase 3
Service de reconnaissance vocale avec faster-whisper
"""

import io
import logging
import wave
from typing import Optional, Dict, Any
import tempfile
import os

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
import numpy as np
import soundfile as sf

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper STT Service", version="3.0.0")

# Global model instance
model: Optional[WhisperModel] = None

# Configuration
MODEL_SIZE = "base"  # tiny, base, small, medium
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


@app.on_event("startup")
async def load_model():
    """Charger le modèle Whisper au démarrage"""
    global model
    logger.info(f"Loading Whisper model: {MODEL_SIZE}")
    
    try:
        model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            download_root="/app/models"
        )
        logger.info("✅ Whisper model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load Whisper model: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if model is not None else "unhealthy",
        "model": MODEL_SIZE,
        "device": DEVICE
    }


@app.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = "fr",
    beam_size: int = 5
):
    """
    Transcrire un fichier audio
    
    Args:
        audio: Fichier audio (WAV, MP3, etc.)
        language: Langue (fr, en, etc.)
        beam_size: Taille du beam search (5 par défaut)
    
    Returns:
        JSON avec texte transcrit et métadonnées
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Lire audio
        audio_bytes = await audio.read()
        
        # Créer fichier temporaire
        audio_file = io.BytesIO(audio_bytes)
        
        logger.info(f"Transcribing audio ({len(audio_bytes)} bytes)")
        
        # Transcription
        segments, info = model.transcribe(
            audio_file,
            language=language,
            beam_size=beam_size,
            vad_filter=True,  # Filtrer silences
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Concaténer segments
        full_text = " ".join([segment.text for segment in segments])
        
        logger.info(f"✅ Transcription: {full_text}")
        
        return {
            "success": True,
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration
        }
        
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe-stream")
async def transcribe_stream(audio: UploadFile = File(...)):
    """
    Transcription streaming (pour implémentation future)
    TODO: WebSocket pour audio streaming temps réel
    """
    return {
        "success": False,
        "message": "Streaming not yet implemented - use /transcribe for now"
    }


@app.post("/detect-keyword")
async def detect_keyword(
    audio: UploadFile = File(...),
    keyword: str = "hopper"
):
    """
    Détecter un mot-clé d'activation
    
    Args:
        audio: Fichier audio court (1-2s)
        keyword: Mot-clé à détecter
    
    Returns:
        detected: bool, confidence: float
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        audio_bytes = await audio.read()
        audio_file = io.BytesIO(audio_bytes)
        
        # Transcription rapide
        segments, _ = model.transcribe(
            audio_file,
            language="fr",
            beam_size=1,  # Plus rapide
            vad_filter=False
        )
        
        text = " ".join([segment.text.lower() for segment in segments])
        
        # Vérifier présence mot-clé
        detected = keyword.lower() in text
        
        logger.info(f"Keyword detection: '{text}' -> {detected}")
        
        return {
            "detected": detected,
            "transcribed_text": text.strip(),
            "confidence": 1.0 if detected else 0.0  # TODO: score réel
        }
        
    except Exception as e:
        logger.error(f"❌ Keyword detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Statistiques du service"""
    return {
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
        "status": "ready" if model is not None else "loading"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
