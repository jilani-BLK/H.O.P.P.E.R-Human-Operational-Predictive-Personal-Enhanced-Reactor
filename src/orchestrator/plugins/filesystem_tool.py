"""
FileSystem Tool - Connecteur de Référence

Implémente ToolInterface pour opérations filesystem locales.
Exemple avec risk_level et confirmation utilisateur.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from core.tool_interface import (
    ToolInterface,
    ToolManifest,
    ToolCapability,
    ToolCategory,
    AuthMethod,
    ToolExecutionContext,
    ToolExecutionResult,
    ParameterValidationError,
    ExecutionError,
    ConsentRequiredError
)
from loguru import logger


class FileSystemTool(ToolInterface):
    """
    Tool filesystem local
    
    Capacités:
    - list_directory: Liste fichiers/dossiers
    - read_file: Lit contenu fichier
    - write_file: Écrit dans fichier
    - delete_file: Supprime fichier (HIGH risk)
    - create_directory: Crée dossier
    - get_file_info: Metadata fichier
    """
    
    def __init__(self, credentials_vault=None):
        manifest = self._create_manifest()
        super().__init__(manifest, credentials_vault)
        
        # Configuration
        self.allowed_directories = [
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            "/tmp"
        ]
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    
    def _create_manifest(self) -> ToolManifest:
        """Crée manifeste filesystem"""
        
        return ToolManifest(
            tool_id="filesystem",
            name="FileSystem",
            version="1.0.0",
            category=ToolCategory.FILESYSTEM,
            description="Opérations filesystem locales sécurisées",
            long_description="""
            Accès contrôlé au système de fichiers local.
            
            Sécurité:
            - Liste blanche de répertoires autorisés
            - Limite de taille de fichiers
            - Confirmation pour opérations destructrices
            - Pas d'accès aux fichiers système
            """,
            author="HOPPER Team",
            homepage=None,
            
            capabilities=[
                ToolCapability(
                    name="list_directory",
                    display_name="Lister répertoire",
                    description="Liste contenu d'un répertoire",
                    parameters={
                        "path": {
                            "type": "string",
                            "required": True,
                            "description": "Chemin du répertoire"
                        },
                        "recursive": {
                            "type": "boolean",
                            "required": False,
                            "default": False
                        }
                    },
                    returns={"files": {"type": "list"}},
                    risk_level="safe"
                ),
                
                ToolCapability(
                    name="read_file",
                    display_name="Lire fichier",
                    description="Lit contenu d'un fichier texte",
                    parameters={
                        "path": {
                            "type": "string",
                            "required": True
                        }
                    },
                    returns={"content": {"type": "string"}},
                    risk_level="safe"
                ),
                
                ToolCapability(
                    name="write_file",
                    display_name="Écrire fichier",
                    description="Écrit ou modifie un fichier",
                    parameters={
                        "path": {"type": "string", "required": True},
                        "content": {"type": "string", "required": True},
                        "append": {"type": "boolean", "default": False}
                    },
                    returns={"success": {"type": "boolean"}},
                    risk_level="medium",
                    requires_confirmation=False
                ),
                
                ToolCapability(
                    name="delete_file",
                    display_name="Supprimer fichier",
                    description="Supprime définitivement un fichier",
                    parameters={
                        "path": {"type": "string", "required": True}
                    },
                    returns={"deleted": {"type": "boolean"}},
                    risk_level="high",
                    requires_confirmation=True  # ⚠️ Confirmation obligatoire
                ),
                
                ToolCapability(
                    name="create_directory",
                    display_name="Créer dossier",
                    description="Crée un nouveau dossier",
                    parameters={
                        "path": {"type": "string", "required": True}
                    },
                    returns={"created": {"type": "boolean"}},
                    risk_level="safe"
                ),
                
                ToolCapability(
                    name="get_file_info",
                    display_name="Info fichier",
                    description="Récupère metadata d'un fichier",
                    parameters={
                        "path": {"type": "string", "required": True}
                    },
                    returns={"info": {"type": "object"}},
                    risk_level="safe"
                )
            ],
            
            auth_method=AuthMethod.NONE,  # Accès local
            requires_internet=False,
            tags=["filesystem", "local", "files"],
            rate_limits=None
        )
    
    
    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Pas d'authentification nécessaire pour filesystem local"""
        
        self._is_connected = True
        logger.info("✅ FileSystem tool activé")
        return True
    
    
    async def disconnect(self):
        """Pas de déconnexion nécessaire"""
        
        self._is_connected = False
        logger.info("🔌 FileSystem tool désactivé")
    
    
    async def test_connection(self) -> bool:
        """Toujours connecté"""
        return True
    
    
    async def invoke(
        self,
        capability_name: str,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolExecutionResult:
        """Invoque opération filesystem"""
        
        start_time = datetime.now()
        
        try:
            # Valider paramètres
            await self.validate_parameters(capability_name, parameters)
            
            # Vérifier consentement pour opérations à risque
            capability = next(
                c for c in self.manifest.capabilities if c.name == capability_name
            )
            
            if capability.requires_confirmation and not context.has_consent:
                raise ConsentRequiredError(
                    f"Confirmation requise pour {capability_name}"
                )
            
            # Router
            if capability_name == "list_directory":
                result = await self._list_directory(parameters)
            elif capability_name == "read_file":
                result = await self._read_file(parameters)
            elif capability_name == "write_file":
                result = await self._write_file(parameters)
            elif capability_name == "delete_file":
                result = await self._delete_file(parameters)
            elif capability_name == "create_directory":
                result = await self._create_directory(parameters)
            elif capability_name == "get_file_info":
                result = await self._get_file_info(parameters)
            else:
                raise Exception(f"Capacité inconnue: {capability_name}")
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ToolExecutionResult(
                success=True,
                data=result,
                execution_time_ms=execution_time,
                tool_id=self.manifest.tool_id,
                capability_name=capability_name
            )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ToolExecutionResult(
                success=False,
                error=str(e),
                error_code=type(e).__name__,
                execution_time_ms=execution_time,
                tool_id=self.manifest.tool_id,
                capability_name=capability_name
            )
    
    
    async def validate_parameters(
        self,
        capability_name: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """Valide paramètres + sécurité filesystem"""
        
        # Validation basique
        capability = next(
            (c for c in self.manifest.capabilities if c.name == capability_name),
            None
        )
        
        if not capability:
            raise Exception(f"Capacité inconnue: {capability_name}")
        
        # Vérifier paramètres requis
        for param_name, param_schema in capability.parameters.items():
            if param_schema.get("required") and param_name not in parameters:
                raise ParameterValidationError(f"Paramètre requis: {param_name}")
        
        # Sécurité: vérifier path autorisé
        if "path" in parameters:
            path = Path(parameters["path"]).resolve()
            
            # Vérifier dans liste blanche
            is_allowed = any(
                str(path).startswith(allowed)
                for allowed in self.allowed_directories
            )
            
            if not is_allowed:
                raise ExecutionError(
                    f"Accès refusé: {path} n'est pas dans les répertoires autorisés"
                )
        
        return True
    
    
    # ============================================
    # Implémentations
    # ============================================
    
    async def _list_directory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Liste contenu répertoire"""
        
        path = Path(parameters["path"])
        recursive = parameters.get("recursive", False)
        
        if not path.exists():
            raise ExecutionError(f"Répertoire inexistant: {path}")
        
        if not path.is_dir():
            raise ExecutionError(f"Pas un répertoire: {path}")
        
        files = []
        
        if recursive:
            for item in path.rglob("*"):
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
        else:
            for item in path.iterdir():
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
        
        return {"files": files, "total": len(files)}
    
    
    async def _read_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Lit fichier texte"""
        
        path = Path(parameters["path"])
        
        if not path.exists():
            raise ExecutionError(f"Fichier inexistant: {path}")
        
        if not path.is_file():
            raise ExecutionError(f"Pas un fichier: {path}")
        
        # Vérifier taille
        size = path.stat().st_size
        if size > self.max_file_size:
            raise ExecutionError(
                f"Fichier trop volumineux: {size} bytes (max: {self.max_file_size})"
            )
        
        content = path.read_text()
        
        return {
            "content": content,
            "size": size,
            "path": str(path)
        }
    
    
    async def _write_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Écrit fichier"""
        
        path = Path(parameters["path"])
        content = parameters["content"]
        append = parameters.get("append", False)
        
        # Créer répertoire parent si nécessaire
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if append:
            with path.open("a") as f:
                f.write(content)
        else:
            path.write_text(content)
        
        return {
            "success": True,
            "path": str(path),
            "size": len(content)
        }
    
    
    async def _delete_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Supprime fichier (HIGH risk)"""
        
        path = Path(parameters["path"])
        
        if not path.exists():
            raise ExecutionError(f"Fichier inexistant: {path}")
        
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        
        logger.warning(f"🗑️ Suppression: {path}")
        
        return {
            "deleted": True,
            "path": str(path)
        }
    
    
    async def _create_directory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Crée dossier"""
        
        path = Path(parameters["path"])
        
        path.mkdir(parents=True, exist_ok=True)
        
        return {
            "created": True,
            "path": str(path)
        }
    
    
    async def _get_file_info(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère metadata fichier"""
        
        path = Path(parameters["path"])
        
        if not path.exists():
            raise ExecutionError(f"Fichier inexistant: {path}")
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "path": str(path),
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix if path.is_file() else None
        }
