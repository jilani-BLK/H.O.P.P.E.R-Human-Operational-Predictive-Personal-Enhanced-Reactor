#!/bin/bash
# Test complete Phase 3 workflow
# Usage: ./test_workflow.sh

set -e

ORCHESTRATOR="http://localhost:5050"
API="${ORCHESTRATOR}/api/v1"

echo "======================================"
echo "🧪 HOPPER Phase 3 - Workflow Test"
echo "======================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction test
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local expected_code="${4:-200}"
    
    echo -n "Testing ${name}... "
    
    if [ "${method}" == "GET" ]; then
        CODE=$(curl -s -o /dev/null -w "%{http_code}" "${url}")
    else
        CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${url}")
    fi
    
    if [ "${CODE}" == "${expected_code}" ]; then
        echo -e "${GREEN}✅ OK${NC} (${CODE})"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (${CODE}, expected ${expected_code})"
        return 1
    fi
}

PASSED=0
FAILED=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Health Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Orchestrator
if test_endpoint "Orchestrator" "GET" "${ORCHESTRATOR}/health"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# STT
if test_endpoint "Whisper STT" "GET" "http://localhost:5003/health"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# TTS
if test_endpoint "Piper TTS" "GET" "http://localhost:5004/health"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Email
if test_endpoint "Email Service" "GET" "http://localhost:5008/health"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Phase 3 Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Voice health
if test_endpoint "Voice Health" "GET" "${API}/voice/health"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Phase 3 stats
if test_endpoint "Phase 3 Stats" "GET" "${API}/phase3/stats"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Notifications
if test_endpoint "Notifications" "GET" "${API}/notifications"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Email summary
if test_endpoint "Email Summary" "GET" "${API}/emails/summary?limit=5"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: TTS Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -n "Testing Text-to-Speech... "
RESPONSE=$(curl -s -X POST "${API}/voice/speak" \
    -H "Content-Type: application/json" \
    -d '{"text":"Test de synthèse vocale","voice":"fr_FR-siwis-medium"}' \
    -w "%{http_code}" \
    -o /tmp/hopper_tts_test.wav)

if [ "${RESPONSE}" == "200" ]; then
    SIZE=$(wc -c < /tmp/hopper_tts_test.wav)
    if [ "${SIZE}" -gt 1000 ]; then
        echo -e "${GREEN}✅ OK${NC} (${SIZE} bytes)"
        ((PASSED++))
        
        # Optionnel: jouer l'audio
        echo "Play audio? (y/N)"
        read -n 1 -t 5 PLAY || PLAY="n"
        echo ""
        if [[ "${PLAY}" == "y" || "${PLAY}" == "Y" ]]; then
            if command -v play &> /dev/null; then
                play /tmp/hopper_tts_test.wav
            elif command -v afplay &> /dev/null; then
                afplay /tmp/hopper_tts_test.wav
            fi
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (file too small)"
        ((FAILED++))
    fi
else
    echo -e "${RED}❌ FAIL${NC} (${RESPONSE})"
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Notification Polling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -n "Starting notification polling... "
RESPONSE=$(curl -s -X POST "${API}/notifications/start-polling")
echo "${RESPONSE}"

if echo "${RESPONSE}" | grep -q "started\|running"; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Already running or error${NC}"
fi

echo ""
echo "Waiting 5 seconds..."
sleep 5

echo -n "Checking polling status... "
STATS=$(curl -s "${API}/phase3/stats" | grep -o '"running":[^,}]*')
echo "${STATS}"

if echo "${STATS}" | grep -q "true"; then
    echo -e "${GREEN}✅ Polling active${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Polling not running${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL=$((PASSED + FAILED))
echo "Total tests: ${TOTAL}"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ "${FAILED}" -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test with real audio: ./scripts/test_voice_command.sh"
    echo "  2. Enroll voice profile: ./scripts/enroll_voice.sh your_name"
    echo "  3. Run complete scenario: pytest tests/phase3/test_scenario.py -v"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Debug steps:"
    echo "  1. Check logs: docker-compose logs orchestrator"
    echo "  2. Check services: docker-compose ps"
    echo "  3. Restart services: docker-compose restart"
    exit 1
fi
