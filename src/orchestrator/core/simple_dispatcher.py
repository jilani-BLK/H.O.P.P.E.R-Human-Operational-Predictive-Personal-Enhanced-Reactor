"""
HOPPER - Simple Dispatcher (Phase 1)
Dispatcher basique utilisant des mots-clés pour router les commandes

Ce dispatcher est volontairement simple pour la Phase 1.
Il sera remplacé par un dispatcher intelligent avec LLM en Phase 2.
"""

from typing import Dict, Any, Optional, Tuple
from loguru import logger
import re


class SimpleDispatcher:
    """
    Dispatcher basique pour Phase 1
    Route les commandes vers les bons services selon des mots-clés
    """
    
    # Mots-clés pour chaque type d'action
    ACTION_KEYWORDS = {
        "list": ["liste", "affiche", "montre", "voir", "ls"],
        "create": ["crée", "créer", "nouveau", "touch", "ajoute"],
        "open": ["ouvre", "ouvrir", "lance", "lancer", "démarre", "démarrer", "open"],
        "read": ["lis", "lire", "cat", "contenu"],
        "info": ["date", "heure", "pwd", "répertoire", "donne"],
    }
    
    # Services cibles par type d'action
    ACTION_TO_SERVICE = {
        "list": "system_executor",
        "create": "system_executor",
        "open": "system_executor",
        "read": "system_executor",
        "info": "system_executor",
    }
    
    def __init__(self):
        logger.info("🎯 SimpleDispatcher initialisé (Phase 1)")
    
    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        Parse une commande simple et extrait l'intention
        
        Args:
            command: Commande en langage naturel
            
        Returns:
            Dict avec action, target, service, etc.
        """
        command_lower = command.lower().strip()
        
        # Détecter l'action
        action = self._detect_action(command_lower)
        
        if not action:
            return {
                "success": False,
                "error": "Action non reconnue",
                "command": command
            }
        
        # Extraire la cible (fichier, dossier, etc.)
        target = self._extract_target(command)
        
        # Déterminer le service
        service = self.ACTION_TO_SERVICE.get(action, "system_executor")
        
        # Construire la commande système
        system_command = self._build_system_command(action, target, command)
        
        return {
            "success": True,
            "action": action,
            "target": target,
            "service": service,
            "system_command": system_command,
            "original_command": command
        }
    
    def _detect_action(self, command: str) -> Optional[str]:
        """Détecte l'action à partir des mots-clés"""
        for action, keywords in self.ACTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in command:
                    return action
        return None
    
    def _extract_target(self, command: str) -> Optional[str]:
        """Extrait la cible de la commande (fichier, dossier, etc.)"""
        
        # Chercher un nom de fichier/dossier
        # Pattern : mot après "fichier", "dossier", etc.
        patterns = [
            r'fichier\s+([^\s]+)',
            r'dossier\s+([^\s]+)',
            r'répertoire\s+([^\s]+)',
            r'application\s+([^\s]+)',
            r'/[^\s]+',  # Chemin absolu
            r'[a-zA-Z0-9_.-]+\.[a-z]+',  # Fichier avec extension
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                if pattern.startswith('/'):
                    return match.group(0)  # Chemin complet
                else:
                    return match.group(1)  # Groupe capturé
        
        return None
    
    def _build_system_command(self, action: str, target: Optional[str], command: str) -> Dict[str, Any]:
        """
        Construit la commande système à exécuter
        
        Args:
            action: Action détectée
            target: Cible extraite
            command: Commande originale (pour context supplémentaire)
            
        Returns:
            Dict avec command, args, cwd
        """
        
        # Mapping action → commande
        if action == "list":
            if target and target.startswith('/'):
                # Chemin absolu
                return {
                    "command": "ls",
                    "args": ["-lh", target],
                    "cwd": None
                }
            elif target:
                # Chemin relatif
                return {
                    "command": "ls",
                    "args": ["-lh", target],
                    "cwd": "/tmp"
                }
            else:
                # Liste répertoire courant
                return {
                    "command": "ls",
                    "args": ["-lh"],
                    "cwd": "/tmp"
                }
        
        elif action == "create":
            if target:
                # Créer dans /tmp pour Phase 1
                filepath = f"/tmp/{target}" if not target.startswith('/') else target
                return {
                    "command": "touch",
                    "args": [filepath],
                    "cwd": None
                }
            else:
                return {
                    "command": "touch",
                    "args": ["/tmp/hopper_test.txt"],
                    "cwd": None
                }
        
        elif action == "open":
            if target:
                # macOS : open -a Application
                if '.' not in target:
                    # Nom d'application
                    return {
                        "command": "open",
                        "args": ["-a", target],
                        "cwd": None
                    }
                else:
                    # Fichier
                    return {
                        "command": "open",
                        "args": [target],
                        "cwd": "/tmp"
                    }
            return {"command": "echo", "args": ["No target specified"], "cwd": None}
        
        elif action == "read":
            if target:
                filepath = f"/tmp/{target}" if not target.startswith('/') else target
                return {
                    "command": "cat",
                    "args": [filepath],
                    "cwd": None
                }
            return {"command": "echo", "args": ["No file specified"], "cwd": None}
        
        elif action == "info":
            # Commandes d'information
            if "date" in command or "heure" in command:
                return {
                    "command": "date",
                    "args": [],
                    "cwd": None
                }
            elif "pwd" in command or "répertoire" in command or "dossier" in command:
                return {
                    "command": "pwd",
                    "args": [],
                    "cwd": "/tmp"
                }
        
        return {"command": "echo", "args": ["Unknown command"], "cwd": None}
    
    def dispatch(self, command: str) -> Dict[str, Any]:
        """
        Point d'entrée principal : parse et route la commande
        
        Args:
            command: Commande en langage naturel
            
        Returns:
            Dict avec le résultat du parsing et le routage
        """
        logger.info(f"📥 Commande reçue : {command}")
        
        # Parser la commande
        parsed = self.parse_command(command)
        
        if not parsed.get("success"):
            logger.warning(f"⚠️  Parsing échoué : {parsed.get('error')}")
            return parsed
        
        logger.info(f"✅ Action détectée : {parsed['action']}")
        logger.info(f"🎯 Cible : {parsed.get('target', 'N/A')}")
        logger.info(f"🔀 Service : {parsed['service']}")
        
        return parsed


# Instance globale pour l'orchestrator
dispatcher = SimpleDispatcher()


if __name__ == "__main__":
    # Tests du dispatcher
    print("=" * 70)
    print("🧪 Test du SimpleDispatcher")
    print("=" * 70)
    print()
    
    test_commands = [
        "liste les fichiers du dossier /tmp",
        "crée un fichier test.txt",
        "ouvre le fichier demo.txt",
        "affiche la date",
        "ouvre l'application Calculator",
    ]
    
    for cmd in test_commands:
        print(f"\n📝 Commande : {cmd}")
        result = dispatcher.dispatch(cmd)
        print(f"   Action : {result.get('action')}")
        print(f"   Cible : {result.get('target')}")
        print(f"   Commande système : {result.get('system_command')}")
        print()
