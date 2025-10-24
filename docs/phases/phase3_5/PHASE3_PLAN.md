# 🚀 Phase 3 : Fonctionnalités Principales & Expérimentations

**Durée estimée** : Mois 5-6 (8 semaines)  
**Date de début** : 22 octobre 2025  
**Statut** : 🟢 EN COURS

---

## 🎯 Objectif Global

Transformer HOPPER en assistant vocal complet capable de :
- 🎤 Comprendre la voix (STT avec Whisper)
- 🔊 Répondre à l'oral (TTS avec Coqui/eSpeak)
- 👤 Identifier l'utilisateur (reconnaissance du locuteur)
- 📧 Gérer les emails (IMAP + synthèse LLM)
- 🔔 Notifier proactivement
- 🎭 Orchestrer plusieurs modules en synergie

---

## 📋 Roadmap Détaillée

### Semaine 1-2 : Reconnaissance Vocale (STT v1)

#### Objectifs
- ✅ Intégrer Whisper (modèle `base` ou `small`)
- ✅ Service Docker dédié avec API FastAPI
- ✅ Transcription audio en temps réel
- ✅ Mot-clé d'activation "Hopper" ou touche espace

#### Tâches
1. **Service STT amélioré** (`src/stt/`)
   - [x] Whisper déjà intégré (voir `src/stt/server.py`)
   - [ ] Ajouter détection de mot-clé (wake word)
   - [ ] Streaming audio en temps réel
   - [ ] Optimiser latence (<2s pour 10s d'audio)

2. **Intégration Orchestrateur**
   - [ ] Route `/command/voice` acceptant audio
   - [ ] Pipeline: Audio → STT → Dispatcher → LLM → Réponse
   - [ ] Gestion des erreurs (bruit, silence, etc.)

3. **Tests**
   - [ ] Test transcription précision >85%
   - [ ] Test latence <2s
   - [ ] Test détection wake word >90%

#### Critère de Réussite
> ✅ L'utilisateur dit "Hopper, quel temps fait-il ?" et reçoit une réponse textuelle

---

### Semaine 3 : Synthèse Vocale (TTS v1)

#### Objectifs
- ✅ Intégrer TTS (Coqui TTS déjà présent)
- ✅ Améliorer qualité vocale française
- ✅ Réponse audio automatique

#### Tâches
1. **Service TTS amélioré** (`src/tts/`)
   - [x] Coqui TTS déjà intégré
   - [ ] Optimiser voix française (modèle `tts_models/fr/mai/tacotron2-DDC`)
   - [ ] Cache des phrases courantes
   - [ ] Streaming audio pour réponses longues

2. **Intégration Orchestrateur**
   - [ ] Paramètre `voice_output: true` dans requêtes
   - [ ] Pipeline: Réponse LLM → TTS → Audio
   - [ ] Format audio: WAV 16kHz ou MP3 compressé

3. **Tests**
   - [ ] Test qualité vocale (intelligibilité)
   - [ ] Test latence <1s pour 50 mots
   - [ ] Test prononciation noms propres

#### Critère de Réussite
> ✅ Hopper répond oralement à une question posée à l'oral

---

### Semaine 4 : Identification Utilisateur (v1)

#### Objectifs
- 👤 Reconnaissance du locuteur
- 🔒 Sécurité basique (alerte si voix inconnue)
- 📊 Entraînement sur échantillons utilisateur

#### Tâches
1. **Service Auth amélioré** (`src/auth/`)
   - [ ] Intégrer Resemblyzer ou SpeechBrain
   - [ ] Entraînement sur 10+ échantillons vocaux
   - [ ] Calcul embedding + similarité cosinus
   - [ ] Seuil de confiance: >80% = utilisateur connu

2. **Gestion Utilisateurs**
   - [ ] Endpoint `/auth/enroll` pour enregistrement
   - [ ] Endpoint `/auth/verify` pour vérification
   - [ ] Base de données des empreintes vocales
   - [ ] Mode "invité" si voix inconnue

3. **Tests**
   - [ ] Test précision >90% utilisateur principal
   - [ ] Test rejet >85% voix inconnues
   - [ ] Test robustesse (bruit, distance micro)

#### Critère de Réussite
> ✅ Hopper identifie l'utilisateur et affiche un avertissement si voix inconnue

---

### Semaine 5 : Connecteur Email (v1)

#### Objectifs
- 📧 Accès IMAP à un compte email
- 📋 Liste des emails non lus
- 🤖 Synthèse intelligente via LLM

#### Tâches
1. **Service Connectors - Module Email** (`src/connectors/`)
   - [ ] Connexion IMAP (imaplib ou aioimaplib)
   - [ ] Récupération emails non lus (sujet, expéditeur, date)
   - [ ] Parsing HTML → texte pour le body
   - [ ] Cache pour éviter re-téléchargement

2. **Intégration LLM**
   - [ ] Commande `"emails nouveaux"` → liste emails
   - [ ] Commande `"résume mes emails"` → synthèse LLM
   - [ ] Commande `"lis le premier email"` → lecture complète
   - [ ] Prompt LLM: "Résume ces emails en 2 phrases max"

3. **Sécurité**
   - [ ] Credentials en variables d'environnement
   - [ ] OAuth2 (optionnel, si Gmail)
   - [ ] Chiffrement des mots de passe

4. **Tests**
   - [ ] Test connexion IMAP
   - [ ] Test récupération emails
   - [ ] Test synthèse LLM pertinente

#### Critère de Réussite
> ✅ Hopper dit "Vous avez 3 nouveaux emails, de Alice, Bob et support@..."

---

### Semaine 6 : Notifications Proactives

#### Objectifs
- 🔔 Alertes en temps réel (nouveaux emails)
- ⏰ Rappels calendrier (si disponible)
- 🔄 Système de polling intelligent

#### Tâches
1. **Background Worker** (`src/orchestrator/workers/`)
   - [ ] Worker asynchrone pour polling email (toutes les 2 min)
   - [ ] Détection nouveaux emails vs cache
   - [ ] File de messages pour notifications

2. **Système de Priorité**
   - [ ] Analyse importance via LLM (expéditeur, sujet, mots-clés)
   - [ ] Catégories: Urgent, Important, Normal, Spam
   - [ ] Règles personnalisables par utilisateur

3. **Notifications Vocales**
   - [ ] Interruption polie ("Excusez-moi, ...")
   - [ ] TTS automatique pour notifications urgentes
   - [ ] Mode "Ne pas déranger" configurable

4. **Tests**
   - [ ] Test détection nouveau email <30s
   - [ ] Test classification importance >80%
   - [ ] Test notification vocale

#### Critère de Réussite
> ✅ Hopper dit "Nouveau message de Alice: Réunion urgente demain 9h"

---

### Semaine 7 : Scénario Filé (Intégration Complète)

#### Scénario de Test Complet

**Contexte**: Utilisateur rentre chez lui à 18h

```
USER: "Hopper, qu'ai-je manqué aujourd'hui ?"

HOPPER: "Bienvenue Marc. Vous avez 2 nouveaux emails importants et 
         1 événement ce soir à 20h : Dîner chez Sophie."

USER: "Lis les emails"

HOPPER: "Premier email de Alice: Confirmation réunion projet lundi 10h.
         Deuxième email de RH: Rappel déclaration télétravail avant vendredi."

USER: "Réponds au second que c'est noté"

HOPPER: "Voici ma proposition: 'Bonjour, c'est noté, je ferai la 
         déclaration cette semaine. Cordialement.' Voulez-vous que 
         je l'envoie ?"

USER: "Oui, envoie"

HOPPER: "Email envoyé. Autre chose ?"
```

#### Modules Impliqués
1. 🎤 STT: Capture voix utilisateur
2. 🧠 LLM: Compréhension intention
3. 📧 Email: Récupération et analyse
4. 📅 Calendrier: Consultation événements
5. 🔊 TTS: Réponse vocale
6. 👤 Auth: Identification utilisateur
7. 🗄️ Context: Mémorisation conversation

#### Tests d'Intégration
- [ ] Test scénario complet bout-en-bout
- [ ] Test latence totale <10s
- [ ] Test gestion erreurs (pas de connexion, etc.)
- [ ] Test enchainement multi-tours
- [ ] Test mémorisation contexte

#### Critère de Réussite
> ✅ Le scénario complet fonctionne sans intervention manuelle

---

### Semaine 8 : Optimisations & Stabilisation

#### Objectifs Performance
- ⚡ Latence totale <5s (voix → voix)
- 💾 RAM <30 Go pour tous les services
- 🔄 Support 3+ utilisateurs simultanés
- 🎯 Précision >90% sur toutes les tâches

#### Tâches d'Optimisation

1. **STT (Whisper)**
   - [ ] Tester modèles: `tiny`, `base`, `small`
   - [ ] Quantization INT8 si possible
   - [ ] GPU Metal pour accélération
   - [ ] Target: <1s pour 5s d'audio

2. **TTS (Coqui)**
   - [ ] Cache vocal pour phrases fréquentes
   - [ ] Streaming pour réponses longues
   - [ ] Compression audio MP3 128kbps
   - [ ] Target: <800ms pour 30 mots

3. **LLM (Mistral-7B)**
   - [ ] Augmenter GPU layers: 10 → 35
   - [ ] Batch processing si multiple requêtes
   - [ ] Cache KV pour contexte
   - [ ] Target: <1.5s pour 100 tokens

4. **Email Connector**
   - [ ] Cache emails avec TTL 5 min
   - [ ] Connexion persistante IMAP IDLE
   - [ ] Parsing asynchrone
   - [ ] Target: <500ms récupération liste

5. **Orchestrateur**
   - [ ] Pool de connexions HTTP
   - [ ] Timeout adaptatifs
   - [ ] Retry logic avec backoff
   - [ ] Monitoring Prometheus

#### Tests de Charge
```bash
# Load testing avec Locust
locust -f tests/load_test.py --host http://localhost:5000

# Objectifs:
# - 3 utilisateurs simultanés, 95th percentile <5s
# - 10 req/s pendant 5 min sans erreur
# - RAM stable <30 Go
```

#### Critère de Réussite
> ✅ HOPPER répond en <5s avec RAM <30Go pour 3 utilisateurs simultanés

---

## 📊 Métriques de Succès Phase 3

| Fonctionnalité | Métrique | Objectif | Critique |
|----------------|----------|----------|----------|
| **STT** | Précision | >85% | ✅ |
| **STT** | Latence | <2s/10s audio | ✅ |
| **TTS** | Intelligibilité | >90% | ✅ |
| **TTS** | Latence | <1s/50 mots | ✅ |
| **Auth Voix** | Précision | >90% | ⚠️ Important |
| **Email** | Connexion | 100% | ✅ |
| **Email** | Synthèse | Pertinente | ✅ |
| **Notifications** | Délai | <30s | ✅ |
| **Scénario Complet** | Succès | 100% | ✅ |
| **RAM Totale** | Usage | <30 Go | ✅ |
| **Latence Totale** | Voix→Voix | <5s | ✅ |

---

## 🛠️ Stack Technique Phase 3

### Nouveaux Packages Python
```python
# STT amélioré
openai-whisper>=20231117
pyaudio>=0.2.14
webrtcvad>=2.0.10  # Détection voix

# Auth vocale
resemblyzer>=0.1.1.dev0
speechbrain>=0.5.16

# Email
aioimaplib>=1.0.1
email-validator>=2.1.0
beautifulsoup4>=4.12.0  # Parsing HTML emails

# Notifications
apscheduler>=3.10.4  # Scheduling
```

### Configuration Système
```bash
# Audio (macOS)
brew install portaudio
brew install ffmpeg

# IMAP (test avec Gmail)
# Activer "Applications moins sécurisées" ou App Password
```

---

## 📁 Structure de Fichiers Phase 3

```
HOPPER/
├── src/
│   ├── orchestrator/
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── email_worker.py      # NEW: Polling email
│   │   │   └── notification_worker.py # NEW: Gestion notifications
│   │   ├── services/
│   │   │   ├── voice_pipeline.py    # NEW: STT→LLM→TTS
│   │   │   └── email_service.py     # NEW: Logique email
│   ├── stt/
│   │   ├── whisper_engine.py        # AMÉLIORER: Optimisations
│   │   ├── wake_word.py             # NEW: Détection "Hopper"
│   │   └── audio_stream.py          # NEW: Capture micro
│   ├── tts/
│   │   ├── coqui_engine.py          # AMÉLIORER: Cache + streaming
│   │   └── voice_profiles.py        # NEW: Voix personnalisées
│   ├── auth/
│   │   ├── voice_auth.py            # NEW: Resemblyzer
│   │   └── user_db.py               # NEW: Empreintes vocales
│   ├── connectors/
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── imap_client.py       # NEW: Client IMAP
│   │   │   ├── email_parser.py      # NEW: Parsing emails
│   │   │   └── email_classifier.py  # NEW: Importance via LLM
├── tests/
│   ├── test_phase3_stt.py           # NEW: Tests STT
│   ├── test_phase3_tts.py           # NEW: Tests TTS
│   ├── test_phase3_auth.py          # NEW: Tests auth vocale
│   ├── test_phase3_email.py         # NEW: Tests email
│   ├── test_phase3_scenario.py      # NEW: Scénario complet
│   └── load_test.py                 # NEW: Tests de charge
├── config/
│   ├── email_config.yaml            # NEW: Config IMAP
│   └── notification_rules.yaml      # NEW: Règles notifications
└── data/
    ├── voice_profiles/              # NEW: Empreintes vocales
    ├── email_cache/                 # NEW: Cache emails
    └── audio_samples/               # NEW: Échantillons test
```

---

## 🚀 Plan de Déploiement Phase 3

### Jour 1 : Préparation
```bash
# Créer structure
mkdir -p src/orchestrator/workers
mkdir -p src/stt/{wake_word,audio_stream}
mkdir -p src/connectors/email
mkdir -p tests/phase3
mkdir -p data/{voice_profiles,email_cache,audio_samples}

# Installer dépendances
pip install openai-whisper resemblyzer aioimaplib apscheduler
```

### Jour 2-10 : STT + Wake Word
- Améliorer service STT
- Détection "Hopper"
- Tests transcription

### Jour 11-15 : TTS Optimisé
- Améliorer qualité voix française
- Cache + streaming
- Tests qualité

### Jour 16-22 : Auth Vocale
- Resemblyzer integration
- Entraînement modèle
- Tests précision

### Jour 23-35 : Email + Notifications
- Client IMAP
- Classification LLM
- Worker notifications
- Tests bout-en-bout

### Jour 36-42 : Scénario Filé
- Intégration complète
- Tests utilisateur réel
- Corrections bugs

### Jour 43-56 : Optimisations
- Profiling performance
- Optimisations ciblées
- Load testing
- Documentation

---

## 🎯 Checklist Phase 3

### Fonctionnalités
- [ ] STT avec Whisper opérationnel
- [ ] Wake word "Hopper" détecté
- [ ] TTS Coqui qualité production
- [ ] Auth vocale >90% précision
- [ ] Email IMAP connecté
- [ ] Synthèse emails via LLM
- [ ] Notifications proactives
- [ ] Scénario complet fonctionnel

### Performance
- [ ] Latence STT <2s
- [ ] Latence TTS <1s
- [ ] Latence totale <5s
- [ ] RAM <30 Go
- [ ] Support 3 utilisateurs

### Tests
- [ ] Tests unitaires >95% couverture
- [ ] Tests intégration passants
- [ ] Tests de charge validés
- [ ] Tests scénario utilisateur

### Documentation
- [ ] Guide utilisation vocal
- [ ] Guide configuration email
- [ ] Guide entraînement voix
- [ ] Troubleshooting

---

## 📅 Timeline Résumée

```
Semaine 1-2: STT + Wake Word       ████████░░░░░░░░░░░░
Semaine 3:   TTS Amélioré          ░░░░░░░░████░░░░░░░░
Semaine 4:   Auth Vocale           ░░░░░░░░░░░░████░░░░
Semaine 5:   Email Connector       ░░░░░░░░░░░░░░░░████
Semaine 6:   Notifications         ░░░░░░░░░░░░░░░░░░░░████
Semaine 7:   Scénario Filé         ░░░░░░░░░░░░░░░░░░░░░░░░████
Semaine 8:   Optimisations         ░░░░░░░░░░░░░░░░░░░░░░░░░░░░████
```

---

## 🔗 Dépendances

**Bloquants**:
- ✅ Phase 1 complète (Infrastructure)
- ✅ Phase 2 complète (LLM + RAG)

**Prérequis**:
- Micro fonctionnel
- Haut-parleurs fonctionnels
- Compte email de test
- GPU pour accélération (recommandé)

**Nice to have**:
- Calendrier (Google Calendar API)
- IoT (HomeAssistant)
- Multi-langues

---

## 📝 Notes de Développement

### Défis Anticipés
1. **Latence STT**: Whisper peut être lent
   - Solution: Modèle `base` + GPU + cache
   
2. **Qualité TTS française**: Accents, intonation
   - Solution: Tester plusieurs modèles Coqui
   
3. **Auth vocale robustesse**: Bruit, distance
   - Solution: Filtres audio + seuils adaptatifs
   
4. **IMAP Gmail**: Authentification complexe
   - Solution: App Password ou OAuth2
   
5. **RAM totale**: Whisper + Mistral-7B + Coqui
   - Solution: Quantization + GPU offloading

### Optimisations Futures (Phase 4)
- Wake word hardware (Porcupine)
- TTS neural streaming (Bark)
- Multi-utilisateurs simultanés
- Apprentissage continu (RLHF)
- Multi-modal (vision + audio)

---

**Date de création**: 22 octobre 2025  
**Prochaine révision**: Fin semaine 1 (STT complet)  
**Responsable**: Équipe HOPPER
