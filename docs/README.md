# HOPPER - Documentation# 📚 Documentation HOPPER# HOPPER - Human Operational Predictive Personal Enhanced Reactor



Documentation complète du projet HOPPER (Human Operational Predictive Personal Enhanced Reactor).



## Structure de la Documentation**H.O.P.P.E.R** - Human Operational Predictive Personal Enhanced Reactor![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue)



### Documents Principaux![License](https://img.shields.io/badge/license-MIT-green)



#### Guides UtilisateurDocumentation complète du projet organisée par catégorie.![Platform](https://img.shields.io/badge/platform-macOS%20|%20Linux-lightgrey)

- **[USER_GUIDE.md](USER_GUIDE.md)** - Guide complet d'utilisation de HOPPER

- **[guides/QUICKSTART.md](guides/QUICKSTART.md)** - Démarrage rapide (installation et premier lancement)

- **[guides/VOICE_SETUP.md](guides/VOICE_SETUP.md)** - Configuration du système vocal (STT/TTS)

---Assistant personnel intelligent autonome fonctionnant entièrement en local, conçu pour apprendre de lui-même et traiter des tâches en temps réel.

#### Guides Développeur

- **[DEV_GUIDE.md](DEV_GUIDE.md)** - Guide de développement et architecture

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture technique complète

- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** - Optimisations Docker et performances## 🗂️ Structure de la Documentation## 🎯 Objectifs



#### Validation et Statut

- **[VALIDATION_COMPLETE.md](VALIDATION_COMPLETE.md)** - Validation complète des 6 phases du projet

### 🏗️ [Architecture](./architecture/)HOPPER est envisagé comme un assistant personnel intelligent qui:

#### Support

- **[guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)** - Résolution de problèmes courantsDocumentation sur l'architecture système et les composants

- **[guides/CLI_GUIDE.md](guides/CLI_GUIDE.md)** - Guide de la ligne de commande

- **Apprend de lui-même** via apprentissage par renforcement et fine-tuning local

### Dossiers Spécialisés

- **[ARCHITECTURE.md](./architecture/ARCHITECTURE.md)** - Architecture globale du système- **Fonctionne 100% en local** sur votre machine (aucune dépendance cloud)

#### `/guides`

Guides pratiques et tutoriels pour l'utilisation et le développement- **[ARCHITECTURE_RAG_AVANCEE.md](./architecture/ARCHITECTURE_RAG_AVANCEE.md)** - Détails RAG avancé- **Prend des décisions autonomes** et propose des suggestions proactives



#### `/security`- **[ARCHITECTURE_RAG_VISUELLE.md](./architecture/ARCHITECTURE_RAG_VISUELLE.md)** - Schémas architecture RAG- **S'intègre avec de multiples systèmes** (OS, web, IoT, autres machines)

Documentation relative à la sécurité, authentification, et protection des données

- **[PLAN_IMPLEMENTATION_RAG_AVANCE.md](./architecture/PLAN_IMPLEMENTATION_RAG_AVANCE.md)** - Plan d'implémentation- **Optimise les performances** avec C/C++ pour le calcul et Python pour l'IA

#### `/reports`

Rapports d'analyse de performance et problèmes identifiés- **Garantit la sécurité** avec authentification vocale/faciale



#### `/phases`### 🔒 [Security](./security/)

Documents de planification et status des différentes phases du projet (1 à 6)

Documentation sécurité et rapports d'audit## 🏗️ Architecture

#### `/archives`

Anciens documents conservés pour référence historique



## Phases du Projet- **[ANALYSE_COMPLETE_SECURITE.md](./security/ANALYSE_COMPLETE_SECURITE.md)** - Analyse sécurité complète### Architecture Microservices



Le projet HOPPER a été développé en 6 phases :- **[RAPPORT_FINAL_SECURITE.md](./security/RAPPORT_FINAL_SECURITE.md)** - Rapport final corrections (11 failles)



1. **Phase 1** : Pipeline de base (STT → LLM → TTS)- **[HTTPS_TLS_SETUP.md](./security/HTTPS_TLS_SETUP.md)** - Guide HTTPS/TLS production```

2. **Phase 2** : Knowledge Base Neo4j avec RAG

3. **Phase 3** : Orchestrateur central- **[QUICKSTART_SECURITE.md](./security/QUICKSTART_SECURITE.md)** - Démarrage rapide sécurité┌─────────────────────────────────────────────────────────┐

4. **Phase 4** : Sécurité et Authentication

5. **Phase 5** : Connecteurs et Système- **[TABLEAU_BORD_SECURITE.md](./security/TABLEAU_BORD_SECURITE.md)** - Tableau de bord sécurité│                   UTILISATEUR                            │

6. **Phase 6** : Monitoring et Maintenance

- **[RAPPORT_CORRECTIONS_SECURITE.md](./security/RAPPORT_CORRECTIONS_SECURITE.md)** - Détails corrections│              (CLI / Voix / Interface)                    │

Voir [VALIDATION_COMPLETE.md](VALIDATION_COMPLETE.md) pour l'état complet de toutes les phases.

- **[RESUME_SESSION_CORRECTIONS.md](./security/RESUME_SESSION_CORRECTIONS.md)** - Résumé sessions└───────────────────────┬─────────────────────────────────┘

## Démarrage Rapide

                        │

```bash

# 1. Cloner le projet### 📋 [Phases](./phases/)┌───────────────────────▼─────────────────────────────────┐

git clone https://github.com/jilani-BLK/H.O.P.P.E.R.git

cd HOPPERDocumentation des différentes phases du projet│              ORCHESTRATEUR CENTRAL (Python)              │



# 2. Lancer les services│  • Analyse d'intention                                   │

docker-compose up -d

#### Phase 1 - Fondations│  • Gestion du contexte conversationnel                   │

# 3. Vérifier le statut

./scripts/test_quick.sh- **[PHASE1_FINAL_REPORT.md](./phases/phase1/PHASE1_FINAL_REPORT.md)** - Rapport final Phase 1│  • Routage des commandes                                 │



# 4. Accéder à l'interface- **[PHASE1_SUCCESS.md](./phases/phase1/PHASE1_SUCCESS.md)** - Succès Phase 1│  • Règles heuristiques et décisions                      │

open http://localhost:5050

```- **[PHASE1_COMPLETE.md](./phases/phase1/PHASE1_COMPLETE.md)** - Phase 1 complète└─────┬────┬────┬────┬────┬────┬───────────────────────┘



Pour plus de détails, consulter [guides/QUICKSTART.md](guides/QUICKSTART.md).- **[PHASE1_STATUS.md](./phases/phase1/PHASE1_STATUS.md)** - Statut Phase 1      │    │    │    │    │    │



## Support et Contribution- **[PHASE1_FINAL_ANALYSIS.md](./phases/phase1/PHASE1_FINAL_ANALYSIS.md)** - Analyse finale      ▼    ▼    ▼    ▼    ▼    ▼



- **Issues** : Utiliser les templates dans `.github/ISSUE_TEMPLATE/`   ┌───┐┌───┐┌───┐┌───┐┌───┐┌────┐

- **Contribution** : Voir [../CONTRIBUTING.md](../CONTRIBUTING.md)

- **Code de Conduite** : [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)#### Phase 2 - Intégration   │LLM││SYS││STT││TTS││AUT││CONN│



## Ressources Externes- **[PHASE2_PLAN.md](./phases/phase2/PHASE2_PLAN.md)** - Plan Phase 2   │   ││EXE││   ││   ││H  ││    │



- **Repository** : https://github.com/jilani-BLK/H.O.P.P.E.R- **[PHASE2_SUCCESS.md](./phases/phase2/PHASE2_SUCCESS.md)** - Succès Phase 2   └───┘└───┘└───┘└───┘└───┘└────┘

- **Ollama** : https://ollama.ai

- **Neo4j** : https://neo4j.com- **[ANALYSE_FINALE_PHASES_1_2.md](./phases/phase2/ANALYSE_FINALE_PHASES_1_2.md)** - Analyse Phases 1&2   C++   C   Py   Py   Py   Py



## License```



MIT License - Voir [../LICENSE](../LICENSE)#### Phase 3.5 - RAG Avancé


- **[PHASE_3_5_COMPLETE.md](./phases/phase3_5/PHASE_3_5_COMPLETE.md)** - Phase 3.5 complète### Modules Principaux

- **[AUDIT_PHASE_3_5.md](./phases/phase3_5/AUDIT_PHASE_3_5.md)** - Audit Phase 3.5

- **[PHASE_3_5_SETUP_SUCCES.md](./phases/phase3_5/PHASE_3_5_SETUP_SUCCES.md)** - Setup succès1. **Orchestrateur Central** (Python)

- **[RESUME_EXECUTIF_PHASE_3_5.md](./phases/phase3_5/RESUME_EXECUTIF_PHASE_3_5.md)** - Résumé exécutif   - Cerveau de HOPPER qui coordonne tous les services

- **[PHASE_3_5_README.md](./phases/phase3_5/PHASE_3_5_README.md)** - README Phase 3.5   - Analyse d'intention et routage des commandes

- **[SUIVI_PHASE_3_5.md](./phases/phase3_5/SUIVI_PHASE_3_5.md)** - Suivi progression   - Gestion du contexte conversationnel

- **Semaines détaillées**: SEMAINE_1, SEMAINE_2, SEMAINE_3   - Logique de décision et règles heuristiques



### 📖 [Guides](./guides/)2. **Moteur LLM** (C++ avec llama.cpp)

Guides d'utilisation et de développement   - Modèle de langage local (LLaMA 2 / Mistral)

   - Inférence optimisée sur GPU Apple Silicon

- **[QUICKSTART.md](./guides/QUICKSTART.md)** - Démarrage rapide   - Contexte étendu via Retrieval Augmented Generation

- **[DEVELOPMENT.md](./guides/DEVELOPMENT.md)** - Guide développement   - Fine-tuning local continu

- **[VOICE_SETUP.md](./guides/VOICE_SETUP.md)** - Configuration voix (STT/TTS)

- **[TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md)** - Dépannage3. **Module d'Exécution Système** (C)

- **[DOCKER_INTEGRATION_FIX.md](./guides/DOCKER_INTEGRATION_FIX.md)** - Fix Docker   - Actions système directes (fichiers, processus)

   - Performances optimales en C pur

### 📊 [Reports](./reports/)   - Serveur HTTP léger avec libmicrohttpd

Rapports d'analyse et archives

4. **Module STT** (Python + Whisper)

- **[PERFORMANCE_ANALYSIS.md](./reports/PERFORMANCE_ANALYSIS.md)** - Analyse performances   - Reconnaissance vocale locale

- **[OPTIMIZATIONS.md](./reports/OPTIMIZATIONS.md)** - Optimisations effectuées   - Support multilingue (français prioritaire)

- **[OPTIMIZATION_RESULTS.md](./reports/OPTIMIZATION_RESULTS.md)** - Résultats optimisations   - Basé sur OpenAI Whisper

- **[RAPPORT_TESTS_COMPLET.md](./reports/RAPPORT_TESTS_COMPLET.md)** - Rapport tests complet

- **[VALIDATION_FINALE.md](./reports/VALIDATION_FINALE.md)** - Validation finale5. **Module TTS** (Python)

- **[PROBLEMES_IDENTIFIES.md](./reports/PROBLEMES_IDENTIFIES.md)** - Problèmes identifiés   - Synthèse vocale naturelle

- **[TESTS_CONCRETS_RESULTATS.md](./reports/TESTS_CONCRETS_RESULTATS.md)** - Résultats tests   - Voix française de qualité

   - Latence minimale

---

6. **Module d'Authentification** (Python)

## 🚀 Par où commencer ?   - Reconnaissance vocale du locuteur

   - Reconnaissance faciale (optionnel)

### Pour les nouveaux utilisateurs   - Gestion multi-utilisateurs

1. **[../README.md](../README.md)** - README principal du projet

2. **[guides/QUICKSTART.md](./guides/QUICKSTART.md)** - Démarrage rapide7. **Connecteurs** (Python)

3. **[architecture/ARCHITECTURE.md](./architecture/ARCHITECTURE.md)** - Comprendre l'architecture   - Email (IMAP/SMTP)

   - Calendrier (Google Calendar, iCloud)

### Pour les développeurs   - IoT (MQTT, Zigbee)

1. **[guides/DEVELOPMENT.md](./guides/DEVELOPMENT.md)** - Guide développement   - Services web et API externes

2. **[architecture/ARCHITECTURE_RAG_AVANCEE.md](./architecture/ARCHITECTURE_RAG_AVANCEE.md)** - RAG avancé

3. **[guides/TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md)** - Résolution problèmes## 🚀 Installation



### Pour la sécurité### Prérequis

1. **[security/RAPPORT_FINAL_SECURITE.md](./security/RAPPORT_FINAL_SECURITE.md)** - Rapport sécurité (score 90-95/100)

2. **[security/QUICKSTART_SECURITE.md](./security/QUICKSTART_SECURITE.md)** - Configuration sécurité- **Système d'exploitation**: macOS (M1/M2/M3), Linux

3. **[security/HTTPS_TLS_SETUP.md](./security/HTTPS_TLS_SETUP.md)** - HTTPS production- **RAM**: Minimum 16 Go, recommandé 32 Go+

- **Espace disque**: 50 Go (pour les modèles)

### Pour les chefs de projet- **Docker**: Version 20.10+

1. **[phases/phase3_5/RESUME_EXECUTIF_PHASE_3_5.md](./phases/phase3_5/RESUME_EXECUTIF_PHASE_3_5.md)** - Résumé Phase 3.5- **Python**: 3.10 ou supérieur

2. **[security/RAPPORT_FINAL_SECURITE.md](./security/RAPPORT_FINAL_SECURITE.md)** - État sécurité

3. **[reports/VALIDATION_FINALE.md](./reports/VALIDATION_FINALE.md)** - Validation complète### Installation Rapide



---```bash

# 1. Cloner le repository

## 📈 État du Projetgit clone https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor.git

cd HOPPER

### Phases

- ✅ **Phase 1** : Tests de base (100% validés)# 2. Copier le fichier de configuration

- ✅ **Phase 2** : Intégration services (100% avec mocks)cp .env.example .env

- ✅ **Phase 3.5** : RAG Avancé (138/138 tests, 100%)

# 3. Télécharger un modèle LLM (exemple avec LLaMA 2 7B)

### Sécuritémkdir -p data/models

- 🎯 **Score** : 90-95/100 (progression depuis 65/100)# Télécharger depuis HuggingFace ou utiliser un modèle existant

- ✅ **11 failles corrigées** : Critiques, urgentes, moyennes# Exemple: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF

- ✅ **Production Ready** : HTTPS, Rate Limiting, API Auth, Backup, Monitoring

# 4. Lancer les services

### Testsdocker-compose up -d

- ✅ **Phase 1** : 45/45 tests

- ✅ **Phase 2** : 25/25 tests (avec mocks HTTP)# 5. Vérifier l'état

- ✅ **Phase 3.5** : 138/138 testsdocker-compose ps

- ✅ **Total** : 208/208 tests (100%)```



---### Vérification de l'Installation



## 📞 Support```bash

# Vérifier la santé des services

Pour toute question :curl http://localhost:5000/health

- Consulter [guides/TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md)

- Voir [../CONTRIBUTING.md](../CONTRIBUTING.md) pour contribuer# Ou utiliser le CLI

- Consulter [../CHANGELOG.md](../CHANGELOG.md) pour l'historiquepython hopper-cli.py --health

```

---

## 💻 Utilisation

**Dernière mise à jour** : 22 octobre 2025  

**Version** : 1.0 - Production Ready### Mode CLI (Ligne de Commande)


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
