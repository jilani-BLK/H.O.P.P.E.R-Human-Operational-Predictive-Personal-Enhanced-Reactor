"""
HOPPER - Antivirus Connector
Service FastAPI pour l'antivirus avec intégration sécurité 3 couches
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adapters.factory import get_antivirus_adapter
from adapters.base import ThreatLevel, ThreatType, ScanType

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HOPPER Antivirus Service",
    description="Service antivirus avec surveillance, détection et élimination des menaces",
    version="1.0.0"
)

# Initialize antivirus adapter
try:
    antivirus = get_antivirus_adapter()
    logger.info("Antivirus adapter initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize antivirus adapter: {e}")
    antivirus = None


# Pydantic Models

class ScanFileRequest(BaseModel):
    file_path: str
    methods: Optional[List[str]] = None


class ScanDirectoryRequest(BaseModel):
    directory_path: str
    recursive: bool = True
    extensions: Optional[List[str]] = None
    max_depth: int = -1


class QuarantineRequest(BaseModel):
    file_path: str
    reason: str = ""


class RemoveThreatRequest(BaseModel):
    file_path: str
    secure_delete: bool = True
    user_confirmed: bool = False  # DOIT être True


class RestoreRequest(BaseModel):
    quarantine_id: str


class UpdateDefinitionsRequest(BaseModel):
    force: bool = False


# Health Check

@app.get("/health")
async def health_check():
    """Vérifie l'état du service"""
    return {
        "status": "healthy",
        "service": "antivirus",
        "adapter_initialized": antivirus is not None,
        "adapter_type": type(antivirus).__name__ if antivirus else None
    }


# Scan Endpoints

@app.post("/scan/file")
async def scan_file(request: ScanFileRequest):
    """
    Scanne un fichier unique.
    
    POST /scan/file
    Body: {
        "file_path": "/path/to/file",
        "methods": ["signature", "heuristic", "behavior"]  # optional
    }
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.scan_file(request.file_path)
        
        # Log si menaces détectées
        if not result.get("clean", True):
            logger.warning(
                f"Threats detected in {request.file_path}: "
                f"{result.get('threats')}"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error scanning file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan/directory")
async def scan_directory(request: ScanDirectoryRequest):
    """
    Scanne un répertoire.
    
    POST /scan/directory
    Body: {
        "directory_path": "/path/to/dir",
        "recursive": true,
        "extensions": [".sh", ".py"],  # optional
        "max_depth": 3  # optional
    }
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.scan_directory(
            request.directory_path,
            recursive=request.recursive,
            extensions=request.extensions,
            max_depth=request.max_depth
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error scanning directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan/full")
async def full_scan(background_tasks: BackgroundTasks):
    """
    Lance un scan complet du système.
    
    POST /scan/full
    
    ⚠️ Opération longue - s'exécute en arrière-plan
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        # Start scan in background
        background_tasks.add_task(antivirus.full_scan)
        
        return {
            "success": True,
            "message": "Full scan started in background",
            "status": "scanning"
        }
        
    except Exception as e:
        logger.error(f"Error starting full scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan/quick")
async def quick_scan():
    """
    Lance un scan rapide des zones critiques.
    
    POST /scan/quick
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.quick_scan()
        return result
        
    except Exception as e:
        logger.error(f"Error during quick scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Quarantine Endpoints

@app.post("/quarantine")
async def quarantine_file(request: QuarantineRequest):
    """
    Met un fichier en quarantaine.
    
    POST /quarantine
    Body: {
        "file_path": "/path/to/suspicious/file",
        "reason": "Trojan detected"
    }
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.quarantine_file(
            request.file_path,
            reason=request.reason
        )
        
        if result.get("success"):
            logger.warning(f"File quarantined: {request.file_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error quarantining file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quarantine/list")
async def list_quarantine():
    """
    Liste tous les fichiers en quarantaine.
    
    GET /quarantine/list
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.list_quarantine()
        return {"quarantined_files": result}
        
    except Exception as e:
        logger.error(f"Error listing quarantine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quarantine/restore")
async def restore_from_quarantine(request: RestoreRequest):
    """
    Restaure un fichier de la quarantaine.
    
    POST /quarantine/restore
    Body: {
        "quarantine_id": "uuid-1234"
    }
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.restore_from_quarantine(request.quarantine_id)
        
        if result.get("success"):
            logger.info(f"File restored from quarantine: {request.quarantine_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error restoring from quarantine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Threat Management

@app.post("/threat/remove")
async def remove_threat(request: RemoveThreatRequest):
    """
    Supprime définitivement une menace.
    
    POST /threat/remove
    Body: {
        "file_path": "/var/hopper/quarantine/...",
        "secure_delete": true,
        "user_confirmed": true  # OBLIGATOIRE
    }
    
    ⚠️ OPÉRATION IRRÉVERSIBLE ⚠️
    ⚠️ REQUIERT user_confirmed=true ⚠️
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    # VÉRIFICATION CRITIQUE: user_confirmed DOIT être True
    if not request.user_confirmed:
        raise HTTPException(
            status_code=403,
            detail="User confirmation required. Set user_confirmed=true"
        )
    
    try:
        result = await antivirus.remove_threat(
            request.file_path,
            secure_delete=request.secure_delete
        )
        
        if result.get("success"):
            logger.critical(
                f"THREAT REMOVED: {request.file_path} "
                f"(user confirmed, method: {result.get('method')})"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error removing threat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Protection Status

@app.get("/status")
async def get_protection_status():
    """
    État actuel de la protection.
    
    GET /status
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.get_protection_status()
        return result
        
    except Exception as e:
        logger.error(f"Error getting protection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics")
async def get_threat_statistics():
    """
    Statistiques sur les menaces.
    
    GET /statistics
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.get_threat_statistics()
        return result
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Definitions Update

@app.post("/update")
async def update_definitions(request: UpdateDefinitionsRequest):
    """
    Met à jour les définitions de virus.
    
    POST /update
    Body: {
        "force": false
    }
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.update_definitions()
        
        if result.get("success"):
            logger.info("Virus definitions updated successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating definitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Scan History

@app.get("/history")
async def get_scan_history(limit: int = 10):
    """
    Historique des scans.
    
    GET /history?limit=10
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.get_scan_history(limit=limit)
        return {"history": result}
        
    except Exception as e:
        logger.error(f"Error getting scan history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Real-time Monitoring

@app.post("/monitor/start")
async def start_monitor():
    """
    Démarre la surveillance temps réel.
    
    POST /monitor/start
    
    🔄 Fonction en développement
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.start_realtime_monitor()
        return result
        
    except Exception as e:
        logger.error(f"Error starting monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/monitor/stop")
async def stop_monitor():
    """
    Arrête la surveillance temps réel.
    
    POST /monitor/stop
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.stop_realtime_monitor()
        return result
        
    except Exception as e:
        logger.error(f"Error stopping monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitor/status")
async def get_monitor_status():
    """
    État du monitoring temps réel.
    
    GET /monitor/status
    """
    if not antivirus:
        raise HTTPException(status_code=503, detail="Antivirus adapter not initialized")
    
    try:
        result = await antivirus.get_monitor_status()
        return result
        
    except Exception as e:
        logger.error(f"Error getting monitor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run the service
if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting HOPPER Antivirus Service on port 5007...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5007,
        log_level="info"
    )
