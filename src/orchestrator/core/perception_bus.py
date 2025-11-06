"""
PerceptionBus - Event-driven architecture
Normalise et route tous les événements (STT, connecteurs, capteurs)
"""

import asyncio
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from collections import deque
from loguru import logger

from core.models import (
    PerceptionEvent,
    InteractionEnvelope,
    InteractionType
)


class PerceptionBus:
    """
    Bus d'événements centralisé pour architecture event-driven
    Tous les inputs (voix, événements, capteurs, connecteurs) passent ici
    """
    
    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        
        # Queue principale d'événements
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        
        # Historique des événements
        self.event_history: deque = deque(maxlen=100)
        
        # Subscribers (handlers par type d'événement)
        self.subscribers: Dict[str, List[Callable]] = {}
        
        # Stats
        self.stats = {
            "total_events": 0,
            "events_by_source": {},
            "events_by_type": {},
            "processing_errors": 0
        }
        
        # État du bus
        self.running = False
        self.processor_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Démarre le bus d'événements"""
        if self.running:
            logger.warning("PerceptionBus déjà démarré")
            return
        
        self.running = True
        self.processor_task = asyncio.create_task(self._process_events())
        logger.info("✅ PerceptionBus démarré")
    
    async def stop(self):
        """Arrête le bus d'événements"""
        self.running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 PerceptionBus arrêté")
    
    async def publish(
        self,
        event: PerceptionEvent
    ) -> bool:
        """
        Publie un événement dans le bus
        
        Args:
            event: PerceptionEvent à publier
            
        Returns:
            True si publié avec succès
        """
        
        try:
            # Ajouter à la queue
            await self.event_queue.put(event)
            
            # Historique
            self.event_history.append(event)
            
            # Stats
            self.stats["total_events"] += 1
            self.stats["events_by_source"][event.source] = \
                self.stats["events_by_source"].get(event.source, 0) + 1
            self.stats["events_by_type"][event.event_type] = \
                self.stats["events_by_type"].get(event.event_type, 0) + 1
            
            logger.debug(f"📤 Event published: {event.source}.{event.event_type}")
            
            return True
            
        except asyncio.QueueFull:
            logger.error("❌ Event queue full!")
            return False
        except Exception as e:
            logger.error(f"❌ Publish error: {e}")
            return False
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[PerceptionEvent], Any]
    ):
        """
        Souscrit à un type d'événement
        
        Args:
            event_type: Type d'événement (ex: 'transcription', 'new_email')
            handler: Fonction appelée lors d'événement (async ou sync)
        """
        
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        logger.info(f"✅ Subscribed to '{event_type}' (handler: {handler.__name__})")
    
    def subscribe_all(
        self,
        handler: Callable[[PerceptionEvent], Any]
    ):
        """
        Souscrit à TOUS les événements
        
        Args:
            handler: Fonction appelée pour chaque événement
        """
        
        self.subscribe("*", handler)
        logger.info(f"✅ Subscribed to ALL events (handler: {handler.__name__})")
    
    async def _process_events(self):
        """
        Boucle de traitement des événements
        Dispatche aux subscribers
        """
        
        logger.info("🔄 Event processor started")
        
        while self.running:
            try:
                # Attendre un événement (timeout pour vérifier self.running)
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                # Dispatcher aux subscribers
                await self._dispatch_event(event)
                
            except asyncio.TimeoutError:
                continue  # Timeout normal, on continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Event processing error: {e}")
                self.stats["processing_errors"] += 1
    
    async def _dispatch_event(self, event: PerceptionEvent):
        """
        Dispatche un événement à tous les subscribers concernés
        
        Args:
            event: Event à dispatcher
        """
        
        # Subscribers spécifiques au type
        handlers = self.subscribers.get(event.event_type, [])
        
        # Subscribers globaux (*)
        handlers.extend(self.subscribers.get("*", []))
        
        if not handlers:
            logger.debug(f"⚠️ No subscribers for {event.event_type}")
            return
        
        # Appeler tous les handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"❌ Handler error ({handler.__name__}): {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du bus"""
        return {
            **self.stats,
            "queue_size": self.event_queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "subscribers_count": sum(len(h) for h in self.subscribers.values()),
            "running": self.running
        }
    
    def get_recent_events(self, limit: int = 10) -> List[PerceptionEvent]:
        """
        Retourne les événements récents
        
        Args:
            limit: Nombre max d'événements
            
        Returns:
            Liste des événements récents
        """
        return list(self.event_history)[-limit:]


class EventPublisher:
    """
    Helper pour publier facilement des événements
    Utilisé par STT, connecteurs, capteurs
    """
    
    def __init__(self, bus: PerceptionBus, source: str):
        self.bus = bus
        self.source = source
    
    async def publish_transcription(
        self,
        text: str,
        user_id: str = "default",
        confidence: float = 1.0
    ):
        """Publie une transcription STT"""
        
        event = PerceptionEvent(
            source=self.source,
            event_type="transcription",
            data={
                "text": text,
                "confidence": confidence
            },
            requires_immediate_response=True,
            target_user=user_id
        )
        
        await self.bus.publish(event)
    
    async def publish_email_received(
        self,
        email_data: Dict[str, Any],
        user_id: str = "default"
    ):
        """Publie un nouvel email reçu"""
        
        event = PerceptionEvent(
            source=self.source,
            event_type="new_email",
            data=email_data,
            priority=7,
            target_user=user_id
        )
        
        await self.bus.publish(event)
    
    async def publish_sensor_data(
        self,
        sensor_type: str,
        value: Any,
        threshold_exceeded: bool = False
    ):
        """Publie des données de capteur"""
        
        event = PerceptionEvent(
            source=self.source,
            event_type=f"sensor_{sensor_type}",
            data={
                "value": value,
                "threshold_exceeded": threshold_exceeded
            },
            priority=9 if threshold_exceeded else 3,
            requires_immediate_response=threshold_exceeded
        )
        
        await self.bus.publish(event)
    
    async def publish_system_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        priority: int = 5
    ):
        """Publie un événement système générique"""
        
        event = PerceptionEvent(
            source=self.source,
            event_type=event_type,
            data=data,
            priority=priority
        )
        
        await self.bus.publish(event)


def create_interaction_from_event(event: PerceptionEvent) -> InteractionEnvelope:
    """
    Convertit un PerceptionEvent en InteractionEnvelope
    Normalisation pour le pipeline LLM
    
    Args:
        event: PerceptionEvent source
        
    Returns:
        InteractionEnvelope normalisée
    """
    
    # Déterminer le type d'interaction
    if event.source == "stt" or event.event_type == "transcription":
        interaction_type = InteractionType.VOICE
    elif event.source.endswith("_connector"):
        interaction_type = InteractionType.CONNECTOR
    elif event.source.startswith("sensor_"):
        interaction_type = InteractionType.SENSOR
    elif event.event_type.startswith("system_"):
        interaction_type = InteractionType.SYSTEM
    else:
        interaction_type = InteractionType.EVENT
    
    return InteractionEnvelope(
        type=interaction_type,
        payload=event.data,
        timestamp=event.timestamp,
        user_id=event.target_user or "default",
        metadata={
            "source": event.source,
            "event_type": event.event_type,
            "priority": event.priority,
            "requires_immediate_response": event.requires_immediate_response
        }
    )


# ==================== EXPORT ====================

__all__ = [
    'PerceptionBus',
    'EventPublisher',
    'create_interaction_from_event'
]
