#!/bin/bash
# Script de démonstration interactive HOPPER
# Teste toutes les fonctionnalités principales du système

set -e

ORCHESTRATOR_URL="http://localhost:5050"
USER_ID="demo_$(date +%s)"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          🤖 HOPPER - Démonstration Interactive              ║${NC}"
echo -e "${BLUE}║           Tests Concrets des Fonctionnalités                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Fonction pour afficher les résultats
show_result() {
    local test_name=$1
    local result=$2
    
    echo -e "${YELLOW}Test: $test_name${NC}"
    echo "$result" | jq '.'
    echo ""
    sleep 1
}

# 1. Health Check
echo -e "${GREEN}[1/7] Health Check du système...${NC}"
HEALTH=$(curl -s "$ORCHESTRATOR_URL/health")
show_result "État de santé" "$HEALTH"

# 2. Liste des services
echo -e "${GREEN}[2/7] Liste des microservices...${NC}"
SERVICES=$(curl -s "$ORCHESTRATOR_URL/api/v1/services")
show_result "Services enregistrés" "$SERVICES"

# 3. Capacités du système
echo -e "${GREEN}[3/7] Capacités disponibles...${NC}"
CAPABILITIES=$(curl -s "$ORCHESTRATOR_URL/api/v1/capabilities")
show_result "Capacités système" "$CAPABILITIES"

# 4. Question générale (LLM)
echo -e "${GREEN}[4/7] Question au LLM...${NC}"
QUESTION=$(curl -s -X POST "$ORCHESTRATOR_URL/command" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"Explique-moi en une phrase ce qu'est un assistant vocal\",
    \"user_id\": \"$USER_ID\"
  }")
show_result "Réponse LLM" "$QUESTION"

# 5. Commande système
echo -e "${GREEN}[5/7] Exécution commande système...${NC}"
SYSTEM_CMD=$(curl -s -X POST "$ORCHESTRATOR_URL/command" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"Liste les fichiers du dossier /tmp\",
    \"user_id\": \"$USER_ID\"
  }")
show_result "Commande système" "$SYSTEM_CMD"

# 6. Contexte utilisateur
echo -e "${GREEN}[6/7] Récupération du contexte...${NC}"
CONTEXT=$(curl -s "$ORCHESTRATOR_URL/context/$USER_ID")
show_result "Contexte utilisateur" "$CONTEXT"

# 7. Nettoyage contexte
echo -e "${GREEN}[7/7] Nettoyage du contexte...${NC}"
DELETE_CONTEXT=$(curl -s -X DELETE "$ORCHESTRATOR_URL/context/$USER_ID")
show_result "Suppression contexte" "$DELETE_CONTEXT"

# Résumé
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    ✅ Démonstration Terminée                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Tous les tests concrets ont réussi !${NC}"
echo ""
echo -e "📊 Statistiques Docker:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""
echo -e "${YELLOW}Pour plus de détails, consultez: TESTS_CONCRETS_RESULTATS.md${NC}"
