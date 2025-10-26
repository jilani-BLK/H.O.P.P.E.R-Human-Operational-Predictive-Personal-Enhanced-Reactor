# 🎤 Amélioration de la Voix HOPPER - Guide de Démarrage Rapide

## 🎯 Objectif

Améliorer la qualité de la voix de HOPPER en optimisant l'échantillon audio et les paramètres de génération TTS.

## 📁 Nouveaux Outils Créés

| Outil | Description | Usage |
|-------|-------------|-------|
| `improve_hopper_voice.py` | Améliore la qualité audio de l'échantillon | Normalisation, réduction de bruit, égalisation |
| `optimize_voice_params.py` | Teste différentes configurations TTS | Trouve les meilleurs paramètres de génération |
| `test_voice_quality.py` | Compare rapidement tous les échantillons | Test de qualité rapide |
| `improve_voice_workflow.sh` | Workflow complet automatisé | Execute toutes les étapes |

## 🚀 Démarrage Ultra-Rapide

### Option 1 : Workflow Automatique (Recommandé)

```bash
./improve_voice_workflow.sh
```

Ce script execute automatiquement les 3 étapes d'amélioration et vous guide à travers le processus.

### Option 2 : Étape par Étape

#### 1. Analyser vos échantillons
```bash
python improve_hopper_voice.py --compare
```

#### 2. Tester la qualité
```bash
python test_voice_quality.py
```

#### 3. Optimiser les paramètres
```bash
python optimize_voice_params.py
```

## 📊 Situation Actuelle

Vous avez **5 versions** de l'échantillon vocal :

- ⭐ `Hopper_voix_ultra_clean.wav` - **MEILLEUR CHOIX** (24kHz, Mono, Optimisé)
- ⭐ `Hopper_voix_clean.wav` - Excellent (22.05kHz, Mono)
- ✅ `Hopper_voix_24k.wav` - Très bon (24kHz, Mono)
- ✅ `Hopper_voix_hq.wav` - Bon (22.05kHz, Mono)
- ⚠️ `Hopper_voix.wav.mp3` - À améliorer (44.1kHz, Stéréo, MP3)

**Recommandation immédiate :** Utilisez `Hopper_voix_ultra_clean.wav` ou `Hopper_voix_clean.wav`

## 🛠️ Utilisation des Outils

### 1. Amélioration Audio (`improve_hopper_voice.py`)

```bash
# Améliorer un échantillon
python improve_hopper_voice.py Hopper_voix.wav.mp3

# Analyser sans modifier
python improve_hopper_voice.py Hopper_voix_clean.wav --analyze-only

# Comparer toutes les versions
python improve_hopper_voice.py --compare

# Options avancées
python improve_hopper_voice.py fichier.wav \
  --output mon_amelioration.wav \
  --target-level -16.0 \
  --no-denoise  # Désactiver réduction bruit
```

**Améliorations appliquées :**
- ✅ Conversion mono (XTTS-v2 préfère)
- ✅ Réduction de bruit de fond
- ✅ Égalisation vocale (300Hz-8kHz)
- ✅ Compression dynamique
- ✅ Normalisation à -16 dBFS
- ✅ Conversion 22.05kHz

### 2. Optimisation Paramètres (`optimize_voice_params.py`)

```bash
# Tester toutes les configurations
python optimize_voice_params.py

# Lister les configurations disponibles
python optimize_voice_params.py --list-configs

# Tester une config spécifique
python optimize_voice_params.py --config balanced

# Comparer tous les échantillons
python optimize_voice_params.py --compare-samples

# Avec texte personnalisé
python optimize_voice_params.py --text "Votre texte ici"
```

**5 Configurations Disponibles :**

1. **ultra_stable** - Clarté maximale (Temperature: 0.5)
2. **balanced** - Équilibré - RECOMMANDÉ (Temperature: 0.65)
3. **natural** - Plus naturel (Temperature: 0.75)
4. **expressive** - Maximum d'émotions (Temperature: 0.85)
5. **slow_clear** - Lent et clair pour tutoriels (Speed: 0.8)

### 3. Test de Qualité (`test_voice_quality.py`)

```bash
# Test rapide de tous les échantillons
python test_voice_quality.py
```

Génère une comparaison directe avec la même phrase pour tous vos échantillons.

## 📖 Guide Complet

Pour des explications détaillées, consultez :
```bash
cat docs/VOICE_IMPROVEMENT_GUIDE.md
```

## 🎯 Plan d'Action Recommandé

### Phase 1 : Diagnostic (5 min)
```bash
python improve_hopper_voice.py --compare
```
→ Identifiez quel échantillon est déjà le meilleur

### Phase 2 : Test de Qualité (10 min)
```bash
python test_voice_quality.py
```
→ Écoutez et comparez tous les échantillons

### Phase 3 : Optimisation (15 min)
```bash
python optimize_voice_params.py
```
→ Trouvez les meilleurs paramètres de génération

### Phase 4 : Application
→ Mettez à jour `test_voice_clone.py` avec vos choix

## 🔧 Résolution de Problèmes Courants

### Voix robotique ou monotone
- ✅ Augmentez `temperature` (0.65 → 0.75)
- ✅ Utilisez config "natural" ou "expressive"

### Artefacts audio (clics, distorsions)
- ✅ Diminuez `temperature` (0.75 → 0.6)
- ✅ Utilisez config "ultra_stable"
- ✅ Améliorez l'échantillon source

### Voix difficile à comprendre
- ✅ Réduisez `speed` (1.0 → 0.85)
- ✅ Utilisez config "slow_clear"
- ✅ Normalisez l'échantillon

### Volume trop faible/élevé
```bash
python improve_hopper_voice.py fichier.wav --target-level -16.0
```

## 📦 Dépendances

### Déjà installées
- `TTS` - Coqui TTS pour XTTS-v2
- `torch` - PyTorch
- `pydub` - Manipulation audio

### À installer (optionnel mais recommandé)
```bash
./venv_tts/bin/pip install noisereduce scipy soundfile loguru
```

## 📈 Critères de Qualité

Votre voix est optimale si :
- ✅ **Clarté** : Chaque mot est compréhensible
- ✅ **Naturalité** : Son humain, pas robotique
- ✅ **Consistance** : Qualité stable
- ✅ **Émotion** : Capable d'exprimer des nuances
- ✅ **Performance** : Génération rapide (<5s)

## 🎬 Exemple de Workflow Complet

```bash
# 1. Analyser la situation
python improve_hopper_voice.py --compare

# 2. Tester la qualité de tous les échantillons
python test_voice_quality.py
# → Écouter dans data/voice_tests/quality_comparison/

# 3. Optimiser les paramètres avec le meilleur échantillon
python optimize_voice_params.py --sample Hopper_voix_ultra_clean.wav
# → Écouter dans data/voice_tests/

# 4. Choisir votre configuration favorite
# → Notez : échantillon + configuration

# 5. Mettre à jour test_voice_clone.py
# → Utilisez vos meilleurs paramètres
```

## 💡 Conseils d'Expert

### Pour la meilleure qualité :
1. **Démarrez avec** `Hopper_voix_ultra_clean.wav`
2. **Configuration "balanced"** pour usage général
3. **Configuration "slow_clear"** pour tutoriels
4. **Configuration "expressive"** pour conversations

### Pour un nouvel enregistrement :
- Environnement silencieux
- Micro de qualité
- 10-20 secondes de parole variée
- Parler naturellement

## 📞 Support

- **Guide Complet** : `docs/VOICE_IMPROVEMENT_GUIDE.md`
- **Documentation TTS** : `VOICE_CLONING.md`
- **Troubleshooting** : `TROUBLESHOOTING.md`

---

**Créé le :** 24 octobre 2025
**Version :** 1.0
**Statut :** ✅ Prêt à l'emploi
