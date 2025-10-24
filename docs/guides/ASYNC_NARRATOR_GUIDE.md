# Mode Asynchrone - ActionNarrator

Guide complet pour l'utilisation du narrateur d'actions en mode asynchrone avec support des callbacks web.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Utilisation de Base](#utilisation-de-base)
- [Callbacks Personnalisés](#callbacks-personnalisés)
- [Callbacks HTTP](#callbacks-http)
- [Intégration FastAPI](#intégration-fastapi)
- [Exemples Complets](#exemples-complets)
- [Référence API](#référence-api)

---

## Vue d'ensemble

`AsyncActionNarrator` est une version asynchrone d'`ActionNarrator` qui permet :

- ✅ **Narration non-bloquante** des actions
- ✅ **Callbacks asynchrones** pour les approbations
- ✅ **Support HTTP** pour les approbations via API
- ✅ **Auto-approbation** configurable pour les actions de faible urgence
- ✅ **Compatible FastAPI** pour les workflows web

### Différences avec ActionNarrator

| Fonctionnalité | ActionNarrator | AsyncActionNarrator |
|---|---|---|
| Exécution | Synchrone (bloquante) | Asynchrone (non-bloquante) |
| Approbation | `input()` console | Callbacks async + HTTP |
| Contexte | CLI, scripts | FastAPI, serveurs web |
| Auto-approbation | Non | Oui (configurable) |

---

## Installation

### Dépendances

```bash
pip install aiohttp  # Pour les callbacks HTTP
```

### Import

```python
from src.communication import (
    AsyncActionNarrator,
    Action,
    ActionType,
    Urgency,
    # Helpers asynchrones
    narrate_file_scan_async,
    narrate_system_command_async,
    narrate_file_modification_async,
    narrate_data_analysis_async
)
```

---

## Utilisation de Base

### Initialisation

```python
# Mode simple (auto-approbation des actions faible urgence)
narrator = AsyncActionNarrator(auto_approve_low_urgency=True)

# Mode avec callback personnalisé
async def my_approval(action):
    # Logique d'approbation personnalisée
    return True

narrator = AsyncActionNarrator(
    approval_callback=my_approval,
    auto_approve_low_urgency=True
)

# Mode avec callback HTTP
narrator = AsyncActionNarrator(
    callback_url="http://localhost:8000/api/approval",
    auto_approve_low_urgency=False
)
```

### Narration d'une Action

```python
import asyncio

async def main():
    narrator = AsyncActionNarrator(auto_approve_low_urgency=True)
    
    action = Action(
        action_type=ActionType.SECURITY_SCAN,
        description="Scanner le fichier upload.pdf",
        reason="vérifier qu'il ne contient pas de malware",
        urgency=Urgency.LOW,
        requires_approval=False
    )
    
    approved = await narrator.narrate_async(action)
    
    if approved:
        print("✅ Action approuvée, exécution...")
        # Exécuter l'action
    else:
        print("⛔ Action refusée")

asyncio.run(main())
```

---

## Callbacks Personnalisés

### Callback Simple

```python
async def approval_callback(action: Action) -> bool:
    """Callback d'approbation personnalisé"""
    print(f"Demande d'approbation: {action.description}")
    
    # Exemple: approuver automatiquement certains types
    if action.action_type == ActionType.SECURITY_SCAN:
        return True
    
    # Pour les autres, vérifier en base de données
    user_preference = await get_user_preference(action.action_type)
    return user_preference.auto_approve

narrator = AsyncActionNarrator(approval_callback=approval_callback)
```

### Callback avec Contexte Utilisateur

```python
class UserApprovalManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    async def approve(self, action: Action) -> bool:
        """Approval basé sur les préférences utilisateur"""
        # Charger préférences depuis DB
        prefs = await db.get_user_preferences(self.user_id)
        
        # Vérifier historique des approbations
        history = await db.get_approval_history(self.user_id)
        
        # Décision basée sur règles métier
        if action.urgency == Urgency.BLOCKING:
            # Toujours demander pour les actions critiques
            return await self.request_user_confirmation(action)
        
        if action.action_type in prefs.auto_approve_types:
            return True
        
        return await self.request_user_confirmation(action)
    
    async def request_user_confirmation(self, action: Action) -> bool:
        """Envoyer notification et attendre réponse"""
        # Créer notification
        notif_id = await notification_service.send(
            user_id=self.user_id,
            title=f"Approbation requise: {action.description}",
            body=f"Urgence: {action.urgency.value}",
            action_buttons=["Approuver", "Refuser"]
        )
        
        # Attendre réponse (avec timeout)
        response = await notification_service.wait_response(
            notif_id,
            timeout=300  # 5 minutes
        )
        
        return response == "Approuver"

# Utilisation
user_manager = UserApprovalManager(user_id="user_123")
narrator = AsyncActionNarrator(approval_callback=user_manager.approve)
```

---

## Callbacks HTTP

### Configuration

```python
narrator = AsyncActionNarrator(
    callback_url="http://localhost:8000/api/approval"
)
```

### Payload Envoyé

Le payload POST contient :

```json
{
  "action_type": "system_command",
  "description": "Exécuter la commande 'ls -la'",
  "reason": "lister les fichiers",
  "urgency": "high",
  "risks": ["Modification système"],
  "benefits": ["Visibilité sur les fichiers"],
  "details": {"command": "ls -la"},
  "estimated_duration": "quelques secondes"
}
```

### Réponse Attendue

```json
{
  "approved": true
}
```

### Exemple de Serveur d'Approbation

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/api/approval")
async def handle_approval(request: Request):
    """Endpoint d'approbation"""
    data = await request.json()
    
    # Logique métier
    action_type = data.get("action_type")
    urgency = data.get("urgency")
    
    # Exemple: auto-approuver les scans de sécurité
    if action_type == "security_scan":
        return {"approved": True}
    
    # Pour les autres, vérifier permissions
    user_id = request.headers.get("X-User-ID")
    has_permission = await check_permission(user_id, action_type)
    
    return {"approved": has_permission}
```

---

## Intégration FastAPI

### Exemple Complet: System Executor

```python
from fastapi import FastAPI, HTTPException, Header
from src.communication import AsyncActionNarrator, narrate_system_command_async
from src.system_executor.server import SystemExecutor

app = FastAPI()

# Créer narrateur avec callback HTTP
narrator = AsyncActionNarrator(
    callback_url="http://approval-service:8000/api/approval",
    auto_approve_low_urgency=False
)

executor = SystemExecutor(
    whitelist_path="./config/whitelist.yaml",
    narrator=narrator
)

@app.post("/execute")
async def execute_command(
    command: str,
    user_id: str = Header(...)
):
    """Exécute une commande avec approbation async"""
    
    # Narrer l'action
    approved = await narrate_system_command_async(
        narrator,
        command,
        purpose="traiter la demande utilisateur"
    )
    
    if not approved:
        raise HTTPException(
            status_code=403,
            detail="Commande refusée par l'utilisateur"
        )
    
    # Exécuter
    result = executor.execute(command, [], timeout=30)
    
    return {
        "success": result.success,
        "output": result.stdout,
        "exit_code": result.exit_code
    }
```

### Workflow avec Queue

```python
import asyncio
from typing import Dict
from uuid import uuid4

# Queue d'approbations en attente
pending_approvals: Dict[str, asyncio.Future] = {}

@app.post("/api/approval/request")
async def request_approval(action: Action):
    """Créer une demande d'approbation"""
    approval_id = str(uuid4())
    
    # Créer Future pour attendre la réponse
    future = asyncio.Future()
    pending_approvals[approval_id] = future
    
    # Envoyer notification à l'utilisateur
    await notification_service.send(
        title=f"Approbation requise",
        body=action.description,
        approval_id=approval_id
    )
    
    # Attendre réponse (avec timeout)
    try:
        approved = await asyncio.wait_for(future, timeout=300)
        return {"approved": approved}
    except asyncio.TimeoutError:
        return {"approved": False, "reason": "timeout"}
    finally:
        pending_approvals.pop(approval_id, None)

@app.post("/api/approval/respond/{approval_id}")
async def respond_approval(approval_id: str, approved: bool):
    """Répondre à une demande d'approbation"""
    if approval_id not in pending_approvals:
        raise HTTPException(404, "Demande non trouvée")
    
    # Résoudre la Future
    pending_approvals[approval_id].set_result(approved)
    
    return {"status": "ok"}
```

---

## Exemples Complets

### 1. Scan Antivirus Asynchrone

```python
from src.communication import AsyncActionNarrator, narrate_file_scan_async

async def scan_file_async(file_path: str, user_id: str):
    """Scanner un fichier avec narration async"""
    
    # Créer narrateur avec callback utilisateur
    async def user_approval(action):
        # Vérifier préférences
        prefs = await get_user_prefs(user_id)
        if prefs.auto_approve_scans:
            return True
        
        # Sinon, demander confirmation
        return await request_user_approval(user_id, action)
    
    narrator = AsyncActionNarrator(
        approval_callback=user_approval,
        auto_approve_low_urgency=True
    )
    
    # Narrer le scan
    approved = await narrate_file_scan_async(narrator, file_path)
    
    if not approved:
        return {"status": "cancelled"}
    
    # Exécuter le scan
    from src.security.malware_detector import MalwareDetector
    detector = MalwareDetector(narrator=narrator)
    
    result = detector.scan_file(file_path)
    
    return {
        "status": "completed",
        "is_malware": result.is_malware,
        "threat_level": result.threat_level.value
    }
```

### 2. Pipeline de Traitement avec Narration

```python
async def process_document_pipeline(doc_path: str):
    """Pipeline complet avec narration de chaque étape"""
    
    narrator = AsyncActionNarrator(auto_approve_low_urgency=True)
    
    # Étape 1: Scan sécurité
    approved = await narrate_file_scan_async(narrator, doc_path)
    if not approved:
        return {"error": "Scan refusé"}
    
    scan_result = await security_scan(doc_path)
    if scan_result.is_malware:
        return {"error": "Malware détecté"}
    
    # Étape 2: Extraction de texte
    from src.communication import Action, ActionType, Urgency
    
    action = Action(
        action_type=ActionType.DATA_ANALYSIS,
        description=f"Extraire le texte de {doc_path}",
        reason="préparer pour l'analyse",
        urgency=Urgency.LOW,
        requires_approval=False
    )
    
    await narrator.narrate_async(action)
    text = await extract_text(doc_path)
    
    # Étape 3: Analyse
    action = Action(
        action_type=ActionType.DATA_ANALYSIS,
        description="Analyser le contenu du document",
        reason="générer un résumé",
        urgency=Urgency.LOW,
        requires_approval=False
    )
    
    await narrator.narrate_async(action)
    summary = await analyze_text(text)
    
    return {
        "status": "success",
        "summary": summary
    }
```

### 3. Intégration avec WebSocket

```python
from fastapi import WebSocket

class WebSocketNarrator:
    """Narrateur avec approbation via WebSocket"""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.narrator = AsyncActionNarrator(
            approval_callback=self.ws_approval
        )
    
    async def ws_approval(self, action: Action) -> bool:
        """Demander approbation via WebSocket"""
        # Envoyer demande
        await self.websocket.send_json({
            "type": "approval_request",
            "action": {
                "description": action.description,
                "urgency": action.urgency.value,
                "risks": action.risks
            }
        })
        
        # Attendre réponse
        response = await self.websocket.receive_json()
        
        return response.get("approved", False)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    ws_narrator = WebSocketNarrator(websocket)
    
    try:
        while True:
            # Recevoir commande
            data = await websocket.receive_json()
            command = data.get("command")
            
            # Narrer et exécuter
            approved = await narrate_system_command_async(
                ws_narrator.narrator,
                command,
                purpose="traiter votre commande"
            )
            
            if approved:
                result = execute_command(command)
                await websocket.send_json({"result": result})
            else:
                await websocket.send_json({"error": "Refusé"})
                
    except WebSocketDisconnect:
        pass
```

---

## Référence API

### AsyncActionNarrator

```python
class AsyncActionNarrator(ActionNarrator):
    def __init__(
        self,
        callback_url: Optional[str] = None,
        approval_callback: Optional[Callable[[Action], Awaitable[bool]]] = None,
        auto_approve_low_urgency: bool = True
    )
```

**Paramètres:**
- `callback_url`: URL pour callbacks HTTP POST
- `approval_callback`: Fonction async pour approbation personnalisée
- `auto_approve_low_urgency`: Auto-approuver actions INFO/LOW

**Méthodes:**

```python
async def narrate_async(self, action: Action) -> bool
```
Narre une action de manière asynchrone.

**Retourne:** `True` si approuvée, `False` sinon

### Helpers Asynchrones

```python
async def narrate_file_scan_async(
    narrator: AsyncActionNarrator,
    file_path: str,
    scan_type: str = "sécurité"
) -> bool
```

```python
async def narrate_file_modification_async(
    narrator: AsyncActionNarrator,
    file_path: str,
    operation: str,
    backup_created: bool = True
) -> bool
```

```python
async def narrate_system_command_async(
    narrator: AsyncActionNarrator,
    command: str,
    purpose: str
) -> bool
```

```python
async def narrate_data_analysis_async(
    narrator: AsyncActionNarrator,
    data_source: str,
    analysis_type: str
) -> bool
```

---

## Bonnes Pratiques

### 1. Gestion des Timeouts

```python
# Toujours définir un timeout pour les approbations
async with asyncio.timeout(300):  # 5 minutes
    approved = await narrator.narrate_async(action)
```

### 2. Gestion des Erreurs

```python
try:
    approved = await narrator.narrate_async(action)
except asyncio.TimeoutError:
    logger.error("Timeout lors de l'approbation")
    approved = False
except Exception as e:
    logger.error(f"Erreur: {e}")
    approved = False
```

### 3. Logging

```python
from loguru import logger

logger.info(f"Demande d'approbation: {action.description}")

if approved:
    logger.success("Action approuvée")
else:
    logger.warning("Action refusée")
```

### 4. Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_narrator():
    """Test du narrateur asynchrone"""
    
    async def mock_approval(action):
        return True
    
    narrator = AsyncActionNarrator(approval_callback=mock_approval)
    
    action = Action(...)
    approved = await narrator.narrate_async(action)
    
    assert approved is True
```

---

## Dépannage

### Problème: Callback non appelé

**Cause:** `auto_approve_low_urgency=True` et action de faible urgence

**Solution:** 
```python
narrator = AsyncActionNarrator(
    approval_callback=my_callback,
    auto_approve_low_urgency=False  # Désactiver l'auto-approbation
)
```

### Problème: Timeout HTTP

**Cause:** Callback URL injoignable ou lente

**Solution:**
```python
# Vérifier la connectivité
import aiohttp

async with aiohttp.ClientSession() as session:
    async with session.get(callback_url) as resp:
        print(f"Status: {resp.status}")
```

### Problème: Blocage en mode synchrone

**Cause:** Pas de callback configuré, fallback vers input()

**Solution:** Toujours configurer au moins `auto_approve_low_urgency=True`

---

## Ressources

- **Code Source:** `src/communication/async_narrator.py`
- **Tests:** `tests/test_system_executor_integration.py`
- **Guide Principal:** `docs/guides/NATURAL_COMMUNICATION_GUIDE.md`
- **Exemples:** `examples/natural_communication_demo.py`

---

**Version:** 1.0.0  
**Dernière mise à jour:** 24 octobre 2025
