"""
Exemple d'utilisation du système d'apprentissage adaptatif HOPPER
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.learning import AdaptiveLearningSystem, FeedbackType

def main():
    print("=" * 80)
    print("HOPPER - Système d'Apprentissage Adaptatif")
    print("=" * 80)
    
    # 1. Initialiser le système
    print("\n1. Initialisation du système...")
    system = AdaptiveLearningSystem(
        storage_path="data/learning_demo",
        auto_approve_low_risk=True
    )
    print("✓ Système initialisé")
    
    # 2. Simuler des interactions
    print("\n2. Traitement d'interactions...")
    
    interactions = [
        {
            "prompt": "Comment utiliser Python pour lire un fichier CSV?",
            "response": "Pour lire un fichier CSV en Python, utilisez pandas:\n\nimport pandas as pd\ndf = pd.read_csv('fichier.csv')\nprint(df.head())",
            "context": {
                "task_type": "coding",
                "user_expertise": "beginner",
                "conversation_depth": 1,
                "user_sentiment": "neutral"
            }
        },
        {
            "prompt": "Explique-moi les DataFrames pandas",
            "response": "Un DataFrame pandas est une structure de données bidimensionnelle avec des colonnes de types potentiellement différents. C'est comme une table Excel en Python.",
            "context": {
                "task_type": "explanation",
                "user_expertise": "beginner",
                "conversation_depth": 2,
                "user_sentiment": "curious"
            }
        },
        {
            "prompt": "Comment filtrer les données dans un DataFrame?",
            "response": "Pour filtrer un DataFrame:\n\n# Filtrer par condition\ndf_filtered = df[df['age'] > 18]\n\n# Plusieurs conditions\ndf_filtered = df[(df['age'] > 18) & (df['city'] == 'Paris')]",
            "context": {
                "task_type": "coding",
                "user_expertise": "beginner",
                "conversation_depth": 3,
                "user_sentiment": "neutral"
            }
        }
    ]
    
    interaction_ids = []
    for i, interaction in enumerate(interactions, 1):
        result = system.process_interaction(
            user_prompt=interaction["prompt"],
            assistant_response=interaction["response"],
            context=interaction["context"]
        )
        interaction_ids.append(result["interaction_id"])
        print(f"  ✓ Interaction {i} traitée - {result['knowledge_extracted']} connaissances extraites")
    
    # 3. Soumettre des feedbacks
    print("\n3. Soumission de feedbacks...")
    
    feedbacks = [
        {
            "id": interaction_ids[0],
            "interaction": interactions[0],
            "type": FeedbackType.POSITIVE,
            "comment": "Excellent exemple de code, très clair"
        },
        {
            "id": interaction_ids[1],
            "interaction": interactions[1],
            "type": FeedbackType.CORRECTION,
            "comment": "Manque de détails sur les colonnes et index",
            "correction": "Un DataFrame pandas est une structure bidimensionnelle avec des lignes (index) et des colonnes nommées. Chaque colonne peut avoir un type différent (int, float, string, etc.). C'est similaire à une table SQL ou Excel."
        },
        {
            "id": interaction_ids[2],
            "interaction": interactions[2],
            "type": FeedbackType.POSITIVE,
            "comment": "Bons exemples pratiques"
        }
    ]
    
    for i, fb in enumerate(feedbacks, 1):
        result = system.submit_feedback(
            interaction_id=fb["id"],
            prompt=fb["interaction"]["prompt"],
            response=fb["interaction"]["response"],
            feedback_type=fb["type"],
            comment=fb["comment"],
            correction=fb.get("correction")
        )
        print(f"  ✓ Feedback {i} soumis - {result['problematic_patterns']} patterns problématiques")
        
        if "adaptation_suggestions" in result and result["adaptation_suggestions"]:
            print(f"    → Suggestions d'adaptation: {len(result['adaptation_suggestions'])}")
    
    # 4. Traiter un document
    print("\n4. Traitement d'un document...")
    
    document = """
# Guide Python - DataFrames pandas

## Qu'est-ce qu'un DataFrame?

DataFrame: Structure de données bidimensionnelle avec colonnes de types variés

## Création d'un DataFrame

Procédure de création:
1. Importer pandas
2. Créer un dictionnaire de données
3. Convertir en DataFrame avec pd.DataFrame()

Exemple:
```python
import pandas as pd

data = {'nom': ['Alice', 'Bob'], 'age': [25, 30]}
df = pd.DataFrame(data)
```

## Filtrage

DataFrame.loc: Permet de filtrer par labels
DataFrame.iloc: Permet de filtrer par positions
"""
    
    doc_result = system.process_document(
        document_content=document,
        source_ref="guide_pandas.md",
        domain="programming"
    )
    print(f"  ✓ Document traité - {doc_result['knowledge_extracted']} connaissances extraites")
    
    # 5. Rechercher connaissances
    print("\n5. Recherche dans la base de connaissances...")
    
    queries = ["pandas dataframe", "filtrer données", "csv python"]
    
    for query in queries:
        results = system.search_knowledge(query, domain="programming")
        print(f"  • '{query}': {len(results)} résultats")
        if results:
            print(f"    Premier résultat: {results[0]['content'][:100]}...")
    
    # 6. Récupérer contexte pertinent
    print("\n6. Récupération du contexte pertinent...")
    
    context = system.get_relevant_context(
        query="comment utiliser pandas pour les fichiers csv",
        max_memories=3,
        max_knowledge=3
    )
    
    print(f"  • Mémoires: {len(context['memories'])}")
    print(f"  • Connaissances: {len(context['knowledge'])}")
    print(f"  • Comportement actuel: {context['current_behavior']}")
    print(f"  • Préférences utilisateur: {len(context['user_preferences'])} catégories")
    
    # 7. Appliquer une adaptation
    print("\n7. Application d'une adaptation...")
    
    adaptation_result = system.apply_adaptation(
        adjustments={"detail_level": "detailed", "explanation_depth": "thorough"},
        reason="Utilisateur débutant préfère explications détaillées",
        require_validation=False  # Auto-approve car faible risque
    )
    
    print(f"  ✓ Adaptation {adaptation_result['status']}")
    print(f"    Ajustements: {adaptation_result['adjustments']}")
    
    # 8. Vérifier les validations en attente
    print("\n8. Vérification des validations en attente...")
    
    pending = system.get_pending_validations()
    print(f"  • {len(pending)} validations en attente")
    
    if pending:
        for req in pending[:3]:
            print(f"    - {req['title']} (risque: {req['risk_level']})")
    
    # 9. Statistiques globales
    print("\n9. Statistiques du système...")
    
    stats = system.get_system_statistics()
    
    print(f"\n  Mémoire:")
    print(f"    • Total: {stats['memory']['total_memories']}")
    print(f"    • Requêtes: {stats['memory']['total_queries']}")
    
    print(f"\n  Préférences:")
    print(f"    • Total observations: {stats['preferences']['total_observations']}")
    print(f"    • Préférences apprises: {stats['preferences']['preferences_learned']}")
    
    print(f"\n  Feedback:")
    print(f"    • Total feedbacks: {stats['feedback']['total_feedbacks']}")
    print(f"    • Positifs: {stats['feedback']['positive_feedbacks']}")
    print(f"    • Négatifs: {stats['feedback']['negative_feedbacks']}")
    print(f"    • Reward moyen: {stats['feedback']['average_reward']:.2f}")
    
    print(f"\n  Adaptation:")
    print(f"    • Règles actives: {stats['adaptation']['active_rules']}")
    print(f"    • Adaptations appliquées: {stats['adaptation']['total_adaptations']}")
    
    print(f"\n  Connaissances:")
    print(f"    • Total entrées: {stats['knowledge']['total_entries']}")
    print(f"    • Domaines: {stats['knowledge']['domains']}")
    print(f"    • Confiance moyenne: {stats['knowledge']['average_confidence']:.2f}")
    
    print(f"\n  Validation:")
    print(f"    • Requêtes totales: {stats['validation']['total_requests']}")
    print(f"    • En attente: {stats['validation']['pending']}")
    print(f"    • Approuvées: {stats['validation']['approved']}")
    print(f"    • Taux auto-approbation: {stats['validation']['auto_approval_rate']:.1%}")
    
    # 10. Export des données
    print("\n10. Export des données d'apprentissage...")
    
    export_files = system.export_learning_data("exports/demo")
    print(f"  ✓ Données exportées:")
    for name, path in export_files.items():
        print(f"    • {name}: {path}")
    
    print("\n" + "=" * 80)
    print("Démonstration terminée!")
    print("=" * 80)


if __name__ == "__main__":
    main()
