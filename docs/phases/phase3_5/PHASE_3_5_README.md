# 🧠 Phase 3.5 - RAG Avancé pour HOPPER

## 🎯 Vue d'Ensemble

Cette phase transforme HOPPER d'un assistant **lecture seule** vers un agent **intelligent et actif**.

### Avant (Phase 3)
```
User: "Envoie un email à Paul"
HOPPER: "Voici comment envoyer un email..." ❌
```

### Après (Phase 3.5)
```
User: "Envoie un email à Paul"
HOPPER: "✅ Email envoyé à paul.dupont@example.com"
```

---

## 🏗️ Composants Principaux

### 1. **Self-RAG** (Semaine 1)
**Problème résolu:** RAG appelé même quand inutile  
**Solution:** Critique intelligente avant récupération  
**Impact:** -30% latence, décision en <100ms

### 2. **GraphRAG** (Semaine 2)
**Problème résolu:** Vecteurs seuls, pas de relations  
**Solution:** Neo4j avec graphe de connaissances  
**Impact:** +40% pertinence, requêtes multi-hop

### 3. **ReAct Agent** (Semaine 3)
**Problème résolu:** Pas d'actions concrètes  
**Solution:** Agent Thought→Action→Observation  
**Impact:** HOPPER peut agir (email, fichiers, agenda)

### 4. **HyDE** (Semaine 4)
**Problème résolu:** Requêtes floues mal comprises  
**Solution:** Expansion via documents hypothétiques  
**Impact:** +30% couverture requêtes vagues

---

## 📁 Documentation

| Fichier | Description |
|---------|-------------|
| **[ARCHITECTURE_RAG_AVANCEE.md](docs/ARCHITECTURE_RAG_AVANCEE.md)** | Concepts théoriques, papers, références |
| **[PLAN_IMPLEMENTATION_RAG_AVANCE.md](docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md)** | Code complet + tests (4 semaines) |
| **[ARCHITECTURE_RAG_VISUELLE.md](docs/ARCHITECTURE_RAG_VISUELLE.md)** | Diagrammes, comparaisons, exemples |

---

## 🚀 Démarrage Rapide

### Installation

```bash
# 1. Installer dépendances
pip install -r requirements-rag-advanced.txt

# 2. Télécharger modèle NER
python -m spacy download fr_core_news_lg

# 3. Setup complet (automatique)
./setup_rag_advanced.sh
```

### Vérification

```bash
# Neo4j Browser
open http://localhost:7474
# Credentials: neo4j / hopper123

# Test connexion
python -c "from neo4j import GraphDatabase; \
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'hopper123')); \
    print('✅ Neo4j OK'); driver.close()"
```

---

## 📅 Roadmap (4 Semaines)

### Semaine 1: Self-RAG
- [ ] Implémenter `src/rag/self_rag.py`
- [ ] Classification rapide (patterns + LLM)
- [ ] Critique post-récupération
- [ ] Tests: `tests/test_self_rag.py`
- [ ] Intégration dispatcher

**Livrables:**
- ✅ Self-RAG opérationnel
- ✅ Métriques: latence < 100ms
- ✅ Distribution décisions (direct/knowledge/action/fuzzy)

---

### Semaine 2: GraphRAG
- [ ] Neo4j via Docker
- [ ] Implémenter `src/rag/graph_store.py`
- [ ] Extraction entités (spaCy)
- [ ] Recherche vectorielle + traversée graphe
- [ ] Migration ChromaDB → Neo4j

**Livrables:**
- ✅ GraphRAG fonctionnel
- ✅ Requêtes multi-hop (depth=2)
- ✅ Neo4j Browser accessible
- ✅ Tests: `tests/test_graph_rag.py`

---

### Semaine 3: ReAct Agent
- [ ] Implémenter `src/agents/react_agent.py`
- [ ] Cycle Thought→Action→Observation
- [ ] Parser actions LLM
- [ ] Tools: email, files, notes, contacts
- [ ] Tests end-to-end

**Livrables:**
- ✅ ReAct opérationnel
- ✅ 5 outils minimum
- ✅ 90% succès actions multi-étapes
- ✅ Tests: `tests/test_react_agent.py`

---

### Semaine 4: HyDE + Intégration
- [ ] Implémenter `src/rag/hyde.py`
- [ ] Expansion requêtes floues
- [ ] `src/orchestrator/core/unified_dispatcher.py`
- [ ] Pipeline complet: Self-RAG → [GraphRAG|ReAct|HyDE]
- [ ] Métriques & monitoring

**Livrables:**
- ✅ HyDE fonctionnel
- ✅ Dispatcher unifié
- ✅ Dashboard métriques
- ✅ Documentation complète
- ✅ 80+ tests (vs 66 Phase 3)

---

## 🔧 Structure Modules

```
src/
├── rag/
│   ├── __init__.py
│   ├── self_rag.py              # Critique RAG
│   ├── graph_store.py           # Neo4j GraphRAG
│   ├── entity_extractor.py      # NER avec spaCy
│   ├── hyde.py                  # Query expansion
│   └── unified_retriever.py     # Pipeline complet
│
├── agents/
│   ├── __init__.py
│   ├── react_agent.py           # ReAct cycle
│   ├── action_parser.py         # Parse LLM → actions
│   └── tools/
│       ├── __init__.py
│       ├── base_tool.py         # Interface Tool
│       ├── email_tool.py        # IMAP/SMTP
│       ├── file_tool.py         # Fichiers locaux
│       ├── notes_tool.py        # GraphRAG interactions
│       └── contacts_tool.py     # Carnet d'adresses
│
└── orchestrator/
    └── core/
        └── unified_dispatcher.py # Dispatcher Phase 3.5
```

---

## 🧪 Tests

### Lancer tous les tests
```bash
pytest tests/rag/ tests/agents/ -v
```

### Tests spécifiques
```bash
# Self-RAG
pytest tests/test_self_rag.py::test_quick_classify_action -v

# GraphRAG
pytest tests/test_graph_rag.py::test_retrieve_with_context -v

# ReAct
pytest tests/test_react_agent.py::test_multi_step_action -v
```

### Coverage
```bash
pytest --cov=src/rag --cov=src/agents --cov-report=html
open htmlcov/index.html
```

---

## 📊 Métriques de Succès

### Performance
- ✅ Self-RAG: < 100ms
- ✅ GraphRAG: < 500ms
- ✅ ReAct: < 3s action complète
- ✅ HyDE: < 200ms expansion
- ✅ Latence globale: -30% vs Phase 3

### Qualité
- ✅ Self-RAG: 85%+ précision éviter RAG inutile
- ✅ GraphRAG: +40% pertinence vs ChromaDB
- ✅ ReAct: 90%+ succès actions multi-étapes
- ✅ HyDE: +30% couverture requêtes floues

### Tests
- ✅ 80+ tests automatisés (vs 66 Phase 3)
- ✅ 100% coverage nouveaux modules
- ✅ 10 scénarios end-to-end complexes

---

## 🎯 Exemples d'Usage

### Exemple 1: Self-RAG évite RAG inutile
```python
from src.rag.self_rag import SelfRAG

rag = SelfRAG(llm_client)

# Question simple → pas de RAG
decision = rag.decide("Bonjour HOPPER", {})
assert decision == "direct"  # LLM seul, 0ms

# Question factuelle → RAG
decision = rag.decide("Quelle est la note du projet X?", {})
assert decision == "knowledge"  # GraphRAG, 500ms
```

### Exemple 2: GraphRAG multi-hop
```python
from src.rag.graph_store import GraphRAG

graph = GraphRAG()

# Ajouter note avec relations automatiques
graph.add_note(
    content="Réunion avec Paul sur bug #123",
    user_id="jilani",
    embedding=embed("réunion paul bug")
)

# Rechercher avec contexte
results = graph.retrieve(
    query_embedding=embed("qui a participé au bug?"),
    user_id="jilani",
    depth=2  # 2 hops: Réunion → Paul + Bug
)

# Résultat: Note + [Paul, Bug #123] liés
```

### Exemple 3: ReAct action multi-étapes
```python
from src.agents.react_agent import ReActAgent

agent = ReActAgent(llm_client, tools={
    "email": EmailTool(),
    "notes": NotesTool()
})

result = agent.run(
    "Envoie un email à Paul avec la note du projet"
)

# Cycle:
# Thought: "Je dois trouver email de Paul"
# Action: contacts.search("Paul")
# Observation: paul@example.com
# Thought: "Je dois récupérer la note"
# Action: notes.search("projet")
# Observation: "Note Phase 3.5..."
# Thought: "Je peux composer l'email"
# Action: email.send(...)
# Result: ✅ Email envoyé
```

### Exemple 4: HyDE requête floue
```python
from src.rag.hyde import HyDE

hyde = HyDE(llm_client)

# Requête vague
query = "le truc de l'autre jour"

# Expansion hypothétique
expanded = hyde.expand_query(query)
# → "Compte-rendu de réunion du 21 octobre 2025..."

# Recherche avec expansion
results = graph.retrieve(embed(expanded))
# → Pertinence +30% vs query directe
```

---

## 🛠️ Configuration

### Neo4j (docker-compose.yml)
```yaml
neo4j:
  image: neo4j:5.15-community
  ports:
    - "7474:7474"  # Browser
    - "7687:7687"  # Bolt
  environment:
    - NEO4J_AUTH=neo4j/hopper123
```

### Self-RAG (src/rag/self_rag.py)
```python
THRESHOLDS = {
    "relevance_min": 0.7,
    "llm_classify_timeout": 100,
    "fast_path_confidence": 0.9
}
```

### GraphRAG (src/rag/graph_store.py)
```python
GRAPH_CONFIG = {
    "embedding_dim": 384,
    "max_hop_depth": 2,
    "top_k_results": 5,
    "entity_types": ["PERSON", "ORG", "LOC", "DATE"]
}
```

### ReAct (src/agents/react_agent.py)
```python
REACT_CONFIG = {
    "max_steps": 5,
    "timeout_per_step": 30,
    "allowed_tools": ["email", "files", "notes"]
}
```

---

## 🐛 Troubleshooting

### Neo4j ne démarre pas
```bash
# Vérifier logs
docker logs hopper-neo4j

# Redémarrer
docker-compose restart neo4j

# Tester connexion
curl http://localhost:7474
```

### Erreur spaCy "Model not found"
```bash
# Télécharger modèle
python -m spacy download fr_core_news_lg

# Vérifier
python -c "import spacy; nlp = spacy.load('fr_core_news_lg'); print('✅ OK')"
```

### Tests échouent
```bash
# Vérifier que Neo4j est démarré
docker ps | grep neo4j

# Réinitialiser base de données
docker-compose down neo4j
docker volume rm hopper_neo4j_data
docker-compose up -d neo4j
```

---

## 📚 Ressources

### Documentation
- [ARCHITECTURE_RAG_AVANCEE.md](docs/ARCHITECTURE_RAG_AVANCEE.md) - Théorie
- [PLAN_IMPLEMENTATION_RAG_AVANCE.md](docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md) - Code
- [ARCHITECTURE_RAG_VISUELLE.md](docs/ARCHITECTURE_RAG_VISUELLE.md) - Diagrammes

### Papers
- **GraphRAG:** https://arxiv.org/abs/2404.16130
- **ReAct:** https://arxiv.org/abs/2210.03629
- **Self-RAG:** https://arxiv.org/abs/2310.11511
- **HyDE:** https://arxiv.org/abs/2212.10496

### Tools
- Neo4j Browser: http://localhost:7474
- Neo4j Docs: https://neo4j.com/docs/
- spaCy: https://spacy.io/models/fr

---

## ✅ Checklist de Démarrage

- [ ] Dépendances installées (`requirements-rag-advanced.txt`)
- [ ] Neo4j démarré (`docker-compose up -d neo4j`)
- [ ] Modèle spaCy téléchargé (`fr_core_news_lg`)
- [ ] Structure modules créée (`src/rag/`, `src/agents/`)
- [ ] Neo4j Browser accessible (http://localhost:7474)
- [ ] Documentation lue (3 fichiers .md)
- [ ] Script setup exécuté (`./setup_rag_advanced.sh`)

---

## 🚀 Prêt à Commencer!

**Étape suivante:** Implémenter Self-RAG (Semaine 1)

```bash
# Créer fichier
nano src/rag/self_rag.py

# Copier code depuis
# docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md (Semaine 1)

# Tests
pytest tests/test_self_rag.py -v
```

**Questions?** Consulter la documentation complète dans `docs/`

**Bon développement!** 🤖
