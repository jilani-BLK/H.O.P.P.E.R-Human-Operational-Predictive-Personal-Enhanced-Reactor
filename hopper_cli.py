#!/usr/bin/env python3
"""
HOPPER CLI - Interface en ligne de commande
Supporte: commandes directes, mode interactif, mode repos
"""

import sys
import requests
import time
from typing import Dict, Any, Optional

ORCHESTRATOR_URL = "http://localhost:5050"

def send_command(command: str) -> Dict[str, Any]:
    """Envoie une commande à l'orchestrateur"""
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/api/v1/command",
            json={"command": command},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Impossible de se connecter à HOPPER. Est-il démarré?"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout - la commande a pris trop de temps"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_health() -> bool:
    """Vérifie que HOPPER est accessible"""
    try:
        response = requests.get(f"{ORCHESTRATOR_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def display_result(result: Dict[str, Any], command: str):
    """Affiche le résultat d'une commande"""
    print("\n" + "=" * 70)
    print(f"🎯 Commande: {command}")
    print("=" * 70)
    
    if result.get("success"):
        print("✅ Succès")
        
        if "type" in result:
            print(f"Type: {result['type']}")
        if "action" in result:
            print(f"Action: {result['action']}")
        
        # Réponse LLM ou sortie système
        if "response" in result:
            print(f"\n💬 Réponse:\n{result['response']}")
        elif "output" in result:
            print(f"\n📤 Sortie:\n{result['output']}")
        
        # Métadonnées
        if "duration_ms" in result:
            print(f"\n⏱️  Durée: {result['duration_ms']}ms")
        if "tokens" in result:
            print(f"🔤 Tokens: {result['tokens']}")
    else:
        print("❌ Échec")
        print(f"Erreur: {result.get('error', 'Erreur inconnue')}")
    
    print("=" * 70 + "\n")

def mode_sleep():
    """Mode repos - HOPPER en veille"""
    print("\n💤 HOPPER en mode repos...")
    print("Commande 'hopper repos' détectée")
    print("Simulant mise en veille (placeholder pour future implémentation)")
    print("\n✅ Mode repos activé\n")
    return 0

def mode_interactive():
    """Mode interactif - dialogue continu"""
    print("\n" + "=" * 70)
    print("🤖 HOPPER - Mode Interactif")
    print("=" * 70)
    print("Tapez vos commandes (Ctrl+C ou 'exit' pour quitter)\n")
    
    if not check_health():
        print("❌ Erreur: HOPPER n'est pas accessible")
        print("Démarrez-le avec: docker-compose up -d\n")
        return 1
    
    try:
        while True:
            try:
                command = input("🎯 Vous: ").strip()
            except EOFError:
                break
            
            if not command:
                continue
            
            if command.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Au revoir!\n")
                break
            
            result = send_command(command)
            
            # Affichage simplifié en mode interactif
            if result.get("success"):
                if "response" in result:
                    print(f"🤖 HOPPER: {result['response']}\n")
                elif "output" in result:
                    print(f"📤 Sortie:\n{result['output']}\n")
            else:
                print(f"❌ Erreur: {result.get('error', 'Inconnue')}\n")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interruption - Au revoir!\n")
        return 0
    
    return 0

def mode_command(command: str):
    """Mode commande simple"""
    if not check_health():
        print("\n❌ Erreur: HOPPER n'est pas accessible")
        print("Démarrez-le avec: docker-compose up -d\n")
        return 1
    
    result = send_command(command)
    display_result(result, command)
    
    return 0 if result.get("success") else 1

def main():
    """Point d'entrée principal"""
    args = sys.argv[1:]
    
    # Mode repos
    if "--sleep" in args:
        return mode_sleep()
    
    # Mode interactif
    if "--interactive" in args or len(args) == 0:
        return mode_interactive()
    
    # Mode commande
    command = " ".join(args)
    return mode_command(command)

if __name__ == "__main__":
    sys.exit(main())
