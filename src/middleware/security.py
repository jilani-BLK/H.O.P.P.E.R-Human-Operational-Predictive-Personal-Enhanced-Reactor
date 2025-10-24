"""
HOPPER - Security Middleware
Middleware centralisé pour rate limiting et authentification API
"""

import os
import time
from typing import Dict, Optional, Callable, Awaitable
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
import asyncio


class RateLimiter:
    """
    Rate Limiter simple basé sur IP
    Prévient les attaques DoS par flood de requêtes
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Limite par minute (défaut: 60)
            requests_per_hour: Limite par heure (défaut: 1000)
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Stockage en mémoire des compteurs
        # Format: {ip: [(timestamp, count), ...]}
        self.minute_counters: Dict[str, list] = defaultdict(list)
        self.hour_counters: Dict[str, list] = defaultdict(list)
        
        # Lock pour thread-safety
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self, client_ip: str) -> tuple[bool, Optional[str]]:
        """
        Vérifie si le client a dépassé les limites
        
        Args:
            client_ip: Adresse IP du client
            
        Returns:
            (allowed, error_message)
        """
        async with self.lock:
            now = datetime.now()
            
            # Nettoyage des anciennes entrées (> 1 heure)
            cutoff_hour = now - timedelta(hours=1)
            cutoff_minute = now - timedelta(minutes=1)
            
            # Filtrer les compteurs minute
            self.minute_counters[client_ip] = [
                ts for ts in self.minute_counters[client_ip]
                if ts > cutoff_minute.timestamp()
            ]
            
            # Filtrer les compteurs heure
            self.hour_counters[client_ip] = [
                ts for ts in self.hour_counters[client_ip]
                if ts > cutoff_hour.timestamp()
            ]
            
            # Vérifier limites
            minute_count = len(self.minute_counters[client_ip])
            hour_count = len(self.hour_counters[client_ip])
            
            if minute_count >= self.requests_per_minute:
                logger.warning(f"🚫 Rate limit (minute) dépassé pour {client_ip}: {minute_count}/{self.requests_per_minute}")
                return False, f"Rate limit exceeded: {minute_count}/{self.requests_per_minute} requests per minute"
            
            if hour_count >= self.requests_per_hour:
                logger.warning(f"🚫 Rate limit (heure) dépassé pour {client_ip}: {hour_count}/{self.requests_per_hour}")
                return False, f"Rate limit exceeded: {hour_count}/{self.requests_per_hour} requests per hour"
            
            # Ajouter nouveau compteur
            timestamp = now.timestamp()
            self.minute_counters[client_ip].append(timestamp)
            self.hour_counters[client_ip].append(timestamp)
            
            return True, None
    
    async def cleanup_old_entries(self):
        """Nettoyage périodique des anciennes entrées"""
        async with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(hours=2)
            cutoff_ts = cutoff.timestamp()
            
            # Nettoyer les IPs sans activité récente
            for ip in list(self.minute_counters.keys()):
                if not self.minute_counters[ip] or max(self.minute_counters[ip]) < cutoff_ts:
                    del self.minute_counters[ip]
            
            for ip in list(self.hour_counters.keys()):
                if not self.hour_counters[ip] or max(self.hour_counters[ip]) < cutoff_ts:
                    del self.hour_counters[ip]


class APITokenAuth:
    """
    Authentification par token API (X-API-Key header)
    Protection contre accès non autorisés
    """
    
    def __init__(self):
        """Initialize API token authenticator"""
        # Token depuis variable d'environnement
        self.api_token = os.getenv("API_TOKEN")
        
        # Liste de tokens valides (support multi-tokens)
        self.valid_tokens = set()
        if self.api_token:
            self.valid_tokens.add(self.api_token)
        
        # Charger tokens additionnels depuis fichier si existant
        token_file = os.getenv("API_TOKENS_FILE", "/data/config/api_tokens.txt")
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    for line in f:
                        token = line.strip()
                        if token and not token.startswith('#'):
                            self.valid_tokens.add(token)
                logger.info(f"✅ {len(self.valid_tokens)} API tokens chargés")
            except Exception as e:
                logger.error(f"❌ Erreur chargement tokens: {e}")
        
        # Mode développement (pas de token requis)
        self.dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        
        if self.dev_mode:
            logger.warning("⚠️ DEV_MODE activé - Authentification API désactivée")
        elif not self.valid_tokens:
            logger.warning("⚠️ Aucun API_TOKEN configuré - Service non protégé!")
    
    def verify_token(self, token: Optional[str]) -> bool:
        """
        Vérifie si le token est valide
        
        Args:
            token: Token API à vérifier
            
        Returns:
            True si valide, False sinon
        """
        # En mode dev, accepter tout
        if self.dev_mode:
            return True
        
        # Si pas de token configuré, accepter (mode permissif)
        if not self.valid_tokens:
            return True
        
        # Vérifier token
        return token in self.valid_tokens


# Instances globales
rate_limiter = RateLimiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
    requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
)

api_auth = APITokenAuth()


async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Middleware de sécurité principal
    Applique rate limiting et authentification
    """
    # Exclure endpoints de santé du rate limiting
    if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # 1. Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    allowed, error_msg = await rate_limiter.check_rate_limit(client_ip)
    
    if not allowed:
        logger.warning(f"🚫 Rate limit dépassé: {client_ip} → {request.url.path}")
        return Response(
            content=f'{{"detail": "{error_msg}"}}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json"
        )
    
    # 2. Authentification API Token
    api_token = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    
    # Nettoyer Authorization header si format Bearer
    if api_token and api_token.startswith("Bearer "):
        api_token = api_token[7:]
    
    if not api_auth.verify_token(api_token):
        logger.warning(f"🚫 Token invalide: {client_ip} → {request.url.path}")
        return Response(
            content='{"detail": "Invalid or missing API token. Set X-API-Key header."}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            media_type="application/json",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 3. Continuer vers la route
    response = await call_next(request)
    
    # Ajouter headers de sécurité
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


def get_security_middleware():
    """
    Factory pour récupérer le middleware de sécurité
    Usage dans FastAPI:
        app.middleware("http")(security_middleware)
    """
    return security_middleware


# Cleanup task pour le rate limiter
async def cleanup_rate_limiter_task():
    """Tâche de nettoyage périodique du rate limiter"""
    while True:
        await asyncio.sleep(3600)  # Toutes les heures
        await rate_limiter.cleanup_old_entries()
        logger.debug("🧹 Rate limiter cleanup effectué")
