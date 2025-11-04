#!/usr/bin/env python3
"""
HOPPER - Validation Phase 2
Tests conversationnels complets sans dépendances externes
"""

import requests
import time
from typing import Dict, List


ORCHESTRATOR_URL = "http://localhost:5050"


class TestCase:
    """Cas de test simple"""
    def __init__(self, name, command, expected_type, keyword="", max_latency=5000):
        self.name = name
        self.command = command
        self.expected_type = expected_type
        self.keyword = keyword
        self.max_latency = max_latency


# 20 tests pour Phase 2
TESTS = [
    # Conversations (12 tests)
    TestCase("Présentation", "Qui es-tu ?", "conversation", "HOPPER"),
    TestCase("Capacités", "Que peux-tu faire ?", "conversation", "aide"),
    TestCase("Salutation", "Bonjour !", "conversation", "bonjour"),
    TestCase("État", "Comment vas-tu ?", "conversation", "bien"),
    TestCase("LLM", "C'est quoi un LLM ?", "conversation", "langage"),
    TestCase("Mode local", "Tu fonctionnes sans Internet ?", "conversation", "local"),
    TestCase("Remerciement", "Merci", "conversation", "plaisir"),
    TestCase("Modèle", "Quel modèle utilises-tu ?", "conversation", "llama"),
    TestCase("Question fichiers", "À quoi servent les fichiers ?", "conversation", "fichier"),
    TestCase("Capacités système", "Quelles commandes peux-tu faire ?", "conversation", "commande"),
    TestCase("Français", "Parles-tu français ?", "conversation", "français"),
    TestCase("Philosophique", "Quelle est ta raison d'être ?", "conversation", "assist"),
    
    # Système (8 tests)
    TestCase("Liste fichiers", "liste les fichiers du dossier /tmp", "system", "", 1000),
    TestCase("Création fichier", "crée un fichier test_phase2.txt", "system", "", 1000),
    TestCase("Date", "donne moi la date", "system", "", 1000),
    TestCase("Affichage", "affiche les fichiers", "system", "", 1000),
    TestCase("Montre", "montre moi le contenu de /tmp", "system", "", 1000),
    TestCase("Ouvre Calculator", "ouvre l'application Calculator", "system", "", 1000),
    TestCase("Voir dossier", "voir le dossier /tmp", "system", "", 1000),
    TestCase("Liste simple", "ls /tmp", "system", "", 1000),
]


def run_test(test: TestCase) -> Dict:
    """Exécute un test"""
    start = time.time()
    
    try:
        resp = requests.post(
            f"{ORCHESTRATOR_URL}/api/v1/command",
            json={"command": test.command, "conversation_history": []},
            timeout=30
        )
        
        latency = int((time.time() - start) * 1000)
        
        if resp.status_code != 200:
            return {"pass": False, "latency": latency, "error": f"HTTP {resp.status_code}"}
        
        data = resp.json()
        result_type = data.get("type", "")
        success = data.get("success", False)
        
        # Vérifications
        type_ok = result_type == test.expected_type
        latency_ok = latency <= test.max_latency
        
        # Vérifier mot-clé si spécifié
        keyword_ok = True
        if test.keyword:
            text = data.get("response", "") + data.get("output", "")
            keyword_ok = test.keyword.lower() in text.lower()
        
        passed = success and type_ok and latency_ok and keyword_ok
        
        return {
            "pass": passed,
            "latency": latency,
            "type": result_type,
            "type_ok": type_ok,
            "latency_ok": latency_ok,
            "keyword_ok": keyword_ok
        }
        
    except Exception as e:
        return {
            "pass": False,
            "latency": int((time.time() - start) * 1000),
            "error": str(e)
        }


def main():
    """Lance tous les tests"""
    print("\n" + "=" * 70)
    print("  🧪 VALIDATION PHASE 2 - HOPPER")
    print("=" * 70)
    print()
    
    # Vérifier connexion
    try:
        r = requests.get(f"{ORCHESTRATOR_URL}/api/v1/status", timeout=3)
        if r.status_code == 200:
            status = r.json()
            print(f"✅ Orchestrator: {status.get('orchestrator')}")
            print(f"🎯 Dispatcher: {status.get('dispatcher')}")
            print(f"📊 Phase: {status.get('phase')}")
            print()
        else:
            print(f"⚠️  Orchestrator status: HTTP {r.status_code}")
            print()
    except:
        print("❌ Orchestrator non disponible\n")
        return False
    
    # Exécuter tests
    results = []
    
    for i, test in enumerate(TESTS, 1):
        print(f"[{i:2d}/{len(TESTS)}] {test.name:25s}", end=" ", flush=True)
        
        result = run_test(test)
        results.append(result)
        
        if result["pass"]:
            print(f"✅ {result['latency']:4d}ms")
        else:
            print(f"❌ {result.get('latency', 0):4d}ms", end="")
            if not result.get("type_ok"):
                print(f" [type:{result.get('type')}]", end="")
            if not result.get("latency_ok"):
                print(f" [slow]", end="")
            if not result.get("keyword_ok"):
                print(f" [keyword]", end="")
            if result.get("error"):
                print(f" [{result['error'][:30]}]", end="")
            print()
        
        time.sleep(0.3)  # Pause entre tests
    
    # Résultats
    print("\n" + "=" * 70)
    print("📊 RÉSULTATS")
    print("=" * 70)
    
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n✅ Réussis: {passed}/{total} ({rate:.1f}%)")
    print(f"❌ Échoués: {total - passed}/{total}")
    
    # Latence
    latencies = [r["latency"] for r in results if "latency" in r]
    if latencies:
        print(f"\n⏱️  Latence: min={min(latencies)}ms, max={max(latencies)}ms, moy={sum(latencies)//len(latencies)}ms")
    
    # Par type
    system_passed = sum(1 for i, r in enumerate(results) if r["pass"] and TESTS[i].expected_type == "system")
    system_total = sum(1 for t in TESTS if t.expected_type == "system")
    conv_passed = sum(1 for i, r in enumerate(results) if r["pass"] and TESTS[i].expected_type == "conversation")
    conv_total = sum(1 for t in TESTS if t.expected_type == "conversation")
    
    print(f"\n📋 Système: {system_passed}/{system_total} ({system_passed/system_total*100:.0f}%)")
    print(f"💬 Conversation: {conv_passed}/{conv_total} ({conv_passed/conv_total*100:.0f}%)")
    
    # Validation
    print("\n" + "=" * 70)
    if rate >= 70:
        print("🎉 PHASE 2 VALIDÉE (≥70% de réussite)")
        validation = True
    else:
        print(f"⚠️  PHASE 2 INCOMPLÈTE ({rate:.1f}% < 70%)")
        validation = False
    print("=" * 70)
    print()
    
    return validation


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
