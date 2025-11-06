#!/bin/bash
# Enroll user voice for speaker recognition
# Usage: ./enroll_voice.sh <user_id>

set -e

USER_ID="${1:-default}"
VOICE_AUTH_URL="http://localhost:5007"
OUTPUT_DIR="data/voice_profiles/${USER_ID}"
TEMP_DIR="/tmp/hopper_voice_enrollment"

echo "======================================"
echo "🎤 HOPPER Voice Enrollment"
echo "======================================"
echo ""
echo "User ID: ${USER_ID}"
echo "Output: ${OUTPUT_DIR}"
echo ""

# Créer dossiers
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${TEMP_DIR}"

# Vérifier que le service est actif
echo "Checking voice auth service..."
if ! curl -s "${VOICE_AUTH_URL}/health" > /dev/null; then
    echo "❌ Voice auth service not reachable at ${VOICE_AUTH_URL}"
    echo "Start it with: docker-compose up -d auth_voice"
    exit 1
fi
echo "✅ Voice auth service is running"
echo ""

# Enregistrer 5 échantillons
echo "📝 Instructions:"
echo "You will be asked to record 5 voice samples."
echo "Please speak clearly for 3-5 seconds each time."
echo "Say a sentence like: 'Hopper, what did I miss today?'"
echo ""

for i in {1..5}; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Recording sample ${i}/5"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Press ENTER to start recording..."
    read
    
    OUTPUT_FILE="${TEMP_DIR}/sample_${i}.wav"
    
    echo "🔴 RECORDING... (Press Ctrl+C when done)"
    echo ""
    
    # Enregistrer avec SoX (Mac: brew install sox)
    if command -v rec &> /dev/null; then
        rec -r 16000 -c 1 -b 16 "${OUTPUT_FILE}" silence 1 0.1 3% 1 2.0 3%
    elif command -v arecord &> /dev/null; then
        # Linux alternative
        arecord -f cd -d 5 "${OUTPUT_FILE}"
    else
        echo "❌ No recording tool found. Install sox: brew install sox"
        exit 1
    fi
    
    echo ""
    echo "✅ Sample ${i} recorded: ${OUTPUT_FILE}"
    echo "Size: $(du -h "${OUTPUT_FILE}" | cut -f1)"
    echo ""
    
    # Optionnel: rejouer
    echo "Play back? (y/N)"
    read -n 1 PLAY
    echo ""
    if [[ "${PLAY}" == "y" || "${PLAY}" == "Y" ]]; then
        if command -v play &> /dev/null; then
            play "${OUTPUT_FILE}"
        elif command -v aplay &> /dev/null; then
            aplay "${OUTPUT_FILE}"
        fi
    fi
    
    echo ""
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📤 Enrolling voice profile..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Envoyer au service d'authentification
for i in {1..5}; do
    SAMPLE_FILE="${TEMP_DIR}/sample_${i}.wav"
    
    echo "Uploading sample ${i}..."
    
    RESPONSE=$(curl -s -X POST "${VOICE_AUTH_URL}/enroll" \
        -F "user_id=${USER_ID}" \
        -F "audio=@${SAMPLE_FILE}" \
        -F "sample_number=${i}")
    
    echo "Response: ${RESPONSE}"
    
    # Copier dans data/
    cp "${SAMPLE_FILE}" "${OUTPUT_DIR}/sample_${i}.wav"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Voice enrollment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "User ID: ${USER_ID}"
echo "Samples: ${OUTPUT_DIR}"
echo ""
echo "Test verification with:"
echo "  ./scripts/test_voice_auth.sh ${USER_ID}"
echo ""

# Cleanup
rm -rf "${TEMP_DIR}"
