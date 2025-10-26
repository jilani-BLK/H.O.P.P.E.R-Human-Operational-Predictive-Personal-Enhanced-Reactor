#!/bin/bash

# 🎤 Script de Démarrage Rapide pour l'Amélioration Vocale HOPPER
# Execute les 3 étapes principales d'amélioration

set -e

echo "======================================================================"
echo "🎤 HOPPER VOICE IMPROVEMENT - WORKFLOW COMPLET"
echo "======================================================================"
echo ""

# Vérifier Python et venv
if [ ! -d "venv_tts" ]; then
    echo "❌ Environnement venv_tts non trouvé"
    echo ""
    echo "💡 Créer l'environnement:"
    echo "   /opt/homebrew/bin/python3.11 -m venv venv_tts"
    echo "   ./venv_tts/bin/pip install TTS pydub torch torchaudio loguru noisereduce scipy soundfile"
    exit 1
fi

PYTHON="./venv_tts/bin/python"

# Vérifier que TTS est installé
if ! $PYTHON -c "import TTS" 2>/dev/null; then
    echo "❌ TTS non installé dans venv_tts"
    echo ""
    echo "💡 Installation:"
    echo "   ./venv_tts/bin/pip install TTS pydub torch torchaudio loguru noisereduce scipy soundfile"
    exit 1
fi

echo "✅ Environnement Python configuré"
echo ""

# Étape 1: Analyse des échantillons existants
echo "======================================================================"
echo "📊 ÉTAPE 1/3: ANALYSE DES ÉCHANTILLONS"
echo "======================================================================"
echo ""

$PYTHON improve_hopper_voice.py --compare

echo ""
read -p "Appuyez sur Entrée pour continuer..."
echo ""

# Étape 2: Test de qualité rapide
echo "======================================================================"
echo "🔬 ÉTAPE 2/3: TEST DE QUALITÉ"
echo "======================================================================"
echo ""
echo "Génération de tests avec tous les échantillons disponibles..."
echo ""

$PYTHON test_voice_quality.py

echo ""
echo "💡 Écoutez les fichiers dans: data/voice_tests/quality_comparison/"
echo ""
read -p "Appuyez sur Entrée après avoir écouté les tests..."
echo ""

# Étape 3: Optimisation des paramètres
echo "======================================================================"
echo "🎚️  ÉTAPE 3/3: OPTIMISATION DES PARAMÈTRES"
echo "======================================================================"
echo ""
echo "Test de toutes les configurations de paramètres..."
echo ""

$PYTHON optimize_voice_params.py

echo ""
echo "💡 Écoutez les fichiers dans: data/voice_tests/"
echo ""
echo "======================================================================"
echo "✅ WORKFLOW TERMINÉ"
echo "======================================================================"
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo ""
echo "1. Écoutez tous les fichiers générés:"
echo "   open data/voice_tests/"
echo ""
echo "2. Identifiez:"
echo "   - Le meilleur échantillon source (quality_comparison/)"
echo "   - La meilleure configuration de paramètres"
echo ""
echo "3. Notez votre choix et mettez à jour test_voice_clone.py"
echo ""
echo "4. Consultez le guide complet:"
echo "   cat docs/VOICE_IMPROVEMENT_GUIDE.md"
echo ""
echo "======================================================================"
