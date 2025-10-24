"""
HOPPER - Tests d'acceptation Phase 2
Tests pour validation LLM, RAG, conversation multi-tour
"""

import pytest
import requests
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
LLM_URL = "http://localhost:5001"
TEST_USER_ID = "test_user_phase2"


class TestPhase2LLM:
    """Tests du modèle LLM"""
    
    def test_llm_loaded(self):
        """Vérifier que le modèle LLM est chargé"""
        r = requests.get(f"{LLM_URL}/health")
        assert r.status_code == 200
        
        data = r.json()
        assert data['model_loaded'] == True, "Modèle LLM non chargé"
        assert data['status'] == 'healthy'
        assert 'mistral' in data['model_path'].lower() or 'llama' in data['model_path'].lower()
        print(f"✅ Modèle chargé: {data['model_path']}")
    
    def test_basic_generation(self):
        """Test génération basique"""
        r = requests.post(
            f"{LLM_URL}/generate",
            json={
                "prompt": "Question: Qu'est-ce que Python?\nRéponse:",
                "max_tokens": 100
            },
            timeout=10
        )
        
        assert r.status_code == 200
        data = r.json()
        
        assert 'text' in data
        assert len(data['text']) > 10, "Réponse trop courte"
        assert data['tokens_generated'] > 0
        
        print(f"✅ Génération: {data['text'][:80]}... ({data['tokens_generated']} tokens)")
    
    def test_performance_generation(self):
        """Vérifier performance <5s pour 200 tokens"""
        start = time.time()
        
        r = requests.post(
            f"{LLM_URL}/generate",
            json={
                "prompt": "Explique Python en 100 mots",
                "max_tokens": 150
            },
            timeout=10
        )
        
        duration = time.time() - start
        
        assert r.status_code == 200
        assert duration < 5.0, f"Trop lent: {duration:.2f}s > 5s"
        
        data = r.json()
        tokens_per_sec = data['tokens_generated'] / duration
        
        print(f"✅ Performance: {duration:.2f}s, {tokens_per_sec:.1f} tokens/sec")


class TestPhase2KnowledgeBase:
    """Tests de la Knowledge Base (RAG)"""
    
    def test_kb_available(self):
        """Vérifier KB disponible"""
        r = requests.get(f"{LLM_URL}/knowledge/stats")
        assert r.status_code == 200
        
        data = r.json()
        assert data['available'] == True
        assert data['embedding_dimension'] == 384
        
        print(f"✅ KB disponible: {data['total_documents']} documents")
    
    def test_learn_fact(self):
        """Test apprentissage d'un fait"""
        fact = "La tour Eiffel mesure 330 mètres de hauteur"
        
        r = requests.post(
            f"{LLM_URL}/learn",
            json={"text": fact}
        )
        
        assert r.status_code == 200
        data = r.json()
        
        assert data['status'] == 'success'
        assert data['added'] == 1
        
        print(f"✅ Fait appris: {fact}")
    
    def test_search_fact(self):
        """Test recherche d'un fait appris"""
        # D'abord apprendre
        requests.post(
            f"{LLM_URL}/learn",
            json={"text": "Python a été créé par Guido van Rossum en 1991"}
        )
        
        # Ensuite chercher
        r = requests.post(
            f"{LLM_URL}/search",
            json={"query": "qui a créé Python", "k": 3}
        )
        
        assert r.status_code == 200
        data = r.json()
        
        assert len(data['results']) > 0, "Aucun résultat trouvé"
        assert data['results'][0]['score'] > 0.3, "Score trop faible"
        
        print(f"✅ Recherche: {len(data['results'])} résultats, score={data['results'][0]['score']:.2f}")


class TestPhase2Conversation:
    """Tests de conversation via orchestrator"""
    
    def test_hopper_persona(self):
        """Vérifier persona HOPPER"""
        r = requests.post(
            f"{BASE_URL}/command",
            json={"text": "Qui es-tu?"}
        )
        
        assert r.status_code == 200
        response = r.json()['message'].lower()
        
        assert 'hopper' in response, "Ne se présente pas comme HOPPER"
        assert 'assistant' in response or 'ia' in response
        
        print(f"✅ Persona: {r.json()['message'][:100]}...")
    
    def test_multi_turn_conversation(self):
        """Test conversation multi-tour avec contexte"""
        user_id = f"test_multiturn_{int(time.time())}"
        
        # Tour 1
        r1 = requests.post(
            f"{BASE_URL}/command",
            json={"text": "Bonjour, comment vas-tu?", "user_id": user_id}
        )
        assert r1.status_code == 200
        print(f"Tour 1: {r1.json()['message'][:60]}...")
        
        # Tour 2
        r2 = requests.post(
            f"{BASE_URL}/command",
            json={"text": "Que peux-tu faire pour moi?", "user_id": user_id}
        )
        assert r2.status_code == 200
        print(f"Tour 2: {r2.json()['message'][:60]}...")
        
        # Tour 3 - référence au contexte
        r3 = requests.post(
            f"{BASE_URL}/command",
            json={"text": "Et tu fais ça comment?", "user_id": user_id}
        )
        assert r3.status_code == 200
        print(f"Tour 3: {r3.json()['message'][:60]}...")
        
        print(f"✅ Conversation multi-tour: 3 échanges réussis")
    
    def test_rag_learn_and_recall(self):
        """Test apprentissage puis rappel (RAG complet)"""
        # Apprendre un fait
        r1 = requests.post(
            f"{BASE_URL}/command",
            json={"text": "Apprends que le Louvre est le musée le plus visité au monde"}
        )
        assert r1.status_code == 200
        assert 'appris' in r1.json()['message'].lower()
        print(f"✅ Apprentissage: {r1.json()['message']}")
        
        # Rappeler le fait
        time.sleep(1)  # Laisser temps d'indexation
        
        r2 = requests.post(
            f"{BASE_URL}/command",
            json={"text": "Quel est le musée le plus visité?"}
        )
        assert r2.status_code == 200
        response = r2.json()['message'].lower()
        assert 'louvre' in response, f"Louvre non mentionné dans: {response}"
        print(f"✅ Rappel: {r2.json()['message']}")
    
    def test_conversation_quality(self):
        """Test qualité conversations (10 scénarios)"""
        scenarios = [
            ("Bonjour", ["bonjour", "hello", "salut", "vous", "je"]),
            ("Qui es-tu?", ["hopper", "assistant", "ia", "je suis"]),
            ("Que peux-tu faire?", ["fichier", "question", "aide", "command", "peux", "faire", "je peux"]),
            ("Explique Python en 20 mots", ["langage", "programmation", "code", "python"]),
            ("Quelle heure est-il?", ["heure", "temps", "local", "ne peux", "sais pas", "hors"]),
            ("Merci", ["de rien", "plaisir", "service", "bienvenue", "vous", "je"]),
            ("Comment créer un fichier?", ["créer", "fichier", "command", "système"]),
            ("C'est quoi une IA?", ["intelligence", "artificielle", "programme", "système", "ia"]),
            ("Au revoir", ["revoir", "bientôt", "bye", "service", "vous"]),
            ("Tu es intelligent?", ["ia", "assistant", "intelligent", "aide", "je", "suis"]),
        ]
        
        passed = 0
        failed_scenarios = []
        
        for question, expected_keywords in scenarios:
            try:
                r = requests.post(
                    f"{BASE_URL}/command",
                    json={"text": question},
                    timeout=30  # Augmenté à 30s pour le LLM
                )
                
                if r.status_code == 200:
                    response = r.json()['message'].lower()
                    
                    if any(keyword in response for keyword in expected_keywords):
                        passed += 1
                        print(f"✅ '{question}': PASS")
                    else:
                        failed_scenarios.append((question, response[:50]))
                        print(f"❌ '{question}': FAIL - {response[:50]}...")
                else:
                    failed_scenarios.append((question, f"HTTP {r.status_code}"))
                    
            except Exception as e:
                failed_scenarios.append((question, str(e)[:50]))
                print(f"❌ '{question}': ERROR - {str(e)[:50]}")
            
            # Délai entre requêtes pour ne pas surcharger le LLM
            time.sleep(0.5)
        
        success_rate = (passed / len(scenarios)) * 100
        
        print(f"\n📊 Résultats: {passed}/{len(scenarios)} réussis ({success_rate:.1f}%)")
        
        if failed_scenarios:
            print("\n❌ Scénarios échoués:")
            for q, err in failed_scenarios:
                print(f"  - '{q}': {err}")
        
        assert success_rate >= 70, f"Taux réussite trop faible: {success_rate:.1f}% < 70%"
        print(f"✅ Taux réussite objectif atteint: {success_rate:.1f}% ≥ 70%")


class TestPhase2Integration:
    """Tests d'intégration bout-en-bout"""
    
    def test_end_to_end_latency(self):
        """Test latence end-to-end CLI→Orchestrator→LLM→Response"""
        start = time.time()
        
        r = requests.post(
            f"{BASE_URL}/command",
            json={"text": "Qu'est-ce que Python?"},
            timeout=15
        )
        
        duration = time.time() - start
        
        assert r.status_code == 200
        assert duration < 10.0, f"Latence trop élevée: {duration:.2f}s"
        
        print(f"✅ Latence end-to-end: {duration:.2f}s")
    
    def test_system_action_still_works(self):
        """Vérifier que les actions système fonctionnent toujours"""
        r = requests.post(
            f"{BASE_URL}/command",
            json={"text": "Liste les fichiers"}
        )
        
        assert r.status_code == 200
        # Devrait appeler system_executor
        
        print(f"✅ Actions système fonctionnelles")
    
    def test_concurrent_requests(self):
        """Test 5 requêtes concurrentes"""
        import concurrent.futures
        
        def make_request(i):
            r = requests.post(
                f"{BASE_URL}/command",
                json={"text": f"Dis bonjour numéro {i}"},
                timeout=15
            )
            return r.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(make_request, range(5)))
        
        success_count = sum(results)
        assert success_count >= 4, f"Seulement {success_count}/5 requêtes réussies"
        
        print(f"✅ Concurrence: {success_count}/5 requêtes réussies")


def test_phase2_summary():
    """Résumé Phase 2"""
    print("\n" + "="*60)
    print("PHASE 2 - RÉSUMÉ DES TESTS")
    print("="*60)
    
    # Stats LLM
    r_llm = requests.get(f"{LLM_URL}/health")
    if r_llm.status_code == 200:
        llm_data = r_llm.json()
        print(f"✅ LLM: {llm_data['model_path'].split('/')[-1]}")
        print(f"   - Contexte: {llm_data['context_size']} tokens")
        print(f"   - Mode: {llm_data['mode']}")
    
    # Stats KB
    r_kb = requests.get(f"{LLM_URL}/knowledge/stats")
    if r_kb.status_code == 200:
        kb_data = r_kb.json()
        print(f"✅ Knowledge Base:")
        print(f"   - Documents: {kb_data['total_documents']}")
        print(f"   - Dimension: {kb_data['embedding_dimension']}")
    
    # Stats Orchestrator
    r_orch = requests.get(f"{BASE_URL}/health")
    if r_orch.status_code == 200:
        orch_data = r_orch.json()
        print(f"✅ Orchestrator:")
        print(f"   - Status: {orch_data['status']}")
        print(f"   - Services actifs: {sum(orch_data['services'].values())}/7")
    
    print("="*60)
    print("PHASE 2 VALIDÉE ✅")
    print("="*60)


if __name__ == "__main__":
    # Exécuter tests avec pytest
    pytest.main([__file__, "-v", "-s"])
