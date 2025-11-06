"""
Test du système de plugins complet

Valide:
- PluginRegistry discovery
- CredentialsVault
- IMAPEmailTool
- FileSystemTool
"""

import asyncio
import sys
from pathlib import Path

# Ajouter src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestrator"))

from core.plugin_registry import PluginRegistry  # type: ignore[import-not-found]
from security.credentials_vault import CredentialsVault  # type: ignore[import-not-found]
from core.tool_interface import ToolExecutionContext  # type: ignore[import-not-found]


async def main():
    print("=" * 60)
    print("🧪 TEST PLUGIN SYSTEM")
    print("=" * 60)
    print()
    
    # 1. Créer CredentialsVault
    print("1️⃣ Initialisation CredentialsVault...")
    vault = CredentialsVault(master_password="test_password_123")
    print("✅ Vault créé\n")
    
    # 2. Créer PluginRegistry
    print("2️⃣ Initialisation PluginRegistry...")
    registry = PluginRegistry(credentials_vault=vault)
    print("✅ Registry créé\n")
    
    # 3. Découvrir plugins
    print("3️⃣ Découverte des plugins...")
    plugins_dir = Path(__file__).parent.parent / "src" / "orchestrator" / "plugins"
    print(f"   📂 Scan: {plugins_dir}")
    
    loaded_count = await registry.discover_and_load_all()
    print(f"✅ {loaded_count} plugins chargés\n")
    
    # 4. Lister tools
    print("4️⃣ Tools disponibles:")
    manifests = registry.list_tools()
    
    for manifest in manifests:
        print(f"   🔧 {manifest.tool_id}")
        print(f"      Nom: {manifest.name}")
        print(f"      Catégorie: {manifest.category}")
        print(f"      Capacités: {len(manifest.capabilities)}")
        
        for cap in manifest.capabilities[:3]:  # 3 premières
            print(f"         - {cap.name} ({cap.risk_level})")
        print()
    
    # 5. Test FileSystemTool
    print("5️⃣ Test FileSystemTool...")
    
    fs_tool = registry.get_tool("filesystem")
    
    if fs_tool:
        # Connexion
        await fs_tool.connect()
        
        # Test list_directory
        context = ToolExecutionContext(user_id="test_user")
        
        result = await fs_tool.invoke(
            capability_name="list_directory",
            parameters={"path": str(Path.home() / "Documents")},
            context=context
        )
        
        if result.success:
            print(f"✅ list_directory: {result.data['total']} fichiers")
        else:
            print(f"❌ Erreur: {result.error}")
        
        await fs_tool.disconnect()
    
    print()
    
    # 6. Test IMAPEmailTool (connexion seulement, sans credentials réels)
    print("6️⃣ Test IMAPEmailTool (structure)...")
    
    imap_tool = registry.get_tool("imap_email")
    
    if imap_tool:
        print(f"✅ IMAP tool chargé")
        print(f"   Auth: {imap_tool.manifest.auth_method}")
        print(f"   Capacités: {[c.name for c in imap_tool.manifest.capabilities]}")
    else:
        print("⚠️ IMAP tool non trouvé")
    
    print()
    
    # 7. Capacités pour LLM
    print("7️⃣ Capacités formatées pour LLM:")
    llm_caps = registry.get_capabilities_for_llm()
    
    for tool_id, caps in llm_caps.items():
        print(f"   {tool_id}:")
        for cap in caps[:2]:  # 2 premières
            print(f"      - {cap['name']}: {cap['description']}")
    
    print()
    
    # 8. Statistiques
    print("8️⃣ Statistiques:")
    stats = registry.get_statistics()
    
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print()
    print("=" * 60)
    print("✅ Tests terminés")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
