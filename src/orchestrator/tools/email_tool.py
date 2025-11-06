"""
Email Tool - Connecteur email avec ToolInterface standardisé

Permet l'envoi et la lecture d'emails via pattern Tool unifié.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger


@dataclass
class EmailConfig:
    """Configuration email (SMTP + IMAP)"""
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int
    username: str
    password: str  # Devrait être récupéré via CredentialsVault
    use_tls: bool = True


class EmailTool:
    """
    Tool pour gestion emails
    
    Capacités:
    - send_email: Envoyer un email
    - read_inbox: Lire emails inbox
    - search_emails: Rechercher emails
    - mark_as_read: Marquer comme lu
    """
    
    # Métadonnées Tool (pour PluginRegistry)
    TOOL_ID = "email"
    CAPABILITIES = [
        "send_email",
        "read_inbox",
        "search_emails",
        "mark_as_read"
    ]
    REQUIRED_CREDENTIALS = ["email_username", "email_password"]
    
    def __init__(self, config: EmailConfig):
        """
        Args:
            config: Configuration SMTP/IMAP
        """
        self.config = config
        self.smtp_connection = None
        self.imap_connection = None
        logger.info(f"✅ EmailTool initialisé ({config.username})")
    
    def _connect_smtp(self):
        """Établit connexion SMTP"""
        if self.smtp_connection:
            return
        
        try:
            self.smtp_connection = smtplib.SMTP(
                self.config.smtp_host,
                self.config.smtp_port
            )
            
            if self.config.use_tls:
                self.smtp_connection.starttls()
            
            self.smtp_connection.login(
                self.config.username,
                self.config.password
            )
            
            logger.debug("📧 Connexion SMTP établie")
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion SMTP: {e}")
            raise
    
    def _connect_imap(self):
        """Établit connexion IMAP"""
        if self.imap_connection:
            return
        
        try:
            if self.config.use_tls:
                self.imap_connection = imaplib.IMAP4_SSL(
                    self.config.imap_host,
                    self.config.imap_port
                )
            else:
                self.imap_connection = imaplib.IMAP4(
                    self.config.imap_host,
                    self.config.imap_port
                )
            
            self.imap_connection.login(
                self.config.username,
                self.config.password
            )
            
            logger.debug("📧 Connexion IMAP établie")
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion IMAP: {e}")
            raise
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Envoie un email
        
        Args:
            to: Destinataire principal
            subject: Sujet
            body: Corps du message
            cc: Liste CC (optionnel)
            bcc: Liste BCC (optionnel)
            html: Si True, body est HTML
            
        Returns:
            {"success": bool, "message": str, "message_id": str}
        """
        try:
            self._connect_smtp()
            
            # Créer message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.config.username
            msg["To"] = to
            msg["Subject"] = subject
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)
            
            # Ajouter corps
            mime_type = "html" if html else "plain"
            msg.attach(MIMEText(body, mime_type))
            
            # Envoyer
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            self.smtp_connection.send_message(msg)
            
            logger.info(f"📧 Email envoyé: {to} - {subject}")
            
            return {
                "success": True,
                "message": f"Email envoyé à {to}",
                "message_id": msg["Message-ID"] if "Message-ID" in msg else None
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email: {e}")
            return {
                "success": False,
                "message": str(e),
                "message_id": None
            }
    
    async def read_inbox(
        self,
        limit: int = 10,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """
        Lit les emails de l'inbox
        
        Args:
            limit: Nombre max d'emails à lire
            unread_only: Si True, uniquement non-lus
            
        Returns:
            {"success": bool, "emails": List[Dict], "count": int}
        """
        try:
            self._connect_imap()
            
            # Sélectionner inbox
            self.imap_connection.select("INBOX")
            
            # Critère de recherche
            search_criteria = "UNSEEN" if unread_only else "ALL"
            
            # Rechercher emails
            status, messages = self.imap_connection.search(None, search_criteria)
            
            if status != "OK":
                return {
                    "success": False,
                    "emails": [],
                    "count": 0,
                    "error": "Erreur recherche IMAP"
                }
            
            email_ids = messages[0].split()
            email_ids = email_ids[-limit:]  # Derniers N emails
            
            emails = []
            for email_id in email_ids:
                status, data = self.imap_connection.fetch(email_id, "(RFC822)")
                
                if status != "OK":
                    continue
                
                # Parser email
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                emails.append({
                    "id": email_id.decode(),
                    "from": msg["From"],
                    "subject": msg["Subject"],
                    "date": msg["Date"],
                    "body": self._extract_body(msg)
                })
            
            logger.info(f"📧 {len(emails)} emails lus")
            
            return {
                "success": True,
                "emails": emails,
                "count": len(emails)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture inbox: {e}")
            return {
                "success": False,
                "emails": [],
                "count": 0,
                "error": str(e)
            }
    
    def _extract_body(self, msg) -> str:
        """Extrait le corps d'un email"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        
        return body
    
    async def search_emails(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Recherche emails par critère
        
        Args:
            query: Critère de recherche (ex: "FROM john@example.com")
            limit: Nombre max de résultats
            
        Returns:
            {"success": bool, "emails": List[Dict], "count": int}
        """
        try:
            self._connect_imap()
            self.imap_connection.select("INBOX")
            
            status, messages = self.imap_connection.search(None, query)
            
            if status != "OK":
                return {
                    "success": False,
                    "emails": [],
                    "count": 0,
                    "error": "Erreur recherche"
                }
            
            email_ids = messages[0].split()[-limit:]
            
            emails = []
            for email_id in email_ids:
                status, data = self.imap_connection.fetch(email_id, "(RFC822)")
                if status == "OK":
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    emails.append({
                        "id": email_id.decode(),
                        "from": msg["From"],
                        "subject": msg["Subject"],
                        "date": msg["Date"]
                    })
            
            return {
                "success": True,
                "emails": emails,
                "count": len(emails)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche emails: {e}")
            return {
                "success": False,
                "emails": [],
                "count": 0,
                "error": str(e)
            }
    
    def close(self):
        """Ferme les connexions"""
        if self.smtp_connection:
            self.smtp_connection.quit()
        if self.imap_connection:
            self.imap_connection.logout()
        logger.debug("📧 Connexions email fermées")


# Factory pour PluginRegistry
async def email_tool_factory(
    config: Dict[str, Any],
    credentials_vault=None
) -> EmailTool:
    """
    Crée EmailTool depuis config + CredentialsVault
    
    Args:
        config: {"smtp_host", "smtp_port", "imap_host", "imap_port"}
        credentials_vault: CredentialsVault pour récupérer password
        
    Returns:
        Instance EmailTool
    """
    # Récupérer credentials via vault
    username = config.get("username")
    password = config.get("password")
    
    if credentials_vault and username:
        try:
            password = credentials_vault.get_credential("email", username)
        except Exception as e:
            logger.warning(f"⚠️ Impossible de récupérer password via vault: {e}")
    
    email_config = EmailConfig(
        smtp_host=config.get("smtp_host", "smtp.gmail.com"),
        smtp_port=config.get("smtp_port", 587),
        imap_host=config.get("imap_host", "imap.gmail.com"),
        imap_port=config.get("imap_port", 993),
        username=username,
        password=password,
        use_tls=config.get("use_tls", True)
    )
    
    return EmailTool(email_config)
