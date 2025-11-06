#!/bin/bash
# Monitor Phase 3 services health and logs
# Usage: ./monitor_phase3.sh

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================"
echo "📊 HOPPER Phase 3 - Service Monitor"
echo "======================================"
echo ""

# Fonction health check
check_service() {
    local name="$1"
    local url="$2"
    
    echo -n "  ${name}: "
    
    if CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "${url}" 2>/dev/null); then
        if [ "${CODE}" == "200" ]; then
            echo -e "${GREEN}✅ Healthy${NC} (${CODE})"
            return 0
        else
            echo -e "${YELLOW}⚠️  Responding${NC} (${CODE})"
            return 1
        fi
    else
        echo -e "${RED}❌ Unreachable${NC}"
        return 1
    fi
}

# Boucle de monitoring
while true; do
    clear
    
    echo "======================================"
    echo "📊 HOPPER Phase 3 - Service Monitor"
    echo "======================================"
    date "+%Y-%m-%d %H:%M:%S"
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Core Services"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    check_service "Orchestrator    " "http://localhost:5050/health"
    check_service "LLM Engine      " "http://localhost:5001/health"
    check_service "System Executor " "http://localhost:5002/health"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Phase 3 Services"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    check_service "Whisper STT     " "http://localhost:5003/health"
    check_service "Piper TTS       " "http://localhost:5004/health"
    check_service "Voice Auth      " "http://localhost:5007/health"
    check_service "Email Service   " "http://localhost:5008/health"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Storage Services"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    check_service "Qdrant          " "http://localhost:6333/health"
    check_service "Neo4j           " "http://localhost:7474/"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Phase 3 Stats"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if STATS=$(curl -s http://localhost:5050/api/v1/phase3/stats 2>/dev/null); then
        echo "${STATS}" | python3 -m json.tool 2>/dev/null || echo "${STATS}"
    else
        echo -e "${RED}Unable to fetch stats${NC}"
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Docker Containers"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | head -15
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Resource Usage"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Memory
    TOTAL_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" | grep -oE '[0-9]+\.[0-9]+GiB' | head -10 | awk '{s+=$1} END {printf "%.2f", s}')
    echo "  Total RAM: ${TOTAL_MEM}GB (target: <36GB)"
    
    # Top consumers
    echo ""
    echo "  Top 5 memory consumers:"
    docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" | sort -k2 -hr | head -6
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Recent Logs (last 5 lines per service)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo -e "${BLUE}[Orchestrator]${NC}"
    docker-compose logs --tail=3 orchestrator 2>/dev/null | tail -3
    
    echo ""
    echo -e "${BLUE}[Whisper STT]${NC}"
    docker-compose logs --tail=3 whisper 2>/dev/null | tail -3
    
    echo ""
    echo -e "${BLUE}[Piper TTS]${NC}"
    docker-compose logs --tail=3 tts_piper 2>/dev/null | tail -3
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Press Ctrl+C to exit | Refreshing in 10s..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    sleep 10
done
