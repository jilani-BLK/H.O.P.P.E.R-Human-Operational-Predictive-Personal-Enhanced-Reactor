#!/usr/bin/env python3
"""
Test complet de détection des patterns System Tools
"""

import re


# Copie COMPLÈTE des patterns de system_integration.py
# NOTE: L'ordre est important !
PATTERNS = {
    # Fichiers EN PREMIER pour éviter conflit avec open_app
    "read_file": [
        r"(?:lis|lire|affiche|afficher|montre(?:-moi)?|montrer)\s+(?:le\s+)?(?:fichier\s+)?['\"]?([^'\"]+\.[a-z0-9]{2,4})['\"]?",
        r"(?:lis|lire|affiche|afficher|montre(?:-moi)?|montrer)\s+(?:le\s+)?fichier\s+['\"]?([^'\"]+)['\"]?",
        r"(?:read|show|display)\s+(?:file\s+)?['\"]?([^'\"]+\.[a-z0-9]{2,4})['\"]?",
        r"(?:ouvre|ouvrir)\s+(?:le\s+)?fichier\s+['\"]?([^'\"]+)['\"]?"
    ],
    "open_app": [
        r"(?:ouvre|démarre|ouvrir|démarrer)\s+(?!le\s+fichier|fichier|la\s+porte|les?\s)([A-Z][A-Za-z0-9\s]{1,30}?)(?:\?|!|\.|$)",
        r"(?:lance|lancer)\s+(?!la\s+commande)(?:l'application\s+)?([A-Z][A-Za-z0-9\s]{1,30}?)(?:\?|!|\.|$)",
        r"(?:open|start)\s+(?:the\s+)?([A-Z][A-Za-z0-9\s]{1,30}?)(?:\?|!|\.|$)"
    ],
    "close_app": [
        r"(?:ferme|fermer|quitte|quitter)\s+(?:l'application\s+)?(.+)",
        r"(?:close|quit)\s+(.+)"
    ],
    "list_apps": [
        r"(?:liste|lister|affiche|afficher)\s+(?:mes\s+)?(?:les\s+)?(?:applications?|apps?)",
        r"(?:montre|montrer)(?:-moi)?\s+(?:les\s+)?(?:applications?|apps?)(?:\s+install)?",
        r"(?:list|show)\s+(?:my\s+)?(?:applications?|apps?)",
        r"quelles?\s+(?:applications?|apps?).*(?:install|disponible)"
    ],
    "list_directory": [
        r"(?:liste|lister|affiche|afficher)\s+(?:le\s+)?(?:contenu\s+(?:du\s+)?)?(?:dossier|répertoire|directory)\s+(.+)",
        r"(?:list|show)\s+(?:directory|folder)\s+(.+)"
    ],
    "find_files": [
        r"(?:cherche|chercher|trouve|trouver|recherche|rechercher)\s+(?:des\s+)?fichiers?\s+(.+)",
        r"(?:find|search)\s+files?\s+(.+)"
    ],
    "get_system_info": [
        r"(?:infos?|informations?)\s+(?:du\s+|de\s+(?:la\s+)?)?(?:système|machine|ordinateur)",
        r"(?:system|machine|computer)\s+info",
        r"état\s+(?:de\s+)?(?:la\s+)?(?:machine|système)"
    ],
    "execute_script": [
        r"(?:exécute|exécuter)\s+(?:la\s+commande\s+)?['\"]?(.+)['\"]?",
        r"(?:lance|lancer)\s+(?:la\s+commande)\s+['\"]?(.+)['\"]?",
        r"(?:execute|run)\s+['\"]?(.+)['\"]?"
    ]
}


def test_detection(text: str):
    """Tester détection"""
    print(f"\n📝 Texte: '{text}'")
    
    for action, patterns in PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                print(f"   ✅ Détecté: {action}")
                if match.groups():
                    print(f"      Paramètres: {match.groups()}")
                return action
    
    print(f"   ❌ Aucune action détectée")
    return None


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Test de détection des patterns System Tools              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    test_cases = [
        # Applications - OPEN
        ("ouvre TextEdit", "open_app"),
        ("lance l'application VS Code", "open_app"),
        ("peux-tu ouvrir Safari?", "open_app"),
        
        # Applications - LIST
        ("liste mes applications", "list_apps"),
        ("montre-moi les apps installées", "list_apps"),
        ("quelles applications sont disponibles?", "list_apps"),
        
        # Applications - CLOSE
        ("ferme Safari", "close_app"),
        ("quitte l'application TextEdit", "close_app"),
        
        # Fichiers - READ
        ("lis le fichier README.md", "read_file"),
        ("affiche config.json", "read_file"),
        ("montre-moi test.py", "read_file"),
        ("ouvre le fichier settings.json", "read_file"),
        
        # Fichiers - LIST DIRECTORY
        ("liste le contenu du dossier src", "list_directory"),
        ("affiche le répertoire /tmp", "list_directory"),
        
        # Fichiers - FIND
        ("cherche des fichiers Python", "find_files"),
        ("trouve fichiers .js", "find_files"),
        ("recherche fichiers test", "find_files"),
        
        # Système - INFO
        ("donne-moi les infos système", "get_system_info"),
        ("infos de la machine", "get_system_info"),
        ("system info please", "get_system_info"),
        
        # Système - EXECUTE
        ("exécute ls -la", "execute_script"),
        ("lance la commande echo hello", "execute_script"),
        
        # Négatifs (ne devraient rien détecter)
        ("bonjour comment vas-tu?", None),
        ("explique-moi Python", None),
        ("ouvre la porte", None),  # "ouvre" mais pas une app
        ("liste les avantages", None),  # "liste" mais pas apps/dossier
    ]
    
    passed = 0
    failed = 0
    
    for text, expected in test_cases:
        detected = test_detection(text)
        
        if detected == expected:
            print(f"      ✅ CORRECT (attendu: {expected})")
            passed += 1
        else:
            print(f"      ❌ INCORRECT (attendu: {expected}, obtenu: {detected})")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"RÉSULTATS: ✅ {passed} réussis, ❌ {failed} échoués")
    print(f"{'='*60}")
