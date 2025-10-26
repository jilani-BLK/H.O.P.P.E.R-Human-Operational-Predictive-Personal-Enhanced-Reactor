# Architecture Détaillée de HOPPER

## Vue d'Ensemble

HOPPER est construit sur une architecture microservices où chaque composant est isolé dans un conteneur Docker, communiquant via des APIs REST HTTP/JSON. Cette conception modulaire assure:

- **Isolation**: Un crash d'un service n'affecte pas les autres
- **Scalabilité**: Chaque service peut être optimisé indépendamment
- **Portabilité**: Déploiement facile sur différents systèmes
- **Maintenabilité**: Code organisé par responsabilité

## Diagramme d'Architecture Détaillé

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERFACES                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   CLI    │  │  Voix    │  │   GUI    │  │  Mobile  │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│           ORCHESTRATEUR CENTRAL (Python:5000)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐         │
│  │   Intent    │  │   Context    │  │    Service     │         │
│  │  Dispatcher │  │   Manager    │  │    Registry    │         │
│  └─────────────┘  └──────────────┘  └────────────────┘         │
│                                                                  │
│  • Analyse d'intention (patterns regex + IA)                    │
│  • Routage vers les services appropriés                         │
│  • Gestion de l'historique conversationnel                      │
│  • Application des règles heuristiques                          │
│  • Fusion des résultats multi-services                          │
└──────┬────────┬────────┬────────┬────────┬────────┬────────────┘
       │        │        │        │        │        │
       │        │        │        │        │        │
   ┌───▼──┐ ┌──▼───┐ ┌──▼──┐ ┌───▼──┐ ┌──▼───┐ ┌──▼─────┐
   │ LLM  │ │ SYS  │ │ STT │ │ TTS  │ │ AUTH │ │  CONN  │
   │ :5001│ │ :5002│ │:5003│ │ :5004│ │ :5005│ │ :5006  │
   └──────┘ └──────┘ └─────┘ └──────┘ └──────┘ └────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      COUCHE DE DONNÉES                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   SQLite     │  │  Vector DB   │  │    Logs      │          │
│  │  (metadata)  │  │   (FAISS)    │  │   (files)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Services Détaillés

### 1. Orchestrateur Central (Port 5000)

**Technologie**: Python 3.11, FastAPI, aiohttp

**Responsabilités**:
- Point d'entrée unique pour toutes les requêtes utilisateur
- Analyse de l'intention via patterns regex et classification
- Maintien du contexte conversationnel (50 derniers échanges)
- Routage intelligent vers les services appropriés
- Application des règles de sécurité et de politiques

**Composants Internes**:

#### IntentDispatcher
```python
Patterns d'intention:
- system_action: manipulations fichiers, lancement apps
- question: requêtes nécessitant le LLM
- email: consultation/envoi d'emails
- control: commandes IoT/domotique
- general: autres cas (délégués au LLM)
```

#### ContextManager
```python
Structure du contexte:
{
  "user_id": str,
  "conversation_history": deque[50],  # FIFO
  "user_preferences": dict,
  "active_tasks": list,
  "variables": dict  # Variables de session
}
```

#### ServiceRegistry
```python
Services enregistrés:
- Healthcheck périodique (circuit breaker pattern)
- Pool de connexions HTTP réutilisables
- Retry automatique avec backoff exponentiel
- Timeout configurables par service
```

**API Endpoints**:
```
POST   /command          - Traiter une commande
GET    /health           - État de santé global
GET    /context/{user}   - Récupérer le contexte
DELETE /context/{user}   - Effacer le contexte
GET    /api/v1/services  - Liste des services
GET    /api/v1/capabilities - Capacités actuelles
```

### 2. Moteur LLM (Port 5001)

**Technologie**: Python, llama.cpp, C++ (via bindings)

**Modèle**: LLaMA 2 13B Instruct (ou Mistral 7B)

**Optimisations**:
- Quantization int4/int8 pour réduire la mémoire
- Utilisation GPU Apple Silicon via Metal
- Context window: 8192 tokens natifs
- Extension de contexte via RAG (Retrieval Augmented Generation)

**Architecture Interne**:
```
Requête → Embedding → Recherche Vectorielle → Context Injection → LLM → Réponse
            ↓              ↓                        ↓
      Sentence-      FAISS Index              Prompt Enrichi
      Transformers   (768 dim)               (query + top-k docs)
```

**Performances Attendues** (Mac M3 Max):
- Latence première réponse: 500-1000ms
- Throughput: 20-30 tokens/seconde
- Mémoire: 8-12 Go pour le modèle 13B quantifié

**API Endpoints**:
```
POST /generate  - Génération de texte
POST /embed     - Création d'embeddings
GET  /health    - État du modèle
```

### 3. Module d'Exécution Système (Port 5002)

**Technologie**: C pur, libmicrohttpd (serveur HTTP), cJSON

**Pourquoi C?**
- Performance maximale (10-100x plus rapide que Python pour I/O)
- Accès direct aux syscalls POSIX/BSD
- Empreinte mémoire minimale (~5 Mo vs ~50 Mo Python)
- Latence prévisible (pas de GC)

**Actions Supportées** (Phase 1):
```c
- create_file(path)      // Création de fichiers
- delete_file(path)      // Suppression
- list_directory(path)   // Listage
- open_application(name) // Lancement d'apps macOS
- execute_command(cmd)   // Exécution sécurisée
```

**Sécurité**:
- Whitelist de commandes autorisées
- Sandboxing via conteneur non-privilegié
- Validation stricte des chemins (pas de .., pas de /)
- Logging de toutes les actions

**API Endpoints**:
```
POST /execute   - Exécuter une action
GET  /health    - État du service
```

### 4. Module STT (Port 5003)

**Technologie**: Python, OpenAI Whisper

**Modèle**: Whisper Medium (multilingue)

**Pipeline Audio**:
```
Microphone → VAD → Chunking → Whisper → Post-processing → Texte
              ↓       ↓          ↓            ↓
          (Silero) (5s max)  (GPU/CPU)   (normalisation)
```

**Optimisations**:
- Voice Activity Detection pour éviter transcription inutile
- Chunking intelligent sur les silences
- Batch processing si plusieurs requêtes
- Cache des transcriptions récentes

**API Endpoints**:
```
POST /transcribe  - Transcrire un fichier audio
POST /stream      - Transcription en streaming (Phase 2)
GET  /health      - État du modèle
```

### 5. Module TTS (Port 5004)

**Technologie**: Python, Coqui TTS (ou macOS `say`)

**Voix**: Française naturelle (Thomas ou voix neuronale)

**Pipeline**:
```
Texte → Normalisation → Phonétisation → Synthèse → Audio
           ↓               ↓              ↓          ↓
     (nombres,        (IPA/SSML)      (neural)   (WAV/MP3)
      dates, etc.)
```

**Latence Cible**: <500ms pour une phrase courte

**API Endpoints**:
```
POST /synthesize  - Synthétiser du texte
GET  /voices      - Lister les voix disponibles
GET  /health      - État du service
```

### 6. Module d'Authentification (Port 5005)

**Technologie**: Python, SpeechBrain, Resemblyzer

**Méthodes**:
- **Reconnaissance vocale**: Embedding de la voix (256-dim)
- **Reconnaissance faciale**: FaceNet/dlib (128-dim)

**Processus d'Enregistrement**:
```
1. Capturer 5-10 échantillons vocaux
2. Générer embeddings moyens
3. Stocker signature chiffrée
4. Calculer seuil de confiance personnalisé
```

**Processus de Vérification**:
```
Audio → Embedding → Distance Cosine → Score → Accepté/Rejeté
                         ↓                ↓
                   vs. référence     (threshold)
```

**API Endpoints**:
```
POST /verify/voice  - Vérifier par la voix
POST /verify/face   - Vérifier par le visage
POST /enroll        - Enregistrer un utilisateur
GET  /health        - État du service
```

### 7. Connecteurs (Port 5006)

**Technologie**: Python, aiohttp, imaplib, MQTT

**Connecteurs Disponibles**:

#### Email (Phase 2)
```python
Protocoles: IMAP (lecture), SMTP (envoi)
Features:
- Filtrage intelligent (VIP, keywords)
- Résumé via LLM
- Suggestion de réponses
- Notifications push
```

#### Calendrier (Phase 2)
```python
APIs: Google Calendar, iCloud
Features:
- Lecture des événements
- Ajout/modification
- Rappels intelligents
```

#### IoT (Phase 2)
```python
Protocoles: MQTT, HTTP, Zigbee
Devices: Lumières, thermostats, prises
Features:
- Découverte automatique
- Groupement par pièce
- Scénarios automatisés
```

**API Endpoints**:
```
POST /email/query      - Consulter emails
POST /email/send       - Envoyer email
GET  /calendar/events  - Événements
POST /iot/control      - Contrôler device
GET  /health           - État des connecteurs
```

## Flux de Données Typiques

### Exemple 1: Commande Système Simple

```
1. User → CLI: "Crée un fichier test.txt"
2. CLI → Orchestrator POST /command
3. Orchestrator → Dispatcher.detect_intent() → "system_action"
4. Orchestrator → System Executor POST /execute
5. System Executor → create_file() → Success
6. System Executor → Orchestrator → Response
7. Orchestrator → CLI → "Fichier créé avec succès"
```

**Latence totale**: 50-100ms

### Exemple 2: Question au LLM

```
1. User → CLI: "Explique-moi le machine learning"
2. CLI → Orchestrator POST /command
3. Orchestrator → Dispatcher.detect_intent() → "question"
4. Orchestrator → ContextManager.format_history()
5. Orchestrator → LLM POST /generate (prompt + context)
6. LLM → Retrieval (si RAG activé)
7. LLM → Inference (llama.cpp)
8. LLM → Orchestrator → Response
9. Orchestrator → ContextManager.add_to_history()
10. Orchestrator → CLI → Réponse formatée
```

**Latence totale**: 2-5 secondes (selon longueur réponse)

### Exemple 3: Interaction Vocale Complète (Phase 2)

```
1. User parle → Microphone
2. STT détecte voix (VAD)
3. STT → Whisper → Transcription
4. STT → Orchestrator → Texte
5. [Flux normal comme Exemple 1 ou 2]
6. Orchestrator → TTS POST /synthesize
7. TTS → Synthèse audio
8. TTS → Haut-parleur → Réponse vocale
```

**Latence totale**: 4-7 secondes (bout en bout)

## Communication Inter-Services

### Protocole: REST HTTP/JSON

**Choix Justifié**:
- ✅ Simple à implémenter et débugger
- ✅ Compatible cross-language (C, Python)
- ✅ Outils de monitoring standards (curl, httpie)
- ✅ Pas de dépendances lourdes
- ❌ Légèrement plus lent que gRPC (~10ms overhead)

**Alternatives Futures**:
- gRPC pour services critiques en latence
- WebSockets pour streaming audio
- Message Queue (RabbitMQ) pour events asynchrones

### Format des Messages

**Requête Standard**:
```json
{
  "user_id": "string",
  "request_id": "uuid",
  "timestamp": "iso8601",
  "data": {
    // Payload spécifique au service
  }
}
```

**Réponse Standard**:
```json
{
  "success": boolean,
  "message": "string",
  "data": object,
  "error": "string?",
  "metadata": {
    "latency_ms": number,
    "service": "string"
  }
}
```

## Stockage et Persistance

### SQLite (Métadonnées)

**Schéma** (Phase 1):
```sql
-- Utilisateurs
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT,
  created_at TIMESTAMP,
  preferences JSON
);

-- Historique conversations
CREATE TABLE conversations (
  id INTEGER PRIMARY KEY,
  user_id TEXT,
  timestamp TIMESTAMP,
  user_input TEXT,
  assistant_response TEXT,
  metadata JSON
);

-- Logs d'actions
CREATE TABLE action_logs (
  id INTEGER PRIMARY KEY,
  timestamp TIMESTAMP,
  user_id TEXT,
  service TEXT,
  action TEXT,
  success BOOLEAN,
  details JSON
);
```

### FAISS (Base Vectorielle)

**Usage**:
- Stockage des embeddings de documents
- Recherche sémantique rapide (k-NN)
- Dimension: 768 (sentence-transformers)

**Index Type**: IVF + PQ (compression) pour >100k docs

## Sécurité

### Niveaux de Sécurité

1. **Réseau**: Services isolés sur réseau Docker interne
2. **Authentification**: Vérification vocale/faciale avant actions critiques
3. **Autorisation**: Whitelist d'actions par utilisateur
4. **Chiffrement**: Données sensibles AES-256 au repos
5. **Audit**: Logging de toutes les actions

### Actions Critiques Nécessitant 2FA

```python
CRITICAL_ACTIONS = [
    "delete_file",
    "execute_command",
    "send_email",
    "iot_unlock_door",
    # ...
]
```

## Scalabilité et Performance

### Optimisations Actuelles

- Connection pooling HTTP (aiohttp)
- Cache LLM pour questions fréquentes (LRU)
- Lazy loading des modèles lourds
- Quantization des modèles IA

### Bottlenecks Potentiels

1. **LLM Inference**: CPU/GPU bound
   - Solution: Queue de requêtes, batch processing
2. **Whisper Transcription**: Temps réel limite
   - Solution: Streaming VAD, modèle plus petit
3. **Mémoire RAM**: Modèles volumineux
   - Solution: Offloading layers, swap intelligent

## Monitoring et Observabilité

### Métriques Clés

```python
- Latence par service (p50, p95, p99)
- Taux d'erreur par endpoint
- Utilisation CPU/GPU/RAM
- Queue length (requêtes en attente)
- Token throughput (LLM)
```

### Outils (Phase future)

- Prometheus pour les métriques
- Grafana pour les dashboards
- Jaeger pour le tracing distribué

## Conclusion

Cette architecture offre:
- ✅ **Modularité**: Services indépendants
- ✅ **Performance**: Optimisations bas-niveau (C, C++)
- ✅ **Flexibilité**: Ajout facile de nouveaux services
- ✅ **Robustesse**: Isolation des pannes
- ✅ **Sécurité**: Authentification multi-niveaux
- ✅ **Évolutivité**: De local à distribué

La roadmap prévoit l'enrichissement progressif sans refonte majeure.
