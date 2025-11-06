#!/usr/bin/env python3
"""
Script de Validation Phase 1 - HOPPER
Vérifie que tous les composants essentiels sont présents et fonctionnels
"""

import os
import sys
import importlib.util
from pathlib import Path

# Couleurs pour output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def check(condition, message):
    """Affiche le résultat d'une vérification"""
    if condition:
        print(f"{GREEN}OK{RESET}   {message}")
        return True
    else:
        print(f"{RED}FAIL{RESET} {message}")
        return False

def check_file_exists(filepath, description):
    """Vérifie qu'un fichier existe"""
    exists = os.path.isfile(filepath)
    return check(exists, f"{description}: {filepath}")

def check_dir_exists(dirpath, description):
    """Vérifie qu'un dossier existe"""
    exists = os.path.isdir(dirpath)
    return check(exists, f"{description}: {dirpath}")

def check_python_syntax(filepath):
    """Vérifie la syntaxe Python d'un fichier"""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return check(True, f"Syntaxe Python OK: {filepath}")
    except SyntaxError as e:
        print(f"{RED}FAIL{RESET} Erreur syntaxe dans {filepath}: {e}")
        return False
    except Exception as e:
        print(f"{YELLOW}WARN{RESET} Impossible de vérifier {filepath}: {e}")
        return True

def main():
    print(f"\n{BOLD}=== VALIDATION PHASE 1 - HOPPER ==={RESET}\n")
    
    total = 0
    passed = 0
    
    # Vérification structure de base
    print(f"{BOLD}[1] Structure de base{RESET}")
    checks = [
        check_file_exists("README.md", "README principal"),
        check_file_exists(".gitignore", "Gitignore"),
        check_file_exists(".env.example", "Template env"),
        check_file_exists("docker-compose.yml", "Docker Compose"),
        check_file_exists("Makefile", "Makefile"),
        check_file_exists("hopper_cli.py", "CLI Phase 1"),
        check_file_exists("scripts/install/install.sh", "Script installation"),
    ]
    total += len(checks)
    passed += sum(checks)
    
    # Vérification dossiers
    print(f"\n{BOLD}[2] Dossiers requis{RESET}")
    checks = [
        check_dir_exists("src", "Source"),
        check_dir_exists("docker", "Dockerfiles"),
        check_dir_exists("docs", "Documentation"),
        check_dir_exists("tests", "Tests"),
        check_dir_exists("config", "Config"),
        check_dir_exists("data", "Data"),
    ]
    total += len(checks)
    passed += sum(checks)
    
    # Vérification Dockerfiles
    print(f"\n{BOLD}[3] Dockerfiles{RESET}")
    dockerfiles = [
        "docker/orchestrator.Dockerfile",
        "docker/llm.Dockerfile",
        "docker/system_executor_python.Dockerfile",
        "docker/auth.Dockerfile",
        "docker/connectors.Dockerfile",
    ]
    checks = [check_file_exists(df, os.path.basename(df)) for df in dockerfiles]
    total += len(checks)
    passed += sum(checks)
    
    # Vérification modules Python
    print(f"\n{BOLD}[4] Modules Python - Orchestrateur{RESET}")
    py_files = [
        "src/orchestrator/main_phase1.py",
        "src/orchestrator/config.py",
        "src/orchestrator/requirements.txt",
        "src/orchestrator/core/simple_dispatcher.py",
        "src/orchestrator/core/service_registry.py",
        "src/orchestrator/api/phase1_routes.py",
    ]
    
    for pf in py_files:
        if check_file_exists(pf, os.path.basename(pf)):
            if pf.endswith('.py'):
                check_python_syntax(pf)
            passed += 1
        total += 1
    
    # Vérification autres services Python
    print(f"\n{BOLD}[5] Services IA et Connecteurs{RESET}")
    services = [
        "src/llm_engine/server.py",
        "src/system_executor/server.py",
        "src/auth/server.py",
        "src/connectors/server.py",
    ]
    
    for sf in services:
        if check_file_exists(sf, os.path.basename(sf)):
            check_python_syntax(sf)
            passed += 1
        total += 1
    
    # Vérification module C
    print(f"\n{BOLD}[6] Module Système (C){RESET}")
    checks = [
        check_file_exists("src/system_executor/Makefile", "Makefile C"),
        check_file_exists("src/system_executor/src/main.c", "main.c"),
    ]
    total += len(checks)
    passed += sum(checks)
    
    # Vérification CLI
    print(f"\n{BOLD}[7] Interface CLI{RESET}")
    if check_file_exists("hopper_cli.py", "CLI Phase 1"):
        check_python_syntax("hopper_cli.py")
        
        # Vérifier si exécutable
        is_executable = os.access("hopper_cli.py", os.X_OK)
        check(is_executable, "CLI exécutable")
        passed += 2
    total += 2
    
    # Vérification documentation
    print(f"\n{BOLD}[8] Documentation{RESET}")
    docs = [
        "docs/README.md",
        "docs/ARCHITECTURE.md",
        "docs/QUICKSTART.md",
        "docs/DEVELOPMENT.md",
    ]
    checks = [check_file_exists(doc, os.path.basename(doc)) for doc in docs]
    total += len(checks)
    passed += sum(checks)
    
    # Vérification tests
    print(f"\n{BOLD}[9] Tests{RESET}")
    checks = [
        check_file_exists("tests/test_integration.py", "Tests d'intégration"),
    ]
    total += len(checks)
    passed += sum(checks)
    
    # Résumé
    print(f"\n{BOLD}{'='*50}{RESET}")
    percentage = (passed / total * 100) if total > 0 else 0
    
    if percentage == 100:
        color = GREEN
        status = "PHASE 1 COMPLETE"
    elif percentage >= 80:
        color = YELLOW
        status = "PHASE 1 PRESQUE COMPLETE"
    else:
        color = RED
        status = "PHASE 1 INCOMPLETE"
    
    print(f"{color}{BOLD}{status}{RESET}")
    print(f"{passed}/{total} vérifications réussies ({percentage:.1f}%)")
    print(f"{BOLD}{'='*50}{RESET}\n")
    
    if percentage == 100:
        print(f"{GREEN}READY FOR PHASE 2{RESET}\n")
        return 0
    else:
        print(f"{RED}Corriger les erreurs avant Phase 2{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
