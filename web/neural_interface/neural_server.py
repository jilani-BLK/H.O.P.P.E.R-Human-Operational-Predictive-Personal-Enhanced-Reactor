"""
HOPPER - Neural Interface Server
Serveur WebSocket pour streaming temps réel de l'activité neuronale
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Set, Dict, Any, Optional
from loguru import logger
import asyncio
import json
from datetime import datetime
from pathlib import Path

app = FastAPI(
    title="HOPPER Neural Interface",
    description="Visualisation temps réel du réseau neural de HOPPER"
)

# Clients WebSocket connectés
active_connections: Set[WebSocket] = set()

# Statistiques globales
stats = {
    "events_sent": 0,
    "connections_total": 0,
    "start_time": datetime.now(),
    "neurons": {"total": 50, "active": 0},
    "connections": {"total": 0, "active": 0}
}


class ConnectionManager:
    """Gestionnaire de connexions WebSocket"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        stats["connections_total"] += 1
        logger.info(f"✅ Client connecté (total: {len(self.active_connections)})")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"❌ Client déconnecté (total: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Erreur envoi message: {e}")
    
    async def broadcast(self, message: dict):
        """Envoie un message à tous les clients connectés"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                stats["events_sent"] += 1
            except Exception as e:
                logger.error(f"Erreur broadcast: {e}")
                disconnected.add(connection)
        
        # Nettoyer les connexions mortes
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@app.get("/")
async def get_interface():
    """Page d'accueil - Interface neuronale"""
    interface_path = Path(__file__).parent / "index.html"
    
    if interface_path.exists():
        return HTMLResponse(content=interface_path.read_text())
    else:
        return HTMLResponse(
            content="""
            <html>
                <body>
                    <h1>HOPPER Neural Interface</h1>
                    <p>WebSocket endpoint: ws://localhost:5050/ws/neural</p>
                    <p>Interface files not found. Place index.html in the same directory.</p>
                </body>
            </html>
            """
        )


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "stats": stats
    }


@app.websocket("/ws/neural")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint pour streaming neural
    
    Messages envoyés:
    - neural_activity: Activité neuronale (events orchestrator)
    - service_event: Événements services
    - voice_activity: Activité vocale (speaking/listening)
    - stats: Statistiques temps réel
    """
    await manager.connect(websocket)
    
    try:
        # Envoyer message de bienvenue
        await manager.send_personal_message({
            "type": "welcome",
            "payload": {
                "message": "Connecté au réseau neural HOPPER",
                "stats": stats
            }
        }, websocket)
        
        # Boucle de réception
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Traiter les messages du client
            await handle_client_message(message, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket: {e}")
        manager.disconnect(websocket)


async def handle_client_message(message: dict, websocket: WebSocket):
    """Traite les messages du client"""
    msg_type = message.get("type")
    
    if msg_type == "ping":
        # Répondre au ping
        await manager.send_personal_message({
            "type": "pong",
            "payload": {
                "latency": 0,
                "timestamp": datetime.now().isoformat()
            }
        }, websocket)
    
    elif msg_type == "client_stats":
        # Mettre à jour les stats
        payload = message.get("payload", {})
        if "neurons" in payload:
            stats["neurons"]["active"] = payload["neurons"]
        if "connections" in payload:
            stats["connections"]["active"] = payload["connections"]


# ============================================
# API pour envoyer des événements
# ============================================

@app.post("/api/neural/event")
async def send_neural_event(event: dict):
    """
    API pour envoyer des événements neuraux
    
    Body:
    {
        "type": "neural_activity",
        "payload": {
            "event_type": "stt|llm|tts|dispatch|service",
            "intensity": 0.0-1.0,
            "metadata": {...}
        }
    }
    """
    await manager.broadcast(event)
    return {"status": "sent", "connections": len(manager.active_connections)}


@app.post("/api/neural/voice")
async def send_voice_activity(
    speaking: bool,
    text: Optional[str] = None,
    duration: Optional[float] = None
):
    """
    Signale une activité vocale
    
    Args:
        speaking: True si HOPPER parle
        text: Texte prononcé (optionnel)
        duration: Durée en secondes (optionnel)
    """
    await manager.broadcast({
        "type": "voice_activity",
        "payload": {
            "speaking": speaking,
            "text": text,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    return {"status": "sent"}


@app.post("/api/neural/service")
async def send_service_event(
    service: str,
    status: str,
    duration: Optional[float] = None
):
    """
    Signale un événement de service
    
    Args:
        service: Nom du service (stt, llm, tts, etc.)
        status: Status (active, completed, error)
        duration: Durée d'exécution (optionnel)
    """
    await manager.broadcast({
        "type": "service_event",
        "payload": {
            "service": service,
            "status": status,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    return {"status": "sent"}


# ============================================
# Tâche de background pour stats périodiques
# ============================================

async def broadcast_stats():
    """Envoie les stats périodiquement"""
    while True:
        await asyncio.sleep(2)
        
        if manager.active_connections:
            await manager.broadcast({
                "type": "stats",
                "payload": {
                    "neurons": stats["neurons"],
                    "connections": stats["connections"],
                    "events_sent": stats["events_sent"],
                    "active_clients": len(manager.active_connections)
                }
            })


@app.on_event("startup")
async def startup_event():
    """Démarrage du serveur"""
    logger.info("🚀 HOPPER Neural Interface Server started")
    logger.info("📡 WebSocket: ws://localhost:5050/ws/neural")
    logger.info("🌐 Interface: http://localhost:5050/")
    
    # Lancer tâche de stats
    asyncio.create_task(broadcast_stats())


@app.on_event("shutdown")
async def shutdown_event():
    """Arrêt du serveur"""
    logger.info("🛑 HOPPER Neural Interface Server stopping")
    
    # Fermer toutes les connexions
    for connection in list(manager.active_connections):
        try:
            await connection.close()
        except:
            pass


# Servir les fichiers statiques
try:
    web_path = Path(__file__).parent
    if (web_path / "neural_visualization.js").exists():
        app.mount("/", StaticFiles(directory=str(web_path), html=True), name="static")
        logger.info(f"✅ Static files mounted from {web_path}")
except Exception as e:
    logger.warning(f"⚠️ Could not mount static files: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "neural_server:app",
        host="0.0.0.0",
        port=5050,
        reload=True,
        log_level="info"
    )
