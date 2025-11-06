"""
Whisper STT Server - Version Simple avec openai-whisper
"""

import os
import tempfile
import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import whisper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HOPPER Whisper STT", version="3.0.0")

# Charger modèle au démarrage
MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
logger.info(f"🎤 Loading Whisper model: {MODEL_NAME}")

try:
    model = whisper.load_model(MODEL_NAME)
    logger.info(f"✅ Whisper model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load Whisper model: {e}")
    model = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if model is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Model not loaded"}
        )
    
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": "cpu"
    }


@app.get("/stats")
async def get_stats():
    """Get model statistics"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model": MODEL_NAME,
        "device": "cpu",
        "status": "ready"
    }


@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: str = Form("fr")
):
    """
    Transcribe audio to text
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Sauvegarder audio temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_path = temp_audio.name
        
        logger.info(f"🎤 Transcribing audio ({len(content)} bytes)")
        
        # Transcrire avec Whisper
        result = model.transcribe(
            temp_path,
            language=language,
            task="transcribe",
            fp16=False  # CPU mode
        )
        
        # Cleanup
        os.unlink(temp_path)
        
        transcribed_text = result["text"].strip()
        logger.info(f"✅ Transcription: {transcribed_text[:100]}...")
        
        return {
            "text": transcribed_text,
            "language": result.get("language", language),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        
        # Cleanup on error
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect-keyword")
async def detect_keyword(
    audio: UploadFile = File(...),
    keyword: str = Form("hopper")
):
    """
    Detect activation keyword in audio
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Sauvegarder audio temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_path = temp_audio.name
        
        logger.info(f"🔍 Detecting keyword '{keyword}'")
        
        # Transcrire
        result = model.transcribe(
            temp_path,
            language="fr",
            task="transcribe",
            fp16=False
        )
        
        # Cleanup
        os.unlink(temp_path)
        
        transcribed_text = result["text"].strip().lower()
        keyword_lower = keyword.lower()
        
        detected = keyword_lower in transcribed_text
        
        logger.info(f"{'✅' if detected else '❌'} Keyword detection: {detected}")
        logger.info(f"   Transcribed: {transcribed_text}")
        
        return {
            "detected": detected,
            "transcribed_text": transcribed_text,
            "keyword": keyword,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ Keyword detection error: {e}")
        
        # Cleanup on error
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "HOPPER Whisper STT",
        "version": "3.0.0",
        "model": MODEL_NAME,
        "endpoints": {
            "health": "/health",
            "stats": "/stats",
            "transcribe": "/transcribe (POST)",
            "detect_keyword": "/detect-keyword (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("STT_SERVICE_PORT", 5003))
    uvicorn.run(app, host="0.0.0.0", port=port)
