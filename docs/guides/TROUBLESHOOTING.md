# HOPPER - Guide de Dépannage Phase 1

## Problèmes Rencontrés et Solutions

### 1. Erreur: `docker-compose: No such file or directory`

**Cause**: Version Docker récente utilise `docker compose` au lieu de `docker-compose`

**Solution**: ✅ CORRIGÉ
- Makefile mis à jour avec `docker compose`
- docker-compose.yml: version obsolète retirée

### 2. Erreur: `ModuleNotFoundError: No module named 'requests'`

**Cause**: Dépendances Python CLI non installées

**Solution**: ✅ CORRIGÉ
- Environnement virtuel Python créé: `.venv`
- Dépendances installées via `install_python_packages`

### 3. Erreur Build Docker: `webrtcvad`, `pyaudio` nécessitent GCC

**Cause**: Services auth/stt/tts tentent d'installer packages nécessitant compilation C

**Solution**: ✅ CORRIGÉ Phase 1
- Dockerfiles simplifiés pour Phase 1 (mode simulation)
- Packages lourds (Whisper, TTS, speechbrain) reportés à Phase 2
- auth.Dockerfile: Seulement fastapi, uvicorn, pydantic, numpy
- stt.Dockerfile: Seulement fastapi, uvicorn, pydantic, numpy
- tts.Dockerfile: Seulement fastapi, uvicorn, pydantic, numpy

### 4. Build Docker très lent (llama-cpp-python)

**Cause**: llama-cpp-python compile du C++ optimisé - prend 5-10 minutes

**Solutions alternatives**:

#### Option A: Build complet Docker (recommandé mais lent)
```bash
docker compose build  # Attendre 10-15 minutes
docker compose up -d
```

#### Option B: Services essentiels seulement (rapide)
```bash
./start-phase1.sh  # Lance orchestrator + system_executor + connectors
```

#### Option C: Mode standalone sans Docker (test rapide)
```bash
./test-standalone.sh  # Lance l'orchestrateur seul en Python
```

## État Actuel Phase 1

### ✅ Corrigé
- Makefile: `docker-compose` → `docker compose`
- docker-compose.yml: Version obsolète retirée
- .env créé depuis .env.example
- Dépendances Python CLI installées
- Dockerfiles simplifiés (pas de compilation lourde)

### ⏳ En Cours
- Build Docker images (peut prendre 10-15 min)
- Installation dépendances orchestrateur standalone

### 📝 À Tester
```bash
# Option 1: Test orchestrateur standalone (sans Docker)
./test-standalone.sh

# Option 2: CLI direct (après démarrage orchestrator)
/Users/jilani/Projet/HOPPER/.venv/bin/python hopper-cli.py --health

# Option 3: Docker complet (après build terminé)
docker compose up -d
docker compose ps
```

## Commandes Utiles

### Vérifier Docker
```bash
docker --version          # Docker version 28.5.1+
docker compose version    # v2.40.0+
docker ps                 # Conteneurs actifs
```

### Vérifier Python
```bash
which python3                                           # /usr/bin/python3 ou /opt/homebrew/bin/python3
/Users/jilani/Projet/HOPPER/.venv/bin/python --version  # Python 3.13.5
```

### Logs Docker
```bash
docker compose logs -f orchestrator
docker compose logs -f system_executor
docker compose logs --tail=50
```

### Arrêter Services
```bash
docker compose down       # Arrêter tous services
docker compose stop       # Pause services
pkill -f "python main.py" # Arrêter orchestrator standalone
```

## Prochaines Étapes

### Une fois services démarrés:
1. **Health check**:
   ```bash
   curl http://localhost:5000/health  # Orchestrator
   curl http://localhost:5002/health  # System Executor
   ```

2. **Test CLI**:
   ```bash
   /Users/jilani/Projet/HOPPER/.venv/bin/python hopper-cli.py --health
   /Users/jilani/Projet/HOPPER/.venv/bin/python hopper-cli.py -i
   ```

3. **Test commande système**:
   ```
   > Crée un fichier test.txt
   > Liste les fichiers du répertoire
   ```

## Phase 2 - Installation Complète

Pour activer services réels (LLM, STT, TTS) voir `PHASE2_PLAN.md`:

1. Télécharger modèle LLM (~4 Go)
2. Installer Whisper (STT)
3. Installer TTS
4. Rebuild Docker avec dépendances complètes

## Support

Si erreur persiste:
1. Vérifier logs: `docker compose logs`
2. Vérifier état: `docker compose ps`
3. Rebuild: `docker compose build --no-cache`
4. Consulter: `PHASE1_STATUS.md`
