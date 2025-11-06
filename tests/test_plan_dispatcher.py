"""
Test PlanBasedDispatcher avec PluginRegistry

Valide:
- Génération de plan JSON via LLM
- Validation tools/capabilities
- Exécution via PluginRegistry
- Formatage réponse
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
    """Mock pour tests sans vrai LLM"""
    
    async def call_service(self, service, endpoint, method="GET", data=None, timeout=10):
        """Simule appel LLM avec plan JSON"""
        
        if endpoint == "/generate":
            # Simuler génération plan
            user_query = data.get("prompt", "")
            
            if "liste" in user_query.lower() and "documents" in user_query.lower():
                # Plan pour "Liste fichiers dans Documents"
                return {
                    "text": '''```json
{
  "intent": "system_action",
  "confidence": 0.98,
  "tool_calls": [
    {
      "tool_id": "filesystem",
      "capability": "list_directory",
      "parameters": {"path": "/Users/jilani/Documents"},
      "reasoning": "Lister le contenu du dossier Documents",
      "risk_level": "safe",
      "requires_confirmation": false
    }
  ],
  "narration": {
    "message": "Je liste les fichiers de votre dossier Documents",
    "tone": "neutral",
    "should_speak": false,
    "urgency": "normal"
  },
  "reasoning": "Commande simple de listing de fichiers",
  "estimated_duration_seconds": 1
}
```'''
                }
            else:
                # Plan générique
                return {
                    "text": '''```json
{
  "intent": "general",
  "confidence": 0.8,
  "tool_calls": [],
  "narration": {
    "message": "Je traite votre demande",
    "tone": "neutral",
    "should_speak": false,
    "urgency": "normal"
  },
  "reasoning": "Requête générale"
}
```'''
                }
        
        return {}


async def main():
    print("=" * 70)
    print("🧪 TEST PLAN-BASED DISPATCHER")
    print("=" * 70)
    print()
    
    # 1. Setup
    print("1️⃣ Setup composants...")
    
    vault = CredentialsVault(master_password="test_pass")
    registry = PluginRegistry(credentials_vault=vault)
    await registry.discover_and_load_all()
    
    context_manager = ContextManager()
    service_registry = MockServiceRegistry()
    
    dispatcher = PlanBasedDispatcher(
        service_registry=service_registry,
        plugin_registry=registry,
        credentials_vault=vault,
        context_manager=context_manager
    )
    
    print(f"✅ {len(registry.tools)} tools chargés")
    print()
    
    # 2. Test commande filesystem
    print("2️⃣ Test: 'Liste fichiers dans Documents'")
    print("-" * 70)
    
    result = await dispatcher.dispatch(
        text="Liste les fichiers dans mon dossier Documents",
        user_id="test_user",
        context={}
    )
    
    print(f"Message: {result['message']}")
    print(f"Actions: {result['actions']}")
    
    if result.get("data") and result["data"].get("plan"):
        plan = result["data"]["plan"]
        print(f"Intent: {plan['intent']}")
        print(f"Tool calls: {len(plan.get('tool_calls', []))}")
        
        if plan.get("tool_calls"):
            for call in plan["tool_calls"]:
                print(f"  - {call['tool_id']}.{call['capability']}")
    
    if result.get("data") and result["data"].get("execution"):
        exec_data = result["data"]["execution"]
        print(f"Execution: {'✅ Success' if exec_data.get('success') else '❌ Failed'}")
        print(f"Time: {exec_data.get('time', 0):.3f}s")
        
        if exec_data.get("results"):
            for r in exec_data["results"]:
                status = "✅" if r.get("success") else "❌"
                print(f"  {status} {r.get('tool_id')}.{r.get('capability')}")
                
                if r.get("data") and "total" in r["data"]:
                    print(f"     → {r['data']['total']} éléments")
    
    print()
    
    # 3. Test question simple (sans tools)
    print("3️⃣ Test: 'Quelle est la capitale de la France?'")
    print("-" * 70)
    
    result2 = await dispatcher.dispatch(
        text="Quelle est la capitale de la France?",
        user_id="test_user",
        context={}
    )
    
    print(f"Message: {result2['message']}")
    print(f"Actions: {result2['actions']}")
    
    if result2.get("data") and result2["data"].get("plan"):
        plan2 = result2["data"]["plan"]
        print(f"Intent: {plan2['intent']}")
        print(f"Tool calls: {len(plan2.get('tool_calls', []))}")
    
    print()
    
    # 4. Stats
    print("4️⃣ Statistiques du dispatcher:")
    print("-" * 70)
    stats = dispatcher.stats
    
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()
    print("=" * 70)
    print("✅ Tests terminés")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
