"""
HOPPER - Module STT (Speech-to-Text)
Reconnaissance vocale via Whisper
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
from loguru import logger
import tempfile
import sys

# Import security middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from middleware.security import security_middleware, cleanup_rate_limiter_task
except ImportError:
    logger.warning("⚠️ Security middleware non disponible")
    security_middleware = None
    cleanup_rate_limiter_task = None

import asyncio

try:
    import whisper  # type: ignore[import-not-found]
except ImportError:
    logger.warning("Whisper non installé, mode simulation")
    whisper = None  # type: ignore[assignment]

# Configuration
STT_MODEL = os.getenv("STT_MODEL", "medium")
STT_LANGUAGE = os.getenv("STT_LANGUAGE", "fr")

# Modèle Whisper
stt_model = None


class TranscriptionResponse(BaseModel):
    """Réponse de transcription"""
    text: str
    language: str
    confidence: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    global stt_model
    
    # Startup
    logger.info("🚀 Démarrage du service STT")
    
    if whisper is not None:
        try:
            logger.info(f"📂 Chargement de Whisper {STT_MODEL}")
            stt_model = whisper.load_model(STT_MODEL)
            logger.success("✅ Modèle STT chargé")
        except Exception as e:
            logger.error(f"❌ Erreur: {str(e)}")
    else:
        logger.warning("⚠️ Mode simulation")
    
    # Lancer cleanup task rate limiter
    cleanup_task = None
    if cleanup_rate_limiter_task:
        cleanup_task = asyncio.create_task(cleanup_rate_limiter_task())
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt du service STT")
    if cleanup_task:
        cleanup_task.cancel()


app = FastAPI(
    title="HOPPER STT Service",
    lifespan=lifespan
)

# Appliquer middleware de sécurité
if security_middleware:
    app.middleware("http")(security_middleware)
    logger.info("✅ Security middleware activé (rate limiting + auth)")


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Vérification de santé"""
    return {
        "status": "healthy",
        "model": STT_MODEL,
        "language": STT_LANGUAGE
    }


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(audio: UploadFile = File(...)):
    """
    Transcrit un fichier audio en texte
    
    Args:
        audio: Fichier audio (WAV, MP3, etc.)
        
    Returns:
        Texte transcrit
        
    Security:
        - Validation taille fichier (max 25MB)
        - Validation type MIME
        - Timeout transcription
    """
    logger.info(f"📥 Fichier audio reçu: {audio.filename}")
    
    # Validation taille fichier (max 25MB)
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
    content = await audio.read()
    
    if len(content) > MAX_FILE_SIZE:
        logger.warning(f"🚫 Fichier trop gros: {len(content)} bytes (max {MAX_FILE_SIZE})")
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE})"
        )
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")
    
    # Validation type fichier (basique)
    allowed_types = ["audio/", "application/octet-stream"]
    content_type = audio.content_type or ""
    
    if not any(content_type.startswith(t) for t in allowed_types):
        logger.warning(f"🚫 Type MIME invalide: {content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {content_type}. Expected audio file."
        )
    
    if stt_model is None:
        return TranscriptionResponse(
            text="[SIMULATION] Transcription vocale factice",
            language="fr",
            confidence=0.95
        )
    
    tmp_path = None
    try:
        # Sauvegarde temporaire du fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcription avec timeout
        # Note: whisper.transcribe est synchrone, utiliser asyncio.to_thread pour async
        result = await asyncio.wait_for(
            asyncio.to_thread(
                stt_model.transcribe,
                tmp_path,
                language=STT_LANGUAGE
            ),
            timeout=60.0  # Timeout 60s
        )
        
        text = result["text"].strip()
        logger.success(f"✅ Transcription: {text[:100]}... ({len(text)} chars)")
        
        return TranscriptionResponse(
            text=text,
            language=result.get("language", STT_LANGUAGE),
            confidence=0.9  # Whisper ne fournit pas de score direct
        )
        
    except asyncio.TimeoutError:
        logger.error("❌ Timeout: transcription trop longue (>60s)")
        raise HTTPException(
            status_code=504,
            detail="Transcription timeout: processing took too long"
        )
    except Exception as e:
        logger.error(f"❌ Erreur transcription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Transcription failed"
        )
    finally:
        # Nettoyage fichier temporaire
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"⚠️ Impossible de supprimer {tmp_path}: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("STT_SERVICE_PORT", 5003))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
