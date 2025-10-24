# HOPPER - Installation et Configuration Antivirus

## 🚀 Installation

### 1. Prérequis macOS

```bash
# Installer ClamAV (moteur antivirus open-source)
brew install clamav

# Configurer ClamAV
sudo mkdir -p /usr/local/etc/clamav
sudo cp /usr/local/etc/clamav/freshclam.conf.sample /usr/local/etc/clamav/freshclam.conf
sudo cp /usr/local/etc/clamav/clamd.conf.sample /usr/local/etc/clamav/clamd.conf

# Éditer freshclam.conf et commenter la ligne "Example"
sudo sed -i '' 's/^Example/#Example/' /usr/local/etc/clamav/freshclam.conf

# Mettre à jour les définitions de virus
sudo freshclam

# Créer les répertoires HOPPER
sudo mkdir -p /var/hopper/quarantine
sudo chmod 755 /var/hopper
```

### 2. Installation des dépendances Python

```bash
# Activer l'environnement virtuel
cd /Users/jilani/Projet/HOPPER
source .venv/bin/activate

# Installer les dépendances
pip install fastapi uvicorn httpx pydantic loguru
```

## 🧪 Tests

### Test Rapide (EICAR)

```bash
# Lancer les tests complets
python test_antivirus.py
```

Ce test va:
1. ✅ Créer un fichier EICAR (test antivirus standard)
2. ✅ Scanner le fichier avec ClamAV + heuristique
3. ✅ Mettre le fichier en quarantaine
4. ✅ Lister les fichiers en quarantaine
5. ✅ Supprimer la menace (secure delete)
6. ✅ Afficher les statistiques

### Test Manuel

```bash
# 1. Démarrer le service antivirus
cd src/connectors/antivirus
python connector.py

# 2. Dans un autre terminal, tester l'API
curl http://localhost:5007/health

# 3. Scanner un fichier
curl -X POST http://localhost:5007/scan/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/tmp/eicar_test.txt"}'

# 4. État de la protection
curl http://localhost:5007/status
```

## 🎯 Utilisation via Langage Naturel

Une fois l'orchestrator lancé, vous pouvez utiliser:

```
Utilisateur: "Scanne mon système pour les virus"
→ HOPPER lance un scan complet

Utilisateur: "Y a-t-il des menaces sur mon Mac?"
→ HOPPER vérifie l'état de protection

Utilisateur: "Nettoie les virus détectés"
→ HOPPER demande confirmation puis supprime

Utilisateur: "Mets à jour l'antivirus"
→ HOPPER met à jour les définitions ClamAV
```

## 📊 Architecture

```
┌──────────────────────────────────────────┐
│  Utilisateur: "Scanne mon PC"            │
└───────────────┬──────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│  Orchestrator (Port 5050)                 │
│  • NLP Pattern Detection                  │
│  • system_integration.py                  │
└───────────────┬───────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│  AntivirusConnector (Port 5007)          │
│  • FastAPI Service                        │
│  • 15 Endpoints REST                      │
└───────────────┬───────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│  MacOSAntivirusAdapter                    │
│  • ClamAV Integration                     │
│  • Heuristic Scanner                      │
│  • Behavior Analyzer                      │
└───────────────┬───────────────────────────┘
                ↓
┌───────────────────────────────────────────┐
│  ClamAV + Custom Heuristics               │
│  • 10M+ Virus Signatures                  │
│  • Pattern Matching                       │
│  • Behavior Detection                     │
└───────────────────────────────────────────┘
```

## 🔒 Sécurité - 3 Couches

### 1. PermissionManager
Toute suppression = `CRITICAL_RISK`

### 2. ConfirmationEngine
L'utilisateur **DOIT** approuver avant suppression:
```python
confirmation = await confirmation_engine.request_confirmation(
    action="remove_virus",
    details={
        "threat_name": "Trojan.Generic",
        "file_path": "/tmp/malware.sh",
        "risk_level": "CRITICAL"
    },
    timeout=60
)

if confirmation.approved:
    await remove_threat()
```

### 3. AuditLogger
Traçabilité complète:
- Tous les scans
- Toutes les quarantaines
- Toutes les suppressions
- Horodatage + user_id

## 📁 Structure des Fichiers

```
src/connectors/antivirus/
├── __init__.py
├── connector.py              # Service FastAPI (Port 5007)
├── adapters/
│   ├── __init__.py
│   ├── base.py              # Interface AntivirusAdapter
│   ├── macos_adapter.py     # Implémentation macOS
│   ├── windows_adapter.py   # TODO: Windows Defender
│   ├── linux_adapter.py     # TODO: ClamAV + rkhunter
│   └── factory.py           # get_antivirus_adapter()
├── scanner/                 # TODO: Scanners avancés
├── quarantine/              # TODO: Gestion quarantaine
└── monitor/                 # TODO: Surveillance temps réel

src/orchestrator/tools/
└── system_integration.py    # Patterns NLP + exécution

docs/
└── ANTIVIRUS_ARCHITECTURE.md  # Documentation complète

test_antivirus.py            # Tests avec EICAR
```

## 🌐 Endpoints API

### Scan
- `POST /scan/file` - Scanner un fichier
- `POST /scan/directory` - Scanner un dossier
- `POST /scan/full` - Scan complet système
- `POST /scan/quick` - Scan rapide zones critiques

### Quarantaine
- `POST /quarantine` - Mettre en quarantaine
- `GET /quarantine/list` - Lister quarantaine
- `POST /quarantine/restore` - Restaurer un fichier

### Menaces
- `POST /threat/remove` - Supprimer (⚠️ confirmation requise)

### Status
- `GET /status` - État protection
- `GET /statistics` - Statistiques menaces
- `GET /history` - Historique scans

### Mise à jour
- `POST /update` - Mettre à jour définitions

### Monitoring (TODO)
- `POST /monitor/start` - Démarrer surveillance
- `POST /monitor/stop` - Arrêter surveillance
- `GET /monitor/status` - État monitoring

## 🎨 Patterns NLP Détectés

### Scan
- "scanne mon système"
- "recherche des virus"
- "y a-t-il des malwares?"
- "vérifie mon Mac"
- "analyse mon ordinateur"

### Quarantaine
- "mets en quarantaine [fichier]"
- "isole le virus"

### Suppression
- "supprime les virus"
- "élimine les menaces"
- "nettoie les malwares"

### Status
- "état de la protection"
- "suis-je protégé?"
- "antivirus actif?"

### Update
- "mets à jour l'antivirus"
- "actualise les définitions"

## 🔬 Méthodes de Détection

### 1. Signature-Based (ClamAV)
- Base de 10M+ signatures virales
- Mise à jour quotidienne via freshclam
- Détection rapide et fiable

### 2. Heuristic-Based (Custom)
Patterns suspects détectés:
- `rm -rf /` → Suppression système
- `curl | sh` → Exécution code distant
- `chmod +x` + scripts → Backdoor potentiel
- `/etc/passwd` → Accès fichiers sensibles
- EICAR test file → Standard test antivirus

### 3. Behavior-Based
- Permissions setuid/setgid suspectes
- Modifications système inhabituelles
- Activité réseau suspecte

### 4. Machine Learning (TODO - Phase 2)
- Classification ML sur features fichiers
- Détection zero-day
- Analyse comportementale avancée

## 📈 Performance

### Scan File
- Temps moyen: 0.1-0.5s par fichier
- Méthodes: signature + heuristic + behavior

### Quick Scan
- Zones: Downloads, Desktop, /tmp, /var/tmp
- Temps: 30-60s
- Fichiers: 200-500

### Full Scan
- Zones: /, /Users, /Applications, /Library
- Temps: 30-60 minutes
- Fichiers: 10,000-50,000

## 🛠️ Dépannage

### ClamAV non installé
```bash
brew install clamav
sudo freshclam
```

### Permissions insuffisantes
```bash
sudo mkdir -p /var/hopper/quarantine
sudo chmod 755 /var/hopper
```

### Service ne démarre pas
```bash
# Vérifier les logs
python src/connectors/antivirus/connector.py

# Vérifier le port
lsof -i :5007
```

## 🚀 Prochaines Étapes

### Phase 2 - Windows
- [ ] Implémenter WindowsAntivirusAdapter
- [ ] Intégration Windows Defender API
- [ ] PowerShell scripts pour scan

### Phase 3 - Linux
- [ ] Implémenter LinuxAntivirusAdapter
- [ ] ClamAV + rkhunter + chkrootkit
- [ ] Détection rootkits

### Phase 4 - Avancé
- [ ] Surveillance temps réel (watchdog)
- [ ] Machine Learning pour détection
- [ ] Sandboxing pour analyse
- [ ] Protection réseau (firewall)

## 📚 Ressources

- ClamAV: https://www.clamav.net/
- EICAR Test: https://www.eicar.org/download-anti-malware-testfile/
- Virus Definitions: https://database.clamav.net/

---

🛡️ **HOPPER protège maintenant votre système contre les menaces !**
