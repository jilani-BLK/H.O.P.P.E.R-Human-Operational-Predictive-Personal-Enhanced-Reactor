"""
HOPPER - Orchestrateur Central
Module principal coordonnant tous les services de l'assistant
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from loguru import logger
import sys
import asyncio

from core.dispatcher import IntentDispatcher
from core.context_manager import ContextManager
from core.service_registry import ServiceRegistry
from api.routes import router

# Import security middleware
try:
    from middleware.security import security_middleware, cleanup_rate_limiter_task
except ImportError:
    logger.warning("⚠️ Security middleware non disponible")
    security_middleware = None
    cleanup_rate_limiter_task = None

# Import learning middleware (Phase 4)
try:
    from src.learning.integration.fastapi_middleware import LearningMiddleware
    learning_enabled = True
except ImportError:
    logger.warning("⚠️ Learning middleware non disponible")
    learning_enabled = False
    LearningMiddleware = None

# Import coordination hub
try:
    from coordination_hub import (
        initialize_hub,
        get_hub,
        ModuleType,
        register_core_module,
        register_llm_module
    )
    from module_registry import register_all_hopper_modules
    coordination_hub_enabled = True
except ImportError:
    logger.warning("⚠️ Coordination Hub non disponible")
    coordination_hub_enabled = False
    initialize_hub = None  # type: ignore[assignment]
    get_hub = None  # type: ignore[assignment]
    register_all_hopper_modules = None  # type: ignore[assignment]

try:
    from .config import settings
except ImportError:
    from config import settings  # type: ignore[import-not-found]

# Configuration des logs
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    "../../data/logs/orchestrator_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

# Gestionnaires globaux
context_manager = ContextManager()
service_registry = ServiceRegistry()
intent_dispatcher = IntentDispatcher(service_registry, context_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    logger.info("🚀 Démarrage de HOPPER Orchestrator")
    
    # ============================================
    # 1. Initialiser le Coordination Hub
    # ============================================
    coordination_hub = None
    if coordination_hub_enabled and initialize_hub:
        coordination_hub = initialize_hub()
        logger.info("🎯 Coordination Hub initialisé")
        
        # Enregistrer les modules core
        register_core_module("context_manager", context_manager)
        register_core_module("service_registry", service_registry)
        register_core_module("intent_dispatcher", intent_dispatcher, ["service_registry", "context_manager"])
        
        logger.info("✅ Modules core enregistrés dans le hub")
    
    # ============================================
    # 2. Enregistrer les services
    # ============================================
    await service_registry.register_services()
    health_status = await service_registry.check_all_health()
    logger.info(f"État des services: {health_status}")
    
    # Enregistrer les services dans le hub
    if coordination_hub:
        for service_name, service_data in service_registry.services.items():
            if hasattr(service_data, 'url'):
                coordination_hub.register_module(
                    service_name,
                    ModuleType.CORE,  # Ou déterminer le type selon le service
                    service_data,
                    []
                )
    
    # ============================================
    # 4. Enregistrer tous les modules HOPPER
    # ============================================
    if coordination_hub and register_all_hopper_modules:
        await register_all_hopper_modules()
        logger.info("🔗 Tous les modules HOPPER enregistrés et coordonnés")
    
    # ============================================
    # 5. Initialiser tous les modules
    # ============================================
    if coordination_hub:
        await coordination_hub.initialize_all()
        
        # Afficher statistiques
        stats = coordination_hub.get_statistics()
        logger.info(f"📊 Hub: {stats['total_modules']} modules, {stats['modules_by_type']}")
    
    logger.success("✅ HOPPER Orchestrator prêt - Tous les modules coordonnés")
    
    # Lancer cleanup task rate limiter
    cleanup_task = None
    if cleanup_rate_limiter_task:
        cleanup_task = asyncio.create_task(cleanup_rate_limiter_task())
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt de HOPPER Orchestrator")
    
    # Arrêter via le hub
    if coordination_hub:
        await coordination_hub.shutdown_all()
    
    await service_registry.close_all()
    if cleanup_task:
        cleanup_task.cancel()


# Initialisation de l'application FastAPI
app = FastAPI(
    title="HOPPER Orchestrator",
    description="Assistant Personnel Intelligent Autonome",
    version="0.1.0",
    lifespan=lifespan
)

# Appliquer middleware de sécurité
if security_middleware:
    app.middleware("http")(security_middleware)
    logger.info("✅ Security middleware activé (rate limiting + auth)")

# Appliquer middleware d'apprentissage (Phase 4)
if learning_enabled and LearningMiddleware:
    app.add_middleware(LearningMiddleware)
    logger.info("✅ Learning middleware activé (preferences + feedback + training data)")
else:
    logger.warning("⚠️ Learning middleware désactivé")


# Modèles de données
class CommandRequest(BaseModel):
    """Requête de commande utilisateur"""
    text: str
    user_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None
    voice_input: bool = False


class CommandResponse(BaseModel):
    """Réponse à une commande"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    actions_taken: List[str] = []


@app.get("/")
async def root():
    """Point d'entrée principal"""
    return {
        "service": "HOPPER Orchestrator",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Vérification de l'état de santé"""
    services_health = await service_registry.check_all_health()
    all_healthy = all(services_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services_health
    }


@app.post("/command", response_model=CommandResponse)
async def process_command(request: CommandRequest, req: Request):
    """
    Point d'entrée principal pour traiter une commande utilisateur
    
    Args:
        request: Commande de l'utilisateur avec contexte
        req: FastAPI Request pour accès au middleware
        
    Returns:
        Réponse structurée avec résultats
    """
    try:
        # Ensure user_id is not None
        user_id: str = request.user_id or "default"
        
        logger.info(f"📥 Commande reçue: '{request.text}' (user: {user_id})")
        
        # Mise à jour du contexte
        if request.context:
            context_manager.update_context(user_id, request.context)
        
        # Récupération du contexte actuel
        current_context = context_manager.get_context(user_id)
        
        # Dispatch de la commande
        result = await intent_dispatcher.dispatch(
            text=request.text,
            user_id=user_id,
            context=current_context
        )
        
        # Mise à jour du contexte avec les résultats
        context_manager.add_to_history(
            user_id,
            user_input=request.text,
            assistant_response=result.get("message", "")
        )
        
        # PHASE 4: Collecter l'interaction pour l'apprentissage
        if learning_enabled and hasattr(req.state, 'learning'):
            learning = req.state.learning
            learning.collect_interaction(
                user_id=user_id,
                user_input=request.text,
                assistant_response=result.get("message", ""),
                intent=result.get("intent"),
                error=None
            )
        
        logger.success(f"✅ Commande traitée avec succès")
        
        # PHASE 4: Vérifier si on doit demander du feedback
        should_request_feedback = False
        feedback_prompt = None
        if learning_enabled and hasattr(req.state, 'learning'):
            learning = req.state.learning
            if learning.should_request_feedback():
                should_request_feedback = True
                feedback_prompt = learning.get_feedback_prompt()
        
        # Enrichir la réponse avec feedback si nécessaire
        response_data = result.get("data", {}) or {}
        if should_request_feedback:
            response_data["feedback_requested"] = True
            response_data["feedback_prompt"] = feedback_prompt
        
        return CommandResponse(
            success=True,
            message=result.get("message", "Commande exécutée"),
            data=response_data,
            actions_taken=result.get("actions", [])
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement: {str(e)}")
        
        # PHASE 4: Collecter l'erreur
        if learning_enabled and hasattr(req.state, 'learning'):
            learning = req.state.learning
            error_user_id: str = request.user_id or "default"
            learning.collect_interaction(
                user_id=error_user_id,
                user_input=request.text,
                assistant_response=f"Erreur: {str(e)}",
                error=str(e)
            )
        
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/context")
async def create_user_context(request: Dict[str, Any]) -> Dict[str, Any]:
    """Crée un nouveau contexte pour un utilisateur"""
    user_id = request.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id requis")
    
    # Initialiser le contexte (vide au départ)
    context_manager.clear_context(user_id)
    
    return {
        "user_id": user_id,
        "context": {},
        "created": True
    }


@app.get("/context/{user_id}")
async def get_user_context(user_id: str) -> Dict[str, Any]:
    """Récupère le contexte d'un utilisateur"""
    context = context_manager.get_context(user_id)
    
    # Convertir deque en list pour la sérialisation JSON
    serializable_context = dict(context)
    serializable_context["conversation_history"] = list(context["conversation_history"])
    
    return {
        "user_id": user_id,
        "context": serializable_context
    }


@app.delete("/context/{user_id}")
async def clear_user_context(user_id: str):
    """Efface le contexte d'un utilisateur"""
    context_manager.clear_context(user_id)
    return {"message": f"Contexte effacé pour {user_id}"}


@app.get("/coordination/stats")
async def get_coordination_stats() -> Dict[str, Any]:
    """Récupère les statistiques du Coordination Hub"""
    if coordination_hub_enabled and get_hub:
        try:
            hub = get_hub()
            stats = hub.get_statistics()
            
            return {
                "total_modules": stats.get("total_modules", 0),
                "modules_by_type": stats.get("modules_by_type", {}),
                "modules": []
            }
        except Exception as e:
            return {
                "error": str(e),
                "total_modules": 0,
                "modules_by_type": {}
            }
    else:
        return {
            "error": "Coordination Hub non disponible",
            "total_modules": 0,
            "modules_by_type": {}
        }


@app.get("/coordination/health")
async def get_coordination_health() -> Dict[str, Any]:
    """Vérifie la santé de tous les modules coordonnés"""
    if coordination_hub_enabled and get_hub:
        try:
            hub = get_hub()
            health_status = await hub.check_all_health()
            
            return {
                "status": "operational",
                "modules": health_status
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "modules": {}
            }
    else:
        return {
            "status": "unavailable",
            "modules": {}
        }


# Inclusion des routes API additionnelles
app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("ORCHESTRATOR_PORT", 5000))
    host = os.getenv("ORCHESTRATOR_HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # Désactivé pour éviter conflicts de port
        log_level=settings.LOG_LEVEL.lower()
    )
