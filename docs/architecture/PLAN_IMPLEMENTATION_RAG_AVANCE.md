# 🎯 Plan d'Implémentation RAG Avancé - Phase 3.5
*Roadmap détaillée pour intégrer GraphRAG + ReAct + Self-RAG*

## 📅 Timeline: 4 Semaines (après Phase 3 vocale)

```
┌────────────┬────────────┬────────────┬────────────┐
│  Semaine 1 │  Semaine 2 │  Semaine 3 │  Semaine 4 │
│  Self-RAG  │  GraphRAG  │   ReAct    │   HyDE +   │
│            │            │   Agent    │ Intégration│
└────────────┴────────────┴────────────┴────────────┘
```

## 🏗️ Architecture Actuelle vs Future

### Actuel (Phase 3)
```python
# src/orchestrator/core/dispatcher.py
def dispatch(command: str) -> Response:
    intent = detect_intent(command)      # Regex patterns
    
    if intent == "question":
        return self._handle_question()   # LLM + RAG (ChromaDB)
    elif intent == "system_action":
        return self._handle_system()     # System Executor
    ...
```

**Limitations:**
- ❌ RAG toujours appelé (même si inutile)
- ❌ ChromaDB = vecteurs seuls (pas de relations)
- ❌ Peut lire des docs mais **ne fait rien** avec

### Future (Phase 3.5)
```python
# src/orchestrator/core/unified_dispatcher.py
def dispatch(command: str) -> Response:
    # 1. Self-RAG: Ai-je besoin de récupérer?
    decision = self.self_rag.decide(command, context)
    
    if decision == "direct":
        return self.llm.generate(command)  # LLM seul (rapide)
    
    elif decision == "knowledge":
        # 2. GraphRAG: Recherche avec contexte relationnel
        docs = self.graph_rag.retrieve(command, depth=2)
        return self.llm.generate_with_context(command, docs)
    
    elif decision == "action":
        # 3. ReAct: Agent avec outils
        return self.react_agent.run(command, tools=self.tools)
    
    elif decision == "fuzzy":
        # 4. HyDE: Expansion requête floue
        expanded = self.hyde.expand(command)
        docs = self.graph_rag.retrieve(expanded)
        return self.llm.generate_with_context(command, docs)
```

**Avantages:**
- ✅ Latence optimale (Self-RAG évite RAG inutile)
- ✅ Contexte riche (GraphRAG avec relations)
- ✅ Actions concrètes (ReAct exécute vraiment)
- ✅ Robuste aux requêtes floues (HyDE)

---

## 📦 Structure des Modules

```
src/
├── rag/
│   ├── __init__.py
│   ├── self_rag.py              # ✅ Semaine 1
│   ├── graph_store.py           # ✅ Semaine 2
│   ├── entity_extractor.py      # ✅ Semaine 2
│   ├── hyde.py                  # ✅ Semaine 4
│   └── unified_retriever.py     # ✅ Semaine 4
│
├── agents/
│   ├── __init__.py
│   ├── react_agent.py           # ✅ Semaine 3
│   ├── action_parser.py         # ✅ Semaine 3
│   └── tools/
│       ├── __init__.py
│       ├── base_tool.py         # ✅ Semaine 3
│       ├── email_tool.py        # ✅ Semaine 3 (refactor Phase 3)
│       ├── file_tool.py         # ✅ Semaine 3 (wrapper system_executor)
│       ├── notes_tool.py        # ✅ Semaine 3
│       └── search_tool.py       # ✅ Semaine 3
│
├── orchestrator/
│   └── core/
│       ├── dispatcher.py        # ⚠️ Actuel (sera remplacé)
│       └── unified_dispatcher.py # ✅ Semaine 4 (nouveau)
│
└── kb/                          # ⚠️ Actuel (ChromaDB)
    └── vector_store.py          # Migration vers GraphRAG
```

---

## 🔨 Semaine 1: Self-RAG

### Objectif
Décider intelligemment **si** et **quand** utiliser RAG.

### Fichiers à créer

#### `src/rag/self_rag.py`
```python
"""
Self-RAG: Critique intelligente pour éviter récupération inutile
Réduit latence de ~30% en évitant RAG sur questions simples
"""

from typing import Literal, Dict, Any
from loguru import logger

DecisionType = Literal["direct", "knowledge", "action", "fuzzy"]


class SelfRAG:
    """Décide si RAG est nécessaire avant de récupérer"""
    
    def __init__(self, llm_client, threshold: float = 0.7):
        self.llm = llm_client
        self.threshold = threshold
        
        # Statistiques pour monitoring
        self.stats = {
            "total_queries": 0,
            "direct": 0,       # LLM seul
            "knowledge": 0,    # RAG nécessaire
            "action": 0,       # Outil requis
            "fuzzy": 0         # HyDE expansion
        }
    
    def decide(self, query: str, context: Dict[str, Any]) -> DecisionType:
        """
        Décide du type de traitement nécessaire
        
        Args:
            query: Requête utilisateur
            context: Contexte conversationnel
            
        Returns:
            "direct": LLM seul suffit
            "knowledge": RAG requis
            "action": Outil nécessaire
            "fuzzy": Requête floue (HyDE)
        """
        self.stats["total_queries"] += 1
        
        # Fast path: Patterns simples (0ms)
        quick_decision = self._quick_classify(query)
        if quick_decision:
            self.stats[quick_decision] += 1
            logger.debug(f"Self-RAG decision (fast): {quick_decision}")
            return quick_decision
        
        # LLM classification (50-100ms)
        decision = self._llm_classify(query, context)
        self.stats[decision] += 1
        
        logger.info(
            f"Self-RAG decision: {decision} "
            f"(stats: {self.get_distribution()})"
        )
        return decision
    
    def _quick_classify(self, query: str) -> DecisionType | None:
        """Classification rapide par patterns (0ms)"""
        import re
        
        # Actions explicites → ReAct
        action_patterns = [
            r"\b(envoie|envoi|crée|créer|supprime|lance|ouvre)\b",
            r"\b(send|create|delete|open|launch)\b"
        ]
        if any(re.search(p, query.lower()) for p in action_patterns):
            return "action"
        
        # Questions factuelles simples → LLM direct
        simple_patterns = [
            r"^(bonjour|salut|hello|hi)\b",
            r"^(merci|thanks)\b",
            r"comment (vas-tu|ça va)",
            r"(oui|non|ok|d'accord)$"
        ]
        if any(re.search(p, query.lower()) for p in simple_patterns):
            return "direct"
        
        # Requêtes floues → HyDE
        fuzzy_indicators = [
            r"\b(truc|machin|chose)\b",
            r"\b(l'autre jour|hier|récemment)\b",
            r"\b(quelque chose sur|à propos de)\b"
        ]
        if any(re.search(p, query.lower()) for p in fuzzy_indicators):
            return "fuzzy"
        
        return None  # → LLM classification
    
    def _llm_classify(self, query: str, context: Dict[str, Any]) -> DecisionType:
        """Classification via LLM (50-100ms)"""
        
        prompt = f"""Classifie cette requête utilisateur:

Requête: "{query}"
Historique récent: {context.get('last_exchanges', [])}

Options:
- "direct": Question simple, conversation générale (LLM seul suffit)
- "knowledge": Question factuelle nécessitant recherche dans docs/notes
- "action": Demande d'action concrète (email, fichier, agenda, etc.)
- "fuzzy": Requête vague/floue nécessitant expansion

Réponse (1 mot):"""

        response = self.llm.generate(
            prompt,
            max_tokens=5,
            temperature=0.1,  # Déterministe
            stop=["\n"]
        )
        
        decision = response.strip().lower()
        
        # Validation
        valid_decisions: set[DecisionType] = {"direct", "knowledge", "action", "fuzzy"}
        if decision not in valid_decisions:
            logger.warning(f"Invalid decision '{decision}', defaulting to 'knowledge'")
            return "knowledge"
        
        return decision  # type: ignore[return-value]
    
    def critique_documents(
        self,
        documents: list[str],
        query: str
    ) -> list[str]:
        """
        Filtre documents non pertinents APRÈS récupération
        
        Args:
            documents: Documents récupérés
            query: Requête originale
            
        Returns:
            Documents filtrés (score > threshold)
        """
        if not documents:
            return []
        
        # Scoring rapide (BM25 ou similarité cosine)
        scored_docs = []
        for doc in documents:
            score = self._relevance_score(doc, query)
            if score > self.threshold:
                scored_docs.append((score, doc))
        
        # Tri par pertinence
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        
        filtered = [doc for _, doc in scored_docs]
        
        logger.debug(
            f"Critique: {len(filtered)}/{len(documents)} docs retenus "
            f"(threshold={self.threshold})"
        )
        
        return filtered
    
    def _relevance_score(self, doc: str, query: str) -> float:
        """Score de pertinence simple (TF-IDF ou cosine)"""
        # TODO: Implémenter BM25 ou embeddings similarity
        # Pour l'instant: simple overlap de mots
        
        doc_words = set(doc.lower().split())
        query_words = set(query.lower().split())
        
        if not query_words:
            return 0.0
        
        overlap = len(doc_words & query_words)
        score = overlap / len(query_words)
        
        return min(score, 1.0)
    
    def get_distribution(self) -> Dict[str, float]:
        """Retourne distribution des décisions (pour monitoring)"""
        total = self.stats["total_queries"]
        if total == 0:
            return {}
        
        return {
            "direct": round(self.stats["direct"] / total * 100, 1),
            "knowledge": round(self.stats["knowledge"] / total * 100, 1),
            "action": round(self.stats["action"] / total * 100, 1),
            "fuzzy": round(self.stats["fuzzy"] / total * 100, 1)
        }
    
    def reset_stats(self):
        """Reset statistiques"""
        self.stats = {k: 0 for k in self.stats}
```

### Tests

#### `tests/test_self_rag.py`
```python
"""Tests pour Self-RAG"""

import pytest
from src.rag.self_rag import SelfRAG


class MockLLM:
    """Mock LLM pour tests"""
    def generate(self, prompt, **kwargs):
        if "envoie" in prompt.lower():
            return "action"
        elif "note" in prompt.lower() or "doc" in prompt.lower():
            return "knowledge"
        elif "bonjour" in prompt.lower():
            return "direct"
        return "fuzzy"


@pytest.fixture
def self_rag():
    return SelfRAG(llm_client=MockLLM())


def test_quick_classify_action(self_rag):
    """Actions détectées par patterns"""
    decision = self_rag.decide("Envoie un email à Paul", {})
    assert decision == "action"


def test_quick_classify_simple(self_rag):
    """Conversations simples détectées"""
    decision = self_rag.decide("Bonjour HOPPER", {})
    assert decision == "direct"


def test_quick_classify_fuzzy(self_rag):
    """Requêtes floues détectées"""
    decision = self_rag.decide("le truc de l'autre jour", {})
    assert decision == "fuzzy"


def test_llm_classify_knowledge(self_rag):
    """Questions factuelles → knowledge"""
    decision = self_rag.decide("Que dit la note sur le projet X?", {})
    assert decision == "knowledge"


def test_critique_documents(self_rag):
    """Filtrage de documents non pertinents"""
    docs = [
        "Python est un langage de programmation",
        "La météo à Paris est ensoleillée",
        "Python offre une syntaxe simple"
    ]
    
    filtered = self_rag.critique_documents(docs, "Python programmation")
    
    # Seuls les 2 docs pertinents doivent rester
    assert len(filtered) == 2
    assert "météo" not in " ".join(filtered).lower()


def test_statistics(self_rag):
    """Statistiques de distribution"""
    self_rag.decide("Bonjour", {})
    self_rag.decide("Envoie email", {})
    self_rag.decide("Cherche doc", {})
    
    stats = self_rag.get_distribution()
    
    assert stats["direct"] > 0
    assert stats["action"] > 0
    assert sum(stats.values()) == pytest.approx(100.0)
```

### Intégration dans dispatcher

#### Modifier `src/orchestrator/core/dispatcher.py`
```python
# Ajouter en haut
from rag.self_rag import SelfRAG

class IntentDispatcher:
    def __init__(self, service_registry, context_manager):
        # ... existing code ...
        
        # Ajouter Self-RAG
        try:
            llm_client = self.service_registry.get_client("llm")
            self.self_rag = SelfRAG(llm_client)
            logger.info("✅ Self-RAG initialisé")
        except Exception as e:
            logger.warning(f"⚠️ Self-RAG non disponible: {e}")
            self.self_rag = None
    
    async def dispatch(self, command: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Route la commande avec Self-RAG"""
        
        context = self.context_manager.get_context(user_id)
        
        # 🆕 Self-RAG decision
        if self.self_rag:
            decision = self.self_rag.decide(command, context)
            
            if decision == "direct":
                # LLM seul, pas de RAG
                return await self._handle_direct(command, user_id)
            
            elif decision == "action":
                # ReAct agent (Phase 3.5 Semaine 3)
                return await self._handle_action(command, user_id)
        
        # Fallback: comportement actuel
        intent = self._detect_intent(command)
        ...
```

### Livrables Semaine 1
- ✅ `src/rag/self_rag.py`
- ✅ `tests/test_self_rag.py`
- ✅ Intégration dans `dispatcher.py`
- ✅ Documentation usage
- ✅ Métriques: latence moyenne < 100ms

---

## 🗄️ Semaine 2: GraphRAG

### Objectif
Remplacer ChromaDB par graphe de connaissances avec relations.

### Prérequis: Installer Neo4j

```bash
# docker-compose.yml
services:
  neo4j:
    image: neo4j:5.15-community
    container_name: hopper-neo4j
    ports:
      - "7474:7474"  # Interface web
      - "7687:7687"  # Bolt protocol
    environment:
      - NEO4J_AUTH=neo4j/hopper123
      - NEO4J_PLUGINS=["graph-data-science", "apoc"]
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - hopper-network

volumes:
  neo4j_data:
  neo4j_logs:
```

### Fichiers à créer

#### `src/rag/graph_store.py`
```python
"""
GraphRAG: Base de connaissances avec relations structurées
Remplace ChromaDB par Neo4j pour contexte relationnel
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from loguru import logger
import numpy as np


class GraphRAG:
    """Store de connaissances en graphe"""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "hopper123"
    ):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._create_indexes()
    
    def _create_indexes(self):
        """Crée indexes pour performance"""
        with self.driver.session() as session:
            # Index sur embeddings pour recherche vectorielle
            session.run(
                "CREATE VECTOR INDEX note_embeddings IF NOT EXISTS "
                "FOR (n:Note) ON (n.embedding) "
                "OPTIONS {indexConfig: {`vector.dimensions`: 384, "
                "`vector.similarity_function`: 'cosine'}}"
            )
            
            # Index sur timestamps
            session.run(
                "CREATE INDEX note_timestamp IF NOT EXISTS "
                "FOR (n:Note) ON (n.timestamp)"
            )
            
            logger.info("✅ Indexes GraphRAG créés")
    
    def add_note(
        self,
        content: str,
        user_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ajoute une note avec extraction d'entités
        
        Returns:
            note_id
        """
        from datetime import datetime
        from .entity_extractor import EntityExtractor
        
        # Extraire entités
        extractor = EntityExtractor()
        entities = extractor.extract(content)
        
        with self.driver.session() as session:
            # Créer note
            result = session.run(
                """
                CREATE (n:Note {
                    content: $content,
                    user_id: $user_id,
                    timestamp: datetime($timestamp),
                    embedding: $embedding,
                    metadata: $metadata
                })
                RETURN id(n) as note_id
                """,
                content=content,
                user_id=user_id,
                timestamp=datetime.now().isoformat(),
                embedding=embedding.tolist(),
                metadata=metadata or {}
            )
            
            note_id = result.single()["note_id"]
            
            # Créer relations avec entités
            for entity_type, entity_name in entities:
                session.run(
                    """
                    MATCH (n:Note) WHERE id(n) = $note_id
                    MERGE (e:Entity {name: $name, type: $type})
                    CREATE (n)-[:MENTIONS]->(e)
                    """,
                    note_id=note_id,
                    name=entity_name,
                    type=entity_type
                )
            
            logger.info(
                f"✅ Note ajoutée: {note_id} "
                f"({len(entities)} entités liées)"
            )
            
            return str(note_id)
    
    def retrieve(
        self,
        query_embedding: np.ndarray,
        user_id: str,
        top_k: int = 5,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Récupère notes + contexte via relations
        
        Args:
            query_embedding: Embedding de la requête
            user_id: Utilisateur
            top_k: Nombre de notes à récupérer
            depth: Profondeur de traversée du graphe
            
        Returns:
            Liste de notes avec contexte relationnel
        """
        with self.driver.session() as session:
            result = session.run(
                """
                // 1. Recherche vectorielle
                CALL db.index.vector.queryNodes(
                    'note_embeddings',
                    $top_k,
                    $query_embedding
                )
                YIELD node as n, score
                WHERE n.user_id = $user_id
                
                // 2. Traversée pour contexte
                OPTIONAL MATCH path = (n)-[r*1..$depth]-(related)
                WHERE related:Note OR related:Entity
                
                // 3. Retourner avec contexte
                RETURN 
                    n.content as content,
                    n.timestamp as timestamp,
                    n.metadata as metadata,
                    score,
                    collect(DISTINCT related.content) as related_content,
                    collect(DISTINCT related.name) as related_entities
                ORDER BY score DESC
                """,
                query_embedding=query_embedding.tolist(),
                user_id=user_id,
                top_k=top_k,
                depth=depth
            )
            
            notes = []
            for record in result:
                notes.append({
                    "content": record["content"],
                    "timestamp": str(record["timestamp"]),
                    "metadata": record["metadata"],
                    "score": record["score"],
                    "related_content": record["related_content"],
                    "related_entities": record["related_entities"]
                })
            
            logger.info(f"📚 Récupéré {len(notes)} notes avec contexte")
            return notes
    
    def query_by_entity(
        self,
        entity_name: str,
        user_id: str,
        max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Requête par entité (ex: "Paul", "Projet X")
        
        Returns:
            Notes mentionnant l'entité + notes liées
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Entity {name: $entity_name})
                MATCH path = (n:Note)-[:MENTIONS]->(e)-[*0..$max_hops]-(related:Note)
                WHERE n.user_id = $user_id
                RETURN DISTINCT
                    n.content as content,
                    n.timestamp as timestamp,
                    collect(DISTINCT related.content) as related_notes
                ORDER BY n.timestamp DESC
                """,
                entity_name=entity_name,
                user_id=user_id,
                max_hops=max_hops
            )
            
            return [dict(record) for record in result]
    
    def close(self):
        """Ferme connexion"""
        self.driver.close()
```

#### `src/rag/entity_extractor.py`
```python
"""
Extraction d'entités nommées (NER) pour GraphRAG
Utilise spaCy pour français
"""

from typing import List, Tuple
from loguru import logger

try:
    import spacy
    nlp = spacy.load("fr_core_news_lg")
except (ImportError, OSError):
    logger.warning("⚠️ spaCy 'fr_core_news_lg' non disponible")
    nlp = None


class EntityExtractor:
    """Extrait entités nommées depuis texte"""
    
    def __init__(self):
        self.nlp = nlp
    
    def extract(self, text: str) -> List[Tuple[str, str]]:
        """
        Extrait entités
        
        Returns:
            [(type, name), ...] ex: [("PERSON", "Paul"), ("ORG", "Google")]
        """
        if not self.nlp:
            # Fallback: extraction simple par patterns
            return self._fallback_extract(text)
        
        doc = self.nlp(text)
        
        entities = []
        for ent in doc.ents:
            # Filtrer types pertinents
            if ent.label_ in ["PERSON", "ORG", "LOC", "DATE", "EVENT"]:
                entities.append((ent.label_, ent.text))
        
        logger.debug(f"Entités extraites: {entities}")
        return entities
    
    def _fallback_extract(self, text: str) -> List[Tuple[str, str]]:
        """Extraction basique sans spaCy"""
        import re
        
        # Majuscules = noms propres
        proper_nouns = re.findall(r'\b[A-Z][a-zéèêàâ]+(?:\s+[A-Z][a-zéèêàâ]+)*\b', text)
        
        return [("UNKNOWN", name) for name in proper_nouns[:5]]  # Max 5
```

### Tests

#### `tests/test_graph_rag.py`
```python
"""Tests pour GraphRAG"""

import pytest
import numpy as np
from src.rag.graph_store import GraphRAG


@pytest.fixture
def graph_rag():
    """Instance GraphRAG pour tests"""
    rag = GraphRAG()
    yield rag
    rag.close()


def test_add_note(graph_rag):
    """Ajout d'une note avec entités"""
    embedding = np.random.rand(384)
    
    note_id = graph_rag.add_note(
        content="Réunion avec Paul pour le projet HOPPER",
        user_id="test_user",
        embedding=embedding,
        metadata={"type": "meeting"}
    )
    
    assert note_id is not None


def test_retrieve_with_context(graph_rag):
    """Récupération avec contexte relationnel"""
    # Ajouter 2 notes liées
    emb1 = np.random.rand(384)
    emb2 = np.random.rand(384)
    
    graph_rag.add_note("Bug #123 sur le port 5000", "test_user", emb1)
    graph_rag.add_note("Fix du bug #123 avec port 5050", "test_user", emb2)
    
    # Rechercher
    query_emb = emb1 + 0.1  # Similaire
    results = graph_rag.retrieve(query_emb, "test_user", top_k=2, depth=2)
    
    assert len(results) > 0
    assert "related_content" in results[0]


def test_query_by_entity(graph_rag):
    """Requête par entité"""
    emb = np.random.rand(384)
    graph_rag.add_note("Paul a proposé la feature X", "test_user", emb)
    
    results = graph_rag.query_by_entity("Paul", "test_user")
    
    assert len(results) > 0
    assert "Paul" in results[0]["content"]
```

### Migration ChromaDB → GraphRAG

```python
# Script de migration: migrate_to_graphrag.py

from src.kb.vector_store import VectorStore  # Actuel
from src.rag.graph_store import GraphRAG

def migrate():
    """Migre données de ChromaDB vers Neo4j"""
    
    # Charger données existantes
    old_store = VectorStore()
    all_docs = old_store.get_all_documents()
    
    # Initialiser GraphRAG
    graph_rag = GraphRAG()
    
    # Migrer
    for doc in all_docs:
        graph_rag.add_note(
            content=doc["content"],
            user_id=doc["user_id"],
            embedding=doc["embedding"],
            metadata=doc["metadata"]
        )
    
    print(f"✅ Migré {len(all_docs)} documents")
```

### Livrables Semaine 2
- ✅ Neo4j en Docker
- ✅ `src/rag/graph_store.py`
- ✅ `src/rag/entity_extractor.py`
- ✅ `tests/test_graph_rag.py`
- ✅ Migration ChromaDB → Neo4j
- ✅ Interface Neo4j Browser accessible (localhost:7474)

---

## 🤖 Semaine 3: ReAct Agent

*(Continue dans prochain fichier...)*

### Objectif
Agent qui **raisonne** puis **agit** avec outils réels.

### Structure
```python
src/agents/
├── react_agent.py       # Cycle Thought→Action→Observation
├── action_parser.py     # Parse actions depuis LLM
└── tools/
    ├── base_tool.py     # Interface Tool
    ├── email_tool.py    # Wrapper module email
    ├── file_tool.py     # Wrapper system_executor
    └── notes_tool.py    # Interactions GraphRAG
```

---

## 📊 Métriques de Validation Phase 3.5

### Performance
- [ ] Self-RAG: <100ms décision
- [ ] GraphRAG: <500ms query (vs 300ms ChromaDB)
- [ ] ReAct: <3s action complète
- [ ] HyDE: <200ms expansion

### Qualité
- [ ] Self-RAG: 85% précision éviter RAG inutile
- [ ] GraphRAG: +40% pertinence vs RAG classique
- [ ] ReAct: 90% succès actions multi-étapes
- [ ] HyDE: +30% couverture requêtes floues

### Tests End-to-End
- [ ] "Envoie email à Paul avec le doc dont on a parlé hier"
  - Self-RAG → action
  - GraphRAG → trouve doc via entité "hier"
  - ReAct → email[send] + files[attach]
  
- [ ] "C'est quoi ce bug du port?"
  - Self-RAG → knowledge
  - GraphRAG → traverse Bug→Fix→Config
  - Réponse contextuelle

---

## 🚀 Pour Commencer Maintenant

**Étape 1: Installer dépendances**
```bash
pip install neo4j spacy
python -m spacy download fr_core_news_lg
```

**Étape 2: Ajouter Neo4j au docker-compose**
```bash
# Éditer docker-compose.yml (voir section Semaine 2)
docker-compose up -d neo4j
```

**Étape 3: Créer `src/rag/self_rag.py`**
```bash
mkdir -p src/rag src/agents/tools
touch src/rag/{__init__,self_rag,graph_store,entity_extractor,hyde,unified_retriever}.py
```

**Prêt à commencer par Self-RAG (Semaine 1)?** 🚀
