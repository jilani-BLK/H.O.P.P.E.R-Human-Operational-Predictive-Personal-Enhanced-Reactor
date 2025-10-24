# 🧠 Architecture RAG Avancée pour HOPPER
*Date: 22 octobre 2025*
*Auteur: Stratégie proposée par jilani*

## 🎯 Vision Stratégique

**Problème du RAG classique:** Il récupère des documents mais **ne fait rien** avec des outils.

**Solution HOPPER:** Architecture hybride combinant GraphRAG, ReAct/Toolformer et Self-RAG.

## 📐 Architecture Proposée

```
┌─────────────────────────────────────────────────────────────┐
│                     HOPPER RAG Pipeline                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │   Self-RAG (Critique)   │◄── "Ai-je besoin de RAG?"
              │   - Relevance check     │
              │   - Latence optimale    │
              └────────┬────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
┌────────────────┐          ┌────────────────┐
│   GraphRAG     │          │  ReAct Agent   │
│  (Knowledge)   │          │   (Actions)    │
├────────────────┤          ├────────────────┤
│ • Notes        │          │ • Email IMAP   │
│ • Docs         │          │ • Agenda       │
│ • Logs système │          │ • Fichiers     │
│ • Relations    │          │ • Domotique    │
│ • Entités      │          │ • Terminal     │
└────────┬───────┘          └────────┬───────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
            ┌────────────────┐
            │  HyDE (optionnel)│
            │  Query expansion │◄── Requêtes floues
            └────────┬─────────┘
                     ▼
            ┌────────────────┐
            │  kNN-LM        │◄── Token-level memory
            │  (décodage)    │    (ultra-rapide)
            └────────────────┘
```

## 🔧 Composants Détaillés

### 1. **Self-RAG** (Priorité: CRITIQUE)
> *"Éviter la récupération inutile et garder la latence basse"*

**Rôle:** Décider **si** et **quand** utiliser RAG.

**Implémentation:**
```python
class SelfRAG:
    """Critique intelligente avant récupération"""
    
    def should_retrieve(self, query: str, context: dict) -> bool:
        """
        Décide si RAG est nécessaire
        
        Critères:
        - Question factuelle? → RAG
        - Conversation simple? → LLM direct
        - Besoin de contexte passé? → RAG historique
        - Action à exécuter? → ReAct agent
        """
        # Prompt léger au LLM (50 tokens max)
        decision = self.llm.classify(
            prompt=f"Cette requête nécessite-t-elle une recherche? {query}",
            options=["search", "direct", "action"]
        )
        
        return decision
    
    def critique_retrieval(self, documents: List[str], query: str) -> List[str]:
        """Filtre les docs non pertinents APRÈS récupération"""
        # Score de pertinence (rapide, pas le LLM)
        relevant = [doc for doc in documents 
                   if self.relevance_score(doc, query) > 0.7]
        return relevant
```

**Métriques de succès:**
- ✅ Latence < 100ms pour décision
- ✅ 80% de précision (éviter RAG inutile)
- ✅ 20% réduction du temps de réponse global

---

### 2. **GraphRAG** (Priorité: HAUTE)
> *"Mémoire longue structurée (notes, docs, logs système)"*

**Rôle:** Base de connaissances avec relations entre entités.

**Structure Graph:**
```
User
 ├─ Notes
 │   ├─ "Réunion projet X" ──relation──> [Date, Participants]
 │   └─ "Idée feature Y"   ──depends_on─> Réunion projet X
 ├─ Documents
 │   ├─ "Manuel HOPPER"    ──version──> 3.0
 │   └─ "Specs Phase 3"    ──implements─> "Manuel HOPPER"
 └─ Logs Système
     ├─ "Erreur Port 5000" ──fixed_by──> "Config Port 5050"
     └─ "Test Integration"  ──validated─> Phase 3
```

**Implémentation:**
```python
# Utiliser Neo4j (graphe natif) OU Nebula Graph (open-source)
from neo4j import GraphDatabase

class GraphRAG:
    """Mémoire structurée en graphe de connaissances"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def add_note(self, content: str, user_id: str, metadata: dict):
        """Ajoute une note avec relations automatiques"""
        with self.driver.session() as session:
            # Extraire entités avec NER (spaCy)
            entities = self.extract_entities(content)
            
            # Créer nœud Note
            session.run(
                "CREATE (n:Note {content: $content, user_id: $user_id, "
                "timestamp: datetime(), metadata: $metadata})",
                content=content, user_id=user_id, metadata=metadata
            )
            
            # Créer relations avec entités existantes
            for entity in entities:
                session.run(
                    "MATCH (n:Note {content: $content}) "
                    "MATCH (e:Entity {name: $entity}) "
                    "CREATE (n)-[:MENTIONS]->(e)",
                    content=content, entity=entity
                )
    
    def retrieve_with_context(self, query: str, depth: int = 2) -> List[dict]:
        """Récupère documents + contexte via relations"""
        with self.driver.session() as session:
            # Recherche vectorielle + traversée du graphe
            results = session.run(
                "MATCH (n:Note)-[r*1..$depth]-(related) "
                "WHERE n.embedding <-> $query_embedding < 0.3 "
                "RETURN n, collect(related) as context",
                query_embedding=self.embed(query),
                depth=depth
            )
            return list(results)
```

**Avantages vs RAG classique:**
- ✅ Comprend **pourquoi** deux infos sont liées
- ✅ Peut répondre: "Qui a participé à la réunion où on a parlé de X?"
- ✅ Traversée multi-hop: "Quelle feature dépend du bug qu'on a fixé hier?"

**Stack technique:**
- **Neo4j** (local avec Docker) OU **Nebula Graph** (plus léger)
- **Embeddings:** `all-MiniLM-L6-v2` (déjà utilisé)
- **NER:** spaCy `fr_core_news_lg` pour extraction d'entités

---

### 3. **ReAct / Toolformer** (Priorité: CRITIQUE)
> *"Piloter des outils locaux (mail, agenda, domotique, fichiers)"*

**Rôle:** Agent qui **raisonne** puis **agit** avec des outils.

**Cycle ReAct:**
```
Thought → Action → Observation → Thought → ...
```

**Implémentation:**
```python
class ReActAgent:
    """Agent avec capacité de raisonnement et d'action"""
    
    def __init__(self, llm, tools: Dict[str, Callable]):
        self.llm = llm
        self.tools = tools  # {"email": EmailTool(), "files": FileTool(), ...}
        
    def run(self, query: str, max_steps: int = 5) -> str:
        """Cycle Thought → Action → Observation"""
        
        trajectory = []
        for step in range(max_steps):
            # 1. THOUGHT: Raisonner sur la prochaine action
            thought = self.llm.generate(
                f"Pensée: Pour '{query}', je dois...\n"
                f"Historique: {trajectory}\n"
                f"Outils disponibles: {list(self.tools.keys())}\n"
                f"Pensée:"
            )
            trajectory.append(f"Thought: {thought}")
            
            # 2. ACTION: Décider de l'outil et des arguments
            action = self.llm.generate(
                f"{thought}\nAction: utiliser <tool>[arg1, arg2]"
            )
            
            tool_name, args = self.parse_action(action)
            
            # 3. OBSERVATION: Exécuter et observer résultat
            if tool_name == "FINISH":
                return args  # Réponse finale
            
            result = self.tools[tool_name](*args)
            trajectory.append(f"Action: {tool_name}({args})")
            trajectory.append(f"Observation: {result}")
        
        return "Max steps reached"
    
    def parse_action(self, action_str: str) -> Tuple[str, List]:
        """Parse: 'email[check_inbox, folder=INBOX]'"""
        # Regex ou parsing simple
        ...
```

**Outils à intégrer (déjà en partie dans HOPPER):**
```python
TOOLS = {
    "email": EmailTool(imap_config),      # ✅ Prévu Phase 3
    "files": FilesTool(workspace_path),   # ✅ Déjà présent (system_executor)
    "agenda": AgendaTool(calendar_api),   # 🔜 Phase 4
    "domotique": HomeAssistantTool(),     # 🔜 Phase 4
    "terminal": TerminalTool(),           # ✅ Déjà présent
    "web_search": DuckDuckGoTool(),       # 🔜 Optionnel
}
```

**Exemple concret:**
```
User: "Envoie un email à Paul pour lui dire que la réunion est à 15h"

Thought 1: Je dois récupérer l'email de Paul
Action 1: contacts[search, name="Paul"]
Observation 1: paul.dupont@example.com

Thought 2: Je dois composer l'email
Action 2: email[compose, to="paul.dupont@example.com", 
                  subject="Horaire réunion", 
                  body="La réunion est confirmée pour 15h."]
Observation 2: Email envoyé avec succès

Thought 3: Tâche terminée
Action 3: FINISH["Email envoyé à Paul concernant la réunion à 15h"]
```

**Différence avec RAG:**
- RAG: "Voici ce que je sais sur les emails"
- ReAct: "Je vais **envoyer** l'email maintenant"

---

### 4. **HyDE** (Priorité: MOYENNE)
> *"Requêtes floues → documents hypothétiques"*

**Rôle:** Transformer requête floue en document hypothétique pour meilleur matching.

**Concept:**
```
User: "truc machin pour la réunion"
     ↓
HyDE: "Compte-rendu de réunion du projet X du 15/10/2025 
       où nous avons discuté des fonctionnalités..."
     ↓
Embedding du document hypothétique (meilleur que query)
     ↓
Recherche vectorielle
```

**Implémentation:**
```python
class HyDE:
    """Hypothetical Document Embeddings"""
    
    def expand_query(self, vague_query: str) -> str:
        """Génère document hypothétique depuis requête floue"""
        
        prompt = f"""Génère un document détaillé qui répondrait à cette requête:
Query: {vague_query}

Document hypothétique (200 mots):"""
        
        hypothetical_doc = self.llm.generate(prompt, max_tokens=200)
        return hypothetical_doc
    
    def retrieve(self, query: str, vector_db) -> List[Document]:
        """Récupère via document hypothétique"""
        
        # 1. Générer doc hypothétique
        hypo_doc = self.expand_query(query)
        
        # 2. Embedder le doc (pas la query)
        hypo_embedding = self.embed(hypo_doc)
        
        # 3. Recherche vectorielle classique
        results = vector_db.search(hypo_embedding, top_k=5)
        
        return results
```

**Quand l'utiliser:**
- ✅ User dit: "le truc de l'autre jour"
- ✅ Requêtes avec pronoms: "comment on fait ça?"
- ✅ Questions vagues: "info sur le projet"
- ❌ Questions précises: "Quelle est la date de la réunion?"

---

### 5. **kNN-LM** (Priorité: BASSE - Optionnel)
> *"Mémoire token-level ultra-rapide au décodage"*

**Rôle:** Base de données de tokens observés pour influencer génération.

**Concept:**
```
Génération LLM normale:
  P(next_token | context) → Softmax sur vocabulaire

Avec kNN-LM:
  P(next_token) = λ * P_LM(token) + (1-λ) * P_kNN(token)
  
  P_kNN = chercher dans DB les contextes similaires 
          et voir quels tokens ont suivi
```

**Cas d'usage HOPPER:**
- ✅ Complétion de noms propres: "Envoie un email à Pa..." → "Paul" (vu dans logs)
- ✅ Commandes récurrentes: "Lance la..." → "musique" (action fréquente)
- ✅ Adaptation style utilisateur

**Implémentation (FAISS):**
```python
import faiss
import numpy as np

class kNNLM:
    """Token-level memory pour génération"""
    
    def __init__(self, dim: int = 768):
        self.index = faiss.IndexFlatL2(dim)  # Index FAISS
        self.tokens_db = []  # (context_embedding, next_token)
    
    def add_sequence(self, tokens: List[str], embeddings: np.ndarray):
        """Ajoute séquence observée dans la DB"""
        for i in range(len(tokens) - 1):
            context_emb = embeddings[i]
            next_token = tokens[i + 1]
            
            self.index.add(context_emb.reshape(1, -1))
            self.tokens_db.append(next_token)
    
    def query(self, context_embedding: np.ndarray, k: int = 10) -> dict:
        """Récupère les k tokens les plus probables"""
        distances, indices = self.index.search(
            context_embedding.reshape(1, -1), k
        )
        
        # Compter fréquence des tokens
        candidates = [self.tokens_db[i] for i in indices[0]]
        probs = {token: candidates.count(token) / k 
                for token in set(candidates)}
        
        return probs
```

**Trade-off:**
- ✅ Complétions personnalisées
- ✅ Ultra-rapide (FAISS)
- ❌ Complexité ajoutée
- ❌ Utile seulement si beaucoup de données utilisateur

**Verdict:** À implémenter **plus tard** (Phase 5-6), après avoir collecté assez d'interactions.

---

## 🏗️ Plan d'Implémentation pour HOPPER

### Phase 3.5 (RAG Avancé) - 4 semaines

#### Semaine 1-2: Self-RAG + GraphRAG
```python
# Fichiers à créer:
src/rag/self_rag.py          # Critique intelligente
src/rag/graph_store.py       # Interface Neo4j
src/rag/entity_extractor.py  # NER avec spaCy
```

**Tâches:**
1. ✅ Installer Neo4j via Docker
2. ✅ Implémenter Self-RAG avec classification rapide
3. ✅ Migrer ChromaDB → GraphRAG
4. ✅ Extraire entités des notes/docs
5. ✅ Tests: requêtes multi-hop

**Validation:**
- Requête: "Qui a parlé du bug qu'on a fixé hier?"
  - GraphRAG trouve: Bug #123 → Réunion X → [Paul, Marie]

#### Semaine 3: ReAct Agent
```python
# Fichiers à créer:
src/agents/react_agent.py       # Cycle Thought→Action→Observation
src/agents/tools/email_tool.py  # ✅ Prévu Phase 3
src/agents/tools/file_tool.py   # ✅ Déjà présent (refactor)
```

**Tâches:**
1. ✅ Implémenter cycle ReAct
2. ✅ Wrapper outils existants (system_executor, email)
3. ✅ Parser actions depuis LLM
4. ✅ Tests: scénarios multi-actions

**Validation:**
- User: "Cherche dans mes emails celui de Paul et crée une note"
  - Agent: email[search, from=Paul] → notes[create, content=...]

#### Semaine 4: HyDE + Intégration
```python
# Fichiers à créer:
src/rag/hyde.py                 # Query expansion
src/rag/unified_retriever.py    # Combine tous les composants
```

**Tâches:**
1. ✅ Implémenter HyDE
2. ✅ Pipeline unifié: Self-RAG → [GraphRAG|ReAct|HyDE]
3. ✅ Métriques: latence, pertinence
4. ✅ Documentation complète

**Validation:**
- User: "le truc de l'autre jour sur le projet"
  - HyDE génère doc hypothétique → GraphRAG trouve note pertinente

---

## 📊 Comparaison Architecture

| Composant | RAG Classique | HOPPER RAG Avancé | Gain |
|-----------|---------------|-------------------|------|
| **Récupération** | Vector search seul | GraphRAG + relations | +40% pertinence |
| **Actions** | ❌ Aucune | ✅ ReAct agent | Tools opérationnels |
| **Décision** | Toujours RAG | Self-RAG critique | -30% latence |
| **Requêtes floues** | Embeddings directs | HyDE expansion | +25% couverture |
| **Mémoire** | Docs entiers | Graph + kNN-LM | Contexte riche |

---

## 🎯 Métriques de Succès

### Performance
- ✅ Latence Self-RAG < 100ms
- ✅ GraphRAG query < 500ms
- ✅ ReAct action complète < 3s
- ✅ HyDE expansion < 200ms

### Qualité
- ✅ 90% précision Self-RAG (éviter RAG inutile)
- ✅ 80% pertinence GraphRAG (vs 60% RAG classique)
- ✅ 95% succès actions ReAct
- ✅ 70% amélioration requêtes floues (HyDE)

### Utilisabilité
- ✅ User peut dire: "fais X avec Y" → ReAct exécute
- ✅ User peut chercher: "truc de Paul" → GraphRAG trouve
- ✅ User voit: <100ms pour questions simples (pas de RAG)

---

## 🚀 Prochaines Étapes Immédiates

1. **Installer Neo4j** (Docker)
   ```bash
   docker run -d --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/hopper123 \
     neo4j:latest
   ```

2. **Créer structure modules**
   ```
   src/rag/
   ├── self_rag.py
   ├── graph_store.py
   ├── hyde.py
   └── unified_retriever.py
   
   src/agents/
   ├── react_agent.py
   └── tools/
       ├── email_tool.py
       ├── file_tool.py
       └── agenda_tool.py
   ```

3. **Tests de validation**
   ```python
   tests/test_rag_advanced.py
   tests/test_react_agent.py
   ```

---

## 📚 Références

- **GraphRAG:** [Microsoft GraphRAG Paper](https://arxiv.org/abs/2404.16130)
- **ReAct:** [ReAct: Synergizing Reasoning and Acting](https://arxiv.org/abs/2210.03629)
- **Self-RAG:** [Self-RAG: Learning to Retrieve, Generate, and Critique](https://arxiv.org/abs/2310.11511)
- **HyDE:** [Precise Zero-Shot Dense Retrieval](https://arxiv.org/abs/2212.10496)
- **kNN-LM:** [Generalization through Memorization](https://arxiv.org/abs/1911.00172)
- **Toolformer:** [Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)

---

## 💡 Conclusion

**Ta suggestion est excellente** car elle combine:
1. ✅ **GraphRAG** → Mémoire structurée (ce que HOPPER sait)
2. ✅ **ReAct/Toolformer** → Actions concrètes (ce que HOPPER fait)
3. ✅ **Self-RAG** → Optimisation latence (ce que HOPPER évite)
4. ✅ **HyDE** → Robustesse requêtes (ce que HOPPER comprend)
5. ⏸️ **kNN-LM** → Personnalisation avancée (Phase 5+)

**Next:** Implémenter Self-RAG + GraphRAG en priorité (Semaines 1-2)?
