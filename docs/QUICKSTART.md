# Guide de Démarrage Rapide - HOPPER

Ce guide vous permettra de lancer HOPPER en 15 minutes.

## ⚡ Installation Express

### 1. Prérequis

```bash
# Vérifier Docker
docker --version  # >= 20.10
docker-compose --version  # >= 1.29

# Vérifier Python
python3 --version  # >= 3.10
```

### 2. Cloner et Configurer

```bash
# Cloner le projet
git clone https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor.git
cd HOPPER

# Copier la configuration
cp .env.example .env

# Créer les dossiers de données
mkdir -p data/models data/logs data/vector_store
```

### 3. Mode Démarrage Rapide (Sans Modèle LLM)

Pour tester immédiatement l'architecture:

```bash
# Lancer les services en mode simulation
docker-compose up -d

# Attendre le démarrage complet (~30 secondes)
sleep 30

# Vérifier l'état
curl http://localhost:5000/health
```

**Résultat attendu**:
```json
{
  "status": "healthy",
  "services": {
    "llm": false,       # Mode simulation
    "system_executor": true,
    "stt": true,
    "tts": true,
    "auth": true,
    "connectors": true
  }
}
```

### 4. Premier Test

```bash
# Installer le CLI
chmod +x hopper-cli.py
python3 hopper-cli.py --health

# Commande de test
python3 hopper-cli.py "Bonjour HOPPER"

# Mode interactif
python3 hopper-cli.py -i
```

## 🎯 Installation Complète (Avec LLM)

### Option A: Télécharger un Modèle Pré-entraîné

```bash
# Installer huggingface-cli
pip install huggingface-hub

# Télécharger LLaMA 2 7B (GGUF quantifié)
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF \
  llama-2-7b-chat.Q4_K_M.gguf \
  --local-dir data/models

# Ou Mistral 7B (plus performant pour la taille)
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir data/models
```

### Option B: Téléchargement Manuel

1. Aller sur [HuggingFace](https://huggingface.co/models)
2. Chercher "GGUF Chat" ou "Instruct"
3. Télécharger un fichier `.gguf` quantifié (Q4_K_M ou Q5_K_M)
4. Placer dans `data/models/`

### Configurer le Modèle

```bash
# Éditer .env
nano .env

# Modifier cette ligne:
LLM_MODEL_PATH=/data/models/votre-modele.gguf

# Redémarrer le service LLM
docker-compose restart llm
```

## 🧪 Tests Fonctionnels

### Test 1: Module Système

```bash
python3 hopper-cli.py "Crée un fichier de test"

# Vérifier
ls /tmp/hopper_test.txt
```

### Test 2: LLM (si modèle chargé)

```bash
python3 hopper-cli.py "Quelle est la capitale de la France?"

# Réponse attendue:
# HOPPER: La capitale de la France est Paris...
```

### Test 3: API REST

```bash
# Tester directement l'API
curl -X POST http://localhost:5000/command \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bonjour, qui es-tu?",
    "user_id": "test_user"
  }'
```

### Test 4: Tous les Services

```bash
# Vérifier chaque service
for port in 5000 5001 5002 5003 5004 5005 5006; do
  echo "Service sur port $port:"
  curl -s http://localhost:$port/health | jq
done
```

## 🐛 Résolution de Problèmes

### Problème: Service ne démarre pas

```bash
# Voir les logs
docker-compose logs service_name

# Exemple pour l'orchestrateur
docker-compose logs orchestrator

# Logs en temps réel
docker-compose logs -f
```

### Problème: Erreur "Cannot connect"

```bash
# Vérifier que Docker tourne
docker ps

# Vérifier les ports
netstat -an | grep LISTEN | grep "500[0-6]"

# Redémarrer tous les services
docker-compose restart
```

### Problème: "Out of Memory" (LLM)

```bash
# Utiliser un modèle plus petit (7B au lieu de 13B)
# Ou augmenter Docker RAM allocation

# Sur macOS:
# Docker Desktop → Settings → Resources → Memory: 8GB+
```

### Problème: Modèle LLM lent

```bash
# Vérifier que le GPU est utilisé
docker-compose logs llm | grep "GPU"

# Augmenter GPU layers dans .env
LLM_GPU_LAYERS=35  # Au lieu de 30
```

## 🎨 Personnalisation Rapide

### Changer la Voix TTS (macOS)

```bash
# Lister les voix disponibles
say -v "?"

# Modifier le service TTS
# Dans docker/tts.Dockerfile ou en appelant l'API avec un paramètre
```

### Ajouter un Utilisateur

```bash
# Via le CLI (futur)
python3 hopper-cli.py --enroll "VotreNom"

# Ou API
curl -X POST http://localhost:5005/enroll \
  -F "user_id=VotreNom" \
  -F "audio=@sample.wav"
```

## 📊 Monitoring en Direct

```bash
# Dashboard simple
watch -n 2 'curl -s http://localhost:5000/health | jq'

# Utilisation ressources
docker stats

# Logs combinés
docker-compose logs -f --tail=50
```

## 🚀 Commandes Utiles

```bash
# Arrêter tous les services
docker-compose down

# Arrêter et nettoyer
docker-compose down -v

# Rebuild complet
docker-compose up --build -d

# Redémarrer un service spécifique
docker-compose restart orchestrator

# Accéder à un conteneur
docker-compose exec orchestrator /bin/bash

# Voir la consommation
docker-compose top
```

## 🎯 Prochaines Étapes

1. **Tester différentes commandes** via le CLI interactif
2. **Ajouter votre propre modèle LLM** optimisé
3. **Configurer les connecteurs** (email, calendrier)
4. **Implémenter l'authentification vocale**
5. **Développer des plugins personnalisés**

## 📚 Ressources

- [Documentation Complète](README.md)
- [Architecture Détaillée](ARCHITECTURE.md)
- [API Reference](API.md)
- [Guide du Développeur](DEVELOPMENT.md)

## ✅ Checklist de Démarrage

- [ ] Docker installé et fonctionnel
- [ ] Projet cloné et configuré
- [ ] Services démarrés (docker-compose up)
- [ ] Health check passé
- [ ] CLI testé en mode interactif
- [ ] Première commande système réussie
- [ ] (Optionnel) Modèle LLM téléchargé et configuré
- [ ] (Optionnel) Tests API passés

---

**Félicitations!** 🎉 HOPPER est opérationnel sur votre machine.

Pour toute question: [Issues GitHub](https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor/issues)
