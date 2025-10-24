"""
HOPPER - Auto Fix
Corrections automatiques des problèmes courants
"""

import subprocess
import asyncio
from typing import Dict, Callable, Optional
from enum import Enum
from loguru import logger


class FixResult(Enum):
    """Résultat d'une correction"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class AutoFix:
    """
    Corrections automatiques des problèmes courants
    
    Features:
    - Redémarrage services
    - Nettoyage cache/logs
    - Réparation configuration
    - Détection automatique de problèmes
    """
    
    def __init__(self):
        # Registre des corrections disponibles
        self.fixes: Dict[str, Callable] = {
            "neo4j_connection_refused": self.fix_neo4j_connection,
            "out_of_memory": self.fix_out_of_memory,
            "disk_full": self.fix_disk_full,
            "service_crashed": self.fix_service_crashed,
            "ollama_not_running": self.fix_ollama_not_running,
            "port_already_in_use": self.fix_port_conflict,
        }
        logger.info("🔧 AutoFix initialisé")
    
    def detect_issue(self, logs: str) -> Optional[str]:
        """
        Détecter le type de problème depuis les logs
        
        Args:
            logs: Logs d'erreur
        
        Returns:
            Type de problème détecté ou None
        """
        logs_lower = logs.lower()
        
        # Connection refused
        if "connection refused" in logs_lower and "neo4j" in logs_lower:
            return "neo4j_connection_refused"
        
        # Out of memory
        if "out of memory" in logs_lower or "oom" in logs_lower:
            return "out_of_memory"
        
        # Disk full
        if "no space left" in logs_lower or "disk full" in logs_lower:
            return "disk_full"
        
        # Service crashed
        if "crashed" in logs_lower or "exited" in logs_lower:
            return "service_crashed"
        
        # Ollama
        if "ollama" in logs_lower and ("not running" in logs_lower or "connection" in logs_lower):
            return "ollama_not_running"
        
        # Port conflict
        if "address already in use" in logs_lower or "port" in logs_lower:
            return "port_already_in_use"
        
        return None
    
    async def apply_fix(self, issue_type: str, context: Optional[Dict] = None) -> FixResult:
        """
        Appliquer une correction
        
        Args:
            issue_type: Type de problème
            context: Contexte additionnel (service, etc.)
        
        Returns:
            Résultat de la correction
        """
        if issue_type not in self.fixes:
            logger.warning(f"⚠️  Pas de fix automatique pour: {issue_type}")
            return FixResult.SKIPPED
        
        logger.info(f"🔧 Application fix: {issue_type}")
        
        try:
            fix_func = self.fixes[issue_type]
            result = await fix_func(context or {})
            
            if result:
                logger.success(f"✅ Fix {issue_type} réussi")
                return FixResult.SUCCESS
            else:
                logger.error(f"❌ Fix {issue_type} échoué")
                return FixResult.FAILED
        
        except Exception as e:
            logger.error(f"❌ Erreur application fix {issue_type}: {e}")
            return FixResult.FAILED
    
    # --- Corrections spécifiques ---
    
    async def fix_neo4j_connection(self, context: Dict) -> bool:
        """Corriger problème connexion Neo4j"""
        logger.info("🔄 Redémarrage Neo4j...")
        
        try:
            # Redémarrer container Neo4j
            result = subprocess.run(
                ["docker-compose", "restart", "neo4j"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Attendre que Neo4j soit prêt
                await asyncio.sleep(10)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Erreur redémarrage Neo4j: {e}")
            return False
    
    async def fix_out_of_memory(self, context: Dict) -> bool:
        """Corriger problème mémoire"""
        logger.info("🧹 Nettoyage mémoire...")
        
        # 1. Nettoyer caches Python
        try:
            subprocess.run(
                ["find", ".", "-type", "d", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+"],
                timeout=30
            )
        except:
            pass
        
        # 2. Nettoyer logs anciens
        try:
            subprocess.run(
                ["find", "data/logs", "-name", "*.log", "-mtime", "+7", "-delete"],
                timeout=30
            )
        except:
            pass
        
        # 3. Redémarrer service concerné
        service = context.get("service")
        if service:
            logger.info(f"🔄 Redémarrage {service}...")
            try:
                subprocess.run(
                    ["docker-compose", "restart", service],
                    timeout=30
                )
                await asyncio.sleep(5)
            except:
                pass
        
        return True
    
    async def fix_disk_full(self, context: Dict) -> bool:
        """Corriger disque plein"""
        logger.info("🧹 Nettoyage disque...")
        
        # 1. Supprimer vieux logs (>30 jours)
        try:
            subprocess.run(
                ["find", "data/logs", "-name", "*.log", "-mtime", "+30", "-delete"],
                timeout=30
            )
        except:
            pass
        
        # 2. Nettoyer backups anciens (>60 jours)
        try:
            subprocess.run(
                ["find", "backups", "-name", "*.tar.gz", "-mtime", "+60", "-delete"],
                timeout=30
            )
        except:
            pass
        
        # 3. Nettoyer Docker images inutilisées
        try:
            subprocess.run(
                ["docker", "system", "prune", "-f"],
                timeout=60
            )
        except:
            pass
        
        return True
    
    async def fix_service_crashed(self, context: Dict) -> bool:
        """Redémarrer service crashé"""
        service = context.get("service", "")
        
        if not service:
            logger.warning("Service non spécifié pour fix_service_crashed")
            return False
        
        logger.info(f"🔄 Redémarrage service crashé: {service}")
        
        try:
            result = subprocess.run(
                ["docker-compose", "restart", service],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                await asyncio.sleep(5)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Erreur redémarrage {service}: {e}")
            return False
    
    async def fix_ollama_not_running(self, context: Dict) -> bool:
        """Démarrer Ollama"""
        logger.info("🚀 Démarrage Ollama...")
        
        try:
            # Sur macOS, Ollama doit être démarré manuellement
            # On peut juste logger l'instruction
            logger.warning("⚠️  Ollama doit être démarré manuellement:")
            logger.warning("    Terminal: ollama serve")
            
            # Sur Linux avec systemd:
            # subprocess.run(["systemctl", "start", "ollama"])
            
            return False  # Nécessite action manuelle
        
        except Exception as e:
            logger.error(f"Erreur démarrage Ollama: {e}")
            return False
    
    async def fix_port_conflict(self, context: Dict) -> bool:
        """Résoudre conflit de port"""
        port = context.get("port")
        service = context.get("service")
        
        logger.info(f"🔄 Résolution conflit port {port} pour {service}")
        
        # Trouver et kill processus utilisant le port
        try:
            # Sur macOS/Linux
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.stdout.strip():
                pid = result.stdout.strip()
                logger.info(f"Kill processus {pid} sur port {port}")
                subprocess.run(["kill", "-9", pid], timeout=5)
                
                await asyncio.sleep(2)
                
                # Redémarrer service
                if service:
                    subprocess.run(
                        ["docker-compose", "restart", service],
                        timeout=30
                    )
                
                return True
        
        except Exception as e:
            logger.error(f"Erreur résolution port: {e}")
        
        return False


# Instance globale
_auto_fix = None

def get_auto_fix() -> AutoFix:
    """Obtenir l'instance globale"""
    global _auto_fix
    if _auto_fix is None:
        _auto_fix = AutoFix()
    return _auto_fix


if __name__ == "__main__":
    # Test de l'auto-fix
    async def test():
        fixer = AutoFix()
        
        # Test détection
        test_logs = [
            "Connection refused to neo4j database",
            "Out of memory error occurred",
            "No space left on device",
            "Service orchestrator crashed"
        ]
        
        for log in test_logs:
            issue = fixer.detect_issue(log)
            print(f"Log: {log[:50]}...")
            print(f"Issue détecté: {issue}")
            print()
    
    asyncio.run(test())
