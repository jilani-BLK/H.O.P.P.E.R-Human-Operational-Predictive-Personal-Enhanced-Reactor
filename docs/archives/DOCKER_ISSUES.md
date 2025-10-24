# 🐳 Problèmes Docker Identifiés

**Date**: 23 octobre 2025  
**Analyse**: Configuration Docker de HOPPER

---

## ❌ PROBLÈMES CRITIQUES

### 1. **Dépendances manquantes dans orchestrator.Dockerfile**
```dockerfile
# ❌ MANQUE httpx (installé localement mais pas dans Docker)
COPY src/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Impact**: 
- Les System Tools ne fonctionneront pas dans Docker
- `import httpx` → ModuleNotFoundError
- Le dispatcher crashera au runtime

---

### 2. **Port incorrect dans orchestrator.Dockerfile**
```dockerfile
EXPOSE 5000  # ❌ Mauvais port
```

**Devrait être**:
```dockerfile
EXPOSE 5050  # ✅ Port orchestrator correct
```

**Impact**: 
- Health check échoue (vérifie 5050 mais container expose 5000)
- Communication inter-services impossible

---

### 3. **Volumes incomplets dans docker-compose.yml**
```yaml
orchestrator:
  volumes:
    - ./src/orchestrator:/app
    - ./config:/config
    - ./data:/data
    # ❌ MANQUE: tools/ filesystem/ 
```

**Impact**:
- `from tools.system_integration import system_tools` → ImportError
- `from src.filesystem import explorer` → ImportError
- Phase 5 (System Tools) complètement cassée

---

### 4. **Pas de .dockerignore**
Sans `.dockerignore`, Docker copie:
- `.venv/` (500+ MB inutiles)
- `__pycache__/` (pollue le cache)
- `.git/` (ralentit build)
- `data/` (potentiellement gros)

**Impact**: 
- Build lent (copie 1+ GB inutilement)
- Image Docker gonflée
- Cache Docker invalidé trop souvent

---

### 5. **Connecteurs manque httpx**
```dockerfile
# connectors.Dockerfile
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    # ... autres dépendances
    # ❌ MANQUE httpx
```

**Impact**:
- LocalSystemConnector peut utiliser httpx dans certains cas
- Appels externes potentiellement cassés

---

### 6. **Pas de requirements.txt pour orchestrator**
Le Dockerfile essaie de copier `src/orchestrator/requirements.txt` mais ce fichier n'existe pas !

```bash
$ ls src/orchestrator/requirements.txt
# ❌ No such file or directory
```

**Impact**: Build Docker échoue immédiatement

---

### 7. **Structure volumes incompatible avec imports**
```yaml
volumes:
  - ./src/orchestrator:/app  # ❌ Monte seulement orchestrator
```

Mais le code fait:
```python
from src.filesystem import explorer  # ❌ src/ n'existe pas dans /app
from tools.system_integration import system_tools  # ❌ tools/ n'existe pas
```

**Impact**: ImportError au démarrage

---

### 8. **Healthcheck utilise curl non installé**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5050/health"]
```

Mais orchestrator.Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y \
    gcc g++ make curl  # ✅ curl installé
```

**Status**: ✅ OK (mais vérifions que l'endpoint /health existe)

---

### 9. **Variables d'environnement manquantes**
docker-compose.yml référence des variables non définies dans `.env`:
- `LLM_MODEL_PATH`
- `KB_PERSIST_PATH`
- `KB_EMBEDDING_MODEL`
- `AUTH_CONFIDENCE_THRESHOLD`
- etc.

**Impact**: Services démarrent avec valeurs par défaut potentiellement incorrectes

---

### 10. **Network bridge par défaut**
```yaml
networks:
  hopper-network:
    driver: bridge  # ❌ Pas optimisé pour dev local
```

**Recommandation**: 
- Utiliser `host` network en dev local pour macOS
- Ou configurer DNS resolution pour service discovery

---

## 📊 Résumé Impact

| Problème | Sévérité | Impact | Bloque Docker? |
|----------|----------|--------|----------------|
| #1 httpx manquant orchestrator | 🔴 CRITIQUE | System Tools crashent | ✅ OUI |
| #2 Port incorrect | 🔴 CRITIQUE | Health check échoue | ✅ OUI |
| #3 Volumes incomplets | 🔴 CRITIQUE | ImportError | ✅ OUI |
| #4 Pas de .dockerignore | 🟠 IMPORTANT | Build lent | ❌ Non |
| #5 httpx manquant connectors | 🟡 MOYEN | Peut causer erreurs | ❌ Non |
| #6 requirements.txt manquant | 🔴 CRITIQUE | Build échoue | ✅ OUI |
| #7 Structure imports cassée | 🔴 CRITIQUE | ImportError | ✅ OUI |
| #8 Healthcheck curl | 🟢 MINEUR | OK si endpoint existe | ❌ Non |
| #9 Variables env manquantes | 🟡 MOYEN | Config par défaut | ❌ Non |
| #10 Network config | 🟢 MINEUR | Optimisation | ❌ Non |

---

## 🚨 VERDICT

**❌ Docker NE FONCTIONNERA PAS actuellement**

Raisons bloquantes:
1. Build échouera (requirements.txt manquant)
2. Si build passe, ImportError au démarrage (volumes incomplets)
3. Si imports passent, ModuleNotFoundError httpx
4. Si httpx passe, port incorrect → health check fail

**Probabilité de succès actuelle: 0%**

---

## ✅ Solutions Requises

1. Créer `src/orchestrator/requirements.txt`
2. Ajouter httpx dans requirements
3. Corriger port EXPOSE 5050
4. Ajuster volumes pour inclure tools/ et filesystem/
5. Créer .dockerignore
6. Vérifier endpoint /health existe
7. Compléter .env.example avec toutes les variables

---

**Recommandation**: Corriger ces problèmes avant tout test Docker
