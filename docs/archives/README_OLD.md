# HOPPER - Human Operational Predictive Personal Enhanced Reactor

![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS%20|%20Linux-lightgrey)

Assistant personnel intelligent autonome fonctionnant entièrement en local, conçu pour apprendre de lui-même et traiter des tâches en temps réel.

## 🎯 Objectifs

HOPPER est envisagé comme un assistant personnel intelligent qui:

- **Apprend de lui-même** via apprentissage par renforcement et fine-tuning local
- **Fonctionne 100% en local** sur votre machine (aucune dépendance cloud)
- **Prend des décisions autonomes** et propose des suggestions proactives
- **S'intègre avec de multiples systèmes** (OS, web, IoT, autres machines)
- **Optimise les performances** avec C/C++ pour le calcul et Python pour l'IA
- **Garantit la sécurité** avec authentification vocale/faciale

## 🏗️ Architecture

### Architecture Microservices

```
┌─────────────────────────────────────────────────────────┐
│                   UTILISATEUR                            │
│              (CLI / Voix / Interface)                    │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              ORCHESTRATEUR CENTRAL (Python)              │
│  • Analyse d'intention                                   │
│  • Gestion du contexte conversationnel                   │
│  • Routage des commandes                                 │
│  • Règles heuristiques et décisions                      │
└─────┬────┬────┬────┬────┬────┬───────────────────────┘
      │    │    │    │    │    │
      ▼    ▼    ▼    ▼    ▼    ▼
   ┌───┐┌───┐┌───┐┌───┐┌───┐┌────┐
   │LLM││SYS││STT││TTS││AUT││CONN│
   │   ││EXE││   ││   ││H  ││    │
   └───┘└───┘└───┘└───┘└───┘└────┘
   C++   C   Py   Py   Py   Py
```

### Modules Principaux

1. **Orchestrateur Central** (Python)
   - Cerveau de HOPPER qui coordonne tous les services
   - Analyse d'intention et routage des commandes
   - Gestion du contexte conversationnel
   - Logique de décision et règles heuristiques

2. **Moteur LLM** (C++ avec llama.cpp)
   - Modèle de langage local (LLaMA 2 / Mistral)
   - Inférence optimisée sur GPU Apple Silicon
   - Contexte étendu via Retrieval Augmented Generation
   - Fine-tuning local continu

3. **Module d'Exécution Système** (C)
   - Actions système directes (fichiers, processus)
   - Performances optimales en C pur
   - Serveur HTTP léger avec libmicrohttpd

4. **Module STT** (Python + Whisper)
   - Reconnaissance vocale locale
   - Support multilingue (français prioritaire)
   - Basé sur OpenAI Whisper

5. **Module TTS** (Python)
   - Synthèse vocale naturelle
   - Voix française de qualité
   - Latence minimale

6. **Module d'Authentification** (Python)
   - Reconnaissance vocale du locuteur
   - Reconnaissance faciale (optionnel)
   - Gestion multi-utilisateurs

7. **Connecteurs** (Python)
   - Email (IMAP/SMTP)
   - Calendrier (Google Calendar, iCloud)
   - IoT (MQTT, Zigbee)
   - Services web et API externes

## 🚀 Installation

### Prérequis

- **Système d'exploitation**: macOS (M1/M2/M3), Linux
- **RAM**: Minimum 16 Go, recommandé 32 Go+
- **Espace disque**: 50 Go (pour les modèles)
- **Docker**: Version 20.10+
- **Python**: 3.10 ou supérieur

### Installation Rapide

```bash
# 1. Cloner le repository
git clone https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor.git
cd HOPPER

# 2. Copier le fichier de configuration
cp .env.example .env

# 3. Télécharger un modèle LLM (exemple avec LLaMA 2 7B)
mkdir -p data/models
# Télécharger depuis HuggingFace ou utiliser un modèle existant
# Exemple: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF

# 4. Lancer les services
docker-compose up -d

# 5. Vérifier l'état
docker-compose ps
```

### Vérification de l'Installation

```bash
# Vérifier la santé des services
curl http://localhost:5000/health

# Ou utiliser le CLI
python hopper-cli.py --health
```

## 💻 Utilisation

### Mode CLI (Ligne de Commande)

```bash
# Mode interactif
python hopper-cli.py -i

# Commande directe
python hopper-cli.py "Quelle heure est-il?"

# Créer un alias pour faciliter l'utilisation
alias hopper="python /chemin/vers/hopper-cli.py"
hopper "Ouvre l'application Notes"
```

### Exemples de Commandes

```bash
# Système
hopper "Crée un fichier test.txt"
hopper "Liste les fichiers du répertoire Documents"
hopper "Ouvre l'application Calculatrice"

# Questions
hopper "Quelle est la capitale de la France?"
hopper "Explique-moi le machine learning"

# Emails (Phase 2)
hopper "Lis mes nouveaux emails importants"

# IoT (Phase 2)
hopper "Allume les lumières du salon"
```

### API REST

```bash
# Envoyer une commande via API
curl -X POST http://localhost:5000/command \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour HOPPER", "user_id": "demo"}'

# Consulter le contexte
curl http://localhost:5000/context/demo

# Vérifier les capacités
curl http://localhost:5000/api/v1/capabilities
```

## 📊 Performances

### Matériel Recommandé

**Configuration Testée (MacBook Pro M3 Max):**
- CPU: 14 cœurs (10 performance + 4 efficiency)
- GPU: 30 cœurs
- RAM: 36 Go unifiée
- Neural Engine: 16 cœurs

**Performances attendues:**
- Inférence LLM (13B): ~20-30 tokens/seconde
- Reconnaissance vocale: <1 seconde (Whisper medium)
- Synthèse vocale: temps réel
- Latence totale commande vocale: 2-4 secondes

## 🗓️ Feuille de Route

### Phase 1: Infrastructure de Base (Mois 1-2) ✅ EN COURS

- [x] Architecture microservices Docker
- [x] Orchestrateur central avec routage basique
- [x] Module d'exécution système en C
- [x] Intégration LLM avec mode simulation
- [ ] CLI fonctionnel avec mode interactif
- [ ] Tests d'intégration bout-en-bout

### Phase 2: Intégrations Externes (Mois 3-4)

- [ ] Module STT (Whisper) opérationnel
- [ ] Module TTS avec voix française
- [ ] Connecteur email (IMAP/SMTP)
- [ ] Connecteur calendrier
- [ ] Connecteur IoT de base
- [ ] Interface vocale complète

### Phase 3: Intelligence et Apprentissage (Mois 5-6)

- [ ] Base de connaissances vectorielle (FAISS)
- [ ] Retrieval Augmented Generation
- [ ] Fine-tuning local automatisé
- [ ] Apprentissage par renforcement basique
- [ ] Système de feedback utilisateur
- [ ] Suggestions proactives

### Phase 4: Sécurité et Autonomie (Mois 7-8)

- [ ] Module d'authentification vocale
- [ ] Reconnaissance faciale
- [ ] Chiffrement des données sensibles
- [ ] Mode hors-ligne complet
- [ ] Gestion multi-utilisateurs
- [ ] Règles de sécurité configurables

### Phase 5: Optimisations (Mois 9-12)

- [ ] Optimisation C++ du moteur LLM
- [ ] Quantization avancée (int4)
- [ ] Cache intelligent des réponses
- [ ] Apprentissage continu en arrière-plan
- [ ] Interface graphique (dashboard)
- [ ] Application mobile companion

## 🛠️ Développement

### Structure du Projet

```
HOPPER/
├── docker/                 # Dockerfiles de chaque service
├── src/
│   ├── orchestrator/      # Orchestrateur central (Python)
│   ├── llm_engine/        # Moteur LLM (Python/C++)
│   ├── system_executor/   # Exécution système (C)
│   ├── stt/              # Speech-to-Text (Python)
│   ├── tts/              # Text-to-Speech (Python)
│   ├── auth/             # Authentification (Python)
│   └── connectors/       # Connecteurs externes (Python)
├── config/               # Fichiers de configuration
├── data/                 # Données et modèles
├── docs/                 # Documentation
├── tests/                # Tests unitaires et d'intégration
├── docker-compose.yml    # Orchestration des services
└── hopper-cli.py        # Interface CLI

```

### Lancer en Mode Développement

```bash
# Rebuild et démarrage
docker-compose up --build

# Voir les logs d'un service
docker-compose logs -f orchestrator

# Redémarrer un service
docker-compose restart llm

# Arrêter tous les services
docker-compose down
```

### Tests

```bash
# Tests unitaires
python -m pytest tests/

# Test d'un service spécifique
docker-compose exec orchestrator python -m pytest

# Tests d'intégration
./tests/integration_test.sh
```

## 🔒 Sécurité et Confidentialité

- **100% Local**: Aucune donnée envoyée au cloud
- **Chiffrement**: Données sensibles chiffrées au repos
- **Authentification**: Reconnaissance vocale/faciale
- **Isolation**: Chaque service dans son conteneur
- **Logs auditables**: Traçabilité complète des actions
- **Mode hors-ligne**: Fonctionnement sans Internet

## 📚 Documentation

- [Guide d'Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Guide du Développeur](docs/DEVELOPMENT.md)
- [Foire Aux Questions](docs/FAQ.md)

## 🤝 Contribution

Ce projet est actuellement en développement actif. Les contributions sont les bienvenues!

## 📄 Licence

MIT License - voir le fichier [LICENSE](LICENSE)

## 🙏 Remerciements

- OpenAI Whisper pour la reconnaissance vocale
- Meta AI pour LLaMA
- llama.cpp pour l'optimisation d'inférence
- La communauté open-source

## 📞 Contact

- **Auteur**: jilani-BLK
- **Projet**: H.O.P.P.E.R
- **Repository**: [GitHub](https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor)

---

**Note**: HOPPER est actuellement en Phase 1 (Alpha). De nombreuses fonctionnalités sont en développement actif.
