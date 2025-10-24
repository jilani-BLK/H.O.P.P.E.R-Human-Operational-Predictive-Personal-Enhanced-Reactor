# 🌐 Architecture Cross-Platform pour HOPPER

**Vision**: HOPPER doit être une IA interconnectée, modulaire et compatible tous OS

---

## 🎯 Objectif

Rendre HOPPER **platform-agnostic** avec des adaptateurs spécifiques par OS :
- 🍎 macOS (AppleScript, Automator)
- 🪟 Windows (PowerShell, Win32 API)
- 🐧 Linux (D-Bus, xdotool, wmctrl)
- 🐳 Docker (API REST vers host)

---

## 🏗️ Architecture Proposée

### Couche 1: Interface Abstraite
```python
# src/connectors/adapters/base.py
class SystemAdapter(ABC):
    """Interface abstraite pour opérations système"""
    
    @abstractmethod
    async def open_application(self, app_name: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def close_application(self, app_name: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def list_applications(self) -> List[str]:
        pass
    
    @abstractmethod
    async def list_running_apps(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        pass
```

### Couche 2: Adaptateurs Spécifiques

#### macOS Adapter
```python
# src/connectors/adapters/macos_adapter.py
class MacOSAdapter(SystemAdapter):
    async def open_application(self, app_name: str):
        script = f'tell application "{app_name}" to activate'
        subprocess.run(["osascript", "-e", script])
    
    async def list_applications(self):
        # Lister /Applications/*.app
        return [app.stem for app in Path("/Applications").glob("*.app")]
```

#### Windows Adapter
```python
# src/connectors/adapters/windows_adapter.py
class WindowsAdapter(SystemAdapter):
    async def open_application(self, app_name: str):
        # Utiliser subprocess + Windows paths
        subprocess.Popen([app_name])
    
    async def list_applications(self):
        # Registry + Program Files
        import winreg
        # ... scan registry
```

#### Linux Adapter
```python
# src/connectors/adapters/linux_adapter.py
class LinuxAdapter(SystemAdapter):
    async def open_application(self, app_name: str):
        # .desktop files + xdg-open
        subprocess.run(["xdg-open", app_name])
    
    async def list_applications(self):
        # Parse .desktop files
        desktop_dirs = [
            "/usr/share/applications",
            "~/.local/share/applications"
        ]
        # ... parse .desktop
```

### Couche 3: Factory Pattern
```python
# src/connectors/adapters/factory.py
def get_system_adapter() -> SystemAdapter:
    """Détecte l'OS et retourne l'adaptateur approprié"""
    system = platform.system()
    
    if system == "Darwin":
        return MacOSAdapter()
    elif system == "Windows":
        return WindowsAdapter()
    elif system == "Linux":
        return LinuxAdapter()
    else:
        raise UnsupportedPlatformError(f"OS {system} non supporté")
```

### Couche 4: LocalSystemConnector Refactorisé
```python
# src/connectors/local_system.py
class LocalSystemConnector:
    def __init__(self):
        # Détection automatique de l'OS
        self.adapter = get_system_adapter()
    
    async def execute(self, action: str, params: Dict[str, Any]):
        if action == "open_app":
            return await self.adapter.open_application(params["app_name"])
        elif action == "list_apps":
            return await self.adapter.list_applications()
        # ...
```

---

## 🎨 Cas d'Usage

### Exemple 1: macOS
```python
# Détection automatique
connector = LocalSystemConnector()  # → MacOSAdapter

# Utilisation
await connector.execute("open_app", {"app_name": "Safari"})
# → osascript -e 'tell application "Safari" to activate'
```

### Exemple 2: Windows
```python
connector = LocalSystemConnector()  # → WindowsAdapter

await connector.execute("open_app", {"app_name": "notepad.exe"})
# → subprocess.Popen(["notepad.exe"])
```

### Exemple 3: Linux
```python
connector = LocalSystemConnector()  # → LinuxAdapter

await connector.execute("open_app", {"app_name": "firefox"})
# → xdg-open firefox
```

### Exemple 4: Docker → Host
```python
# Dans Docker, utiliser RemoteAdapter
class RemoteAdapter(SystemAdapter):
    async def open_application(self, app_name: str):
        # Appel REST vers agent sur host
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://host.docker.internal:9999/system/open_app",
                json={"app_name": app_name}
            )
        return response.json()
```

---

## 📋 Implémentation par Fonctionnalité

### Applications

| Fonctionnalité | macOS | Windows | Linux |
|----------------|-------|---------|-------|
| **Ouvrir app** | `osascript` | `subprocess.Popen` | `xdg-open` |
| **Fermer app** | `osascript quit` | `taskkill /IM` | `pkill` |
| **Lister apps** | `/Applications/*.app` | Registry | `.desktop` files |
| **Apps en cours** | `osascript -e 'tell application "System Events"'` | `tasklist` | `ps aux` |
| **Focus window** | AppleScript | Win32 API | `wmctrl` |

### Fichiers

| Fonctionnalité | macOS | Windows | Linux |
|----------------|-------|---------|-------|
| **Lire fichier** | `open()` | `open()` | `open()` |
| **Lister dossier** | `os.listdir()` | `os.listdir()` | `os.listdir()` |
| **Trouver fichiers** | `glob` / `find` | `glob` / `dir` | `glob` / `find` |
| **Ouvrir avec app** | `open -a` | `start` | `xdg-open` |

### Système

| Fonctionnalité | macOS | Windows | Linux |
|----------------|-------|---------|-------|
| **Info système** | `platform` + `psutil` | `platform` + `psutil` | `platform` + `psutil` |
| **Processus** | `psutil.process_iter()` | `psutil.process_iter()` | `psutil.process_iter()` |
| **Volume** | `osascript` | `pycaw` | `amixer` |
| **Luminosité** | `brightness` | `wmi` | `xrandr` |

---

## 🔧 Implémentation Étape par Étape

### Phase 1: Refactoring LocalSystem (URGENT)
1. ✅ Créer `src/connectors/adapters/base.py` (interface)
2. ✅ Créer `src/connectors/adapters/macos_adapter.py`
3. ✅ Créer `src/connectors/adapters/factory.py`
4. ✅ Refactoriser `LocalSystemConnector` pour utiliser adapter
5. ✅ Tests sur macOS

### Phase 2: Support Windows
1. ✅ Créer `windows_adapter.py`
2. ✅ Implémenter 12 méthodes
3. ✅ Tests sur Windows VM

### Phase 3: Support Linux
1. ✅ Créer `linux_adapter.py`
2. ✅ Implémenter avec xdg-open, wmctrl, etc.
3. ✅ Tests sur Ubuntu/Debian

### Phase 4: Docker Bridge
1. ✅ Créer `remote_adapter.py`
2. ✅ Créer agent host (REST API)
3. ✅ Communication Docker → Host

---

## 🐳 Solution Docker

### Architecture Docker Hybride

```
┌─────────────────────────────────┐
│      Docker Container           │
│  ┌──────────────────────────┐   │
│  │  HOPPER Services         │   │
│  │  - Orchestrator          │   │
│  │  - LLM                   │   │
│  │  - Connectors            │   │
│  │    → RemoteAdapter ───────────┼──┐
│  └──────────────────────────┘   │  │ HTTP REST
└─────────────────────────────────┘  │
                                     │
                                     ▼
              ┌──────────────────────────────────┐
              │     Host Machine (macOS)         │
              │  ┌────────────────────────────┐  │
              │  │  System Agent (Python)     │  │
              │  │  Port: 9999                │  │
              │  │                            │  │
              │  │  Endpoints:                │  │
              │  │  POST /system/open_app     │  │
              │  │  POST /system/close_app    │  │
              │  │  GET  /system/list_apps    │  │
              │  │  etc.                      │  │
              │  │                            │  │
              │  │  ✅ AppleScript native     │  │
              │  │  ✅ Full macOS access      │  │
              │  └────────────────────────────┘  │
              └──────────────────────────────────┘
```

### System Agent Code
```python
# system_agent.py (sur host macOS)
from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.post("/system/open_app")
async def open_app(app_name: str):
    script = f'tell application "{app_name}" to activate'
    result = subprocess.run(["osascript", "-e", script], 
                          capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "app_name": app_name
    }

# Lancer: uvicorn system_agent:app --host 0.0.0.0 --port 9999
```

### RemoteAdapter (dans Docker)
```python
class RemoteAdapter(SystemAdapter):
    def __init__(self):
        self.base_url = os.getenv("SYSTEM_AGENT_URL", "http://host.docker.internal:9999")
    
    async def open_application(self, app_name: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/system/open_app",
                json={"app_name": app_name},
                timeout=10.0
            )
            return response.json()
```

---

## 📊 Comparaison Solutions

| Solution | Avantages | Inconvénients | Recommandé |
|----------|-----------|---------------|------------|
| **Dev Local (sans Docker)** | ✅ Accès direct macOS<br>✅ Pas de complexité<br>✅ Performance max | ❌ Pas portable<br>❌ Dépend de l'environnement | ✅ **OUI pour dev** |
| **Docker + System Agent** | ✅ Services portables<br>✅ Isolation<br>✅ Accès macOS via API | ❌ Setup complexe<br>❌ Latence réseau<br>❌ Deux processus | 🟡 Pour déploiement |
| **Adaptateurs Multi-OS** | ✅ Vraiment portable<br>✅ Un seul code<br>✅ Pas de Docker | ❌ Implémentation longue<br>❌ Tests sur 3 OS | ✅ **OUI pour prod** |

---

## 🎯 Recommandations Finales

### Pour Développement (maintenant)
```bash
# Sans Docker, avec adapter macOS
python src/connectors/server.py  # Port 5006
python src/orchestrator/main.py  # Port 5050

# HOPPER utilise automatiquement MacOSAdapter
```

### Pour Production (futur)
```bash
# Option A: Docker + System Agent (si un seul OS)
docker-compose up
./system_agent.py  # Sur host

# Option B: Build natif par OS (si multi-OS)
# Détection automatique de l'adaptateur
```

### Priorités
1. **URGENT**: Refactoriser LocalSystem avec pattern Adapter ✅
2. **COURT TERME**: Implémenter MacOSAdapter complet ✅
3. **MOYEN TERME**: WindowsAdapter + LinuxAdapter
4. **LONG TERME**: RemoteAdapter pour Docker

---

## 🚀 Plan d'Action Immédiat

```bash
# 1. Créer structure adapters
mkdir -p src/connectors/adapters
touch src/connectors/adapters/__init__.py
touch src/connectors/adapters/base.py
touch src/connectors/adapters/macos_adapter.py
touch src/connectors/adapters/factory.py

# 2. Implémenter code (voir ci-dessus)

# 3. Refactoriser LocalSystemConnector

# 4. Tester
python test_local_system.py
```

---

**Conclusion**: HOPPER sera **vraiment modulaire et cross-platform** avec cette architecture. Le code actuel ne change que dans `LocalSystemConnector`, tout le reste reste identique (Orchestrator, System Tools, etc.).

**Bénéfice majeur**: Un seul codebase, compatible macOS/Windows/Linux/Docker ! 🎉
