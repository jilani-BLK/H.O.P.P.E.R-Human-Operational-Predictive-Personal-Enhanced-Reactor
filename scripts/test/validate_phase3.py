#!/usr/bin/env python3
"""
Validation de la Phase 3 - HOPPER
Vérifie la progression des fonctionnalités principales
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Affiche un en-tête"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

def check_file(path: str, description: str) -> bool:
    """Vérifie qu'un fichier existe"""
    exists = os.path.exists(path)
    status = f"{Colors.GREEN}OK{Colors.END}" if exists else f"{Colors.RED}TODO{Colors.END}"
    print(f"  [{status}] {description}: {path}")
    return exists

def check_package(package: str, description: str) -> bool:
    """Vérifie qu'un package Python est installé"""
    try:
        __import__(package)
        print(f"  [{Colors.GREEN}OK{Colors.END}] {description}: {package}")
        return True
    except ImportError:
        print(f"  [{Colors.YELLOW}TODO{Colors.END}] {description}: {package}")
        return False

def main():
    """Point d'entrée principal"""
    
    print(f"\n{Colors.BOLD}{'='*60}")
    print("  VALIDATION PHASE 3 - HOPPER")
    print(f"  Fonctionnalités Principales & Expérimentations")
    print(f"{'='*60}{Colors.END}\n")
    
    total_checks = 0
    passed_checks = 0
    
    # ========================================
    # 1. STT - Reconnaissance Vocale
    # ========================================
    print_header("[1] STT - Reconnaissance Vocale")
    
    stt_checks = [
        ("src/stt/server.py", "Service STT existant"),
        ("src/stt/whisper_engine.py", "Whisper engine optimisé"),
        ("src/stt/wake_word.py", "Détection wake word"),
        ("src/stt/audio_stream.py", "Streaming audio"),
    ]
    
    for path, desc in stt_checks:
        total_checks += 1
        if check_file(path, desc):
            passed_checks += 1
    
    # Packages STT
    stt_packages = [
        ("whisper", "OpenAI Whisper"),
        ("pyaudio", "PyAudio (capture micro)"),
    ]
    
    for package, desc in stt_packages:
        total_checks += 1
        if check_package(package, desc):
            passed_checks += 1
    
    # ========================================
    # 2. TTS - Synthèse Vocale
    # ========================================
    print_header("[2] TTS - Synthèse Vocale")
    
    tts_checks = [
        ("src/tts/server.py", "Service TTS existant"),
        ("src/tts/coqui_engine.py", "Coqui TTS optimisé"),
        ("src/tts/voice_profiles.py", "Profils vocaux"),
    ]
    
    for path, desc in tts_checks:
        total_checks += 1
        if check_file(path, desc):
            passed_checks += 1
    
    # Packages TTS
    tts_packages = [
        ("TTS", "Coqui TTS"),
    ]
    
    for package, desc in tts_packages:
        total_checks += 1
        if check_package(package, desc):
            passed_checks += 1
    
    # ========================================
    # 3. Auth Vocale
    # ========================================
    print_header("[3] Auth - Identification Vocale")
    
    auth_checks = [
        ("src/auth/server.py", "Service Auth existant"),
        ("src/auth/voice_auth.py", "Reconnaissance vocale"),
        ("src/auth/user_db.py", "Base empreintes vocales"),
        ("data/voice_profiles/", "Dossier empreintes"),
    ]
    
    for path, desc in auth_checks:
        total_checks += 1
        if check_file(path, desc):
            passed_checks += 1
    
    # Packages Auth
    auth_packages = [
        ("speechbrain", "SpeechBrain (recommandé)"),
    ]
    
    for package, desc in auth_packages:
        total_checks += 1
        if check_package(package, desc):
            passed_checks += 1
    
    # ========================================
    # 4. Email Connector
    # ========================================
    print_header("[4] Email - Connecteur IMAP")
    
    email_checks = [
        ("src/connectors/server.py", "Service Connectors existant"),
        ("src/connectors/email/__init__.py", "Module email"),
        ("src/connectors/email/imap_client.py", "Client IMAP"),
        ("src/connectors/email/email_parser.py", "Parser emails"),
        ("src/connectors/email/email_classifier.py", "Classification LLM"),
        ("config/email_config.yaml", "Configuration email"),
        ("data/email_cache/", "Cache emails"),
    ]
    
    for path, desc in email_checks:
        total_checks += 1
        if check_file(path, desc):
            passed_checks += 1
    
    # Packages Email
    email_packages = [
        ("aioimaplib", "IMAP asynchrone"),
        ("bs4", "BeautifulSoup (parsing HTML)"),
    ]
    
    for package, desc in email_packages:
        total_checks += 1
        if check_package(package, desc):
            passed_checks += 1
    
    # ========================================
    # 5. Notifications Proactives
    # ========================================
    print_header("[5] Notifications Proactives")
    
    notif_checks = [
        ("src/orchestrator/workers/__init__.py", "Module workers"),
        ("src/orchestrator/workers/email_worker.py", "Worker email"),
        ("src/orchestrator/workers/notification_worker.py", "Worker notifications"),
        ("config/notification_rules.yaml", "Règles notifications"),
    ]
    
    for path, desc in notif_checks:
        total_checks += 1
        if check_file(path, desc):
            passed_checks += 1
    
    # Packages Notifications
    notif_packages = [
        ("apscheduler", "Scheduler"),
    ]
    
    for package, desc in notif_packages:
        total_checks += 1
        if check_package(package, desc):
            passed_checks += 1
    
    # ========================================
    # 6. Pipeline Vocal Complet
    # ========================================
    print_header("[6] Pipeline Vocal (STT → LLM → TTS)")
    
    pipeline_checks = [
        ("src/orchestrator/services/voice_pipeline.py", "Pipeline vocal"),
        ("src/orchestrator/services/email_service.py", "Service email"),
    ]
    
    for path, desc in pipeline_checks:
        total_checks += 1
        if check_file(path, desc):
            passed_checks += 1
    
    # ========================================
    # 7. Tests Phase 3
    # ========================================
    print_header("[7] Tests Phase 3")
    
    test_checks = [
        ("tests/test_phase3_stt.py", "Tests STT"),
        ("tests/test_phase3_tts.py", "Tests TTS"),
        ("tests/test_phase3_auth.py", "Tests auth vocale"),
        ("tests/test_phase3_email.py", "Tests email"),
        ("tests/test_phase3_scenario.py", "Scénario complet"),
        ("tests/load_test.py", "Tests de charge"),
    ]
    
    for path, desc in test_checks:
        total_checks += 1
        if check_file(path, desc):
            passed_checks += 1
    
    # ========================================
    # 8. Documentation
    # ========================================
    print_header("[8] Documentation Phase 3")
    
    doc_checks = [
        ("docs/PHASE3_PLAN.md", "Plan Phase 3"),
        ("docs/VOICE_SETUP.md", "Guide configuration vocale"),
        ("docs/EMAIL_SETUP.md", "Guide configuration email"),
    ]
    
    for path, desc in doc_checks:
        total_checks += 1
        if check_file(path, desc):
            passed_checks += 1
    
    # ========================================
    # RÉSUMÉ
    # ========================================
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    
    percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n{Colors.BOLD}RÉSUMÉ PHASE 3{Colors.END}")
    print(f"{passed_checks}/{total_checks} vérifications réussies ({percentage:.1f}%)\n")
    
    # Barre de progression
    bar_length = 40
    filled = int(bar_length * passed_checks / total_checks)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    if percentage >= 90:
        color = Colors.GREEN
        status = "EXCELLENT"
    elif percentage >= 70:
        color = Colors.YELLOW
        status = "EN COURS"
    elif percentage >= 30:
        color = Colors.YELLOW
        status = "DÉBUT"
    else:
        color = Colors.YELLOW
        status = "À DÉMARRER"
    
    print(f"{color}[{bar}] {percentage:.1f}%{Colors.END}")
    print(f"\nStatut: {color}{status}{Colors.END}\n")
    
    # Prochaines étapes
    if percentage < 100:
        print(f"{Colors.BOLD}PROCHAINES ÉTAPES:{Colors.END}")
        
        if percentage < 20:
            print("  1. Créer structure de fichiers (voir docs/PHASE3_PLAN.md)")
            print("  2. Installer dépendances: pip install -r requirements-phase3.txt")
            print("  3. Commencer par STT (Semaine 1-2)")
        elif percentage < 40:
            print("  1. Compléter module STT + wake word")
            print("  2. Tester transcription audio")
            print("  3. Débuter TTS amélioré")
        elif percentage < 60:
            print("  1. Finaliser TTS + cache")
            print("  2. Implémenter auth vocale")
            print("  3. Débuter connecteur email")
        elif percentage < 80:
            print("  1. Finaliser email + notifications")
            print("  2. Créer pipeline vocal complet")
            print("  3. Tests d'intégration")
        else:
            print("  1. Optimisations performance")
            print("  2. Tests de charge")
            print("  3. Documentation utilisateur")
    else:
        print(f"{Colors.GREEN}✨ PHASE 3 COMPLÈTE ! ✨{Colors.END}")
        print(f"\nProchaine étape: Phase 4 (Fonctionnalités avancées)")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    # Code de sortie
    return 0 if percentage >= 90 else 1

if __name__ == "__main__":
    sys.exit(main())
