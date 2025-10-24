# 🚀 HOPPER - Guide d'Optimisation

> Guide complet pour optimiser les performances de HOPPER : CPU, mémoire, latence, Docker

---

## 📊 Table des Matières

1. [Profiling](#profiling)
2. [Optimisation Docker](#optimisation-docker)
3. [Optimisation LLM](#optimisation-llm)
4. [Optimisation STT/TTS](#optimisation-stttts)
5. [Optimisation Neo4j](#optimisation-neo4j)
6. [Optimisation Réseau](#optimisation-réseau)
7. [Monitoring Continu](#monitoring-continu)

---

## 🔍 Profiling

### Lancer le Profiling Complet

```bash
./scripts/profile.sh
```

Ce script analyse:
- **Docker**: CPU, RAM, I/O de chaque conteneur
- **Endpoints**: Latence moyenne (5 requêtes)
- **Mémoire système**: Utilisation globale
- **Modèles**: Taille des modèles LLM/STT
- **Recommandations**: Basées sur les métriques

### Résultats

Le rapport est sauvegardé dans `profiling_results/profile_YYYYMMDD_HHMMSS.txt`

### Outils Avancés

#### py-spy (Profiling CPU Python)

```bash
# Installation
pip install py-spy

# Profiler un processus
sudo py-spy record --duration 60 --output flamegraph.svg --pid <PID>

# Profiler toute l'exécution
sudo py-spy record -o profile.svg -- python src/orchestrator/main.py
```

#### memory_profiler (Profiling Mémoire)

```bash
# Installation
pip install memory-profiler

# Décorer les fonctions critiques
@profile
def fonction_critique():
    ...

# Profiler
python -m memory_profiler script.py
```

#### cProfile (Profiling Standard Python)

```bash
python -m cProfile -o output.pstats src/orchestrator/main.py
python -m pstats output.pstats
```

---

## 🐳 Optimisation Docker

### 1. Réduire l'Utilisation Mémoire

#### Combiner Services Légers

**Avant**: 6 conteneurs séparés  
**Après**: 4 conteneurs (combiner FileSystem + LocalSystem + Spotify)

```yaml
# docker-compose.yml
services:
  hopper-connectors:
    build: ./src/connectors
    environment:
      - SERVICES=filesystem,localsystem,spotify
    ports:
      - "5006:5006"  # Multiplexer sur un seul port
```

**Gain**: -500MB RAM, -2 conteneurs

#### Limiter la Mémoire

```yaml
services:
  hopper-stt:
    deploy:
      resources:
        limits:
          memory: 2G     # Limite stricte
        reservations:
          memory: 1G     # Garantie minimale
```

### 2. Optimiser les Images

#### Utiliser Alpine Linux

**Avant**: `python:3.10` (920MB)  
**Après**: `python:3.10-alpine` (50MB)

```dockerfile
# Avant
FROM python:3.10

# Après
FROM python:3.10-alpine
RUN apk add --no-cache gcc musl-dev libffi-dev
```

**Gain**: -870MB par image

#### Multi-stage Builds

```dockerfile
# Stage 1: Builder
FROM python:3.10 as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim
COPY --from=builder /root/.local /root/.local
COPY src/ /app/src/
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "/app/src/main.py"]
```

**Gain**: -60% taille image

### 3. Cache Layers Intelligent

```dockerfile
# ❌ Mauvais: Invalidation cache fréquente
COPY . /app
RUN pip install -r requirements.txt

# ✅ Bon: Dépendances stable
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
COPY src/ /app/src/
```

### 4. Docker Compose Optimisé

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.13
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
    environment:
      NEO4J_dbms_memory_heap_max__size: 1G
      NEO4J_dbms_memory_pagecache_size: 512M
    volumes:
      - ./data/neo4j:/data
    restart: unless-stopped
    
  hopper-llm:
    build:
      context: ./src/services/llm
      dockerfile: Dockerfile
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4'
    environment:
      MODEL_QUANTIZATION: '4bit'  # Quantization 4-bit
      TORCH_THREADS: '4'
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    restart: unless-stopped
```

---

## 🤖 Optimisation LLM

### 1. Quantization

**Réduction de 75% de la mémoire sans perte significative de qualité**

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

# Configuration 4-bit
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# Charger le modèle quantizé
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B",
    quantization_config=bnb_config,
    device_map="auto"
)
```

**Comparaison**:
- **Float32**: ~12GB RAM
- **Float16**: ~6GB RAM
- **8-bit**: ~3GB RAM
- **4-bit**: ~1.5GB RAM ✅

### 2. Pré-chargement au Démarrage

```python
import asyncio
from functools import lru_cache

@lru_cache(maxsize=1)
def load_model():
    """Charge le modèle une seule fois au démarrage"""
    model = AutoModelForCausalLM.from_pretrained(...)
    tokenizer = AutoTokenizer.from_pretrained(...)
    return model, tokenizer

# Au démarrage du service
@app.on_event("startup")
async def startup_event():
    log.info("Pré-chargement du modèle LLM...")
    load_model()  # Bloque 30s au démarrage, mais 0s aux requêtes
    log.info("Modèle chargé en mémoire")
```

**Gain**: Latence première requête 30s → 0.5s

### 3. Batch Processing

```python
async def process_batch(prompts: List[str]) -> List[str]:
    """Traiter plusieurs prompts en un seul passage"""
    inputs = tokenizer(prompts, return_tensors="pt", padding=True)
    outputs = model.generate(**inputs, max_new_tokens=50)
    return tokenizer.batch_decode(outputs, skip_special_tokens=True)
```

**Gain**: 5 requêtes séquentielles 10s → batch 3s

### 4. Cache des Réponses Fréquentes

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_response(prompt_hash: str) -> str:
    """Cache des réponses pour prompts identiques"""
    return generate_response(prompt)

def query_llm(prompt: str) -> str:
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    return get_cached_response(prompt_hash)
```

**Gain**: Réponses instantanées pour prompts répétés

### 5. GPU vs CPU

```python
import torch

# Détecter GPU disponible
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = model.to(device)

# Si GPU disponible (Metal sur macOS M1/M2)
if torch.backends.mps.is_available():
    device = torch.device("mps")
    model = model.to(device)
```

**Gain**: GPU = 10-30x plus rapide que CPU

### 6. Modèles Hybrides

```python
# Modèle rapide pour requêtes simples
small_model = "TinyLlama-1.1B"  # 1.1GB, 50ms latence

# Modèle puissant pour requêtes complexes
large_model = "Llama-3.2-3B"    # 6GB, 500ms latence

def select_model(prompt: str) -> str:
    if is_simple_query(prompt):  # "quelle heure?", "bonjour"
        return small_model
    else:
        return large_model
```

---

## 🎤 Optimisation STT/TTS

### STT (Whisper)

#### 1. Modèle Optimal

**Comparaison**:
| Modèle | Taille | RAM | Latence | Précision |
|--------|--------|-----|---------|-----------|
| tiny   | 39MB   | 1GB | 50ms    | 70%       |
| base   | 74MB   | 1GB | 100ms   | 80%       |
| small  | 244MB  | 2GB | 300ms   | 90%       |
| medium | 769MB  | 5GB | 1s      | 95%       | ✅
| large  | 1.5GB  | 10GB| 3s      | 98%       |

**Recommandation**: `base` ou `small` pour usage quotidien

```python
import whisper

# Charger un modèle plus léger
model = whisper.load_model("base")  # au lieu de "medium"
```

#### 2. Segments Overlappants

```python
def transcribe_with_overlap(audio_file: str) -> str:
    """Améliore la précision avec overlapping"""
    result = model.transcribe(
        audio_file,
        language="fr",
        task="transcribe",
        initial_prompt="Transcription en français.",
        condition_on_previous_text=True,  # Contexte
        compression_ratio_threshold=2.4,
        logprob_threshold=-1.0
    )
    return result["text"]
```

**Gain**: +5% précision, +200ms latence

#### 3. GPU Acceleration

```python
# Utiliser GPU si disponible
model = whisper.load_model("base", device="cuda")  # ou "mps" pour M1/M2
```

**Gain**: 30x plus rapide (3s → 100ms)

### TTS

#### 1. Cache Audio

```python
import hashlib
from pathlib import Path

CACHE_DIR = Path("/tmp/hopper_tts_cache")
CACHE_DIR.mkdir(exist_ok=True)

def synthesize_cached(text: str) -> bytes:
    """Cache des audio générés"""
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{text_hash}.mp3"
    
    if cache_file.exists():
        return cache_file.read_bytes()
    
    audio = synthesize(text)
    cache_file.write_bytes(audio)
    return audio
```

**Gain**: Phrases répétées instantanées

#### 2. Streaming Audio

```python
async def stream_audio(text: str):
    """Streamer l'audio au fur et à mesure"""
    for chunk in split_text(text, max_length=100):
        audio_chunk = synthesize(chunk)
        yield audio_chunk
        await asyncio.sleep(0)
```

**Gain**: Début lecture immédiat (perception de rapidité)

---

## 📊 Optimisation Neo4j

### 1. Indexation

```cypher
// Indexer les propriétés fréquemment requêtées
CREATE INDEX conversation_timestamp IF NOT EXISTS
FOR (c:Conversation) ON (c.timestamp);

CREATE INDEX user_name IF NOT EXISTS
FOR (u:User) ON (u.name);

CREATE INDEX entity_type IF NOT EXISTS
FOR (e:Entity) ON (e.type);
```

**Gain**: Requêtes 100x plus rapides

### 2. Configuration Mémoire

```properties
# neo4j.conf
dbms.memory.heap.initial_size=1G
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=1G
```

**Recommandation**:
- Heap: 25% RAM disponible
- Pagecache: 50% RAM disponible

### 3. Nettoyage Automatique

```cypher
// Supprimer conversations >30 jours
MATCH (c:Conversation)
WHERE c.timestamp < datetime() - duration('P30D')
DETACH DELETE c;

// Archiver au lieu de supprimer
MATCH (c:Conversation)
WHERE c.timestamp < datetime() - duration('P30D')
SET c:Archived
REMOVE c:Conversation;
```

### 4. Connection Pooling

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password"),
    max_connection_pool_size=50,  # Pool de 50 connexions
    connection_acquisition_timeout=30
)
```

---

## 🌐 Optimisation Réseau

### 1. Compression HTTP

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress >1KB
```

**Gain**: -70% bande passante

### 2. Cache Redis (optionnel)

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379)

async def query_llm_cached(prompt: str) -> str:
    # Vérifier cache
    cached = redis_client.get(f"llm:{prompt}")
    if cached:
        return json.loads(cached)
    
    # Générer réponse
    response = await query_llm(prompt)
    
    # Stocker en cache (expire 1h)
    redis_client.setex(f"llm:{prompt}", 3600, json.dumps(response))
    
    return response
```

### 3. HTTP/2

```python
# Utiliser Uvicorn avec HTTP/2
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    http="h2"  # HTTP/2
)
```

---

## 📈 Monitoring Continu

### 1. Script Monitor

```bash
# Mode temps réel
./scripts/monitor.sh --live

# Mode snapshot
./scripts/monitor.sh --snapshot

# Mode alertes
./scripts/monitor.sh --alert
```

### 2. Prometheus + Grafana (optionnel)

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 3. Alertes Automatiques

```bash
# Alerter si CPU >80% pendant 5min
while true; do
    CPU=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    if (( $(echo "$CPU > 80" | bc -l) )); then
        echo "ALERTE: CPU élevé (${CPU}%)" | mail -s "HOPPER Alert" admin@example.com
    fi
    sleep 300
done
```

---

## 📋 Checklist d'Optimisation

### Priorité 1 (Rapide, Impact Élevé)

- [ ] Activer quantization 4-bit sur LLM
- [ ] Utiliser modèle Whisper `base` au lieu de `medium`
- [ ] Indexer Neo4j (conversations, entités)
- [ ] Activer compression HTTP (GZip)
- [ ] Limiter mémoire Docker (deploy.resources.limits)

### Priorité 2 (Moyen Terme)

- [ ] Combiner services légers en un conteneur
- [ ] Pré-charger LLM au démarrage
- [ ] Cache Redis pour réponses fréquentes
- [ ] Images Alpine Linux
- [ ] Connection pooling Neo4j

### Priorité 3 (Long Terme)

- [ ] GPU acceleration (Whisper + LLM)
- [ ] Prometheus + Grafana monitoring
- [ ] Multi-stage Docker builds
- [ ] Modèles hybrides (petit + grand)
- [ ] CDN pour assets statiques

---

## 🎯 Résultats Attendus

### Avant Optimisation

| Métrique | Valeur |
|----------|--------|
| RAM totale | ~12GB |
| Latence LLM | 2-5s |
| Latence STT | 1-3s |
| Démarrage | 5min |
| CPU idle | 15% |

### Après Optimisation

| Métrique | Valeur | Gain |
|----------|--------|------|
| RAM totale | ~6GB | -50% ✅ |
| Latence LLM | 0.5-1s | -75% ✅ |
| Latence STT | 200-500ms | -80% ✅ |
| Démarrage | 2min | -60% ✅ |
| CPU idle | 3% | -80% ✅ |

---

## 🔗 Ressources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [PyTorch Performance Tuning](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)
- [Neo4j Performance](https://neo4j.com/developer/guide-performance-tuning/)
- [Whisper Optimization](https://github.com/openai/whisper/discussions)
- [Transformers Quantization](https://huggingface.co/docs/transformers/main_classes/quantization)

---

**Auteur**: HOPPER Team  
**Date**: Octobre 2025  
**Version**: 1.0
