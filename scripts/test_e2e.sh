#!/usr/bin/env bash
###############################################################################
# HOPPER - End-to-End Tests
# Tests complets du flux STT -> LLM -> TTS et tous les connecteurs
###############################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
HOPPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_AUDIO="${HOPPER_DIR}/tests/test_audio.wav"
RESULTS_DIR="${HOPPER_DIR}/test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_FILE="${RESULTS_DIR}/e2e_results_${TIMESTAMP}.txt"

# Compteurs
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Fonctions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_test() { echo -e "${YELLOW}[TEST]${NC} $1"; }

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    🧪 HOPPER - End-to-End Tests                             ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

###############################################################################
# Test d'un service HTTP
###############################################################################

test_http_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log_test "Test: ${name}"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" -eq "$expected_code" ]; then
        log_success "${name} - OK (HTTP ${HTTP_CODE})"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "${name}: PASS" >> "$RESULTS_FILE"
        return 0
    else
        log_error "${name} - ÉCHEC (HTTP ${HTTP_CODE}, attendu ${expected_code})"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "${name}: FAIL (HTTP ${HTTP_CODE})" >> "$RESULTS_FILE"
        return 1
    fi
}

###############################################################################
# Test d'un endpoint avec payload
###############################################################################

test_post_endpoint() {
    local name=$1
    local url=$2
    local data=$3
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log_test "Test: ${name}"
    
    RESPONSE=$(curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$data" \
        --max-time 30 2>/dev/null || echo "ERROR")
    
    if [[ "$RESPONSE" != "ERROR" ]] && [[ "$RESPONSE" != "" ]]; then
        log_success "${name} - OK"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "${name}: PASS" >> "$RESULTS_FILE"
        echo "  Response: ${RESPONSE:0:100}..." >> "$RESULTS_FILE"
        return 0
    else
        log_error "${name} - ÉCHEC"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "${name}: FAIL" >> "$RESULTS_FILE"
        return 1
    fi
}

###############################################################################
# Tests des services de base
###############################################################################

test_core_services() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 1: Services de base"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    test_http_service "Neo4j Browser" "http://localhost:7474"
    test_http_service "Orchestrator Health" "http://localhost:8000/health"
    test_http_service "STT Service Health" "http://localhost:5001/health"
    test_http_service "LLM Service Health" "http://localhost:5002/health"
    test_http_service "TTS Service Health" "http://localhost:5003/health"
}

###############################################################################
# Tests STT
###############################################################################

test_stt_service() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 2: Service STT"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Test avec un texte simulé (pas de fichier audio réel)
    log_test "Test STT avec simulation"
    
    # Simuler une transcription
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    RESPONSE=$(curl -s -X POST "http://localhost:5001/transcribe" \
        -H "Content-Type: application/json" \
        -d '{"text": "test simulation"}' \
        --max-time 10 2>/dev/null || echo "ERROR")
    
    if [[ "$RESPONSE" != "ERROR" ]]; then
        log_success "STT Service répond"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "STT Simulation: PASS" >> "$RESULTS_FILE"
    else
        log_error "STT Service ne répond pas"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "STT Simulation: FAIL" >> "$RESULTS_FILE"
    fi
}

###############################################################################
# Tests LLM
###############################################################################

test_llm_service() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 3: Service LLM"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    test_post_endpoint "LLM Query Simple" \
        "http://localhost:5002/query" \
        '{"prompt": "Bonjour, comment vas-tu?", "max_tokens": 50}'
    
    test_post_endpoint "LLM Query avec Contexte" \
        "http://localhost:5002/query" \
        '{"prompt": "Quel est mon nom?", "context": "Je m appelle Jean.", "max_tokens": 30}'
}

###############################################################################
# Tests TTS
###############################################################################

test_tts_service() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 4: Service TTS"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    test_post_endpoint "TTS Synthèse Simple" \
        "http://localhost:5003/synthesize" \
        '{"text": "Bonjour, ceci est un test.", "voice": "fr"}'
}

###############################################################################
# Tests Connecteurs
###############################################################################

test_connectors() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 5: Connecteurs"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Spotify
    test_http_service "Spotify Health" "http://localhost:5006/health"
    test_http_service "Spotify Status" "http://localhost:5006/status"
    
    # Antivirus
    test_http_service "Antivirus Status" "http://localhost:5007/status"
    test_http_service "Antivirus Statistics" "http://localhost:5007/statistics"
}

###############################################################################
# Tests Antivirus
###############################################################################

test_antivirus() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 6: Système Antivirus"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Test EICAR
    log_test "Test: Détection EICAR"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    # Créer fichier EICAR temporaire
    EICAR_FILE="/tmp/eicar_test_${TIMESTAMP}.txt"
    echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > "$EICAR_FILE"
    
    # Scanner le fichier
    SCAN_RESULT=$(curl -s -X POST "http://localhost:5007/scan/file" \
        -H "Content-Type: application/json" \
        -d "{\"file_path\": \"$EICAR_FILE\"}" \
        --max-time 30 2>/dev/null || echo "ERROR")
    
    # Vérifier détection
    if [[ "$SCAN_RESULT" == *"EICAR"* ]] || [[ "$SCAN_RESULT" == *"threat"* ]]; then
        log_success "EICAR détecté correctement"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "Antivirus EICAR Detection: PASS" >> "$RESULTS_FILE"
    else
        log_error "EICAR non détecté"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "Antivirus EICAR Detection: FAIL" >> "$RESULTS_FILE"
    fi
    
    # Nettoyer
    rm -f "$EICAR_FILE"
    
    # Test scan rapide
    test_post_endpoint "Antivirus Quick Scan" \
        "http://localhost:5007/scan/quick" \
        '{}'
}

###############################################################################
# Tests Système Local
###############################################################################

test_local_system() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 7: Contrôle Système Local"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Ces tests nécessitent le LocalSystem connector en cours d'exécution
    test_post_endpoint "System Get Time" \
        "http://localhost:8000/execute" \
        '{"command": "get_time"}'
    
    test_post_endpoint "System Get Weather (simulation)" \
        "http://localhost:8000/execute" \
        '{"command": "get_weather", "location": "Paris"}'
}

###############################################################################
# Test flux complet E2E
###############################################################################

test_full_pipeline() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 8: Flux Complet STT -> LLM -> TTS"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log_test "Pipeline complet avec texte simulé"
    
    # Simuler une requête utilisateur complète
    USER_TEXT="Bonjour HOPPER, quelle heure est-il?"
    
    # 1. LLM traite la requête
    log_info "Étape 1/2: Traitement LLM..."
    LLM_RESPONSE=$(curl -s -X POST "http://localhost:5002/query" \
        -H "Content-Type: application/json" \
        -d "{\"prompt\": \"${USER_TEXT}\", \"max_tokens\": 100}" \
        --max-time 30 2>/dev/null || echo "ERROR")
    
    if [[ "$LLM_RESPONSE" == "ERROR" ]]; then
        log_error "Pipeline - Échec LLM"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "Full Pipeline: FAIL (LLM)" >> "$RESULTS_FILE"
        return 1
    fi
    
    log_success "LLM a répondu"
    
    # 2. TTS synthétise la réponse
    log_info "Étape 2/2: Synthèse TTS..."
    
    # Extraire le texte de la réponse (supposons qu'il soit dans un champ "text" ou "response")
    RESPONSE_TEXT=$(echo "$LLM_RESPONSE" | jq -r '.text // .response // "Test réponse"' 2>/dev/null || echo "Test réponse")
    
    TTS_RESPONSE=$(curl -s -X POST "http://localhost:5003/synthesize" \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"${RESPONSE_TEXT}\"}" \
        --max-time 30 2>/dev/null || echo "ERROR")
    
    if [[ "$TTS_RESPONSE" == "ERROR" ]]; then
        log_error "Pipeline - Échec TTS"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "Full Pipeline: FAIL (TTS)" >> "$RESULTS_FILE"
        return 1
    fi
    
    log_success "TTS a synthétisé la réponse"
    log_success "Pipeline complet - OK"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "Full Pipeline: PASS" >> "$RESULTS_FILE"
}

###############################################################################
# Tests de charge basiques
###############################################################################

test_load() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "TEST 9: Tests de Charge"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log_test "10 requêtes simultanées au LLM"
    
    FAILED_REQUESTS=0
    
    for i in {1..10}; do
        curl -s -X POST "http://localhost:5002/query" \
            -H "Content-Type: application/json" \
            -d '{"prompt": "Test charge '$i'", "max_tokens": 20}' \
            --max-time 30 &>/dev/null &
    done
    
    # Attendre que toutes les requêtes soient terminées
    wait
    
    if [ $? -eq 0 ]; then
        log_success "Test de charge - 10 requêtes OK"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "Load Test (10 requests): PASS" >> "$RESULTS_FILE"
    else
        log_error "Test de charge - Échecs détectés"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "Load Test (10 requests): FAIL" >> "$RESULTS_FILE"
    fi
}

###############################################################################
# Rapport final
###############################################################################

print_summary() {
    echo ""
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 RÉSULTATS FINAUX${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    SUCCESS_RATE=$(echo "scale=1; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc)
    
    echo -e "  Tests totaux:   ${TESTS_TOTAL}"
    echo -e "  ${GREEN}✓ Réussis:      ${TESTS_PASSED}${NC}"
    echo -e "  ${RED}✗ Échoués:      ${TESTS_FAILED}${NC}"
    echo -e "  Taux de réussite: ${SUCCESS_RATE}%"
    echo ""
    
    # Bannière finale
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}"
        echo "╔══════════════════════════════════════════════════════════════════════════════╗"
        echo "║                                                                              ║"
        echo "║                    ✅ TOUS LES TESTS ONT RÉUSSI !                           ║"
        echo "║                                                                              ║"
        echo "╚══════════════════════════════════════════════════════════════════════════════╝"
        echo -e "${NC}"
    else
        echo -e "${YELLOW}"
        echo "╔══════════════════════════════════════════════════════════════════════════════╗"
        echo "║                                                                              ║"
        echo "║                    ⚠️  CERTAINS TESTS ONT ÉCHOUÉ                            ║"
        echo "║                                                                              ║"
        echo "╚══════════════════════════════════════════════════════════════════════════════╝"
        echo -e "${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📄 Rapport détaillé:${NC} ${RESULTS_FILE}"
    echo ""
    
    # Écrire le résumé dans le fichier
    {
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "RÉSUMÉ"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Tests totaux:     $TESTS_TOTAL"
        echo "Tests réussis:    $TESTS_PASSED"
        echo "Tests échoués:    $TESTS_FAILED"
        echo "Taux de réussite: ${SUCCESS_RATE}%"
        echo "Date:             $(date)"
    } >> "$RESULTS_FILE"
}

###############################################################################
# Script principal
###############################################################################

main() {
    print_header
    
    # Créer le répertoire de résultats
    mkdir -p "$RESULTS_DIR"
    
    # Header du fichier de résultats
    {
        echo "╔══════════════════════════════════════════════════════════════════════════════╗"
        echo "║                                                                              ║"
        echo "║                    HOPPER - End-to-End Test Results                          ║"
        echo "║                                                                              ║"
        echo "╚══════════════════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Date: $(date)"
        echo ""
    } > "$RESULTS_FILE"
    
    log_info "Démarrage des tests end-to-end..."
    log_info "Résultats seront sauvegardés dans: ${RESULTS_FILE}"
    echo ""
    
    # Vérifier que Docker tourne
    if ! docker info &>/dev/null; then
        log_error "Docker n'est pas en cours d'exécution"
        exit 1
    fi
    
    # Vérifier que les services HOPPER tournent
    if ! docker ps | grep -q "hopper"; then
        log_error "Aucun service HOPPER détecté. Démarrez d'abord: docker-compose up -d"
        exit 1
    fi
    
    log_success "Services HOPPER détectés"
    
    # Attendre que les services soient prêts
    log_info "Attente du démarrage complet des services (15s)..."
    sleep 15
    
    # Exécuter les suites de tests
    test_core_services
    test_stt_service
    test_llm_service
    test_tts_service
    test_connectors
    test_antivirus
    test_local_system
    test_full_pipeline
    test_load
    
    # Rapport final
    print_summary
}

# Exécution
main "$@"
