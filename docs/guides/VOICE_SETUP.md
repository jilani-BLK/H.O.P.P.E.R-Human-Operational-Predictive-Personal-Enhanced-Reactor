# 🎤 Guide de Démarrage Rapide - Phase 3

**HOPPER - Fonctionnalités Vocales**

---

## 🚀 Installation

### 1. Installer les dépendances

```bash
cd /Users/jilani/Projet/HOPPER

# Activer l'environnement virtuel
source .venv/bin/activate

# Installer les packages Phase 3
pip install -r requirements-phase3.txt
```

### 2. Installer les dépendances système (macOS)

```bash
# Audio
brew install portaudio
brew install ffmpeg

# Si erreur compilation pyaudio:
brew install portaudio
pip install --global-option='build_ext' --global-option='-I/opt/homebrew/include' --global-option='-L/opt/homebrew/lib' pyaudio
```

### 3. Vérifier l'installation

```bash
python validate_phase3.py
```

---

## 🎤 Test du Wake Word

### Test 1: Détection de voix

```bash
cd src/stt
python wake_word.py
```

Parlez près du micro - le système détecte l'activité vocale.

### Test 2: Simulation

```python
from src.stt.wake_word import WakeWordDetector

def on_wake():
    print("Wake word détecté!")

detector = WakeWordDetector()
detector.start_listening(on_wake)
detector.simulate_wake_word()  # Simule la détection
```

---

## 🎙️ Test STT (Speech-to-Text)

### Option 1: Service déjà en place

```bash
# Démarrer le service STT
docker-compose up stt

# Tester la transcription
curl -X POST http://localhost:5003/transcribe \
  -F "audio=@test_audio.wav"
```

### Option 2: Test local

```python
import httpx
import asyncio

async def test_stt():
    with open("audio.wav", "rb") as f:
        audio = f.read()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:5003/transcribe",
            files={"audio": audio}
        )
        print(response.json())

asyncio.run(test_stt())
```

---

## 🔊 Test TTS (Text-to-Speech)

### Test avec Coqui TTS

```bash
# Démarrer le service TTS
docker-compose up tts

# Tester la synthèse
curl -X POST http://localhost:5004/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Bonjour, je suis Hopper"}' \
  --output response.wav

# Écouter le résultat
afplay response.wav  # macOS
```

---

## 🎭 Test Pipeline Complet (STT → LLM → TTS)

### Script de test

```python
import asyncio
from src.orchestrator.services.voice_pipeline import voice_command

async def test():
    # Charger un fichier audio de test
    with open("test_question.wav", "rb") as f:
        audio = f.read()
    
    # Traiter la commande vocale
    result = await voice_command(audio, voice_output=True)
    
    print(f"📝 Transcription: {result['transcription']}")
    print(f"💬 Réponse: {result['response_text']}")
    print(f"⏱️  Latence totale: {result['latency']['total']:.2f}s")
    
    # Sauvegarder la réponse audio
    if result['response_audio']:
        with open("response.wav", "wb") as f:
            f.write(result['response_audio'])
        print("🔊 Audio sauvegardé: response.wav")

asyncio.run(test())
```

---

## 📧 Configuration Email (IMAP)

### 1. Créer la configuration

```bash
cp config/email_config.yaml.example config/email_config.yaml
```

### 2. Éditer la configuration

```yaml
# config/email_config.yaml
email:
  imap_server: "imap.gmail.com"
  imap_port: 993
  username: "votre.email@gmail.com"
  password: "votre_mot_de_passe_app"  # App Password Gmail
  use_ssl: true
  
  polling_interval: 120  # secondes
  
  folders:
    inbox: "INBOX"
    sent: "[Gmail]/Sent"
```

### 3. Obtenir un App Password Gmail

1. Aller sur https://myaccount.google.com/security
2. Activer la validation en 2 étapes
3. "Mots de passe des applications" → Générer
4. Utiliser ce mot de passe dans la config

---

## 🔒 Entraînement Auth Vocale

### 1. Enregistrer votre voix

```bash
# Créer 10 échantillons de votre voix
python scripts/enroll_voice.py --user-id=marc --samples=10
```

Le script vous demandera de dire des phrases comme:
- "Hopper, ouvre mes emails"
- "Quel temps fait-il aujourd'hui"
- "Rappelle-moi d'appeler Alice"

### 2. Tester la reconnaissance

```bash
python scripts/test_voice_auth.py --user-id=marc --test-audio=test.wav
```

---

## 🧪 Tests Phase 3

### Test complet

```bash
# Tous les tests Phase 3
pytest tests/phase3/ -v

# Test STT uniquement
pytest tests/phase3/test_stt.py -v

# Test pipeline vocal
pytest tests/phase3/test_voice_pipeline.py -v

# Test email
pytest tests/phase3/test_email.py -v
```

### Test de charge

```bash
# Installer locust
pip install locust

# Lancer les tests de charge
locust -f tests/load_test.py --host=http://localhost:5000

# Ouvrir http://localhost:8089
```

---

## 🎯 Scénario de Test Complet

### Préparer le test

```bash
# 1. Démarrer tous les services
make up

# 2. Vérifier que tout est opérationnel
curl http://localhost:5000/health
curl http://localhost:5001/health
curl http://localhost:5003/health
curl http://localhost:5004/health

# 3. Lancer le CLI vocal
./hopper-cli.py --voice
```

### Scénario d'utilisation

```
USER: "Hopper, qu'ai-je manqué aujourd'hui ?"

HOPPER: (analyse emails, calendrier, notifications)
        "Bonjour Marc. Vous avez 2 nouveaux emails importants
         et 1 événement ce soir à 20h."

USER: "Lis les emails"

HOPPER: "Premier email de Alice: Confirmation réunion projet lundi 10h.
         Deuxième email de RH: Rappel déclaration télétravail."

USER: "Réponds au second que c'est noté"

HOPPER: "Voici ma proposition: 'Bonjour, c'est noté, je ferai la
         déclaration cette semaine. Cordialement.'
         Voulez-vous que je l'envoie ?"

USER: "Oui"

HOPPER: "Email envoyé. Autre chose ?"
```

---

## 🐛 Troubleshooting

### Erreur: "pyaudio not found"

```bash
# macOS
brew install portaudio
pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### Erreur: "No audio input device"

```bash
# Vérifier les devices
python -c "import pyaudio; p=pyaudio.PyAudio(); print(p.get_default_input_device_info())"

# Configurer le device dans wake_word.py
detector = WakeWordDetector(device_index=1)
```

### STT trop lent

```bash
# Utiliser modèle Whisper plus petit
# Dans src/stt/server.py, changer:
model = whisper.load_model("tiny")  # au lieu de "base"
```

### TTS qualité médiocre

```bash
# Tester différents modèles Coqui
# Dans src/tts/server.py:
tts = TTS(model_name="tts_models/fr/mai/tacotron2-DDC")
```

### Email connection timeout

```bash
# Vérifier la connexion IMAP
telnet imap.gmail.com 993

# Vérifier les credentials
python -c "import aioimaplib; print('OK')"
```

---

## 📊 Métriques à Surveiller

### Latence

- **STT**: <2s pour 10s d'audio
- **LLM**: <1.5s pour 100 tokens
- **TTS**: <1s pour 50 mots
- **Total**: <5s voix-à-voix

### Ressources

```bash
# Surveiller l'utilisation RAM
docker stats

# Objectif: <30 Go total
```

### Précision

- **STT**: >85% accuracy (WER)
- **Auth Vocale**: >90% recognition
- **Wake Word**: >90% detection, <5% false positives

---

## 🎨 Personnalisation

### Changer le wake word

```python
# src/stt/wake_word.py
detector = WakeWordDetector(wake_word="jarvis")
```

### Ajuster la sensibilité

```python
# 0.0 = moins sensible, 1.0 = plus sensible
detector = WakeWordDetector(sensitivity=0.8)
```

### Voix TTS personnalisée

```python
# Dans src/tts/server.py
tts = TTS(
    model_name="tts_models/fr/mai/tacotron2-DDC",
    speaker="speaker_1"
)
```

---

## 📚 Ressources

### Documentation
- [Plan Phase 3](PHASE3_PLAN.md)
- [Architecture Vocale](VOICE_ARCHITECTURE.md)
- [Configuration Email](EMAIL_SETUP.md)

### Outils
- [Whisper Models](https://github.com/openai/whisper)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [SpeechBrain](https://speechbrain.github.io/)

### Support
- Issues GitHub: [H.O.P.P.E.R Issues](https://github.com/jilani-BLK/H.O.P.P.E.R/issues)
- Discord: [HOPPER Community](#)

---

**Dernière mise à jour**: 22 octobre 2025  
**Version**: Phase 3 v0.1
