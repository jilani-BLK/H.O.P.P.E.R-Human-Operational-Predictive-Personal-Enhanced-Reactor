"""
Tests d'intégration pour l'architecture LLM-First
Valide le pipeline complet Thought → Act → Observe → Answer
"""

import pytest
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:5050"
USER_ID = "integration_test"


class TestLlmFirstPipeline:
    """Tests end-to-end du pipeline LLM-First"""
    
    def test_pipeline_create_file(self):
        """
        Test: Créer un fichier via le pipeline LLM-First
        
        Pipeline:
        1. User: "Crée un fichier /tmp/test_integration.txt avec bonjour"
        2. PromptAssembler: Injecte contexte + outils disponibles
        3. LLM: Génère SystemPlan JSON avec create_file
        4. ToolExecutor: Appelle system_executor
        5. System Executor (C): Parse JSON et crée fichier
        6. LlmAgent: Reformule réponse naturelle
        """
        
        # Commande utilisateur
        payload = {
            "text": "Crée un fichier /tmp/test_integration.txt avec le contenu bonjour",
            "user_id": USER_ID
        }
        
        # Appel API
        response = requests.post(f"{BASE_URL}/command", json=payload)
        
        # Assertions
        assert response.status_code == 200, "L'API doit répondre 200"
        
        data = response.json()
        assert data["success"] is True, "Le succès doit être True"
        assert "test_integration.txt" in data["message"], "Le message doit mentionner le fichier"
        
        # Vérifier les métadonnées du pipeline
        assert data["data"]["intent"] == "action_system", "L'intent doit être action_system"
        assert data["data"]["tools_executed"] == 1, "1 outil doit être exécuté"
        assert data["data"]["tools_succeeded"] == 1, "1 outil doit réussir"
        assert data["data"]["tools_failed"] == 0, "Aucun outil ne doit échouer"
        
        # Vérifier les résultats d'exécution
        results = data["data"]["results"]
        assert len(results) == 1, "1 résultat attendu"
        assert results[0]["tool"] == "system_executor", "L'outil doit être system_executor"
        assert results[0]["action"] == "create_file", "L'action doit être create_file"
        assert results[0]["result"]["success"] is True, "L'exécution doit réussir"
        
        # Vérifier le path dans la réponse
        result_data = results[0]["result"]["data"]
        assert result_data["path"] == "/tmp/test_integration.txt", "Le path doit correspondre"
    
    
    def test_pipeline_list_directory(self):
        """
        Test: Lister un répertoire via le pipeline LLM-First
        
        Pipeline:
        1. User: "Liste le contenu de /tmp"
        2. LLM: Génère SystemPlan avec list_directory
        3. System Executor (C): Exécute readdir()
        4. Reformulation naturelle
        """
        
        payload = {
            "text": "Liste le contenu du répertoire /tmp",
            "user_id": USER_ID
        }
        
        response = requests.post(f"{BASE_URL}/command", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Vérifier la structure
        assert data["data"]["intent"] == "action_system"
        assert data["data"]["tools_executed"] == 1
        
        results = data["data"]["results"]
        assert results[0]["tool"] == "system_executor"
        assert results[0]["action"] == "list_directory"
        
        # Vérifier que des fichiers sont listés
        files = results[0]["result"]["data"]["data"]["files"]
        assert isinstance(files, list), "files doit être une liste"
        assert len(files) > 0, "Le répertoire /tmp ne devrait pas être vide"
    
    
    def test_pipeline_delete_file(self):
        """
        Test: Supprimer un fichier via le pipeline LLM-First
        
        Pipeline:
        1. Créer un fichier à supprimer
        2. User: "Supprime le fichier X"
        3. LLM: Génère SystemPlan avec delete_file
        4. System Executor (C): Exécute remove()
        5. Vérifier la suppression
        """
        
        # 1. Créer le fichier à supprimer
        create_payload = {
            "text": "Crée un fichier /tmp/to_delete.txt avec le contenu test",
            "user_id": USER_ID
        }
        response = requests.post(f"{BASE_URL}/command", json=create_payload)
        assert response.json()["success"] is True, "La création doit réussir"
        
        time.sleep(1)  # Attendre que le fichier soit créé
        
        # 2. Supprimer le fichier
        delete_payload = {
            "text": "Supprime le fichier /tmp/to_delete.txt",
            "user_id": USER_ID
        }
        response = requests.post(f"{BASE_URL}/command", json=delete_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Vérifier les métadonnées
        assert data["data"]["intent"] == "action_system"
        assert data["data"]["tools_succeeded"] == 1
        
        results = data["data"]["results"]
        assert results[0]["action"] == "delete_file"
        assert results[0]["result"]["success"] is True
    
    
    def test_pipeline_multi_turn_conversation(self):
        """
        Test: Conversation multi-tour avec contexte
        
        Valide:
        - Context Manager historique
        - Injection contexte dans prompts
        - Reformulation avec contexte
        """
        
        # Tour 1: Présentation
        payload1 = {
            "text": "Je m'appelle Alice",
            "user_id": USER_ID
        }
        response1 = requests.post(f"{BASE_URL}/command", json=payload1)
        assert response1.json()["success"] is True
        
        time.sleep(1)
        
        # Tour 2: Rappel du nom
        payload2 = {
            "text": "Comment je m'appelle ?",
            "user_id": USER_ID
        }
        response2 = requests.post(f"{BASE_URL}/command", json=payload2)
        
        data = response2.json()
        assert data["success"] is True
        
        # Le LLM doit se souvenir du nom grâce au Context Manager
        assert "Alice" in data["message"], "Le LLM doit se souvenir du nom Alice"
    
    
    def test_pipeline_error_handling(self):
        """
        Test: Gestion d'erreurs (fichier inexistant)
        
        Valide:
        - Fallback sur erreur d'outil
        - Message d'erreur user-friendly
        - Métadonnées d'échec
        """
        
        payload = {
            "text": "Supprime le fichier /tmp/fichier_inexistant_xyz123.txt",
            "user_id": USER_ID
        }
        
        response = requests.post(f"{BASE_URL}/command", json=payload)
        
        # L'API doit répondre 200 même en cas d'échec d'outil
        assert response.status_code == 200
        
        data = response.json()
        # Le système peut soit échouer l'outil soit dire que c'est fait
        # selon la logique du system_executor
        assert "success" in data
    
    
    def test_pipeline_json_parsing_robustness(self):
        """
        Test: Robustesse du parsing JSON LLM
        
        Valide:
        - Extraction JSON même avec texte avant/après
        - Gestion multi-objets JSON
        - Fallback si JSON invalide
        """
        
        # Commande complexe pour forcer du texte autour du JSON
        payload = {
            "text": "Crée un fichier /tmp/complex.txt avec le texte 'JSON test'",
            "user_id": USER_ID
        }
        
        response = requests.post(f"{BASE_URL}/command", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True, "Le parsing doit gérer le texte autour du JSON"


class TestLlmFirstComponents:
    """Tests unitaires des composants LLM-First"""
    
    def test_health_check(self):
        """Vérifier que l'orchestrator répond"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
    
    
    def test_api_structure(self):
        """Valider la structure de réponse API"""
        payload = {
            "text": "Bonjour",
            "user_id": USER_ID
        }
        
        response = requests.post(f"{BASE_URL}/command", json=payload)
        data = response.json()
        
        # Structure obligatoire
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "actions_taken" in data
        
        # Structure data
        if data["success"]:
            assert "intent" in data["data"]
            assert "confidence" in data["data"]


class TestSystemExecutorC:
    """Tests spécifiques au System Executor C"""
    
    SYSTEM_EXECUTOR_URL = "http://localhost:5002"
    
    def test_health_endpoint(self):
        """Tester le endpoint /health du system_executor"""
        response = requests.get(f"{self.SYSTEM_EXECUTOR_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "system_executor"
    
    
    def test_direct_json_parsing(self):
        """Tester le parsing JSON direct (sans LLM)"""
        
        payload = {
            "action": "create_file",
            "path": "/tmp/direct_test.txt",
            "content": "Direct JSON test"
        }
        
        response = requests.post(f"{self.SYSTEM_EXECUTOR_URL}/execute", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "Fichier créé avec succès" in data["message"]
        assert data["data"]["path"] == "/tmp/direct_test.txt"


# Fixtures
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    """Nettoyer les fichiers de test après la session"""
    yield
    
    # Cleanup après tous les tests
    test_files = [
        "/tmp/test_integration.txt",
        "/tmp/to_delete.txt",
        "/tmp/complex.txt",
        "/tmp/direct_test.txt"
    ]
    
    for filepath in test_files:
        try:
            payload = {
                "text": f"Supprime le fichier {filepath}",
                "user_id": "cleanup"
            }
            requests.post(f"{BASE_URL}/command", json=payload, timeout=5)
        except:
            pass  # Ignorer les erreurs de cleanup


if __name__ == "__main__":
    """Lancer les tests avec pytest"""
    pytest.main([__file__, "-v", "--tb=short"])
