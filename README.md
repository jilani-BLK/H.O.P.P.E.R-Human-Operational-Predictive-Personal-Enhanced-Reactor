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

**Version**: Phase 2 optimisée (22 Octobre 2025)

| Fonctionnalité | Status | Performance |
|---------------|--------|-------------|
| Architecture 7 services | ✅ 100% | Latence <10ms |
| LLM (Mistral-7B) | ✅ Opérationnel | 8-20s (optimisé -25%) |
| Conversation multi-tour | ✅ Parfait | 50 échanges, contexte maintenu |
| RAG (Knowledge Base) | ✅ Parfait | 100% précision, 50ms learn |
| Mode offline | ✅ 100% | Garanti |
| Tests automatisés | ✅ 53/53 | 100% succès |

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
# Mode interactif
python3 hopper-cli.py -i

# Commandes système
hopper "Crée un fichier notes.txt"
hopper "Ouvre l'application Calculatrice"

# Questions
hopper "Explique-moi le machine learning en termes simples"
hopper "Résume ce document PDF"

# Emails (Phase 2)
hopper "Lis mes nouveaux emails importants"

# Contrôle IoT (Phase 2)
hopper "Allume les lumières du salon"
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
