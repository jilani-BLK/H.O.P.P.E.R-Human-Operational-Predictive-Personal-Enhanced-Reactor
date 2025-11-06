"""
HOPPER - Orchestrateur Central (Phase 1 Simplifié)
Version minimale pour valider l'infrastructure de base
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

# Import des routes Phase 1
from api.phase1_routes import router as phase1_router

# Configuration des logs
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Création de l'application FastAPI
app = FastAPI(
    title="HOPPER Orchestrator",
    description="Assistant Personnel Intelligent - Phase 1",
    version="1.0.0-phase1"
)

# CORS pour tests locaux
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes Phase 1
app.include_router(phase1_router, prefix="/api/v1", tags=["phase1"])

@app.on_event("startup")
async def startup_event():
    """Démarrage de l'orchestrator"""
    logger.info("=" * 70)
    logger.info("🚀 HOPPER Orchestrator - Phase 1")
    logger.info("=" * 70)
    logger.info("")
    logger.info("✅ Orchestrator démarré")
    logger.info("🎯 Dispatcher: SimpleDispatcher (mots-clés)")
    logger.info("🔗 Services: system_executor")
    logger.info("")
    logger.info("📡 API disponible sur http://localhost:5050")
    logger.info("📖 Documentation: http://localhost:5050/docs")
    logger.info("")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Arrêt de l'orchestrator"""
    logger.info("🛑 Arrêt de l'orchestrator")

@app.get("/")
async def root():
    """Page d'accueil"""
    return {
        "service": "HOPPER Orchestrator",
        "phase": 1,
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "status": "/api/v1/status",
            "command": "/api/v1/command (POST)",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    """Health check global"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🎬 Lancement du serveur...")
    
    uvicorn.run(
        "main_phase1:app",
        host="0.0.0.0",
        port=5050,
        reload=True,
        log_level="info"
    )
