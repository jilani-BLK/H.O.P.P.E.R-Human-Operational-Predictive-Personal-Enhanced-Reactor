# 🐳 Guide de Résolution - Tests d'Intégration Docker

**Problème** : Le port 5000 est occupé par AirPlay Receiver (macOS Control Center)  
**Impact** : Impossible d'exécuter les tests d'intégration Docker  
**Solutions** : 3 options disponibles

---

## 🎯 Solution 1 : Changer le Port de l'Orchestrateur (RECOMMANDÉ)

Cette solution est la plus simple et n'affecte pas les services système.

### Étape 1 : Créer le fichier .env

```bash
cd /Users/jilani/Projet/HOPPER

# Créer le fichier .env avec le nouveau port
cat > .env << 'EOF'
# Configuration HOPPER
ORCHESTRATOR_PORT=5050
ORCHESTRATOR_HOST=0.0.0.0

# URLs des services (adapter si nécessaire)
LLM_SERVICE_URL=http://llm:5001
SYSTEM_EXECUTOR_URL=http://system_executor:5002
STT_SERVICE_URL=http://stt:5003
TTS_SERVICE_URL=http://tts:5004
AUTH_SERVICE_URL=http://auth:5005
CONNECTORS_URL=http://connectors:5006
EOF
```

### Étape 2 : Modifier docker-compose.yml

```bash
# Backup de l'original
cp docker-compose.yml docker-compose.yml.backup

# Modifier le port de l'orchestrateur
sed -i.bak 's/- "5000:5000"/- "5050:5050"/' docker-compose.yml
```

Ou manuellement dans `docker-compose.yml` :

```yaml
services:
  orchestrator:
    # ... autres configurations ...
    ports:
      - "5050:5050"  # Changé de 5000 à 5050
    environment:
      - ORCHESTRATOR_PORT=5050
```

### Étape 3 : Mettre à jour les tests

```bash
# Créer un fichier de configuration pour les tests
cat > tests/test_config.py << 'EOF'
"""Configuration des tests d'intégration"""
import os

# Port de l'orchestrateur (depuis .env ou défaut)
ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", "5050"))
BASE_URL = f"http://localhost:{ORCHESTRATOR_PORT}"

# Timeouts
TIMEOUT = 30

print(f"Tests configurés pour: {BASE_URL}")
EOF
```

### Étape 4 : Modifier tests/test_integration.py

```python
# Au début du fichier, remplacer:
BASE_URL = "http://localhost:5000"

# Par:
from test_config import BASE_URL
```

### Étape 5 : Tester

```bash
# Démarrer les services avec le nouveau port
make up
# ou
docker-compose up -d

# Vérifier que l'orchestrateur répond
curl http://localhost:5050/health

# Lancer les tests d'intégration
pytest tests/test_integration.py -v
```

**Avantages** :
- ✅ Pas besoin de toucher aux services système
- ✅ Solution permanente
- ✅ Facile à maintenir

---

## 🔧 Solution 2 : Désactiver AirPlay Receiver (Temporaire)

Cette solution désactive temporairement AirPlay pour libérer le port 5000.

### Méthode A : Via les Préférences Système

```bash
# Ouvrir les préférences Partage
open "x-apple.systempreferences:com.apple.preferences.sharing"
```

Puis :
1. Décocher "Récepteur AirPlay"
2. Le port 5000 sera libéré

### Méthode B : Via la ligne de commande

```bash
# Désactiver AirPlay Receiver
sudo defaults write /Library/Preferences/com.apple.AppleFileServer guestAccess -bool NO

# Redémarrer Control Center
killall ControlCenter

# Vérifier que le port est libre
lsof -ti:5000
# (devrait être vide)
```

### Pour réactiver après les tests

```bash
# Réactiver AirPlay via Préférences Système
# ou
sudo defaults delete /Library/Preferences/com.apple.AppleFileServer guestAccess
```

**Avantages** :
- ✅ Garde le port 5000 original
- ✅ Pas besoin de modifier le code

**Inconvénients** :
- ⚠️ AirPlay désactivé pendant les tests
- ⚠️ À refaire à chaque redémarrage

---

## 🚀 Solution 3 : Tests Sans Docker (Mode Local)

Exécuter les services en local sans Docker pour les tests.

### Étape 1 : Script de démarrage local

```bash
cat > start_local_services.sh << 'EOF'
#!/bin/bash
# Démarre les services HOPPER en local pour tests

# Activer l'environnement virtuel
source .venv/bin/activate

# Fonction pour démarrer un service
start_service() {
    local name=$1
    local dir=$2
    local port=$3
    
    echo "🚀 Démarrage $name sur port $port..."
    cd $dir
    python server.py &
    local pid=$!
    echo $pid > /tmp/hopper_${name}.pid
    cd - > /dev/null
}

# Démarrer les services
start_service "orchestrator" "src/orchestrator" 5050
start_service "llm" "src/llm_engine" 5001
start_service "system_executor" "src/system_executor" 5002
start_service "stt" "src/stt" 5003
start_service "tts" "src/tts" 5004
start_service "auth" "src/auth" 5005
start_service "connectors" "src/connectors" 5006

echo ""
echo "✅ Services démarrés avec port 5050 pour l'orchestrateur"
echo "Pour arrêter : ./stop_local_services.sh"
EOF

chmod +x start_local_services.sh
```

### Étape 2 : Script d'arrêt

```bash
cat > stop_local_services.sh << 'EOF'
#!/bin/bash
# Arrête les services HOPPER locaux

services=("orchestrator" "llm" "system_executor" "stt" "tts" "auth" "connectors")

for service in "${services[@]}"; do
    pidfile="/tmp/hopper_${service}.pid"
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        echo "🛑 Arrêt $service (PID: $pid)"
        kill $pid 2>/dev/null
        rm "$pidfile"
    fi
done

echo "✅ Tous les services arrêtés"
EOF

chmod +x stop_local_services.sh
```

### Étape 3 : Tester

```bash
# Démarrer les services locaux
./start_local_services.sh

# Attendre 5 secondes
sleep 5

# Tester
pytest tests/test_integration.py -v

# Arrêter
./stop_local_services.sh
```

**Avantages** :
- ✅ Pas besoin de Docker en développement
- ✅ Plus rapide à démarrer/arrêter
- ✅ Facilite le debug

**Inconvénients** :
- ⚠️ Ne teste pas la vraie configuration Docker
- ⚠️ Nécessite Python installé localement

---

## 📊 Comparaison des Solutions

| Solution | Difficulté | Temps | Production-Ready | AirPlay |
|----------|-----------|-------|------------------|---------|
| **1. Changer port** | Facile | 10 min | ✅ Oui | ✅ Fonctionne |
| **2. Désactiver AirPlay** | Facile | 2 min | ⚠️ Temporaire | ❌ Désactivé |
| **3. Mode local** | Moyen | 15 min | ⚠️ Dev only | ✅ Fonctionne |

---

## 🎯 Recommandation Finale

**Utiliser la Solution 1 (Changer le port à 5050)** car :

1. ✅ **Permanent** : Fonctionne toujours
2. ✅ **Production-ready** : Configuration propre
3. ✅ **Pas d'impact** : AirPlay reste fonctionnel
4. ✅ **Standard** : Port 5050 est libre et conventionnel

### Script d'Application Rapide

```bash
#!/bin/bash
# apply_port_change.sh - Applique tous les changements pour le port 5050

cd /Users/jilani/Projet/HOPPER

echo "🔧 Application du changement de port 5000 → 5050"

# 1. Créer .env
echo "ORCHESTRATOR_PORT=5050" > .env
echo "✅ Fichier .env créé"

# 2. Modifier docker-compose.yml
sed -i.backup 's/"5000:5000"/"5050:5050"/' docker-compose.yml
echo "✅ docker-compose.yml modifié"

# 3. Modifier tests
sed -i.backup 's|localhost:5000|localhost:5050|g' tests/test_integration.py
echo "✅ tests/test_integration.py modifié"

# 4. Vérifier que le port 5050 est libre
if lsof -ti:5050 > /dev/null 2>&1; then
    echo "⚠️  Port 5050 occupé!"
    lsof -ti:5050 | xargs ps -p
else
    echo "✅ Port 5050 disponible"
fi

echo ""
echo "✨ Changement appliqué avec succès!"
echo ""
echo "Prochaines étapes:"
echo "  1. make up              # Démarrer avec Docker"
echo "  2. curl http://localhost:5050/health"
echo "  3. pytest tests/test_integration.py -v"
```

---

## 🧪 Vérification Post-Installation

Après avoir appliqué la Solution 1, vérifier :

```bash
# 1. Port 5050 libre
lsof -ti:5050
# (vide = OK)

# 2. .env existe
cat .env | grep ORCHESTRATOR_PORT
# ORCHESTRATOR_PORT=5050

# 3. docker-compose.yml modifié
grep "5050:5050" docker-compose.yml
# - "5050:5050"

# 4. Tests modifiés
grep "localhost:5050" tests/test_integration.py
# BASE_URL = "http://localhost:5050"

# 5. Démarrer et tester
docker-compose up -d orchestrator
sleep 5
curl http://localhost:5050/health
# {"status": "healthy", ...}

# 6. Tests d'intégration
pytest tests/test_integration.py::TestHealthChecks::test_orchestrator_health -v
# PASSED ✅
```

---

## 📚 Documentation à Mettre à Jour

Après le changement, mettre à jour :

1. **README.md** : Mentionner le port 5050
2. **docs/QUICKSTART.md** : Exemples avec port 5050
3. **hopper-cli.py** : Argument `--port` par défaut à 5050
4. **Postman/Thunder Client** : Collections d'API

---

## 🐛 Troubleshooting

### Erreur : Port 5050 aussi occupé ?

```bash
# Trouver un autre port libre
for port in 5050 5100 8000 8080 9000; do
    if ! lsof -ti:$port > /dev/null 2>&1; then
        echo "Port $port disponible"
        break
    fi
done
```

### Erreur : Docker ne démarre pas

```bash
# Vérifier les logs
docker-compose logs orchestrator

# Vérifier la variable d'environnement
docker-compose exec orchestrator env | grep PORT
```

### Erreur : Tests échouent toujours

```bash
# Vérifier que l'orchestrateur répond
curl -v http://localhost:5050/health

# Vérifier les logs des tests
pytest tests/test_integration.py -v -s --log-cli-level=DEBUG
```

---

**Dernière mise à jour** : 22 octobre 2025  
**Recommandation** : Solution 1 (Port 5050) ✅
