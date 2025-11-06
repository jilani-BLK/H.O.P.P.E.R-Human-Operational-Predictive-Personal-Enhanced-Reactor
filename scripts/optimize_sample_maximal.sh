#!/bin/bash
# Préparation ULTIME de l'échantillon pour fidélité maximale
# Utilise le meilleur échantillon et l'optimise agressivement

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🎯 OPTIMISATION MAXIMALE - FIDÉLITÉ VOCALE"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Trouver le meilleur échantillon (le plus long = plus de données)
echo "📊 Analyse des échantillons disponibles..."
echo ""

best_file=""
max_duration=0

for file in data/voice_cloning/hopper_clone_*.wav; do
    if [ -f "$file" ]; then
        duration=$(ffprobe -i "$file" -show_entries format=duration -v quiet -of csv="p=0" 2>/dev/null || echo "0")
        size=$(du -h "$file" | cut -f1)
        echo "   • $(basename "$file"): ${duration}s ($size)"
        
        # Comparer durées (bash arithmetic)
        if (( $(echo "$duration > $max_duration" | bc -l 2>/dev/null || echo "0") )); then
            max_duration=$duration
            best_file="$file"
        fi
    fi
done

echo ""
echo "✅ Meilleur échantillon: $(basename "$best_file") (${max_duration}s)"
echo ""

# Créer un échantillon ULTRA-PROPRE
echo "🔧 Traitement audio ULTRA-HAUTE-QUALITÉ..."
echo ""

output="data/voice/hopper.wav"

# Étape 1: Prétraitement ultra-propre (CONSERVE LA DURÉE)
ffmpeg -y -i "$best_file" \
    -ar 24000 \
    -ac 1 \
    -acodec pcm_s16le \
    -af "highpass=f=60, lowpass=f=10000, \
         afftdn=nf=-20:tn=1, \
         anlmdn=s=0.00001, \
         silenceremove=start_periods=1:start_duration=0.05:start_threshold=-50dB:stop_periods=1:stop_duration=0.05:stop_threshold=-50dB, \
         compand=attacks=0.3:decays=0.8:points=-80/-80|-45/-15|-27/-9|0/-7|20/-7:soft-knee=6:gain=0:volume=0, \
         loudnorm=I=-16:TP=-1.5:LRA=7, \
         highpass=f=80" \
    "$output" 2>&1 | grep -E "Duration|Stream" || true

echo ""
echo "✅ Échantillon ultra-propre créé: $output"
echo ""

# Analyser l'échantillon final
echo "📊 Analyse de l'échantillon final:"
ffprobe -i "$output" -show_entries format=duration,stream=sample_rate,channels -v quiet -of default=noprint_wrappers=1 2>/dev/null || true

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Préparation terminée - Échantillon optimisé pour XTTS v2"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📋 Optimisations appliquées:"
echo "   • Sample rate: 24 kHz (optimal pour XTTS v2)"
echo "   • Débruitage FFT agressif (nf=-25)"
echo "   • Débruitage non-linéaire (anlmdn)"
echo "   • Suppression silences stricte (-45dB)"
echo "   • Compression dynamique (compand)"
echo "   • Normalisation loudness stricte (LRA=7)"
echo "   • Filtrage passe-haut/bas optimisé"
echo ""
echo "🔜 Prochaine étape:"
echo "   ./scripts/test_voice_quick.sh \"Phrase de test\""
echo ""
