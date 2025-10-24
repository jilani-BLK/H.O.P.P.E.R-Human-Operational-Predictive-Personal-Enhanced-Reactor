"""
HOPPER - Central Coordination Hub
Module central assurant que toutes les fonctions sont coordonnées et reliées au noyau

Ce hub garantit que:
1. Tous les modules peuvent communiquer entre eux via l'orchestrator
2. Les événements sont propagés à tous les composants concernés
3. L'état global est cohérent
4. Le monitoring neural suit toutes les activités
"""

from typing import Dict, Any, Optional, List, Callable
from loguru import logger
from dataclasses import dataclass, field
from enum import Enum
import asyncio


class ModuleType(Enum):
    """Types de modules dans HOPPER"""
    CORE = "core"  # Orchestrator, Dispatcher, ServiceRegistry
    LLM = "llm"  # Moteur LLM, Knowledge Base
    RAG = "rag"  # Self-RAG, GraphRAG, HyDE
    AGENT = "agent"  # ReAct Agent
    REASONING = "reasoning"  # Code Executor, Planner
    SECURITY = "security"  # Permissions, Malware Detector, Audit
    COMMUNICATION = "communication"  # ActionNarrator, Async narrator
    SYSTEM = "system"  # System Executor, File System
    LEARNING = "learning"  # ValidationSystem, PreferenceLearner
    VOICE = "voice"  # STT, TTS, Wake Word, Voice Cloning
    AUTH = "auth"  # Voice recognition, Face recognition
    MONITORING = "monitoring"  # Neural Monitor, Metrics
    CONNECTORS = "connectors"  # Local System, Email, etc.


@dataclass
class ModuleInfo:
    """Informations sur un module"""
    name: str
    type: ModuleType
    instance: Any
    dependencies: List[str] = field(default_factory=list)
    health: str = "unknown"  # healthy, degraded, unhealthy
    last_check: Optional[float] = None


class CoordinationHub:
    """
    Hub central de coordination de HOPPER
    
    Responsabilités:
    - Enregistrer tous les modules
    - Vérifier les dépendances
    - Propager les événements
    - Maintenir la cohérence
    - Monitorer la santé globale
    """
    
    def __init__(self):
        self.modules: Dict[str, ModuleInfo] = {}
        self.event_listeners: Dict[str, List[Callable]] = {}
        self._initialized = False
        
        logger.info("🎯 CoordinationHub initialisé")
    
    def register_module(
        self,
        name: str,
        module_type: ModuleType,
        instance: Any,
        dependencies: Optional[List[str]] = None
    ) -> bool:
        """
        Enregistre un module dans le hub
        
        Args:
            name: Nom unique du module
            module_type: Type de module
            instance: Instance du module
            dependencies: Liste des modules dont il dépend
        
        Returns:
            True si enregistré avec succès
        """
        if name in self.modules:
            logger.warning(f"⚠️ Module '{name}' déjà enregistré - mise à jour")
        
        self.modules[name] = ModuleInfo(
            name=name,
            type=module_type,
            instance=instance,
            dependencies=dependencies or []
        )
        
        logger.info(f"✅ Module '{name}' ({module_type.value}) enregistré")
        
        # Vérifier les dépendances
        self._check_dependencies(name)
        
        return True
    
    def _check_dependencies(self, module_name: str):
        """Vérifie que toutes les dépendances sont satisfaites"""
        module = self.modules.get(module_name)
        if not module:
            return
        
        missing = []
        for dep in module.dependencies:
            if dep not in self.modules:
                missing.append(dep)
        
        if missing:
            logger.warning(
                f"⚠️ Module '{module_name}' manque dépendances: {missing}"
            )
        else:
            logger.debug(f"✅ Toutes les dépendances de '{module_name}' satisfaites")
    
    def get_module(self, name: str) -> Optional[Any]:
        """Récupère l'instance d'un module"""
        module = self.modules.get(name)
        return module.instance if module else None
    
    def get_modules_by_type(self, module_type: ModuleType) -> List[Any]:
        """Récupère tous les modules d'un type"""
        return [
            m.instance for m in self.modules.values()
            if m.type == module_type
        ]
    
    async def emit_event(
        self,
        event_name: str,
        data: Dict[str, Any],
        target_modules: Optional[List[str]] = None
    ):
        """
        Émet un événement à tous les modules concernés
        
        Args:
            event_name: Nom de l'événement
            data: Données de l'événement
            target_modules: Modules cibles (None = tous)
        """
        logger.debug(f"📡 Émission événement: {event_name}")
        
        # Notifier les listeners
        if event_name in self.event_listeners:
            for listener in self.event_listeners[event_name]:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(data)
                    else:
                        listener(data)
                except Exception as e:
                    logger.error(f"❌ Erreur listener {event_name}: {e}")
        
        # Notifier les modules ciblés
        targets = target_modules if target_modules else list(self.modules.keys())
        
        for module_name in targets:
            module = self.modules.get(module_name)
            if not module:
                continue
            
            # Si le module a une méthode on_event
            if hasattr(module.instance, 'on_event'):
                try:
                    if asyncio.iscoroutinefunction(module.instance.on_event):
                        await module.instance.on_event(event_name, data)
                    else:
                        module.instance.on_event(event_name, data)
                except Exception as e:
                    logger.error(f"❌ Erreur module {module_name}.on_event: {e}")
    
    def on(self, event_name: str, listener: Callable):
        """Enregistre un listener d'événement"""
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
        
        self.event_listeners[event_name].append(listener)
        logger.debug(f"✅ Listener enregistré pour '{event_name}'")
    
    async def check_all_health(self) -> Dict[str, str]:
        """Vérifie la santé de tous les modules"""
        health_status = {}
        
        for name, module in self.modules.items():
            if hasattr(module.instance, 'health_check'):
                try:
                    if asyncio.iscoroutinefunction(module.instance.health_check):
                        healthy = await module.instance.health_check()
                    else:
                        healthy = module.instance.health_check()
                    
                    module.health = "healthy" if healthy else "unhealthy"
                except Exception as e:
                    logger.error(f"❌ Health check failed for {name}: {e}")
                    module.health = "unhealthy"
            else:
                # Pas de health check = assume healthy si instance existe
                module.health = "healthy"
            
            health_status[name] = module.health
        
        return health_status
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Retourne le graphe de dépendances"""
        return {
            name: module.dependencies
            for name, module in self.modules.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le hub"""
        modules_by_type = {}
        for module_type in ModuleType:
            count = len([m for m in self.modules.values() if m.type == module_type])
            if count > 0:
                modules_by_type[module_type.value] = count
        
        health_counts = {}
        for module in self.modules.values():
            health_counts[module.health] = health_counts.get(module.health, 0) + 1
        
        return {
            "total_modules": len(self.modules),
            "modules_by_type": modules_by_type,
            "health_status": health_counts,
            "initialized": self._initialized
        }
    
    async def initialize_all(self):
        """Initialise tous les modules dans l'ordre des dépendances"""
        logger.info("🚀 Initialisation de tous les modules...")
        
        # Tri topologique pour respecter les dépendances
        initialized = set()
        remaining = set(self.modules.keys())
        
        while remaining:
            # Trouver modules sans dépendances non satisfaites
            ready = [
                name for name in remaining
                if all(dep in initialized for dep in self.modules[name].dependencies)
            ]
            
            if not ready:
                logger.error("❌ Dépendances circulaires détectées!")
                break
            
            # Initialiser les modules prêts
            for name in ready:
                module = self.modules[name]
                
                if hasattr(module.instance, 'initialize'):
                    try:
                        logger.info(f"   🔧 Initialisation {name}...")
                        if asyncio.iscoroutinefunction(module.instance.initialize):
                            await module.instance.initialize()
                        else:
                            module.instance.initialize()
                        
                        initialized.add(name)
                        logger.success(f"   ✅ {name} initialisé")
                    except Exception as e:
                        logger.error(f"   ❌ Erreur initialisation {name}: {e}")
                else:
                    # Pas de méthode initialize = déjà initialisé
                    initialized.add(name)
                
                remaining.discard(name)
        
        self._initialized = True
        logger.success(f"✅ {len(initialized)} modules initialisés")
    
    async def shutdown_all(self):
        """Arrête tous les modules proprement"""
        logger.info("🛑 Arrêt de tous les modules...")
        
        for name, module in reversed(list(self.modules.items())):
            if hasattr(module.instance, 'shutdown'):
                try:
                    logger.info(f"   🛑 Arrêt {name}...")
                    if asyncio.iscoroutinefunction(module.instance.shutdown):
                        await module.instance.shutdown()
                    else:
                        module.instance.shutdown()
                    
                    logger.success(f"   ✅ {name} arrêté")
                except Exception as e:
                    logger.error(f"   ❌ Erreur arrêt {name}: {e}")
        
        self._initialized = False
        logger.success("✅ Tous les modules arrêtés")


# Instance globale du hub
_hub: Optional[CoordinationHub] = None


def get_hub() -> CoordinationHub:
    """Retourne l'instance globale du hub"""
    global _hub
    if _hub is None:
        _hub = CoordinationHub()
    return _hub


def initialize_hub() -> CoordinationHub:
    """Initialise et retourne le hub"""
    global _hub
    _hub = CoordinationHub()
    return _hub


# ============================================
# Helpers pour enregistrement rapide
# ============================================

def register_core_module(name: str, instance: Any, dependencies: Optional[List[str]] = None):
    """Helper pour enregistrer un module core"""
    hub = get_hub()
    hub.register_module(name, ModuleType.CORE, instance, dependencies)


def register_llm_module(name: str, instance: Any, dependencies: Optional[List[str]] = None):
    """Helper pour enregistrer un module LLM"""
    hub = get_hub()
    hub.register_module(name, ModuleType.LLM, instance, dependencies)


def register_rag_module(name: str, instance: Any, dependencies: Optional[List[str]] = None):
    """Helper pour enregistrer un module RAG"""
    hub = get_hub()
    hub.register_module(name, ModuleType.RAG, instance, dependencies)


def register_security_module(name: str, instance: Any, dependencies: Optional[List[str]] = None):
    """Helper pour enregistrer un module Security"""
    hub = get_hub()
    hub.register_module(name, ModuleType.SECURITY, instance, dependencies)


def register_communication_module(name: str, instance: Any, dependencies: Optional[List[str]] = None):
    """Helper pour enregistrer un module Communication"""
    hub = get_hub()
    hub.register_module(name, ModuleType.COMMUNICATION, instance, dependencies)


# ============================================
# Tests
# ============================================

async def test_coordination_hub():
    """Test du hub de coordination"""
    print("=" * 60)
    print("🧪 Test Coordination Hub")
    print("=" * 60)
    
    hub = initialize_hub()
    
    # Simuler des modules
    class MockModule:
        def __init__(self, name):
            self.name = name
            self.events_received = []
        
        def on_event(self, event_name, data):
            self.events_received.append((event_name, data))
            print(f"   📬 {self.name} received: {event_name}")
        
        def health_check(self):
            return True
    
    # Enregistrer modules
    print("\n1. Enregistrement modules...")
    dispatcher = MockModule("Dispatcher")
    llm = MockModule("LLM")
    rag = MockModule("RAG")
    security = MockModule("Security")
    
    register_core_module("dispatcher", dispatcher)
    register_llm_module("llm", llm, ["dispatcher"])
    register_rag_module("rag", rag, ["llm"])
    register_security_module("security", security, ["dispatcher"])
    
    # Stats
    print("\n2. Statistiques:")
    stats = hub.get_statistics()
    print(f"   Total modules: {stats['total_modules']}")
    print(f"   Par type: {stats['modules_by_type']}")
    
    # Health check
    print("\n3. Health check...")
    health = await hub.check_all_health()
    print(f"   Status: {health}")
    
    # Événements
    print("\n4. Test événements...")
    await hub.emit_event("command_received", {"text": "test"})
    await hub.emit_event("llm_response", {"response": "ok"})
    
    print(f"\n   Events dispatcher: {len(dispatcher.events_received)}")
    print(f"   Events llm: {len(llm.events_received)}")
    
    # Graphe dépendances
    print("\n5. Graphe de dépendances:")
    graph = hub.get_dependency_graph()
    for module, deps in graph.items():
        print(f"   {module} → {deps if deps else 'none'}")
    
    print("\n✅ Tests terminés")


if __name__ == "__main__":
    asyncio.run(test_coordination_hub())
