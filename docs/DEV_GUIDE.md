# 🔧 HOPPER - Guide Développeur

> Guide complet pour contribuer, étendre et personnaliser HOPPER

---

## 🎯 Objectif

Ce guide vous permettra de:
- 🏗️ Comprendre l'architecture de HOPPER
- 🔌 Ajouter de nouveaux connecteurs
- 🧩 Étendre les capabilities du système
- 🧪 Tester vos modifications
- 📦 Contribuer au projet

---

## 📑 Table des Matières

1. [Architecture](#architecture)
2. [Setup Développement](#setup-développement)
3. [Ajouter un Connecteur](#ajouter-un-connecteur)
4. [Ajouter une Capability](#ajouter-une-capability)
5. [Patterns NLP](#patterns-nlp)
6. [Tests](#tests)
7. [Documentation](#documentation)
8. [Contribution](#contribution)

---

## 🏗️ Architecture

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    👤 UTILISATEUR                           │
│                         │                                   │
│                         ▼                                   │
│              🎤 INPUT VOCAL (micro)                         │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │  STT SERVICE (5001)  │                       │
│              │  Whisper             │                       │
│              └──────────┬───────────┘                       │
│                         │                                   │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │  ORCHESTRATOR (8000) │◄───┐                 │
│              │  - Dispatcher        │    │                 │
│              │  - Context Manager   │    │                 │
│              │  - Security          │    │                 │
│              └──────────┬───────────┘    │                 │
│                         │                │                 │
│          ┌──────────────┼────────────┐   │                 │
│          │              │            │   │                 │
│          ▼              ▼            ▼   │                 │
│  ┌───────────┐  ┌────────────┐  ┌──────────────┐          │
│  │ LLM (5002)│  │ CONNECTORS │  │ NEO4J (7474) │          │
│  │ Llama 3.2 │  │            │  │ Knowledge    │          │
│  └───────────┘  └──────┬─────┘  └──────────────┘          │
│                        │                                   │
│          ┌─────────────┼──────────────┐                    │
│          │             │              │                    │
│          ▼             ▼              ▼                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │LocalSys  │  │Antivirus │  │ Spotify  │                 │
│  │(5005)    │  │(5007)    │  │ (5006)   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
               ┌──────────────────────┐
               │  TTS SERVICE (5003)  │
               │  CoquiTTS            │
               └──────────┬───────────┘
                          │
                          ▼
                  🔊 OUTPUT VOCAL
```

### Composants Clés

| Composant | Port | Rôle | Technologie |
|-----------|------|------|-------------|
| **Orchestrator** | 8000 | Chef d'orchestre | FastAPI + Python |
| **STT** | 5001 | Speech-to-Text | Whisper |
| **LLM** | 5002 | Compréhension | Llama 3.2 |
| **TTS** | 5003 | Text-to-Speech | CoquiTTS |
| **Neo4j** | 7474 | Graphe connaissances | Neo4j |
| **LocalSystem** | 5005 | Contrôle système | Python |
| **Spotify** | 5006 | Musique | Spotipy |
| **Antivirus** | 5007 | Protection | ClamAV |

---

## 🛠️ Setup Développement

### 1. Cloner & Installer

```bash
git clone https://github.com/votre-repo/HOPPER.git
cd HOPPER
./scripts/setup.sh
```

### 2. Environnement Virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Outils dev
```

### 3. Configuration IDE

#### VS Code

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

#### PyCharm

- Interpreter: `.venv/bin/python`
- Code Style: Black
- Test Runner: pytest

### 4. Variables d'Environnement

`.env`:

```bash
# Développement
DEBUG=true
LOG_LEVEL=DEBUG

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=hopper123

# Services
ORCHESTRATOR_HOST=localhost
ORCHESTRATOR_PORT=8000

# Spotify (optionnel)
SPOTIFY_CLIENT_ID=votre_id
SPOTIFY_CLIENT_SECRET=votre_secret
```

---

## 🔌 Ajouter un Connecteur

### Étape 1: Structure

```bash
# Créer la structure
mkdir -p src/connectors/email
touch src/connectors/email/__init__.py
touch src/connectors/email/connector.py
touch src/connectors/email/config.py
```

### Étape 2: Définir le Connecteur

`src/connectors/email/connector.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any

app = FastAPI(title="Email Connector", version="1.0.0")

# ==================== CONFIGURATION ====================

class EmailConfig:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = "votre@email.com"
    EMAIL_PASSWORD = "votre_password"

# ==================== MODÈLES PYDANTIC ====================

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str

class EmailResponse(BaseModel):
    success: bool
    message: str
    email_id: str = None

# ==================== CAPABILITIES ====================

CAPABILITIES = {
    "send_email": {
        "description": "Envoyer un email",
        "parameters": ["to", "subject", "body"],
        "risk_level": "LOW"
    },
    "check_inbox": {
        "description": "Vérifier la boîte de réception",
        "parameters": [],
        "risk_level": "SAFE"
    }
}

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "email",
        "version": "1.0.0"
    }

@app.get("/capabilities")
async def get_capabilities():
    """Retourne les capabilities du connecteur"""
    return CAPABILITIES

# ==================== SEND EMAIL ====================

@app.post("/send", response_model=EmailResponse)
async def send_email(request: SendEmailRequest):
    """Envoyer un email"""
    try:
        # Créer le message
        msg = MIMEText(request.body)
        msg['Subject'] = request.subject
        msg['From'] = EmailConfig.EMAIL_ADDRESS
        msg['To'] = request.to
        
        # Connexion SMTP
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            server.starttls()
            server.login(EmailConfig.EMAIL_ADDRESS, EmailConfig.EMAIL_PASSWORD)
            server.send_message(msg)
        
        return EmailResponse(
            success=True,
            message=f"Email envoyé à {request.to}",
            email_id=f"email_{int(time.time())}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CHECK INBOX ====================

@app.get("/inbox")
async def check_inbox(limit: int = 10):
    """Vérifier les derniers emails"""
    try:
        # Se connecter à IMAP
        import imaplib
        
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EmailConfig.EMAIL_ADDRESS, EmailConfig.EMAIL_PASSWORD)
        mail.select("inbox")
        
        # Rechercher les emails récents
        _, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()[-limit:]
        
        emails = []
        for email_id in email_ids:
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            # Parser l'email...
            emails.append({
                "id": email_id.decode(),
                "subject": "...",  # À implémenter
                "from": "...",
                "date": "..."
            })
        
        mail.close()
        mail.logout()
        
        return {
            "success": True,
            "count": len(emails),
            "emails": emails
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5008)
```

### Étape 3: Docker

`src/connectors/email/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code
COPY connector.py .
COPY config.py .

EXPOSE 5008

CMD ["python", "connector.py"]
```

### Étape 4: Docker Compose

`docker-compose.yml`:

```yaml
services:
  hopper-email:
    build: ./src/connectors/email
    container_name: hopper-email
    ports:
      - "5008:5008"
    environment:
      - EMAIL_ADDRESS=${EMAIL_ADDRESS}
      - EMAIL_PASSWORD=${EMAIL_PASSWORD}
    restart: unless-stopped
    networks:
      - hopper-network
```

### Étape 5: Intégrer à l'Orchestrator

`src/orchestrator/tools/system_integration.py`:

```python
# Ajouter l'URL
EMAIL_URL = "http://localhost:5008"

# Ajouter les patterns
EMAIL_PATTERNS = [
    # Envoyer email
    (r"envoie un email à (\S+) avec comme sujet (.+?) et message (.+)", "send_email"),
    (r"envoie un mail à (\S+)", "send_email"),
    
    # Vérifier inbox
    (r"vérifie mes emails?", "check_inbox"),
    (r"quels? sont mes derniers? emails?", "check_inbox"),
]

# Ajouter la fonction d'exécution
async def _execute_email_action(action: str, text: str) -> Dict[str, Any]:
    """Exécuter une action email"""
    
    if action == "send_email":
        # Extraire les paramètres
        match = re.match(r"envoie un email à (\S+) avec comme sujet (.+?) et message (.+)", text)
        if match:
            to = match.group(1)
            subject = match.group(2)
            body = match.group(3)
            
            response = await client.post(
                f"{EMAIL_URL}/send",
                json={"to": to, "subject": subject, "body": body}
            )
            return response.json()
    
    elif action == "check_inbox":
        response = await client.get(f"{EMAIL_URL}/inbox?limit=5")
        return response.json()
    
    return {"error": "Action inconnue"}
```

### Étape 6: Tests

`tests/test_email_connector.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.connectors.email.connector import app

client = TestClient(app)

def test_health():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_send_email():
    """Test envoi email"""
    response = client.post("/send", json={
        "to": "test@example.com",
        "subject": "Test",
        "body": "Ceci est un test"
    })
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_check_inbox():
    """Test vérification inbox"""
    response = client.get("/inbox?limit=5")
    assert response.status_code == 200
    assert "emails" in response.json()
```

---

## 🧩 Ajouter une Capability

### Exemple: Ajouter "traduire du texte"

#### 1. Créer le Service

`src/services/translator/service.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import MarianMTModel, MarianTokenizer

app = FastAPI()

# Charger le modèle au démarrage
model_name = "Helsinki-NLP/opus-mt-fr-en"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "fr"
    target_lang: str = "en"

@app.post("/translate")
async def translate(request: TranslateRequest):
    """Traduire un texte"""
    inputs = tokenizer(request.text, return_tensors="pt", padding=True)
    outputs = model.generate(**inputs)
    translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return {
        "original": request.text,
        "translation": translation,
        "source_lang": request.source_lang,
        "target_lang": request.target_lang
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5009)
```

#### 2. Intégrer à l'Orchestrator

```python
# tools/system_integration.py

TRANSLATOR_URL = "http://localhost:5009"

TRANSLATION_PATTERNS = [
    (r"traduis (.+) en anglais", "translate_to_english"),
    (r"traduis (.+)", "translate"),
]

async def _execute_translation_action(action: str, text: str):
    match = re.match(r"traduis (.+) en anglais", text)
    if match:
        text_to_translate = match.group(1)
        response = await client.post(
            f"{TRANSLATOR_URL}/translate",
            json={"text": text_to_translate, "target_lang": "en"}
        )
        return response.json()
```

---

## 🗣️ Patterns NLP

### Syntaxe

```python
PATTERNS = [
    # (regex, action_name)
    (r"ouvre? (.+)", "open_app"),
    (r"lance (.+)", "open_app"),
    (r"démarre (.+)", "open_app"),
]
```

### Bonnes Pratiques

#### ✅ Bon Pattern

```python
# Flexible, capture les variations
(r"envoie? (?:un )?emails? à (\S+)", "send_email")

# Accepte:
# - "envoie un email à john@example.com"
# - "envoie email à john@example.com"
# - "envoyer un email à john@example.com"
```

#### ❌ Mauvais Pattern

```python
# Trop rigide
(r"envoie un email à (\S+)", "send_email")

# N'accepte QUE: "envoie un email à"
# Reject: "envoyer", "envoie email"
```

### Groupes de Capture

```python
# Capture multiple
(r"envoie un email à (\S+) avec sujet (.+?) et message (.+)", "send_email")

# Extraction:
match = re.match(pattern, text)
to = match.group(1)        # john@example.com
subject = match.group(2)   # Urgent
body = match.group(3)      # Ceci est important
```

### Regex Utiles

```python
# Email
r"\S+@\S+"

# Nombre
r"\d+"

# URL
r"https?://[^\s]+"

# Nom de fichier
r"[\w\-. ]+"

# Optionnel
r"(?:un )?"  # "un" est optionnel

# Alternative
r"(?:ouvre|lance|démarre)"

# Non-greedy
r".+?"  # Capture minimum
```

---

## 🧪 Tests

### Structure

```
tests/
├── unit/
│   ├── test_orchestrator.py
│   ├── test_stt_service.py
│   └── test_llm_service.py
├── integration/
│   ├── test_full_pipeline.py
│   └── test_connectors.py
└── e2e/
    └── test_scenarios.py
```

### Test Unitaire

```python
import pytest
from src.orchestrator.core.dispatcher import Dispatcher

@pytest.fixture
def dispatcher():
    return Dispatcher()

def test_detect_intent(dispatcher):
    """Test détection d'intention"""
    intent = dispatcher.detect_intent("ouvre Safari")
    assert intent["action"] == "open_app"
    assert intent["target"] == "Safari"

def test_security_check(dispatcher):
    """Test vérification sécurité"""
    result = dispatcher.check_security("rm -rf /")
    assert result["risk_level"] == "CRITICAL"
    assert result["requires_confirmation"] == True
```

### Test d'Intégration

```python
import pytest
from fastapi.testclient import TestClient
from src.orchestrator.main import app

client = TestClient(app)

def test_full_flow():
    """Test flux complet STT -> LLM -> Action"""
    
    # 1. STT
    stt_response = client.post("/stt/transcribe", json={"audio": "..."})
    assert stt_response.status_code == 200
    text = stt_response.json()["text"]
    
    # 2. LLM
    llm_response = client.post("/llm/query", json={"prompt": text})
    assert llm_response.status_code == 200
    
    # 3. Action
    action_response = client.post("/execute", json={"command": text})
    assert action_response.status_code == 200
```

### Test E2E

```bash
# Lancer tous les tests
./scripts/test_e2e.sh

# Tests spécifiques
pytest tests/unit/test_orchestrator.py -v
pytest tests/integration/ -v
pytest tests/e2e/ --slow
```

---

## 📚 Documentation

### Docstrings

```python
def send_email(to: str, subject: str, body: str) -> EmailResponse:
    """
    Envoyer un email via SMTP.
    
    Args:
        to (str): Adresse email destinataire
        subject (str): Sujet de l'email
        body (str): Corps du message
    
    Returns:
        EmailResponse: Résultat de l'envoi
        
    Raises:
        SMTPException: Si l'envoi échoue
        
    Example:
        >>> send_email("john@example.com", "Test", "Hello World")
        EmailResponse(success=True, email_id="...")
    """
    ...
```

### README Connecteur

```markdown
# Email Connector

## Description
Connecteur pour envoyer et recevoir des emails via SMTP/IMAP.

## Capabilities
- `send_email`: Envoyer un email
- `check_inbox`: Vérifier la boîte de réception

## Configuration
\```bash
EMAIL_ADDRESS=votre@email.com
EMAIL_PASSWORD=votre_mot_de_passe
SMTP_SERVER=smtp.gmail.com
\```

## Exemples
\```bash
# Envoyer un email
"Envoie un email à john@example.com avec sujet Test et message Hello"

# Vérifier emails
"Quels sont mes derniers emails ?"
\```

## Tests
\```bash
pytest tests/test_email_connector.py
\```
```

---

## 🤝 Contribution

### Workflow Git

```bash
# 1. Fork et clone
git clone https://github.com/YOUR_USERNAME/HOPPER.git
cd HOPPER

# 2. Créer une branche
git checkout -b feature/email-connector

# 3. Coder et tester
# ...

# 4. Commit
git add .
git commit -m "feat: add email connector with send/receive"

# 5. Push
git push origin feature/email-connector

# 6. Pull Request sur GitHub
```

### Convention Commits

```
feat: nouvelle fonctionnalité
fix: correction de bug
docs: documentation
style: formatage code
refactor: refactorisation
test: ajout tests
chore: maintenance
```

### Pull Request Template

```markdown
## Description
Ajoute un connecteur Email pour envoyer/recevoir des emails.

## Type de changement
- [x] Nouvelle fonctionnalité
- [ ] Correction bug
- [ ] Documentation

## Tests
- [x] Tests unitaires ajoutés
- [x] Tests d'intégration OK
- [x] Tests E2E passent

## Checklist
- [x] Code formaté (black)
- [x] Docstrings ajoutées
- [x] Documentation mise à jour
- [x] Tests passent
```

---

## 🎓 Ressources

### Documentation Technique

- **FastAPI**: https://fastapi.tiangolo.com/
- **Transformers**: https://huggingface.co/docs/transformers
- **Neo4j**: https://neo4j.com/docs/
- **Docker**: https://docs.docker.com/

### Exemples Connecteurs

- `src/connectors/spotify/`: Connecteur Spotify complet
- `src/connectors/antivirus/`: Système antivirus avec adapters
- `src/connectors/local_system/`: Contrôle système cross-platform

### Outils Dev

```bash
# Linter
pylint src/

# Formatter
black src/

# Type checking
mypy src/

# Tests avec coverage
pytest --cov=src tests/

# Profiling
py-spy record -o profile.svg -- python src/orchestrator/main.py
```

---

**Happy Coding! 🚀**

HOPPER Team - Octobre 2025
