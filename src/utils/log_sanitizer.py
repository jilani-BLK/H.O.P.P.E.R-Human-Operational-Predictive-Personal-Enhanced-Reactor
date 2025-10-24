"""
Log Sanitizer - Masque les données sensibles dans les logs
Security: CWE-532 (Information Exposure Through Log Files)
"""

import re
from typing import Any
from loguru import logger


# Patterns de données sensibles à masquer
SENSITIVE_PATTERNS = [
    # Passwords
    (r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password=***MASKED***'),
    (r'passwd["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'passwd=***MASKED***'),
    (r'pwd["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'pwd=***MASKED***'),
    
    # API Keys & Tokens
    (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'api_key=***MASKED***'),
    (r'token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'token=***MASKED***'),
    (r'secret["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'secret=***MASKED***'),
    (r'bearer\s+([a-zA-Z0-9\-._~+/]+=*)', 'Bearer ***MASKED***'),
    
    # Authorization headers
    (r'authorization["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'Authorization: ***MASKED***'),
    (r'x-api-key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'X-API-Key: ***MASKED***'),
    
    # OpenAI API Keys (sk-... format)
    (r'sk-[a-zA-Z0-9]{20,}', 'sk-***MASKED***'),
    (r'sk-proj-[a-zA-Z0-9]{20,}', 'sk-proj-***MASKED***'),
    
    # Database URIs with passwords (toutes variantes)
    (r'(mongodb(\+srv)?|mysql|postgres(ql)?|redis|mariadb)://([^:]+):([^@]+)@', r'\1://\4:***MASKED***@'),
    (r'(bolt|neo4j(\+s|\+ssc)?)://([^:]+):([^@]+)@', r'\1://\3:***MASKED***@'),
    
    # AWS Keys
    (r'AKIA[0-9A-Z]{16}', 'AKIA***MASKED***'),
    (r'aws_secret_access_key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'aws_secret_access_key=***MASKED***'),
    
    # Private keys (detect BEGIN PRIVATE KEY)
    (r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----.*?-----END (?:RSA |EC |DSA )?PRIVATE KEY-----', 
     '-----BEGIN PRIVATE KEY----- ***MASKED*** -----END PRIVATE KEY-----'),
    
    # Email addresses (optionnel, dépend du contexte)
    # (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL_MASKED***'),
    
    # Credit cards (basique)
    (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '****-****-****-****'),
    
    # Phone numbers (optionnel)
    # (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '***-***-****'),
]


def sanitize_message(message: str) -> str:
    """
    Sanitize un message de log en masquant les données sensibles.
    
    Args:
        message: Message de log original
        
    Returns:
        Message sanitizé
    """
    if not isinstance(message, str):
        message = str(message)
    
    sanitized = message
    
    # Appliquer tous les patterns
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized


def sanitize_record(record: dict) -> dict:
    """
    Sanitize un record loguru complet.
    
    Args:
        record: Record loguru
        
    Returns:
        Record sanitizé
    """
    # Sanitize le message principal
    if 'message' in record:
        record['message'] = sanitize_message(record['message'])
    
    # Sanitize les extra fields
    if 'extra' in record and isinstance(record['extra'], dict):
        for key, value in record['extra'].items():
            if isinstance(value, str):
                record['extra'][key] = sanitize_message(value)
    
    return record


def sanitizing_filter(record: Any) -> bool:
    """
    Filtre Loguru pour sanitizer automatiquement tous les logs.
    
    Args:
        record: Record loguru (type Any pour compatibilité)
        
    Returns:
        True (toujours accepter le record après sanitization)
        
    Usage:
        from loguru import logger
        logger.add(sys.stdout, filter=sanitizing_filter)
    """
    try:
        # Loguru passe un objet Record, on accède au message via ['message']
        if 'message' in record:
            record['message'] = sanitize_message(str(record['message']))
    except (KeyError, TypeError, AttributeError):
        pass  # Ignorer les erreurs, ne pas bloquer le log
    
    return True


def configure_sanitized_logging():
    """
    Configure loguru avec sanitization automatique.
    À appeler au démarrage de l'application.
    """
    import sys
    
    # Supprimer les handlers par défaut
    logger.remove()
    
    # Ajouter handler avec filtre de sanitization
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        filter=sanitizing_filter,
        level="DEBUG"
    )
    
    logger.info("✅ Log sanitization configurée")


# Tests
if __name__ == "__main__":
    print("="*60)
    print("Test Log Sanitizer")
    print("="*60)
    
    test_cases = [
        'password="secret123"',
        'api_key=sk-1234567890abcdef',
        'token: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"',
        'mongodb://user:password123@localhost:27017',
        'bolt://neo4j:hopper123@localhost:7687',
        'Authorization: Bearer abc123def456',
        'X-API-Key: my-secret-key',
        'aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"',
        'AKIAIOSFODNN7EXAMPLE',
        'normal log message without secrets',
        '{"user": "john", "password": "secret", "email": "john@example.com"}',
    ]
    
    print("\n🔍 Test sanitization:")
    for i, test in enumerate(test_cases, 1):
        sanitized = sanitize_message(test)
        masked = "✅ MASKED" if sanitized != test else "⚠️  NO CHANGE"
        print(f"\n{i}. {masked}")
        print(f"   Original:  {test[:80]}")
        print(f"   Sanitized: {sanitized[:80]}")
    
    print("\n" + "="*60)
    
    # Test avec loguru
    print("\n📝 Test avec loguru:")
    configure_sanitized_logging()
    
    logger.debug("Normal message")
    logger.info("User authenticated with password=secret123")
    logger.warning("API key detected: api_key=sk-test-1234567890")
    logger.error("Connection failed: mongodb://admin:pass123@db:27017")
    
    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)
