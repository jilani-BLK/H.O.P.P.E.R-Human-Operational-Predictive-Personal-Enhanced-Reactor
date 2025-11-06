"""
Email Connector Server - Phase 3
Service de gestion des emails (IMAP + SMTP)
"""

import asyncio
import email
import email.message
import imaplib
import logging
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Email Connector Service", version="3.0.0")

# Configuration from environment
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASS = os.getenv("IMAP_PASS", "")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # Secondes

# État global
imap_client: Optional[imaplib.IMAP4_SSL] = None
last_checked_ids = set()


class EmailSummary(BaseModel):
    id: str
    from_: str
    subject: str
    date: str
    preview: str
    is_read: bool


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    reply_to: Optional[str] = None


@app.on_event("startup")
async def connect_imap():
    """Connexion IMAP au démarrage"""
    global imap_client
    
    if not IMAP_USER or not IMAP_PASS:
        logger.warning("⚠️  IMAP credentials not configured")
        return
    
    try:
        logger.info(f"Connecting to IMAP: {IMAP_HOST}:{IMAP_PORT}")
        imap_client = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        imap_client.login(IMAP_USER, IMAP_PASS)
        logger.info(f"✅ Connected as {IMAP_USER}")
    except Exception as e:
        logger.error(f"❌ IMAP connection failed: {e}")
        imap_client = None


@app.on_event("shutdown")
async def disconnect_imap():
    """Déconnexion IMAP"""
    global imap_client
    if imap_client:
        try:
            imap_client.logout()
            logger.info("✅ IMAP disconnected")
        except:
            pass


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if imap_client else "disconnected",
        "imap_host": IMAP_HOST,
        "imap_user": IMAP_USER if IMAP_USER else "not configured",
        "check_interval": CHECK_INTERVAL
    }


def _decode_header(header: str) -> str:
    """Décoder un header email"""
    if not header:
        return ""
    
    decoded = decode_header(header)
    parts = []
    
    for content, encoding in decoded:
        if isinstance(content, bytes):
            parts.append(content.decode(encoding or "utf-8", errors="ignore"))
        else:
            parts.append(content)
    
    return " ".join(parts)


def _extract_body(msg: email.message.Message) -> str:
    """Extraire le corps du message"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode("utf-8", errors="ignore")
                        break
                except:
                    pass
            elif content_type == "text/html":
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        html = payload.decode("utf-8", errors="ignore")
                        body = BeautifulSoup(html, "lxml").get_text()
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                body = payload.decode("utf-8", errors="ignore")
            else:
                body = str(payload)
        except:
            body = str(msg.get_payload())
    
    return body.strip()


@app.get("/emails/unread")
async def get_unread_emails(limit: int = 10) -> Dict:
    """
    Récupérer les emails non lus
    
    Args:
        limit: Nombre max d'emails à récupérer
    
    Returns:
        Liste d'emails avec métadonnées
    """
    if not imap_client:
        raise HTTPException(status_code=503, detail="IMAP not connected")
    
    try:
        imap_client.select("INBOX")
        status, messages = imap_client.search(None, "UNSEEN")
        
        if status != "OK":
            raise HTTPException(status_code=500, detail="IMAP search failed")
        
        msg_ids = messages[0].split()
        
        if not msg_ids:
            return {"count": 0, "emails": []}
        
        # Limiter le nombre
        msg_ids = msg_ids[-limit:]
        
        emails = []
        
        for msg_id in msg_ids:
            status, msg_data = imap_client.fetch(msg_id, "(RFC822)")
            
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            
            raw_email = msg_data[0][1]
            if not isinstance(raw_email, bytes):
                continue
                
            email_body = email.message_from_bytes(raw_email)
            
            # Extraire informations
            from_ = _decode_header(email_body.get("From", ""))
            subject = _decode_header(email_body.get("Subject", ""))
            date = email_body.get("Date", "")
            body = _extract_body(email_body)
            
            emails.append(EmailSummary(
                id=msg_id.decode(),
                from_=from_,
                subject=subject,
                date=date,
                preview=body[:200],
                is_read=False
            ))
        
        logger.info(f"✅ Retrieved {len(emails)} unread emails")
        
        return {
            "count": len(emails),
            "emails": [e.dict() for e in emails]
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/emails/all")
async def get_all_emails(limit: int = 20) -> Dict:
    """Récupérer tous les emails (lus et non lus)"""
    if not imap_client:
        raise HTTPException(status_code=503, detail="IMAP not connected")
    
    try:
        imap_client.select("INBOX")
        status, messages = imap_client.search(None, "ALL")
        
        if status != "OK":
            raise HTTPException(status_code=500, detail="IMAP search failed")
        
        msg_ids = messages[0].split()[-limit:]
        
        emails = []
        
        for msg_id in msg_ids:
            status, msg_data = imap_client.fetch(msg_id, "(RFC822)")
            
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            
            raw_email = msg_data[0][1]
            if not isinstance(raw_email, bytes):
                continue
                
            email_body = email.message_from_bytes(raw_email)
            
            from_ = _decode_header(email_body.get("From", ""))
            subject = _decode_header(email_body.get("Subject", ""))
            date = email_body.get("Date", "")
            body = _extract_body(email_body)
            
            emails.append({
                "id": msg_id.decode(),
                "from": from_,
                "subject": subject,
                "date": date,
                "preview": body[:200]
            })
        
        return {"count": len(emails), "emails": emails}
        
    except Exception as e:
        logger.error(f"❌ Error fetching emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/emails/send")
async def send_email(request: SendEmailRequest):
    """
    Envoyer un email
    
    Args:
        request: Données de l'email à envoyer
    
    Returns:
        Confirmation d'envoi
    """
    if not IMAP_USER or not IMAP_PASS:
        raise HTTPException(status_code=503, detail="SMTP credentials not configured")
    
    try:
        # Créer message
        msg = MIMEMultipart()
        msg["From"] = IMAP_USER
        msg["To"] = request.to
        msg["Subject"] = request.subject
        
        if request.reply_to:
            msg["In-Reply-To"] = request.reply_to
            msg["References"] = request.reply_to
        
        msg.attach(MIMEText(request.body, "plain", "utf-8"))
        
        # Envoyer via SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(IMAP_USER, IMAP_PASS)
            server.send_message(msg)
        
        logger.info(f"✅ Email sent to {request.to}")
        
        return {
            "success": True,
            "to": request.to,
            "subject": request.subject
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/emails/mark-read")
async def mark_as_read(email_id: str):
    """Marquer un email comme lu"""
    if not imap_client:
        raise HTTPException(status_code=503, detail="IMAP not connected")
    
    try:
        imap_client.select("INBOX")
        imap_client.store(email_id, "+FLAGS", "\\Seen")
        
        logger.info(f"✅ Email {email_id} marked as read")
        
        return {"success": True, "email_id": email_id}
        
    except Exception as e:
        logger.error(f"❌ Error marking email as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5008)
