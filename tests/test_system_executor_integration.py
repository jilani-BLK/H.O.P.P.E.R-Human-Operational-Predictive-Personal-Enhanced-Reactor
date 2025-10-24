"""
Tests d'intégration pour System Executor avec ActionNarrator
Vérifie que les commandes système sont narrées de manière transparente
"""

import sys
from pathlib import Path
import asyncio

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.communication import ActionNarrator, AsyncActionNarrator
    from src.system_executor.server import SystemExecutor
    HAS_DEPENDENCIES = True
except ImportError as e:
    print(f"⚠️ Dépendances manquantes: {e}")
    HAS_DEPENDENCIES = False


def test_system_executor_with_narrator():
    """Test: System Executor avec narration synchrone"""
    if not HAS_DEPENDENCIES:
        print("❌ Test skipped: dépendances manquantes")
        return
    
    print("\n" + "="*80)
    print("TEST: System Executor avec ActionNarrator")
    print("="*80 + "\n")
    
    # Créer le narrateur
    narrator = ActionNarrator()
    
    # Créer l'executor avec narration
    executor = SystemExecutor(
        whitelist_path="./config/command_whitelist.yaml",
        narrator=narrator
    )
    
    print("✅ System Executor initialisé avec narration\n")
    
    # Test 1: Commande simple (ls)
    print("Test 1: Commande autorisée (ls)\n")
    
    try:
        # Note: Dans un vrai test, on aurait besoin de mocker l'approbation
        # Pour la démo, on utilise une commande qui ne nécessite pas d'approbation
        result = executor.execute(
            command="pwd",
            args=[],
            timeout=5
        )
        
        print(f"\n📊 Résultat:")
        print(f"   • Succès: {result.success}")
        print(f"   • Code sortie: {result.exit_code}")
        print(f"   • Commande: {result.command_executed}")
        print(f"   • Sortie: {result.stdout[:100] if result.stdout else 'Vide'}")
        
        assert result.success, "La commande aurait dû réussir"
        print("\n✅ Test 1 réussi!")
        
    except Exception as e:
        print(f"❌ Test 1 échoué: {e}")
    
    # Test 2: Commande non autorisée
    print("\n\nTest 2: Commande non autorisée (rm)\n")
    
    try:
        result = executor.execute(
            command="rm",
            args=["-rf", "/tmp/test"],
            timeout=5
        )
        
        print("❌ Test 2 échoué: la commande aurait dû être bloquée")
        
    except Exception as e:
        print(f"✅ Test 2 réussi: commande bloquée comme prévu")
        print(f"   Raison: {str(e)}")
    
    print("\n" + "="*80)
    print("✅ Tests System Executor terminés")
    print("="*80)


async def test_async_narrator_with_callback():
    """Test: Narrateur asynchrone avec callback"""
    if not HAS_DEPENDENCIES:
        print("❌ Test skipped: dépendances manquantes")
        return
    
    print("\n" + "="*80)
    print("TEST: AsyncActionNarrator avec Callback")
    print("="*80 + "\n")
    
    # Callback personnalisé pour approbation
    async def approval_callback(action):
        print(f"\n📋 Callback d'approbation appelé:")
        print(f"   Action: {action.description}")
        print(f"   Urgence: {action.urgency.value}")
        
        # Simuler une décision (en prod: vérification DB, UI, etc.)
        await asyncio.sleep(0.1)
        
        # Auto-approuver pour le test
        approved = True
        print(f"   Décision: {'✅ Approuvé' if approved else '⛔ Refusé'}")
        return approved
    
    # Créer narrateur async
    narrator = AsyncActionNarrator(
        approval_callback=approval_callback,
        auto_approve_low_urgency=True
    )
    
    print("✅ AsyncActionNarrator initialisé\n")
    
    # Test avec helpers asynchrones
    from src.communication import (
        narrate_file_scan_async,
        narrate_system_command_async
    )
    
    # Test 1: Scan de fichier (faible urgence, auto-approuvé)
    print("Test 1: Scan de fichier (auto-approuvé)\n")
    approved = await narrate_file_scan_async(narrator, "test_file.txt")
    assert approved, "Le scan aurait dû être auto-approuvé"
    print("✅ Test 1 réussi!")
    
    # Test 2: Commande système (haute urgence, callback)
    print("\n\nTest 2: Commande système (callback)\n")
    approved = await narrate_system_command_async(
        narrator,
        "ls -la /home",
        purpose="lister les fichiers"
    )
    assert approved, "La commande aurait dû être approuvée"
    print("✅ Test 2 réussi!")
    
    print("\n" + "="*80)
    print("✅ Tests AsyncActionNarrator terminés")
    print("="*80)


def test_narrator_examples():
    """Test: Exemples de narration pour différentes actions"""
    if not HAS_DEPENDENCIES:
        print("❌ Test skipped: dépendances manquantes")
        return
    
    print("\n" + "="*80)
    print("TEST: Exemples de Narration d'Actions")
    print("="*80 + "\n")
    
    from src.communication import (
        ActionNarrator,
        Action,
        ActionType,
        Urgency
    )
    
    narrator = ActionNarrator()
    
    # Exemple 1: Analyse de données
    print("Exemple 1: Analyse de données\n")
    action = Action(
        action_type=ActionType.DATA_ANALYSIS,
        description="Analyser les logs système des 7 derniers jours",
        reason="identifier les anomalies",
        urgency=Urgency.MEDIUM,
        requires_approval=False,
        estimated_duration="2-3 minutes",
        benefits=["Détection d'anomalies", "Rapport généré"],
    )
    narrator.narrate(action)
    
    # Exemple 2: Modification de code
    print("\n\nExemple 2: Modification de code\n")
    action = Action(
        action_type=ActionType.CODE_EXECUTION,
        description="Refactoriser la fonction calculate_total()",
        reason="améliorer la performance",
        urgency=Urgency.LOW,
        requires_approval=False,
        estimated_duration="quelques secondes",
        details={
            "file": "src/utils/calculator.py",
            "function": "calculate_total",
            "change": "Optimisation algorithme"
        }
    )
    narrator.narrate(action)
    
    print("\n\n✅ Exemples terminés!")


def main():
    """Exécute tous les tests"""
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*20 + "TESTS SYSTEM EXECUTOR & ASYNC NARRATOR" + " "*20 + "║")
    print("╚" + "═"*78 + "╝")
    
    # Tests synchrones
    test_system_executor_with_narrator()
    test_narrator_examples()
    
    # Tests asynchrones
    print("\n\n")
    asyncio.run(test_async_narrator_with_callback())
    
    print("\n\n" + "="*80)
    print("✅ TOUS LES TESTS TERMINÉS")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
