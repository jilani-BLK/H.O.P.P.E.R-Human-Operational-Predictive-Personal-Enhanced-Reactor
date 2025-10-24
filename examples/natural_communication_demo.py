"""
Démonstration: Communication Naturelle et Transparente de HOPPER

Ce fichier montre comment HOPPER communique clairement ses actions
à l'utilisateur, en langage naturel, sans jargon technique.
"""

import asyncio
from pathlib import Path
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.communication import (
    ActionNarrator,
    Action,
    ActionType,
    Urgency,
    narrate_file_scan,
    narrate_file_modification,
    narrate_system_command,
    narrate_learning,
    narrate_reasoning
)


def demo_security_scan():
    """Démonstration: Scan de sécurité transparent"""
    print("\n" + "=" * 80)
    print("SCÉNARIO 1: Scan de Sécurité d'un Fichier Suspect")
    print("=" * 80 + "\n")
    
    narrator = ActionNarrator(verbose=True)
    
    # Utilisateur télécharge un fichier
    print("👤 Utilisateur: J'ai reçu ce fichier par email, peux-tu le vérifier ?")
    print()
    
    # HOPPER explique ce qu'il va faire
    narrate_file_scan(narrator, "facture_importante.pdf")
    
    # Simulation du scan
    import time
    print("\n   🔍 Scan en cours...")
    time.sleep(1)
    
    # Résultat expliqué clairement
    print("\n✅ Scan terminé : Aucune menace détectée !")
    print("   Vous pouvez ouvrir ce fichier en toute sécurité.")


def demo_file_modification():
    """Démonstration: Modification de fichier avec approbation"""
    print("\n" + "=" * 80)
    print("SCÉNARIO 2: Modification de Fichier Important")
    print("=" * 80 + "\n")
    
    narrator = ActionNarrator(verbose=True, auto_approve_low_risk=False)
    
    print("👤 Utilisateur: Peux-tu nettoyer les métadonnées de mes photos ?")
    print()
    
    # HOPPER explique l'action ET demande confirmation
    action = Action(
        action_type=ActionType.FILE_OPERATION,
        description="Je vais modifier vos 15 photos",
        reason="pour supprimer les métadonnées sensibles (localisation, appareil photo, etc.)",
        estimated_duration="environ 30 secondes",
        urgency=Urgency.MEDIUM,
        requires_approval=True,
        benefits=[
            "Protection de votre vie privée",
            "Suppression des données de géolocalisation",
            "Suppression des informations sur l'appareil photo"
        ],
        risks=[
            "Les métadonnées seront définitivement supprimées",
            "Certaines applications pourraient ne plus afficher la date de prise de vue"
        ],
        details={
            "files_count": 15,
            "total_size": "24 MB"
        }
    )
    
    narrator.narrate(action)
    
    print("\n✓ Action approuvée (simulation)")
    print("\n   📸 Traitement des photos...")
    import time
    time.sleep(0.5)
    print("   ✅ 15 photos nettoyées avec succès !")
    print("   💾 Copies de sauvegarde créées dans Photos/Backup/")


def demo_reasoning_process():
    """Démonstration: Partage du processus de raisonnement"""
    print("\n" + "=" * 80)
    print("SCÉNARIO 3: Raisonnement Transparent")
    print("=" * 80 + "\n")
    
    narrator = ActionNarrator(verbose=True)
    
    print("👤 Utilisateur: Comment puis-je optimiser mon code Python qui est lent ?")
    print()
    
    # HOPPER partage sa réflexion
    narrator.share_reasoning(
        question="Optimisation de code Python",
        steps=[
            "D'abord, je vais profiler votre code pour identifier les goulots d'étranglement",
            "Ensuite, j'analyserai les boucles et structures de données utilisées",
            "Je vérifierai s'il existe des bibliothèques optimisées pour vos opérations",
            "Enfin, je proposerai des modifications concrètes avec comparaison de performance"
        ],
        conclusion="Je vais commencer par exécuter un profiler sur votre code"
    )
    
    print("\n   🔍 Analyse en cours...\n")
    import time
    time.sleep(0.5)
    
    print("📊 **Résultats du profilage :**")
    print("   • 85% du temps dans la fonction process_data()")
    print("   • Cause: boucle for imbriquée (complexité O(n²))")
    print()
    print("💡 **Ma recommandation :**")
    print("   Remplacer la liste par un dictionnaire pour les recherches.")
    print("   Gain estimé: ~10x plus rapide")
    print()
    print("   Voulez-vous que je fasse cette modification ?")


def demo_uncertainty_communication():
    """Démonstration: Communication honnête des limites"""
    print("\n" + "=" * 80)
    print("SCÉNARIO 4: Transparence sur les Limites")
    print("=" * 80 + "\n")
    
    narrator = ActionNarrator(verbose=True)
    
    print("👤 Utilisateur: Quelles sont les implications juridiques de ce contrat ?")
    print()
    
    # HOPPER est honnête sur ses limitations
    narrator.explain_uncertainty(
        topic="cette question juridique complexe",
        confidence=0.6,  # 60% de confiance
        limitations=[
            "Je ne suis pas un avocat et mes informations sont générales",
            "Le droit des contrats varie selon les pays et régions",
            "Mes connaissances datent de 2023 et les lois ont pu évoluer",
            "Certaines clauses peuvent avoir des interprétations spécifiques"
        ]
    )
    
    print()
    print("📋 **Ce que je peux faire :**")
    print("   • Identifier les clauses standards")
    print("   • Signaler les points qui semblent inhabituels")
    print("   • Vous orienter vers les bonnes questions à poser à un avocat")
    print()
    print("⚖️  **Pour une validation juridique officielle, je vous recommande**")
    print("   **de consulter un avocat spécialisé en droit des contrats.**")


def demo_learning_transparency():
    """Démonstration: Apprentissage transparent"""
    print("\n" + "=" * 80)
    print("SCÉNARIO 5: Apprentissage Continu Transparent")
    print("=" * 80 + "\n")
    
    narrator = ActionNarrator(verbose=True)
    
    print("👤 Utilisateur: [Utilise HOPPER régulièrement pour des tâches Git]")
    print()
    
    # HOPPER explique qu'il apprend
    narrate_learning(
        narrator,
        observation="Vous utilisez fréquemment 'git status' suivi de 'git add'",
        what="vos habitudes Git",
        benefit="Je pourrai vous suggérer des raccourcis et automatisations personnalisées"
    )
    
    print()
    print("💡 **Suggestion basée sur votre utilisation :**")
    print("   Je peux créer un alias 'gs' pour 'git status'")
    print("   et 'ga' pour 'git add' si vous le souhaitez.")
    print()
    print("   Voulez-vous que je configure ces raccourcis ? (oui/non)")


def demo_multi_step_explanation():
    """Démonstration: Explication d'un workflow multi-étapes"""
    print("\n" + "=" * 80)
    print("SCÉNARIO 6: Workflow Multi-Étapes Expliqué")
    print("=" * 80 + "\n")
    
    narrator = ActionNarrator(verbose=True)
    
    print("👤 Utilisateur: Analyse tous mes emails non lus et résume-les")
    print()
    
    # HOPPER explique son plan complet
    action = Action(
        action_type=ActionType.DATA_ANALYSIS,
        description="Je vais analyser vos emails non lus",
        reason="pour créer un résumé personnalisé",
        estimated_duration="1 à 2 minutes",
        urgency=Urgency.MEDIUM,
        details={
            "steps": [
                "Connexion sécurisée à votre boîte email",
                "Récupération des emails non lus (42 trouvés)",
                "Classification par importance et catégorie",
                "Extraction des points clés de chaque email",
                "Génération d'un résumé structuré",
                "Identification des actions urgentes à prendre"
            ]
        },
        benefits=[
            "Gain de temps : pas besoin de lire 42 emails",
            "Priorisation automatique",
            "Aucun email important ne sera manqué"
        ]
    )
    
    narrator.narrate(action)
    
    print("\n   📧 Analyse en cours...")
    import time
    for i, step in enumerate(action.details["steps"], 1):
        time.sleep(0.3)
        print(f"   ✓ Étape {i}/6 : {step}")
    
    print()
    print("📊 **Résumé de vos 42 emails non lus :**")
    print()
    print("🔴 **Urgent (3 emails) :**")
    print("   • Réunion projet client demain 14h (confirmation nécessaire)")
    print("   • Facture à payer avant vendredi")
    print("   • Problème serveur signalé par l'équipe technique")
    print()
    print("🟡 **Important (8 emails) :**")
    print("   • 5 emails projets en cours")
    print("   • 3 demandes de réunion (dates flexibles)")
    print()
    print("⚪ **Informatif (31 emails) :**")
    print("   • 15 newsletters")
    print("   • 12 notifications automatiques")
    print("   • 4 messages de suivi")
    print()
    print("💡 **Actions recommandées :**")
    print("   1. Confirmer votre présence à la réunion de demain")
    print("   2. Traiter la facture en priorité")
    print("   3. Contacter l'équipe technique pour le problème serveur")


def demo_system_command():
    """Démonstration: Commande système avec explication"""
    print("\n" + "=" * 80)
    print("SCÉNARIO 7: Exécution Commande Système")
    print("=" * 80 + "\n")
    
    narrator = ActionNarrator(verbose=True)
    
    print("👤 Utilisateur: Mon disque est plein, peux-tu nettoyer les fichiers temporaires ?")
    print()
    
    # HOPPER explique exactement ce qu'il va faire
    action = Action(
        action_type=ActionType.SYSTEM_COMMAND,
        description="Je vais nettoyer les fichiers temporaires",
        reason="pour libérer de l'espace disque sur votre système",
        estimated_duration="30 secondes à 2 minutes",
        urgency=Urgency.HIGH,
        requires_approval=True,
        details={
            "steps": [
                "Vider le dossier /tmp (fichiers temporaires système)",
                "Supprimer les caches d'applications (~ 2.3 GB)",
                "Nettoyer les logs anciens (> 30 jours)",
                "Vider la corbeille"
            ]
        },
        benefits=[
            "Libération de ~4.5 GB d'espace disque",
            "Amélioration des performances système",
            "Nettoyage sans risque (fichiers temporaires uniquement)"
        ],
        risks=[
            "Certaines applications devront reconstruire leur cache",
            "Les fichiers de la corbeille seront définitivement supprimés"
        ]
    )
    
    narrator.narrate(action)
    
    print("\n✓ Action approuvée (simulation)")
    print("\n   🧹 Nettoyage en cours...")
    import time
    for i, step in enumerate(action.details["steps"], 1):
        time.sleep(0.4)
        print(f"   ✓ {step}")
    
    print()
    print("✅ **Nettoyage terminé avec succès !**")
    print("   💾 Espace libéré : 4.7 GB")
    print("   📊 Espace disponible : 23.4 GB / 256 GB (9%)")


async def main():
    """Fonction principale - Exécute toutes les démonstrations"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "HOPPER - Communication Naturelle et Transparente" + " " * 15 + "║")
    print("║" + " " * 22 + "Démonstration des Capacités" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝")
    
    demos = [
        ("Scan de Sécurité", demo_security_scan),
        ("Modification de Fichier", demo_file_modification),
        ("Raisonnement Transparent", demo_reasoning_process),
        ("Communication des Limites", demo_uncertainty_communication),
        ("Apprentissage Transparent", demo_learning_transparency),
        ("Workflow Multi-Étapes", demo_multi_step_explanation),
        ("Commande Système", demo_system_command),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        print(f"\n\n{'🔹' * 40}")
        print(f"Démo {i}/{len(demos)}: {name}")
        print(f"{'🔹' * 40}")
        
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Erreur dans la démo: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(demos):
            print("\n\n[Appuyez sur Entrée pour continuer...]")
            input()
    
    print("\n\n" + "=" * 80)
    print("RÉSUMÉ DES PRINCIPES DE COMMUNICATION NATURELLE")
    print("=" * 80)
    print("""
✅ **Transparence Totale**
   Chaque action importante est expliquée AVANT exécution

✅ **Langage Simple**
   Pas de jargon technique, communication accessible à tous

✅ **Justification Claire**
   L'utilisateur comprend toujours POURQUOI une action est faite

✅ **Approbation Demandée**
   Actions critiques nécessitent confirmation explicite

✅ **Partage du Raisonnement**
   HOPPER explique son processus de réflexion

✅ **Honnêteté sur les Limites**
   Les incertitudes et limitations sont clairement communiquées

✅ **Bénéfices et Risques**
   L'utilisateur est informé des avantages ET des inconvénients

✅ **Communication Progressive**
   Les workflows multi-étapes sont expliqués étape par étape

🎯 **Objectif Final:** Construire la confiance par la transparence.
                      L'utilisateur ne se demande jamais "Que fait-il ?!"

📚 **Guide Complet:** docs/guides/NATURAL_COMMUNICATION_GUIDE.md
🔧 **Code Source:** src/communication/action_narrator.py
""")


if __name__ == "__main__":
    asyncio.run(main())
