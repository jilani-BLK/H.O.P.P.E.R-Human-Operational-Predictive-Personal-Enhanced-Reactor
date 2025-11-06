#!/bin/bash
# Installation Piper TTS - Voix naturelle hors ligne
# Meilleure alternative locale aux voix robotiques

set -e

echo "🎤 Installation Piper TTS - Voix Naturelle Hors Ligne"
echo "======================================================"
echo ""

# Détecter architecture
ARCH=$(uname -m)
OS=$(uname -s)

if [ "$OS" != "Darwin" ]; then
    echo "❌ Ce script est pour macOS uniquement"
    exit 1
fi

PIPER_DIR="/Users/jilani/Projet/piper-tts"
MODELS_DIR="$PIPER_DIR/models"

# Télécharger Piper pour macOS ARM64
echo "📥 Téléchargement Piper pour macOS ARM64..."

mkdir -p "$PIPER_DIR"
cd "$PIPER_DIR"

# URL du build macOS (Piper pre-compiled)
if [ "$ARCH" = "arm64" ]; then
    PIPER_URL="https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_macos_aarch64.tar.gz"
else
    PIPER_URL="https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_macos_x86_64.tar.gz"
fi

if [ ! -f "piper" ]; then
    echo "   Téléchargement depuis GitHub..."
    curl -L "$PIPER_URL" -o piper.tar.gz
    tar -xzf piper.tar.gz
    chmod +x piper
    rm piper.tar.gz
    echo "   ✅ Piper installé"
else
    echo "   ✅ Piper déjà installé"
fi

# Télécharger modèles français de haute qualité
echo ""
echo "📦 Téléchargement modèles vocaux français..."

mkdir -p "$MODELS_DIR/fr"
cd "$MODELS_DIR/fr"

# Modèle français haute qualité (siwis medium)
if [ ! -f "fr_FR-siwis-medium.onnx" ]; then
    echo "   🇫🇷 Modèle français haute qualité..."
    curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx" -o fr_FR-siwis-medium.onnx
    curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json" -o fr_FR-siwis-medium.onnx.json
    echo "   ✅ Modèle téléchargé (~50 MB)"
else
    echo "   ✅ Modèle déjà présent"
fi

# Modèle français voix masculine (gilles low - plus rapide)
if [ ! -f "fr_FR-gilles-low.onnx" ]; then
    echo "   🧑 Modèle français voix masculine (rapide)..."
    curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/gilles/low/fr_FR-gilles-low.onnx" -o fr_FR-gilles-low.onnx
    curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/gilles/low/fr_FR-gilles-low.onnx.json" -o fr_FR-gilles-low.onnx.json
    echo "   ✅ Modèle téléchargé (~20 MB)"
else
    echo "   ✅ Modèle déjà présent"
fi

echo ""
echo "=" * 70
echo "✅ Installation terminée!"
echo "=" * 70
echo ""
echo "📍 Installation:"
echo "   Piper: $PIPER_DIR/piper"
echo "   Modèles: $MODELS_DIR/fr/"
echo ""
echo "🎤 Modèles disponibles:"
echo ""
echo "   1. fr_FR-siwis-medium (RECOMMANDÉ)"
echo "      - Qualité: ⭐⭐⭐⭐⭐ Très naturelle"
echo "      - Voix: Féminine, claire, professionnelle"
echo "      - Vitesse: Moyenne (~2-3s par phrase)"
echo ""
echo "   2. fr_FR-gilles-low (RAPIDE)"
echo "      - Qualité: ⭐⭐⭐⭐ Naturelle"
echo "      - Voix: Masculine, jeune, dynamique"
echo "      - Vitesse: Rapide (~1-2s par phrase)"
echo ""
echo "🧪 Test rapide:"
echo ""
echo "   # Voix féminine (siwis)"
echo "   $PIPER_DIR/piper --model $MODELS_DIR/fr/fr_FR-siwis-medium.onnx \\"
echo "     --output_file test.wav \\"
echo "     <<< \"Bonjour, je suis HOPPER, votre assistant intelligent.\""
echo "   afplay test.wav"
echo ""
echo "   # Voix masculine (gilles)"
echo "   $PIPER_DIR/piper --model $MODELS_DIR/fr/fr_FR-gilles-low.onnx \\"
echo "     --output_file test.wav \\"
echo "     <<< \"Bonjour, je suis HOPPER, votre assistant intelligent.\""
echo "   afplay test.wav"
echo ""
echo "🚀 Intégration HOPPER:"
echo "   Le script Python est déjà prêt!"
echo "   python3 dialogue_hopper.py"
echo ""
echo "=" * 70
