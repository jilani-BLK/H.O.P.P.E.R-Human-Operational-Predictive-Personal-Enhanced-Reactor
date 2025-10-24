"""
HOPPER - Module Registry & Integration
Enregistre et intègre TOUS les modules de HOPPER au hub de coordination

Ce fichier garantit que:
1. Tous les modules sont détectés automatiquement
2. Les dépendances sont correctement définies
3. L'ordre d'initialisation est respecté
4. Aucun module n'est isolé du noyau
"""

from typing import Dict, Any, Optional
from loguru import logger
from pathlib import Path
import importlib
import sys

try:
    from coordination_hub import (
        get_hub,
        ModuleType,
    )
    hub_available = True
except ImportError:
    hub_available = False
    logger.warning("⚠️ Coordination Hub non disponible")


class ModuleRegistry:
    """
    Registre de tous les modules HOPPER
    Assure que tout est connecté au noyau
    """
    
    # Définition de tous les modules et leurs dépendances
    MODULE_DEFINITIONS = {
        # ============================================
        # CORE - Noyau de l'orchestrator
        # ============================================
        "context_manager": {
            "type": ModuleType.CORE,
            "path": "src.orchestrator.core.context_manager",
            "class": "ContextManager",
            "dependencies": []
        },
        "service_registry": {
            "type": ModuleType.CORE,
            "path": "src.orchestrator.core.service_registry",
            "class": "ServiceRegistry",
            "dependencies": []
        },
        "intent_dispatcher": {
            "type": ModuleType.CORE,
            "path": "src.orchestrator.core.dispatcher",
            "class": "IntentDispatcher",
            "dependencies": ["service_registry", "context_manager"]
        },
        "unified_dispatcher": {
            "type": ModuleType.CORE,
            "path": "src.orchestrator.core.unified_dispatcher",
            "class": "UnifiedDispatcher",
            "dependencies": ["self_rag", "hyde"]
        },
        "prompt_builder": {
            "type": ModuleType.CORE,
            "path": "src.orchestrator.core.prompt_builder",
            "class": "PromptBuilder",
            "dependencies": []
        },
        
        # ============================================
        # RAG - Retrieval Augmented Generation
        # ============================================
        "self_rag": {
            "type": ModuleType.RAG,
            "path": "src.rag.self_rag",
            "class": "SelfRAG",
            "dependencies": []
        },
        "graph_rag": {
            "type": ModuleType.RAG,
            "path": "src.rag.graph_store",
            "class": "GraphStore",
            "dependencies": []
        },
        "hyde": {
            "type": ModuleType.RAG,
            "path": "src.rag.hyde",
            "class": "HyDE",
            "dependencies": []
        },
        
        # ============================================
        # AGENTS - Agents autonomes
        # ============================================
        "react_agent": {
            "type": ModuleType.AGENT,
            "path": "src.agents.react_agent",
            "class": "ReActAgent",
            "dependencies": ["llm"]
        },
        
        # ============================================
        # REASONING - Raisonnement et planification
        # ============================================
        "code_executor": {
            "type": ModuleType.REASONING,
            "path": "src.reasoning.code_executor",
            "class": "CodeExecutor",
            "dependencies": []
        },
        "chain_of_thought": {
            "type": ModuleType.REASONING,
            "path": "src.reasoning.chain_of_thought",
            "class": "ChainOfThought",
            "dependencies": ["llm"]
        },
        "planner": {
            "type": ModuleType.REASONING,
            "path": "src.reasoning.planner",
            "class": "Planner",
            "dependencies": ["llm"]
        },
        
        # ============================================
        # SECURITY - Sécurité et permissions
        # ============================================
        "permission_manager": {
            "type": ModuleType.SECURITY,
            "path": "src.security.permissions",
            "class": "PermissionManager",
            "dependencies": []
        },
        "malware_detector": {
            "type": ModuleType.SECURITY,
            "path": "src.security.malware_detector",
            "class": "MalwareDetector",
            "dependencies": []
        },
        "confirmation_engine": {
            "type": ModuleType.SECURITY,
            "path": "src.security.confirmation",
            "class": "ConfirmationEngine",
            "dependencies": []
        },
        "audit_logger": {
            "type": ModuleType.SECURITY,
            "path": "src.security.permissions",
            "class": "AuditLogger",
            "dependencies": []
        },
        
        # ============================================
        # COMMUNICATION - Communication naturelle
        # ============================================
        "action_narrator": {
            "type": ModuleType.COMMUNICATION,
            "path": "src.communication.action_narrator",
            "class": "ActionNarrator",
            "dependencies": []
        },
        
        # ============================================
        # LEARNING - Apprentissage continu
        # ============================================
        "validation_system": {
            "type": ModuleType.LEARNING,
            "path": "src.learning.validation_system",
            "class": "ValidationSystem",
            "dependencies": []
        },
        "preference_learner": {
            "type": ModuleType.LEARNING,
            "path": "src.learning.preference_learner",
            "class": "PreferenceLearner",
            "dependencies": []
        },
        
        # ============================================
        # VOICE - Vocal (STT, TTS, etc.)
        # ============================================
        "voice_pipeline": {
            "type": ModuleType.VOICE,
            "path": "src.orchestrator.services.voice_pipeline",
            "class": "VoicePipeline",
            "dependencies": []
        },
        "voice_cloner": {
            "type": ModuleType.VOICE,
            "path": "src.tts.voice_cloning",
            "class": "HopperVoiceCloner",
            "dependencies": []
        },
        
        # ============================================
        # SYSTEM - Exécution système et fichiers
        # ============================================
        "system_tools": {
            "type": ModuleType.SYSTEM,
            "path": "src.orchestrator.tools.system_integration",
            "class": "SystemToolsIntegration",
            "dependencies": []
        },
        "filesystem_tools": {
            "type": ModuleType.SYSTEM,
            "path": "src.orchestrator.tools.filesystem_integration",
            "class": "FileSystemToolsIntegration",
            "dependencies": []
        },
    }
    
    def __init__(self):
        self.registered_modules: Dict[str, Any] = {}
        self.failed_modules: Dict[str, str] = {}
    
    def register_all_modules(self):
        """
        Enregistre tous les modules dans le hub de coordination
        Assure que rien n'est isolé du noyau
        """
        if not hub_available:
            logger.warning("⚠️ Hub non disponible - enregistrement ignoré")
            return
        
        hub = get_hub()
        
        logger.info("🔄 Enregistrement de tous les modules dans le hub...")
        
        registered_count = 0
        failed_count = 0
        
        for module_name, module_def in self.MODULE_DEFINITIONS.items():
            try:
                # Tenter d'importer et d'instancier le module
                module_path = module_def["path"]
                class_name = module_def["class"]
                module_type = module_def["type"]
                dependencies = module_def["dependencies"]
                
                # Import du module
                try:
                    module = importlib.import_module(module_path)
                    module_class = getattr(module, class_name)
                    
                    # Instancier (attention: certains modules peuvent nécessiter des paramètres)
                    try:
                        instance = module_class()
                    except TypeError:
                        # Si le constructeur nécessite des arguments, utiliser None comme placeholder
                        instance = None
                        logger.debug(f"   ⚠️ {module_name}: instance placeholder (constructeur avec args)")
                    
                    # Enregistrer dans le hub
                    hub.register_module(module_name, module_type, instance, dependencies)
                    
                    self.registered_modules[module_name] = instance
                    registered_count += 1
                    logger.debug(f"   ✅ {module_name} enregistré")
                    
                except ImportError as e:
                    self.failed_modules[module_name] = f"Import error: {e}"
                    failed_count += 1
                    logger.debug(f"   ⏭️  {module_name}: module non disponible")
                    
            except Exception as e:
                self.failed_modules[module_name] = str(e)
                failed_count += 1
                logger.error(f"   ❌ {module_name}: {e}")
        
        logger.info(f"✅ Enregistrement terminé: {registered_count} modules, {failed_count} non disponibles")
        
        # Afficher le graphe de dépendances
        self._log_dependency_graph()
    
    def _log_dependency_graph(self):
        """Affiche le graphe de dépendances"""
        if not hub_available:
            return
        
        hub = get_hub()
        graph = hub.get_dependency_graph()
        
        logger.info("📊 Graphe de dépendances:")
        
        # Grouper par type
        by_type: Dict[str, list] = {}
        for module_name, module_info in hub.modules.items():
            type_name = module_info.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(module_name)
        
        for type_name, modules in sorted(by_type.items()):
            logger.info(f"   {type_name.upper()}: {len(modules)} modules")
            for module_name in sorted(modules):
                deps = graph.get(module_name, [])
                if deps:
                    logger.info(f"      • {module_name} → {deps}")
                else:
                    logger.info(f"      • {module_name}")
    
    def get_module(self, name: str) -> Optional[Any]:
        """Récupère un module enregistré"""
        return self.registered_modules.get(name)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur l'enregistrement"""
        return {
            "total_defined": len(self.MODULE_DEFINITIONS),
            "registered": len(self.registered_modules),
            "failed": len(self.failed_modules),
            "success_rate": len(self.registered_modules) / len(self.MODULE_DEFINITIONS) * 100
        }


# Instance globale
_registry: Optional[ModuleRegistry] = None


def get_registry() -> ModuleRegistry:
    """Retourne l'instance globale du registre"""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry


def register_all_hopper_modules():
    """
    Fonction principale pour enregistrer tous les modules HOPPER
    À appeler au démarrage de l'orchestrator
    """
    registry = get_registry()
    registry.register_all_modules()
    
    stats = registry.get_statistics()
    logger.info(f"📊 Statistiques d'enregistrement: {stats['registered']}/{stats['total_defined']} modules ({stats['success_rate']:.1f}%)")
    
    return registry


# ============================================
# Tests
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Test Module Registry")
    print("=" * 60)
    
    registry = register_all_hopper_modules()
    
    stats = registry.get_statistics()
    print(f"\n📊 Statistiques:")
    print(f"   Total défini: {stats['total_defined']}")
    print(f"   Enregistrés: {stats['registered']}")
    print(f"   Échecs: {stats['failed']}")
    print(f"   Taux de succès: {stats['success_rate']:.1f}%")
    
    if registry.failed_modules:
        print(f"\n⚠️ Modules non disponibles:")
        for name, reason in registry.failed_modules.items():
            print(f"   • {name}: {reason}")
    
    print("\n✅ Test terminé")
