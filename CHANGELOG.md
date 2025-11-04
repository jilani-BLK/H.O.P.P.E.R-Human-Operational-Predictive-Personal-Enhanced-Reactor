# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère à [Semantic Versioning](https://semver.org/lang/fr/).

## [Non publié]

### À venir (Phase 3)
- Amélioration routing (75% → 90%+ précision)
- Démonstration complète RAG avec Knowledge Base
- Commande "hopper learn" pour apprentissage interactif
- Optimisation performance (<1s conversations courtes)
- Streaming réponses LLM token-par-token
- PermissionManager + ConsentPolicy (SQLite)
- AuditStore pour traçabilité complète
- ActionNarrator + TTS feedback
- Knowledge Graph Neo4j integration
- GPU acceleration pour LLM (Metal macOS)
- Cache de plans LLM (Redis)
- Tests BDD avec Gherkin/Behave
- Interface graphique (dashboard)

## [0.2.1-phase2] - 2025-11-04

### 🎉 Phase 2 VALIDÉE - Conversations LLM (MAJEUR)

#### ✅ Validation Officielle
- **Tests automatisés**: 15/20 réussis (75%, critère ≥70% atteint)
- **Performance**: 810ms moyenne (cible <5s atteinte)
- **Mode offline**: 100% via Ollama v0.12.6
- **Conversations françaises**: Naturelles avec llama3.2 (2GB)
- **Multi-tour**: Contexte maintenu sur 10 messages

#### Nouveaux Composants (1075+ lignes)

**LLMDispatcher** (`src/orchestrator/core/llm_dispatcher.py`, 190 lignes):
- Routage automatique système vs conversation
- Templates de prompts avec personnalité HOPPER
- Détection contextuelle d'intentions (mots-clés + patterns)
- Intégration API LLM service
- Gestion historique et contexte

**Phase2 Routes** (`src/orchestrator/api/phase2_routes.py`, 212 lignes):
- Endpoint unifié `POST /api/v1/command`
- Support dual: commandes système + conversations
- Modèles Pydantic: CommandRequest, CommandResponse
- Health checks détaillés: `/api/v1/status`
- Format JSON structuré (type, action/response, durée, tokens)

**Orchestrateur Phase 2** (`src/orchestrator/main_phase2.py`, 75 lignes):
- FastAPI app avec phase2_routes
- CORS configuré
- Startup/shutdown events
- Logging structuré

**ConversationManager** (`src/orchestrator/core/conversation_manager.py`, 200 lignes):
- Gestion historique conversations en mémoire
- Dataclasses Message/Conversation
- Limite 10 messages (gestion tokens)
- Truncation automatique
- Thread-safe storage

**CLI v2 Interactif** (`hopper_cli_v2.py`, 178 lignes):
- Mode REPL avec prompt `hopper>`
- Mode single-command pour questions/commandes ponctuelles
- Commandes spéciales: `clear`, `help`, `exit`
- Affichage enrichi: emoji, durée, tokens
- Historique session complet

**Tests Validation** (`scripts/test/validate_phase2.py`, 220 lignes):
- 20 tests automatisés (12 conversations + 8 système)
- Validation type (système/conversation)
- Vérification mots-clés dans réponses
- Mesure latence par test
- Rapport détaillé avec statistiques

#### Intégration LLM

**Ollama + llama3.2**:
- Version Ollama: v0.12.6
- Modèle actif: llama3.2:latest (2GB)
- Modèles disponibles: llama2, mistral, llama3.1:8b, llama3.2
- Configuration Docker: host.docker.internal:11434
- Performance: 30-50 tokens/seconde

**Knowledge Base FAISS**:
- 25 documents chargés
- Vector Store: IndexFlatIP (similarité cosine)
- Embeddings: all-MiniLM-L6-v2 (384 dimensions)
- Recherche: <50ms par requête
- Statut: Infrastructure prête (RAG à tester Phase 3)

#### Métriques Phase 2

**Performance**:
- Latence système: 25ms moyenne (min=4ms, max=28ms)
- Latence conversation: 1529ms moyenne (min=342ms, max=2849ms)
- Latence globale: 810ms moyenne
- Tokens par échange: 250-310 (prompt ~150, réponse 100-160)

**Tests**:
- Système: 6/8 réussis (75%)
- Conversation: 9/12 réussis (75%)
- Total: 15/20 réussis (75%)

**Qualité**:
- Français naturel: 100% réponses correctes
- Pertinence: 75% réponses pertinentes
- Cohérence persona: HOPPER maintient son identité
- Contexte multi-tour: Références bien comprises

#### Modifications Configuration

**docker-compose.yml**:
- Variables Ollama: `OLLAMA_HOST=http://host.docker.internal:11434`
- Modèle: `OLLAMA_MODEL=llama3.2`
- Contexte: `LLM_CONTEXT_SIZE=4096`

**docker/orchestrator.Dockerfile**:
- CMD changé vers `main_phase2.py`
- Commentaires phases (Phase 1, 2, 3+)

#### Documentation

- `PHASE2_VALIDATION.md`: Résultats tests détaillés
- `PHASE2_FINAL_REPORT.md`: Rapport complet 15 pages
- `PHASE2_QUICK_REF.md`: Guide rapide utilisation
- `README.md`: Section Phase 2 mise à jour

#### Problèmes Connus

**Routing (3 échecs)**:
- "Quel modèle utilises-tu?" → Mal routé vers système
- "À quoi servent les fichiers?" → Mal routé vers système
- "ls /tmp" → Mal routé vers conversation
- Solution Phase 3: Classification LLM des intentions

**Limitation Docker**:
- "ouvre Calculator" → Échec (pas de GUI dans conteneur)
- Comportement attendu et documenté

## [0.2.0-alpha] - 2025-11-01

### 🚀 Architecture LLM-First (MAJEUR)

#### Nouveaux Composants Core (1730+ lignes)
- **Models Layer** (`core/models.py`, 430 lignes): Pydantic schemas complets
  - `InteractionEnvelope`: Normalisation tous inputs (voix, texte, événements)
  - `SystemPlan`: Plan d'action généré par LLM
  - `ToolCall`: Appels d'outils structurés
  - `PerceptionEvent`, `ConsentPolicy`, `AuditEntry`
  - Enums: `RiskLevel`, `ToolStatus`, `ConsentMode`, `InteractionType`

- **PromptAssembler** (`core/prompt_assembler.py`, 400 lignes): Injection contextuelle
  - Historique conversation complet
  - Résultats RAG (top-k=3 via FAISS)
  - Permissions actives et audit récent
  - Function calling schema pour LLM
  - Reformulation avec résultats d'exécution

- **LlmAgent** (`core/llm_agent.py`, 550 lignes): Pipeline ReAct complet
  - **THOUGHT**: Assembler contexte via PromptAssembler
  - **ACT**: LLM génère SystemPlan JSON validé Pydantic
  - **OBSERVE**: Exécution séquentielle d'outils avec permissions
  - **ANSWER**: Reformulation naturelle avec résultats
  - JSON parsing robuste avec `JSONDecoder.raw_decode()`
  - Timeout fallback + retry logic

- **PerceptionBus** (`core/perception_bus.py`, 350 lignes): Event-driven architecture
  - Pub/Sub asyncio avec `asyncio.Queue`
  - Subscribe par type ou wildcard
  - Historique 100 derniers événements
  - Stats par source et type

- **LlmFirstDispatcher** (`core/llm_first_dispatcher.py`): Dispatcher intelligent
  - Remplace regex hardcodées par planning LLM
  - Fallback heuristique si LLM échoue
  - Métriques succès/échec + timing

- **ToolExecutor** (`core/tool_executor.py`): Unified tool execution
  - 6 outils supportés: system_executor, llm_knowledge, email, calendar, tts, stt
  - Timeout configurable par outil
  - Préparation automatique des payloads
  - Logging détaillé + error handling

#### System Executor C - Refactorisation Majeure
- ✅ **JSON Parsing Complet** avec cJSON
  - Parsing requêtes POST avec body accumulation
  - Extraction `action`, `path`, `content` du JSON
  - Switch sur actions: create_file, delete_file, list_directory

- ✅ **Nouvelles Fonctions**
  - `create_file_with_content(path, content)`: Création avec contenu custom
  - `delete_file(path)`: Suppression avec `remove()`
  - `list_directory(path)`: Listage avec `opendir()` + `readdir()`
  - JSON responses structurées

- ✅ **Performance**: <10ms par action (vs 50-100ms Python)

#### Bugs Critiques Résolus
- ✅ **CLI Broken** (P0): Dépendance `requests` manquante → installée
- ✅ **Context Manager** (P0): Historique non sauvegardé → `append(exchange)` ajouté
- ✅ **System Executor** (P0): Stub hardcodé → JSON parsing complet

### Tests d'Intégration
- ✅ Test suite complète (`tests/test_llm_first_integration.py`)
- ✅ Tests end-to-end: create_file, list_directory, delete_file
- ✅ Test multi-tour conversation avec contexte
- ✅ Test error handling + JSON parsing robustness
- ✅ Tests direct system_executor C

### Documentation
- ✅ `LLM_FIRST_SUCCESS.md`: Rapport succès complet (validation, tests, métriques)
- ✅ `QUICKSTART_LLM_FIRST.md`: Guide démarrage rapide
- ✅ `ARCHITECTURE_LLM_FIRST.md`: Documentation architecture technique
- ✅ `ETAT_REEL.md`: État honnête projet avant transformation
- ✅ `CORRECTIFS_APPLIQUES.md`: Documentation bugs critiques

### Améliorations Performance
- LLM planning: 15-20s (acceptable pour CPU Mistral-7B)
- System Executor C: <10ms par action
- Total pipeline: ~18-20s user input → final response

### À Venir (Prochaine Version)
- PermissionManager + SQLite
- AuditStore + SQLite
- Tests BDD (Gherkin/Behave)
- GPU acceleration LLM (→ 2-3s au lieu de 15s)
- Cache plans LLM (Redis)

## [0.1.0-alpha] - 2025-10-22

### Ajouté

#### Architecture Microservices
- Architecture complète en 7 microservices Docker
- Communication inter-services via REST HTTP/JSON
- Isolation complète via conteneurs Docker
- Orchestration avec Docker Compose

#### Orchestrateur Central (Python)
- API REST complète avec FastAPI
- Système de routage d'intentions (IntentDispatcher)
- Gestion du contexte conversationnel (ContextManager)
- Registre de services avec health checks (ServiceRegistry)
- Support de 50 derniers échanges en mémoire
- Gestion des timeouts et retry logic

#### Module d'Exécution Système (C)
- Serveur HTTP léger avec libmicrohttpd
- Actions système: création/suppression fichiers
- Listage de répertoires
- Lancement d'applications macOS
- Logging structuré
- Réponses JSON avec cJSON

#### Moteur LLM (Python/C++)
- Support llama.cpp pour inférence optimisée
- Mode simulation (sans modèle) pour tests
- API de génération de texte
- Support du contexte enrichi
- Prêt pour GPU Apple Silicon (Metal)
- Support modèles LLaMA 2 / Mistral

#### Module STT (Python)
- Intégration OpenAI Whisper
- Support multilingue (français prioritaire)
- API de transcription de fichiers audio
- Mode streaming prévu (Phase 2)

#### Module TTS (Python)
- Synthèse vocale avec support macOS
- API de génération audio
- Support voix françaises
- Latence optimisée

#### Module d'Authentification (Python)
- API de vérification vocale
- API de vérification faciale (skeleton)
- Système d'enregistrement utilisateur
- Prêt pour SpeechBrain/Resemblyzer

#### Module Connecteurs (Python)
- Structure pour connecteurs externes
- Squelettes Email, IoT, Calendrier
- API unifiée pour intégrations

#### CLI (Python)
- Mode interactif complet
- Mode commande directe
- Commandes système (/health, /clear, /help)
- Formatage coloré des sorties
- Gestion d'erreurs élégante
- Support des alias

#### Infrastructure
- Script d'installation automatisé (install.sh)
- Configuration via fichier .env
- Makefile avec 25+ commandes utiles
- Fichiers .gitignore complets
- Structure de dossiers complète

#### Documentation
- README.md principal (guide complet)
- ARCHITECTURE.md (60+ pages techniques)
- QUICKSTART.md (installation rapide)
- DEVELOPMENT.md (guide développeur)
- CONTRIBUTING.md (guide de contribution)
- STRUCTURE.md (visualisation arborescence)
- PROJECT_SUMMARY.md (résumé)
- CHANGELOG.md (ce fichier)

#### Tests
- Tests d'intégration de base
- Structure de tests unitaires
- Commandes make pour testing

### Sécurité
- Isolation des services via Docker
- Logging de toutes les actions
- Validation des entrées
- Support authentification multi-facteurs (prévu)
- Aucune dépendance cloud

### Performances
- Code C pour actions critiques
- C++ pour inférence LLM
- Support GPU Apple Silicon
- Latence <100ms pour actions système
- Pool de connexions HTTP réutilisables

## Notes de Version

### [0.1.0-alpha] - Phase 1 Complétée

Cette version alpha marque l'achèvement de la **Phase 1** du projet HOPPER:

**✅ Accomplissements**:
- Architecture microservices complète et fonctionnelle
- 7 services dockerisés et orchestrés
- >3000 lignes de code (Python, C, C++)
- 100+ pages de documentation
- CLI interactif opérationnel
- Infrastructure prête pour Phase 2

**⚠️ Limitations Connues**:
- LLM en mode simulation (modèle non inclus)
- STT/TTS en mode basique
- Authentification en mode skeleton
- Connecteurs non implémentés (Phase 2)
- Pas d'interface graphique (Phase 5)

**🎯 Prochaine Version (0.2.0)**:
- Intégration modèle LLM réel
- Connecteur Email fonctionnel
- Interface vocale complète (STT+TTS)
- Connecteur IoT de base
- Tests d'intégration complets

### Compatibilité

- **Systèmes**: macOS M1/M2/M3, Linux x86_64
- **Docker**: >= 20.10
- **Python**: >= 3.10
- **Compilateur C**: gcc >= 12.0 ou clang >= 14.0

### Installation

```bash
git clone https://github.com/jilani-BLK/H.O.P.P.E.R-Human-Operational-Predictive-Personal-Enhanced-Reactor.git
cd HOPPER
./install.sh
```

### Migration

Première version - Pas de migration nécessaire.

---

**Légende**:
- `Ajouté` : Nouvelles fonctionnalités
- `Modifié` : Changements de fonctionnalités existantes
- `Déprécié` : Fonctionnalités bientôt supprimées
- `Supprimé` : Fonctionnalités supprimées
- `Corrigé` : Corrections de bugs
- `Sécurité` : Vulnérabilités corrigées

---

*Dernière mise à jour: 22 octobre 2025*
