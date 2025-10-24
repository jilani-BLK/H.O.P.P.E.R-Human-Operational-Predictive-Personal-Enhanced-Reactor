"""
HOPPER - Health Checker
Surveillance santé des services avec auto-diagnostics
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from loguru import logger


class ServiceStatus(Enum):
    """Status d'un service"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Résultat d'un health check"""
    service: str
    status: ServiceStatus
    response_time_ms: float
    timestamp: str
    message: str = ""
    details: Optional[Dict] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class HealthChecker:
    """
    Surveillance santé services HOPPER
    
    Features:
    - Health checks HTTP périodiques
    - Mesure latence
    - Détection dégradation
    - Historique des checks
    - Alertes automatiques
    """
    
    # Configuration des services
    SERVICES = {
        "neo4j": {
            "url": "http://localhost:7474",
            "timeout": 5.0,
            "critical": True
        },
        "orchestrator": {
            "url": "http://localhost:5050/health",
            "timeout": 3.0,
            "critical": True
        },
        "stt": {
            "url": "http://localhost:5003/health",
            "timeout": 3.0,
            "critical": True
        },
        "llm": {
            "url": "http://localhost:5001/health",
            "timeout": 5.0,
            "critical": True
        },
        "tts": {
            "url": "http://localhost:5004/health",
            "timeout": 3.0,
            "critical": True
        },
        "auth": {
            "url": "http://localhost:5005/health",
            "timeout": 2.0,
            "critical": True
        },
        "system_executor": {
            "url": "http://localhost:5002/health",
            "timeout": 2.0,
            "critical": True
        },
        "connectors": {
            "url": "http://localhost:5006/health",
            "timeout": 3.0,
            "critical": False
        }
    }
    
    def __init__(self):
        self.history: Dict[str, List[HealthCheckResult]] = {
            service: [] for service in self.SERVICES.keys()
        }
        self.max_history_size = 100  # Garder 100 derniers checks par service
        logger.info("❤️ HealthChecker initialisé")
    
    async def check_service(self, service_name: str) -> HealthCheckResult:
        """
        Vérifier la santé d'un service
        
        Args:
            service_name: Nom du service
        
        Returns:
            Résultat du health check
        """
        if service_name not in self.SERVICES:
            return HealthCheckResult(
                service=service_name,
                status=ServiceStatus.UNKNOWN,
                response_time_ms=0,
                timestamp=datetime.now().isoformat(),
                message=f"Service inconnu: {service_name}"
            )
        
        config = self.SERVICES[service_name]
        url = config["url"]
        timeout = config["timeout"]
        
        timestamp = datetime.now().isoformat()
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                status = ServiceStatus.HEALTHY
                message = "Service OK"
                
                # Vérifier dégradation (latence élevée)
                if response_time > timeout * 1000 * 0.8:  # >80% timeout
                    status = ServiceStatus.DEGRADED
                    message = f"Latence élevée: {response_time:.0f}ms"
                
                try:
                    details = response.json()
                except:
                    details = {}
                
            else:
                status = ServiceStatus.UNHEALTHY
                message = f"HTTP {response.status_code}"
                details = {}
                response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        except httpx.TimeoutException:
            status = ServiceStatus.UNHEALTHY
            message = f"Timeout après {timeout}s"
            response_time = timeout * 1000
            details = {}
        
        except Exception as e:
            status = ServiceStatus.UNHEALTHY
            message = f"Erreur: {type(e).__name__}"
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            details = {"error": str(e)}
        
        result = HealthCheckResult(
            service=service_name,
            status=status,
            response_time_ms=response_time,
            timestamp=timestamp,
            message=message,
            details=details
        )
        
        # Ajouter à l'historique
        self._add_to_history(service_name, result)
        
        return result
    
    def _add_to_history(self, service_name: str, result: HealthCheckResult):
        """Ajouter résultat à l'historique"""
        if service_name not in self.history:
            self.history[service_name] = []
        
        self.history[service_name].append(result)
        
        # Limiter taille historique
        if len(self.history[service_name]) > self.max_history_size:
            self.history[service_name].pop(0)
    
    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """
        Vérifier tous les services
        
        Returns:
            Dictionnaire service -> résultat
        """
        tasks = []
        for service_name in self.SERVICES.keys():
            tasks.append(self.check_service(service_name))
        
        results = await asyncio.gather(*tasks)
        
        return {result.service: result for result in results}
    
    def get_service_health(self, service_name: str) -> Optional[HealthCheckResult]:
        """Récupérer dernier check d'un service"""
        if service_name in self.history and self.history[service_name]:
            return self.history[service_name][-1]
        return None
    
    def get_unhealthy_services(self) -> List[str]:
        """Récupérer services non-healthy"""
        unhealthy = []
        for service_name, checks in self.history.items():
            if checks and checks[-1].status != ServiceStatus.HEALTHY:
                unhealthy.append(service_name)
        return unhealthy
    
    def get_critical_services_down(self) -> List[str]:
        """Récupérer services critiques down"""
        critical_down = []
        for service_name, config in self.SERVICES.items():
            if config["critical"]:
                last_check = self.get_service_health(service_name)
                if last_check and last_check.status == ServiceStatus.UNHEALTHY:
                    critical_down.append(service_name)
        return critical_down
    
    def get_average_response_time(self, service_name: str, last_n: int = 10) -> float:
        """Calculer temps de réponse moyen"""
        if service_name not in self.history:
            return 0.0
        
        checks = self.history[service_name][-last_n:]
        if not checks:
            return 0.0
        
        # Exclure les timeouts du calcul
        valid_times = [
            c.response_time_ms for c in checks 
            if c.status != ServiceStatus.UNHEALTHY
        ]
        
        if not valid_times:
            return 0.0
        
        return sum(valid_times) / len(valid_times)
    
    def get_uptime_percentage(self, service_name: str, last_n: int = 100) -> float:
        """Calculer uptime en %"""
        if service_name not in self.history:
            return 0.0
        
        checks = self.history[service_name][-last_n:]
        if not checks:
            return 0.0
        
        healthy_count = sum(
            1 for c in checks if c.status == ServiceStatus.HEALTHY
        )
        
        return (healthy_count / len(checks)) * 100
    
    def generate_report(self) -> str:
        """Générer rapport santé"""
        report = []
        report.append("=" * 60)
        report.append("❤️  RAPPORT SANTÉ HOPPER")
        report.append("=" * 60)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Status global
        unhealthy = self.get_unhealthy_services()
        critical_down = self.get_critical_services_down()
        
        total_services = len(self.SERVICES)
        healthy_services = total_services - len(unhealthy)
        
        report.append(f"📊 STATUS GLOBAL:")
        report.append(f"  Services actifs: {healthy_services}/{total_services}")
        
        if critical_down:
            report.append(f"  🚨 Services critiques DOWN: {len(critical_down)}")
            for service in critical_down:
                report.append(f"    - {service}")
        else:
            report.append("  ✅ Tous services critiques OK")
        report.append("")
        
        # Détails par service
        report.append("🔍 DÉTAILS PAR SERVICE:")
        for service_name in sorted(self.SERVICES.keys()):
            last_check = self.get_service_health(service_name)
            if not last_check:
                report.append(f"  - {service_name}: Pas de données")
                continue
            
            status_icon = {
                ServiceStatus.HEALTHY: "✅",
                ServiceStatus.DEGRADED: "⚠️ ",
                ServiceStatus.UNHEALTHY: "❌",
                ServiceStatus.UNKNOWN: "❓"
            }[last_check.status]
            
            avg_time = self.get_average_response_time(service_name)
            uptime = self.get_uptime_percentage(service_name)
            
            report.append(f"  {status_icon} {service_name}:")
            report.append(f"      Status: {last_check.status.value}")
            report.append(f"      Latence: {last_check.response_time_ms:.0f}ms "
                        f"(moy: {avg_time:.0f}ms)")
            report.append(f"      Uptime: {uptime:.1f}%")
            if last_check.message:
                report.append(f"      Message: {last_check.message}")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    async def monitor_continuous(self, interval: int = 60):
        """
        Surveillance continue
        
        Args:
            interval: Intervalle entre checks (secondes)
        """
        logger.info(f"🔄 Démarrage surveillance continue (interval={interval}s)")
        
        while True:
            try:
                results = await self.check_all()
                
                # Logger services unhealthy
                unhealthy = [
                    name for name, result in results.items()
                    if result.status != ServiceStatus.HEALTHY
                ]
                
                if unhealthy:
                    logger.warning(f"⚠️  Services non-healthy: {', '.join(unhealthy)}")
                
                # Vérifier services critiques
                critical_down = self.get_critical_services_down()
                if critical_down:
                    logger.error(f"🚨 Services CRITIQUES down: {', '.join(critical_down)}")
                
            except Exception as e:
                logger.error(f"Erreur surveillance: {e}")
            
            await asyncio.sleep(interval)


# Instance globale
_health_checker = None

def get_health_checker() -> HealthChecker:
    """Obtenir l'instance globale du checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


if __name__ == "__main__":
    # Test du checker
    async def test():
        checker = HealthChecker()
        
        print("🔍 Test health check tous services...")
        results = await checker.check_all()
        
        for service, result in results.items():
            status_icon = "✅" if result.status == ServiceStatus.HEALTHY else "❌"
            print(f"{status_icon} {service}: {result.status.value} "
                  f"({result.response_time_ms:.0f}ms)")
        
        print("\n" + checker.generate_report())
    
    asyncio.run(test())
