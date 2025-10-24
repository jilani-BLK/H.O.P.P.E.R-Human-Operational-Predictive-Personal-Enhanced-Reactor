# 🧠 HOPPER Neural Interface

Interface neuronale 3D interactive en temps réel pour visualiser le cerveau de HOPPER.

![Neural Interface](https://img.shields.io/badge/Status-Beta-orange)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-green)
![Three.js](https://img.shields.io/badge/Three.js-3D-blue)

## ✨ Fonctionnalités

### 🎨 Visualisation 3D
- **50 neurones** organisés en 5 couches (Input, STT, Dispatcher, LLM, Output)
- **Connexions dynamiques** entre neurones adjacents
- **Animation fluide** avec rotation automatique et effets de particules
- **Activité temps réel** : les neurones s'illuminent selon l'activité de HOPPER

### 🎤 Clonage Vocal
- **Clone la voix de HOPPER** depuis l'échantillon audio `Hopper_voix.wav.mp3` (22 sec)
- Utilise **Coqui TTS XTTS-v2** pour synthèse vocale haute fidélité
- Supporte multi-langues (FR, EN, ES, etc.)

### ⚡ Monitoring Temps Réel
- **WebSocket** pour streaming d'événements
- Les neurones **s'accélèrent quand HOPPER parle**
- Tracking des services (STT, LLM, TTS, etc.)
- Logs d'activité colorés par type d'événement

### 📊 HUD Informatif
- Compteur de neurones actifs
- Statut des services
- Latence réseau
- Niveau d'activité

## 🚀 Installation

### 1. Dépendances Python

```bash
# Dépendances vocales
pip install TTS pydub

# Dépendances serveur
pip install fastapi uvicorn websockets httpx

# Optional: pour audio processing
pip install soundfile librosa
```

### 2. Préparer l'échantillon vocal

Placez votre fichier audio à la racine du projet :
```
HOPPER/
├── Hopper_voix.wav.mp3  # 22 secondes d'échantillon vocal
└── ...
```

Formats supportés : WAV, MP3, M4A, FLAC, etc.

## 🎯 Utilisation

### 1. Démarrer le serveur neural interface

```bash
cd web/neural_interface
python neural_server.py
```

Le serveur démarre sur `http://localhost:5050`

### 2. Ouvrir l'interface web

Naviguer vers : **http://localhost:5050/**

Ou utiliser le mode démo :
```
http://localhost:5050/?demo=true
```

### 3. Démarrer l'orchestrator avec monitoring

L'orchestrator s'initialise automatiquement avec le neural monitoring :

```bash
cd src/orchestrator
python main.py
```

### 4. Tester le clonage vocal

```bash
cd src/tts
python voice_cloning.py "Bonjour, je suis HOPPER, votre assistant intelligent!"
```

L'audio généré sera sauvegardé dans `hopper_test_voice.wav`

Écouter :
```bash
afplay hopper_test_voice.wav  # macOS
# ou ouvrir dans votre lecteur audio
```

## 📡 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   HOPPER ORCHESTRATOR               │
│  ┌──────────────────────────────────────────────┐  │
│  │   Neural Activity Monitor (Middleware)       │  │
│  │   - Capture events (STT, LLM, TTS, etc.)     │  │
│  │   - Send to Neural Server via HTTP           │  │
│  └──────────────┬───────────────────────────────┘  │
└─────────────────┼───────────────────────────────────┘
                  │ HTTP POST /api/neural/event
                  ▼
┌─────────────────────────────────────────────────────┐
│            Neural Interface Server                  │
│            (FastAPI + WebSocket)                    │
│  ┌──────────────────────────────────────────────┐  │
│  │   Connection Manager                         │  │
│  │   - Manage WebSocket clients                 │  │
│  │   - Broadcast events to all clients          │  │
│  └──────────────┬───────────────────────────────┘  │
└─────────────────┼───────────────────────────────────┘
                  │ WebSocket ws://localhost:5050/ws/neural
                  ▼
┌─────────────────────────────────────────────────────┐
│          Neural Interface Web (Three.js)            │
│  ┌──────────────────────────────────────────────┐  │
│  │   3D Neural Network Visualization            │  │
│  │   - 50 neurons in 5 layers                   │  │
│  │   - Dynamic connections                      │  │
│  │   - Real-time activity pulsing               │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Composants

#### 1. **Voice Cloning** (`src/tts/voice_cloning.py`)
- Clone la voix de HOPPER avec Coqui TTS XTTS-v2
- Nécessite seulement 6-22 sec d'audio
- Support multi-langues

#### 2. **Neural Server** (`web/neural_interface/neural_server.py`)
- Serveur FastAPI avec WebSocket
- Endpoints HTTP pour recevoir événements
- Broadcasting temps réel vers clients web

#### 3. **Neural Monitor** (`src/orchestrator/neural_monitor.py`)
- Middleware pour l'orchestrator
- Capture automatique des événements
- Queue asynchrone pour performance

#### 4. **Web Interface** (`web/neural_interface/`)
- `index.html` : Structure HTML + HUD
- `neural_visualization.js` : Three.js 3D rendering
- `websocket_client.js` : Client WebSocket + event handling

## 🎮 Events Types

### Neural Activity Events

| Type | Description | Visualisation |
|------|-------------|---------------|
| `input` | Commande utilisateur reçue | Neurones Input actifs |
| `stt` | Speech-to-Text en cours | Neurones STT pulsent (cyan) |
| `dispatch` | Dispatching d'intention | Neurones Dispatcher actifs (orange) |
| `llm` | LLM génère réponse | Neurones LLM pulsent fort (magenta) |
| `tts` | Text-to-Speech génère audio | Neurones Output actifs (jaune) |
| `service` | Appel service générique | Neurones aléatoires (vert) |

### Voice Activity Events

Quand HOPPER parle :
- **pulse_speed x2** : Les neurones s'accélèrent
- **15 neurones** activés simultanément
- Retour à la normale après la parole

## 🔧 Configuration

### Neural Monitor

```python
# Dans src/orchestrator/main.py

neural_monitor = init_neural_monitor(
    neural_server_url="http://localhost:5050",
    enabled=True  # Désactiver en production si nécessaire
)
```

### Neural Server

```python
# Dans web/neural_interface/neural_server.py

# Port du serveur
PORT = 5050

# Fréquence des stats
STATS_INTERVAL = 2  # secondes
```

### Visualization

```javascript
// Dans neural_visualization.js

config = {
    neuronCount: 50,       // Nombre de neurones
    layerCount: 5,         // Nombre de couches
    connectionProbability: 0.15,  // Densité des connexions
    pulseSpeed: 2.0,       // Vitesse de pulsation (x2 quand parle)
    rotationSpeed: 0.001   // Vitesse de rotation
}
```

## 📊 API Reference

### Neural Server Endpoints

#### `GET /`
Interface web principale

#### `GET /health`
Health check + statistiques
```json
{
  "status": "healthy",
  "active_connections": 2,
  "stats": {
    "events_sent": 150,
    "connections_total": 5
  }
}
```

#### `WebSocket /ws/neural`
Endpoint WebSocket pour streaming temps réel

**Messages reçus :**
```json
{
  "type": "neural_activity",
  "payload": {
    "event_type": "llm",
    "intensity": 1.5,
    "metadata": {...}
  }
}
```

#### `POST /api/neural/event`
Envoyer un événement neural
```json
{
  "type": "neural_activity",
  "payload": {
    "event_type": "stt",
    "intensity": 1.0,
    "metadata": {"text": "Hello"}
  }
}
```

#### `POST /api/neural/voice`
Signaler activité vocale
```json
{
  "speaking": true,
  "text": "Bonjour, je suis HOPPER",
  "duration": 2.5
}
```

#### `POST /api/neural/service`
Signaler événement service
```json
{
  "service": "llm",
  "status": "completed",
  "duration": 1.2
}
```

## 🎨 Personnalisation

### Couleurs des neurones

```javascript
// neural_visualization.js

config.baseColor = 0x00ff00;    // Vert (idle)
config.activeColor = 0xff00ff;  // Magenta (actif)
```

### Types de neurones

Modifier les couches dans `createNeuralNetwork()`:
```javascript
const types = [
  'input',      // Layer 0
  'stt',        // Layer 1
  'dispatcher', // Layer 2
  'llm',        // Layer 3
  'output'      // Layer 4
];
```

### Vitesse de parole

```javascript
// websocket_client.js - handleVoiceActivity()

if (speaking) {
    neuralNet.config.pulseSpeed = 4.0;  // Modifier ici
}
```

## 🐛 Troubleshooting

### Le serveur neural ne démarre pas
```bash
# Vérifier que le port 5050 est libre
lsof -i :5050

# Tuer le processus si nécessaire
kill -9 <PID>
```

### L'interface ne se connecte pas
1. Vérifier que le serveur neural tourne : `http://localhost:5050/health`
2. Ouvrir la console navigateur (F12) pour voir les erreurs WebSocket
3. Vérifier les CORS si déployé sur domaine différent

### Le clonage vocal échoue
```bash
# Vérifier l'installation de TTS
python -c "from TTS.api import TTS; print('OK')"

# Vérifier pydub
python -c "from pydub import AudioSegment; print('OK')"

# Vérifier l'échantillon audio
ls -lh Hopper_voix.wav.mp3
```

### Les neurones ne s'animent pas
1. Vérifier que le neural monitor est activé dans l'orchestrator
2. Vérifier les logs du serveur neural
3. Utiliser le mode démo : `?demo=true`

## 📝 TODO / Améliorations futures

- [ ] Support multi-utilisateurs (couleurs différentes par utilisateur)
- [ ] Enregistrement et replay de sessions
- [ ] Graphiques de performance (latence, throughput)
- [ ] Export vidéo de l'activité neuronale
- [ ] Mode VR/AR pour visualisation immersive
- [ ] Fine-tuning du modèle vocal avec plus d'échantillons
- [ ] Reconnaissance d'émotions dans la voix
- [ ] Compression des événements pour performances
- [ ] Dashboard administrateur
- [ ] Alertes visuelles sur erreurs

## 🤝 Contributing

Pour contribuer :
1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

Ce projet fait partie de HOPPER - voir LICENSE pour détails.

## 🙏 Remerciements

- **Coqui TTS** pour le clonage vocal
- **Three.js** pour le rendu 3D
- **FastAPI** pour le serveur WebSocket
- La communauté open-source

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: 24 octobre 2025

Pour questions ou support : ouvrir une issue sur GitHub
