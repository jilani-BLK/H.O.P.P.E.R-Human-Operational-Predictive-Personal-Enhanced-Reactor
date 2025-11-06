"""
Phase 3 API Routes - Voice & Email
Routes pour les fonctionnalités vocales et email
"""

import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any

from voice_handler import voice_handler
from notification_manager import notification_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["phase3"])


# ============================================
# Models
# ============================================

class VoiceCommandRequest(BaseModel):
    user_id: Optional[str] = "default"
    verify_speaker: bool = False
    language: str = "fr"


class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "fr_FR-siwis-medium"


class EmailSummaryRequest(BaseModel):
    limit: int = 10
    only_important: bool = True


# ============================================
# Voice Routes
# ============================================

@router.post("/api/v1/voice/command")
async def voice_command(audio: UploadFile = File(...)):
    """
    Commande vocale complète : Audio → STT → LLM/System → TTS → Audio
    
    ✅ INTÉGRATION PHASE 3 + PHASE 5
    Pipeline complet:
    1. Transcription audio (Whisper STT)
    2. Détection commande système (SystemCommandsHandler Phase 5)
    3. Exécution via dispatcher (LLM ou LocalSystem)
    4. Synthèse réponse (Piper TTS)
    
    Upload: fichier audio .wav
    Retourne: réponse audio + texte
    """
    audio_bytes = await audio.read()
    result = await voice_handler.process_voice_command(audio_bytes)
    
    if result.get("success"):
        # Retourner l'audio de la réponse
        return {
            "command": result.get("command_text"),
            "response": result.get("response_text"),
            "duration_ms": result.get("duration", 0)
        }
    else:
        raise HTTPException(status_code=400, detail=result.get("error"))


@router.post("/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("fr")
):
    """
    Transcrire un audio en texte
    """
    try:
        audio_bytes = await audio.read()
        
        result = await voice_handler.transcribe_audio(audio_bytes, language)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Transcription failed")
        
        return {
            "success": True,
            "text": result.get("text"),
            "language": result.get("language"),
            "duration": result.get("duration")
        }
        
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/speak")
async def text_to_speech(request: TextToSpeechRequest):
    """
    Synthétiser du texte en audio
    """
    try:
        audio_bytes = await voice_handler.synthesize_speech(
            request.text,
            request.voice
        )
        
        if audio_bytes is None:
            raise HTTPException(status_code=500, detail="Synthesis failed")
        
        from fastapi.responses import Response
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/detect-keyword")
async def detect_activation_keyword(
    audio: UploadFile = File(...),
    keyword: str = Form("hopper")
):
    """
    Détecter le mot-clé d'activation
    """
    try:
        audio_bytes = await audio.read()
        
        result = await voice_handler.detect_activation_keyword(audio_bytes)
        
        return {
            "detected": result.get("detected", False),
            "transcribed": result.get("transcribed_text", ""),
            "keyword": keyword
        }
        
    except Exception as e:
        logger.error(f"❌ Keyword detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/listen")
async def listen_and_respond(
    audio: UploadFile = File(...),
    user_id: str = Form("default")
):
    """
    Mode écoute complet: détecte activation → transcrit → répond
    """
    try:
        audio_bytes = await audio.read()
        
        result = await voice_handler.listen_and_respond(audio_bytes, user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Listen and respond error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Email Routes (DISABLED)
# ============================================

# Email features temporarily disabled
# Uncomment when email service is ready

# @router.get("/emails/summary")
# async def get_email_summary(limit: int = 10, only_important: bool = True):
#     """
#     Obtenir un résumé vocal des emails
#     """
#     try:
#         # Vérifier emails via notification manager
#         notifications = await notification_manager.check_email_notifications()
#         
#         if only_important:
#             notifications = [n for n in notifications if n.priority >= 7]
#         
#         notifications = notifications[:limit]
#         
#         if not notifications:
#             message = "Vous n'avez pas de nouveaux emails importants."
#         else:
#             count = len(notifications)
#             message = f"Vous avez {count} nouveau{'x' if count > 1 else ''} email{'s' if count > 1 else ''} important{'s' if count > 1 else ''}: "
#             
#             for notif in notifications:
#                 message += f"{notif.title}. "
#         
#         # Synthétiser
#         audio_bytes = await voice_handler.synthesize_speech(message)
#         
#         return {
#             "count": len(notifications),
#             "message": message,
#             "emails": [n.to_dict() for n in notifications],
#             "has_audio": audio_bytes is not None
#         }
#         
#     except Exception as e:
#         logger.error(f"❌ Email summary error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/emails/read/{email_id}")
# async def read_email_aloud(email_id: str):
#     """
#     Lire un email spécifique à voix haute
#     """
#     try:
#         # TODO: Récupérer email complet depuis service email
#         # Pour l'instant, réponse simulée
#         
#         message = f"Email numéro {email_id}. Fonctionnalité en développement."
#         
#         audio_bytes = await voice_handler.synthesize_speech(message)
#         
#         return {
#             "email_id": email_id,
#             "message": message,
#             "has_audio": audio_bytes is not None
#         }
#         
#     except Exception as e:
#         logger.error(f"❌ Read email error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Notification Routes
# ============================================

@router.get("/notifications")
async def get_notifications(limit: int = 20):
    """
    Obtenir la liste des notifications
    """
    try:
        # Récupérer depuis notification manager
        stats = notification_manager.get_stats()
        
        # Récupérer dernières notifications
        recent = list(notification_manager.notification_queue)[-limit:]
        
        return {
            "total": len(notification_manager.notification_queue),
            "pending": len(notification_manager.pending_notifications),
            "notifications": [n.to_dict() for n in recent if hasattr(n, 'to_dict')],
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Get notifications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/start-polling")
async def start_notification_polling():
    """
    Démarrer le polling des notifications
    """
    try:
        if notification_manager.running:
            return {"message": "Polling already running"}
        
        # Lancer en tâche de fond
        import asyncio
        asyncio.create_task(notification_manager.run_polling_loop())
        
        return {
            "message": "Notification polling started",
            "interval": "60s"
        }
        
    except Exception as e:
        logger.error(f"❌ Start polling error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/stop-polling")
async def stop_notification_polling():
    """
    Arrêter le polling des notifications
    """
    try:
        notification_manager.stop()
        
        return {"message": "Notification polling stopped"}
        
    except Exception as e:
        logger.error(f"❌ Stop polling error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Health & Stats
# ============================================

@router.get("/voice/health")
async def voice_health_check():
    """Health check des services vocaux"""
    import requests
    
    health = {
        "stt": "unknown",
        "tts": "unknown",
        "voice_auth": "unknown"
    }
    
    # Check STT
    try:
        resp = requests.get(f"{voice_handler.stt_url}/health", timeout=2)
        health["stt"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except:
        health["stt"] = "unreachable"
    
    # Check TTS
    try:
        resp = requests.get(f"{voice_handler.tts_url}/health", timeout=2)
        health["tts"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except:
        health["tts"] = "unreachable"
    
    # Check Voice Auth
    try:
        resp = requests.get(f"{voice_handler.voice_auth_url}/health", timeout=2)
        health["voice_auth"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except:
        health["voice_auth"] = "unreachable"
    
    all_healthy = all(s == "healthy" for s in health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": health
    }


@router.get("/phase3/stats")
async def get_phase3_stats():
    """Statistiques Phase 3"""
    return {
        "voice_handler": {
            "current_user": voice_handler.current_user,
            "activation_keyword": voice_handler.activation_keyword
        },
        "notifications": notification_manager.get_stats()
    }
