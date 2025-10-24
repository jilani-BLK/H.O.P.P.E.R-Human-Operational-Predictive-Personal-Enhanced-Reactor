# HOPPER - Phase 2: Intégration LLM et Conversation

**Durée estimée**: Mois 3-4  
**Objectif**: Doter Hopper de capacités de compréhension du langage naturel et conversation en local

---

## 📋 Vue d'ensemble

### Objectifs Phase 2

1. ✅ **LLM Local**: Modèle LLaMA/Mistral fonctionnel hors-ligne
2. ✅ **Conversation**: Multi-tour avec mémoire contextuelle
3. ✅ **RAG**: Knowledge Base vectorielle avec FAISS
4. ✅ **Optimisation**: Performance <5s par réponse
5. ✅ **Validation**: 70%+ taux réussite conversations

### Prérequis Phase 1

- ✅ Infrastructure Docker opérationnelle
- ✅ Orchestrateur avec dispatcher
- ✅ Service LLM (mode simulation)
- ✅ ContextManager fonctionnel
- ✅ CLI testé et validé

---

## 🎯 Tâches Détaillées

### 1. Choix et Téléchargement Modèle LLM

**Modèle recommandé**: Mistral-7B-Instruct-v0.2 (GGUF)

**Caractéristiques**:
- Taille: ~4 GB (Q4_K_M quantization)
- Contexte: 32K tokens (vs 4K LLaMA 2)
- Multilangue: Excellent en français
- Performance: Optimisé pour Apple Metal

**Commandes téléchargement**:
```bash
# Créer dossier modèles
mkdir -p /Users/jilani/Projet/HOPPER/data/models

# Option 1: Mistral-7B-Instruct (recommandé)
cd data/models
curl -L -o mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"

# Option 2: LLaMA 2 7B Chat (alternative)
curl -L -o llama-2-7b-chat.Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"

# Vérifier téléchargement
ls -lh data/models/*.gguf
```

**Configuration `.env`**:
```bash
# LLM Configuration
LLM_MODEL_PATH=/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
LLM_CONTEXT_SIZE=4096
LLM_N_THREADS=8
LLM_N_GPU_LAYERS=1  # Metal GPU acceleration
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=512
```

### 2. Intégration llama.cpp dans Service LLM

**Fichier**: `src/llm_engine/main.py`

**Modifications**:

```python
from llama_cpp import Llama
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger

app = FastAPI()

# Initialisation modèle
MODEL_PATH = os.getenv("LLM_MODEL_PATH", "/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
CONTEXT_SIZE = int(os.getenv("LLM_CONTEXT_SIZE", "4096"))
N_THREADS = int(os.getenv("LLM_N_THREADS", "8"))
N_GPU_LAYERS = int(os.getenv("LLM_N_GPU_LAYERS", "1"))

llm = None

@app.on_event("startup")
async def load_model():
    global llm
    logger.info(f"Chargement modèle: {MODEL_PATH}")
    
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=CONTEXT_SIZE,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False
        )
        logger.info("✅ Modèle LLM chargé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur chargement modèle: {e}")
        raise

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    stop: list[str] = ["User:", "Utilisateur:"]

class GenerateResponse(BaseModel):
    text: str
    tokens_generated: int
    finish_reason: str

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    if llm is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    
    logger.info(f"Génération: {request.prompt[:100]}...")
    
    try:
        output = llm(
            request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
            echo=False
        )
        
        response_text = output['choices'][0]['text']
        tokens = output['usage']['completion_tokens']
        
        logger.info(f"✅ Généré {tokens} tokens")
        
        return GenerateResponse(
            text=response_text.strip(),
            tokens_generated=tokens,
            finish_reason=output['choices'][0]['finish_reason']
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur génération: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {
        "status": "healthy" if llm is not None else "degraded",
        "model_loaded": llm is not None,
        "model_path": MODEL_PATH
    }
```

**Dockerfile update**: `docker/llm.Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dépendances système pour llama.cpp
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    loguru==0.7.2 \
    pydantic==2.5.0 \
    llama-cpp-python==0.2.20 \
    sentence-transformers==2.2.2 \
    faiss-cpu==1.7.4 \
    numpy

COPY src/llm_engine/ .

EXPOSE 5001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
```

**docker-compose.yml update**:

```yaml
llm:
  build:
    context: .
    dockerfile: docker/llm.Dockerfile
  container_name: hopper-llm
  ports:
    - "${LLM_SERVICE_PORT:-5001}:5001"
  volumes:
    - ./data/models:/models:ro  # Lecture seule
    - ./config:/config:ro
  environment:
    - LLM_MODEL_PATH=${LLM_MODEL_PATH}
    - LLM_CONTEXT_SIZE=${LLM_CONTEXT_SIZE}
    - LLM_N_THREADS=${LLM_N_THREADS}
    - LLM_N_GPU_LAYERS=${LLM_N_GPU_LAYERS}
  networks:
    - hopper-network
  # Augmenter mémoire pour LLM
  deploy:
    resources:
      limits:
        memory: 8G
```

### 3. Test Inférence LLM

**Test basique**:
```bash
# Vérifier modèle chargé
curl http://localhost:5001/health | jq

# Test génération simple
curl -X POST http://localhost:5001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Question: Qui es-tu?\nRéponse:",
    "max_tokens": 200,
    "temperature": 0.7
  }' | jq

# Expected output:
# {
#   "text": "Je suis un assistant IA...",
#   "tokens_generated": 45,
#   "finish_reason": "stop"
# }
```

**Benchmark performance**:
```bash
# Mesurer temps génération
time curl -X POST http://localhost:5001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explique Python en 100 mots", "max_tokens": 150}'

# Objectif: <5 secondes pour 150 tokens
```

### 4. Orchestrateur: Gestion Prompts

**Fichier**: `config/prompts.yaml`

```yaml
system_prompt: |
  Tu es HOPPER (Human Operational Predictive Personal Enhanced Reactor), 
  un assistant personnel intelligent fonctionnant 100% en local.
  
  Tes capacités:
  - Répondre aux questions en français
  - Gérer des fichiers et applications
  - Lire et envoyer des emails (bientôt)
  - Contrôler des appareils connectés (bientôt)
  
  Personnalité:
  - Précis et concis
  - Respectueux de la vie privée
  - Proactif et utile
  
  Limitations:
  - Tu fonctionnes hors-ligne (pas d'accès Internet)
  - Tu ne peux pas naviguer sur le web
  - Tes connaissances datent de ton entraînement

conversation_template: |
  {system_prompt}
  
  Historique de conversation:
  {history}
  
  Utilisateur: {user_input}
  HOPPER:

user_prefix: "Utilisateur:"
assistant_prefix: "HOPPER:"
```

**Fichier**: `src/orchestrator/core/prompt_builder.py`

```python
import yaml
from pathlib import Path
from loguru import logger

class PromptBuilder:
    def __init__(self, config_path: str = "/config/prompts.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("prompts.yaml non trouvé, utilisation defaults")
            return self._default_config()
    
    def _default_config(self) -> dict:
        return {
            'system_prompt': "Tu es HOPPER, un assistant IA local.",
            'conversation_template': "{system_prompt}\n\n{history}\n\nUtilisateur: {user_input}\nHOPPER:",
            'user_prefix': "Utilisateur:",
            'assistant_prefix': "HOPPER:"
        }
    
    def build_prompt(
        self, 
        user_input: str, 
        history: list[dict] = None,
        max_history_tokens: int = 2048
    ) -> str:
        """
        Construit le prompt complet pour le LLM
        
        Args:
            user_input: Question/commande utilisateur
            history: Liste [{"role": "user"/"assistant", "content": "..."}]
            max_history_tokens: Limite tokens contexte
        
        Returns:
            Prompt formaté
        """
        # Formater historique
        history_text = ""
        if history:
            # Limiter historique (approximation: 4 chars = 1 token)
            history = self._truncate_history(history, max_history_tokens * 4)
            
            for exchange in history:
                if exchange['role'] == 'user':
                    history_text += f"{self.config['user_prefix']} {exchange['content']}\n"
                else:
                    history_text += f"{self.config['assistant_prefix']} {exchange['content']}\n"
        
        # Construire prompt complet
        prompt = self.config['conversation_template'].format(
            system_prompt=self.config['system_prompt'],
            history=history_text,
            user_input=user_input
        )
        
        logger.debug(f"Prompt construit: {len(prompt)} caractères")
        return prompt
    
    def _truncate_history(self, history: list[dict], max_chars: int) -> list[dict]:
        """Garde seulement les N derniers échanges qui tiennent dans max_chars"""
        total_chars = 0
        truncated = []
        
        # Parcourir à l'envers (garder les plus récents)
        for exchange in reversed(history):
            exchange_chars = len(exchange['content'])
            if total_chars + exchange_chars > max_chars:
                break
            truncated.insert(0, exchange)
            total_chars += exchange_chars
        
        if len(truncated) < len(history):
            logger.info(f"Historique tronqué: {len(history)} → {len(truncated)} échanges")
        
        return truncated
```

**Modifier**: `src/orchestrator/core/dispatcher.py`

```python
from .prompt_builder import PromptBuilder
from .context_manager import ContextManager
import aiohttp
from loguru import logger

class IntentDispatcher:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.context_manager = ContextManager()
        self.llm_url = os.getenv("LLM_SERVICE_URL", "http://llm:5001")
    
    async def _handle_question(self, user_id: str, query: str) -> str:
        """Traite question via LLM avec contexte"""
        
        # Récupérer historique conversation
        history = self.context_manager.get_history(user_id)
        
        # Construire prompt
        prompt = self.prompt_builder.build_prompt(
            user_input=query,
            history=history
        )
        
        # Appeler LLM
        logger.info(f"Envoi au LLM: {query}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_url}/generate",
                    json={
                        "prompt": prompt,
                        "max_tokens": 512,
                        "temperature": 0.7
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        raise Exception(f"LLM error: {response.status}")
                    
                    result = await response.json()
                    answer = result['text']
                    
                    # Sauvegarder dans contexte
                    self.context_manager.add_exchange(user_id, query, answer)
                    
                    logger.info(f"✅ LLM réponse: {len(answer)} chars, {result['tokens_generated']} tokens")
                    
                    return answer
                    
        except Exception as e:
            logger.error(f"❌ Erreur LLM: {e}")
            return f"Désolé, je ne peux pas répondre pour le moment: {str(e)}"
```

### 5. Conversation Multi-Tour

**Modifier**: `src/orchestrator/core/context_manager.py`

```python
from collections import deque, defaultdict
from datetime import datetime
from loguru import logger

class ContextManager:
    def __init__(self, max_history: int = 50):
        # user_id -> deque([{"role": "user/assistant", "content": "...", "timestamp": "..."}])
        self.conversations = defaultdict(lambda: deque(maxlen=max_history))
        self.user_preferences = {}
        
    def add_exchange(self, user_id: str, user_input: str, assistant_response: str):
        """Ajoute un échange complet à l'historique"""
        timestamp = datetime.now().isoformat()
        
        self.conversations[user_id].append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        self.conversations[user_id].append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": timestamp
        })
        
        logger.debug(f"Contexte mis à jour pour {user_id}: {len(self.conversations[user_id])} messages")
    
    def get_history(self, user_id: str, last_n: int = None) -> list[dict]:
        """Récupère l'historique pour construction de prompt"""
        history = list(self.conversations[user_id])
        
        if last_n:
            history = history[-last_n:]
        
        return history
    
    def clear_context(self, user_id: str):
        """Efface l'historique d'un utilisateur"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"Contexte effacé pour {user_id}")
    
    def get_context_summary(self, user_id: str) -> dict:
        """Stats sur le contexte utilisateur"""
        conv = self.conversations.get(user_id, [])
        
        return {
            "user_id": user_id,
            "total_messages": len(conv),
            "user_messages": len([m for m in conv if m['role'] == 'user']),
            "assistant_messages": len([m for m in conv if m['role'] == 'assistant']),
            "first_message": conv[0]['timestamp'] if conv else None,
            "last_message": conv[-1]['timestamp'] if conv else None
        }
```

**Test multi-tour**:
```bash
# Conversation 1
hopper "Bonjour, qui es-tu?"
# → "Je suis HOPPER, ton assistant personnel..."

# Conversation 2 (même session)
hopper "Et que peux-tu faire?"
# → "Je peux t'aider à... [se souvient du contexte précédent]"

# Conversation 3
hopper "Peux-tu créer un fichier?"
# → "Oui, je peux créer des fichiers..."
```

### 6. Knowledge Base avec FAISS

**Fichier**: `src/llm_engine/knowledge_base.py`

```python
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from loguru import logger
import pickle

class KnowledgeBase:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Knowledge Base vectorielle avec FAISS
        
        Args:
            embedding_model: Modèle sentence-transformers (384 dims, multilangue)
        """
        logger.info(f"Chargement modèle embeddings: {embedding_model}")
        self.encoder = SentenceTransformer(embedding_model)
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
        # FAISS index (Inner Product pour similarité cosine)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Stockage textes originaux
        self.texts = []
        
        logger.info("✅ Knowledge Base initialisée")
    
    def add(self, texts: List[str]):
        """Ajoute des documents à la KB"""
        if not texts:
            return
        
        logger.info(f"Ajout {len(texts)} documents à la KB")
        
        # Générer embeddings
        embeddings = self.encoder.encode(texts, convert_to_numpy=True)
        
        # Normaliser pour similarité cosine
        faiss.normalize_L2(embeddings)
        
        # Ajouter à l'index
        self.index.add(embeddings)
        
        # Stocker textes
        self.texts.extend(texts)
        
        logger.info(f"KB size: {len(self.texts)} documents")
    
    def search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """
        Cherche les k documents les plus similaires
        
        Returns:
            [(texte, score), ...]
        """
        if len(self.texts) == 0:
            return []
        
        # Encoder query
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        
        # Recherche
        k = min(k, len(self.texts))
        scores, indices = self.index.search(query_embedding, k)
        
        # Formater résultats
        results = [
            (self.texts[idx], float(score))
            for idx, score in zip(indices[0], scores[0])
        ]
        
        logger.debug(f"Recherche '{query}': {len(results)} résultats")
        
        return results
    
    def save(self, path: str):
        """Sauvegarde la KB sur disque"""
        faiss.write_index(self.index, f"{path}/faiss.index")
        
        with open(f"{path}/texts.pkl", 'wb') as f:
            pickle.dump(self.texts, f)
        
        logger.info(f"KB sauvegardée: {path}")
    
    def load(self, path: str):
        """Charge la KB depuis disque"""
        self.index = faiss.read_index(f"{path}/faiss.index")
        
        with open(f"{path}/texts.pkl", 'rb') as f:
            self.texts = pickle.load(f)
        
        logger.info(f"KB chargée: {len(self.texts)} documents")
    
    def clear(self):
        """Vide la KB"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.texts = []
        logger.info("KB vidée")
```

**Ajouter endpoints**: `src/llm_engine/main.py`

```python
from knowledge_base import KnowledgeBase

# Global KB instance
kb = KnowledgeBase()

class LearnRequest(BaseModel):
    text: str

class SearchRequest(BaseModel):
    query: str
    k: int = 3

@app.post("/learn")
async def learn(request: LearnRequest):
    """Apprend un nouveau fait"""
    kb.add([request.text])
    
    return {
        "status": "success",
        "message": f"Fait appris: {request.text}",
        "total_knowledge": len(kb.texts)
    }

@app.post("/search")
async def search_knowledge(request: SearchRequest):
    """Cherche dans la knowledge base"""
    results = kb.search(request.query, request.k)
    
    return {
        "query": request.query,
        "results": [
            {"text": text, "score": score}
            for text, score in results
        ]
    }

@app.get("/knowledge/stats")
async def knowledge_stats():
    return {
        "total_documents": len(kb.texts),
        "embedding_dimension": kb.dimension,
        "model": "all-MiniLM-L6-v2"
    }
```

### 7. RAG dans Orchestrateur

**Modifier**: `src/orchestrator/core/dispatcher.py`

```python
async def _enrich_prompt_with_knowledge(self, query: str) -> str:
    """Enrichit le prompt avec knowledge base"""
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.llm_url}/search",
                json={"query": query, "k": 3},
                timeout=5
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['results']:
                        # Construire contexte
                        context = "\n".join([
                            f"- {result['text']}"
                            for result in data['results']
                            if result['score'] > 0.5  # Seuil similarité
                        ])
                        
                        if context:
                            logger.info(f"Knowledge ajoutée: {len(context)} chars")
                            return f"Contexte pertinent:\n{context}\n\n"
                
    except Exception as e:
        logger.warning(f"Erreur enrichissement knowledge: {e}")
    
    return ""

async def _handle_question(self, user_id: str, query: str) -> str:
    """Traite question via LLM avec contexte + RAG"""
    
    # Enrichir avec knowledge base
    knowledge_context = await self._enrich_prompt_with_knowledge(query)
    
    # Récupérer historique
    history = self.context_manager.get_history(user_id)
    
    # Construire prompt
    prompt = self.prompt_builder.build_prompt(
        user_input=query,
        history=history
    )
    
    # Injecter knowledge avant la question
    if knowledge_context:
        prompt = prompt.replace(
            f"Utilisateur: {query}",
            f"{knowledge_context}Utilisateur: {query}"
        )
    
    # [... reste du code LLM ...]
```

### 8. Tests Phase 2

**Fichier**: `tests/test_phase2.py`

```python
import pytest
import requests
import time

BASE_URL = "http://localhost:8000"
LLM_URL = "http://localhost:5001"

class TestPhase2:
    """Tests d'acceptation Phase 2"""
    
    def test_llm_loaded(self):
        """Vérifier modèle LLM chargé"""
        r = requests.get(f"{LLM_URL}/health")
        assert r.status_code == 200
        data = r.json()
        assert data['model_loaded'] == True
    
    def test_basic_generation(self):
        """Test génération basique"""
        r = requests.post(
            f"{LLM_URL}/generate",
            json={
                "prompt": "Question: Qu'est-ce que Python?\nRéponse:",
                "max_tokens": 100
            }
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data['text']) > 10
        assert data['tokens_generated'] > 0
    
    def test_performance(self):
        """Vérifier performance <5s"""
        start = time.time()
        r = requests.post(
            f"{LLM_URL}/generate",
            json={"prompt": "Explique Python en 50 mots", "max_tokens": 100}
        )
        duration = time.time() - start
        
        assert r.status_code == 200
        assert duration < 5.0, f"Trop lent: {duration}s"
    
    def test_hopper_persona(self):
        """Vérifier persona Hopper"""
        r = requests.post(
            f"{BASE_URL}/command",
            json={"command": "Qui es-tu?"}
        )
        assert r.status_code == 200
        response = r.json()['response'].lower()
        assert 'hopper' in response or 'assistant' in response
    
    def test_multi_turn_conversation(self):
        """Test conversation multi-tour"""
        user_id = "test_user_123"
        
        # Tour 1
        r1 = requests.post(
            f"{BASE_URL}/command",
            json={"command": "Bonjour", "user_id": user_id}
        )
        assert r1.status_code == 200
        
        # Tour 2
        r2 = requests.post(
            f"{BASE_URL}/command",
            json={"command": "Que peux-tu faire?", "user_id": user_id}
        )
        assert r2.status_code == 200
        
        # Vérifier contexte conservé
        r3 = requests.get(f"{BASE_URL}/context/{user_id}")
        assert r3.status_code == 200
        context = r3.json()
        assert context['total_messages'] >= 4  # 2 user + 2 assistant
    
    def test_knowledge_base_learn(self):
        """Test apprentissage KB"""
        r = requests.post(
            f"{LLM_URL}/learn",
            json={"text": "Paris est la capitale de la France"}
        )
        assert r.status_code == 200
        assert r.json()['status'] == 'success'
    
    def test_knowledge_base_search(self):
        """Test recherche KB"""
        # Apprendre
        requests.post(
            f"{LLM_URL}/learn",
            json={"text": "Paris est la capitale de la France"}
        )
        
        # Chercher
        r = requests.post(
            f"{LLM_URL}/search",
            json={"query": "capitale France", "k": 3}
        )
        assert r.status_code == 200
        results = r.json()['results']
        assert len(results) > 0
        assert results[0]['score'] > 0.5
    
    def test_rag_integration(self):
        """Test RAG complet"""
        # Apprendre
        requests.post(
            f"{LLM_URL}/learn",
            json={"text": "Le mont Blanc culmine à 4808 mètres"}
        )
        
        # Question utilisant RAG
        r = requests.post(
            f"{BASE_URL}/command",
            json={"command": "Quelle est la hauteur du mont Blanc?"}
        )
        assert r.status_code == 200
        response = r.json()['response']
        assert '4808' in response or '4 808' in response
    
    def test_conversation_quality(self):
        """Test qualité conversations (10 scénarios)"""
        scenarios = [
            ("Bonjour", ["bonjour", "salut", "hello"]),
            ("Qui es-tu?", ["hopper", "assistant"]),
            ("Que peux-tu faire?", ["fichier", "command", "aide"]),
            ("Explique Python", ["langage", "programmation", "code"]),
            ("Quelle heure est-il?", ["heure", "temps", "locale"]),
            ("Crée un fichier test.txt", ["fichier", "créé", "success"]),
            ("Merci", ["de rien", "plaisir", "bienvenue"]),
            ("Au revoir", ["au revoir", "à bientôt", "bye"]),
        ]
        
        passed = 0
        for question, expected_keywords in scenarios:
            r = requests.post(
                f"{BASE_URL}/command",
                json={"command": question}
            )
            
            if r.status_code == 200:
                response = r.json()['response'].lower()
                if any(keyword in response for keyword in expected_keywords):
                    passed += 1
        
        success_rate = (passed / len(scenarios)) * 100
        assert success_rate >= 70, f"Taux réussite: {success_rate}% < 70%"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 9. Commandes Phase 2

**Makefile additions**:

```makefile
.PHONY: download-model
download-model: ## Télécharge modèle LLM
	@echo "📥 Téléchargement Mistral-7B-Instruct..."
	mkdir -p data/models
	cd data/models && curl -L -o mistral-7b-instruct-v0.2.Q4_K_M.gguf \
		"https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
	@echo "✅ Modèle téléchargé"

.PHONY: test-llm
test-llm: ## Test LLM basique
	@echo "🧪 Test génération LLM..."
	curl -X POST http://localhost:5001/generate \
		-H "Content-Type: application/json" \
		-d '{"prompt":"Question: Qui es-tu?\nRéponse:","max_tokens":100}' | jq

.PHONY: test-conversation
test-conversation: ## Test conversation complète
	@echo "💬 Test conversation..."
	$(PYTHON) hopper-cli.py -i

.PHONY: test-knowledge
test-knowledge: ## Test knowledge base
	@echo "🧠 Test KB..."
	curl -X POST http://localhost:5001/learn -H "Content-Type: application/json" \
		-d '{"text":"Paris est la capitale de la France"}'
	curl -X POST http://localhost:5001/search -H "Content-Type: application/json" \
		-d '{"query":"capitale France"}' | jq

.PHONY: test-phase2
test-phase2: ## Lance tests Phase 2
	@echo "🧪 Tests Phase 2..."
	pytest tests/test_phase2.py -v

.PHONY: benchmark
benchmark: ## Benchmark performance LLM
	@echo "⚡ Benchmark LLM..."
	@for i in 1 2 3 4 5; do \
		echo "Test $$i:"; \
		time curl -s -X POST http://localhost:5001/generate \
			-H "Content-Type: application/json" \
			-d '{"prompt":"Explique Python","max_tokens":100}' > /dev/null; \
	done
```

---

## 📊 Critères de Réussite Phase 2

### Tests à Passer

- [x] **Modèle LLM chargé**: Health check retourne `model_loaded: true`
- [x] **Génération basique**: Réponse cohérente à prompt simple
- [x] **Performance**: <5s pour générer 200 tokens
- [x] **Persona Hopper**: Se présente comme "HOPPER" quand demandé
- [x] **Multi-tour**: 3+ échanges avec mémoire contextuelle
- [x] **Knowledge Base**: Apprentissage + recherche fonctionnels
- [x] **RAG**: Enrichissement prompts avec KB
- [x] **Qualité**: 70%+ réussite sur 10 scénarios tests
- [x] **CLI complet**: Conversation interactive fluide
- [x] **Hors-ligne**: Fonctionne sans Internet

### Métriques Attendues

```
Performance:
  - Temps chargement modèle: <30s
  - Latence génération: <5s (200 tokens)
  - Throughput: 30-50 tokens/sec
  - Mémoire LLM: ~6 GB

Qualité:
  - Taux réussite conversations: ≥70%
  - Précision RAG: ≥80% (facts corrects)
  - Cohérence multi-tour: ≥85%

Robustesse:
  - Uptime LLM: 99%+
  - Erreurs gérées gracefully
  - Contexts limits respectées
```

---

## 🚀 Plan d'Exécution

### Jour 1-2: Infrastructure LLM
1. Télécharger modèle Mistral-7B
2. Modifier service LLM (llama-cpp-python)
3. Tester génération basique
4. Optimiser performance (threads, GPU)

### Jour 3-4: Prompts et Persona
5. Créer prompts.yaml
6. Implémenter PromptBuilder
7. Intégrer avec dispatcher
8. Tester persona Hopper

### Jour 5-6: Conversation
9. Étendre ContextManager
10. Implémenter multi-tour
11. Tester mémoire conversationnelle

### Jour 7-8: Knowledge Base
12. Implémenter KB avec FAISS
13. Endpoints /learn et /search
14. Intégrer RAG dans orchestrator

### Jour 9-10: Tests et Validation
15. Créer test_phase2.py
16. Exécuter 10 scénarios
17. Optimiser jusqu'à 70%+ réussite
18. Benchmark performance

### Jour 11-12: Documentation
19. Mettre à jour ARCHITECTURE.md
20. Créer PHASE2_GUIDE.md
21. Exemples conversations
22. Guide troubleshooting LLM

---

## 🎯 Next: Phase 3

Après Phase 2, nous ajouterons:
- STT réel (Whisper)
- TTS réel
- Connecteurs email/IoT fonctionnels
- Interface Web

**Phase 2 transforme Hopper d'un dispatcher simple en assistant conversationnel intelligent!**
