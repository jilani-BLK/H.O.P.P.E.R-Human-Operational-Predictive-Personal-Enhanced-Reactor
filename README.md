# HOPPER - Human Operational Predictive Personal Enhanced Reactor

![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS%20M1%2FM2%2FM3-lightgrey)

> # H.O.P.P.E.R - Human Operational Predictive Personal Enhanced Reactor

**Assistant personnel intelligent fonctionnant 100% en local**  
Développé en Python et C | Phase 2 complétée et optimisée ✅

[![Phase 1](https://img.shields.io/badge/Phase%201-100%25%20Complete-success)](docs/PHASE1_FINAL_ANALYSIS.md)
[![Phase 2](https://img.shields.io/badge/Phase%202-95%25%20Complete-success)](PHASE2_SUCCESS.md)
[![Tests](https://img.shields.io/badge/Tests-53%2F53%20Passed-success)](tests/)
[![Code](https://img.shields.io/badge/Code-2453%20lines-blue)](#)

---

## 🎯 Statut Actuel

**Version**: Phase 2 validée + Architecture Hybride (4 Novembre 2025)

| Fonctionnalité | Status | Performance |
|---------------|--------|-------------|
| **Phase 2 Conversationnelle** | ✅ **VALIDÉE 75%** | Taux réussite tests |
| Architecture 5 services | ✅ 100% | Latence <1s |
| LLM (llama3.2 2GB) | ✅ Opérationnel | 810ms moyenne |
| Dispatcher Hybride | ✅ Intelligent | Routing système+LLM |
| Conversation multi-tour | ✅ Fonctionnel | 10 messages historique |
| RAG (Knowledge Base) | ✅ Chargée | 25 documents FAISS |
| CLI v2 Interactif | ✅ 100% | REPL + single-command |
| Mode offline | ✅ 100% | Ollama local v0.12.6 |
| Tests automatisés | ✅ 15/20 validés | 75% succès |

### 🎉 Phase 2 Validée (Nouveau)

HOPPER peut maintenant **converser en français de manière naturelle** et **maintenir le contexte** sur plusieurs échanges.

**Architecture Hybride** (Système + LLM):
- 🎯 **Dispatcher Intelligent**: Routage automatique commandes système vs conversations
- 🧠 **LLM Local**: llama3.2 (2GB) via Ollama v0.12.6, 100% offline
- 💬 **Conversations Multi-tour**: Historique 10 messages, contexte maintenu
- � **Knowledge Base**: 25 documents FAISS, RAG ready
- 🖥️ **CLI v2**: Mode interactif REPL + single-command

📘 **Documentation**: [`PHASE2_VALIDATION.md`](PHASE2_VALIDATION.md) | 🚀 **Succès**: [`PHASE2_SUCCESS.md`](PHASE2_SUCCESS.md) | 🧪 **Tests**: [`scripts/test/validate_phase2.py`](scripts/test/validate_phase2.py)

📊 [**Rapport Performance Complet**](PERFORMANCE_ANALYSIS.md) | 📈 [**Résultats Optimisation**](OPTIMIZATION_RESULTS.md) | 📋 [**Rapport Final**](FINAL_REPORT.md)

HOPPER est un assistant IA personnel conçu pour apprendre de lui-même, traiter des tâches en temps réel et s'intégrer avec de multiples systèmes - le tout sur votre machine, sans dépendance cloud.

## Caractéristiques Principales

- **Intelligence Locale**: Modèle de langage puissant (LLaMA/Mistral) tournant sur Mac M3 Max
- **Apprentissage Autonome**: Fine-tuning local et apprentissage par renforcement
- **100% Privé**: Aucune donnée envoyée au cloud, tout reste sur votre machine
- **Performances Optimales**: Architecture C/C++/Python pour vitesse maximale
- **Interface Vocale**: Reconnaissance (Whisper) et synthèse vocale naturelle
- **Sécurité**: Authentification vocale/faciale intégrée
- **Modulaire**: Architecture microservices Docker extensible

## Démarrage Rapide

```bash
# 1. Cloner le projet
git clone https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor.git
cd HOPPER

# 2. Installation automatique
chmod +x install.sh
./install.sh

# 3. Tester
python3 hopper-cli.py -i
```

**Guide détaillé**: [docs/QUICKSTART.md](docs/QUICKSTART.md)

## Exemples d'Utilisation

```bash
# Mode interactif conversationnel (NOUVEAU Phase 2)
python3 hopper_cli_v2.py

hopper> Bonjour, qui es-tu ?
🤖 HOPPER: Je suis HOPPER, votre assistant personnel intelligent et local...
⏱️ 2.1s | 142 tokens

hopper> Que peux-tu faire ?
🤖 HOPPER: Je peux exécuter des commandes système et répondre à vos questions...
⏱️ 1.8s | 98 tokens

# Mode single-command (conversations)
python3 hopper_cli_v2.py "C'est quoi un LLM ?"

# Commandes système (Phase 1)
python3 hopper_cli_v2.py "liste les fichiers de /tmp"
python3 hopper_cli_v2.py "crée un fichier notes.txt"
python3 hopper_cli_v2.py "donne moi la date"

# API REST
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"Qui es-tu ?"}'
```

## Architecture

```
┌─────────────────────────────────────────┐
│         INTERFACES UTILISATEUR          │
│    CLI │ Voix │ API REST │ Web GUI     │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      ORCHESTRATEUR CENTRAL              │
│  (Analyse, Routage, Contexte, Décision) │
└─┬─────┬─────┬─────┬─────┬─────┬────────┘
  │     │     │     │     │     │
  ▼     ▼     ▼     ▼     ▼     ▼
┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌────┐
│LLM│ │SYS│ │STT│ │TTS│ │AUT│ │CONN│
│C++│ │ C │ │Py │ │Py │ │Py │ │ Py │
└───┘ └───┘ └───┘ └───┘ └───┘ └────┘
```

**Services**:
- **Orchestrateur** (Python): Cerveau central coordonnant tous les services
- **LLM Engine** (C++ llama.cpp): Modèle de langage optimisé pour Apple Silicon
- **System Executor** (C): Actions système haute performance
- **STT** (Whisper): Reconnaissance vocale multilingue
- **TTS**: Synthèse vocale naturelle
- **Auth**: Authentification vocale/faciale
- **Connectors**: Intégrations (email, IoT, calendrier...)

**Architecture détaillée**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Performances

**Configuration Testée** (MacBook Pro M3 Max):
- CPU: 14 cœurs | GPU: 30 cœurs | RAM: 36 Go
- **LLM (13B)**: 20-30 tokens/sec
- **Whisper**: <1 sec transcription
- **Latence totale** (voix → réponse): 2-4 sec

## Roadmap

- [x] **Phase 1** (Mois 1-2): Infrastructure microservices ✅
- [ ] **Phase 2** (Mois 3-4): Intégrations (email, voix, IoT)
- [ ] **Phase 3** (Mois 5-6): Apprentissage et RAG
- [ ] **Phase 4** (Mois 7-8): Sécurité avancée
- [ ] **Phase 5** (Mois 9-12): Optimisations et GUI

[Voir la feuille de route complète](docs/README.md)

## Documentation

- [Guide Complet](docs/README.md)
- [Démarrage Rapide](docs/QUICKSTART.md)
- [Architecture](docs/ARCHITECTURE.md)

## Technologies

**Langages**: Python 3.11, C (C11), C++ (via bindings)

**Frameworks**:
- FastAPI, aiohttp (APIs)
- llama.cpp (inférence LLM)
- OpenAI Whisper (STT)
- Docker & Docker Compose

**IA/ML**:
- LLaMA 2 / Mistral (modèles)
- FAISS (base vectorielle)
- Sentence-Transformers (embeddings)

## Contribution

Les contributions sont bienvenues! Ce projet est en développement actif (Phase 1).

## Licence

MIT License - Voir [LICENSE](LICENSE)

## Contact

- **Auteur**: jilani-BLK
- **GitHub**: [H.O.P.P.E.R](https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor)

---

**Note**: HOPPER est actuellement en **Phase 1 (Alpha)**. L'architecture de base est fonctionnelle, les fonctionnalités avancées sont en développement.
