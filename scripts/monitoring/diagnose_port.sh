#!/bin/bash
# Script de test rapide des solutions de port

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  HOPPER - Diagnostic Port 5000                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[Diagnostic 1]${NC} Port 5000"
echo "─────────────────────────────────────────────────────────────────"
if lsof -ti:5000 > /dev/null 2>&1; then
    pid=$(lsof -ti:5000 | head -1)
    process=$(ps -p $pid -o comm= 2>/dev/null)
    echo -e "${RED}❌ Port 5000 OCCUPÉ${NC}"
    echo "   PID: $pid"
    echo "   Processus: $process"
    
    if [[ "$process" == *"ControlCenter"* ]] || [[ "$process" == *"AirPlay"* ]]; then
        echo -e "${YELLOW}   → C'est AirPlay Receiver (macOS)${NC}"
        echo ""
        echo "   Solutions:"
        echo "   1. Désactiver AirPlay:"
        echo "      Préférences Système → Partage → Décocher 'Récepteur AirPlay'"
        echo ""
        echo "   2. Changer le port HOPPER à 5050 (RECOMMANDÉ):"
        echo "      ./apply_port_change.sh"
    fi
else
    echo -e "${GREEN}✓ Port 5000 LIBRE${NC}"
fi

echo ""
echo -e "${BLUE}[Diagnostic 2]${NC} Port 5050 (alternative)"
echo "─────────────────────────────────────────────────────────────────"
if lsof -ti:5050 > /dev/null 2>&1; then
    pid=$(lsof -ti:5050)
    process=$(ps -p $pid -o comm= 2>/dev/null)
    echo -e "${RED}❌ Port 5050 OCCUPÉ${NC}"
    echo "   PID: $pid"
    echo "   Processus: $process"
else
    echo -e "${GREEN}✓ Port 5050 LIBRE${NC}"
    echo -e "${GREEN}   → Parfait pour HOPPER!${NC}"
fi

echo ""
echo -e "${BLUE}[Diagnostic 3]${NC} Configuration actuelle"
echo "─────────────────────────────────────────────────────────────────"

# Vérifier .env
if [ -f ".env" ]; then
    if grep -q "ORCHESTRATOR_PORT" .env; then
        port=$(grep "ORCHESTRATOR_PORT" .env | cut -d'=' -f2)
        echo -e "${GREEN}✓${NC} Fichier .env existe"
        echo "   ORCHESTRATOR_PORT=$port"
    else
        echo -e "${YELLOW}⚠${NC} Fichier .env existe mais sans ORCHESTRATOR_PORT"
    fi
else
    echo -e "${YELLOW}⚠${NC} Fichier .env n'existe pas"
fi

# Vérifier docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    port_line=$(grep -A 2 "orchestrator:" docker-compose.yml | grep "ports:" -A 1 | grep -oE "[0-9]+:[0-9]+" | head -1)
    if [ -n "$port_line" ]; then
        host_port=$(echo $port_line | cut -d':' -f1)
        echo -e "${GREEN}✓${NC} docker-compose.yml configuré"
        echo "   Port hôte: $host_port"
        
        if [ "$host_port" = "5000" ]; then
            echo -e "${YELLOW}   → Attention: conflit potentiel avec AirPlay${NC}"
        fi
    fi
else
    echo -e "${RED}✗${NC} docker-compose.yml non trouvé"
fi

# Vérifier les tests
if [ -f "tests/test_integration.py" ]; then
    if grep -q "BASE_URL" tests/test_integration.py; then
        url=$(grep "BASE_URL" tests/test_integration.py | grep -oE "http://[^\"]+")
        echo -e "${GREEN}✓${NC} Tests d'intégration configurés"
        echo "   URL: $url"
    fi
else
    echo -e "${YELLOW}⚠${NC} test_integration.py non trouvé"
fi

echo ""
echo -e "${BLUE}[Diagnostic 4]${NC} Services Docker"
echo "─────────────────────────────────────────────────────────────────"
if docker ps > /dev/null 2>&1; then
    hopper_containers=$(docker ps -a --filter "name=hopper" --format "{{.Names}}" | wc -l)
    hopper_running=$(docker ps --filter "name=hopper" --format "{{.Names}}" | wc -l)
    
    echo -e "${GREEN}✓${NC} Docker accessible"
    echo "   Conteneurs HOPPER: $hopper_containers (dont $hopper_running en cours)"
    
    if [ $hopper_running -gt 0 ]; then
        echo ""
        echo "   Conteneurs actifs:"
        docker ps --filter "name=hopper" --format "   - {{.Names}} ({{.Status}})"
    fi
else
    echo -e "${YELLOW}⚠${NC} Docker non accessible ou non démarré"
fi

echo ""
echo -e "${BLUE}[Diagnostic 5]${NC} Autres ports disponibles"
echo "─────────────────────────────────────────────────────────────────"
for port in 5050 5100 8000 8080 9000; do
    if ! lsof -ti:$port > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Port $port disponible"
    else
        echo -e "${RED}✗${NC} Port $port occupé"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${BLUE}📋 RECOMMANDATIONS${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Déterminer la recommandation
if lsof -ti:5000 > /dev/null 2>&1 && ! lsof -ti:5050 > /dev/null 2>&1; then
    echo -e "${GREEN}✨ Solution Recommandée: Changer le port à 5050${NC}"
    echo ""
    echo "   Exécutez:"
    echo -e "   ${BLUE}./apply_port_change.sh${NC}"
    echo ""
    echo "   Puis:"
    echo -e "   ${BLUE}docker-compose up -d${NC}"
    echo -e "   ${BLUE}curl http://localhost:5050/health${NC}"
    echo -e "   ${BLUE}pytest tests/test_integration.py -v${NC}"
elif ! lsof -ti:5000 > /dev/null 2>&1; then
    echo -e "${GREEN}✨ Port 5000 est libre!${NC}"
    echo ""
    echo "   Vous pouvez utiliser le port 5000 directement:"
    echo -e "   ${BLUE}docker-compose up -d${NC}"
    echo -e "   ${BLUE}pytest tests/test_integration.py -v${NC}"
else
    echo -e "${YELLOW}⚠️  Ports 5000 et 5050 occupés${NC}"
    echo ""
    echo "   Essayez un autre port (8000, 8080, 9000)"
    echo "   Ou libérez un des ports actuels"
fi

echo ""
echo "📚 Documentation complète:"
echo "   docs/DOCKER_INTEGRATION_FIX.md"
echo ""
