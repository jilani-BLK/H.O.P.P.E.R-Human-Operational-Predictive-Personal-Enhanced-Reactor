# 🧠 Architecture RAG Avancée HOPPER - Vue d'Ensemble

## 🎯 Situation Actuelle vs Future

### ❌ Phase 3 Actuel (Limitations)
```
User: "Envoie un email à Paul avec la note d'hier"
  ↓
Dispatcher (regex patterns)
  ↓
RAG (ChromaDB) ← TOUJOURS appelé (même si inutile)
  ↓ Trouve "note d'hier" ✅
  ↓
LLM: "Voici la note que j'ai trouvée..."
  ↓
❌ PROBLÈME: Ne peut PAS envoyer l'email (juste lire)
```

**Temps de réponse:** ~3.5s (RAG + LLM)  
**Actions possibles:** ❌ Aucune (lecture seule)

---

### ✅ Phase 3.5 Future (Solution Complète)
```
User: "Envoie un email à Paul avec la note d'hier"
  ↓
┌─────────────────────────────────────────┐
│ 1. Self-RAG (Décision: 50ms)           │
│    → Détecte: action + knowledge        │
└────────────┬────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌──────────┐  ┌──────────────┐
│ GraphRAG │  │ ReAct Agent  │
│ (500ms)  │  │ (2s)         │
└────┬─────┘  └──────┬───────┘
     │               │
     │ "Note du     │ Action 1: GraphRAG.get("hier")
     │  15/10/2025" │ Action 2: Email.send(paul, note)
     │               │
     └───────┬───────┘
             ▼
    ✅ Email envoyé avec note attachée
```

**Temps de réponse:** ~2.5s (-30% latence)  
**Actions possibles:** ✅ Envoi email, création fichier, agenda, etc.

---

## 📊 Comparaison Détaillée

| Critère | Phase 3 Actuel | Phase 3.5 RAG Avancé | Gain |
|---------|----------------|----------------------|------|
| **Décision RAG** | Toujours utilisé | Self-RAG critique | -30% latence |
| **Type de mémoire** | Vecteurs seuls | Graphe + relations | +40% pertinence |
| **Actions** | ❌ Lecture seule | ✅ ReAct agent | Tools actifs |
| **Requêtes floues** | Embeddings directs | HyDE expansion | +30% couverture |
| **Contexte** | Document isolé | Multi-hop traversal | Contexte riche |
| **Personnalisation** | Générique | kNN-LM (Phase 5+) | Adapté user |

---

## 🏗️ Architecture Complète

```
┌──────────────────────────────────────────────────────────────┐
│                    USER INPUT                                 │
│  "Envoie un email à Paul avec le doc sur le projet HOPPER"  │
└───────────────────────┬──────────────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                   UNIFIED DISPATCHER                          │
│  (Remplace dispatcher.py actuel)                             │
└───────────────────────┬──────────────────────────────────────┘
                        ▼
        ┌───────────────────────────────┐
        │     1. SELF-RAG (50-100ms)    │
        │  Décide: direct | knowledge   │
        │          | action | fuzzy     │
        └──────────┬────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌────────┐   ┌──────────┐   ┌──────────┐   ┌──────┐
│ direct │   │knowledge │   │  action  │   │fuzzy │
│  LLM   │   │ GraphRAG │   │  ReAct   │   │ HyDE │
└────┬───┘   └────┬─────┘   └────┬─────┘   └──┬───┘
     │            │              │            │
     └────────────┴──────────────┴────────────┘
                   ▼
          ┌────────────────┐
          │  LLM Generation│
          │  + Execution   │
          └────────┬───────┘
                   ▼
            ┌──────────────┐
            │   RESPONSE   │
            │ ✅ Email sent│
            └──────────────┘
```

---

## 🔍 Zoom sur Chaque Composant

### 1️⃣ Self-RAG (Semaine 1)

**Rôle:** "Est-ce que j'ai vraiment besoin de chercher?"

```python
query = "Bonjour HOPPER"
decision = self_rag.decide(query)
# → "direct" (pas de RAG, LLM seul suffit)
# Temps: 0ms (pattern matching)

query = "Quelle est la note sur le projet X?"
decision = self_rag.decide(query)
# → "knowledge" (RAG nécessaire)
# Temps: 50ms (LLM classification)

query = "Envoie un email à Paul"
decision = self_rag.decide(query)
# → "action" (outil requis)
# Temps: 10ms (pattern matching)
```

**Impact:**
- ✅ 30% requêtes évitent RAG inutile
- ✅ Latence moyenne: 3.5s → 2.5s
- ✅ Moins de charge sur Neo4j

---

### 2️⃣ GraphRAG (Semaine 2)

**Rôle:** "Comment les infos sont-elles liées?"

#### ChromaDB Actuel (Vecteurs seuls)
```
Query: "Qui a participé à la réunion sur le bug?"

ChromaDB: 
  - Doc 1: "Réunion du 15/10" (score: 0.8)
  - Doc 2: "Bug #123 sur port" (score: 0.75)
  
❌ Pas de lien explicite entre réunion et bug
```

#### GraphRAG (Relations explicites)
```
Query: "Qui a participé à la réunion sur le bug?"

GraphRAG:
┌────────────┐
│ Réunion    │──DISCUSSES──→┌─────────┐
│ 15/10/2025 │              │ Bug #123│
└─────┬──────┘              └────┬────┘
      │                          │
      │ HAS_PARTICIPANT          │ FIXED_BY
      ▼                          ▼
┌──────────┐              ┌─────────────┐
│  Paul    │              │ Config port │
│  Marie   │              │    5050     │
└──────────┘              └─────────────┘

Réponse: "Paul et Marie ont participé à la réunion 
          où le bug #123 a été discuté (fixé par 
          changement de port vers 5050)"
```

**Impact:**
- ✅ +40% pertinence (contexte relationnel)
- ✅ Requêtes multi-hop possibles
- ✅ Mémoire structurée (pas juste vecteurs)

---

### 3️⃣ ReAct Agent (Semaine 3)

**Rôle:** "Comment je fais ça concrètement?"

#### Exemple Complet
```
User: "Envoie un email à Paul avec la note du projet"

──────────────────────────────────────────────────
THOUGHT 1:
"Je dois d'abord trouver l'email de Paul"

ACTION 1: contacts.search("Paul")
OBSERVATION 1: paul.dupont@example.com

──────────────────────────────────────────────────
THOUGHT 2:
"Maintenant je dois récupérer la note du projet"

ACTION 2: graphrag.query("note projet")
OBSERVATION 2: "Note: Phase 3.5 RAG avancé..."

──────────────────────────────────────────────────
THOUGHT 3:
"J'ai tout, je peux composer et envoyer l'email"

ACTION 3: email.send(
    to="paul.dupont@example.com",
    subject="Note du projet",
    body="Voici la note demandée...",
    attachments=["note_projet.txt"]
)
OBSERVATION 3: ✅ Email envoyé

──────────────────────────────────────────────────
THOUGHT 4:
"Tâche terminée"

ACTION 4: FINISH
RESULT: "Email envoyé à Paul avec la note du projet"
```

**Outils Disponibles:**
- ✅ `email` - Envoyer/lire emails (IMAP/SMTP)
- ✅ `files` - Créer/modifier fichiers (system_executor)
- ✅ `notes` - Ajouter/chercher notes (GraphRAG)
- ✅ `contacts` - Rechercher contacts
- ✅ `terminal` - Exécuter commandes shell
- 🔜 `agenda` - Créer événements calendrier
- 🔜 `domotique` - Contrôler appareils

**Impact:**
- ✅ HOPPER peut **agir**, pas juste parler
- ✅ 90% succès actions multi-étapes
- ✅ Extension facile (nouveau tool = +1 fichier)

---

### 4️⃣ HyDE (Semaine 4)

**Rôle:** "Que voulait vraiment dire l'utilisateur?"

#### Sans HyDE
```
Query: "le truc de l'autre jour"

Embedding direct:
  vector([0.12, -0.34, ...])  ← Vague!

Résultats:
  - Doc 1: "Historique des trucs" (???)
  - Doc 2: "Configuration autre jour" (???)
  
❌ Pas assez précis
```

#### Avec HyDE
```
Query: "le truc de l'autre jour"

1. Génération document hypothétique (LLM):
   "Compte-rendu de réunion du projet HOPPER 
    du 21 octobre 2025 où nous avons discuté 
    des fonctionnalités RAG avancées, notamment 
    l'intégration de GraphRAG et ReAct agent..."

2. Embedding du document hypothétique:
   vector([0.89, 0.45, ...])  ← Riche en contexte!

3. Recherche:
   - Doc 1: "Réunion 21/10 GraphRAG" (0.92) ✅
   - Doc 2: "Phase 3.5 RAG avancé" (0.87) ✅

✅ +30% pertinence sur requêtes floues
```

**Impact:**
- ✅ Robuste aux requêtes vagues
- ✅ Comprend pronoms ("ça", "ça", "le truc")
- ✅ Contexte temporel ("hier", "la semaine dernière")

---

## 🎛️ Configuration & Tuning

### Self-RAG Thresholds
```python
# src/rag/self_rag.py
THRESHOLDS = {
    "relevance_min": 0.7,      # Score min pour garder doc
    "llm_classify_timeout": 100, # ms max pour décision
    "fast_path_confidence": 0.9  # Confiance patterns
}
```

### GraphRAG Parameters
```python
# src/rag/graph_store.py
GRAPH_CONFIG = {
    "embedding_dim": 384,       # all-MiniLM-L6-v2
    "max_hop_depth": 2,         # Traversée graphe
    "top_k_results": 5,         # Nb docs récupérés
    "entity_types": [           # Entités à extraire
        "PERSON", "ORG", "LOC", 
        "DATE", "EVENT", "PRODUCT"
    ]
}
```

### ReAct Agent Limits
```python
# src/agents/react_agent.py
REACT_CONFIG = {
    "max_steps": 5,            # Max itérations Thought→Action
    "timeout_per_step": 30,    # Secondes max par action
    "allowed_tools": [         # Outils activés
        "email", "files", "notes", 
        "contacts", "terminal"
    ]
}
```

### HyDE Settings
```python
# src/rag/hyde.py
HYDE_CONFIG = {
    "hypo_doc_length": 200,    # Tokens du doc hypothétique
    "temperature": 0.8,        # Créativité LLM
    "use_hyde_if": [           # Quand utiliser HyDE
        "fuzzy_keywords",      # "truc", "machin"
        "temporal_vague",      # "l'autre jour"
        "low_query_length"     # < 5 mots
    ]
}
```

---

## 📈 Métriques & Monitoring

### Dashboard (à implémenter)
```python
# src/rag/metrics.py

class RAGMetrics:
    """Tracking performance RAG avancé"""
    
    def __init__(self):
        self.metrics = {
            # Self-RAG
            "self_rag_decisions": {
                "direct": 0,
                "knowledge": 0,
                "action": 0,
                "fuzzy": 0
            },
            "self_rag_latency_ms": [],
            
            # GraphRAG
            "graph_queries": 0,
            "graph_latency_ms": [],
            "avg_hops": [],
            "entities_found": [],
            
            # ReAct
            "react_actions": 0,
            "react_success_rate": [],
            "avg_steps_per_query": [],
            
            # HyDE
            "hyde_expansions": 0,
            "hyde_improvement": []  # vs direct embedding
        }
    
    def report(self) -> dict:
        """Génère rapport de performance"""
        return {
            "self_rag": {
                "distribution": self.get_distribution(),
                "avg_latency_ms": statistics.mean(
                    self.metrics["self_rag_latency_ms"]
                )
            },
            "graphrag": {
                "total_queries": self.metrics["graph_queries"],
                "avg_latency_ms": statistics.mean(
                    self.metrics["graph_latency_ms"]
                ),
                "avg_hops": statistics.mean(self.metrics["avg_hops"])
            },
            "react": {
                "total_actions": self.metrics["react_actions"],
                "success_rate": statistics.mean(
                    self.metrics["react_success_rate"]
                ) * 100,
                "avg_steps": statistics.mean(
                    self.metrics["avg_steps_per_query"]
                )
            },
            "hyde": {
                "total_expansions": self.metrics["hyde_expansions"],
                "avg_improvement": statistics.mean(
                    self.metrics["hyde_improvement"]
                ) * 100
            }
        }
```

### Logs Structurés
```python
# Exemple de log
logger.info(
    "RAG query completed",
    extra={
        "decision": "action",
        "tools_used": ["graphrag", "email"],
        "latency_ms": 2450,
        "success": True,
        "user_id": "jilani"
    }
)
```

---

## 🚀 Roadmap Complète

### Phase 3.5 (4 semaines)
```
Semaine 1: Self-RAG
├─ self_rag.py
├─ Tests + benchmarks
└─ Intégration dispatcher

Semaine 2: GraphRAG
├─ Neo4j setup
├─ graph_store.py
├─ entity_extractor.py
├─ Migration ChromaDB
└─ Tests multi-hop

Semaine 3: ReAct Agent
├─ react_agent.py
├─ Tools (email, files, notes)
├─ Action parser
└─ Tests end-to-end

Semaine 4: HyDE + Intégration
├─ hyde.py
├─ unified_dispatcher.py
├─ Métriques dashboard
├─ Documentation
└─ Tests complets (66 → 80+)
```

### Phase 4 (après Phase 3.5)
- Outils supplémentaires: agenda, domotique
- API externe: météo, actualités
- Multi-utilisateurs avancé

### Phase 5+ (Long terme)
- kNN-LM pour personnalisation
- Fine-tuning LLM sur données user
- Federated learning (privacy)

---

## 📚 Ressources Complémentaires

### Papers
- **GraphRAG:** https://arxiv.org/abs/2404.16130
- **ReAct:** https://arxiv.org/abs/2210.03629
- **Self-RAG:** https://arxiv.org/abs/2310.11511
- **HyDE:** https://arxiv.org/abs/2212.10496
- **Toolformer:** https://arxiv.org/abs/2302.04761

### Implémentations de Référence
- LangGraph (ReAct): https://github.com/langchain-ai/langgraph
- GraphRAG (Microsoft): https://github.com/microsoft/graphrag
- Neo4j Python: https://neo4j.com/docs/python-manual/current/

### Outils
- Neo4j Browser: http://localhost:7474
- Neo4j Bloom (visualisation graphe)
- Weights & Biases (métriques ML)

---

## ✅ Checklist de Validation Phase 3.5

### Fonctionnalités
- [ ] Self-RAG évite 30%+ RAG inutile
- [ ] GraphRAG traverse relations (2+ hops)
- [ ] ReAct exécute actions multi-étapes
- [ ] HyDE améliore requêtes floues (+30%)

### Performance
- [ ] Self-RAG < 100ms
- [ ] GraphRAG < 500ms
- [ ] ReAct < 3s
- [ ] Latence globale -30% vs Phase 3

### Tests
- [ ] 80+ tests automatisés (vs 66 Phase 3)
- [ ] 100% coverage nouveaux modules
- [ ] Tests end-to-end: 10 scénarios complexes
- [ ] Benchmarks: 1000 requêtes variées

### Documentation
- [ ] Architecture complète
- [ ] Guides d'utilisation
- [ ] API reference
- [ ] Troubleshooting

---

## 🎯 Prochaine Action

**Prêt à démarrer?**

1. **Installer dépendances:**
   ```bash
   pip install -r requirements-rag-advanced.txt
   ```

2. **Lancer Neo4j:**
   ```bash
   # Ajouter service neo4j au docker-compose.yml
   docker-compose up -d neo4j
   ```

3. **Créer Self-RAG:**
   ```bash
   mkdir -p src/rag
   # Copier code depuis PLAN_IMPLEMENTATION_RAG_AVANCE.md
   ```

4. **Premier test:**
   ```python
   from src.rag.self_rag import SelfRAG
   
   rag = SelfRAG(llm_client)
   decision = rag.decide("Bonjour HOPPER", {})
   assert decision == "direct"  # Pas de RAG!
   ```

**On commence par Self-RAG (Semaine 1)?** 🚀
