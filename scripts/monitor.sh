#!/usr/bin/env bash
###############################################################################
# HOPPER - Monitor Script
# Surveillance en temps réel des ressources système (CPU, RAM, Docker)
###############################################################################

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables
HOPPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REFRESH_RATE=2  # Secondes

###############################################################################
# Fonctions
###############################################################################

get_cpu_usage() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//'
    else
        # Linux
        top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}'
    fi
}

get_memory_usage() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f Mi\n", "$1:", $2 * $size / 1048576);' | grep "active\|wired" | awk '{sum+=$2} END {printf "%.1f", sum}'
    else
        # Linux
        free -m | awk 'NR==2{printf "%.1f", $3}'
    fi
}

get_memory_total() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sysctl -n hw.memsize | awk '{printf "%.1f", $1/1024/1024}'
    else
        # Linux
        free -m | awk 'NR==2{printf "%.1f", $2}'
    fi
}

get_disk_usage() {
    df -h "${HOPPER_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//'
}

get_container_stats() {
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | grep hopper
}

###############################################################################
# Affichage en temps réel
###############################################################################

print_header() {
    clear
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    📊 HOPPER - System Monitor                               ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

get_bar() {
    local percentage=$1
    local width=50
    local filled=$(printf "%.0f" $(echo "$percentage * $width / 100" | bc -l))
    local empty=$((width - filled))
    
    # Couleur selon le pourcentage
    local color="${GREEN}"
    if (( $(echo "$percentage > 70" | bc -l) )); then
        color="${YELLOW}"
    fi
    if (( $(echo "$percentage > 90" | bc -l) )); then
        color="${RED}"
    fi
    
    echo -ne "${color}"
    printf '█%.0s' $(seq 1 $filled)
    echo -ne "${NC}"
    printf '░%.0s' $(seq 1 $empty)
}

monitor_loop() {
    while true; do
        print_header
        
        # Timestamp
        echo -e "${CYAN}🕐 $(date '+%Y-%m-%d %H:%M:%S')${NC}"
        echo ""
        
        # Ressources système
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}📊 RESSOURCES SYSTÈME${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        # CPU
        CPU=$(get_cpu_usage)
        printf "%-15s [" "🔥 CPU"
        get_bar "$CPU"
        printf "] %.1f%%\n" "$CPU"
        
        # RAM
        MEM_USED=$(get_memory_usage)
        MEM_TOTAL=$(get_memory_total)
        MEM_PERCENT=$(echo "scale=1; $MEM_USED * 100 / $MEM_TOTAL" | bc)
        printf "%-15s [" "💾 RAM"
        get_bar "$MEM_PERCENT"
        printf "] %.1f%% (%.1f/%.1f GB)\n" "$MEM_PERCENT" "$(echo "scale=1; $MEM_USED/1024" | bc)" "$(echo "scale=1; $MEM_TOTAL/1024" | bc)"
        
        # Disque
        DISK=$(get_disk_usage)
        printf "%-15s [" "💿 Disque"
        get_bar "$DISK"
        printf "] %s%%\n" "$DISK"
        
        echo ""
        
        # Conteneurs Docker
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}🐳 CONTENEURS DOCKER${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        if docker ps --filter "name=hopper" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | grep -q "hopper"; then
            # Stats détaillées
            docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null | grep -E "NAME|hopper" | head -10
        else
            echo -e "${YELLOW}⚠️  Aucun conteneur HOPPER en cours d'exécution${NC}"
        fi
        
        echo ""
        
        # Services Health Check
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}🏥 HEALTH CHECKS${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        check_service() {
            local name=$1
            local url=$2
            
            if curl -s --max-time 2 "$url" &>/dev/null; then
                echo -e "  ${GREEN}✓${NC} $name"
            else
                echo -e "  ${RED}✗${NC} $name"
            fi
        }
        
        check_service "Neo4j           (7474)" "http://localhost:7474"
        check_service "Orchestrator    (8000)" "http://localhost:8000/health"
        check_service "STT Service     (5001)" "http://localhost:5001/health"
        check_service "LLM Service     (5002)" "http://localhost:5002/health"
        check_service "TTS Service     (5003)" "http://localhost:5003/health"
        check_service "Spotify         (5006)" "http://localhost:5006/health"
        check_service "Antivirus       (5007)" "http://localhost:5007/status"
        
        echo ""
        
        # Logs récents (dernière ligne de chaque service)
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}📝 DERNIERS LOGS (dernière ligne par service)${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        docker-compose logs --tail=1 2>/dev/null | tail -10
        
        echo ""
        echo -e "${CYAN}♻️  Rafraîchissement toutes les ${REFRESH_RATE}s - Ctrl+C pour quitter${NC}"
        
        sleep $REFRESH_RATE
    done
}

###############################################################################
# Mode snapshot (une seule capture)
###############################################################################

snapshot_mode() {
    print_header
    
    echo -e "${CYAN}📸 Capture instantanée - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
    
    # CPU & RAM
    CPU=$(get_cpu_usage)
    MEM_USED=$(get_memory_usage)
    MEM_TOTAL=$(get_memory_total)
    MEM_PERCENT=$(echo "scale=1; $MEM_USED * 100 / $MEM_TOTAL" | bc)
    DISK=$(get_disk_usage)
    
    echo -e "${BLUE}SYSTÈME:${NC}"
    printf "  CPU:    %.1f%%\n" "$CPU"
    printf "  RAM:    %.1f%% (%.1f/%.1f GB)\n" "$MEM_PERCENT" "$(echo "scale=1; $MEM_USED/1024" | bc)" "$(echo "scale=1; $MEM_TOTAL/1024" | bc)"
    printf "  Disque: %s%%\n" "$DISK"
    echo ""
    
    echo -e "${BLUE}CONTENEURS:${NC}"
    docker stats --no-stream --format "  {{.Name}}: CPU {{.CPUPerc}} | RAM {{.MemUsage}}" 2>/dev/null | grep hopper
    echo ""
    
    echo -e "${BLUE}SERVICES:${NC}"
    check_service "  Neo4j        " "http://localhost:7474"
    check_service "  Orchestrator " "http://localhost:8000/health"
    check_service "  STT          " "http://localhost:5001/health"
    check_service "  LLM          " "http://localhost:5002/health"
    check_service "  TTS          " "http://localhost:5003/health"
    check_service "  Antivirus    " "http://localhost:5007/status"
    echo ""
}

check_service() {
    local name=$1
    local url=$2
    
    if curl -s --max-time 2 "$url" &>/dev/null; then
        echo -e "${name}${GREEN}✓${NC}"
    else
        echo -e "${name}${RED}✗${NC}"
    fi
}

###############################################################################
# Mode alertes
###############################################################################

alert_mode() {
    print_header
    
    echo -e "${YELLOW}⚠️  MODE SURVEILLANCE DES ALERTES${NC}"
    echo -e "${CYAN}Vérification toutes les 5s - Alertes si CPU>80% ou RAM>90%${NC}"
    echo ""
    
    while true; do
        CPU=$(get_cpu_usage)
        MEM_USED=$(get_memory_usage)
        MEM_TOTAL=$(get_memory_total)
        MEM_PERCENT=$(echo "scale=1; $MEM_USED * 100 / $MEM_TOTAL" | bc)
        
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        
        # Alertes
        if (( $(echo "$CPU > 80" | bc -l) )); then
            echo -e "${RED}🔥 [${TIMESTAMP}] ALERTE CPU ÉLEVÉ: ${CPU}%${NC}"
        fi
        
        if (( $(echo "$MEM_PERCENT > 90" | bc -l) )); then
            echo -e "${RED}💾 [${TIMESTAMP}] ALERTE RAM CRITIQUE: ${MEM_PERCENT}%${NC}"
        fi
        
        # Vérifier les conteneurs crashés
        CRASHED=$(docker ps -a --filter "name=hopper" --filter "status=exited" --format "{{.Names}}" 2>/dev/null)
        if [ -n "$CRASHED" ]; then
            echo -e "${RED}💥 [${TIMESTAMP}] CONTENEUR(S) CRASHÉ(S): ${CRASHED}${NC}"
        fi
        
        sleep 5
    done
}

###############################################################################
# Menu principal
###############################################################################

show_menu() {
    print_header
    
    echo -e "${BLUE}Modes disponibles:${NC}"
    echo ""
    echo "  1. 📊 Monitor (temps réel)"
    echo "  2. 📸 Snapshot (capture instantanée)"
    echo "  3. ⚠️  Alertes (surveillance continue)"
    echo "  4. 🚪 Quitter"
    echo ""
    read -p "Choisissez un mode (1-4): " -r MODE
    
    case $MODE in
        1) monitor_loop ;;
        2) snapshot_mode ;;
        3) alert_mode ;;
        4) exit 0 ;;
        *) 
            echo "Option invalide"
            sleep 2
            show_menu
            ;;
    esac
}

###############################################################################
# Script principal
###############################################################################

main() {
    # Vérifier les arguments
    if [ $# -eq 0 ]; then
        # Mode interactif
        show_menu
    else
        case $1 in
            --live|-l)
                monitor_loop
                ;;
            --snapshot|-s)
                snapshot_mode
                ;;
            --alert|-a)
                alert_mode
                ;;
            --help|-h)
                echo "Usage: $0 [option]"
                echo ""
                echo "Options:"
                echo "  -l, --live       Mode monitor en temps réel"
                echo "  -s, --snapshot   Capture instantanée"
                echo "  -a, --alert      Mode surveillance des alertes"
                echo "  -h, --help       Afficher cette aide"
                echo ""
                ;;
            *)
                echo "Option inconnue: $1"
                echo "Utilisez --help pour voir les options disponibles"
                exit 1
                ;;
        esac
    fi
}

# Exécution
main "$@"
