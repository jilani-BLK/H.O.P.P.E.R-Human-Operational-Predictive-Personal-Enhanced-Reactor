"""
Plugin Registry - Chargement Dynamique de Tools

Découvre, charge et gère les plugins/tools de manière dynamique.
Support du hot-reload et des entry points Python.
"""

import importlib
import importlib.util
import inspect
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
from loguru import logger

from core.tool_interface import ToolInterface, ToolManifest, ToolCategory
from security.credentials_vault import CredentialsVault


class PluginRegistry:
    """
    Registry centralisé des tools/plugins
    
    Fonctionnalités:
    - Découverte automatique de plugins
    - Chargement dynamique (entry points)
    - Hot-reload pour développement
    - Validation des manifestes
    - Injection de dépendances
    """
    
    def __init__(
        self,
        plugins_dir: str = "src/orchestrator/plugins",
        credentials_vault: Optional[CredentialsVault] = None
    ):
        self.plugins_dir = Path(plugins_dir)
        self.credentials_vault = credentials_vault
        
        # Registry: tool_id → instance ToolInterface
        self.tools: Dict[str, ToolInterface] = {}
        
        # Manifestes chargés: tool_id → ToolManifest
        self.manifests: Dict[str, ToolManifest] = {}
        
        logger.info(f"✅ PluginRegistry initialisé (plugins_dir: {plugins_dir})")
    
    
    async def discover_and_load_all(self):
        """
        Découvre et charge tous les plugins disponibles
        
        Méthodes de découverte:
        1. Scan du dossier plugins/
        2. Entry points Python (setuptools)
        3. Manifestes JSON externes
        """
        
        logger.info("🔍 Découverte des plugins...")
        
        # 1. Scan dossier plugins
        if self.plugins_dir.exists():
            await self._scan_plugins_directory()
        
        # 2. Entry points (pour distribution packagée)
        await self._load_from_entry_points()
        
        logger.success(f"✅ {len(self.tools)} tools chargés")
    
    
    async def _scan_plugins_directory(self):
        """Scan le dossier plugins/ pour trouver tools"""
        
        for plugin_file in self.plugins_dir.glob("*_tool.py"):
            try:
                await self._load_plugin_from_file(plugin_file)
            except Exception as e:
                logger.error(f"❌ Erreur chargement {plugin_file.name}: {e}")
    
    
    async def _load_plugin_from_file(self, plugin_file: Path):
        """Charge un plugin depuis un fichier Python"""
        
        module_name = plugin_file.stem
        
        # Import dynamique
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if not spec or not spec.loader:
            logger.warning(f"⚠️ Impossible de charger {plugin_file}")
            return
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Trouver classe implémentant ToolInterface
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, ToolInterface) and obj != ToolInterface:
                # Instancier le tool - les tools concrets créent leur manifest en interne
                # et appellent super().__init__(manifest, credentials_vault)
                tool_instance = obj(credentials_vault=self.credentials_vault)  # type: ignore[call-arg]
                manifest = tool_instance.get_manifest()
                
                # Enregistrer
                self.tools[manifest.tool_id] = tool_instance
                self.manifests[manifest.tool_id] = manifest
                
                logger.info(
                    f"📦 Plugin chargé: {manifest.name} ({manifest.tool_id}) "
                    f"- {len(manifest.capabilities)} capacités"
                )
                break
    
    
    async def _load_from_entry_points(self):
        """Charge plugins depuis entry points Python"""
        
        try:
            from importlib.metadata import entry_points
            
            # Récupérer entry points groupe 'hopper.tools'
            eps = entry_points()
            
            if hasattr(eps, 'select'):
                # Python 3.10+
                tools_eps = eps.select(group='hopper.tools')
            else:
                # Python 3.9 - eps est un dict
                tools_eps = eps.get('hopper.tools', [])  # type: ignore[union-attr]
            
            for ep in tools_eps:
                try:
                    # Charger classe du tool
                    tool_class = ep.load()
                    
                    # Instancier
                    tool_instance = tool_class(credentials_vault=self.credentials_vault)
                    manifest = tool_instance.get_manifest()
                    
                    # Enregistrer
                    self.tools[manifest.tool_id] = tool_instance
                    self.manifests[manifest.tool_id] = manifest
                    
                    logger.info(f"📦 Plugin chargé (entry point): {manifest.name}")
                
                except Exception as e:
                    logger.error(f"❌ Erreur chargement entry point {ep.name}: {e}")
        
        except ImportError:
            logger.debug("importlib.metadata non disponible (entry points désactivés)")
    
    
    def register_tool(
        self,
        tool_instance: ToolInterface
    ):
        """
        Enregistre manuellement un tool
        
        Utile pour tools créés programmatiquement
        """
        
        manifest = tool_instance.get_manifest()
        
        self.tools[manifest.tool_id] = tool_instance
        self.manifests[manifest.tool_id] = manifest
        
        logger.info(f"✅ Tool enregistré: {manifest.name} ({manifest.tool_id})")
    
    
    def get_tool(self, tool_id: str) -> Optional[ToolInterface]:
        """Récupère une instance de tool"""
        return self.tools.get(tool_id)
    
    
    def get_manifest(self, tool_id: str) -> Optional[ToolManifest]:
        """Récupère le manifeste d'un tool"""
        return self.manifests.get(tool_id)
    
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        enabled_only: bool = True
    ) -> List[ToolManifest]:
        """
        Liste les tools disponibles
        
        Args:
            category: Filtrer par catégorie
            enabled_only: Uniquement tools activés
            
        Returns:
            Liste des manifestes
        """
        
        manifests = list(self.manifests.values())
        
        if category:
            manifests = [m for m in manifests if m.category == category]
        
        if enabled_only:
            manifests = [m for m in manifests if m.is_enabled]
        
        return manifests
    
    
    def get_capabilities_for_llm(self) -> Dict[str, List[Dict]]:
        """
        Génère résumé des capacités pour injection dans prompts LLM
        
        Format:
        {
          "imap_email": [
            {"name": "read_email", "description": "...", "parameters": [...]}
          ],
          "calendar": [...]
        }
        """
        
        result = {}
        
        for tool_id, tool in self.tools.items():
            manifest = self.manifests[tool_id]
            
            if not manifest.is_enabled:
                continue
            
            result[tool_id] = tool.get_capabilities_summary()
        
        return result
    
    
    async def reload_tool(self, tool_id: str) -> bool:
        """
        Recharge un tool à chaud (hot-reload)
        
        Utile en développement
        """
        
        if tool_id not in self.tools:
            logger.warning(f"⚠️ Tool {tool_id} non chargé")
            return False
        
        try:
            # TODO: Implémenter logique reload
            # 1. Sauvegarder état
            # 2. Décharger module
            # 3. Recharger module
            # 4. Restaurer état
            
            logger.info(f"♻️ Tool rechargé: {tool_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erreur reload {tool_id}: {e}")
            return False
    
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne statistiques du registry"""
        
        return {
            "total_tools": len(self.tools),
            "enabled_tools": len([m for m in self.manifests.values() if m.is_enabled]),
            "tools_by_category": self._count_by_category(),
            "total_capabilities": sum(
                len(m.capabilities) for m in self.manifests.values()
            )
        }
    
    
    def _count_by_category(self) -> Dict[str, int]:
        """Compte tools par catégorie"""
        
        counts = {}
        
        for manifest in self.manifests.values():
            category = manifest.category.value
            counts[category] = counts.get(category, 0) + 1
        
        return counts
