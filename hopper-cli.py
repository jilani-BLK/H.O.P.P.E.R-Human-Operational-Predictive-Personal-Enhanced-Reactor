#!/usr/bin/env python3
"""
HOPPER CLI - Interface en ligne de commande
Permet d'interagir avec l'assistant depuis le terminal
"""

import sys
import argparse
import requests
import json
from typing import Optional

# Configuration
ORCHESTRATOR_URL = "http://localhost:5000"


class HopperCLI:
    """Interface CLI pour HOPPER"""
    
    def __init__(self, base_url: str = ORCHESTRATOR_URL):
        self.base_url = base_url
        self.user_id = "cli_user"
    
    def send_command(self, text: str, voice: bool = False) -> dict:
        """
        Envoie une commande à HOPPER
        
        Args:
            text: Texte de la commande
            voice: Si True, utilise l'entrée vocale
            
        Returns:
            Réponse de l'assistant
        """
        url = f"{self.base_url}/command"
        
        payload = {
            "text": text,
            "user_id": self.user_id,
            "voice_input": voice
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Erreur de connexion: {str(e)}"
            }
    
    def check_health(self) -> dict:
        """Vérifie l'état de santé du système"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "unreachable", "error": str(e)}
    
    def get_capabilities(self) -> dict:
        """Récupère les capacités de HOPPER"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/capabilities", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def interactive_mode(self):
        """Mode interactif"""
        print("╔════════════════════════════════════════════════╗")
        print("║         HOPPER - Assistant Personnel          ║")
        print("║    Human Operational Predictive Personal      ║")
        print("║            Enhanced Reactor                    ║")
        print("╚════════════════════════════════════════════════╝")
        print()
        print("Mode interactif activé. Tapez 'quit' pour quitter.")
        print("Commandes spéciales:")
        print("  /health  - Vérifier l'état du système")
        print("  /clear   - Effacer le contexte")
        print("  /help    - Afficher l'aide")
        print()
        
        while True:
            try:
                user_input = input("Vous: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Au revoir!")
                    break
                
                if user_input == '/health':
                    health = self.check_health()
                    print(f"\n🏥 État du système: {json.dumps(health, indent=2)}\n")
                    continue
                
                if user_input == '/clear':
                    # TODO: Implémenter l'effacement du contexte
                    print("\n✅ Contexte effacé\n")
                    continue
                
                if user_input == '/help':
                    self.show_help()
                    continue
                
                # Envoi de la commande
                print("🤔 Traitement...", end='\r')
                result = self.send_command(user_input)
                
                print(" " * 50, end='\r')  # Efface le message "Traitement..."
                
                if result.get("success"):
                    print(f"HOPPER: {result['message']}")
                    
                    if result.get("actions_taken"):
                        print(f"   └─ Actions: {', '.join(result['actions_taken'])}")
                else:
                    print(f"❌ {result.get('message', 'Erreur inconnue')}")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"\n❌ Erreur: {str(e)}\n")
    
    def show_help(self):
        """Affiche l'aide"""
        print("""
╔════════════════════════════════════════════════╗
║                   AIDE HOPPER                  ║
╚════════════════════════════════════════════════╝

Exemples de commandes:

📁 Fichiers et système:
  • "Crée un fichier test.txt"
  • "Ouvre l'application Calculatrice"
  • "Liste les fichiers du répertoire Documents"

💬 Questions générales:
  • "Quelle est la capitale de la France?"
  • "Explique-moi le machine learning"
  • "Résume ce document"

📧 Emails (Phase 2):
  • "Lis mes nouveaux emails"
  • "Réponds à l'email de Jean"

🏠 Contrôle IoT (Phase 2):
  • "Allume les lumières du salon"
  • "Baisse le chauffage"

Commandes système:
  /health  - État des services
  /clear   - Effacer le contexte
  /help    - Cette aide
  quit     - Quitter

Pour plus d'informations: docs/README.md
        """)


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="HOPPER - Assistant Personnel Intelligent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "command",
        nargs="*",
        help="Commande à exécuter (mode direct)"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Mode interactif"
    )
    
    parser.add_argument(
        "--health",
        action="store_true",
        help="Vérifier l'état du système"
    )
    
    parser.add_argument(
        "--url",
        default=ORCHESTRATOR_URL,
        help=f"URL de l'orchestrateur (défaut: {ORCHESTRATOR_URL})"
    )
    
    args = parser.parse_args()
    
    cli = HopperCLI(base_url=args.url)
    
    # Mode health check
    if args.health:
        health = cli.check_health()
        print(json.dumps(health, indent=2))
        sys.exit(0 if health.get("status") == "healthy" else 1)
    
    # Mode interactif
    if args.interactive or not args.command:
        cli.interactive_mode()
        sys.exit(0)
    
    # Mode commande directe
    command_text = " ".join(args.command)
    result = cli.send_command(command_text)
    
    if result.get("success"):
        print(result["message"])
        sys.exit(0)
    else:
        print(f"❌ {result.get('message', 'Erreur')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
