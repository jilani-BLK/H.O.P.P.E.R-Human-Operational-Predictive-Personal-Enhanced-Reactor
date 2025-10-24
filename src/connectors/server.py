# HOPPER - Connectors Service
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger
from base import ConnectorRegistry, ConnectorConfig
from spotify import SpotifyConnector
from local_system import LocalSystemConnector

CONNECTORS_PORT = int(os.getenv("CONNECTORS_PORT", "5006"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logger.remove()
logger.add("../../data/logs/connectors.log", rotation="10 MB", retention="30 days", level=LOG_LEVEL)
logger.add(lambda msg: print(msg, end=""), level=LOG_LEVEL, colorize=True)

registry = ConnectorRegistry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Démarrage Connectors Service")
    await initialize_connectors()
    await registry.connect_all()
    logger.success("✅ Connectors Service prêt")
    yield
    logger.info("🛑 Arrêt Connectors Service")
    await registry.disconnect_all()

app = FastAPI(title="HOPPER Connectors", lifespan=lifespan)

class ExecuteRequest(BaseModel):
    connector: str
    action: str
    params: Dict[str, Any] = {}
    user_id: str = "default"  # Identification utilisateur

async def initialize_connectors():
    logger.info("🔌 Init connecteurs...")
    
    # Spotify
    spotify_config = ConnectorConfig(
        name="spotify",
        enabled=True,
        config={"client_id": os.getenv("SPOTIFY_CLIENT_ID"), "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET")}
    )
    spotify = SpotifyConnector(spotify_config)
    registry.register(spotify)
    
    # Système Local - LE PLUS IMPORTANT
    local_config = ConnectorConfig(
        name="local_system",
        enabled=True,
        config={}
    )
    local_system = LocalSystemConnector(local_config)
    registry.register(local_system)
    
    logger.success(f"✅ {len(registry.list_all())} connecteurs initialisés")

@app.get("/health")
async def health():
    enabled = registry.list_enabled()
    connected = [n for n in enabled if registry.get(n) and registry.get(n).connected]
    return {"status": "healthy", "service": "connectors", "connectors": {"total": len(registry.list_all()), "enabled": len(enabled), "connected": len(connected)}}

@app.get("/connectors")
async def list_connectors():
    connectors_info = []
    for name in registry.list_all():
        connector = registry.get(name)
        if connector:
            status = connector.get_status()
            connectors_info.append({"name": status.name, "enabled": status.enabled, "connected": status.connected, "capabilities_count": len(status.capabilities), "last_error": status.last_error})
    return {"connectors": connectors_info}

@app.get("/connectors/{connector_name}")
async def get_connector_details(connector_name: str):
    connector = registry.get(connector_name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connecteur '{connector_name}' non trouvé")
    status = connector.get_status()
    return {"name": status.name, "enabled": status.enabled, "connected": status.connected, "last_error": status.last_error, "capabilities": [{"name": cap.name, "description": cap.description, "parameters": cap.parameters} for cap in status.capabilities]}

@app.get("/capabilities")
async def get_all_capabilities():
    capabilities = registry.get_all_capabilities()
    formatted = {}
    for connector_name, caps in capabilities.items():
        formatted[connector_name] = [{"name": cap.name, "description": cap.description, "parameters": cap.parameters} for cap in caps]
    return {"capabilities": formatted}

@app.post("/execute")
async def execute_action(request: ExecuteRequest):
    logger.info(f"📥 Exécution: {request.connector}.{request.action} (user: {request.user_id})")
    connector = registry.get(request.connector)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connecteur '{request.connector}' non trouvé")
    if not connector.connected:
        raise HTTPException(status_code=503, detail=f"Connecteur '{request.connector}' non connecté")
    try:
        # Exécuter l'action (user_id peut être utilisé dans les logs si nécessaire)
        result = await connector.execute(request.action, request.params)
        
        logger.success(f"✅ Action {request.action} exécutée")
        return {"success": result.get("success", True), "data": result.get("data"), "error": result.get("error")}
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/connectors/{connector_name}/connect")
async def connect_connector(connector_name: str):
    connector = registry.get(connector_name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connecteur '{connector_name}' non trouvé")
    try:
        success = await connector.connect()
        return {"success": success, "message": f"Connecteur '{connector_name}' {'connecté' if success else 'échec connexion'}"}
    except Exception as e:
        logger.error(f"❌ Erreur connexion {connector_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/security/audit")
async def get_audit(user_id: Optional[str] = None, limit: int = 100):
    """Consulter l'audit de sécurité"""
    from src.security import permission_manager
    if user_id:
        report = permission_manager.get_security_report(user_id)
        recent = permission_manager.audit.get_recent_actions(limit)
        user_actions = [a for a in recent if a["user_id"] == user_id]
        return {"user_id": user_id, "stats": report.get("stats", {}), "recent_actions": user_actions}
    else:
        report = permission_manager.get_security_report()
        recent = permission_manager.audit.get_recent_actions(limit)
        return {"global_stats": report, "recent_actions": recent}

@app.post("/connectors/{connector_name}/disconnect")
async def disconnect_connector(connector_name: str):
    connector = registry.get(connector_name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connecteur '{connector_name}' non trouvé")
    try:
        success = await connector.disconnect()
        return {"success": success, "message": f"Connecteur '{connector_name}' déconnecté"}
    except Exception as e:
        logger.error(f"❌ Erreur déconnexion {connector_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"🚀 Démarrage sur port {CONNECTORS_PORT}")
    uvicorn.run("server:app", host="0.0.0.0", port=CONNECTORS_PORT, reload=True, log_level=LOG_LEVEL.lower())
