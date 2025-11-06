#!/usr/bin/env python3
"""
HOPPER - Validation Technique Phase 2
Tests basés sur disponibilité API, temps réponse, statuts HTTP
Sans assertions sur contenu des réponses (non-déterministes)
"""

import requests
import time
import sys
from typing import Dict, Any, List, Tuple

# Configuration
BASE_URL = "http://localhost:5050"
LLM_URL = "http://localhost:5001"
MAX_LATENCY_MS = 5000  # 5 secondes max


class Colors:
    """Couleurs ANSI pour terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Affiche un header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_test(name: str, success: bool, details: str = ""):
    """Affiche résultat d'un test"""
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if success else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")


class Phase2Validator:
    """Validateur technique Phase 2"""
    
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
    
    def test(self, name: str, success: bool, details: str = ""):
        """Enregistre résultat test"""
        self.results.append((name, success, details))
        print_test(name, success, details)
        return success
    
    def run_all(self) -> bool:
        """Exécute tous les tests"""
        
        print_header("🔍 VALIDATION TECHNIQUE PHASE 2")
        
        # 1. Disponibilité services
        print(f"\n{Colors.BOLD}1. Disponibilité des services{Colors.RESET}")
        orchestrator_up = self.test_orchestrator_health()
        llm_up = self.test_llm_health()
        
        if not (orchestrator_up and llm_up):
            print(f"\n{Colors.RED}❌ Services essentiels indisponibles - arrêt{Colors.RESET}")
            return False
        
        # 2. Endpoints API
        print(f"\n{Colors.BOLD}2. Endpoints API{Colors.RESET}")
        self.test_command_endpoint()
        self.test_status_endpoint()
        
        # 3. Performance
        print(f"\n{Colors.BOLD}3. Performance{Colors.RESET}")
        self.test_response_latency()
        
        # 4. Knowledge Base
        print(f"\n{Colors.BOLD}4. Knowledge Base{Colors.RESET}")
        self.test_kb_available()
        self.test_kb_learn()
        self.test_kb_search()
        
        # 5. Résumé
        print_header("📊 RÉSUMÉ")
        return self.print_summary()
    
    def test_orchestrator_health(self) -> bool:
        """Test disponibilité orchestrator"""
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=2)
            success = r.status_code == 200
            details = f"Status: {r.status_code}"
            return self.test("Orchestrator /health", success, details)
        except Exception as e:
            return self.test("Orchestrator /health", False, f"Erreur: {e}")
    
    def test_llm_health(self) -> bool:
        """Test disponibilité LLM"""
        try:
            r = requests.get(f"{LLM_URL}/health", timeout=2)
            success = r.status_code == 200
            if success:
                data = r.json()
                model = data.get('model_loaded', False)
                details = f"Status: {r.status_code}, Model loaded: {model}"
            else:
                details = f"Status: {r.status_code}"
            return self.test("LLM /health", success, details)
        except Exception as e:
            return self.test("LLM /health", False, f"Erreur: {e}")
    
    def test_command_endpoint(self) -> bool:
        """Test endpoint /command"""
        try:
            r = requests.post(
                f"{BASE_URL}/api/v1/command",
                json={"command": "Test"},
                timeout=10
            )
            success = r.status_code == 200
            if success:
                data = r.json()
                has_success = "success" in data
                details = f"Status: {r.status_code}, Has 'success': {has_success}"
            else:
                details = f"Status: {r.status_code}"
            return self.test("POST /api/v1/command", success, details)
        except Exception as e:
            return self.test("POST /api/v1/command", False, f"Erreur: {e}")
    
    def test_status_endpoint(self) -> bool:
        """Test endpoint /status"""
        try:
            r = requests.get(f"{BASE_URL}/api/v1/status", timeout=2)
            success = r.status_code == 200
            if success:
                data = r.json()
                has_phase = "phase" in data
                details = f"Status: {r.status_code}, Has 'phase': {has_phase}"
            else:
                details = f"Status: {r.status_code}"
            return self.test("GET /api/v1/status", success, details)
        except Exception as e:
            return self.test("GET /api/v1/status", False, f"Erreur: {e}")
    
    def test_response_latency(self) -> bool:
        """Test latence réponse"""
        try:
            start = time.time()
            r = requests.post(
                f"{BASE_URL}/api/v1/command",
                json={"command": "Bonjour"},
                timeout=15
            )
            latency_ms = int((time.time() - start) * 1000)
            
            success = r.status_code == 200 and latency_ms < MAX_LATENCY_MS
            details = f"Latence: {latency_ms}ms (max: {MAX_LATENCY_MS}ms)"
            return self.test("Latence < 5s", success, details)
        except Exception as e:
            return self.test("Latence < 5s", False, f"Erreur: {e}")
    
    def test_kb_available(self) -> bool:
        """Test disponibilité KB"""
        try:
            r = requests.get(f"{LLM_URL}/knowledge/stats", timeout=2)
            success = r.status_code == 200
            if success:
                data = r.json()
                backend = data.get('backend', 'unknown')
                total = data.get('total_documents', 0)
                details = f"Backend: {backend}, Docs: {total}"
            else:
                details = f"Status: {r.status_code}"
            return self.test("KB disponible", success, details)
        except Exception as e:
            return self.test("KB disponible", False, f"Erreur: {e}")
    
    def test_kb_learn(self) -> bool:
        """Test apprentissage KB"""
        try:
            test_fact = f"Test_{int(time.time())}: Validation technique"
            r = requests.post(
                f"{LLM_URL}/kb/learn",
                json={"text": test_fact},
                timeout=5
            )
            success = r.status_code == 200
            if success:
                data = r.json()
                added = data.get('added', False)
                details = f"Fait ajouté: {added}"
            else:
                details = f"Status: {r.status_code}"
            return self.test("KB /learn", success, details)
        except Exception as e:
            return self.test("KB /learn", False, f"Erreur: {e}")
    
    def test_kb_search(self) -> bool:
        """Test recherche KB"""
        try:
            r = requests.post(
                f"{LLM_URL}/search",
                json={"query": "test", "k": 3},
                timeout=5
            )
            success = r.status_code == 200
            if success:
                data = r.json()
                nb_results = len(data.get('results', []))
                details = f"Résultats: {nb_results}"
            else:
                details = f"Status: {r.status_code}"
            return self.test("KB /search", success, details)
        except Exception as e:
            return self.test("KB /search", False, f"Erreur: {e}")
    
    def print_summary(self) -> bool:
        """Affiche résumé et retourne statut global"""
        total = len(self.results)
        passed = sum(1 for _, success, _ in self.results if success)
        failed = total - passed
        
        percentage = int((passed / total) * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}Tests:{Colors.RESET}")
        print(f"  • Total: {total}")
        print(f"  • {Colors.GREEN}Réussis: {passed}{Colors.RESET}")
        print(f"  • {Colors.RED}Échoués: {failed}{Colors.RESET}")
        print(f"  • Taux: {percentage}%")
        
        if percentage >= 90:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ PHASE 2 VALIDÉE{Colors.RESET}")
            return True
        elif percentage >= 70:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  PHASE 2 PARTIELLE{Colors.RESET}")
            print(f"{Colors.YELLOW}Certains tests ont échoué mais le système est opérationnel{Colors.RESET}")
            return True
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ PHASE 2 NON VALIDÉE{Colors.RESET}")
            return False


def main():
    """Point d'entrée"""
    validator = Phase2Validator()
    
    try:
        success = validator.run_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Tests interrompus{Colors.RESET}")
        sys.exit(2)


if __name__ == "__main__":
    main()
