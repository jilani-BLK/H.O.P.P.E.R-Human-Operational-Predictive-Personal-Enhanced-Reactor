"""
HOPPER - Phase 5 Routes
Routes API pour contrôle système local via Connectors

Endpoints:
- POST /system/apps/open - Ouvrir application
- POST /system/apps/close - Fermer application
- GET /system/apps - Lister applications
- POST /system/files/read - Lire fichier
- GET /system/files/list - Lister répertoire
- POST /system/files/search - Rechercher fichiers
- GET /system/info - Informations système
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger

from connectors_client import get_connectors_client


router = APIRouter(prefix="/api/v1/system", tags=["system"])


# === Models ===

class OpenAppRequest(BaseModel):
    app_name: str
    user_id: str = "default"


class CloseAppRequest(BaseModel):
    app_name: str
    user_id: str = "default"


class ReadFileRequest(BaseModel):
    file_path: str
    max_lines: int = 50
    user_id: str = "default"


class ListDirectoryRequest(BaseModel):
    path: str
    user_id: str = "default"


class SearchFilesRequest(BaseModel):
    pattern: str
    directory: str = "."
    user_id: str = "default"


class ExecuteScriptRequest(BaseModel):
    script: str
    user_id: str = "default"


# === Routes Applications ===

@router.post("/apps/open")
async def open_application(request: OpenAppRequest):
    """
    Ouvrir une application
    
    Exemple:
    ```json
    {
        "app_name": "Safari",
        "user_id": "john"
    }
    ```
    """
    client = get_connectors_client()
    result = await client.open_app(request.app_name, request.user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


@router.post("/apps/close")
async def close_application(request: CloseAppRequest):
    """Fermer une application"""
    client = get_connectors_client()
    result = await client.close_app(request.app_name, request.user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


@router.get("/apps")
async def list_applications(user_id: str = "default"):
    """Lister toutes les applications installées"""
    client = get_connectors_client()
    result = await client.list_apps(user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


# === Routes Fichiers ===

@router.post("/files/read")
async def read_file(request: ReadFileRequest):
    """
    Lire le contenu d'un fichier
    
    Exemple:
    ```json
    {
        "file_path": "/tmp/test.txt",
        "max_lines": 50,
        "user_id": "john"
    }
    ```
    """
    client = get_connectors_client()
    result = await client.read_file(
        request.file_path,
        request.max_lines,
        request.user_id
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


@router.post("/files/list")
async def list_directory(request: ListDirectoryRequest):
    """Lister le contenu d'un répertoire"""
    client = get_connectors_client()
    result = await client.list_directory(request.path, request.user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


@router.post("/files/search")
async def search_files(request: SearchFilesRequest):
    """
    Rechercher des fichiers par pattern
    
    Exemple:
    ```json
    {
        "pattern": "*.py",
        "directory": "/app",
        "user_id": "john"
    }
    ```
    """
    client = get_connectors_client()
    result = await client.find_files(
        request.pattern,
        request.directory,
        request.user_id
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


@router.get("/files/info")
async def get_file_info(file_path: str, user_id: str = "default"):
    """Obtenir les métadonnées d'un fichier"""
    client = get_connectors_client()
    result = await client.get_file_info(file_path, user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


# === Routes Système ===

@router.get("/info")
async def get_system_info(user_id: str = "default"):
    """Obtenir les informations système (CPU, RAM, disque, etc.)"""
    client = get_connectors_client()
    result = await client.get_system_info(user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


@router.post("/script")
async def execute_script(request: ExecuteScriptRequest):
    """
    Exécuter un script/commande système
    
    ⚠️ DANGER: Cette action nécessite des permissions élevées
    
    Exemple:
    ```json
    {
        "script": "echo 'Hello HOPPER'",
        "user_id": "admin"
    }
    ```
    """
    client = get_connectors_client()
    result = await client.execute_script(request.script, request.user_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    
    return result


# === Routes Connectors ===

@router.get("/connectors")
async def list_connectors():
    """Lister tous les connectors disponibles"""
    client = get_connectors_client()
    result = await client.list_connectors()
    
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    
    return result


@router.get("/connectors/capabilities")
async def get_capabilities(connector_name: Optional[str] = None):
    """Obtenir les capacités d'un ou tous les connectors"""
    client = get_connectors_client()
    result = await client.get_capabilities(connector_name)
    
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    
    return result


@router.get("/health")
async def health_check():
    """Vérifier l'état du service connectors"""
    client = get_connectors_client()
    result = await client.health_check()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("error"))
    
    return result
