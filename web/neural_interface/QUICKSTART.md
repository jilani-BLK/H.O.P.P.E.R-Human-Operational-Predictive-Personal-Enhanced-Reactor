# 🚀 Guide de Démarrage Rapide - Neural Interface

## Installation en 3 minutes

### 1️⃣ Installer les dépendances

```bash
cd web/neural_interface
pip install -r requirements.txt
```

### 2️⃣ Placer l'échantillon vocal

Copiez votre fichier `Hopper_voix.wav.mp3` (22 sec) à la racine du projet :

```
HOPPER/
├── Hopper_voix.wav.mp3  ⬅️ ICI
├── web/
│   └── neural_interface/
└── ...
```

### 3️⃣ Démarrer l'interface

**Option A : Script automatique (recommandé)**
```bash
./start_neural_interface.sh
```

**Option B : Manuel**
```bash
python3 neural_server.py
```

### 4️⃣ Ouvrir dans le navigateur

Naviguer vers : **http://localhost:5050/**

## 🎮 Utilisation

### Mode Normal
L'interface se connecte automatiquement à l'orchestrator et affiche l'activité en temps réel.

### Mode Démo
Pour tester sans orchestrator :
```
http://localhost:5050/?demo=true
```

### Tester le clonage vocal

```bash
cd ../../src/tts
python voice_cloning.py "Bonjour, je suis HOPPER!"
afplay hopper_test_voice.wav
```

## 🎨 Ce que vous verrez

- **50 neurones** organisés en réseau 3D
- **Connexions lumineuses** entre neurones
- **Pulsations** selon l'activité de HOPPER
- **Accélération** quand HOPPER parle
- **Logs temps réel** des événements

## 🔧 Intégration avec l'orchestrator

L'orchestrator est déjà configuré pour envoyer les événements :

1. Démarrer l'interface neural (port 5050)
2. Démarrer l'orchestrator (port 5000)
3. Envoyer des commandes via le CLI
4. Observer l'activité neuronale en temps réel !

## ❓ Problèmes courants

**Port 5050 déjà utilisé ?**
```bash
# Modifier le port dans neural_server.py (ligne 256)
uvicorn.run(..., port=5051)
```

**TTS non installé ?**
```bash
pip install TTS pydub
```

**L'interface ne se connecte pas ?**
- Vérifier que le serveur tourne : `curl http://localhost:5050/health`
- Vérifier la console navigateur (F12)

## 📚 Documentation complète

Voir `README.md` pour tous les détails.

---

**Bon voyage dans le cerveau de HOPPER !** 🧠✨
