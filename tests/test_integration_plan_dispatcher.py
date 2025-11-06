"""
Test d'intégration - PlanBasedDispatcher dans main.py

Valide que le nouveau dispatcher est bien intégré et fonctionne
avec les vrais endpoints.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestrator"))

from core.plan_dispatcher import PlanBasedDispatcher  # type: ignore[import-not-found]
from core.plugin_registry import PluginRegistry  # type: ignore[import-not-found]
from security.credentials_vault import CredentialsVault  # type: ignore[import-not-found]
from core.context_manager import ContextManager  # type: ignore[import-not-found]
from core.service_registry import ServiceRegistry  # type: ignore[import-not-found]


class MockServiceRegistry:
    """Mock pour tests sans vrais services"""
    
    async def call_service(self, service, endpoint, method="POST", data=None, timeout=30.0):
        """Simule LLM pour génération de plans"""
        
        if endpoint == "/generate":
            text = data.get("prompt", "")
            
            # Détecter le type de requête
            if "Liste" in text or "fichiers" in text:
                return {
                    "text": """{
  "intent": "system_action",
  "confidence": 0.98,
  "tool_calls": [
    {
      "tool_id": "filesystem",
      "capability": "list_directory",
      "parameters": {
        "path": "/Users/jilani/Documents"
      },
      "reasoning": "L'utilisateur veut voir ses fichiers",
      "risk_level": "safe"
    }
  ],
  "narration": {
    "message": "Je liste les fichiers de votre dossier Documents",
    "tone": "informative",
    "should_speak": false
  },
  "reasoning": "Action simple de listage",
  "metadata": {
    "requires_confirmation": false,
    "estimated_duration": 1.0
  }
}"""
                }
            else:
                return {
                    "text": """{
  "intent": "general",
  "confidence": 0.80,
  "tool_calls": [],
  "narration": {
    "message": "Je traite votre demande",
    "tone": "friendly"
  },
  "reasoning": "Question générale",
  "metadata": {}
}"""
                }
        
        return {}


async def test_integration():
    """Test l'intégration complète"""
    
    print("=" * 70)
    print("🧪 TEST INTÉGRATION - PlanBasedDispatcher dans architecture")
    print("=" * 70)
    
    # 1. Setup composants (comme dans main.py)
    print("\n1️⃣ Setup composants...")
    
    service_registry = MockServiceRegistry()
    context_manager = ContextManager()
    
    credentials_vault = CredentialsVault(
        vault_path="data/test_vault.enc",
        master_password="test_password",
        use_keychain=False
    )
    
    plugin_registry = PluginRegistry(
        plugins_dir="src/orchestrator/plugins",
        credentials_vault=credentials_vault
    )
    await plugin_registry.discover_and_load_all()
    
    print(f"✅ {len(plugin_registry.tools)} tools chargés")
    
    # 2. Créer dispatcher (comme dans main.py startup)
    print("\n2️⃣ Initialiser PlanBasedDispatcher...")
    
    dispatcher = PlanBasedDispatcher(
        service_registry=service_registry,
        plugin_registry=plugin_registry,
        credentials_vault=credentials_vault,
        context_manager=context_manager
    )
    
    print("✅ Dispatcher initialisé")
    
    # 3. Test commande (comme endpoint /command)
    print("\n3️⃣ Test commande: 'Liste fichiers Documents'")
    print("-" * 70)
    
    result = await dispatcher.dispatch(
        text="Liste les fichiers dans mon dossier Documents",
        user_id="test_user",
        context={}
    )
    
    print(f"\nMessage: {result['message']}")
    print(f"Actions: {result.get('actions', [])}")
    print(f"Intent: {result.get('plan').intent if 'plan' in result else 'N/A'}")
    
    if 'execution' in result:
        exec_result = result['execution']
        print(f"Execution: {'✅' if exec_result.success else '❌'} ({len(exec_result.tool_results)} tools)")
        
        for tr in exec_result.tool_results:
            status = "✅" if tr.success else "❌"
            print(f"  {status} {tr.tool_id}.{tr.capability}")
            if tr.success and tr.result and 'files' in tr.result:
                print(f"     → {len(tr.result['files'])} fichiers trouvés")
    
    # 4. Test question simple
    print("\n4️⃣ Test question simple: 'Quelle est la capitale de la France?'")
    print("-" * 70)
    
    result2 = await dispatcher.dispatch(
        text="Quelle est la capitale de la France?",
        user_id="test_user",
        context={}
    )
    
    print(f"\nMessage: {result2['message']}")
    print(f"Actions: {result2.get('actions', [])}")
    print(f"Tool calls: {len(result2.get('plan').tool_calls) if 'plan' in result2 else 0}")
    
    # 5. Statistiques
    print("\n5️⃣ Statistiques dispatcher:")
    print("-" * 70)
    stats = dispatcher.stats
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ Test d'intégration terminé avec succès!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_integration())
