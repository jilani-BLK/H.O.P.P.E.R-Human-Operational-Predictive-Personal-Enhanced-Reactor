#!/usr/bin/env python3
"""
Service STT (Speech-to-Text) - Simulation Phase 2
Transcription audio vers texte

Endpoints:
- GET /health - Health check
- POST /transcribe - Transcription audio (simulation)
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import sys

# Configuration logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

app = FastAPI(title="HOPPER STT Service", version="1.0.0")

# Configuration
STT_CONFIG = {
    "model": "whisper-medium",
    "language": "fr",
    "sample_rate": 16000,
    "simulation_mode": True  # Phase 2 = simulation
}

logger.info(f"🎤 STT Service démarré - Mode: {'SIMULATION' if STT_CONFIG['simulation_mode'] else 'PRODUCTION'}")
logger.info(f"📊 Modèle: {STT_CONFIG['model']} | Langue: {STT_CONFIG['language']}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: Status du service STT
    """
    return {
        "status": "healthy",
        "model": STT_CONFIG["model"],
        "language": STT_CONFIG["language"],
        "simulation": STT_CONFIG["simulation_mode"]
    }


@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcription audio vers texte
    
    Phase 2: Mode simulation - retourne transcription factice
    Phase 3+: Intégration Whisper réel
    
    Args:
        audio: Fichier audio (WAV, MP3, etc.)
        
    Returns:
        dict: Transcription avec métadonnées
    """
    try:
        # Lire le fichier audio
        audio_data = await audio.read()
        audio_size = len(audio_data)
        
        logger.info(f"📥 Transcription demandée: {audio.filename} ({audio_size} bytes)")
        
        # Mode simulation Phase 2
        if STT_CONFIG["simulation_mode"]:
            # Transcription factice basée sur la taille de l'audio
            if audio_size < 10000:
                transcription = "Bonjour HOPPER"
            elif audio_size < 50000:
                transcription = "Quelle est la météo aujourd'hui ?"
            elif audio_size < 100000:
                transcription = "Peux-tu m'aider à organiser mes fichiers ?"
            else:
                transcription = "Raconte-moi l'histoire de l'intelligence artificielle"
            
            result = {
                "text": transcription,
                "language": STT_CONFIG["language"],
                "confidence": 0.95,
                "duration_ms": audio_size // 32,  # Estimation durée
                "simulation": True
            }
            
            logger.info(f"✅ Transcription: '{transcription}' (simulation)")
            return result
        
        else:
            # TODO Phase 3+: Implémentation Whisper réel
            raise HTTPException(
                status_code=501,
                detail="Transcription réelle non implémentée (Phase 3+)"
            )
    
    except Exception as e:
        logger.error(f"❌ Erreur transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la transcription: {str(e)}"
        )


@app.get("/info")
async def service_info():
    """
    Informations sur le service STT
    
    Returns:
        dict: Configuration et capabilities
    """
    return {
        "service": "HOPPER STT (Speech-to-Text)",
        "version": "1.0.0",
        "phase": "2",
        "configuration": STT_CONFIG,
        "supported_formats": ["wav", "mp3", "ogg", "flac"],
        "endpoints": {
            "/health": "Health check",
            "/transcribe": "Transcription audio → texte",
            "/info": "Informations service"
        },
        "notes": "Mode simulation pour Phase 2. Whisper réel en Phase 3+."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
