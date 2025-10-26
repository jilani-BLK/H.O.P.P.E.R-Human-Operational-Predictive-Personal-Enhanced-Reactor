# Phase 2 - Plan d'Action Concret

**Objectif**: Rendre HOPPER fonctionnel avec services réels (LLM, Email, Voix)
**Durée estimée**: 3-4 semaines
**Prérequis**: Phase 1 validée (41/41 tests OK)

## Étape 1: Installation Infrastructure (Jour 1)

### Docker et Docker Compose
```bash
# Installation via Homebrew
brew install --cask docker

# Ou Docker Desktop depuis:
# https://www.docker.com/products/docker-desktop/

# Vérification
docker --version
docker-compose --version
```

### Démarrage Services Base
```bash
cd /Users/jilani/Projet/HOPPER
docker-compose build
docker-compose up -d

# Vérifier health
curl http://localhost:5000/health  # Orchestrator
curl http://localhost:5002/health  # System Executor
```

## Étape 2: LLM Engine Réel (Jours 2-3)

### Téléchargement Modèle
```bash
# Créer répertoire modèles
mkdir -p data/models

# Option 1: Mistral-7B-Instruct (Recommandé pour M3 Max)
cd data/models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Option 2: LLaMA 2 13B (Plus puissant)
wget https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf
```

### Intégration llama.cpp
```bash
# Dans src/llm_engine/
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Compilation pour Apple Silicon
make clean
LLAMA_METAL=1 make -j

# Test modèle
./main -m ../../data/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
       -n 128 -p "Bonjour, je suis HOPPER"
```

### Mise à Jour server.py
Remplacer mode simulation par:
```python
from llama_cpp import Llama

llm = Llama(
    model_path="/app/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    n_ctx=4096,
    n_gpu_layers=35,  # GPU Metal
    n_threads=6
)

@app.post("/generate")
async def generate(request: GenerateRequest):
    response = llm(
        request.prompt,
        max_tokens=request.max_tokens,
        temperature=0.7,
        top_p=0.9
    )
    return {"response": response["choices"][0]["text"]}
```

### Test End-to-End
```bash
# CLI
python3 hopper-cli.py -i
> Explique-moi la physique quantique en 3 phrases

# Doit retourner réponse LLM réelle (pas simulation)
```

## Étape 3: Speech-to-Text (Jours 4-5)

### Installation Whisper
```bash
cd src/stt/
pip install openai-whisper torch torchaudio

# Télécharger modèle
python3 -c "import whisper; whisper.load_model('medium')"
```

### Mise à Jour server.py
```python
import whisper

model = whisper.load_model("medium")  # Français optimisé

@app.post("/transcribe")
async def transcribe(file: UploadFile):
    # Sauvegarder fichier audio
    audio_path = f"/tmp/{file.filename}"
    with open(audio_path, "wb") as f:
        f.write(await file.read())
    
    # Transcription
    result = model.transcribe(
        audio_path,
        language="fr",
        task="transcribe"
    )
    
    return {
        "text": result["text"],
        "language": result["language"],
        "confidence": result.get("confidence", 0.0)
    }
```

### Test Audio
```bash
# Enregistrer audio test
# macOS: QuickTime Player > Nouvel enregistrement audio

# Tester API
curl -X POST http://localhost:5003/transcribe \
  -F "file=@test_audio.wav"
```

## Étape 4: Connecteur Email (Jours 6-8)

### Bibliothèques
```bash
cd src/connectors/
pip install imapclient smtplib email
```

### Implémentation IMAP/SMTP
```python
from imapclient import IMAPClient
import smtplib
from email.mime.text import MIMEText

class EmailConnector:
    def __init__(self, email, password):
        self.email = email
        self.imap_server = "imap.gmail.com"
        self.smtp_server = "smtp.gmail.com"
        self.password = password
    
    def read_emails(self, folder="INBOX", limit=10):
        with IMAPClient(self.imap_server, ssl=True) as client:
            client.login(self.email, self.password)
            client.select_folder(folder)
            
            messages = client.search(['UNSEEN'])
            emails = []
            
            for uid in messages[:limit]:
                raw = client.fetch([uid], ['ENVELOPE', 'BODY[TEXT]'])
                envelope = raw[uid][b'ENVELOPE']
                body = raw[uid][b'BODY[TEXT]'].decode('utf-8')
                
                emails.append({
                    'from': envelope.from_[0].mailbox.decode(),
                    'subject': envelope.subject.decode(),
                    'body': body,
                    'date': envelope.date
                })
            
            return emails
    
    def send_email(self, to, subject, body):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = to
        
        with smtplib.SMTP_SSL(self.smtp_server, 465) as server:
            server.login(self.email, self.password)
            server.send_message(msg)
```

### Configuration
```bash
# .env
EMAIL_ADDRESS=votre.email@gmail.com
EMAIL_PASSWORD=mot_de_passe_app  # Pas mot de passe normal!

# Gmail: Activer "App Passwords"
# https://myaccount.google.com/apppasswords
```

### Tests
```bash
# Lire emails
curl http://localhost:5006/connectors/email/read

# Envoyer email
curl -X POST http://localhost:5006/connectors/email/send \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Test HOPPER", "body": "Bonjour!"}'
```

## Étape 5: Interface Vocale Complète (Jours 9-11)

### Workflow
```
Utilisateur parle
    ↓
Enregistrement audio (pyaudio)
    ↓
STT (Whisper) → Texte
    ↓
Orchestrator → Traitement
    ↓
LLM → Réponse texte
    ↓
TTS → Audio
    ↓
Lecture audio (pygame/pydub)
```

### Implémentation CLI Vocal
```python
import pyaudio
import wave
from pydub import AudioSegment
from pydub.playback import play

class VoiceInterface:
    def __init__(self, stt_url, tts_url):
        self.stt_url = stt_url
        self.tts_url = tts_url
        self.audio = pyaudio.PyAudio()
    
    def record_audio(self, duration=5):
        """Enregistrer audio microphone"""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        print("Parlez maintenant...")
        frames = []
        for _ in range(0, int(16000 / 1024 * duration)):
            frames.append(stream.read(1024))
        
        stream.stop_stream()
        stream.close()
        
        # Sauvegarder WAV
        wf = wave.open("/tmp/input.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return "/tmp/input.wav"
    
    def transcribe(self, audio_path):
        """Convertir audio → texte"""
        with open(audio_path, "rb") as f:
            response = requests.post(
                self.stt_url,
                files={"file": f}
            )
        return response.json()["text"]
    
    def synthesize(self, text):
        """Convertir texte → audio"""
        response = requests.post(
            self.tts_url,
            json={"text": text}
        )
        audio_data = response.content
        
        # Sauvegarder et jouer
        with open("/tmp/output.wav", "wb") as f:
            f.write(audio_data)
        
        audio = AudioSegment.from_wav("/tmp/output.wav")
        play(audio)
```

### Mode Vocal CLI
```bash
# Ajouter au hopper-cli.py
python3 hopper-cli.py --voice

# Workflow:
# [HOPPER écoute] → Utilisateur parle
# → Transcription affichée
# → Traitement commande
# → Réponse vocale
```

## Étape 6: Tests Intégration (Jours 12-14)

### Tests End-to-End
```python
# tests/test_phase2.py
import pytest
import requests

def test_llm_real_response():
    """LLM retourne réponse réelle (pas simulation)"""
    response = requests.post(
        "http://localhost:5001/generate",
        json={"prompt": "Dis bonjour", "max_tokens": 20}
    )
    assert "simulation" not in response.json()["response"].lower()

def test_stt_transcription():
    """STT transcrit audio réel"""
    with open("tests/fixtures/test_audio.wav", "rb") as f:
        response = requests.post(
            "http://localhost:5003/transcribe",
            files={"file": f}
        )
    assert len(response.json()["text"]) > 0

def test_email_read():
    """Connecteur email lit vrais emails"""
    response = requests.get("http://localhost:5006/connectors/email/read")
    emails = response.json()["emails"]
    assert isinstance(emails, list)

def test_voice_workflow():
    """Test workflow vocal complet"""
    # Enregistrer → Transcrire → Traiter → Synthétiser
    # ...
```

### Performance
```bash
# Benchmark latence
time python3 -c "
import requests
requests.post('http://localhost:5000/command', 
              json={'command': 'Explique Python'})
"

# Objectif: <3 secondes pour workflow complet
```

## Étape 7: Optimisations (Jours 15-18)

### Cache LLM
```python
# Réponses fréquentes en cache
from functools import lru_cache

@lru_cache(maxsize=100)
def generate_cached(prompt):
    return llm(prompt)
```

### Compression Contexte
```python
# Résumer historique long
if len(context) > 20:
    summary = llm(f"Résume: {context[:10]}")
    context = [summary] + context[-10:]
```

### Parallélisation
```python
# Traiter plusieurs requêtes async
import asyncio

async def process_batch(commands):
    tasks = [process_command(cmd) for cmd in commands]
    return await asyncio.gather(*tasks)
```

## Checklist Phase 2

### Infrastructure
- [ ] Docker Desktop installé
- [ ] Tous services démarrent sans erreur
- [ ] Health checks OK (5000-5006)

### LLM
- [ ] Modèle GGUF téléchargé (Mistral/LLaMA)
- [ ] llama.cpp compilé avec Metal
- [ ] Génération texte fonctionne
- [ ] Latence <2 sec pour 100 tokens

### STT
- [ ] Whisper medium installé
- [ ] Transcription français OK
- [ ] Précision >90% sur tests

### Email
- [ ] IMAP/SMTP configuré
- [ ] Lecture emails fonctionne
- [ ] Envoi emails fonctionne
- [ ] Gestion erreurs (auth, network)

### Voix
- [ ] Enregistrement microphone
- [ ] Workflow STT → LLM → TTS
- [ ] Latence totale <5 sec
- [ ] Qualité audio acceptable

### Tests
- [ ] Tests unitaires passent
- [ ] Tests intégration E2E
- [ ] Performance satisfaisante
- [ ] Logs sans erreurs critiques

## Commandes Phase 2

```bash
# Installation rapide
make install-phase2

# Tests Phase 2
make test-phase2

# Benchmark
make benchmark

# Monitoring
make monitor
```

## Résultat Attendu

À la fin de Phase 2, HOPPER peut:
1. Comprendre commandes vocales (français)
2. Générer réponses intelligentes via LLM local
3. Lire et envoyer emails
4. Répondre vocalement
5. Exécuter actions système
6. Maintenir contexte conversationnel

**Latence cible**: <5 sec workflow vocal complet
**Mémoire**: <12 Go RAM
**CPU**: <50% utilisation moyenne
