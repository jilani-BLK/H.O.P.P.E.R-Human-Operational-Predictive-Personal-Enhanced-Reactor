"""
HOPPER - Orchestrateur Phase 2
Version avec support LLM et conversations
"""

import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

# Import routes Phase 2
from api.phase2_routes import router as phase2_router
from api.voice_routes import router as voice_router

# Import routes Phase 3
from api.phase3_routes import router as phase3_router

# Import routes Phase 5
from api.phase5_routes import router as phase5_router

# Import routes Phase 4
from api.phase4_routes import router as phase4_router

# Import Phase 3 handlers
from voice_handler import voice_handler
from notification_manager import notification_manager

# Configuration logging
logger.add(
    "logs/orchestrator_phase2.log",
    rotation="100 MB",
    retention="30 days",
    level="INFO"
)

# FastAPI app
app = FastAPI(
    title="HOPPER Orchestrator - Phase 2",
    description="Orchestrateur avec LLM et conversations",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(phase2_router)
app.include_router(voice_router)  # Routes vocales STT/TTS
app.include_router(phase3_router)  # Routes Phase 3: Voice + Email + Notifications
app.include_router(phase4_router)  # Routes Phase 4: Learning & Feedback
app.include_router(phase5_router)  # Routes Phase 5: System Control via Connectors


@app.on_event("startup")
async def startup_event():
    """Événement de démarrage"""
    logger.info("=" * 70)
    logger.info("🚀 HOPPER Orchestrator - Phase 2 + Phase 3")
    logger.info("=" * 70)
    logger.info("")
    logger.info("✅ Orchestrateur démarré")
    logger.info("🎯 Dispatcher: Hybrid (System + LLM)")
    logger.info("🔗 Services Phase 2: system_executor + llm + stt + tts")
    logger.info("🔗 Services Phase 3: whisper + piper + auth_voice + email")
    logger.info("🎤 Voice Handler: Keyword detection + Full pipeline")
    logger.info("📧 Notification Manager: Email polling + LLM scoring")
    logger.info("")
    logger.info("📡 API disponible sur http://localhost:5050")
    logger.info("📖 Documentation: http://localhost:5050/docs")
    logger.info("")
    logger.info("🎯 Phase 3 endpoints:")
    logger.info("   POST /api/v1/voice/command - Process voice command")
    logger.info("   POST /api/v1/voice/speak - Text to speech")
    logger.info("   GET  /api/v1/emails/summary - Email summary")
    logger.info("   GET  /api/v1/notifications - Get notifications")
    logger.info("   GET  /api/v1/phase3/stats - Phase 3 statistics")
    logger.info("")
    logger.info("=" * 70)
    
    # Démarrer notification polling
    try:
        logger.info("🔔 Starting notification polling loop...")
        asyncio.create_task(notification_manager.run_polling_loop())
        logger.info("✅ Notification polling started")
    except Exception as e:
        logger.error(f"❌ Failed to start notification polling: {e}")
    
    # Log voice handler status
    logger.info(f"🎤 Voice Handler initialized: {voice_handler.current_user}")
    logger.info(f"🔑 Activation keyword: {voice_handler.activation_keyword}")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt"""
    logger.info("🛑 Arrêt de l'orchestrateur Phase 2")


if __name__ == "__main__":
    port = int(os.getenv("ORCHESTRATOR_PORT", 5050))
    uvicorn.run(
        "main_phase2:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
