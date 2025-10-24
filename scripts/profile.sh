#!/usr/bin/env bash
###############################################################################
# HOPPER - Profiling Script
# Analyse des performances de tous les services (CPU, Mémoire, Latence)
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
PROFILE_DIR="${HOPPER_DIR}/profiling_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROFILE_FILE="${PROFILE_DIR}/profile_${TIMESTAMP}.txt"

# Fonctions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    ⚡ HOPPER - Performance Profiling                         ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

###############################################################################
# Profiling Docker Containers
###############################################################################

profile_docker_resources() {
    log_info "Profiling des ressources Docker..."
    
    {
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🐳 RESSOURCES DOCKER"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Stats des conteneurs
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" | grep -E "NAME|hopper"
        
        echo ""
        echo "Images Docker:"
        docker images | grep -E "REPOSITORY|hopper"
        
    } | tee -a "$PROFILE_FILE"
    
    log_success "Profiling Docker terminé"
}

###############################################################################
# Profiling des endpoints (latence)
###############################################################################

profile_endpoint_latency() {
    log_info "Profiling de la latence des endpoints..."
    
    {
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⚡ LATENCE DES ENDPOINTS (moyenne sur 5 requêtes)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
    } | tee -a "$PROFILE_FILE"
    
    # Fonction pour mesurer la latence
    measure_latency() {
        local name=$1
        local url=$2
        local method=${3:-GET}
        local data=${4:-}
        
        echo -n "  ${name}... " | tee -a "$PROFILE_FILE"
        
        local total=0
        local count=5
        
        for i in $(seq 1 $count); do
            if [ "$method" = "POST" ]; then
                latency=$(curl -s -w "%{time_total}" -o /dev/null -X POST "$url" \
                    -H "Content-Type: application/json" \
                    -d "$data" \
                    --max-time 30 2>/dev/null || echo "999")
            else
                latency=$(curl -s -w "%{time_total}" -o /dev/null "$url" --max-time 5 2>/dev/null || echo "999")
            fi
            
            total=$(echo "$total + $latency" | bc)
            sleep 0.5
        done
        
        avg=$(echo "scale=3; $total / $count" | bc)
        
        if (( $(echo "$avg < 1" | bc -l) )); then
            echo -e "${GREEN}${avg}s ✓${NC}" | tee -a "$PROFILE_FILE"
        elif (( $(echo "$avg < 3" | bc -l) )); then
            echo -e "${YELLOW}${avg}s ⚠${NC}" | tee -a "$PROFILE_FILE"
        else
            echo -e "${RED}${avg}s ✗${NC}" | tee -a "$PROFILE_FILE"
        fi
    }
    
    # Mesurer tous les endpoints
    measure_latency "Orchestrator /health    " "http://localhost:8000/health"
    measure_latency "STT /health             " "http://localhost:5001/health"
    measure_latency "LLM /health             " "http://localhost:5002/health"
    measure_latency "TTS /health             " "http://localhost:5003/health"
    measure_latency "Spotify /health         " "http://localhost:5006/health"
    measure_latency "Antivirus /status       " "http://localhost:5007/status"
    
    echo "" | tee -a "$PROFILE_FILE"
    
    # Tests avec charge (LLM)
    log_info "Test LLM avec requête réelle..."
    measure_latency "LLM /query (50 tokens)  " "http://localhost:5002/query" "POST" '{"prompt": "Bonjour", "max_tokens": 50}'
    
    log_success "Profiling latence terminé"
}

###############################################################################
# Profiling Python avec py-spy
###############################################################################

profile_python_services() {
    log_info "Profiling Python avec py-spy..."
    
    if ! command -v py-spy &> /dev/null; then
        log_warning "py-spy n'est pas installé. Installation recommandée:"
        echo "  pip install py-spy"
        return
    fi
    
    {
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🐍 PROFILING PYTHON (py-spy)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Profiling pendant 10 secondes..."
        echo ""
        
    } | tee -a "$PROFILE_FILE"
    
    # Trouver les PIDs des processus Python HOPPER
    ORCHESTRATOR_PID=$(pgrep -f "orchestrator/main.py" || echo "")
    
    if [ -n "$ORCHESTRATOR_PID" ]; then
        log_info "Profiling Orchestrator (PID: ${ORCHESTRATOR_PID})..."
        
        FLAME_FILE="${PROFILE_DIR}/orchestrator_flame_${TIMESTAMP}.svg"
        
        sudo py-spy record --duration 10 --output "$FLAME_FILE" --pid "$ORCHESTRATOR_PID" 2>&1 | tee -a "$PROFILE_FILE"
        
        if [ -f "$FLAME_FILE" ]; then
            log_success "Flamegraph créé: $FLAME_FILE"
            echo "  Flamegraph: $FLAME_FILE" | tee -a "$PROFILE_FILE"
        fi
    else
        log_warning "Orchestrator Python non détecté (non en mode dev?)"
    fi
}

###############################################################################
# Profiling mémoire
###############################################################################

profile_memory() {
    log_info "Analyse de la mémoire..."
    
    {
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "💾 UTILISATION MÉMOIRE"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            echo "Mémoire système:"
            vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f Mi\n", "$1:", $2 * $size / 1048576);'
        else
            # Linux
            echo "Mémoire système:"
            free -h
        fi
        
        echo ""
        echo "Top 10 processus par mémoire:"
        ps aux | sort -nrk 4 | head -10
        
    } | tee -a "$PROFILE_FILE"
    
    log_success "Analyse mémoire terminée"
}

###############################################################################
# Analyse des modèles
###############################################################################

profile_models() {
    log_info "Analyse des modèles..."
    
    {
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🤖 MODÈLES"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        if [ -d "${HOPPER_DIR}/models" ]; then
            echo "Modèles stockés:"
            du -sh "${HOPPER_DIR}/models"/* 2>/dev/null || echo "  Aucun modèle local"
        else
            echo "  Répertoire models non trouvé"
        fi
        
        echo ""
        echo "Cache Hugging Face (~/.cache/huggingface):"
        if [ -d ~/.cache/huggingface ]; then
            du -sh ~/.cache/huggingface 2>/dev/null
        else
            echo "  Aucun cache"
        fi
        
    } | tee -a "$PROFILE_FILE"
    
    log_success "Analyse modèles terminée"
}

###############################################################################
# Recommandations d'optimisation
###############################################################################

generate_recommendations() {
    log_info "Génération des recommandations..."
    
    {
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "💡 RECOMMANDATIONS D'OPTIMISATION"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Analyser la RAM Docker
        DOCKER_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" | grep -oE "[0-9.]+" | head -1)
        
        echo "🔍 Analyse automatique:"
        echo ""
        
        # Recommandations Docker
        echo "1. DOCKER & CONTENEURS"
        echo "   • Utilisation mémoire actuelle: ${DOCKER_MEM}MB"
        
        if (( $(echo "$DOCKER_MEM > 4000" | bc -l) )); then
            echo "   ⚠️  RAM élevée. Considérez:"
            echo "      - Combiner services légers (FileSystem + LocalSystem)"
            echo "      - Réduire les limites mémoire dans docker-compose.yml"
            echo "      - Optimiser les images (Alpine Linux)"
        else
            echo "   ✓ RAM acceptable"
        fi
        
        echo ""
        echo "2. MODÈLES LLM"
        echo "   • Llama-3.2-3B: ~6GB en mémoire"
        echo "   💡 Optimisations:"
        echo "      - Utiliser quantization (4-bit, 8-bit)"
        echo "      - Pré-charger au démarrage pour éviter latence"
        echo "      - Considérer modèles plus petits pour réponses simples"
        
        echo ""
        echo "3. WHISPER (STT)"
        echo "   💡 Optimisations:"
        echo "      - Utiliser modèle 'base' ou 'small' au lieu de 'medium'"
        echo "      - Activer segments overlappants pour meilleure précision"
        echo "      - GPU si disponible (30x plus rapide)"
        
        echo ""
        echo "4. BASES DE DONNÉES"
        echo "   • Neo4j: Graphe de connaissances"
        echo "   💡 Optimisations:"
        echo "      - Indexer propriétés fréquemment requêtées"
        echo "      - Nettoyer anciennes conversations (>30 jours)"
        echo "      - Augmenter cache si >10K nœuds"
        
        echo ""
        echo "5. RÉSEAU & I/O"
        echo "   💡 Optimisations:"
        echo "      - Activer compression HTTP (gzip)"
        echo "      - Cache Redis pour requêtes fréquentes"
        echo "      - Connection pooling pour Neo4j"
        
        echo ""
        echo "📊 Pour profiling détaillé:"
        echo "   - py-spy: pip install py-spy"
        echo "   - memory_profiler: pip install memory-profiler"
        echo "   - cProfile: python -m cProfile -o output.pstats script.py"
        
    } | tee -a "$PROFILE_FILE"
    
    log_success "Recommandations générées"
}

###############################################################################
# Résumé
###############################################################################

print_summary() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    ✅ PROFILING TERMINÉ                                      ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${BLUE}📄 Rapport complet:${NC}"
    echo "   ${PROFILE_FILE}"
    echo ""
    echo -e "${BLUE}📊 Prochaines étapes:${NC}"
    echo "   1. Consulter le rapport: ${YELLOW}cat ${PROFILE_FILE}${NC}"
    echo "   2. Appliquer les optimisations recommandées"
    echo "   3. Re-profiler pour mesurer les améliorations"
    echo ""
    echo -e "${BLUE}🔧 Outils avancés:${NC}"
    echo "   • py-spy: Profiling CPU Python"
    echo "   • memory_profiler: Profiling mémoire"
    echo "   • docker stats: Surveillance en temps réel"
    echo ""
}

###############################################################################
# Script principal
###############################################################################

main() {
    print_header
    
    mkdir -p "$PROFILE_DIR"
    
    {
        echo "╔══════════════════════════════════════════════════════════════════════════════╗"
        echo "║                                                                              ║"
        echo "║                    HOPPER - Performance Profiling Report                     ║"
        echo "║                                                                              ║"
        echo "╚══════════════════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Date: $(date)"
        echo "Hostname: $(hostname)"
        echo "OS: $(uname -s) $(uname -r)"
        
    } > "$PROFILE_FILE"
    
    log_info "Démarrage du profiling..."
    log_info "Résultats: ${PROFILE_FILE}"
    echo ""
    
    profile_docker_resources
    echo ""
    
    profile_endpoint_latency
    echo ""
    
    profile_memory
    echo ""
    
    profile_models
    echo ""
    
    profile_python_services
    echo ""
    
    generate_recommendations
    
    print_summary
}

# Exécution
main "$@"
