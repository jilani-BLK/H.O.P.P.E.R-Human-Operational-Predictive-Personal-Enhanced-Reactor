#!/usr/bin/env python3
"""
Tests de validation rapides pour le système d'apprentissage adaptatif
"""

import sys
from pathlib import Path

# Ajouter au path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test: Tous les imports fonctionnent"""
    print("Test 1: Imports...")
    try:
        from src.learning import (
            AdaptiveLearningSystem,
            MemoryManager, MemoryType,
            AdaptivePreferenceManager, PreferenceCategory,
            FeedbackSystem, FeedbackType,
            AdaptationEngine, ContextType,
            KnowledgeBase, KnowledgeType,
            ValidationSystem, ValidationType
        )
        print("  ✓ Tous les imports réussis")
        return True
    except Exception as e:
        print(f"  ✗ Erreur d'import: {e}")
        return False

def test_memory_manager():
    """Test: MemoryManager fonctionne"""
    print("\nTest 2: MemoryManager...")
    try:
        from src.learning import MemoryManager, MemoryType, MemoryQuery
        
        manager = MemoryManager("data/test_memory")
        
        # Ajouter mémoire
        memory = manager.add_memory(
            "Test de mémoire",
            MemoryType.CONVERSATION,
            importance=0.8,
            tags=["test"]
        )
        
        # Rechercher
        results = manager.search(MemoryQuery(query="test"))
        
        assert len(results) > 0, "Aucun résultat"
        assert results[0].memory.content == "Test de mémoire"
        
        print("  ✓ MemoryManager fonctionne")
        return True
    except Exception as e:
        print(f"  ✗ Erreur MemoryManager: {e}")
        return False

def test_preference_manager():
    """Test: PreferenceManager fonctionne"""
    print("\nTest 3: PreferenceManager...")
    try:
        from src.learning import AdaptivePreferenceManager, PreferenceCategory
        
        manager = AdaptivePreferenceManager("data/test_prefs.json")
        
        # Observer interaction
        manager.observe_interaction({
            "response_length": 500,
            "topic": "test"
        })
        
        # Config
        config = manager.get_adaptation_config()
        
        assert "detail_level" in config
        
        print("  ✓ PreferenceManager fonctionne")
        return True
    except Exception as e:
        print(f"  ✗ Erreur PreferenceManager: {e}")
        return False

def test_feedback_system():
    """Test: FeedbackSystem fonctionne"""
    print("\nTest 4: FeedbackSystem...")
    try:
        from src.learning import FeedbackSystem, FeedbackType
        
        system = FeedbackSystem("data/test_feedback")
        
        # Soumettre feedback
        fb_id = system.submit_feedback(
            interaction_id="test_001",
            prompt="Question test",
            response="Réponse test",
            feedback_type=FeedbackType.POSITIVE,
            comment="Bon"
        )
        
        assert fb_id is not None
        
        print("  ✓ FeedbackSystem fonctionne")
        return True
    except Exception as e:
        print(f"  ✗ Erreur FeedbackSystem: {e}")
        return False

def test_adaptation_engine():
    """Test: AdaptationEngine fonctionne"""
    print("\nTest 5: AdaptationEngine...")
    try:
        from src.learning import AdaptationEngine
        
        engine = AdaptationEngine(storage_path="data/test_adaptation")
        
        # Mettre à jour contexte
        engine.update_context(
            task_type="test",
            user_expertise="intermediate"
        )
        
        # Récupérer comportement
        behavior = engine.get_current_behavior()
        
        assert "detail_level" in behavior
        
        print("  ✓ AdaptationEngine fonctionne")
        return True
    except Exception as e:
        print(f"  ✗ Erreur AdaptationEngine: {e}")
        return False

def test_knowledge_base():
    """Test: KnowledgeBase fonctionne"""
    print("\nTest 6: KnowledgeBase...")
    try:
        from src.learning import KnowledgeBase, KnowledgeType, SourceType
        
        kb = KnowledgeBase("data/test_knowledge")
        
        # Ajouter connaissance
        kid = kb.add_knowledge(
            content="Test: Ceci est un test",
            knowledge_type=KnowledgeType.FACT,
            source=SourceType.DOCUMENT,
            source_ref="test.md",
            tags=["test"]
        )
        
        # Rechercher
        results = kb.search("test")
        
        assert len(results) > 0
        
        print("  ✓ KnowledgeBase fonctionne")
        return True
    except Exception as e:
        print(f"  ✗ Erreur KnowledgeBase: {e}")
        return False

def test_validation_system():
    """Test: ValidationSystem fonctionne"""
    print("\nTest 7: ValidationSystem...")
    try:
        from src.learning import ValidationSystem, ValidationType
        
        system = ValidationSystem("data/test_validation")
        
        # Soumettre requête
        req_id = system.submit_validation_request(
            validation_type=ValidationType.ADAPTATION,
            title="Test",
            description="Test validation",
            proposed_change={"test": "value"},
            rationale="Test"
        )
        
        assert req_id is not None
        
        print("  ✓ ValidationSystem fonctionne")
        return True
    except Exception as e:
        print(f"  ✗ Erreur ValidationSystem: {e}")
        return False

def test_adaptive_learning_system():
    """Test: AdaptiveLearningSystem fonctionne"""
    print("\nTest 8: AdaptiveLearningSystem (intégration)...")
    try:
        from src.learning import AdaptiveLearningSystem, FeedbackType
        
        system = AdaptiveLearningSystem("data/test_system")
        
        # Traiter interaction
        result = system.process_interaction(
            user_prompt="Question test",
            assistant_response="Réponse test",
            context={"task_type": "test"}
        )
        
        assert "interaction_id" in result
        
        # Soumettre feedback
        fb = system.submit_feedback(
            interaction_id=result["interaction_id"],
            prompt="Question test",
            response="Réponse test",
            feedback_type=FeedbackType.POSITIVE,
            comment="Test"
        )
        
        # Rechercher
        context = system.get_relevant_context("test")
        
        assert "memories" in context
        assert "knowledge" in context
        
        # Stats
        stats = system.get_system_statistics()
        
        assert "memory" in stats
        assert "feedback" in stats
        
        print("  ✓ AdaptiveLearningSystem fonctionne")
        return True
    except Exception as e:
        print(f"  ✗ Erreur AdaptiveLearningSystem: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Tests de Validation - Système d'Apprentissage Adaptatif")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_memory_manager,
        test_preference_manager,
        test_feedback_system,
        test_adaptation_engine,
        test_knowledge_base,
        test_validation_system,
        test_adaptive_learning_system
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Résultats: {sum(results)}/{len(results)} tests réussis")
    
    if all(results):
        print("✓ TOUS LES TESTS RÉUSSIS")
    else:
        print("✗ CERTAINS TESTS ONT ÉCHOUÉ")
    
    print("=" * 60)
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
