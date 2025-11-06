"""
System Monitor - Surveillance Continue des Ressources

Publie des PerceptionEvent sur le PerceptionBus lors de
dépassements de seuils (CPU, RAM, disque, réseau).
"""

import asyncio
import psutil
from datetime import datetime
from loguru import logger
from typing import Optional

from core.models import PerceptionEvent


class SystemMonitor:
    """
    Moniteur système qui surveille ressources et publie événements
    """
    
    def __init__(
        self,
        perception_bus,
        check_interval: int = 30,  # Secondes entre checks
        cpu_threshold: float = 80.0,  # %
        memory_threshold: float = 85.0,  # %
        disk_threshold: float = 90.0  # %
    ):
        self.perception_bus = perception_bus
        self.check_interval = check_interval
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        
        # État précédent pour détecter changements
        self._prev_alerts = set()
        
        logger.info(f"✅ SystemMonitor initialisé (intervalle: {check_interval}s)")
    
    
    async def start(self):
        """Démarre la surveillance continue"""
        
        logger.info("🔍 Démarrage surveillance système...")
        
        while True:
            try:
                await self._check_resources()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("🛑 SystemMonitor arrêté")
                break
            except Exception as e:
                logger.error(f"Erreur SystemMonitor: {e}")
                await asyncio.sleep(self.check_interval)
    
    
    async def _check_resources(self):
        """Vérifie ressources et publie événements si seuils dépassés"""
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.cpu_threshold:
            await self._publish_alert(
                "cpu_high",
                {
                    "cpu_percent": cpu_percent,
                    "threshold": self.cpu_threshold,
                    "processes": self._get_top_processes_cpu()
                },
                priority=7 if cpu_percent > 90 else 5
            )
        
        # RAM
        memory = psutil.virtual_memory()
        if memory.percent > self.memory_threshold:
            await self._publish_alert(
                "memory_high",
                {
                    "memory_percent": memory.percent,
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "threshold": self.memory_threshold
                },
                priority=7 if memory.percent > 95 else 5
            )
        
        # Disque
        disk = psutil.disk_usage('/')
        if disk.percent > self.disk_threshold:
            await self._publish_alert(
                "disk_full",
                {
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                    "disk_total_gb": round(disk.total / (1024**3), 2),
                    "threshold": self.disk_threshold
                },
                priority=8 if disk.percent > 95 else 6
            )
    
    
    async def _publish_alert(
        self,
        event_type: str,
        data: dict,
        priority: int
    ):
        """Publie une alerte sur le PerceptionBus"""
        
        alert_key = f"system_monitor:{event_type}"
        
        # Éviter spam: publier seulement si nouvelle alerte
        if alert_key in self._prev_alerts:
            return
        
        self._prev_alerts.add(alert_key)
        
        event = PerceptionEvent(
            source="system_monitor",
            event_type=event_type,
            data=data,
            priority=priority,
            timestamp=datetime.now(),
            requires_immediate_response=priority >= 8
        )
        
        await self.perception_bus.publish(event)
        
        logger.debug(f"📊 Alerte publiée: {event_type} (priorité {priority})")
    
    
    def _get_top_processes_cpu(self, limit: int = 3) -> list:
        """Récupère les processus les plus gourmands en CPU"""
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append({
                        "name": proc.info['name'],
                        "cpu_percent": proc.info['cpu_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Trier par CPU
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
        
        except Exception as e:
            logger.error(f"Erreur récupération processes: {e}")
            return []
