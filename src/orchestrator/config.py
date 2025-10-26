"""
Configuration de l'orchestrateur
"""

try:
    from pydantic_settings import BaseSettings  # type: ignore[import-untyped]
except ImportError:
    from pydantic import BaseSettings  # type: ignore[attr-defined,import-not-found]


class Settings(BaseSettings):
    """Paramètres de configuration"""
    
    # Service
    ORCHESTRATOR_PORT: int = 5000
    ORCHESTRATOR_HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    
    # URLs des services (utiliser noms de containers Docker)
    LLM_SERVICE_URL: str = "http://hopper-llm:5001"
    SYSTEM_EXECUTOR_URL: str = "http://hopper-system-executor:5002"
    STT_SERVICE_URL: str = "http://hopper-stt:5003"
    TTS_SERVICE_URL: str = "http://hopper-tts:5004"
    AUTH_SERVICE_URL: str = "http://hopper-auth:5005"
    CONNECTORS_URL: str = "http://hopper-connectors:5006"
    
    # Base de données
    DB_PATH: str = "/data/hopper.db"
    VECTOR_DB_PATH: str = "/data/vector_store"
    
    # Sécurité
    ENABLE_VOICE_AUTH: bool = True
    ENABLE_FACE_AUTH: bool = False
    REQUIRE_2FA_FOR_CRITICAL: bool = True
    
    # Mode
    OFFLINE_MODE: bool = False
    DEBUG_MODE: bool = False
    DEV_MODE: bool = False
    
    # Timeouts
    SERVICE_TIMEOUT: int = 30
    LLM_TIMEOUT: int = 60
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore les variables .env non déclarées
    }


settings = Settings()
