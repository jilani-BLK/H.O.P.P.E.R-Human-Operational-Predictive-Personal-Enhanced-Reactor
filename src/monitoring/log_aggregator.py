"""
HOPPER - Log Aggregator
Agrégation et analyse des logs de tous les services
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from collections import defaultdict
from loguru import logger


class LogEntry:
    """Entrée de log parsée"""
    
    def __init__(
        self,
        timestamp: datetime,
        level: str,
        service: str,
        message: str,
        raw_line: str
    ):
        self.timestamp = timestamp
        self.level = level
        self.service = service
        self.message = message
        self.raw_line = raw_line


class LogAggregator:
    """
    Agrégation et analyse des logs
    
    Features:
    - Parsing logs multi-services
    - Détection patterns d'erreurs
    - Agrégation temporelle
    - Génération rapports
    - Recherche full-text
    """
    
    # Patterns de parsing pour différents formats de logs
    LOG_PATTERNS = [
        # Format loguru: 2025-10-23 15:42:38.200 | INFO | module:function:line - message
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| (\w+)\s+\| .*? - (.+)',
        
        # Format standard Python: INFO:module:message
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d+) (\w+) (.+)',
        
        # Format uvicorn: INFO: message
        r'(\w+):\s+(.+)',
    ]
    
    def __init__(self, logs_dir: str = "data/logs"):
        self.logs_dir = Path(logs_dir)
        self.entries: List[LogEntry] = []
        logger.info(f"📝 LogAggregator initialisé (logs_dir={logs_dir})")
    
    def _parse_log_line(self, line: str, service: str) -> Optional[LogEntry]:
        """Parser une ligne de log"""
        line = line.strip()
        if not line:
            return None
        
        # Essayer chaque pattern
        for pattern in self.LOG_PATTERNS:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                
                # Format loguru complet
                if len(groups) >= 3:
                    try:
                        timestamp = datetime.fromisoformat(groups[0].replace(',', '.'))
                        level = groups[1]
                        message = groups[2] if len(groups) == 3 else groups[3]
                        
                        return LogEntry(
                            timestamp=timestamp,
                            level=level.upper(),
                            service=service,
                            message=message,
                            raw_line=line
                        )
                    except:
                        continue
                
                # Format simple (level: message)
                elif len(groups) == 2:
                    level, message = groups
                    return LogEntry(
                        timestamp=datetime.now(),  # Pas de timestamp dans le log
                        level=level.upper(),
                        service=service,
                        message=message,
                        raw_line=line
                    )
        
        # Si aucun pattern ne match, créer entrée basique
        return LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            service=service,
            message=line,
            raw_line=line
        )
    
    def load_logs(self, service: Optional[str] = None, last_hours: int = 24):
        """
        Charger les logs
        
        Args:
            service: Service spécifique ou None pour tous
            last_hours: Charger logs des X dernières heures
        """
        self.entries = []
        
        if not self.logs_dir.exists():
            logger.warning(f"Répertoire logs introuvable: {self.logs_dir}")
            return
        
        # Calculer cutoff time
        cutoff = datetime.now() - timedelta(hours=last_hours)
        
        # Parcourir fichiers de logs
        log_files = list(self.logs_dir.glob("*.log"))
        
        for log_file in log_files:
            # Déterminer service depuis nom fichier
            service_name = log_file.stem  # orchestrator.log -> orchestrator
            
            if service and service != service_name:
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry = self._parse_log_line(line, service_name)
                        if entry and entry.timestamp >= cutoff:
                            self.entries.append(entry)
            except Exception as e:
                logger.error(f"Erreur lecture {log_file}: {e}")
        
        # Trier par timestamp
        self.entries.sort(key=lambda x: x.timestamp)
        
        logger.info(f"📊 {len(self.entries)} entrées de log chargées")
    
    def get_entries_by_level(self, level: str) -> List[LogEntry]:
        """Récupérer entrées par niveau"""
        return [e for e in self.entries if e.level == level.upper()]
    
    def get_errors(self) -> List[LogEntry]:
        """Récupérer toutes les erreurs"""
        return [e for e in self.entries if e.level in ['ERROR', 'CRITICAL']]
    
    def get_warnings(self) -> List[LogEntry]:
        """Récupérer tous les warnings"""
        return self.get_entries_by_level('WARNING')
    
    def search(self, query: str, case_sensitive: bool = False) -> List[LogEntry]:
        """
        Rechercher dans les logs
        
        Args:
            query: Terme de recherche
            case_sensitive: Recherche sensible à la casse
        
        Returns:
            Entrées matchant la recherche
        """
        if not case_sensitive:
            query = query.lower()
        
        results = []
        for entry in self.entries:
            text = entry.message if case_sensitive else entry.message.lower()
            if query in text:
                results.append(entry)
        
        return results
    
    def get_stats(self) -> Dict:
        """Générer statistiques"""
        stats = {
            "total_entries": len(self.entries),
            "by_level": defaultdict(int),
            "by_service": defaultdict(int),
            "error_count": 0,
            "warning_count": 0,
            "time_range": {
                "start": None,
                "end": None
            }
        }
        
        if not self.entries:
            return stats
        
        # Par niveau
        for entry in self.entries:
            stats["by_level"][entry.level] += 1
            stats["by_service"][entry.service] += 1
        
        # Compter erreurs et warnings
        stats["error_count"] = stats["by_level"].get("ERROR", 0) + \
                              stats["by_level"].get("CRITICAL", 0)
        stats["warning_count"] = stats["by_level"].get("WARNING", 0)
        
        # Time range
        stats["time_range"]["start"] = self.entries[0].timestamp.isoformat()
        stats["time_range"]["end"] = self.entries[-1].timestamp.isoformat()
        
        # Convertir defaultdict en dict normal
        stats["by_level"] = dict(stats["by_level"])
        stats["by_service"] = dict(stats["by_service"])
        
        return stats
    
    def detect_patterns(self) -> Dict[str, int]:
        """
        Détecter patterns d'erreurs communs
        
        Returns:
            Dictionnaire pattern -> count
        """
        patterns = {
            "connection_error": r'connection|connect|refused',
            "timeout": r'timeout|timed out',
            "not_found": r'not found|404',
            "permission": r'permission|denied|forbidden|403',
            "memory": r'memory|oom|out of memory',
            "database": r'database|db|sql|neo4j',
            "authentication": r'auth|authentication|unauthorized|401',
        }
        
        counts = defaultdict(int)
        
        errors = self.get_errors()
        
        for entry in errors:
            message_lower = entry.message.lower()
            
            for pattern_name, pattern_regex in patterns.items():
                if re.search(pattern_regex, message_lower):
                    counts[pattern_name] += 1
        
        return dict(counts)
    
    def generate_report(self) -> str:
        """Générer rapport d'analyse"""
        stats = self.get_stats()
        patterns = self.detect_patterns()
        
        report = []
        report.append("=" * 60)
        report.append("📝 RAPPORT D'ANALYSE DES LOGS")
        report.append("=" * 60)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Période
        if stats["time_range"]["start"]:
            report.append(f"📅 PÉRIODE:")
            report.append(f"  De: {stats['time_range']['start']}")
            report.append(f"  À:  {stats['time_range']['end']}")
            report.append("")
        
        # Statistiques globales
        report.append(f"📊 STATISTIQUES:")
        report.append(f"  Total entrées: {stats['total_entries']}")
        report.append(f"  Erreurs: {stats['error_count']}")
        report.append(f"  Warnings: {stats['warning_count']}")
        report.append("")
        
        # Par niveau
        report.append("🔴 PAR NIVEAU:")
        for level, count in sorted(stats['by_level'].items(), 
                                   key=lambda x: x[1], reverse=True):
            report.append(f"  - {level}: {count}")
        report.append("")
        
        # Par service
        report.append("🔧 PAR SERVICE:")
        for service, count in sorted(stats['by_service'].items(), 
                                     key=lambda x: x[1], reverse=True):
            report.append(f"  - {service}: {count}")
        report.append("")
        
        # Patterns détectés
        if patterns:
            report.append("🔍 PATTERNS D'ERREURS DÉTECTÉS:")
            for pattern, count in sorted(patterns.items(), 
                                        key=lambda x: x[1], reverse=True):
                if count > 0:
                    report.append(f"  - {pattern}: {count} occurrences")
            report.append("")
        
        # Dernières erreurs
        recent_errors = self.get_errors()[-10:]
        if recent_errors:
            report.append("🚨 DERNIÈRES ERREURS:")
            for entry in recent_errors:
                time_str = entry.timestamp.strftime("%H:%M:%S")
                report.append(f"  [{time_str}] {entry.service}: {entry.message[:70]}...")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


# Instance globale
_log_aggregator = None

def get_log_aggregator() -> LogAggregator:
    """Obtenir l'instance globale"""
    global _log_aggregator
    if _log_aggregator is None:
        _log_aggregator = LogAggregator()
    return _log_aggregator


if __name__ == "__main__":
    # Test de l'aggregator
    aggregator = LogAggregator()
    
    print("📝 Chargement logs (dernières 24h)...")
    aggregator.load_logs(last_hours=24)
    
    print(aggregator.generate_report())
    
    # Recherche
    print("\n🔍 Recherche 'error':")
    results = aggregator.search("error")
    print(f"Trouvé {len(results)} résultats")
