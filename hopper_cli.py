#!/usr/bin/env python3
"""
HOPPER CLI - Interface en ligne de commande (Version Simplifiée)
Utilisation: hopper "votre commande"
Utilisation streaming: hopper --stream "votre commande"
"""

import sys
import argparse
import requests
import json
from pathlib import Path


class HopperCLI:
    """Interface CLI pour HOPPER via l'API"""
    
    def __init__(self, base_url="http://localhost:5050"):
        self.base_url = base_url
    
    def process_command_streaming(self, text: str, user_id: str = "cli_user"):
        """
        Envoie une commande avec streaming de pensées
        
        Args:
            text: Texte de la commande
            user_id: ID utilisateur
        """
        try:
            print(f"\n🤖 HOPPER > {text}")
            print("─" * 60)
            
            response = requests.post(
                f"{self.base_url}/command/stream",
                json={
                    "text": text,
                    "user_id": user_id
                },
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ Erreur HTTP {response.status_code}")
                return {
                    "success": False,
                    "message": f"Erreur HTTP {response.status_code}"
                }
            
            final_response = None
            
            # Lire le flux SSE
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    if line_str.startswith("data: "):
                        # Extraire le JSON
                        json_str = line_str[6:]
                        try:
                            thought = json.loads(json_str)
                            
                            thought_type = thought.get("type", "")
                            message = thought.get("message", "")
                            
                            # Afficher la pensée avec emoji
                            emoji_map = {
                                "analyzing": "🔍",
                                "thinking": "🤔",
                                "searching": "📚",
                                "generating": "💭",
                                "executing": "⚙️",
                                "learning": "📖",
                                "done": "✅",
                                "error": "❌",
                                "response": "💬"
                            }
                            
                            emoji = emoji_map.get(thought_type, "💡")
                            
                            # Afficher selon le type
                            if thought_type == "response":
                                # La réponse finale
                                print("─" * 60)
                                print(f"\n{message}\n")
                                final_response = message
                            elif thought_type == "error":
                                print(f"{emoji} ERREUR: {message}")
                            elif thought_type == "done":
                                # Ne rien afficher pour "done" car on a déjà la réponse
                                pass
                            else:
                                # Pensée intermédiaire
                                print(f"{emoji} {message}")
                                
                        except json.JSONDecodeError:
                            pass
            
            return {
                "success": True,
                "message": final_response or "Commande traitée"
            }
            
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de se connecter à HOPPER")
            return {
                "success": False,
                "message": "Connection error"
            }
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
        
    def process_command(self, text: str, user_id: str = "cli_user"):
        """
        Envoie une commande à l'orchestrateur
        
        Args:
            text: Texte de la commande
            user_id: ID utilisateur
        """
        try:
            response = requests.post(
                f"{self.base_url}/command",
                json={
                    "text": text,
                    "user_id": user_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "message": f"Erreur HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "❌ Impossible de se connecter à HOPPER. L'orchestrateur est-il démarré ?",
                "error": "connection_error"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "❌ Timeout - HOPPER met trop de temps à répondre",
                "error": "timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Erreur: {str(e)}",
                "error": str(e)
            }
    
    def submit_feedback(self, user_id: str, score: int, comment: str | None = None):
        """Soumet un feedback"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/feedback",
                json={
                    "user_id": user_id,
                    "score": score,
                    "comment": comment
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"Erreur {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="HOPPER - Assistant Personnel Intelligent",
        epilog='Exemples:\n'
               '  hopper "Quel temps fait-il à Paris ?"\n'
               '  hopper -i                  # Mode interactif\n'
               '  hopper --feedback 5 "Super !"',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'command',
        nargs='?',
        help='Commande à exécuter'
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Mode interactif'
    )
    parser.add_argument(
        '-s', '--stream',
        action='store_true',
        help='Mode streaming (affiche les pensées de HOPPER en temps réel)'
    )
    parser.add_argument(
        '-u', '--user',
        default='cli_user',
        help='ID utilisateur (défaut: cli_user)'
    )
    parser.add_argument(
        '--url',
        default='http://localhost:5050',
        help='URL de l\'orchestrateur (défaut: http://localhost:5050)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Mode debug (affiche plus de détails)'
    )
    parser.add_argument(
        '--feedback',
        type=int,
        choices=[1, 2, 3, 4, 5],
        help='Soumettre un feedback (score 1-5)'
    )
    
    args = parser.parse_args()
    
    # Créer l'instance CLI
    cli = HopperCLI(base_url=args.url)
    
    # Mode feedback
    if args.feedback:
        result = cli.submit_feedback(
            user_id=args.user,
            score=args.feedback,
            comment=args.command if args.command else None
        )
        
        if result.get("success", True):
            print(f"✅ Feedback {args.feedback}/5 enregistré")
        else:
            print(f"❌ {result.get('message', 'Erreur')}")
        return
    
    # Mode interactif
    if args.interactive:
        print("╔═══════════════════════════════════════════════════════╗")
        print("║       🎙️  HOPPER - Mode Interactif                   ║")
        print("╚═══════════════════════════════════════════════════════╝")
        print()
        print("Tapez vos commandes. Commandes spéciales:")
        print("  • 'exit' ou 'quit' - Quitter")
        print("  • 'feedback N' - Donner un feedback (1-5)")
        print("  • 'help' - Afficher l'aide")
        print()
        
        while True:
            try:
                command = input("🎙️  Vous: ").strip()
                
                if command.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Au revoir !")
                    break
                
                if not command:
                    continue
                
                if command.lower() == 'help':
                    print("\n📖 Commandes disponibles:")
                    print("  • Toute phrase en langage naturel")
                    print("  • feedback N - Donner un feedback (1-5)")
                    print("  • exit/quit - Quitter")
                    print()
                    continue
                
                # Feedback
                if command.lower().startswith('feedback '):
                    try:
                        score = int(command.split()[1])
                        if 1 <= score <= 5:
                            result = cli.submit_feedback(args.user, score)
                            if result.get("success", True):
                                print(f"✅ Feedback {score}/5 enregistré\n")
                            else:
                                print(f"❌ {result.get('message')}\n")
                        else:
                            print("❌ Score doit être entre 1 et 5\n")
                    except (ValueError, IndexError):
                        print("❌ Usage: feedback <1-5>\n")
                    continue
                
                # Traiter la commande normale
                if args.stream:
                    result = cli.process_command_streaming(command, args.user)
                else:
                    result = cli.process_command(command, args.user)
                
                # Afficher la réponse (seulement si pas en mode streaming car déjà affiché)
                if not args.stream:
                    if result.get("success"):
                        print(f"🤖 HOPPER: {result.get('message', '')}")
                        
                        if args.debug and result.get("data"):
                            print(f"   📊 Données: {json.dumps(result['data'], indent=2)}")
                        
                        if result.get("actions"):
                            print(f"   ⚡ Actions: {', '.join(result['actions'])}")
                        
                        # Feedback demandé ?
                    if result.get("data", {}).get("feedback_requested"):
                        print(f"\n💭 {result['data'].get('feedback_prompt', 'Comment était cette interaction ?')}")
                        print("   Tapez: feedback <1-5>")
                else:
                    print(f"❌ {result.get('message', 'Erreur inconnue')}")
                
                print()  # Ligne vide
                
            except KeyboardInterrupt:
                print("\n\n👋 Au revoir !")
                break
            except EOFError:
                print("\n\n👋 Au revoir !")
                break
    
    elif args.command:
        # Mode commande unique
        if args.stream:
            result = cli.process_command_streaming(args.command, args.user)
        else:
            result = cli.process_command(args.command, args.user)
        
        # Afficher la réponse (seulement si pas en streaming car déjà affiché)
        if not args.stream:
            if result.get("success"):
                print(f"{result.get('message', '')}")
                
                if args.debug:
                    if result.get("data"):
                        print(f"\n📊 Données: {json.dumps(result['data'], indent=2)}")
                    if result.get("actions"):
                        print(f"⚡ Actions: {', '.join(result['actions'])}")
                
                # Feedback demandé ?
                if result.get("data", {}).get("feedback_requested"):
                    print(f"\n💭 {result['data'].get('feedback_prompt')}")
                    print(f"   Donnez votre avis: hopper --feedback <1-5>")
            else:
                print(f"{result.get('message', 'Erreur inconnue')}")
                sys.exit(1)
        else:
            # En mode streaming, vérifier si la commande a réussi
            if not result.get("success"):
                sys.exit(1)
    
    else:
        # Aucune commande
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interruption - Au revoir !")
        sys.exit(0)
