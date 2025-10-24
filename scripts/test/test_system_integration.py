#!/usr/bin/env python3
"""
Test de l'intégration System Tools avec le LLM
Envoie des commandes en langage naturel et vérifie que les outils s'exécutent
"""

import asyncio
import httpx
from loguru import logger

ORCHESTRATOR_URL = "http://localhost:5050"
CONNECTORS_URL = "http://localhost:5006"


async def test_system_tools():
    """Tester l'intégration des outils système"""
    
    test_cases = [
        # Applications
        {
            "query": "Peux-tu ouvrir TextEdit?",
            "expected_tool": "open_app"
        },
        {
            "query": "Liste toutes mes applications installées",
            "expected_tool": "list_apps"
        },
        
        # Fichiers
        {
            "query": "Montre-moi le contenu du fichier README.md",
            "expected_tool": "read_file"
        },
        {
            "query": "Cherche tous les fichiers Python dans src/",
            "expected_tool": "find_files"
        },
        
        # Système
        {
            "query": "Donne-moi les informations système",
            "expected_tool": "get_system_info"
        },
        {
            "query": "Exécute la commande echo 'Hello from HOPPER'",
            "expected_tool": "execute_script"
        }
    ]
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Test d'intégration System Tools + LLM                    ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # Vérifier que les services sont up
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # Check Orchestrator
            resp = await client.get(f"{ORCHESTRATOR_URL}/health")
            if resp.status_code != 200:
                print("❌ Orchestrator non disponible (port 5050)")
                print("   Lancez: cd src/orchestrator && python main.py")
                return
            print("✅ Orchestrator OK")
            
            # Check Connectors
            resp = await client.get(f"{CONNECTORS_URL}/health")
            if resp.status_code != 200:
                print("❌ Connectors Service non disponible (port 5006)")
                print("   Lancez: cd src/connectors && python server.py")
                return
            print("✅ Connectors Service OK\n")
        
        except Exception as e:
            print(f"❌ Erreur connexion services: {e}")
            return
    
    # Exécuter tests
    passed = 0
    failed = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test in enumerate(test_cases, 1):
            query = test["query"]
            expected = test["expected_tool"]
            
            print(f"\n{'='*60}")
            print(f"Test {i}/{len(test_cases)}: {query}")
            print(f"Outil attendu: {expected}")
            print(f"{'='*60}")
            
            try:
                # Envoyer requête
                resp = await client.post(
                    f"{ORCHESTRATOR_URL}/query",
                    json={"text": query, "user_id": "test_user"}
                )
                
                if resp.status_code != 200:
                    print(f"❌ Erreur HTTP {resp.status_code}")
                    failed += 1
                    continue
                
                result = resp.json()
                
                # Vérifier si outil exécuté
                tools_executed = result.get("tools_executed", [])
                actions = result.get("actions", [])
                message = result.get("message", "")
                
                print(f"\n📝 Réponse HOPPER:")
                print(f"{message[:200]}...")
                
                print(f"\n🔧 Outils exécutés: {len(tools_executed)}")
                for tool in tools_executed:
                    print(f"   - {tool.get('action')}")
                
                # Vérifier si l'outil attendu a été exécuté
                tool_found = any(
                    tool.get("action") == expected 
                    for tool in tools_executed
                )
                
                if tool_found:
                    print(f"✅ Test RÉUSSI - Outil {expected} exécuté")
                    passed += 1
                else:
                    print(f"❌ Test ÉCHOUÉ - Outil {expected} non exécuté")
                    print(f"   Outils détectés: {[t.get('action') for t in tools_executed]}")
                    failed += 1
            
            except Exception as e:
                print(f"❌ Erreur: {e}")
                failed += 1
            
            await asyncio.sleep(1)  # Pause entre tests
    
    # Résumé
    print(f"\n\n{'='*60}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*60}")
    print(f"✅ Réussis: {passed}/{len(test_cases)}")
    print(f"❌ Échoués: {failed}/{len(test_cases)}")
    print(f"{'='*60}\n")
    
    if passed == len(test_cases):
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
    else:
        print("⚠️  Certains tests ont échoué - vérifiez les logs")


async def test_direct_detection():
    """Tester la détection sans passer par l'orchestrator"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  Test de détection directe (sans orchestrator)            ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    from src.orchestrator.tools.system_integration import system_tools
    
    test_phrases = [
        ("Bien sûr, je vais ouvrir TextEdit", "ouvre TextEdit", "open_app"),
        ("Je vais lister vos applications", "liste applications", "list_apps"),
        ("Voici le fichier README", "lis README.md", "read_file"),
        ("Voici les infos système", "infos système", "get_system_info")
    ]
    
    for llm_response, user_query, expected_action in test_phrases:
        print(f"\nLLM: '{llm_response}'")
        print(f"User: '{user_query}'")
        
        result = await system_tools.detect_and_execute(llm_response, user_query)
        
        if result:
            detected_action = result.get("action")
            print(f"✅ Détecté: {detected_action}")
            if detected_action == expected_action:
                print(f"✅ CORRECT - Attendu: {expected_action}")
            else:
                print(f"❌ INCORRECT - Attendu: {expected_action}, Obtenu: {detected_action}")
        else:
            print(f"❌ Aucune action détectée (attendu: {expected_action})")


if __name__ == "__main__":
    import sys
    
    if "--direct" in sys.argv:
        asyncio.run(test_direct_detection())
    else:
        asyncio.run(test_system_tools())
