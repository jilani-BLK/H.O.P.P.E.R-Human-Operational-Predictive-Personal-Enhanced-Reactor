"""
IMAP Email Tool - Connecteur de Référence

Implémente ToolInterface pour accès email via IMAP.
Exemple d'architecture modulaire et sécurisée.
"""

import asyncio
import imaplib
import email
from email.header import decode_header
from typing import Dict, Any, List
from datetime import datetime

from core.tool_interface import (
    ToolInterface,
    ToolManifest,
    ToolCapability,
    ToolCategory,
    AuthMethod,
    ToolExecutionContext,
    ToolExecutionResult,
    AuthenticationError,
    ConnectionError as ToolConnectionError,
    CapabilityNotFoundError,
    ParameterValidationError
)
from loguru import logger


class IMAPEmailTool(ToolInterface):
    """
    Tool IMAP pour lecture/envoi d'emails
    
    Capacités:
    - list_folders: Liste dossiers IMAP
    - list_emails: Liste emails d'un dossier
    - read_email: Lit contenu d'un email
    - search_emails: Recherche par critères
    - mark_as_read: Marque comme lu
    """
    
    def __init__(self, credentials_vault=None):
        # Définir manifeste
        manifest = self._create_manifest()
        super().__init__(manifest, credentials_vault)
        
        # État connexion
        self.imap_connection = None
        self.current_folder = None
    
    
    def _create_manifest(self) -> ToolManifest:
        """Crée le manifeste déclaratif du tool"""
        
        return ToolManifest(
            tool_id="imap_email",
            name="Email (IMAP)",
            version="1.0.0",
            category=ToolCategory.COMMUNICATION,
            description="Accès email via protocole IMAP",
            long_description="""
            Connecteur IMAP pour lecture et gestion d'emails.
            
            Supporte:
            - Gmail, Outlook, iCloud, serveurs IMAP standards
            - SSL/TLS
            - Recherche avancée
            - Gestion des dossiers
            """,
            author="HOPPER Team",
            homepage=None,
            
            # Capacités
            capabilities=[
                ToolCapability(
                    name="list_folders",
                    display_name="Lister dossiers",
                    description="Liste tous les dossiers IMAP disponibles",
                    parameters={},
                    returns={"folders": {"type": "list", "description": "Liste des dossiers"}},
                    risk_level="safe"
                ),
                
                ToolCapability(
                    name="list_emails",
                    display_name="Lister emails",
                    description="Liste les emails d'un dossier",
                    parameters={
                        "folder": {
                            "type": "string",
                            "required": False,
                            "default": "INBOX",
                            "description": "Dossier à lire"
                        },
                        "limit": {
                            "type": "integer",
                            "required": False,
                            "default": 20,
                            "description": "Nombre d'emails max"
                        }
                    },
                    returns={"emails": {"type": "list"}},
                    risk_level="safe"
                ),
                
                ToolCapability(
                    name="read_email",
                    display_name="Lire email",
                    description="Lit le contenu complet d'un email",
                    parameters={
                        "email_id": {
                            "type": "string",
                            "required": True,
                            "description": "ID de l'email"
                        }
                    },
                    returns={"email": {"type": "object"}},
                    risk_level="safe"
                ),
                
                ToolCapability(
                    name="search_emails",
                    display_name="Rechercher emails",
                    description="Recherche emails par critères",
                    parameters={
                        "query": {
                            "type": "string",
                            "required": True,
                            "description": "Requête de recherche"
                        },
                        "folder": {
                            "type": "string",
                            "required": False,
                            "default": "INBOX"
                        }
                    },
                    returns={"emails": {"type": "list"}},
                    risk_level="safe"
                )
            ],
            
            # Authentification
            auth_method=AuthMethod.BASIC,
            credentials_schema={
                "host": {
                    "type": "string",
                    "required": True,
                    "description": "Serveur IMAP (ex: imap.gmail.com)",
                    "examples": ["imap.gmail.com", "outlook.office365.com"]
                },
                "port": {
                    "type": "integer",
                    "required": False,
                    "default": 993,
                    "description": "Port IMAP SSL"
                },
                "username": {
                    "type": "string",
                    "required": True,
                    "description": "Email ou nom d'utilisateur"
                },
                "password": {
                    "type": "string",
                    "required": True,
                    "secret": True,
                    "description": "Mot de passe ou mot de passe d'application"
                }
            },
            
            # Configuration
            config_schema={
                "use_ssl": {
                    "type": "boolean",
                    "default": True
                },
                "timeout": {
                    "type": "integer",
                    "default": 30
                }
            },
            
            requires_internet=True,
            tags=["email", "imap", "communication"],
            rate_limits=None
        )
    
    
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Établit connexion IMAP"""
        
        try:
            host = credentials.get("host")
            port = credentials.get("port", 993)
            username = credentials.get("username")
            password = credentials.get("password")
            
            if not all([host, username, password]):
                raise AuthenticationError("Credentials incomplets")
            
            # Type assertions pour Pylance
            assert isinstance(host, str)
            assert isinstance(username, str)
            assert isinstance(password, str)
            
            # Connexion IMAP SSL
            self.imap_connection = imaplib.IMAP4_SSL(host, port)
            
            # Login
            self.imap_connection.login(username, password)
            
            self._credentials = credentials
            self._is_connected = True
            
            logger.info(f"✅ Connexion IMAP établie: {username}@{host}")
            
            return True
        
        except imaplib.IMAP4.error as e:
            raise AuthenticationError(f"Échec authentification IMAP: {e}")
        except Exception as e:
            raise ToolConnectionError(f"Erreur connexion IMAP: {e}")
    
    
    async def disconnect(self):
        """Ferme connexion IMAP"""
        
        if self.imap_connection:
            try:
                self.imap_connection.logout()
            except:
                pass
            
            self.imap_connection = None
            self._is_connected = False
            
            logger.info("🔌 Connexion IMAP fermée")
    
    
    async def test_connection(self) -> bool:
        """Teste si connexion IMAP active"""
        
        if not self.imap_connection:
            return False
        
        try:
            self.imap_connection.noop()
            return True
        except:
            return False
    
    
    async def invoke(
        self,
        capability_name: str,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolExecutionResult:
        """Invoque une capacité IMAP"""
        
        start_time = datetime.now()
        
        try:
            # Vérifier connexion
            if not await self.test_connection():
                raise ToolConnectionError("Connexion IMAP inactive")
            
            # Router vers méthode appropriée
            if capability_name == "list_folders":
                result = await self._list_folders()
            elif capability_name == "list_emails":
                result = await self._list_emails(parameters)
            elif capability_name == "read_email":
                result = await self._read_email(parameters)
            elif capability_name == "search_emails":
                result = await self._search_emails(parameters)
            else:
                raise CapabilityNotFoundError(f"Capacité inconnue: {capability_name}")
            
            # Calcul temps d'exécution
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
        """Valide paramètres avant exécution"""
        
        # Trouver capacité
        capability = next(
            (c for c in self.manifest.capabilities if c.name == capability_name),
            None
        )
        
        if not capability:
            raise CapabilityNotFoundError(f"Capacité inconnue: {capability_name}")
        
        # Vérifier paramètres requis
        for param_name, param_schema in capability.parameters.items():
            if param_schema.get("required") and param_name not in parameters:
                raise ParameterValidationError(
                    f"Paramètre requis manquant: {param_name}"
                )
        
        return True
    
    
    # ============================================
    # Implémentations des capacités
    # ============================================
    
    async def _list_folders(self) -> Dict[str, Any]:
        """Liste dossiers IMAP"""
        
        status, folders = self.imap_connection.list()
        
        if status != "OK":
            raise Exception(f"Erreur IMAP: {status}")
        
        folder_names = []
        for folder in folders:
            # Parser format IMAP
            if isinstance(folder, bytes):
                parts = folder.decode().split('"')
                if len(parts) >= 3:
                    folder_names.append(parts[-2])
        
        return {"folders": folder_names}
    
    
    async def _list_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Liste emails d'un dossier"""
        
        folder = parameters.get("folder", "INBOX")
        limit = parameters.get("limit", 20)
        
        # Sélectionner dossier
        self.imap_connection.select(folder)
        
        # Rechercher tous emails
        status, messages = self.imap_connection.search(None, "ALL")
        
        if status != "OK":
            raise Exception(f"Erreur recherche IMAP: {status}")
        
        # Récupérer IDs
        email_ids = messages[0].split()
        email_ids = email_ids[-limit:]  # Derniers N emails
        
        emails = []
        for email_id in email_ids:
            # Récupérer headers
            status, msg_data = self.imap_connection.fetch(email_id, "(RFC822.HEADER)")
            
            if status == "OK" and msg_data and len(msg_data) > 0:
                raw_msg = msg_data[0][1]
                if isinstance(raw_msg, bytes):
                    msg = email.message_from_bytes(raw_msg)
                    
                    emails.append({
                        "id": email_id.decode(),
                        "from": msg.get("From"),
                        "subject": self._decode_header(msg.get("Subject") or ""),
                        "date": msg.get("Date")
                    })
        
        return {"emails": emails, "total": len(email_ids)}
    
    
    async def _read_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Lit contenu complet d'un email"""
        
        email_id = parameters.get("email_id")
        
        if not email_id:
            raise ParameterValidationError("email_id requis")
        
        # Récupérer email complet
        status, msg_data = self.imap_connection.fetch(email_id, "(RFC822)")
        
        if status != "OK" or not msg_data or len(msg_data) == 0:
            raise Exception(f"Erreur fetch IMAP: {status}")
        
        raw_msg = msg_data[0][1]
        if not isinstance(raw_msg, bytes):
            raise Exception("Format email invalide")
            
        msg = email.message_from_bytes(raw_msg)
        
        # Extraire body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode()
                    break
        else:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                body = payload.decode()
        
        return {
            "id": email_id,
            "from": msg.get("From"),
            "to": msg.get("To"),
            "subject": self._decode_header(msg.get("Subject") or ""),
            "date": msg.get("Date"),
            "body": body
        }
    
    
    async def _search_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Recherche emails par critères"""
        
        query = parameters.get("query", "")
        folder = parameters.get("folder", "INBOX")
        
        self.imap_connection.select(folder)
        
        # Recherche IMAP (simple: SUBJECT)
        status, messages = self.imap_connection.search(None, f'SUBJECT "{query}"')
        
        if status != "OK":
            raise Exception(f"Erreur recherche: {status}")
        
        email_ids = messages[0].split()
        
        return {
            "query": query,
            "results_count": len(email_ids),
            "email_ids": [eid.decode() for eid in email_ids]
        }
    
    
    def _decode_header(self, header: str) -> str:
        """Décode header MIME"""
        
        if not header:
            return ""
        
        decoded = decode_header(header)
        parts = []
        
        for content, encoding in decoded:
            if isinstance(content, bytes):
                parts.append(content.decode(encoding or "utf-8"))
            else:
                parts.append(content)
        
        return " ".join(parts)
