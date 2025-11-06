"""
Test PlanBasedDispatcher avec vraie LLM Ollama

Valide la génération de plans JSON via Mistral/Llama
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestrator"))

from core.plan_dispatcher import PlanBasedDispatcher
from core.plugin_registry import PluginRegistry
from security.credentials_vault import CredentialsVault
from core.context_manager import ContextManager
from core.service_registry import ServiceRegistry


async def test_real_llm():
    """Test avec vraie LLM"""
    
    print("=" * 70)
    print("🧪 TEST PLAN GENERATION - VRAIE LLM OLLAMA")
    print("=" * 70)
    print()
    
    # 1. Setup composants
    print("1️⃣ Setup composants...")
    
    credentials_vault = CredentialsVault(
        vault_path="data/vault_test.enc",
        master_password="test_password"
    )
    
    plugin_registry = PluginRegistry(
        plugins_dir="src/orchestrator/plugins",
        credentials_vault=credentials_vault
    )
    await plugin_registry.discover_and_load_all()
    print(f"✅ {len(plugin_registry.tools)} tools chargés")
    
    # ServiceRegistry qui pointe vers vraie LLM
    service_registry = ServiceRegistry()
    await service_registry.register_services()
    # Override avec URL locale pour test
    service_registry.services["llm"] = "http://localhost:5001"
    print(f"✅ ServiceRegistry initialisé (LLM: {service_registry.services['llm']})")
    
    context_manager = ContextManager()
    
    dispatcher = PlanBasedDispatcher(
        service_registry=service_registry,
        plugin_registry=plugin_registry,
        credentials_vault=credentials_vault,
        context_manager=context_manager
    )
    print("✅ Dispatcher avec vraie LLM initialisé")
    print()
    
    # 2. Test 1: Question simple
    print("2️⃣ Test: 'Quelle est la capitale de la France?'")
    print("-" * 70)
    
    result1 = await dispatcher.dispatch(
        text="Quelle est la capitale de la France?",
        user_id="test_user",
        context={}
    )
    
    print(f"Message: {result1.get('message')}")
    print(f"Intent: {result1.get('plan', {}).get('intent') if result1.get('plan') else 'N/A'}")
    print(f"Tool calls: {len(result1.get('plan', {}).get('tool_calls', [])) if result1.get('plan') else 0}")
    
    if result1.get('plan'):
        plan = result1['plan']
        print(f"Confidence: {plan.confidence}")
        print(f"Reasoning: {plan.reasoning[:100]}...")
        for i, call in enumerate(plan.tool_calls):
            print(f"  [{i+1}] {call.tool_id}.{call.capability}")
            print(f"      Params: {call.parameters}")
            print(f"      Risk: {call.risk_level}")
    
    print()
    
    # 3. Test 2: Commande avec tool
    print()
    print("3️⃣ Test: 'Combien de fichiers y a-t-il dans Downloads?'")
    print("-" * 70)
    
    result2 = await dispatcher.dispatch(
        text="Combien de fichiers y a-t-il dans mon dossier Downloads?",
        user_id="test_user",
        context={}
    )
    
    print(f"Message: {result2.get('message')}")
    print(f"Intent: {result2.get('plan', {}).get('intent') if result2.get('plan') else 'N/A'}")
    print(f"Tool calls: {len(result2.get('plan', {}).get('tool_calls', [])) if result2.get('plan') else 0}")
    
    if result2.get('plan'):
        plan = result2['plan']
        print(f"Confidence: {plan.confidence}")
        print(f"Narration: {plan.narration.message}")
    
    print()
    
    # 4. Test 3: Commande email (skip pour l'instant - nécessite config)
    # print("4️⃣ Test: 'Lis mes derniers emails'")
    # print("-" * 70)
    # ...
    
    # 5. Statistiques
    print("5️⃣ Statistiques dispatcher:")
    print("-" * 70)
    stats = dispatcher.stats
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()
    print("=" * 70)
    print("✅ Tests avec vraie LLM terminés!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_real_llm())
