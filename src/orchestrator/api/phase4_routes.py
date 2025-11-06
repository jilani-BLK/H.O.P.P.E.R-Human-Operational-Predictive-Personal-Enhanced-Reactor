"""
HOPPER - Phase 4 Routes
Routes API pour Intelligence & Apprentissage

Endpoints:
- POST /feedback - Enregistrer feedback utilisateur (thumbs up/down)
- GET /stats/conversations - Statistiques conversations du jour
- POST /training/export - Exporter dataset pour fine-tuning
- GET /metrics - Métriques qualité & performance
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from loguru import logger

try:
    from conversation_logger import get_conversation_logger
except ImportError:
    from src.orchestrator.conversation_logger import get_conversation_logger


router = APIRouter(prefix="/api/v1", tags=["phase4"])


# === Models ===

class FeedbackRequest(BaseModel):
    """Feedback utilisateur sur une interaction"""
    user_input: str
    response: str
    feedback: Literal["positive", "negative", "neutral"]
    comment: Optional[str] = None
    user_id: str = "default"


class ExportRequest(BaseModel):
    """Paramètres export dataset"""
    output_file: str = "data/training/finetune_dataset.jsonl"
    min_quality: float = 0.0
    types: list[str] = ["conversation"]


# === Routes Feedback ===

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Enregistrer feedback utilisateur (👍/👎)
    
    Exemple:
    ```json
    {
        "user_input": "Quelle est la météo?",
        "response": "Je ne peux pas...",
        "feedback": "negative",
        "comment": "Devrait intégrer API météo",
        "user_id": "john"
    }
    ```
    """
    logger.info(f"📥 Feedback reçu: {request.feedback}")
    
    conv_logger = get_conversation_logger()
    conv_logger.log_feedback(
        user_input=request.user_input,
        response=request.response,
        feedback=request.feedback,
        comment=request.comment,
        user_id=request.user_id
    )
    
    return {
        "success": True,
        "message": f"Feedback '{request.feedback}' enregistré",
        "thank_you": "Merci ! Cela aide HOPPER à s'améliorer."
    }


# === Routes Statistiques ===

@router.get("/stats/conversations")
async def get_conversation_stats():
    """Statistiques des conversations du jour"""
    conv_logger = get_conversation_logger()
    stats = conv_logger.get_stats()
    
    return {
        "success": True,
        "date": "today",
        "stats": stats
    }


@router.get("/conversations/today")
async def get_today_conversations(limit: int = 50):
    """
    Récupérer les dernières conversations du jour
    
    Args:
        limit: Nombre maximum de conversations à retourner
    """
    conv_logger = get_conversation_logger()
    conversations = conv_logger.get_today_conversations()
    
    # Limiter le nombre
    conversations = conversations[-limit:] if len(conversations) > limit else conversations
    
    return {
        "success": True,
        "count": len(conversations),
        "conversations": conversations
    }


# === Routes Training ===

@router.post("/training/export")
async def export_for_training(request: ExportRequest):
    """
    Exporter conversations pour fine-tuning
    
    Format de sortie: JSONL compatible avec fine-tuning
    ```json
    {"instruction": "...", "input": "...", "output": "..."}
    ```
    
    Exemple:
    ```json
    {
        "output_file": "data/training/my_dataset.jsonl",
        "min_quality": 0.5,
        "types": ["conversation", "system_local"]
    }
    ```
    """
    logger.info(f"📤 Export dataset: {request.output_file}")
    
    conv_logger = get_conversation_logger()
    count = conv_logger.export_for_finetuning(
        output_file=request.output_file,
        min_quality=request.min_quality,
        types=request.types
    )
    
    if count > 0:
        return {
            "success": True,
            "message": f"{count} conversations exportées",
            "output_file": request.output_file,
            "count": count
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="Aucune conversation à exporter"
        )


# === Routes Métriques ===

@router.get("/metrics")
async def get_metrics():
    """
    Métriques qualité & performance globales
    
    Retourne:
    - Nombre total d'interactions
    - Taux de satisfaction (feedbacks)
    - Temps de réponse moyen
    - Types d'interactions les plus fréquents
    """
    conv_logger = get_conversation_logger()
    stats = conv_logger.get_stats()
    
    # Calcul métriques
    total_feedbacks = sum(stats["feedbacks"].values())
    satisfaction_rate = 0.0
    if total_feedbacks > 0:
        positive = stats["feedbacks"]["positive"]
        satisfaction_rate = (positive / total_feedbacks) * 100
    
    return {
        "success": True,
        "metrics": {
            "total_interactions": stats["total"],
            "active_users": stats["user_count"],
            "satisfaction_rate": round(satisfaction_rate, 1),
            "feedbacks": stats["feedbacks"],
            "by_type": stats["by_type"],
            "file": stats["file"]
        }
    }


# === Routes Analyse ===

@router.get("/analyze/errors")
async def analyze_errors():
    """
    Analyser les interactions avec erreurs
    
    Retourne les patterns d'erreurs fréquents pour amélioration
    """
    conv_logger = get_conversation_logger()
    conversations = conv_logger.get_today_conversations()
    
    # Filtrer les erreurs
    errors = [
        c for c in conversations
        if not c.get("metadata", {}).get("success", True)
    ]
    
    # Grouper par type d'erreur
    error_patterns = {}
    for error in errors:
        error_type = error.get("type", "unknown")
        error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
    
    return {
        "success": True,
        "total_errors": len(errors),
        "error_rate": round((len(errors) / len(conversations) * 100), 1) if conversations else 0,
        "patterns": error_patterns,
        "recent_errors": errors[-10:]  # 10 dernières erreurs
    }
