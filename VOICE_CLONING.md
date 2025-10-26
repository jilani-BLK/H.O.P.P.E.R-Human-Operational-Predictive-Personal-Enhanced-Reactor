# 🎤 Clonage Vocal HOPPER

## Vue d'ensemble

HOPPER utilise **Coqui TTS XTTS-v2** pour cloner parfaitement votre voix depuis un échantillon audio de 6-22 secondes.

## Prérequis

- Python 3.11 (TTS ne supporte pas encore Python 3.13)
- Échantillon vocal: `Hopper_voix.wav.mp3` (22 secondes)
- ~2.5 GB d'espace disque (modèle XTTS-v2)

## Installation

### 1. Environnement Python 3.11

```bash
# Installer Python 3.11 (si nécessaire)
brew install python@3.11

# Créer l'environnement virtuel
/opt/homebrew/bin/python3.11 -m venv venv_tts

# Installer les dépendances
./venv_tts/bin/pip install TTS pydub torch torchaudio soundfile
```

### 2. Échantillon vocal

Placez votre fichier audio à la racine:
```
HOPPER/
├── Hopper_voix.wav.mp3  ⬅️ 22 secondes de voix claire
└── ...
```

**Recommandations pour l'échantillon:**
- Durée: 6-22 secondes
- Qualité: Audio clair, sans bruit de fond
- Contenu: Parole naturelle et variée
- Format: WAV, MP3, M4A, FLAC, etc.

## Utilisation

### Test complet avec 5 phrases

```bash
./venv_tts/bin/python test_voice_clone.py
```

Génère 5 fichiers audio dans `data/voice_cloning/` avec la voix clonée de HOPPER.

### Texte personnalisé

```bash
./venv_tts/bin/python test_voice_clone.py \
  --text "Bonjour, je suis HOPPER" \
  --emotion neutral
```

**Émotions disponibles:**
- `neutral` - Voix neutre (défaut)
- `happy` - Joyeux
- `sad` - Triste
- `angry` - En colère
- `surprised` - Surpris

### Écouter les résultats

```bash
# Ouvrir le dossier
open data/voice_cloning/

# Jouer un fichier
afplay data/voice_cloning/hopper_clone_1.wav
```

## Architecture technique

### XTTS-v2 (Coqui TTS)

- **Modèle**: `tts_models/multilingual/multi-dataset/xtts_v2`
- **Taille**: ~2 GB
- **Langues**: Multilingue (français inclus)
- **Qualité**: Clonage haute fidélité avec seulement 6s d'audio

### Flux de clonage

```
Hopper_voix.wav.mp3
        ↓
  Préparation audio
  (conversion WAV)
        ↓
   Modèle XTTS-v2
   (analyse vocale)
        ↓
   Génération TTS
  (avec voix clonée)
        ↓
  hopper_clone_*.wav
```

### Intégration avec HOPPER

Le module `src/tts/voice_cloning.py` fournit la classe `HopperVoiceCloner`:

```python
from src.tts.voice_cloning import HopperVoiceCloner

# Initialiser
cloner = HopperVoiceCloner(
    voice_sample_path="Hopper_voix.wav.mp3",
    device="auto"  # CPU, CUDA, ou MPS (Apple Silicon)
)

# Charger le modèle
cloner.load_model()

# Préparer l'échantillon
speaker_wav = cloner.prepare_voice_sample()

# Générer
cloner.generate_speech(
    text="Bonjour, je suis HOPPER",
    output_path="output.wav",
    language="fr",
    temperature=0.7,
    speed=1.0
)
```

## Performance

### Sur Apple Silicon (M1/M2/M3)

- **Device**: MPS (Metal Performance Shaders)
- **Première génération**: ~5-10 secondes (chargement modèle)
- **Générations suivantes**: ~2-3 secondes par phrase
- **Mémoire**: ~2-3 GB RAM

### Sur CPU

- **Première génération**: ~20-30 secondes
- **Générations suivantes**: ~10-15 secondes par phrase
- **Mémoire**: ~2-3 GB RAM

### Sur CUDA (GPU NVIDIA)

- **Première génération**: ~2-3 secondes
- **Générations suivantes**: <1 seconde par phrase
- **Mémoire**: ~2 GB VRAM

## Dépannage

### Erreur: "TTS not installed"

```bash
./venv_tts/bin/pip install TTS
```

### Erreur: "No module named 'torch'"

```bash
./venv_tts/bin/pip install torch torchaudio
```

### Erreur: "Voice sample not found"

Vérifiez que `Hopper_voix.wav.mp3` est bien à la racine du projet.

### Modèle trop long à télécharger

Le modèle XTTS-v2 fait ~2GB. Sur une connexion lente, cela peut prendre 10-20 minutes. Le modèle est mis en cache localement après le premier téléchargement.

### Qualité audio médiocre

- Vérifiez la qualité de votre échantillon vocal
- Essayez d'augmenter la durée (jusqu'à 22 secondes)
- Assurez-vous qu'il n'y a pas de bruit de fond
- Ajustez la `temperature` (0.5-1.0)

## Avantages du clonage vocal

✅ **Consistance**: Voix identique sur toutes les générations
✅ **Personnalisation**: La vraie voix de HOPPER
✅ **Multilingue**: Fonctionne en français et autres langues
✅ **Émotions**: Support des nuances émotionnelles
✅ **Qualité**: Audio haute fidélité (22kHz)

## Alternatives

### Pour un prototype rapide (sans clonage)

Utilisez `test_voice_direct.py` qui utilise les voix système de macOS:

```bash
python test_voice_direct.py
```

Voix disponibles: Thomas (masculin), Amélie (féminin)

### Comparaison

| Méthode | Qualité | Personnalisation | Vitesse | Setup |
|---------|---------|------------------|---------|-------|
| XTTS-v2 | ⭐⭐⭐⭐⭐ | Voix unique | ⭐⭐⭐ | Complexe |
| macOS say | ⭐⭐⭐ | Voix standard | ⭐⭐⭐⭐⭐ | Simple |

## Ressources

- [Coqui TTS Documentation](https://docs.coqui.ai/)
- [XTTS-v2 Paper](https://arxiv.org/abs/2310.19889)
- [GitHub Coqui TTS](https://github.com/coqui-ai/TTS)

## Licence

Le module de clonage vocal HOPPER utilise Coqui TTS sous licence MPL 2.0.
