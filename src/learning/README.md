# Système d'Apprentissage Adaptatif HOPPER

Système complet d'apprentissage continu et d'adaptation sous contrôle humain.

## Architecture

Le système est composé de 6 modules interconnectés :

### 1. **MemoryManager** - Mémoire à Long Terme
- **Fichier**: `memory_manager.py`
- **Rôle**: Stockage vectoriel local des connaissances, conversations, préférences
- **Fonctionnalités**:
  - 8 types de mémoires (conversation, knowledge, preference, experience, document, feedback, error, success)
  - Embeddings vectoriels (128-dim, TF-IDF simplifié, upgradable vers sentence-transformers)
  - Recherche sémantique avec similarité cosine
  - Index triple (type, tag, vecteur)
  - Scoring de pertinence (similarité + importance + récence)
  - Consolidation automatique (nettoyage mémoires peu importantes)
  - Persistance JSON

### 2. **PreferenceManager** - Gestionnaire de Préférences
- **Fichier**: `preference_manager.py`
- **Rôle**: Apprentissage des préférences utilisateur
- **Fonctionnalités**:
  - 8 catégories (response_style, detail_level, format, tone, language, domain, interaction, privacy)
  - Observation d'interactions pour détecter patterns
  - Feedback explicite vs inféré
  - Score de confiance (0-1)
  - Configuration d'adaptation dynamique
  - Statistiques d'apprentissage

### 3. **FeedbackSystem** - Système RLHF-like
- **Fichier**: `feedback_system.py`
- **Rôle**: Intégration retours utilisateur, correction erreurs
- **Fonctionnalités**:
  - 6 types de feedback (positive, negative, correction, suggestion, error, safety)
  - Signaux de récompense (-1 à +1)
  - Extraction patterns d'erreurs et de succès
  - Règles de correction apprises
  - Suggestions de corrections basées sur historique
  - Intégration avec MemoryManager et PreferenceManager

### 4. **AdaptationEngine** - Adaptation Contextuelle
- **Fichier**: `adaptation_engine_contextual.py`
- **Rôle**: Ajustement dynamique du comportement
- **Fonctionnalités**:
  - Analyse contexte en temps réel (task, user_state, conversation, environment, temporal)
  - 4 stratégies d'adaptation (immediate, gradual, validated, experimental)
  - Règles d'adaptation configurables
  - Comportements ajustables (detail_level, tone, code_style, explanation_depth, proactivity)
  - 5 règles par défaut (beginner, expert, frustration, long_conversation, debugging)
  - Historique d'adaptations

### 5. **KnowledgeBase** - Base de Connaissances
- **Fichier**: `knowledge_base.py`
- **Rôle**: Extraction, stockage, indexation connaissances
- **Fonctionnalités**:
  - 6 types de connaissances (fact, concept, procedure, relationship, example, rule)
  - Extraction automatique depuis documents (concepts, procédures, exemples)
  - Extraction depuis conversations (corrections, faits)
  - Graphe de connaissances (nodes + edges)
  - Recherche avec scoring
  - Index multiples (type, tag, domaine)
  - Score de confiance évolutif

### 6. **ValidationSystem** - Validation Humaine
- **Fichier**: `validation_system.py`
- **Rôle**: Workflow validation, garde-fous sécurité
- **Fonctionnalités**:
  - 5 types de validation (adaptation, knowledge, correction, safety, permission)
  - 4 niveaux de risque (low, medium, high, critical)
  - 4 garde-fous par défaut (data_access, system_modification, external_access, code_execution)
  - Auto-approbation risques faibles (optionnel)
  - Analyse d'impact (composants, performance, données)
  - Timeout configurable
  - Audit trail complet

### 7. **AdaptiveLearningSystem** - Orchestrateur
- **Fichier**: `adaptive_learning_system.py`
- **Rôle**: API unifiée, orchestration composants
- **Fonctionnalités**:
  - Initialisation tous composants
  - `process_interaction()`: traitement complet interaction
  - `submit_feedback()`: soumission feedback avec suggestions adaptations
  - `apply_adaptation()`: adaptation avec validation
  - `process_document()`: extraction connaissances document
  - `search_knowledge()`: recherche base connaissances
  - `get_relevant_context()`: contexte pertinent (mémoires + connaissances + préférences)
  - `get_pending_validations()`: validations en attente
  - `approve/reject_validation()`: gestion validations
  - `get_system_statistics()`: stats tous composants
  - `export_learning_data()`: export complet
  - `reset_to_default()`: réinitialisation

## Flux de Données

```
User Interaction
       ↓
AdaptiveLearningSystem.process_interaction()
       ↓
   ┌───┴───┬───────┬──────────┬────────┐
   ↓       ↓       ↓          ↓        ↓
Memory  Prefs  Knowledge  Adaptation  Validation
   ↑       ↑       ↑          ↑        ↑
   └───────┴───────┴──────────┴────────┘
              ↓
         Feedback
              ↓
     Pattern Detection
              ↓
    Adaptation Proposal
              ↓
        Validation
              ↓
         Applied
```

## Utilisation

### Initialisation
```python
from src.learning import AdaptiveLearningSystem

system = AdaptiveLearningSystem(
    storage_path="data/learning",
    auto_approve_low_risk=True
)
```

### Traiter une Interaction
```python
result = system.process_interaction(
    user_prompt="Comment utiliser pandas?",
    assistant_response="Pandas est une bibliothèque...",
    context={
        "task_type": "coding",
        "user_expertise": "beginner",
        "conversation_depth": 3,
        "user_sentiment": "neutral"
    }
)
# → Enregistre en mémoire, observe préférences, extrait connaissances
```

### Soumettre Feedback
```python
from src.learning import FeedbackType

feedback = system.submit_feedback(
    interaction_id=result["interaction_id"],
    prompt="Comment utiliser pandas?",
    response="Pandas est une bibliothèque...",
    feedback_type=FeedbackType.POSITIVE,
    comment="Excellente explication"
)
# → Analyse patterns, suggère adaptations si nécessaire
```

### Appliquer Adaptation
```python
adaptation = system.apply_adaptation(
    adjustments={"detail_level": "detailed"},
    reason="Utilisateur débutant demande plus de détails",
    require_validation=False  # Auto-approve si risque faible
)
# → Valide puis applique si approuvé
```

### Traiter un Document
```python
doc_result = system.process_document(
    document_content=open("doc.md").read(),
    source_ref="doc.md",
    domain="programming"
)
# → Extrait concepts, procédures, exemples
```

### Récupérer Contexte Pertinent
```python
context = system.get_relevant_context(
    query="pandas dataframe",
    max_memories=5,
    max_knowledge=3
)
# → Retourne mémoires + connaissances + préférences + comportement
```

### Gérer Validations
```python
# Récupérer validations en attente
pending = system.get_pending_validations()

# Approuver
system.approve_validation(pending[0]["request_id"])

# Rejeter
system.reject_validation(pending[1]["request_id"], reason="Trop risqué")
```

### Statistiques
```python
stats = system.get_system_statistics()
# → Stats de tous les composants (memory, preferences, feedback, etc.)
```

### Export
```python
files = system.export_learning_data("exports/")
# → Exporte memories.json, preferences.json, knowledge.json, audit_trail.json
```

## Stockage

```
data/
├── memory/              # Mémoires
│   ├── mem_*.json
│   └── index.json
├── preferences/         # Préférences
│   └── user_preferences.json
├── feedback/           # Feedbacks
│   ├── feedbacks.json
│   ├── patterns.json
│   ├── correction_rules.json
│   └── stats.json
├── adaptation/         # Adaptations
│   ├── rules.json
│   ├── adaptation_history.json
│   ├── current_behavior.json
│   └── stats.json
├── knowledge/          # Connaissances
│   ├── knowledge.json
│   ├── graph.json
│   └── stats.json
└── validation/         # Validations
    ├── requests.json
    ├── guardrails.json
    ├── decision_history.json
    └── stats.json
```

## Principes de Design

1. **Local First**: Tout fonctionne localement, pas de dépendances cloud
2. **Human-in-the-Loop**: Validations pour adaptations importantes
3. **Gradual Learning**: Apprentissage progressif avec scores de confiance
4. **Safety First**: Garde-fous multiples, analyse de risque
5. **Transparency**: Audit trail complet, export données
6. **Modularity**: Composants indépendants mais intégrés
7. **Zero Heavy Deps**: Embeddings simples au début, upgradables

## Prochaines Étapes

1. **Intégration HOPPER**: Connecter au système principal
2. **UI Validation**: Interface pour gérer validations
3. **Embeddings Avancés**: Upgrade vers sentence-transformers
4. **Fine-tuning Local**: Ajout capacité fine-tuning modèle local
5. **Métriques Avancées**: Tableaux de bord, analytics
6. **Tests Unitaires**: Suite complète de tests
7. **Documentation API**: API reference détaillée

## Version

**v1.0.0** - Système complet opérationnel

## Auteur

Système d'apprentissage adaptatif pour HOPPER
Créé le 2024
