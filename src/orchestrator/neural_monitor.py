"""
HOPPER - Neural Activity Monitor
Middleware pour capturer et streamer l'activité de l'orchestrator
en temps réel vers l'interface neuronale
"""

from typing import Optional, Dict, Any, Callable
from loguru import logger
import httpx
import asyncio
import time
from functools import wraps
from contextlib import asynccontextmanager


class NeuralActivityMonitor:
    """
    Moniteur d'activité neuronale
    
    Capture les événements de l'orchestrator et les envoie
    au serveur neural interface via API HTTP
    """
    
    def __init__(
        self,
        neural_server_url: str = "http://localhost:5050",
        enabled: bool = True,
        batch_events: bool = False
    ):
        """
        Args:
            neural_server_url: URL du serveur neural interface
            enabled: Activer/désactiver le monitoring
            batch_events: Batching des événements (pas encore implémenté)
        """
        self.neural_server_url = neural_server_url
        self.enabled = enabled
        self.batch_events = batch_events
        
        self.client: Optional[httpx.AsyncClient] = None
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        
        # Statistiques
        self.stats = {
            "events_sent": 0,
            "events_failed": 0,
            "last_event_time": None
        }
        
        logger.info(f"🧠 NeuralActivityMonitor initialized (enabled: {enabled})")
    
    async def start(self):
        """Démarre le moniteur"""
        if not self.enabled:
            return
        
        self.client = httpx.AsyncClient(timeout=5.0)
        
        # Démarrer worker pour envoyer les événements
        self.worker_task = asyncio.create_task(self._event_worker())
        
        logger.success("✅ Neural monitor started")
    
    async def stop(self):
        """Arrête le moniteur"""
        if not self.enabled:
            return
        
        # Arrêter le worker
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        # Fermer le client HTTP
        if self.client:
            await self.client.aclose()
        
        logger.info("🛑 Neural monitor stopped")
    
    async def _event_worker(self):
        """Worker qui traite la queue d'événements"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._send_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Event worker error: {e}")
    
    async def _send_event(self, event: dict):
        """Envoie un événement au serveur neural"""
        if not self.client:
            return
        
        try:
            response = await self.client.post(
                f"{self.neural_server_url}/api/neural/event",
                json=event,
                timeout=2.0
            )
            
            if response.status_code == 200:
                self.stats["events_sent"] += 1
                self.stats["last_event_time"] = time.time()
            else:
                self.stats["events_failed"] += 1
                logger.warning(f"⚠️ Event send failed: {response.status_code}")
                
        except Exception as e:
            self.stats["events_failed"] += 1
            logger.debug(f"Neural server unavailable: {e}")
    
    async def emit_neural_activity(
        self,
        event_type: str,
        intensity: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Émet une activité neuronale
        
        Args:
            event_type: Type (stt, llm, tts, dispatch, service)
            intensity: Intensité 0.0-1.0
            metadata: Métadonnées additionnelles
        """
        if not self.enabled:
            return
        
        event = {
            "type": "neural_activity",
            "payload": {
                "event_type": event_type,
                "intensity": intensity,
                "metadata": metadata or {},
                "timestamp": time.time()
            }
        }
        
        await self.event_queue.put(event)
    
    async def emit_service_event(
        self,
        service: str,
        status: str,
        duration: Optional[float] = None
    ):
        """
        Émet un événement de service
        
        Args:
            service: Nom du service
            status: Status (active, completed, error)
            duration: Durée d'exécution
        """
        if not self.enabled:
            return
        
        if not self.client:
            return
        
        try:
            await self.client.post(
                f"{self.neural_server_url}/api/neural/service",
                json={
                    "service": service,
                    "status": status,
                    "duration": duration
                },
                timeout=2.0
            )
        except Exception as e:
            logger.debug(f"Service event send failed: {e}")
    
    async def emit_voice_activity(
        self,
        speaking: bool,
        text: Optional[str] = None,
        duration: Optional[float] = None
    ):
        """
        Émet une activité vocale
        
        Args:
            speaking: True si HOPPER parle
            text: Texte prononcé
            duration: Durée
        """
        if not self.enabled:
            return
        
        if not self.client:
            return
        
        try:
            await self.client.post(
                f"{self.neural_server_url}/api/neural/voice",
                json={
                    "speaking": speaking,
                    "text": text,
                    "duration": duration
                },
                timeout=2.0
            )
        except Exception as e:
            logger.debug(f"Voice activity send failed: {e}")


# Instance globale
_neural_monitor: Optional[NeuralActivityMonitor] = None


def get_neural_monitor() -> Optional[NeuralActivityMonitor]:
    """Retourne l'instance du moniteur neural"""
    return _neural_monitor


def init_neural_monitor(
    neural_server_url: str = "http://localhost:5050",
    enabled: bool = True
) -> NeuralActivityMonitor:
    """
    Initialise le moniteur neural global
    
    Usage:
        monitor = init_neural_monitor()
        await monitor.start()
    """
    global _neural_monitor
    _neural_monitor = NeuralActivityMonitor(neural_server_url, enabled)
    return _neural_monitor


# ============================================
# Décorateurs pour tracking automatique
# ============================================

def track_neural_activity(event_type: str, intensity: float = 1.0):
    """
    Décorateur pour tracker automatiquement l'activité neuronale
    
    Usage:
        @track_neural_activity("llm", intensity=1.5)
        async def generate_response(text):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitor = get_neural_monitor()
            
            if monitor and monitor.enabled:
                # Émettre début d'activité
                await monitor.emit_neural_activity(
                    event_type=event_type,
                    intensity=intensity,
                    metadata={"function": func.__name__, "status": "start"}
                )
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Émettre fin d'activité
                if monitor and monitor.enabled:
                    duration = time.time() - start_time
                    await monitor.emit_neural_activity(
                        event_type=event_type,
                        intensity=intensity * 0.5,
                        metadata={
                            "function": func.__name__,
                            "status": "completed",
                            "duration": duration
                        }
                    )
                
                return result
                
            except Exception as e:
                # Émettre erreur
                if monitor and monitor.enabled:
                    await monitor.emit_neural_activity(
                        event_type=event_type,
                        intensity=0.3,
                        metadata={
                            "function": func.__name__,
                            "status": "error",
                            "error": str(e)
                        }
                    )
                raise
        
        return wrapper
    return decorator


@asynccontextmanager
async def neural_activity_context(
    event_type: str,
    intensity: float = 1.0,
    metadata: Optional[Dict] = None
):
    """
    Context manager pour tracker l'activité neuronale
    
    Usage:
        async with neural_activity_context("llm", intensity=1.5):
            response = await generate_response(text)
    """
    monitor = get_neural_monitor()
    
    if monitor and monitor.enabled:
        await monitor.emit_neural_activity(event_type, intensity, metadata)
    
    start_time = time.time()
    
    try:
        yield
    finally:
        if monitor and monitor.enabled:
            duration = time.time() - start_time
            await monitor.emit_neural_activity(
                event_type,
                intensity * 0.5,
                {**(metadata or {}), "duration": duration}
            )


# ============================================
# Helper functions
# ============================================

async def emit_stt_activity(text: str, duration: float):
    """Helper: Émettre activité STT"""
    monitor = get_neural_monitor()
    if monitor:
        await monitor.emit_neural_activity(
            "stt",
            intensity=1.2,
            metadata={"text": text[:50], "duration": duration}
        )


async def emit_llm_activity(prompt: str, response: str, duration: float):
    """Helper: Émettre activité LLM"""
    monitor = get_neural_monitor()
    if monitor:
        await monitor.emit_neural_activity(
            "llm",
            intensity=1.5,
            metadata={
                "prompt_length": len(prompt),
                "response_length": len(response),
                "duration": duration
            }
        )


async def emit_tts_activity(text: str, duration: float):
    """Helper: Émettre activité TTS"""
    monitor = get_neural_monitor()
    if monitor:
        await monitor.emit_voice_activity(
            speaking=True,
            text=text,
            duration=duration
        )
        
        # Attendre la durée de parole
        await asyncio.sleep(duration)
        
        await monitor.emit_voice_activity(speaking=False)


async def emit_dispatch_activity(intent: str, service: str):
    """Helper: Émettre activité dispatch"""
    monitor = get_neural_monitor()
    if monitor:
        await monitor.emit_neural_activity(
            "dispatch",
            intensity=1.0,
            metadata={"intent": intent, "service": service}
        )


# ============================================
# Tests
# ============================================

async def test_neural_monitor():
    """Test du moniteur neural"""
    print("=" * 60)
    print("🧪 Neural Monitor Test")
    print("=" * 60)
    
    # Initialiser
    monitor = init_neural_monitor(enabled=True)
    await monitor.start()
    
    print("✅ Monitor started")
    
    # Simuler des événements
    print("\n📡 Sending test events...")
    
    await monitor.emit_neural_activity("stt", 1.0, {"test": "listening"})
    await asyncio.sleep(0.5)
    
    await monitor.emit_neural_activity("llm", 1.5, {"test": "thinking"})
    await asyncio.sleep(0.5)
    
    await monitor.emit_voice_activity(True, "Bonjour, je suis HOPPER", 2.0)
    await asyncio.sleep(2.5)
    await monitor.emit_voice_activity(False)
    
    await monitor.emit_service_event("stt", "completed", 0.5)
    await monitor.emit_service_event("llm", "completed", 1.2)
    await monitor.emit_service_event("tts", "completed", 2.0)
    
    print(f"\n📊 Stats: {monitor.stats}")
    
    # Nettoyer
    await monitor.stop()
    print("✅ Monitor stopped")


if __name__ == "__main__":
    asyncio.run(test_neural_monitor())
