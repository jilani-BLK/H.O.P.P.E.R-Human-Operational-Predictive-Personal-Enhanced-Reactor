"""
HOPPER - Antivirus Adapter Base
Interface abstraite pour les adapters antivirus cross-platform
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime


class ThreatLevel(Enum):
    """Niveau de menace détecté"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Type de menace"""
    VIRUS = "virus"
    TROJAN = "trojan"
    RANSOMWARE = "ransomware"
    SPYWARE = "spyware"
    ADWARE = "adware"
    ROOTKIT = "rootkit"
    WORM = "worm"
    SUSPICIOUS = "suspicious"
    UNKNOWN = "unknown"


class ScanType(Enum):
    """Type de scan"""
    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"
    FILE = "file"
    DIRECTORY = "directory"


class AntivirusAdapter(ABC):
    """
    Interface abstraite pour les adapters antivirus cross-platform.
    
    Chaque OS (macOS, Windows, Linux) implémente cette interface
    avec ses outils spécifiques (ClamAV, Windows Defender, etc.)
    """
    
    @abstractmethod
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scanne un fichier unique pour détecter des menaces.
        
        Args:
            file_path: Chemin absolu du fichier à scanner
            
        Returns:
            {
                "clean": bool,
                "file_path": str,
                "threats": [
                    {
                        "name": "Trojan.MacOS.Generic",
                        "type": ThreatType.TROJAN,
                        "level": ThreatLevel.HIGH,
                        "description": "Trojan malveillant",
                        "action_recommended": "delete",
                        "detection_method": "signature"
                    }
                ],
                "scan_time": 0.5,
                "methods_used": ["signature", "heuristic"],
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def scan_directory(
        self, 
        directory_path: str,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
        max_depth: int = -1
    ) -> Dict[str, Any]:
        """
        Scanne un répertoire pour détecter des menaces.
        
        Args:
            directory_path: Chemin du répertoire à scanner
            recursive: Scanner récursivement les sous-dossiers
            extensions: Liste d'extensions à scanner (None = toutes)
            max_depth: Profondeur maximale (-1 = illimité)
            
        Returns:
            {
                "directory": str,
                "files_scanned": 150,
                "threats_found": 2,
                "clean_files": 148,
                "infected_files": [
                    {
                        "path": "/path/to/virus.sh",
                        "threats": [...]
                    }
                ],
                "scan_time": 45.2,
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def full_scan(self) -> Dict[str, Any]:
        """
        Scan complet du système.
        
        Scanne les zones critiques selon l'OS:
        - macOS: /, /Users, /Applications, /Library
        - Windows: C:\\, Program Files, Users, Windows
        - Linux: /, /home, /opt, /usr
        
        Returns:
            {
                "scan_type": ScanType.FULL,
                "total_files_scanned": 15000,
                "threats_found": 5,
                "clean_files": 14995,
                "infected_files": [...],
                "scan_time": 3600.5,
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def quick_scan(self) -> Dict[str, Any]:
        """
        Scan rapide des zones critiques.
        
        Scanne uniquement:
        - Répertoire téléchargements
        - Répertoire temporaire
        - Applications récemment installées
        - Dossiers système critiques
        
        Returns:
            {
                "scan_type": ScanType.QUICK,
                "files_scanned": 500,
                "threats_found": 1,
                "scan_time": 30.5,
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def detect_threats(
        self,
        file_path: str,
        methods: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Détection multi-méthodes sur un fichier.
        
        Args:
            file_path: Chemin du fichier à analyser
            methods: Liste des méthodes à utiliser
                - "signature": Base de signatures virales
                - "behavior": Analyse comportementale
                - "heuristic": Détection heuristique
                - "ml": Machine learning (optionnel)
                
        Returns:
            [
                {
                    "name": "Trojan.Generic",
                    "type": ThreatType.TROJAN,
                    "level": ThreatLevel.HIGH,
                    "confidence": 0.95,
                    "method": "signature",
                    "description": "...",
                    "indicators": [
                        "suspicious_api_calls",
                        "code_injection_detected"
                    ]
                }
            ]
        """
        if methods is None:
            methods = ["signature", "heuristic"]
        pass
    
    @abstractmethod
    async def quarantine_file(self, file_path: str, reason: str = "") -> Dict[str, Any]:
        """
        Isole un fichier suspect dans la zone de quarantaine.
        
        Actions:
        1. Déplace le fichier vers /var/hopper/quarantine/
        2. Supprime les permissions d'exécution
        3. Crée un ID unique pour le fichier
        4. Log l'opération
        
        Args:
            file_path: Chemin du fichier à mettre en quarantaine
            reason: Raison de la quarantaine
            
        Returns:
            {
                "success": True,
                "original_path": "/path/to/virus.sh",
                "quarantine_path": "/var/hopper/quarantine/uuid_virus.sh",
                "quarantine_id": "uuid-1234",
                "timestamp": "2025-10-23T10:30:00",
                "reason": "Trojan detected"
            }
        """
        pass
    
    @abstractmethod
    async def remove_threat(
        self,
        file_path: str,
        secure_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Supprime définitivement un fichier malveillant.
        
        ⚠️ CETTE OPÉRATION EST IRRÉVERSIBLE ⚠️
        ⚠️ REQUIERT CONFIRMATION UTILISATEUR OBLIGATOIRE ⚠️
        
        Args:
            file_path: Chemin du fichier à supprimer
            secure_delete: Si True, écrase avec données aléatoires (shred)
                          Si False, suppression simple
                          
        Returns:
            {
                "success": True,
                "file_path": str,
                "method": "secure_shred" | "simple_delete",
                "passes": 3,  # Nombre de passes shred
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def restore_from_quarantine(self, quarantine_id: str) -> Dict[str, Any]:
        """
        Restaure un fichier depuis la quarantaine.
        
        Utilisé en cas de faux positif détecté.
        
        Args:
            quarantine_id: ID unique du fichier en quarantaine
            
        Returns:
            {
                "success": True,
                "quarantine_id": "uuid-1234",
                "original_path": "/path/to/file.sh",
                "restored": True,
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def list_quarantine(self) -> List[Dict[str, Any]]:
        """
        Liste tous les fichiers en quarantaine.
        
        Returns:
            [
                {
                    "quarantine_id": "uuid-1234",
                    "original_path": "/path/to/virus.sh",
                    "quarantine_path": "/var/hopper/quarantine/...",
                    "threat_name": "Trojan.Generic",
                    "quarantine_date": "2025-10-23T10:30:00",
                    "reason": "..."
                }
            ]
        """
        pass
    
    @abstractmethod
    async def update_definitions(self) -> Dict[str, Any]:
        """
        Met à jour les définitions de virus.
        
        Selon l'OS:
        - macOS: freshclam (ClamAV)
        - Windows: Update-MpSignature (Defender)
        - Linux: freshclam + custom signatures
        
        Returns:
            {
                "success": True,
                "previous_version": "2025.10.22",
                "new_version": "2025.10.23",
                "signatures_added": 150,
                "signatures_updated": 50,
                "update_time": 30.5,
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def get_protection_status(self) -> Dict[str, Any]:
        """
        Retourne l'état actuel de la protection.
        
        Returns:
            {
                "enabled": True,
                "realtime_protection": True,
                "last_scan_date": "2025-10-23T10:30:00",
                "last_update_date": "2025-10-23T08:00:00",
                "definitions_version": "2025.10.23",
                "signatures_count": 10000000,
                "threats_quarantined": 3,
                "threats_removed": 15,
                "total_scans": 150,
                "uptime": 86400  # secondes
            }
        """
        pass
    
    @abstractmethod
    async def start_realtime_monitor(self) -> Dict[str, Any]:
        """
        Démarre la surveillance en temps réel.
        
        Active:
        - Watchdog sur fichiers créés/modifiés
        - Analyse comportementale des processus
        - Détection d'intrusions réseau (optionnel)
        - Monitoring activité système suspecte
        
        Returns:
            {
                "success": True,
                "monitor_started": True,
                "monitoring_paths": ["/Users", "/Applications"],
                "watch_extensions": [".sh", ".app", ".dmg", ".pkg"],
                "pid": 12345,
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def stop_realtime_monitor(self) -> Dict[str, Any]:
        """
        Arrête la surveillance en temps réel.
        
        Returns:
            {
                "success": True,
                "monitor_stopped": True,
                "uptime": 3600,
                "files_monitored": 5000,
                "threats_detected": 2,
                "timestamp": "2025-10-23T10:30:00"
            }
        """
        pass
    
    @abstractmethod
    async def get_monitor_status(self) -> Dict[str, Any]:
        """
        État du monitoring temps réel.
        
        Returns:
            {
                "running": True,
                "uptime": 3600,
                "files_monitored": 5000,
                "threats_detected": 2,
                "last_threat": "2025-10-23T09:45:00",
                "cpu_usage": 2.5,
                "memory_usage": 150.5
            }
        """
        pass
    
    @abstractmethod
    async def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Historique des scans effectués.
        
        Args:
            limit: Nombre maximum de scans à retourner
            
        Returns:
            [
                {
                    "scan_id": "uuid-scan-123",
                    "scan_type": ScanType.FULL,
                    "start_time": "2025-10-23T10:00:00",
                    "end_time": "2025-10-23T11:00:00",
                    "duration": 3600,
                    "files_scanned": 15000,
                    "threats_found": 2,
                    "threats": [...]
                }
            ]
        """
        pass
    
    @abstractmethod
    async def get_threat_statistics(self) -> Dict[str, Any]:
        """
        Statistiques sur les menaces détectées.
        
        Returns:
            {
                "total_threats_detected": 50,
                "threats_quarantined": 30,
                "threats_removed": 20,
                "threats_by_type": {
                    "virus": 10,
                    "trojan": 15,
                    "ransomware": 2,
                    "spyware": 5
                },
                "threats_by_level": {
                    "low": 10,
                    "medium": 15,
                    "high": 20,
                    "critical": 5
                },
                "last_24h": 5,
                "last_7d": 15,
                "last_30d": 50
            }
        """
        pass
