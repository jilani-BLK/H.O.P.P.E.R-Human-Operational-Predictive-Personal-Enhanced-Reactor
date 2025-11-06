#!/bin/bash

##############################################################################
# HOPPER Interactive CLI - Talk to your AI assistant
##############################################################################

ORCHESTRATOR_URL="http://localhost:5050"
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                    🤖 HOPPER v2.0                            ║
║         Human Operational Predictive Personal                ║
║              Enhanced Reactor with Voice                     ║
╚══════════════════════════════════════════════════════════════╝
EOF

echo ""
echo -e "${BLUE}📡 Vérification des services...${NC}"

# Check orchestrator
if curl -s -f "${ORCHESTRATOR_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Orchestrator actif (port 5050)${NC}"
else
    echo -e "${RED}✗ Orchestrator inactif - Lancez: docker-compose up -d${NC}"
    exit 1
fi

# Check connectors
if curl -s -f "${ORCHESTRATOR_URL}/api/v1/system/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ System Control actif (Phase 5)${NC}"
else
    echo -e "${YELLOW}⚠ System Control inactif (certaines commandes ne marcheront pas)${NC}"
fi

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}Commandes disponibles:${NC}"
echo ""
echo -e "  ${GREEN}Système:${NC}"
echo "    • info système"
echo "    • liste les applications"
echo "    • lis le fichier [chemin]"
echo "    • cherche les fichiers [pattern]"
echo ""
echo -e "  ${BLUE}Conversation:${NC}"
echo "    • Quelle est la météo?"
echo "    • Raconte-moi une blague"
echo "    • Apprends que [préférence]"
echo ""
echo -e "  ${YELLOW}Commandes spéciales:${NC}"
echo "    • stats     → Voir les statistiques"
echo "    • metrics   → Voir les métriques qualité"
echo "    • help      → Afficher l'aide"
echo "    • quit      → Quitter"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to send command
send_command() {
    local cmd="$1"
    local response
    
    # Show loading
    echo -e "${BLUE}⏳ Traitement...${NC}"
    
    # Send request
    response=$(curl -s -X POST "${ORCHESTRATOR_URL}/api/v1/command" \
        -H "Content-Type: application/json" \
        -d "{\"command\":\"${cmd}\"}")
    
    # Check if response is valid JSON
    if ! echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        echo -e "${RED}❌ Erreur: Réponse invalide du serveur${NC}"
        echo "$response"
        return 1
    fi
    
    # Parse response
    local success=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))")
    local type=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('type', 'unknown'))")
    local answer=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('response', ''))")
    local duration=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('duration_ms', 0))")
    
    # Display result
    echo ""
    if [ "$success" = "True" ]; then
        echo -e "${GREEN}✓ Réponse (${duration}ms):${NC}"
        echo -e "${BOLD}${answer}${NC}"
        
        # Show detailed output if available
        local output=$(echo "$response" | python3 -c "import sys,json; o=json.load(sys.stdin).get('output'); print(o if o else '')")
        if [ -n "$output" ] && [ "$output" != "None" ]; then
            echo ""
            echo -e "${BLUE}Détails:${NC}"
            echo "$output" | head -n 10
            local lines=$(echo "$output" | wc -l)
            if [ $lines -gt 10 ]; then
                echo -e "${YELLOW}... (${lines} lignes au total)${NC}"
            fi
        fi
    else
        echo -e "${RED}✗ Erreur:${NC}"
        echo "$answer"
    fi
    echo ""
    
    # Ask for feedback
    read -p "$(echo -e ${YELLOW}'Cette réponse était-elle utile? (y/n/skip): '${NC})" feedback
    if [ "$feedback" = "y" ]; then
        curl -s -X POST "${ORCHESTRATOR_URL}/api/v1/feedback" \
            -H "Content-Type: application/json" \
            -d "{\"user_input\":\"${cmd}\",\"response\":\"${answer}\",\"feedback\":\"positive\"}" > /dev/null
        echo -e "${GREEN}✓ Merci pour le feedback positif!${NC}"
    elif [ "$feedback" = "n" ]; then
        read -p "Commentaire (optionnel): " comment
        curl -s -X POST "${ORCHESTRATOR_URL}/api/v1/feedback" \
            -H "Content-Type: application/json" \
            -d "{\"user_input\":\"${cmd}\",\"response\":\"${answer}\",\"feedback\":\"negative\",\"comment\":\"${comment}\"}" > /dev/null
        echo -e "${YELLOW}✓ Merci pour le feedback, nous améliorerons!${NC}"
    fi
    echo ""
}

# Function to show stats
show_stats() {
    echo -e "${BLUE}📊 Statistiques du jour:${NC}"
    curl -s "${ORCHESTRATOR_URL}/api/v1/stats/conversations" | python3 -m json.tool
    echo ""
}

# Function to show metrics
show_metrics() {
    echo -e "${BLUE}📈 Métriques qualité:${NC}"
    curl -s "${ORCHESTRATOR_URL}/api/v1/metrics" | python3 -m json.tool
    echo ""
}

# Function to show help
show_help() {
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}Aide détaillée HOPPER${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}Commandes système (Phase 5):${NC}"
    echo "  • info système          → Affiche CPU, RAM, disque"
    echo "  • liste les applications → Liste apps installées"
    echo "  • lis le fichier X      → Lit le contenu du fichier X"
    echo "  • liste répertoire X    → Liste contenu du dossier X"
    echo "  • cherche fichiers *.py → Trouve tous les fichiers .py"
    echo ""
    echo -e "${BLUE}Conversations (LLM):${NC}"
    echo "  • Questions générales"
    echo "  • Conversations naturelles"
    echo "  • Apprentissage de préférences"
    echo ""
    echo -e "${YELLOW}Commandes spéciales:${NC}"
    echo "  • stats    → Statistiques d'utilisation"
    echo "  • metrics  → Métriques qualité (satisfaction rate)"
    echo "  • help     → Cette aide"
    echo "  • quit     → Quitter le programme"
    echo ""
    echo -e "${BOLD}Documentation complète:${NC}"
    echo "  • Guide: /tmp/hopper_guide.txt"
    echo "  • API: http://localhost:5050/docs"
    echo "  • Logs: docker logs -f hopper-orchestrator"
    echo ""
}

# Main loop
while true; do
    echo -ne "${BOLD}${GREEN}HOPPER >${NC} "
    read -r user_input
    
    # Trim whitespace
    user_input=$(echo "$user_input" | xargs)
    
    # Skip empty input
    if [ -z "$user_input" ]; then
        continue
    fi
    
    # Handle special commands
    case "$user_input" in
        "quit"|"exit"|"q")
            echo -e "${GREEN}👋 Au revoir!${NC}"
            exit 0
            ;;
        "stats")
            show_stats
            ;;
        "metrics")
            show_metrics
            ;;
        "help"|"aide"|"?")
            show_help
            ;;
        "clear"|"cls")
            clear
            ;;
        *)
            send_command "$user_input"
            ;;
    esac
done
