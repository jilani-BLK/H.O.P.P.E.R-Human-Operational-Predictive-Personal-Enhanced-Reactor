#!/usr/bin/env bash
###############################################################################
# HOPPER - Quick Tests
# Tests rapides des services disponibles
###############################################################################

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║          🧪 HOPPER - Tests Rapides                          ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

PASSED=0
FAILED=0

test_service() {
    local name=$1
    local url=$2
    
    echo -n "Testing ${name}... "
    
    if curl -s --max-time 3 "$url" &>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
    fi
}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Services Core${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_service "Neo4j Browser     " "http://localhost:7474"
test_service "Orchestrator      " "http://localhost:5050/health"
test_service "STT Service       " "http://localhost:5003/health"
test_service "TTS Service       " "http://localhost:5004/health"
test_service "Auth Service      " "http://localhost:5005/health"
test_service "System Executor   " "http://localhost:5002/health"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Résumé${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Total tests: $((PASSED + FAILED))"
echo -e "${GREEN}Réussis: ${PASSED}${NC}"
echo -e "${RED}Échoués: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Tous les tests ont réussi !${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Certains services ne sont pas disponibles${NC}"
    echo "Pour plus de détails: docker-compose logs"
    exit 1
fi
