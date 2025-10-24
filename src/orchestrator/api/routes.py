"""
Routes API supplémentaires
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

router = APIRouter()


class ServiceStatus(BaseModel):
    """Statut d'un service"""
    name: str
    url: str
    healthy: bool


class FeedbackRequest(BaseModel):
    """Requête de feedback utilisateur"""
    user_id: str
    score: int = Field(..., ge=1, le=5, description="Score de satisfaction 1-5")
    comment: Optional[str] = None
    interaction_type: Optional[str] = None


@router.get("/services")
async def list_services() -> Dict[str, List[str]]:
    """Liste tous les services enregistrés"""
    # TODO: Implémenter avec le service_registry
    return {
        "services": [
            "orchestrator",
            "llm",
            "system_executor",
            "stt",
            "tts",
            "auth",
            "connectors"
        ]
    }


@router.get("/capabilities")
async def get_capabilities() -> Dict[str, Dict[str, bool]]:
    """Retourne les capacités de HOPPER"""
    return {
        "capabilities": {
            "natural_language": True,
            "voice_input": True,
            "voice_output": True,
            "system_actions": True,
            "email_integration": False,  # Phase 2
            "iot_control": False,  # Phase 2
            "learning": True,  # Phase 4 ✅
            "offline_mode": True
        }
    }


@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest, request: Request) -> Dict[str, Any]:
    """
    Soumet un feedback utilisateur pour l'apprentissage (Phase 4)
    
    Args:
        feedback: Données de feedback (score 1-5, commentaire optionnel)
        request: FastAPI Request pour accès au middleware
        
    Returns:
        Confirmation et éventuelle demande de feedback
    """
    # Accéder au middleware d'apprentissage
    if not hasattr(request.state, 'learning'):
        return {
            "message": "Feedback enregistré (learning désactivé)",
            "user_id": feedback.user_id,
            "score": feedback.score
        }
    
    learning = request.state.learning
    
    # Enregistrer le feedback
    response_time_ms = getattr(request.state, 'response_time_ms', None)
    
    learning.add_feedback(
        score=feedback.score,
        comment=feedback.comment,
        interaction_type=feedback.interaction_type,
        response_time_ms=response_time_ms,
        error_occurred=False
    )
    
    # Vérifier si demander feedback
    response_data = {
        "message": "Feedback enregistré avec succès",
        "user_id": feedback.user_id,
        "score": feedback.score
    }
    
    if learning.should_request_feedback():
        response_data["request_feedback"] = True
        response_data["prompt"] = learning.get_feedback_prompt()
    
    return response_data


@router.get("/learning/stats/daily")
async def get_daily_stats(request: Request) -> Dict[str, Any]:
    """
    Retourne les statistiques d'apprentissage du jour (Phase 4)
    
    Returns:
        Statistiques quotidiennes (avg, satisfaction rate, etc.)
    """
    if not hasattr(request.state, 'learning'):
        raise HTTPException(status_code=503, detail="Learning middleware non disponible")
    
    learning = request.state.learning
    stats = learning.get_daily_stats()
    
    return {
        "period": "daily",
        "stats": stats
    }


@router.get("/learning/stats/weekly")
async def get_weekly_stats(request: Request) -> Dict[str, Any]:
    """
    Retourne les statistiques d'apprentissage hebdomadaires (Phase 4)
    
    Returns:
        Statistiques hebdomadaires (trends, issues, etc.)
    """
    if not hasattr(request.state, 'learning'):
        raise HTTPException(status_code=503, detail="Learning middleware non disponible")
    
    learning = request.state.learning
    stats = learning.get_weekly_stats()
    
    return {
        "period": "weekly",
        "stats": stats
    }


@router.get("/learning/conversations/stats")
async def get_conversation_stats(request: Request) -> Dict[str, Any]:
    """
    Retourne les statistiques des conversations collectées (Phase 4)
    
    Returns:
        Stats conversations (total, avg satisfaction, etc.)
    """
    if not hasattr(request.state, 'learning'):
        raise HTTPException(status_code=503, detail="Learning middleware non disponible")
    
    learning = request.state.learning
    stats = learning.get_conversation_stats()
    
    return {
        "conversations": stats
    }


@router.post("/learning/export")
async def export_training_data(
    request: Request,
    min_satisfaction: float = 3.0
) -> Dict[str, Any]:
    """
    Exporte les données de training pour fine-tuning (Phase 4)
    
    Args:
        min_satisfaction: Score minimum pour inclure (défaut: 3.0)
        
    Returns:
        Chemin du fichier exporté
    """
    if not hasattr(request.state, 'learning'):
        raise HTTPException(status_code=503, detail="Learning middleware non disponible")
    
    learning = request.state.learning
    
    try:
        filepath = learning.export_training_data(min_satisfaction=min_satisfaction)
        
        return {
            "success": True,
            "message": "Données exportées avec succès",
            "filepath": filepath,
            "min_satisfaction": min_satisfaction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur export: {str(e)}")

