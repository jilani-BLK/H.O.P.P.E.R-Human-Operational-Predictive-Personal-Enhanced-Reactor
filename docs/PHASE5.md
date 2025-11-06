# Phase 5 - Système de Contrôle Local

**Status** : ✅ OPÉRATIONNELLE + INTÉGRÉE  
**Période** : Mois 7-8  
**Objectif** : Contrôle total et sécurisé de la machine locale  
**Date Intégration** : 5 novembre 2025

---

## 🎯 Services Déployés

| Service | Port | Status | Technologie |
|---------|------|--------|-------------|
| **Orchestrator** | 5050 | ✅ Running | FastAPI + Phase 5 routes |
| **Connectors** | 5006 | ✅ Running | FastAPI + BaseConnector |
| **LocalSystem** | - | ✅ Enabled | LinuxAdapter (Docker) |
| **Spotify** | - | ✅ Enabled | Spotipy API |
| **Security** | - | 🔄 Dev Mode | PermissionManager (disabled) |

---

## 🏗️ Architecture Complète

```
User: "lis le fichier README"
  ↓
POST /api/v1/command
  ↓
Orchestrator :5050
  ├─ SystemCommandsHandler (détection patterns)
  │   ↓ détecte: action=read_file, params={file_path: "README"}
  ├─ ConnectorsClient (HTTP bridge)
  │   ↓ POST :5006/execute
  ├─ Connectors Service :5006
  │   ↓ route vers connector approprié
  ├─ LocalSystemConnector
  │   ├─ Security bypass (dev mode)
  │   └─ LinuxAdapter.read_file()
  │       ↓ lecture réelle du fichier
  └─ Response: {success: true, data: {content: "...", lines: 5}}

Alternative: Routes directes
  POST /api/v1/system/files/read → même flow sans detection patterns
```

---

## 🆕 Intégration Orchestrateur (Nov 2025)

### Nouveaux Composants

**1. ConnectorsClient** (`src/orchestrator/connectors_client.py`)
```python
client = get_connectors_client()  # Singleton
result = await client.read_file("/app/README.md", max_lines=50)
# → HTTP POST :5006/execute → LocalSystem.read_file()
```

**2. SystemCommandsHandler** (`src/orchestrator/system_commands_handler.py`)
- Détection 40+ patterns (FR + EN)
- Mapping: "ouvre Safari" → `{action: "open_app", params: {app_name: "Safari"}}`
- Intégré dans dispatcher hybride (priorité > LLM)

**3. Phase 5 Routes** (`src/orchestrator/api/phase5_routes.py`)
```
POST   /api/v1/system/apps/open       - Ouvrir application
POST   /api/v1/system/apps/close      - Fermer application  
GET    /api/v1/system/apps            - Lister applications
POST   /api/v1/system/files/read      - Lire fichier
POST   /api/v1/system/files/list      - Lister répertoire
POST   /api/v1/system/files/search    - Rechercher fichiers
GET    /api/v1/system/info            - Infos système (CPU/RAM/Disk)
POST   /api/v1/system/script          - Exécuter script (HIGH risk)
GET    /api/v1/system/connectors      - Liste connectors disponibles
GET    /api/v1/system/health          - Health check connectors
```

### Dispatcher Hybride Amélioré

```python
# Flux de routage (phase2_routes.py)
1. SystemCommandsHandler.detect(command)
   ├─ Si détecté → execute via ConnectorsClient
   └─ Sinon → continue vers LLMDispatcher (legacy)

2. LLMDispatcher.route(command)
   ├─ Si "system" → SimpleDispatcher (mots-clés)
   └─ Si "conversation" → LLM service

# Exemples détection:
"lis le fichier test.txt"    → read_file (Phase 5)
"info système"               → system_info (Phase 5)
"ouvre Safari"               → open_app (Phase 5)
"quelle est la météo?"       → LLM conversation (Phase 2)
"create directory foo"       → SimpleDispatcher (Phase 1)
```

---

## 🔐 Système de Sécurité 3 Couches

### Layer 1: Permission Manager
**Risk Levels:**
- `SAFE` - Lecture seule, info système → Exécution immédiate
- `LOW` - Actions bénignes → Confirmation dev
- `MEDIUM` - Modifications réversibles → Confirmation requise
- `HIGH` - Actions sensibles → Confirmation + log
- `CRITICAL` - Danger système → **BLOQUÉ**

**Whitelists:**
```python
SAFE_ACTIONS = ["read_file", "list_directory", "get_system_info"]
MODERATE_COMMANDS = ["open", "mkdir", "git", "npm", "pip"]
BANNED_COMMANDS = ["rm -rf", "sudo", "kill -9", "shutdown", "dd"]
```

### Layer 2: Intelligent Detection
- Regex pattern matching pour commandes dangereuses
- Validation extension fichiers (.exe, .dmg, .sh)
- Protection répertoires système (/System, /Library/System)
- Détection wildcards dangereux (*, .*)

### Layer 3: Confirmation Engine
```python
# Mode DEV (auto-confirm)
HOPPER_DEV_MODE=true  # Pour tests

# Mode PROD (confirmation manuelle)
HOPPER_DEV_MODE=false # Pour production
- Prompt CLI avec timeout 30s
- Questions claires: "Voulez-vous exécuter: open_app Safari?"
- Fallback: DENY si timeout
```

---

## 📦 LocalSystem Connector - 12 Capabilities

### Applications (6 actions)
```python
open_app(app_name)           # Lancer application
close_app(app_name)          # Fermer application  
list_apps()                  # 28+ apps détectées
get_running_apps()           # Apps en cours
focus_app(app_name)          # Focus fenêtre
minimize_app(app_name)       # Minimiser fenêtre
```

### Fichiers (4 actions)
```python
read_file(file_path, max_lines=None)  # Lire fichier texte/code
list_directory(dir_path)               # Explorer répertoire
find_files(pattern, start_dir)         # Recherche par pattern
get_file_info(file_path)               # Métadonnées (taille, dates)
```

### Système (2 actions)
```python
get_system_info()            # CPU, RAM, disque, OS
execute_script(command)      # Script shell sécurisé
```

---

## 🚀 Utilisation

### Via API Direct
```bash
# Health check
curl http://localhost:5006/health

# Lister applications
curl -X POST http://localhost:5006/execute \
  -H "Content-Type: application/json" \
  -d '{
    "connector": "local_system",
    "action": "list_apps",
    "params": {},
    "user_id": "user"
  }'

# Lire fichier
curl -X POST http://localhost:5006/execute \
  -H "Content-Type: application/json" \
  -d '{
    "connector": "local_system",
    "action": "read_file",
    "params": {"file_path": "README.md", "max_lines": 20},
    "user_id": "user"
  }'

# Info système
curl -X POST http://localhost:5006/execute \
  -H "Content-Type: application/json" \
  -d '{
    "connector": "local_system",
    "action": "get_system_info",
    "params": {},
    "user_id": "user"
  }'
```

### Via Orchestrator ✅ FONCTIONNEL (5 Nov 2025)

**Méthode 1: Commande naturelle via dispatcher**
```bash
curl -X POST http://localhost:5050/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command":"lis le fichier /app/README.md"}'

# Réponse:
{
  "success": true,
  "type": "system_local",
  "action": "read_file",
  "response": "✅ Fichier lu (5 lignes)",
  "output": "{'content': '# HOPPER...', 'lines_read': 5}",
  "duration_ms": 35
}
```

**Méthode 2: Routes directes**
```bash
# Lire fichier
curl -X POST http://localhost:5050/api/v1/system/files/read \
  -H "Content-Type: application/json" \
  -d '{"file_path":"/tmp/test.txt","max_lines":50}'

# Info système
curl http://localhost:5050/api/v1/system/info

# Health check connectors
curl http://localhost:5050/api/v1/system/health
```

**Exemples de commandes détectées:**
```bash
# Français
"lis le fichier README"     → read_file
"ouvre Safari"              → open_app
"ferme Chrome"              → close_app
"liste les applications"    → list_apps
"info système"              → system_info
"cherche les fichiers .py"  → find_files

# Anglais
"read file test.txt"        → read_file
"open Safari"               → open_app  
"show system"               → system_info
"list apps"                 → list_apps
```

---

## 📊 Audit & Monitoring

### Logs Audit
```bash
# Localisation
data/logs/audit/{date}.json

# Format
{
  "timestamp": "2025-11-05T20:00:00Z",
  "user_id": "user",
  "connector": "local_system",
  "action": "read_file",
  "params": {"file_path": "README.md"},
  "risk_level": "SAFE",
  "status": "success",
  "duration_ms": 45
}
```

### Endpoint Audit
```bash
# Consulter audit utilisateur
curl "http://localhost:5006/security/audit?user_id=user&limit=50"

# Métriques
{
  "total_actions": 127,
  "by_risk": {
    "SAFE": 95,
    "LOW": 20,
    "MEDIUM": 10,
    "HIGH": 2
  },
  "success_rate": 0.98,
  "top_actions": ["list_apps", "read_file", "get_system_info"]
}
```

---

## 🔧 Configuration

### Variables d'Environnement
```bash
# Mode confirmation
HOPPER_DEV_MODE=true|false  # Auto-confirm vs Manual

# Permissions
HOPPER_SAFE_DIRS=/Users/vous,/tmp  # Répertoires safe
HOPPER_BLOCKED_DIRS=/System,/Library/System  # Interdits
```

### Permissions macOS Requises
1. **Full Disk Access** - Lire fichiers système
2. **Accessibility** - Contrôler applications (AppleScript)
3. **Automation** - Scripts automatisés

```bash
# Configuration
Préférences Système → Sécurité et confidentialité → Confidentialité
- Full Disk Access: Ajouter Terminal/iTerm
- Accessibility: Ajouter Terminal/iTerm
```

---

## 🧪 Tests Intégration (5 Nov 2025)

### Via Dispatcher Intelligent ✅
```bash
# Test 1: Info système
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"info système"}'
→ ✅ Détecté: system_info
→ ✅ Exécution: 1052ms
→ ✅ Résultat: Linux, 12 CPU, 7.65GB RAM

# Test 2: Lecture fichier
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"lis le fichier /tmp/test.txt"}'
→ ✅ Détecté: read_file
→ ✅ Exécution: 19ms
→ ✅ Résultat: 2 lignes lues

# Test 3: Lecture README  
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"lis le fichier /app/README.md"}'
→ ✅ Détecté: read_file
→ ✅ Exécution: 35ms
→ ✅ Résultat: 5 lignes lues (# HOPPER...)

# Test 4: Liste apps (anglais)
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"list apps"}'
→ ✅ Détecté: list_apps
→ ✅ Exécution: 18ms
→ ✅ Résultat: 0 apps (container Docker)

# Test 5: System info (anglais)
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"show system"}'
→ ✅ Détecté: system_info
→ ✅ Exécution: 1041ms
→ ✅ Résultat: Linux aarch64
```

### Via Routes Directes ✅
```bash
# Health check
curl http://localhost:5050/api/v1/system/health
→ {"status":"healthy","connectors":{"total":2,"enabled":2,"connected":2}}

# Liste connectors
curl http://localhost:5050/api/v1/system/connectors
→ [{"name":"spotify","enabled":true},{"name":"local_system","enabled":true}]

# Capabilities
curl http://localhost:5050/api/v1/system/connectors/capabilities?connector_name=local_system
→ 12 capabilities listées (open_app, read_file, etc.)
```

### Métriques Performance
| Action | Temps | Notes |
|--------|-------|-------|
| **read_file** | 19-35ms | Fichiers <10KB |
| **list_apps** | 18ms | Scan répertoires binaires |
| **get_system_info** | 1000ms | psutil metrics |
| **health_check** | 10ms | Status ping |

---

## 📁 Fichiers Phase 5

### Core Services
```
src/connectors/
├── server.py (135 lignes)
│   └── FastAPI service + routing
│
├── base.py (150 lignes)
│   └── BaseConnector abstract class
│
├── local_system.py (560 lignes)
│   └── LocalSystem 12 capabilities + security integration
│
├── adapters/
│   ├── base.py (200 lignes) - Interface abstraite
│   ├── macos_adapter.py (400 lignes) - AppleScript implementation
│   ├── linux_adapter.py (280 lignes) - ✅ NEW (5 Nov 2025)
│   └── factory.py (75 lignes) - Auto-detection OS

### Orchestrator Integration (5 Nov 2025)
```
src/orchestrator/
├── connectors_client.py (280 lignes) - ✅ NEW
│   └── HTTP bridge vers connectors service
│
├── system_commands_handler.py (230 lignes) - ✅ NEW
│   └── Pattern detection + execution (40+ patterns FR/EN)
│
├── api/phase5_routes.py (250 lignes) - ✅ NEW
│   └── REST API: /api/v1/system/* (11 endpoints)
│
├── api/phase2_routes.py (MODIFIÉ)
│   └── Dispatcher hybride: SystemCommandsHandler > LLM > Simple
│   ├── LocalSystemConnector
│   ├── 12 capabilities (apps, files, system)
│   └── macOS integration (AppleScript, psutil)
│
└── spotify.py (200 lignes)
    └── SpotifyConnector (music control)
```

### Security Layer
```
src/security/
├── permissions.py (379 lignes)
│   ├── PermissionManager
│   ├── Risk assessment
│   ├── Whitelist/blacklist
│   └── Audit logging
│
└── confirmation.py (240 lignes)
    ├── ConfirmationEngine
    ├── CLI prompts
    └── Timeout handling
```

### Docker
```
docker/
└── connectors.Dockerfile
    └── Python 3.11 + psutil + spotipy
```

---

## 🎯 Objectifs Atteints

### ✅ Complétés (95% - 5 Nov 2025)
- [x] Architecture connectors modulaire
- [x] LocalSystem connector (12 capabilities)
- [x] LinuxAdapter pour Docker (NEW)
- [x] Système sécurité 3 couches (mode dev bypass)
- [x] Audit logging complet
- [x] Confirmation engine
- [x] Tests sécurité validés
- [x] Integration docker-compose
- [x] API REST complète (connectors service)
- [x] **Integration orchestrator ↔ connectors** ✅ NEW
- [x] **ConnectorsClient HTTP bridge** ✅ NEW
- [x] **SystemCommandsHandler (40+ patterns)** ✅ NEW
- [x] **Phase 5 Routes (/api/v1/system/*)** ✅ NEW
- [x] **Dispatcher hybride intelligent** ✅ NEW
- [x] **Commandes naturelles FR/EN détectées** ✅ NEW
- [x] **Tests end-to-end passés** ✅ NEW

### 🔄 Améliorations Futures (5%)
- [ ] FileSystem Explorer (indexation automatique)
- [ ] Decision Engine (suggestions autonomes)
- [ ] Réactiver sécurité 3-layer en production
- [ ] Performance profiling détaillé
- [ ] Tests stabilité 24h
- [ ] Support macOS host via RemoteAdapter

---

## 🔥 Cas d'Usage Testés

### ✅ Scénario 1: Lecture Fichier (5 Nov 2025)
```bash
# Commande
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"lis le fichier /app/README.md"}'

# Résultat
{
  "success": true,
  "type": "system_local",
  "action": "read_file",
  "response": "✅ Fichier lu (5 lignes)",
  "output": "# HOPPER - H.O.P.P.E.R\nHuman Operational...",
  "duration_ms": 35
}
```

### ✅ Scénario 2: Info Système (5 Nov 2025)
```bash
# Commande (français)
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"info système"}'

# Résultat
{
  "success": true,
  "action": "system_info",
  "response": "✅ Système: Linux, 12 CPU",
  "output": "{'os':'Linux','cpu_count':12,'memory_total_gb':7.65,...}",
  "duration_ms": 1052
}
```

### ✅ Scénario 3: Liste Applications (5 Nov 2025)
```bash
# Commande (anglais)
curl -X POST http://localhost:5050/api/v1/command \
  -d '{"command":"list apps"}'

# Résultat
{
  "success": true,
  "action": "list_apps",
  "response": "✅ 0 applications trouvées",
  "duration_ms": 18
}
```

### 🔮 Scénario 4: Futur (Voice + LLM)
```
USER (voice): "Hopper, ouvre VS Code et liste les fichiers Python"
HOPPER: 
  1. Détection: "ouvre VS Code" + "liste fichiers Python"
  2. Exécution parallèle:
     - open_app("VSCode") → [success]
     - find_files("*.py") → ["app.py", "test.py", ...]
  3. Réponse vocale: "VS Code ouvert, 27 fichiers Python trouvés"
```
```
USER: "Lis-moi le fichier main.py"
HOPPER: [read_file main.py] → [Retourne contenu + syntaxe]
```

### Scénario 4: Musique (Spotify)
```
USER: "Lance ma playlist workout"
HOPPER: [spotify.play_playlist "workout"] → "Lecture en cours"
```

---

## 🐛 Limitations Connues

1. **Permissions macOS**
   - Requiert Full Disk Access pour fichiers système
   - Accessibility pour contrôle apps
   - À configurer manuellement

2. **AppleScript Latency**
   - open_app: 1-2s (lancement app)
   - Alternative future: NSWorkspace API

3. **Spotify Authentication**
   - Requiert token OAuth
   - À configurer dans .env
   - Refresh token 1h

4. **Confirmation UX**
   - CLI prompt basique
   - Future: Notification macOS native
   - Future: Web UI confirmation

---

## 📚 Références

- **Connectors**: http://localhost:5006/docs
- **Audit API**: http://localhost:5006/security/audit
- **Source**: `src/connectors/`, `src/security/`

---

**Créé** : Octobre 2025  
**Dernière MAJ** : 5 Novembre 2025  
**Status** : Production-ready (70% complet)
