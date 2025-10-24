"""
HOPPER - Module TTS (Text-to-Speech)
Synthèse vocale
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
import os
import subprocess
import shlex
from loguru import logger
import tempfile
import sys
import re

# Import security middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from middleware.security import security_middleware, cleanup_rate_limiter_task
except ImportError:
    logger.warning("⚠️ Security middleware non disponible")
    security_middleware = None
    cleanup_rate_limiter_task = None

import asyncio

app = FastAPI(title="HOPPER TTS Service")

# Appliquer middleware de sécurité
if security_middleware:
    app.middleware("http")(security_middleware)
    logger.info("✅ Security middleware activé (rate limiting + auth)")

# Configuration
TTS_VOICE = os.getenv("TTS_VOICE", "fr-FR")


class SynthesizeRequest(BaseModel):
    """Requête de synthèse"""
    text: str = Field(..., min_length=1, max_length=5000, description="Texte à synthétiser (max 5000 caractères)")
    voice: str = Field(default="default", pattern="^[a-zA-Z0-9_-]+$")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Vitesse de parole (0.5-2.0)")
    
    @validator('text')
    def validate_text(cls, v):
        """Validation stricte du texte pour prévenir injection"""
        if not v or not v.strip():
            raise ValueError("Le texte ne peut pas être vide")
        
        # Interdire caractères de contrôle dangereux
        dangerous_chars = ['\x00', '\x1b', '\r\n\r\n']
        for char in dangerous_chars:
            if char in v:
                raise ValueError("Caractères de contrôle interdits détectés")
        
        # Vérifier patterns d'injection shell
        injection_patterns = [
            r'[;|&$`]',  # Shell metacharacters
            r'>\s*/',    # Redirection vers fichiers système
            r'<\s*/',    # Lecture fichiers système
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, v):
                raise ValueError("Pattern d'injection potentielle détecté")
        
        return v.strip()


@app.get("/health")
async def health():
    """Vérification de santé"""
    return {
        "status": "healthy",
        "voice": TTS_VOICE
    }


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    Synthétise du texte en audio
    
    Args:
        request: Texte à synthétiser (validé)
        
    Returns:
        Fichier audio WAV
        
    Security:
        - Input validation: longueur max, chars interdits
        - Timeout: 30s max
        - No shell injection: subprocess with shell=False
    """
    logger.info(f"📥 Synthèse demandée: {request.text[:100]}... (len={len(request.text)})")
    
    # Validation longueur (double check)
    if len(request.text) > 5000:
        raise HTTPException(
            status_code=400,
            detail="Texte trop long (max 5000 caractères)"
        )
    
    try:
        # Utilisation de la commande 'say' sur macOS (temporaire)
        # TODO: Implémenter avec Coqui TTS pour plus de contrôle
        
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".aiff")
        tmp_file.close()
        
        # SÉCURITÉ: subprocess avec shell=False + timeout
        # Le texte est déjà validé par Pydantic
        result = subprocess.run(
            ['say', '-v', 'Thomas', request.text, '-o', tmp_file.name],
            capture_output=True,
            text=True,
            timeout=30,  # Timeout 30s
            check=True,
            shell=False  # JAMAIS shell=True
        )
        
        # Vérifier que le fichier a été créé
        if not os.path.exists(tmp_file.name) or os.path.getsize(tmp_file.name) == 0:
            logger.error("❌ Fichier audio vide ou inexistant")
            raise HTTPException(status_code=500, detail="Synthesis produced empty file")
        
        logger.success(f"✅ Audio synthétisé: {os.path.getsize(tmp_file.name)} bytes")
        
        return FileResponse(
            tmp_file.name,
            media_type="audio/aiff",
            filename="speech.aiff",
            headers={
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout: synthèse trop longue (>30s)")
        raise HTTPException(
            status_code=504,
            detail="Synthesis timeout: processing took too long"
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erreur commande 'say': {e.stderr}")
        raise HTTPException(
            status_code=500,
            detail="Synthesis command failed"
        )
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TTS_SERVICE_PORT", 5004))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
