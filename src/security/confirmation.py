"""
HOPPER - Confirmation Engine
Système de demande de confirmation pour actions sensibles
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from loguru import logger


class ConfirmationRequest:
    """Requête de confirmation"""
    def __init__(
        self,
        action: str,
        params: Dict[str, Any],
        risk: str,
        reason: str,
        user_id: str,
        timeout: int = 30
    ):
        self.action = action
        self.params = params
        self.risk = risk
        self.reason = reason
        self.user_id = user_id
        self.timeout = timeout
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=timeout)
        self.confirmed: Optional[bool] = None
        self.response_at: Optional[datetime] = None


class ConfirmationEngine:
    """
    Moteur de confirmation pour actions sensibles
    
    Modes:
    - CLI: Demande via terminal (input)
    - API: Stocke requête, attend réponse via endpoint
    - AUTO: Confirme automatiquement (dev only)
    """
    
    def __init__(self, mode: str = "cli", auto_confirm: bool = False):
        self.mode = mode
        self.auto_confirm = auto_confirm
        self.pending_requests: Dict[str, ConfirmationRequest] = {}
    
    async def request_confirmation(
        self,
        action: str,
        params: Dict[str, Any],
        risk: str,
        reason: str,
        user_id: str = "default",
        timeout: int = 30
    ) -> bool:
        """
        Demande confirmation pour une action
        
        Args:
            action: Nom de l'action
            params: Paramètres de l'action
            risk: Niveau de risque
            reason: Raison de la confirmation
            user_id: ID utilisateur
            timeout: Timeout en secondes
            
        Returns:
            True si confirmé, False sinon
        """
        # Mode auto-confirm (dev)
        if self.auto_confirm:
            logger.warning(f"⚠️ AUTO-CONFIRM activé: {action} (DEV MODE)")
            return True
        
        # Créer requête
        request = ConfirmationRequest(
            action=action,
            params=params,
            risk=risk,
            reason=reason,
            user_id=user_id,
            timeout=timeout
        )
        
        # Mode CLI
        if self.mode == "cli":
            return await self._request_cli(request)
        
        # Mode API
        elif self.mode == "api":
            return await self._request_api(request)
        
        # Par défaut: refuser
        logger.error(f"❌ Mode confirmation inconnu: {self.mode}")
        return False
    
    async def _request_cli(self, request: ConfirmationRequest) -> bool:
        """Demande confirmation via CLI"""
        logger.warning("⚠️" * 20)
        logger.warning(f"🔐 CONFIRMATION REQUISE")
        logger.warning(f"Action: {request.action}")
        logger.warning(f"Risque: {request.risk}")
        logger.warning(f"Raison: {request.reason}")
        logger.warning(f"Paramètres: {request.params}")
        logger.warning("⚠️" * 20)
        
        # Demander confirmation avec timeout
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    input,
                    f"\n⚠️  Confirmer l'action '{request.action}'? (oui/non) [timeout: {request.timeout}s]: "
                ),
                timeout=request.timeout
            )
            
            confirmed = response.lower() in ["oui", "yes", "y", "o"]
            request.confirmed = confirmed
            request.response_at = datetime.now()
            
            if confirmed:
                logger.success(f"✅ Action confirmée: {request.action}")
            else:
                logger.info(f"❌ Action refusée: {request.action}")
            
            return confirmed
            
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout confirmation pour: {request.action}")
            request.confirmed = False
            request.response_at = datetime.now()
            return False
    
    async def _request_api(self, request: ConfirmationRequest) -> bool:
        """
        Demande confirmation via API
        Stocke la requête et attend une réponse
        """
        request_id = f"{request.user_id}_{request.action}_{datetime.now().timestamp()}"
        self.pending_requests[request_id] = request
        
        logger.info(f"📝 Requête confirmation créée: {request_id}")
        
        # Attendre réponse ou timeout
        start = datetime.now()
        while (datetime.now() - start).seconds < request.timeout:
            if request.confirmed is not None:
                logger.info(f"✅ Réponse reçue: {request.confirmed}")
                del self.pending_requests[request_id]
                return request.confirmed
            
            await asyncio.sleep(0.5)
        
        # Timeout
        logger.error(f"⏱️ Timeout confirmation API: {request_id}")
        del self.pending_requests[request_id]
        return False
    
    def respond_to_request(self, request_id: str, confirmed: bool) -> bool:
        """
        Répond à une requête de confirmation (mode API)
        
        Args:
            request_id: ID de la requête
            confirmed: True pour confirmer, False pour refuser
            
        Returns:
            True si réponse enregistrée
        """
        request = self.pending_requests.get(request_id)
        if not request:
            logger.error(f"❌ Requête inconnue: {request_id}")
            return False
        
        # Vérifier timeout
        if datetime.now() > request.expires_at:
            logger.error(f"⏱️ Requête expirée: {request_id}")
            del self.pending_requests[request_id]
            return False
        
        # Enregistrer réponse
        request.confirmed = confirmed
        request.response_at = datetime.now()
        
        logger.info(f"{'✅' if confirmed else '❌'} Confirmation: {request_id}")
        return True
    
    def get_pending_requests(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Récupère les requêtes en attente
        
        Args:
            user_id: Filtrer par utilisateur
            
        Returns:
            Dict[request_id, request_data]
        """
        # Nettoyer les requêtes expirées
        now = datetime.now()
        expired = [
            req_id for req_id, req in self.pending_requests.items()
            if now > req.expires_at
        ]
        for req_id in expired:
            del self.pending_requests[req_id]
        
        # Filtrer par user_id si spécifié
        requests = self.pending_requests
        if user_id:
            requests = {
                req_id: req for req_id, req in requests.items()
                if req.user_id == user_id
            }
        
        # Formater pour JSON
        return {
            req_id: {
                "action": req.action,
                "params": req.params,
                "risk": req.risk,
                "reason": req.reason,
                "user_id": req.user_id,
                "created_at": req.created_at.isoformat(),
                "expires_at": req.expires_at.isoformat(),
                "timeout_seconds": req.timeout
            }
            for req_id, req in requests.items()
        }


# Instance globale
# MODE DEV: auto_confirm=True pour tester sans bloquer
# MODE PROD: auto_confirm=False pour demander confirmation réelle
import os
DEV_MODE = os.getenv("HOPPER_DEV_MODE", "false").lower() == "true"
confirmation_engine = ConfirmationEngine(mode="cli", auto_confirm=DEV_MODE)
