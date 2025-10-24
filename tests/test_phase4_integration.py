"""
Test d'intégration Phase 4 - Learning Middleware
Vérifie que tout fonctionne ensemble
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from learning.preferences.preferences_manager import PreferencesManager
from learning.fine_tuning.conversation_collector import ConversationCollector
from learning.feedback.feedback_manager import FeedbackManager


def test_preferences():
    """Test du gestionnaire de préférences"""
    print("\n" + "="*70)
    print("TEST 1: Gestionnaire de Préférences")
    print("="*70)
    
    manager = PreferencesManager()
    print(f"✅ Preferences chargées")
    print(f"   Mode nuit: {manager.is_night_mode_active()}")
    print(f"   Verbosité: {manager.get_verbosity_level()}")
    
    # Test notification
    should_notify = manager.should_notify(priority="urgent", content="URGENT problème")
    print(f"   Notification urgente: {should_notify}")
    
    # Test confirmation
    needs_confirm = manager.requires_confirmation("rm -rf /")
    print(f"   Confirmation rm: {needs_confirm}")
    
    return True


def test_collector():
    """Test du collecteur de conversations"""
    print("\n" + "="*70)
    print("TEST 2: Collecteur de Conversations")
    print("="*70)
    
    collector = ConversationCollector()
    
    # Démarrer une conversation
    conv_id = collector.start_conversation()
    print(f"✅ Conversation démarrée: {conv_id}")
    
    # Ajouter quelques tours
    collector.add_turn(
        user_input="Quel temps fait-il à Paris ?",
        assistant_response="Il fait 15°C avec quelques nuages à Paris.",
        intent="weather",
        satisfaction_score=5,
        context={"time_of_day": "morning"}
    )
    
    collector.add_turn(
        user_input="Et demain ?",
        assistant_response="Demain il fera 18°C avec du soleil.",
        satisfaction_score=5,
        context={"time_of_day": "morning"}
    )
    
    print(f"✅ 2 tours ajoutés")
    
    # Stats
    stats = collector.get_statistics()
    print(f"   Conversations: {stats['total_conversations']}")
    print(f"   Tours moyens: {stats['avg_turns_per_conversation']:.1f}")
    print(f"   Satisfaction: {stats['avg_satisfaction']:.2f}/5")
    
    return True


def test_feedback():
    """Test du gestionnaire de feedback"""
    print("\n" + "="*70)
    print("TEST 3: Gestionnaire de Feedback")
    print("="*70)
    
    manager = FeedbackManager()
    
    # Ajouter quelques feedbacks
    manager.add_feedback(
        score=5,
        comment="Excellent, très rapide !",
        context="morning",
        interaction_type="chat",
        response_time_ms=250
    )
    
    manager.add_feedback(
        score=4,
        comment="Bien mais un peu lent",
        context="afternoon",
        interaction_type="chat",
        response_time_ms=1200
    )
    
    manager.add_feedback(
        score=2,
        comment="N'a pas compris ma demande",
        context="evening",
        interaction_type="chat",
        response_time_ms=300,
        error_occurred=False
    )
    
    print(f"✅ 3 feedbacks ajoutés")
    
    # Stats quotidiennes
    daily = manager.get_daily_summary()
    print(f"   Score moyen: {daily['avg_score']:.1f}/5")
    print(f"   Satisfaction: {daily['satisfaction_rate']:.0f}%")
    if 'avg_response_time_ms' in daily and daily['avg_response_time_ms'] is not None:
        print(f"   Temps réponse: {daily['avg_response_time_ms']:.0f}ms")
    
    # Demande feedback
    should_ask = manager.should_request_feedback()
    print(f"   Demander feedback: {should_ask}")
    
    if should_ask:
        prompt = manager.get_feedback_prompt()
        print(f"   Prompt: {prompt}")
    
    return True


def test_integration():
    """Test d'intégration complète"""
    print("\n" + "="*70)
    print("TEST 4: Intégration Complète")
    print("="*70)
    
    # Simuler une session utilisateur
    preferences = PreferencesManager()
    collector = ConversationCollector()
    feedback_mgr = FeedbackManager()
    
    print("✅ Composants initialisés")
    
    # Scénario: Utilisateur pose une question
    user_input = "Envoie un email à Jean avec sujet 'Réunion demain'"
    
    # 1. Vérifier si confirmation nécessaire
    needs_confirm = preferences.requires_confirmation(user_input)
    print(f"   Confirmation requise: {needs_confirm}")
    
    # 2. Traiter (simulé)
    assistant_response = "Confirmation requise: envoyer email à Jean ?"
    
    # 3. Collecter l'interaction
    collector.add_turn(
        user_input=user_input,
        assistant_response=assistant_response,
        intent="send_email",
        satisfaction_score=None,  # Pas encore évalué
        context={"time_of_day": "afternoon", "user_id": "test_user"}
    )
    print(f"✅ Interaction collectée")
    
    # 4. Vérifier notification
    should_notify = preferences.should_notify(
        priority="medium",
        content="Confirmation requise"
    )
    print(f"   Notification envoyée: {should_notify}")
    
    # 5. Feedback utilisateur
    feedback_mgr.add_feedback(
        score=4,
        comment="Bien, mais j'aimerais plus de détails",
        context="afternoon",
        interaction_type="command",
        response_time_ms=500
    )
    print(f"✅ Feedback enregistré")
    
    # 6. Stats finales
    conv_stats = collector.get_statistics()
    feedback_stats = feedback_mgr.get_daily_summary()
    
    print(f"\n   📊 RÉSULTATS:")
    print(f"      Conversations: {conv_stats['total_conversations']}")
    print(f"      Feedback moyen: {feedback_stats['avg_score']:.1f}/5")
    if 'avg_response_time_ms' in feedback_stats and feedback_stats['avg_response_time_ms'] is not None:
        print(f"      Temps réponse: {feedback_stats['avg_response_time_ms']:.0f}ms")
    
    return True


def main():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("   🧪 TESTS D'INTÉGRATION PHASE 4 - LEARNING MIDDLEWARE")
    print("="*70)
    
    tests = [
        ("Préférences", test_preferences),
        ("Collecteur", test_collector),
        ("Feedback", test_feedback),
        ("Intégration", test_integration)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    # Résumé
    print("\n" + "="*70)
    print("   📊 RÉSUMÉ DES TESTS")
    print("="*70)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for name, result, error in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
        if error:
            print(f"      Erreur: {error}")
    
    print(f"\n   Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n   🎉 TOUS LES TESTS PASSENT ! Phase 4 opérationnelle !")
        return 0
    else:
        print("\n   ⚠️  Certains tests ont échoué")
        return 1


if __name__ == "__main__":
    sys.exit(main())
