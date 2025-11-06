#!/usr/bin/env python3
"""
Service TTS (Text-to-Speech) - Fix Phase 2
Synthèse vocale texte vers audio

Endpoints:
- GET /health - Health check
- POST /synthesize - Synthèse vocale (audio factice)
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from loguru import logger
import sys
import os
import base64
import hashlib
from pathlib import Path
import numpy as np
import soundfile as sf

# Configuration logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

app = FastAPI(title="HOPPER TTS Service", version="1.0.0")

# Configuration
TTS_CONFIG = {
    "voice": "fr-FR",
    "sample_rate": 16000,
    "simulation_mode": True,  # Phase 2 = simulation
    "output_dir": "/app/output"
}

# Créer le répertoire de sortie
os.makedirs(TTS_CONFIG["output_dir"], exist_ok=True)

logger.info(f"🔊 TTS Service démarré - Mode: {'SIMULATION' if TTS_CONFIG['simulation_mode'] else 'PRODUCTION'}")
logger.info(f"📊 Voix: {TTS_CONFIG['voice']} | Sample rate: {TTS_CONFIG['sample_rate']}")


class SynthesizeRequest(BaseModel):
    """Requête de synthèse vocale"""
    text: str = Field(..., description="Texte à synthétiser", min_length=1)
    language: str = Field(default="fr", description="Langue de synthèse")
    voice: str = Field(default="fr-FR", description="Voix à utiliser")
    format: str = Field(default="wav", description="Format audio (wav, mp3)")


class SynthesizeResponse(BaseModel):
    """Réponse de synthèse vocale"""
    success: bool
    audio_file: str
    audio_base64: str = None
    text: str
    duration_ms: int
    format: str
    simulation: bool = True


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: Status du service TTS
    """
    return {
        "status": "healthy",
        "voice": TTS_CONFIG["voice"],
        "sample_rate": TTS_CONFIG["sample_rate"],
        "simulation": TTS_CONFIG["simulation_mode"]
    }


def generate_audio_tone(text: str, duration_sec: float = None) -> tuple[str, int]:
    """
    Génère un fichier audio avec un ton simple
    Phase 2: Simulation avec ton sinusoïdal
    
    Args:
        text: Texte source (pour générer nom fichier)
        duration_sec: Durée en secondes (None = auto basé sur texte)
        
    Returns:
        tuple: (chemin_fichier, durée_ms)
    """
    # Calculer durée basée sur le texte (environ 3 caractères/sec)
    if duration_sec is None:
        duration_sec = max(0.5, len(text) / 3.0)
        duration_sec = min(duration_sec, 10.0)  # Max 10 secondes
    
    sample_rate = TTS_CONFIG["sample_rate"]
    
    # Générer un ton simple (440 Hz = La) qui "pulse" pour simuler la parole
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec))
    
    # Fréquence porteuse (voix moyenne ~200 Hz)
    carrier_freq = 200
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    
    # Modulation d'amplitude pour simuler des syllabes (3 syllabes/sec)
    modulation_freq = 3
    modulation = 0.5 + 0.5 * np.sin(2 * np.pi * modulation_freq * t)
    
    # Signal final avec envelope
    envelope = np.exp(-2 * t / duration_sec)  # Décroissance
    audio_signal = carrier * modulation * envelope * 0.3  # Volume réduit
    
    # Générer nom de fichier unique basé sur le texte
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    filename = f"tts_{text_hash}.wav"
    filepath = os.path.join(TTS_CONFIG["output_dir"], filename)
    
    # Sauvegarder le fichier WAV
    sf.write(filepath, audio_signal, sample_rate)
    
    duration_ms = int(duration_sec * 1000)
    
    logger.debug(f"Audio généré: {filename} ({duration_ms}ms)")
    
    return filepath, duration_ms


@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_text(request: SynthesizeRequest):
    """
    Synthèse vocale texte vers audio
    
    Phase 2: Mode simulation - génère audio factice (ton)
    Phase 3+: Intégration Coqui TTS ou ElevenLabs
    
    Args:
        request: Requête avec texte et paramètres
        
    Returns:
        SynthesizeResponse: Chemin fichier audio et métadonnées
    """
    try:
        logger.info(f"📥 Synthèse demandée: {request.text[:50]}... (len={len(request.text)})")
        
        # Mode simulation Phase 2
        if TTS_CONFIG["simulation_mode"]:
            # Générer audio factice
            filepath, duration_ms = generate_audio_tone(request.text)
            
            # Lire le fichier pour base64 (optionnel)
            with open(filepath, "rb") as f:
                audio_bytes = f.read()
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            result = SynthesizeResponse(
                success=True,
                audio_file=f"/output/{os.path.basename(filepath)}",
                audio_base64=audio_base64[:100] + "...",  # Tronqué pour réponse
                text=request.text,
                duration_ms=duration_ms,
                format=request.format,
                simulation=True
            )
            
            logger.info(f"✅ Audio généré: {os.path.basename(filepath)} ({duration_ms}ms)")
            return result
        
        else:
            # TODO Phase 3+: Implémentation TTS réel (Coqui, ElevenLabs)
            raise HTTPException(
                status_code=501,
                detail="Synthèse vocale réelle non implémentée (Phase 3+)"
            )
    
    except Exception as e:
        logger.error(f"❌ Erreur synthèse: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la synthèse: {str(e)}"
        )


@app.get("/output/{filename}")
async def get_audio_file(filename: str):
    """
    Récupération d'un fichier audio généré
    
    Args:
        filename: Nom du fichier audio
        
    Returns:
        FileResponse: Fichier audio WAV
    """
    filepath = os.path.join(TTS_CONFIG["output_dir"], filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier audio non trouvé")
    
    return FileResponse(
        filepath,
        media_type="audio/wav",
        filename=filename
    )


@app.get("/info")
async def service_info():
    """
    Informations sur le service TTS
    
    Returns:
        dict: Configuration et capabilities
    """
    return {
        "service": "HOPPER TTS (Text-to-Speech)",
        "version": "1.0.0",
        "phase": "2",
        "configuration": TTS_CONFIG,
        "supported_languages": ["fr", "en"],
        "supported_formats": ["wav"],
        "endpoints": {
            "/health": "Health check",
            "/synthesize": "Synthèse texte → audio",
            "/output/{filename}": "Téléchargement fichier audio",
            "/info": "Informations service"
        },
        "notes": "Mode simulation pour Phase 2 (ton sinusoïdal). TTS réel en Phase 3+."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
