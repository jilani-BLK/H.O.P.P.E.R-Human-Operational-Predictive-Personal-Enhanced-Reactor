"""
HOPPER - API Routes Phase 2
Routes API hybrides: commandes système + conversations LLM
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import time
from loguru import logger

try:
    from core.simple_dispatcher import SimpleDispatcher
    from core.llm_dispatcher import LLMDispatcher
except ImportError:
    from src.orchestrator.core.simple_dispatcher import SimpleDispatcher
    from src.orchestrator.core.llm_dispatcher import LLMDispatcher

try:
    from system_commands_handler import get_system_handler
except ImportError:
    from src.orchestrator.system_commands_handler import get_system_handler

try:
    from conversation_logger import get_conversation_logger
except ImportError:
    from src.orchestrator.conversation_logger import get_conversation_logger


router = APIRouter()

# Dispatchers
simple_dispatcher = SimpleDispatcher()
llm_dispatcher = LLMDispatcher("http://llm:5001")
system_handler = get_system_handler()

# Phase 4: Conversation logger
conv_logger = get_conversation_logger()


class CommandRequest(BaseModel):
    """Requête de commande/conversation"""
    command: str
    conversation_history: list = []
    use_kb: bool = True


class CommandResponse(BaseModel):
    """Réponse unifiée"""
    success: bool
    type: str  # "system" ou "conversation"
    action: str | None = None
    response: str = ""
    output: str = ""
    error: str | None = None
    duration_ms: int = 0
    tokens: int = 0


@router.post("/api/v1/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """
    Exécute une commande (système ou conversation)
    Route intelligemment vers SimpleDispatcher ou LLMDispatcher
    
    Args:
        request: Commande utilisateur avec historique optionnel
        
    Returns:
        Résultat exécution ou réponse conversationnelle
    """
    start_time = time.time()
    command = request.command
    
    logger.info(f"📥 Nouvelle requête : {command}")
    
    # 0. D'abord vérifier si c'est une commande système locale (Phase 5)
    system_cmd = system_handler.detect(command)
    if system_cmd:
        logger.info(f"🎯 Commande système locale détectée: {system_cmd['action']}")
        result = await system_handler.execute(
            action=system_cmd["action"],
            params=system_cmd["params"],
            user_id="user"
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log interaction (Phase 4)
        conv_logger.log_interaction(
            user_input=command,
            response=result["message"] if result["success"] else result.get("error", ""),
            metadata={
                "action": system_cmd["action"],
                "params": system_cmd["params"],
                "duration_ms": duration_ms,
                "success": result["success"]
            },
            type_="system_local"
        )
        
        if result["success"]:
            return CommandResponse(
                success=True,
                type="system_local",
                action=system_cmd["action"],
                response=result["message"],
                output=str(result.get("data", "")),
                duration_ms=duration_ms
            )
        else:
            return CommandResponse(
                success=False,
                type="system_local",
                action=system_cmd["action"],
                error=result["message"],
                duration_ms=duration_ms
            )
    
    # 1. Router vers le bon dispatcher (legacy)
    routing = llm_dispatcher.route(command)
    
    if routing["type"] == "system":
        # === COMMANDE SYSTÈME (legacy system_executor) ===
        logger.info(f"🔀 Routing: SYSTÈME ({routing['reason']})")
        
        # Dispatcher simple (mots-clés)
        parsed = simple_dispatcher.parse_command(command)
        
        if not parsed.get("success"):
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResponse(
                success=False,
                type="system",
                error=parsed.get("error"),
                duration_ms=duration_ms
            )
        
        # Extraire la commande système
        system_command = parsed.get("system_command")
        
        if not system_command:
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResponse(
                success=False,
                type="system",
                error="Commande système non définie",
                duration_ms=duration_ms
            )
        
        # Appeler system_executor
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
                
                return CommandResponse(
                    success=result.get("success", True),
                    type="system",
                    action=parsed.get("action"),
                    output=result.get("stdout", ""),
                    error=result.get("stderr", ""),
                    duration_ms=duration_ms
                )
            else:
                raise Exception(f"system_executor error: {executor_response.text}")
                
        except Exception as e:
            logger.error(f"❌ Erreur system_executor: {e}")
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResponse(
                success=False,
                type="system",
                error=f"Erreur exécution: {str(e)}",
                duration_ms=duration_ms
            )
    
    else:
        # === CONVERSATION LLM ===
        logger.info(f"💬 Routing: CONVERSATION ({routing['reason']})")
        
        # Détection apprentissage: "Apprends que..." → /kb/learn
        command_lower = command.lower()
        learn_keywords = ["apprends que", "retiens que", "souviens-toi que", "savoir que"]
        is_learning = any(keyword in command_lower for keyword in learn_keywords)
        
        if is_learning:
            # Extraire le fait à apprendre (après "que")
            fact = command
            for keyword in learn_keywords:
                if keyword in command_lower:
                    # Découper en ignorant la casse
                    idx = command_lower.find(keyword)
                    if idx >= 0:
                        fact = command[idx + len(keyword):].strip()
                    break
            
            logger.info(f"📚 Apprentissage détecté: {fact[:50]}...")
            
            # Appeler /kb/learn
            try:
                learn_response = requests.post(
                    "http://llm:5001/kb/learn",
                    json={"text": fact},
                    timeout=5
                )
                
                if learn_response.status_code == 200:
                    learn_data = learn_response.json()
                    total_docs = learn_data.get("total_knowledge", 0)
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    response_text = f"D'accord, j'ai appris que {fact}. " \
                                  f"Je dispose maintenant de {total_docs} connaissances dans ma base."
                    
                    logger.success(f"✅ Fait appris: {total_docs} documents total")
                    
                    return CommandResponse(
                        success=True,
                        type="conversation",
                        action="kb_learn",
                        response=response_text,
                        duration_ms=duration_ms
                    )
                else:
                    logger.warning(f"⚠️ KB learn error: {learn_response.status_code}")
                    # Continuer avec LLM normal si KB échoue
            except Exception as e:
                logger.error(f"❌ Erreur KB learn: {e}")
                # Continuer avec LLM normal
        
        # Générer réponse via LLM
        llm_result = llm_dispatcher.generate(
            user_message=command,
            conversation_history=request.conversation_history,
            max_tokens=300,
            temperature=0.7
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        if llm_result.get("success"):
            logger.success(f"✅ Réponse LLM générée en {duration_ms}ms")
            
            # Log conversation (Phase 4)
            conv_logger.log_interaction(
                user_input=command,
                response=llm_result.get("response", ""),
                metadata={
                    "tokens": llm_result.get("tokens", 0),
                    "duration_ms": duration_ms,
                    "conversation_history_length": len(request.conversation_history)
                },
                type_="conversation"
            )
            
            return CommandResponse(
                success=True,
                type="conversation",
                action="llm_response",
                response=llm_result.get("response", ""),
                tokens=llm_result.get("tokens", 0),
                duration_ms=duration_ms
            )
        else:
            logger.error(f"❌ Erreur LLM: {llm_result.get('error')}")
            
            return CommandResponse(
                success=False,
                type="conversation",
                error=llm_result.get("error"),
                response=llm_result.get("response", "Erreur interne"),
                duration_ms=duration_ms
            )


@router.get("/health")
async def health_root():
    """Health check simple pour Docker (racine)"""
    return {"status": "healthy", "phase": 2}


@router.get("/api/v1/health")
async def health_api():
    """Health check simple (API v1)"""
    return {"status": "healthy", "phase": 2}


@router.get("/api/v1/status")
async def status():
    """Status détaillé avec info dispatchers"""
    # Check LLM
    llm_status = "unknown"
    try:
        llm_health = requests.get("http://llm:5001/health", timeout=2)
        if llm_health.status_code == 200:
            llm_status = "healthy"
    except:
        llm_status = "unavailable"
    
    # Check System Executor
    executor_status = "unknown"
    try:
        executor_health = requests.get("http://system_executor:5002/health", timeout=2)
        if executor_health.status_code == 200:
            executor_status = "healthy"
    except:
        executor_status = "unavailable"
    
    return {
        "orchestrator": "healthy",
        "dispatcher": "hybrid_llm_system",
        "services": {
            "llm": llm_status,
            "system_executor": executor_status
        },
        "phase": 2,
        "features": ["system_commands", "conversations", "routing"]
    }
