"""
Routes API Phase 1 - Commandes simples
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time
import requests
from loguru import logger

# Import du dispatcher Phase 1
from core.simple_dispatcher import dispatcher

router = APIRouter()


class CommandRequest(BaseModel):
    """Requête de commande simple"""
    command: str


class CommandResponse(BaseModel):
    """Réponse de commande"""
    success: bool
    action: Optional[str] = None
    message: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


@router.post("/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest) -> Dict[str, Any]:
    """
    Exécute une commande simple (Phase 1)
    
    Pipeline:
    1. Parse la commande avec SimpleDispatcher
    2. Route vers system_executor
    3. Exécute et retourne le résultat
    
    Args:
        request: Commande en langage naturel
        
    Returns:
        Résultat de l'exécution
    """
    start_time = time.time()
    
    try:
        logger.info(f"📥 Nouvelle commande : {request.command}")
        
        # 1. Parser la commande
        parsed = dispatcher.dispatch(request.command)
        
        if not parsed.get("success"):
            logger.warning(f"⚠️  Parsing échoué : {parsed.get('error')}")
            return {
                "success": False,
                "error": parsed.get("error"),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        
        # 2. Extraire la commande système
        system_command = parsed.get("system_command")
        
        if not system_command:
            logger.error("❌ Impossible de construire la commande système")
            return {
                "success": False,
                "error": "Commande système non définie",
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        
        # 3. Appeler system_executor
        logger.info(f"🔀 Routage vers system_executor : {system_command}")
        
        try:
            executor_response = requests.post(
                "http://system_executor:5002/exec",
                json={
                    "command": system_command["command"],
                    "args": system_command.get("args", []),
                    "cwd": system_command.get("cwd"),
                    "timeout": 30
                },
                timeout=35
            )
            
            if executor_response.status_code == 200:
                result = executor_response.json()
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.info(f"✅ Exécution réussie en {duration_ms}ms")
                
                return {
                    "success": result.get("success", True),
                    "action": parsed.get("action"),
                    "message": result.get("message", "Commande exécutée"),
                    "output": result.get("stdout", ""),
                    "duration_ms": duration_ms
                }
            else:
                logger.error(f"❌ system_executor HTTP {executor_response.status_code}")
                return {
                    "success": False,
                    "error": f"system_executor error: {executor_response.text}",
                    "duration_ms": int((time.time() - start_time) * 1000)
                }
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Impossible de contacter system_executor")
            return {
                "success": False,
                "error": "system_executor non disponible. Vérifiez que le service Docker est démarré.",
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout system_executor")
            return {
                "success": False,
                "error": "Timeout: system_executor ne répond pas",
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        
    except Exception as e:
        logger.exception("❌ Erreur inattendue")
        return {
            "success": False,
            "error": f"Erreur interne: {str(e)}",
            "duration_ms": int((time.time() - start_time) * 1000)
        }


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check simple"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "phase": "1"
    }


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Status détaillé de l'orchestrator"""
    
    # Tester system_executor
    system_executor_healthy = False
    try:
        response = requests.get("http://system_executor:5002/health", timeout=2)
        system_executor_healthy = response.status_code == 200
    except:
        pass
    
    return {
        "orchestrator": "healthy",
        "dispatcher": "simple_dispatcher_v1",
        "services": {
            "system_executor": "healthy" if system_executor_healthy else "unhealthy"
        },
        "phase": 1
    }
