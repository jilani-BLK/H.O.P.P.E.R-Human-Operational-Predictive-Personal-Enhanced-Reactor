# HOPPER - Architecture Antivirus Complète

## 🎯 Vision

HOPPER devient un **gardien de sécurité proactif** qui :
- ✅ Surveille en temps réel les menaces
- ✅ Détecte les virus, malwares, ransomwares, trojans
- ✅ Protège contre les intrusions et fichiers malveillants
- ✅ Élimine les menaces avec l'accord de l'utilisateur
- ✅ Fonctionne sur macOS, Windows et Linux
- ✅ S'intègre avec le langage naturel

## 🏗️ Architecture Globale

```
┌─────────────────────────────────────────────────────────┐
│  Utilisateur: "Scanne mon système pour les virus"       │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  Orchestrator + NLP System Tools                         │
│  (Détection de patterns antivirus)                       │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  AntivirusConnector (FastAPI - Port 5007)               │
│  • Endpoints: /scan, /monitor, /quarantine, /remove     │
│  • Intégration sécurité 3 couches                       │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  AntivirusAdapter (Interface abstraite)                 │
│  • scan_file / scan_directory / full_scan               │
│  • detect_threats / analyze_behavior                    │
│  • quarantine_file / remove_threat                      │
│  • update_definitions / monitor_realtime                │
└──────────────────────┬───────────────────────────────────┘
                       ↓
       ┌───────────────┴───────────────┬─────────────────┐
       ↓                               ↓                 ↓
┌──────────────┐             ┌──────────────┐   ┌──────────────┐
│ MacOS        │             │ Windows      │   │ Linux        │
│ Antivirus    │             │ Antivirus    │   │ Antivirus    │
│              │             │              │   │              │
│ • ClamAV     │             │ • Defender   │   │ • ClamAV     │
│ • XProtect   │             │ • API        │   │ • rkhunter   │
│ • Heuristic  │             │ • PowerShell │   │ • chkrootkit │
└──────────────┘             └──────────────┘   └──────────────┘
```

## 🔒 Intégration Sécurité 3 Couches

### 1. PermissionManager
```python
# Toute suppression de virus = CRITICAL_RISK
risk_level = RiskLevel.CRITICAL_RISK

# Whitelist des actions antivirus
ALLOWED_ANTIVIRUS_ACTIONS = [
    "scan_file",
    "scan_directory", 
    "full_scan",
    "detect_threats",
    "quarantine_file"  # Pas de suppression directe
]
```

### 2. ConfirmationEngine
```python
# User doit TOUJOURS approuver la suppression
confirmation = await confirmation_engine.request_confirmation(
    action="remove_virus",
    details={
        "threat_name": "Trojan.MacOS.FakeAV",
        "file_path": "/tmp/suspicious.sh",
        "risk_level": "CRITICAL",
        "recommended_action": "DELETE"
    },
    timeout=60  # 60 secondes pour décider
)

if confirmation.approved:
    await remove_threat()
else:
    await quarantine_only()  # Juste isoler
```

### 3. AuditLogger
```python
# Traçabilité complète
await audit_logger.log(
    action="virus_removed",
    user_id=user_id,
    details={
        "threat": threat_info,
        "file": file_path,
        "scan_method": "signature_based",
        "user_approved": True,
        "timestamp": datetime.now()
    }
)
```

## 🦠 Méthodes de Détection

### 1. Signature-Based (Définitions)
```python
# Base de données de signatures virales
virus_signatures = {
    "EICAR-Test": "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR",
    "Trojan.Generic": "pattern_hex_abc123",
    "Ransomware.Locky": "pattern_hex_def456"
}

def scan_with_signatures(file_content: bytes) -> List[str]:
    """Scan contre base de signatures connues"""
    threats = []
    for virus_name, pattern in virus_signatures.items():
        if pattern in file_content:
            threats.append(virus_name)
    return threats
```

### 2. Behavior-Based (Heuristique)
```python
SUSPICIOUS_BEHAVIORS = [
    # Comportements suspects
    "modify_system_files",
    "disable_antivirus",
    "encrypt_user_files",
    "connect_to_c2_server",
    "escalate_privileges",
    "inject_code",
    "hide_process",
    "keylogging"
]

def analyze_behavior(process_info: dict) -> ThreatLevel:
    """Analyse comportementale temps réel"""
    suspicious_count = 0
    
    if process_info.get("system_file_modification"):
        suspicious_count += 3
    if process_info.get("network_connection_suspicious_ip"):
        suspicious_count += 2
    if process_info.get("rapid_file_encryption"):
        suspicious_count += 5  # RANSOMWARE!
        
    if suspicious_count >= 5:
        return ThreatLevel.CRITICAL
    elif suspicious_count >= 3:
        return ThreatLevel.HIGH
    else:
        return ThreatLevel.LOW
```

### 3. Machine Learning (Optionnel - Phase 2)
```python
# Modèle ML pour détecter patterns inconnus
# Entraîné sur dataset de malwares connus
model = load_ml_model("antivirus_classifier.pkl")

def ml_scan(file_features: np.array) -> float:
    """
    Retourne probabilité que le fichier soit malveillant
    0.0 = sûr, 1.0 = malware
    """
    return model.predict_proba([file_features])[0][1]
```

## 📦 Structure des Fichiers

```
src/connectors/antivirus/
├── __init__.py
├── connector.py              # AntivirusConnector (FastAPI service)
├── adapters/
│   ├── __init__.py
│   ├── base.py              # AntivirusAdapter (interface)
│   ├── macos_adapter.py     # macOS implementation
│   ├── windows_adapter.py   # Windows implementation (TODO)
│   ├── linux_adapter.py     # Linux implementation (TODO)
│   └── factory.py           # get_antivirus_adapter()
├── scanner/
│   ├── __init__.py
│   ├── signature_scanner.py  # Scan par signatures
│   ├── behavior_scanner.py   # Analyse comportementale
│   └── heuristic_scanner.py  # Détection heuristique
├── quarantine/
│   ├── __init__.py
│   └── manager.py           # Gestion zone de quarantaine
└── monitor/
    ├── __init__.py
    ├── realtime_monitor.py  # Surveillance temps réel
    └── file_watcher.py      # Watchdog sur fichiers

src/orchestrator/tools/
└── antivirus_integration.py  # Patterns NLP antivirus
```

## 🔍 Interface AntivirusAdapter

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum

class ThreatLevel(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    VIRUS = "virus"
    TROJAN = "trojan"
    RANSOMWARE = "ransomware"
    SPYWARE = "spyware"
    ADWARE = "adware"
    ROOTKIT = "rootkit"
    WORM = "worm"
    SUSPICIOUS = "suspicious"

class AntivirusAdapter(ABC):
    """Interface abstraite pour antivirus cross-platform"""
    
    @abstractmethod
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scanne un fichier unique
        
        Returns:
            {
                "clean": bool,
                "threats": [
                    {
                        "name": "Trojan.MacOS.Generic",
                        "type": ThreatType.TROJAN,
                        "level": ThreatLevel.HIGH,
                        "description": "...",
                        "action_recommended": "delete"
                    }
                ],
                "scan_time": 0.5,
                "method": "signature_based"
            }
        """
        pass
    
    @abstractmethod
    async def scan_directory(
        self, 
        directory_path: str,
        recursive: bool = True,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Scanne un répertoire
        
        Returns:
            {
                "files_scanned": 150,
                "threats_found": 2,
                "clean_files": 148,
                "infected_files": [
                    {
                        "path": "/path/to/virus.sh",
                        "threats": [...]
                    }
                ],
                "scan_time": 45.2
            }
        """
        pass
    
    @abstractmethod
    async def full_scan(self) -> Dict[str, Any]:
        """
        Scan complet du système
        - macOS: /, /Users, /Applications
        - Windows: C:\, Program Files, Users
        - Linux: /, /home, /opt
        """
        pass
    
    @abstractmethod
    async def quick_scan(self) -> Dict[str, Any]:
        """
        Scan rapide des zones critiques
        - Téléchargements
        - Temporaires
        - Applications récentes
        """
        pass
    
    @abstractmethod
    async def detect_threats(
        self,
        file_path: str,
        methods: List[str] = ["signature", "behavior", "heuristic"]
    ) -> List[Dict[str, Any]]:
        """
        Détection multi-méthodes
        
        methods:
            - "signature": Base de signatures
            - "behavior": Analyse comportementale
            - "heuristic": Détection heuristique
            - "ml": Machine learning (optionnel)
        """
        pass
    
    @abstractmethod
    async def quarantine_file(self, file_path: str) -> Dict[str, Any]:
        """
        Isole un fichier suspect dans zone de quarantaine
        - Déplace vers /var/hopper/quarantine/
        - Supprime permissions d'exécution
        - Log l'opération
        """
        pass
    
    @abstractmethod
    async def remove_threat(
        self,
        file_path: str,
        secure_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Supprime définitivement un fichier malveillant
        
        secure_delete:
            - True: Écrase avec données aléatoires (shred)
            - False: Suppression simple (rm)
        
        ⚠️ REQUIERT CONFIRMATION UTILISATEUR ⚠️
        """
        pass
    
    @abstractmethod
    async def restore_from_quarantine(self, file_id: str) -> Dict[str, Any]:
        """
        Restaure un fichier de la quarantaine
        (si faux positif détecté)
        """
        pass
    
    @abstractmethod
    async def update_definitions(self) -> Dict[str, Any]:
        """
        Met à jour les définitions de virus
        - ClamAV: freshclam
        - Windows: Update-MpSignature
        - Custom: télécharge signatures HOPPER
        """
        pass
    
    @abstractmethod
    async def get_protection_status(self) -> Dict[str, Any]:
        """
        État de la protection
        
        Returns:
            {
                "enabled": True,
                "realtime_protection": True,
                "last_scan": "2025-10-23T10:30:00",
                "last_update": "2025-10-23T08:00:00",
                "definitions_version": "2025.10.23",
                "threats_quarantined": 3,
                "threats_removed": 15
            }
        """
        pass
    
    @abstractmethod
    async def start_realtime_monitor(self) -> Dict[str, Any]:
        """
        Démarre la surveillance en temps réel
        - Watchdog sur fichiers modifiés
        - Analyse comportementale des processus
        - Détection intrusions réseau
        """
        pass
    
    @abstractmethod
    async def stop_realtime_monitor(self) -> Dict[str, Any]:
        """Arrête la surveillance temps réel"""
        pass
    
    @abstractmethod
    async def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Historique des scans effectués"""
        pass
```

## 🍎 Implémentation macOS

### ClamAV Integration
```python
# Installation: brew install clamav
# Update: freshclam
# Scan: clamscan -r /path/to/scan

class MacOSAntivirusAdapter(AntivirusAdapter):
    def __init__(self):
        self.clamav_installed = self._check_clamav()
        self.quarantine_dir = Path("/var/hopper/quarantine")
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        
    def _check_clamav(self) -> bool:
        """Vérifie si ClamAV est installé"""
        try:
            result = subprocess.run(
                ["which", "clamscan"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan avec ClamAV + heuristique custom"""
        threats = []
        
        # 1. ClamAV scan
        if self.clamav_installed:
            result = subprocess.run(
                ["clamscan", "--no-summary", file_path],
                capture_output=True,
                text=True
            )
            
            if "FOUND" in result.stdout:
                # Parse ClamAV output
                for line in result.stdout.split("\n"):
                    if "FOUND" in line:
                        virus_name = line.split(":")[1].replace("FOUND", "").strip()
                        threats.append({
                            "name": virus_name,
                            "type": self._classify_threat(virus_name),
                            "level": ThreatLevel.HIGH,
                            "method": "clamav_signature"
                        })
        
        # 2. Custom heuristic scan
        heuristic_threats = await self._heuristic_scan(file_path)
        threats.extend(heuristic_threats)
        
        # 3. Behavioral analysis (si exécutable)
        if self._is_executable(file_path):
            behavior_threats = await self._behavior_scan(file_path)
            threats.extend(behavior_threats)
        
        return {
            "clean": len(threats) == 0,
            "threats": threats,
            "scan_time": time.time() - start_time,
            "methods_used": ["clamav", "heuristic", "behavior"]
        }
    
    async def _heuristic_scan(self, file_path: str) -> List[Dict]:
        """Détection heuristique custom"""
        threats = []
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            # Patterns suspects
            if b"rm -rf /" in content:
                threats.append({
                    "name": "Suspicious.DeleteSystemFiles",
                    "type": ThreatType.SUSPICIOUS,
                    "level": ThreatLevel.HIGH,
                    "description": "Tentative de suppression système"
                })
            
            if b"curl" in content and b"| sh" in content:
                threats.append({
                    "name": "Suspicious.RemoteCodeExecution",
                    "type": ThreatType.SUSPICIOUS,
                    "level": ThreatLevel.CRITICAL,
                    "description": "Exécution code distant"
                })
            
            # EICAR test file
            if b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR" in content:
                threats.append({
                    "name": "EICAR-Test-File",
                    "type": ThreatType.VIRUS,
                    "level": ThreatLevel.HIGH,
                    "description": "Fichier de test EICAR"
                })
        
        except Exception as e:
            logger.error(f"Heuristic scan error: {e}")
        
        return threats
    
    async def quarantine_file(self, file_path: str) -> Dict[str, Any]:
        """Déplace vers quarantaine"""
        try:
            file_path = Path(file_path)
            quarantine_path = self.quarantine_dir / f"{uuid.uuid4()}_{file_path.name}"
            
            # Déplacer le fichier
            shutil.move(str(file_path), str(quarantine_path))
            
            # Supprimer permissions
            os.chmod(quarantine_path, 0o000)
            
            # Logger
            logger.warning(f"File quarantined: {file_path} -> {quarantine_path}")
            
            return {
                "success": True,
                "original_path": str(file_path),
                "quarantine_path": str(quarantine_path),
                "quarantine_id": quarantine_path.stem
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def remove_threat(
        self,
        file_path: str,
        secure_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Suppression sécurisée
        ⚠️ DOIT être appelé APRÈS confirmation utilisateur
        """
        try:
            file_path = Path(file_path)
            
            if secure_delete:
                # Secure delete avec shred (écrase 3 fois)
                subprocess.run(
                    ["shred", "-vfz", "-n", "3", str(file_path)],
                    check=True
                )
            else:
                # Suppression simple
                file_path.unlink()
            
            logger.critical(f"THREAT REMOVED: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "method": "secure_shred" if secure_delete else "simple_delete"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

## 🌐 Patterns NLP Antivirus

```python
# src/orchestrator/tools/antivirus_integration.py

ANTIVIRUS_PATTERNS = {
    "scan_system": [
        r"scann?e?\s+(?:mon\s+)?(?:système|ordinateur|pc|mac)",
        r"(?:recherch(?:e|er)|cherch(?:e|er))\s+(?:des?\s+)?virus",
        r"vérifi(?:e|er)\s+(?:si|les)\s+virus",
        r"analys(?:e|er)\s+(?:mon\s+)?système",
        r"détect(?:e|er)\s+(?:des?\s+)?malware"
    ],
    
    "remove_virus": [
        r"supprim(?:e|er)\s+(?:le|les)\s+virus",
        r"élimin(?:e|er)\s+(?:le|les)\s+(?:virus|malware|menace)",
        r"nettoy(?:e|er)\s+(?:le|les)\s+virus",
        r"détruit|effac(?:e|er)\s+(?:le|les)\s+virus"
    ],
    
    "quarantine_threat": [
        r"met(?:tre|s)?\s+en\s+quarantaine",
        r"isol(?:e|er)\s+(?:le|les)\s+(?:fichier|virus|menace)",
        r"quarantaine\s+(?:le|les)\s+(?:fichier|virus)"
    ],
    
    "check_protection": [
        r"(?:état|status)\s+(?:de\s+)?(?:la\s+)?protection",
        r"antivirus\s+(?:actif|activé|fonctionne)",
        r"suis-je\s+protégé",
        r"y\s+a-t-il\s+des\s+virus"
    ],
    
    "update_definitions": [
        r"met(?:tre|s)?\s+à\s+jour\s+(?:les\s+)?(?:définitions|signatures)",
        r"updat(?:e|er)\s+antivirus",
        r"actualise(?:r)?\s+(?:les\s+)?définitions"
    ],
    
    "realtime_monitor": [
        r"activ(?:e|er)\s+(?:la\s+)?surveillance",
        r"(?:démarre|lance)(?:r)?\s+(?:la\s+)?protection\s+temps\s+réel",
        r"monitoring\s+antivirus",
        r"surveillance\s+continue"
    ]
}
```

## ⚡ Flux de Suppression avec Confirmation

```python
async def handle_virus_removal_flow(threat_info: dict):
    """
    Flux complet de suppression avec confirmation utilisateur
    """
    
    # 1. Détection
    scan_result = await antivirus.scan_file(file_path)
    
    if not scan_result["clean"]:
        threats = scan_result["threats"]
        
        for threat in threats:
            # 2. Quarantaine automatique
            quarantine_result = await antivirus.quarantine_file(
                threat["file_path"]
            )
            
            # 3. Demande de confirmation utilisateur
            confirmation = await confirmation_engine.request_confirmation(
                action="remove_virus",
                details={
                    "threat_name": threat["name"],
                    "threat_type": threat["type"],
                    "threat_level": threat["level"],
                    "file_path": threat["file_path"],
                    "description": threat.get("description", ""),
                    "quarantine_id": quarantine_result["quarantine_id"],
                    "recommended_action": "DELETE",
                    "warning": "⚠️ Cette action est IRRÉVERSIBLE ⚠️"
                },
                timeout=60  # 60 secondes pour décider
            )
            
            # 4. Action selon décision
            if confirmation.approved:
                # SUPPRESSION APPROUVÉE
                remove_result = await antivirus.remove_threat(
                    quarantine_result["quarantine_path"],
                    secure_delete=True
                )
                
                # 5. Audit log
                await audit_logger.log(
                    action="virus_removed",
                    risk_level=RiskLevel.CRITICAL_RISK,
                    user_id=confirmation.user_id,
                    details={
                        "threat": threat,
                        "user_approved": True,
                        "removal_method": "secure_delete",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                logger.critical(
                    f"THREAT ELIMINATED: {threat['name']} "
                    f"from {threat['file_path']} (USER APPROVED)"
                )
                
            else:
                # SUPPRESSION REFUSÉE - reste en quarantaine
                logger.warning(
                    f"Threat kept in quarantine: {threat['name']} "
                    f"(USER DENIED removal)"
                )
                
                await audit_logger.log(
                    action="virus_quarantined_only",
                    details={
                        "threat": threat,
                        "user_approved": False,
                        "reason": "User denied removal"
                    }
                )
```

## 🚀 Prochaines Étapes

### Phase 1 (Maintenant) - macOS
1. ✅ Créer structure antivirus
2. ✅ Implémenter AntivirusAdapter interface
3. ✅ Implémenter MacOSAntivirusAdapter avec ClamAV
4. ✅ Créer AntivirusConnector service
5. ✅ Intégrer sécurité 3 couches
6. ✅ Ajouter patterns NLP
7. ✅ Tests avec EICAR

### Phase 2 - Windows
1. Implémenter WindowsAntivirusAdapter
2. Intégration Windows Defender API
3. PowerShell scripts pour scan
4. Tests cross-platform

### Phase 3 - Linux
1. Implémenter LinuxAntivirusAdapter
2. ClamAV + rkhunter + chkrootkit
3. Surveillance rootkits
4. Tests multi-distros

### Phase 4 - Avancé
1. Machine Learning pour détection
2. Analyse sandboxing
3. Protection réseau (firewall)
4. Détection zero-day

## 📊 Métriques et Monitoring

```python
class AntivirusMetrics:
    """Métriques de performance antivirus"""
    
    total_scans: int = 0
    files_scanned: int = 0
    threats_detected: int = 0
    threats_removed: int = 0
    threats_quarantined: int = 0
    false_positives: int = 0
    scan_time_avg: float = 0.0
    last_update: datetime = None
    definitions_version: str = "1.0.0"
```

## ✅ Avantages

1. **Sécurité Maximale**
   - Confirmation utilisateur obligatoire
   - Audit trail complet
   - Quarantaine avant suppression

2. **Multi-Détection**
   - Signatures (ClamAV)
   - Heuristique custom
   - Analyse comportementale
   - ML (Phase 2)

3. **Cross-Platform**
   - Adapter pattern
   - macOS / Windows / Linux
   - Un seul codebase

4. **Langage Naturel**
   - "Scanne mon PC"
   - "Y a-t-il des virus?"
   - "Nettoie les menaces"

5. **Temps Réel**
   - Surveillance continue
   - Détection proactive
   - Alertes instantanées

---

🛡️ **HOPPER devient un véritable gardien de sécurité !**
