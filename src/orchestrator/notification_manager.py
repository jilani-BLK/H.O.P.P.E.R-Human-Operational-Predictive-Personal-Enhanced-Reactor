"""
Notification Manager - Phase 3
Gestion des notifications proactives (emails, événements, etc.)
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import requests
from collections import deque

logger = logging.getLogger(__name__)


class Notification:
    """Représente une notification"""
    
    def __init__(
        self,
        source: str,
        type: str,
        priority: int,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ):
        self.source = source  # email, calendar, system, etc.
        self.type = type  # new_email, event_reminder, etc.
        self.priority = priority  # 0-10
        self.title = title
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()
        self.delivered = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "type": self.type,
            "priority": self.priority,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "delivered": self.delivered
        }


class NotificationManager:
    """Gestionnaire de notifications proactives"""
    
    def __init__(
        self,
        tts_url: str = "http://tts_piper:5004",
        email_url: Optional[str] = None,  # Disabled for now
        llm_url: str = "http://llm:5001"
    ):
        self.tts_url = tts_url
        self.email_url = email_url
        self.llm_url = llm_url
        self.email_enabled = False  # Email features disabled
        
        # Queue de notifications
        self.notification_queue: deque = deque(maxlen=100)
        self.pending_notifications: List[Notification] = []
        
        # Seuils de notification
        self.min_priority = 7  # Notifier si priorité >= 7
        self.notification_interval = 5  # Secondes entre notifications
        
        # État
        self.running = False
        self.last_notification_time = None
        
        logger.info("✅ NotificationManager initialized")
    
    def add_notification(self, notification: Notification):
        """Ajouter une notification à la queue"""
        self.notification_queue.append(notification)
        
        if notification.priority >= self.min_priority:
            self.pending_notifications.append(notification)
            logger.info(
                f"🔔 New priority notification: {notification.title} "
                f"(priority={notification.priority})"
            )
    
    async def check_email_notifications(self) -> List[Notification]:
        """
        Vérifier les nouveaux emails et créer des notifications
        
        Returns:
            Liste de notifications créées
        """
        # Email features disabled
        if not self.email_enabled or not self.email_url:
            return []
            
        try:
            # Récupérer emails non lus
            response = requests.get(
                f"{self.email_url}/emails/unread",
                params={"limit": 10},
                timeout=5
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch emails: {response.status_code}")
                return []
            
            result = response.json()
            emails = result.get("emails", [])
            
            if not emails:
                return []
            
            logger.info(f"📧 Found {len(emails)} unread emails")
            
            notifications = []
            for email in emails:
                # Scorer l'importance via LLM
                priority = await self._score_email_importance(email)
                
                notification = Notification(
                    source="email",
                    type="new_email",
                    priority=priority,
                    title=f"Nouveau mail de {email.get('from_', 'Inconnu')}",
                    message=f"Sujet: {email.get('subject', 'Sans sujet')}",
                    data=email
                )
                
                self.add_notification(notification)
                notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"❌ Error checking email notifications: {e}")
            return []
    
    async def _score_email_importance(self, email: Dict) -> int:
        """
        Scorer l'importance d'un email avec le LLM
        
        Args:
            email: Dict contenant from, subject, preview
            
        Returns:
            Score 0-10
        """
        try:
            prompt = f"""Analyse cet email et donne un score d'importance de 0 à 10.

De: {email.get('from_', 'Inconnu')}
Sujet: {email.get('subject', 'Sans sujet')}
Aperçu: {email.get('preview', '')[:200]}

Critères:
- Expéditeur connu/important: +3
- Mots-clés urgents (urgent, important, rappel): +2
- Questions directes: +1
- Newsletters, pub: -3

Réponds juste avec un nombre de 0 à 10."""

            response = requests.post(
                f"{self.llm_url}/generate",
                json={"prompt": prompt, "max_tokens": 10},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "5").strip()
                
                # Extraire le score
                try:
                    score = int(text.split()[0])
                    score = max(0, min(10, score))  # Clamp 0-10
                    logger.info(f"Email importance score: {score}/10")
                    return score
                except:
                    logger.warning("Could not parse LLM score, using default")
                    return 5
            else:
                logger.warning("LLM scoring failed, using default")
                return 5
                
        except Exception as e:
            logger.error(f"❌ Error scoring email: {e}")
            return 5  # Score par défaut
    
    async def deliver_notification(self, notification: Notification):
        """
        Délivrer une notification vocalement
        
        Args:
            notification: Notification à délivrer
        """
        try:
            # Créer message vocal
            vocal_message = f"{notification.title}. {notification.message}"
            
            logger.info(f"🔊 Delivering notification: {vocal_message}")
            
            # Synthétiser avec TTS
            response = requests.post(
                f"{self.tts_url}/synthesize",
                json={"text": vocal_message},
                timeout=5
            )
            
            if response.status_code == 200:
                # TODO: Jouer l'audio
                # Pour l'instant, juste logger
                logger.info("✅ Notification audio generated")
                notification.delivered = True
                self.last_notification_time = datetime.now()
            else:
                logger.error(f"TTS failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error delivering notification: {e}")
    
    async def process_pending_notifications(self):
        """Traiter les notifications en attente"""
        if not self.pending_notifications:
            return
        
        # Trier par priorité
        self.pending_notifications.sort(key=lambda n: n.priority, reverse=True)
        
        # Délivrer la plus importante
        notification = self.pending_notifications.pop(0)
        await self.deliver_notification(notification)
    
    async def run_polling_loop(self):
        """
        Boucle de polling pour vérifier les notifications
        """
        self.running = True
        logger.info("🔄 Notification polling started")
        
        while self.running:
            try:
                # Vérifier emails
                await self.check_email_notifications()
                
                # Traiter notifications en attente
                await self.process_pending_notifications()
                
                # Attendre avant prochaine vérification
                await asyncio.sleep(60)  # 60 secondes
                
            except Exception as e:
                logger.error(f"❌ Error in polling loop: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Arrêter le polling"""
        self.running = False
        logger.info("⏹️  Notification polling stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du notification manager"""
        return {
            "total_notifications": len(self.notification_queue),
            "pending_notifications": len(self.pending_notifications),
            "min_priority": self.min_priority,
            "running": self.running,
            "last_notification": self.last_notification_time.isoformat() if self.last_notification_time else None
        }


# Instance globale
notification_manager = NotificationManager()


async def main():
    """Test du notification manager"""
    print("NotificationManager test mode")
    
    # Test notification
    notif = Notification(
        source="test",
        type="test",
        priority=8,
        title="Test notification",
        message="Ceci est un test"
    )
    
    notification_manager.add_notification(notif)
    
    print(f"Stats: {notification_manager.get_stats()}")
    
    # Délivrer
    await notification_manager.deliver_notification(notif)


if __name__ == "__main__":
    asyncio.run(main())
