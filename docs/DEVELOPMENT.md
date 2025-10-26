# Guide du Développeur - HOPPER

Ce guide s'adresse aux développeurs souhaitant contribuer à HOPPER ou créer leurs propres modules.

## 🛠️ Configuration de l'Environnement de Développement

### Prérequis

```bash
# Installer les outils
brew install docker docker-compose python@3.11 gcc make

# Vérifier les versions
docker --version        # >= 20.10
python3 --version       # >= 3.10
gcc --version          # >= 12.0
```

### Configuration Initiale

```bash
# Cloner et setup
git clone https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor.git
cd HOPPER

# Créer un environnement virtuel Python (optionnel)
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances de développement
pip install -r src/orchestrator/requirements.txt
pip install pytest pytest-asyncio black flake8
```

## 📁 Structure du Code

```
src/
├── orchestrator/          # Orchestrateur Python
│   ├── main.py           # Point d'entrée FastAPI
│   ├── config.py         # Configuration
│   ├── core/
│   │   ├── dispatcher.py      # Routage des intentions
│   │   ├── context_manager.py # Gestion du contexte
│   │   └── service_registry.py # Registre des services
│   └── api/
│       └── routes.py     # Routes API additionnelles
│
├── llm_engine/           # Moteur LLM
│   └── server.py         # Serveur d'inférence
│
├── system_executor/      # Module C
│   ├── Makefile
│   └── src/
│       └── main.c        # Serveur HTTP + actions
│
├── stt/                  # Speech-to-Text
│   └── server.py
│
├── tts/                  # Text-to-Speech
│   └── server.py
│
├── auth/                 # Authentification
│   └── server.py
│
└── connectors/           # Connecteurs externes
    └── server.py
```

## 🔧 Développement d'un Nouveau Module

### 1. Créer un Service Python

```python
# src/mon_service/server.py
from fastapi import FastAPI
import os
from loguru import logger

app = FastAPI(title="Mon Service")

@app.on_event("startup")
async def startup():
    logger.info("🚀 Démarrage de Mon Service")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/action")
async def do_something(data: dict):
    logger.info(f"Action reçue: {data}")
    # Votre logique ici
    return {"success": True, "result": "..."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MON_SERVICE_PORT", 5007))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
```

### 2. Créer le Dockerfile

```dockerfile
# docker/mon_service.Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn loguru

COPY src/mon_service/ .

EXPOSE 5007

CMD ["python", "server.py"]
```

### 3. Ajouter au docker-compose.yml

```yaml
  mon_service:
    build:
      context: .
      dockerfile: docker/mon_service.Dockerfile
    container_name: hopper-mon-service
    ports:
      - "5007:5007"
    volumes:
      - ./src/mon_service:/app
    env_file:
      - .env
    networks:
      - hopper-network
    restart: unless-stopped
```

### 4. Enregistrer dans l'Orchestrateur

```python
# src/orchestrator/config.py
class Settings(BaseSettings):
    # ...
    MON_SERVICE_URL: str = "http://mon_service:5007"

# src/orchestrator/core/service_registry.py
async def register_services(self) -> None:
    self.services = {
        # ... services existants
        "mon_service": settings.MON_SERVICE_URL
    }
```

### 5. Utiliser dans le Dispatcher

```python
# src/orchestrator/core/dispatcher.py
async def _handle_mon_action(self, text, user_id, context):
    result = await self.service_registry.call_service(
        "mon_service",
        "/action",
        method="POST",
        data={"text": text, "user_id": user_id}
    )
    return {
        "message": result.get("result"),
        "data": result,
        "actions": ["mon_action"]
    }
```

## 🧪 Tests

### Tests Unitaires

```python
# tests/test_mon_service.py
import pytest
from src.mon_service.server import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_action():
    response = client.post("/action", json={"test": "data"})
    assert response.status_code == 200
    assert "success" in response.json()
```

### Lancer les Tests

```bash
# Tous les tests
pytest tests/ -v

# Un fichier spécifique
pytest tests/test_mon_service.py -v

# Avec couverture
pytest --cov=src tests/
```

### Tests d'Intégration

```bash
# Démarrer les services
docker-compose up -d

# Attendre qu'ils soient prêts
sleep 30

# Lancer les tests d'intégration
pytest tests/test_integration.py -v

# Arrêter
docker-compose down
```

## 🐛 Debugging

### Logs en Temps Réel

```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f orchestrator

# Filtrer
docker-compose logs -f | grep ERROR
```

### Accéder à un Conteneur

```bash
# Shell interactif
docker-compose exec orchestrator /bin/bash

# Exécuter une commande
docker-compose exec orchestrator python -c "import sys; print(sys.version)"
```

### Debugger Python avec pdb

```python
# Dans votre code Python
import pdb; pdb.set_trace()

# Ou avec breakpoint() (Python 3.7+)
breakpoint()
```

### Profiling Performance

```python
# Avec cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code à profiler
result = await process_command(text)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## 📊 Monitoring

### Métriques Basiques

```python
# Dans votre service
import time
from collections import defaultdict

metrics = defaultdict(list)

@app.middleware("http")
async def add_metrics(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    metrics[request.url.path].append(duration)
    return response

@app.get("/metrics")
async def get_metrics():
    return {
        path: {
            "count": len(durations),
            "avg": sum(durations) / len(durations),
            "max": max(durations)
        }
        for path, durations in metrics.items()
    }
```

## 🎨 Standards de Code

### Python (PEP 8 + Black)

```bash
# Formatter le code
black src/

# Vérifier le style
flake8 src/ --max-line-length=100

# Type checking
mypy src/orchestrator/
```

### C (LLVM/Clang)

```bash
# Formatter
clang-format -i src/system_executor/src/*.c

# Analyser
clang-tidy src/system_executor/src/*.c
```

### Conventions

**Python**:
- snake_case pour fonctions et variables
- PascalCase pour classes
- UPPER_CASE pour constantes
- Type hints partout
- Docstrings (Google style)

**C**:
- snake_case pour tout
- Préfixes pour fonctions publiques
- Commentaires Doxygen

## 🔄 Workflow Git

```bash
# Créer une branche
git checkout -b feature/mon-feature

# Commiter régulièrement
git add .
git commit -m "feat: ajout de mon_service"

# Pousser
git push origin feature/mon-feature

# Pull request sur GitHub
```

### Conventions de Commit

```
feat: nouvelle fonctionnalité
fix: correction de bug
docs: documentation
style: formatage
refactor: refactoring
test: ajout de tests
chore: maintenance
```

## 📦 Build et Déploiement

### Build Local

```bash
# Rebuild tout
docker-compose build

# Rebuild un service
docker-compose build orchestrator

# Sans cache
docker-compose build --no-cache
```

### Optimisation des Images

```dockerfile
# Multi-stage build exemple
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim

COPY --from=builder /root/.local /root/.local
COPY src/ /app/

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "server.py"]
```

## 🔐 Sécurité

### Secrets Management

```bash
# Jamais commiter .env
echo ".env" >> .gitignore

# Utiliser des variables d'environnement
export API_KEY="secret"
docker-compose up
```

### Scanning de Vulnérabilités

```bash
# Scanner les dépendances Python
pip install safety
safety check

# Scanner les images Docker
docker scan hopper-orchestrator
```

## 📚 Ressources

### Documentation des Bibliothèques

- [FastAPI](https://fastapi.tiangolo.com/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Whisper](https://github.com/openai/whisper)
- [Docker Compose](https://docs.docker.com/compose/)

### Outils Recommandés

- **IDE**: VS Code, PyCharm
- **API Testing**: Postman, httpie
- **Monitoring**: Prometheus, Grafana (futur)
- **Profiling**: py-spy, cProfile

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Implémenter + tests
4. Documenter
5. Pull request avec description claire

## 📝 Checklist Pull Request

- [ ] Code formatté (black, clang-format)
- [ ] Tests passants
- [ ] Documentation mise à jour
- [ ] Pas de secrets committés
- [ ] Build Docker réussi
- [ ] Health check implémenté

---

**Questions?** Ouvrir une [issue GitHub](https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor/issues)
