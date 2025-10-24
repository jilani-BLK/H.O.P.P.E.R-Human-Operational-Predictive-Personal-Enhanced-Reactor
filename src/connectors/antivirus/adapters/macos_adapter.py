"""
HOPPER - macOS Antivirus Adapter
Implémentation antivirus pour macOS utilisant ClamAV + détection heuristique custom
"""

import os
import shutil
import subprocess
import uuid
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .base import (
    AntivirusAdapter,
    ThreatLevel,
    ThreatType,
    ScanType
)

logger = logging.getLogger(__name__)


class MacOSAntivirusAdapter(AntivirusAdapter):
    """
    Implémentation antivirus pour macOS.
    
    Utilise:
    - ClamAV pour scan par signatures
    - Détection heuristique custom
    - Analyse comportementale basique
    - XProtect intégration (optionnel)
    """
    
    def __init__(self):
        """Initialise l'adapter macOS"""
        self.quarantine_dir = Path("/var/hopper/quarantine")
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        self.scan_history_file = Path("/var/hopper/scan_history.json")
        self.scan_history_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.quarantine_index_file = Path("/var/hopper/quarantine_index.json")
        
        self.clamav_installed = self._check_clamav()
        self.monitor_process = None
        
        # Statistiques
        self.stats = {
            "total_threats_detected": 0,
            "threats_quarantined": 0,
            "threats_removed": 0,
            "total_scans": 0
        }
        
        self._load_stats()
        
        logger.info(f"MacOSAntivirusAdapter initialized (ClamAV: {self.clamav_installed})")
    
    def _check_clamav(self) -> bool:
        """Vérifie si ClamAV est installé"""
        try:
            result = subprocess.run(
                ["which", "clamscan"],
                capture_output=True,
                text=True,
                timeout=5
            )
            installed = result.returncode == 0
            
            if not installed:
                logger.warning(
                    "ClamAV not installed. Install with: brew install clamav"
                )
            
            return installed
        except Exception as e:
            logger.error(f"Error checking ClamAV: {e}")
            return False
    
    def _load_stats(self):
        """Charge les statistiques depuis le disque"""
        stats_file = Path("/var/hopper/antivirus_stats.json")
        try:
            if stats_file.exists():
                with open(stats_file, "r") as f:
                    self.stats = json.load(f)
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
    
    def _save_stats(self):
        """Sauvegarde les statistiques sur le disque"""
        stats_file = Path("/var/hopper/antivirus_stats.json")
        try:
            with open(stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scanne un fichier unique"""
        start_time = time.time()
        threats = []
        methods_used = []
        
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            # 1. ClamAV scan
            if self.clamav_installed:
                clamav_threats = await self._clamav_scan(str(file_path_obj))
                threats.extend(clamav_threats)
                methods_used.append("signature")
            
            # 2. Heuristic scan
            heuristic_threats = await self._heuristic_scan(str(file_path_obj))
            threats.extend(heuristic_threats)
            methods_used.append("heuristic")
            
            # 3. Behavioral analysis (si exécutable)
            if self._is_executable(str(file_path_obj)):
                behavior_threats = await self._behavior_scan(str(file_path_obj))
                threats.extend(behavior_threats)
                methods_used.append("behavior")
            
            scan_time = time.time() - start_time
            
            result = {
                "success": True,
                "clean": len(threats) == 0,
                "file_path": str(file_path_obj),
                "threats": threats,
                "scan_time": scan_time,
                "methods_used": methods_used,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update stats
            self.stats["total_scans"] += 1
            if threats:
                self.stats["total_threats_detected"] += len(threats)
            self._save_stats()
            
            # Save scan history
            await self._save_scan_history(result, ScanType.FILE)
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _clamav_scan(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan avec ClamAV"""
        threats = []
        
        try:
            result = subprocess.run(
                ["clamscan", "--no-summary", file_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse output
            if "FOUND" in result.stdout:
                for line in result.stdout.split("\n"):
                    if "FOUND" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            virus_name = parts[1].replace("FOUND", "").strip()
                            
                            threats.append({
                                "name": virus_name,
                                "type": self._classify_threat(virus_name).value,
                                "level": ThreatLevel.HIGH.value,
                                "confidence": 0.95,
                                "method": "clamav_signature",
                                "description": f"ClamAV detected: {virus_name}",
                                "action_recommended": "quarantine"
                            })
        
        except subprocess.TimeoutExpired:
            logger.warning(f"ClamAV scan timeout for {file_path}")
        except Exception as e:
            logger.error(f"ClamAV scan error: {e}")
        
        return threats
    
    async def _heuristic_scan(self, file_path: str) -> List[Dict[str, Any]]:
        """Détection heuristique custom"""
        threats = []
        
        try:
            with open(file_path, "rb") as f:
                content = f.read(1024 * 1024)  # Read first 1MB
            
            # EICAR test file
            if b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR" in content:
                threats.append({
                    "name": "EICAR-Test-File",
                    "type": ThreatType.VIRUS.value,
                    "level": ThreatLevel.HIGH.value,
                    "confidence": 1.0,
                    "method": "signature_match",
                    "description": "EICAR antivirus test file",
                    "action_recommended": "quarantine"
                })
            
            # Suspicious commands
            dangerous_patterns = [
                (b"rm -rf /", "Suspicious.DeleteSystemFiles", 
                 "Tentative de suppression système complète"),
                (b"curl", b"| sh", "Suspicious.RemoteCodeExecution",
                 "Exécution de code distant"),
                (b"wget", b"| bash", "Suspicious.RemoteCodeExecution",
                 "Téléchargement et exécution de script"),
                (b"chmod +x", "Suspicious.PermissionChange",
                 "Modification permissions exécution"),
                (b"/etc/passwd", "Suspicious.SystemFileAccess",
                 "Accès fichier système sensible"),
                (b"sudo", b"rm", "Suspicious.ElevatedDeletion",
                 "Suppression avec privilèges élevés")
            ]
            
            for pattern_data in dangerous_patterns:
                if len(pattern_data) == 4:
                    pattern1, pattern2, name, desc = pattern_data
                    if pattern1 in content and pattern2 in content:
                        threats.append({
                            "name": name,
                            "type": ThreatType.SUSPICIOUS.value,
                            "level": ThreatLevel.HIGH.value,
                            "confidence": 0.75,
                            "method": "heuristic",
                            "description": desc,
                            "action_recommended": "quarantine"
                        })
                else:
                    pattern, name, desc = pattern_data
                    if pattern in content:
                        threats.append({
                            "name": name,
                            "type": ThreatType.SUSPICIOUS.value,
                            "level": ThreatLevel.MEDIUM.value,
                            "confidence": 0.60,
                            "method": "heuristic",
                            "description": desc,
                            "action_recommended": "review"
                        })
        
        except Exception as e:
            logger.error(f"Heuristic scan error: {e}")
        
        return threats
    
    async def _behavior_scan(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyse comportementale basique"""
        threats = []
        
        try:
            # Check file permissions
            stat_info = os.stat(file_path)
            
            # Exécutable avec setuid/setgid = suspect
            if stat_info.st_mode & 0o4000 or stat_info.st_mode & 0o2000:
                threats.append({
                    "name": "Suspicious.SetuidBinary",
                    "type": ThreatType.SUSPICIOUS.value,
                    "level": ThreatLevel.MEDIUM.value,
                    "confidence": 0.50,
                    "method": "behavior",
                    "description": "Exécutable avec setuid/setgid",
                    "action_recommended": "review"
                })
        
        except Exception as e:
            logger.error(f"Behavior scan error: {e}")
        
        return threats
    
    def _is_executable(self, file_path: str) -> bool:
        """Vérifie si un fichier est exécutable"""
        try:
            return os.access(file_path, os.X_OK)
        except:
            return False
    
    def _classify_threat(self, virus_name: str) -> ThreatType:
        """Classifie un type de menace selon son nom"""
        name_lower = virus_name.lower()
        
        if "trojan" in name_lower or "troj" in name_lower:
            return ThreatType.TROJAN
        elif "ransom" in name_lower:
            return ThreatType.RANSOMWARE
        elif "spy" in name_lower:
            return ThreatType.SPYWARE
        elif "adware" in name_lower or "adload" in name_lower:
            return ThreatType.ADWARE
        elif "rootkit" in name_lower:
            return ThreatType.ROOTKIT
        elif "worm" in name_lower:
            return ThreatType.WORM
        else:
            return ThreatType.VIRUS
    
    async def scan_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
        max_depth: int = -1
    ) -> Dict[str, Any]:
        """Scanne un répertoire"""
        start_time = time.time()
        
        try:
            directory_path_obj = Path(directory_path)
            
            if not directory_path_obj.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory_path}"
                }
            
            files_scanned = 0
            threats_found = 0
            infected_files = []
            
            # Collect files to scan
            if recursive:
                files = list(directory_path_obj.rglob("*"))
            else:
                files = list(directory_path_obj.glob("*"))
            
            files = [f for f in files if f.is_file()]
            
            # Filter by extensions
            if extensions:
                files = [f for f in files if f.suffix in extensions]
            
            # Scan each file
            for file_path in files:
                scan_result = await self.scan_file(str(file_path))
                files_scanned += 1
                
                if not scan_result.get("clean", True):
                    threats_found += len(scan_result.get("threats", []))
                    infected_files.append({
                        "path": str(file_path),
                        "threats": scan_result.get("threats", [])
                    })
            
            scan_time = time.time() - start_time
            
            result = {
                "success": True,
                "directory": str(directory_path),
                "files_scanned": files_scanned,
                "threats_found": threats_found,
                "clean_files": files_scanned - len(infected_files),
                "infected_files": infected_files,
                "scan_time": scan_time,
                "timestamp": datetime.now().isoformat()
            }
            
            await self._save_scan_history(result, ScanType.DIRECTORY)
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "directory": str(directory_path),
                "timestamp": datetime.now().isoformat()
            }
    
    async def full_scan(self) -> Dict[str, Any]:
        """Scan complet macOS"""
        start_time = time.time()
        
        # Zones critiques macOS
        critical_paths = [
            "/Users",
            "/Applications",
            "/Library",
            "/tmp",
            "/var/tmp"
        ]
        
        total_files = 0
        total_threats = 0
        infected_files = []
        
        for path in critical_paths:
            if Path(path).exists():
                logger.info(f"Scanning {path}...")
                result = await self.scan_directory(path, recursive=True)
                
                if result.get("success"):
                    total_files += result.get("files_scanned", 0)
                    total_threats += result.get("threats_found", 0)
                    infected_files.extend(result.get("infected_files", []))
        
        scan_time = time.time() - start_time
        
        result = {
            "success": True,
            "scan_type": ScanType.FULL.value,
            "total_files_scanned": total_files,
            "threats_found": total_threats,
            "clean_files": total_files - len(infected_files),
            "infected_files": infected_files,
            "scan_time": scan_time,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._save_scan_history(result, ScanType.FULL)
        
        return result
    
    async def quick_scan(self) -> Dict[str, Any]:
        """Scan rapide des zones critiques"""
        start_time = time.time()
        
        # Zones rapides
        quick_paths = [
            str(Path.home() / "Downloads"),
            "/tmp",
            "/var/tmp",
            str(Path.home() / "Desktop")
        ]
        
        total_files = 0
        total_threats = 0
        infected_files = []
        
        for path in quick_paths:
            if Path(path).exists():
                result = await self.scan_directory(path, recursive=False)
                
                if result.get("success"):
                    total_files += result.get("files_scanned", 0)
                    total_threats += result.get("threats_found", 0)
                    infected_files.extend(result.get("infected_files", []))
        
        scan_time = time.time() - start_time
        
        result = {
            "success": True,
            "scan_type": ScanType.QUICK.value,
            "files_scanned": total_files,
            "threats_found": total_threats,
            "infected_files": infected_files,
            "scan_time": scan_time,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._save_scan_history(result, ScanType.QUICK)
        
        return result
    
    async def detect_threats(
        self,
        file_path: str,
        methods: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Détection multi-méthodes"""
        if methods is None:
            methods = ["signature", "heuristic"]
        
        all_threats = []
        
        if "signature" in methods and self.clamav_installed:
            threats = await self._clamav_scan(file_path)
            all_threats.extend(threats)
        
        if "heuristic" in methods:
            threats = await self._heuristic_scan(file_path)
            all_threats.extend(threats)
        
        if "behavior" in methods:
            threats = await self._behavior_scan(file_path)
            all_threats.extend(threats)
        
        return all_threats
    
    async def quarantine_file(self, file_path: str, reason: str = "") -> Dict[str, Any]:
        """Met un fichier en quarantaine"""
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            # Générer ID unique
            quarantine_id = str(uuid.uuid4())
            quarantine_filename = f"{quarantine_id}_{file_path_obj.name}"
            quarantine_path = self.quarantine_dir / quarantine_filename
            
            # Déplacer le fichier
            shutil.move(str(file_path_obj), str(quarantine_path))
            
            # Supprimer permissions
            os.chmod(quarantine_path, 0o000)
            
            # Enregistrer dans l'index
            await self._add_to_quarantine_index({
                "quarantine_id": quarantine_id,
                "original_path": str(file_path_obj),
                "quarantine_path": str(quarantine_path),
                "quarantine_date": datetime.now().isoformat(),
                "reason": reason
            })
            
            # Stats
            self.stats["threats_quarantined"] += 1
            self._save_stats()
            
            logger.warning(f"File quarantined: {file_path} -> {quarantine_path}")
            
            return {
                "success": True,
                "original_path": str(file_path),
                "quarantine_path": str(quarantine_path),
                "quarantine_id": quarantine_id,
                "timestamp": datetime.now().isoformat(),
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error quarantining file: {e}")
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
        Supprime un fichier malveillant
        ⚠️ IRRÉVERSIBLE - Confirmation utilisateur REQUISE
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            if secure_delete:
                # Secure delete avec shred
                try:
                    subprocess.run(
                        ["shred", "-vfz", "-n", "3", str(file_path_obj)],
                        check=True,
                        capture_output=True,
                        timeout=60
                    )
                    method = "secure_shred"
                    passes = 3
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback: overwrite puis delete
                    with open(file_path_obj, "wb") as f:
                        f.write(os.urandom(file_path_obj.stat().st_size))
                    file_path_obj.unlink()
                    method = "overwrite_delete"
                    passes = 1
            else:
                # Simple deletion
                file_path_obj.unlink()
                method = "simple_delete"
                passes = 0
            
            # Stats
            self.stats["threats_removed"] += 1
            self._save_stats()
            
            logger.critical(f"THREAT REMOVED: {file_path} (method: {method})")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "method": method,
                "passes": passes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error removing threat: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def restore_from_quarantine(self, quarantine_id: str) -> Dict[str, Any]:
        """Restaure un fichier de la quarantaine"""
        try:
            index = await self._load_quarantine_index()
            
            entry = None
            for item in index:
                if item.get("quarantine_id") == quarantine_id:
                    entry = item
                    break
            
            if not entry:
                return {
                    "success": False,
                    "error": f"Quarantine ID not found: {quarantine_id}"
                }
            
            quarantine_path = Path(entry["quarantine_path"])
            original_path = Path(entry["original_path"])
            
            if not quarantine_path.exists():
                return {
                    "success": False,
                    "error": f"Quarantine file not found: {quarantine_path}"
                }
            
            # Restaurer permissions
            os.chmod(quarantine_path, 0o644)
            
            # Déplacer vers l'emplacement original
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(quarantine_path), str(original_path))
            
            # Retirer de l'index
            index.remove(entry)
            await self._save_quarantine_index(index)
            
            logger.info(f"File restored from quarantine: {quarantine_id}")
            
            return {
                "success": True,
                "quarantine_id": quarantine_id,
                "original_path": str(original_path),
                "restored": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error restoring from quarantine: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_quarantine(self) -> List[Dict[str, Any]]:
        """Liste les fichiers en quarantaine"""
        try:
            return await self._load_quarantine_index()
        except Exception as e:
            logger.error(f"Error listing quarantine: {e}")
            return []
    
    async def update_definitions(self) -> Dict[str, Any]:
        """Met à jour les définitions ClamAV"""
        if not self.clamav_installed:
            return {
                "success": False,
                "error": "ClamAV not installed"
            }
        
        try:
            start_time = time.time()
            
            # Execute freshclam
            result = subprocess.run(
                ["freshclam"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            update_time = time.time() - start_time
            
            success = result.returncode == 0
            
            return {
                "success": success,
                "update_time": update_time,
                "timestamp": datetime.now().isoformat(),
                "output": result.stdout if success else result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Update timeout (>5 minutes)"
            }
        except Exception as e:
            logger.error(f"Error updating definitions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_protection_status(self) -> Dict[str, Any]:
        """État de la protection"""
        try:
            # Load scan history
            history = await self._load_scan_history()
            last_scan = history[0] if history else None
            
            return {
                "enabled": True,
                "clamav_installed": self.clamav_installed,
                "realtime_protection": self.monitor_process is not None,
                "last_scan_date": last_scan.get("timestamp") if last_scan else None,
                "last_scan_type": last_scan.get("scan_type") if last_scan else None,
                "threats_quarantined": self.stats.get("threats_quarantined", 0),
                "threats_removed": self.stats.get("threats_removed", 0),
                "total_scans": self.stats.get("total_scans", 0),
                "total_threats_detected": self.stats.get("total_threats_detected", 0)
            }
        except Exception as e:
            logger.error(f"Error getting protection status: {e}")
            return {"enabled": False, "error": str(e)}
    
    async def start_realtime_monitor(self) -> Dict[str, Any]:
        """Démarre la surveillance temps réel"""
        # TODO: Implémenter avec watchdog
        return {
            "success": False,
            "error": "Realtime monitoring not yet implemented"
        }
    
    async def stop_realtime_monitor(self) -> Dict[str, Any]:
        """Arrête la surveillance temps réel"""
        return {
            "success": False,
            "error": "Realtime monitoring not yet implemented"
        }
    
    async def get_monitor_status(self) -> Dict[str, Any]:
        """État du monitoring"""
        return {
            "running": False,
            "message": "Realtime monitoring not yet implemented"
        }
    
    async def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Historique des scans"""
        try:
            history = await self._load_scan_history()
            return history[:limit]
        except Exception as e:
            logger.error(f"Error getting scan history: {e}")
            return []
    
    async def get_threat_statistics(self) -> Dict[str, Any]:
        """Statistiques sur les menaces"""
        return {
            "total_threats_detected": self.stats.get("total_threats_detected", 0),
            "threats_quarantined": self.stats.get("threats_quarantined", 0),
            "threats_removed": self.stats.get("threats_removed", 0),
            "total_scans": self.stats.get("total_scans", 0)
        }
    
    # Helper methods
    
    async def _save_scan_history(self, scan_result: dict, scan_type: ScanType):
        """Sauvegarde l'historique de scan"""
        try:
            history = await self._load_scan_history()
            
            scan_entry = {
                "scan_id": str(uuid.uuid4()),
                "scan_type": scan_type.value,
                "timestamp": scan_result.get("timestamp"),
                "duration": scan_result.get("scan_time"),
                "files_scanned": scan_result.get("files_scanned", 0),
                "threats_found": scan_result.get("threats_found", 0)
            }
            
            history.insert(0, scan_entry)
            
            # Keep only last 100 scans
            history = history[:100]
            
            with open(self.scan_history_file, "w") as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving scan history: {e}")
    
    async def _load_scan_history(self) -> List[Dict[str, Any]]:
        """Charge l'historique de scan"""
        try:
            if self.scan_history_file.exists():
                with open(self.scan_history_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading scan history: {e}")
            return []
    
    async def _add_to_quarantine_index(self, entry: dict):
        """Ajoute une entrée à l'index de quarantaine"""
        try:
            index = await self._load_quarantine_index()
            index.append(entry)
            await self._save_quarantine_index(index)
        except Exception as e:
            logger.error(f"Error adding to quarantine index: {e}")
    
    async def _load_quarantine_index(self) -> List[Dict[str, Any]]:
        """Charge l'index de quarantaine"""
        try:
            if self.quarantine_index_file.exists():
                with open(self.quarantine_index_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading quarantine index: {e}")
            return []
    
    async def _save_quarantine_index(self, index: List[Dict[str, Any]]):
        """Sauvegarde l'index de quarantaine"""
        try:
            with open(self.quarantine_index_file, "w") as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving quarantine index: {e}")
