#!/bin/bash
# Script d'application rapide du changement de port 5000 → 5050
# Résout le conflit avec AirPlay Receiver (macOS)

set -e

cd "$(dirname "$0")"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  HOPPER - Application Changement de Port                      ║"
echo "║  5000 (AirPlay) → 5050 (HOPPER)                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Vérifier qu'on est dans le bon dossier
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Erreur: docker-compose.yml non trouvé${NC}"
    echo "   Assurez-vous d'être dans le dossier HOPPER"
    exit 1
fi

echo -e "${BLUE}[1/6]${NC} Vérification du port 5000..."
if lsof -ti:5000 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 5000 occupé (probablement AirPlay)${NC}"
    process=$(ps -p $(lsof -ti:5000) -o comm= 2>/dev/null | head -1)
    echo "    Processus: $process"
else
    echo -e "${GREEN}✓${NC} Port 5000 libre"
fi

echo ""
echo -e "${BLUE}[2/6]${NC} Vérification du port 5050..."
if lsof -ti:5050 > /dev/null 2>&1; then
    echo -e "${RED}❌ Port 5050 déjà utilisé!${NC}"
    process=$(ps -p $(lsof -ti:5050) -o comm= 2>/dev/null)
    echo "    Processus: $process"
    echo "    Libérez le port 5050 ou choisissez un autre port"
    exit 1
else
    echo -e "${GREEN}✓${NC} Port 5050 disponible"
fi

echo ""
echo -e "${BLUE}[3/6]${NC} Création du fichier .env..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Fichier .env existe déjà${NC}"
    if grep -q "ORCHESTRATOR_PORT" .env; then
        current_port=$(grep "ORCHESTRATOR_PORT" .env | cut -d'=' -f2)
        echo "    Port actuel: $current_port"
    fi
    echo -n "    Écraser? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cp .env .env.backup
        echo -e "${GREEN}✓${NC} Backup créé: .env.backup"
    else
        echo "    Utilisation du .env existant"
        echo "ORCHESTRATOR_PORT=5050" >> .env
        echo -e "${GREEN}✓${NC} ORCHESTRATOR_PORT ajouté"
    fi
else
    cat > .env << 'EOF'
# Configuration HOPPER - Ports
ORCHESTRATOR_PORT=5050
ORCHESTRATOR_HOST=0.0.0.0

# URLs des services
LLM_SERVICE_URL=http://llm:5001
SYSTEM_EXECUTOR_URL=http://system_executor:5002
STT_SERVICE_URL=http://stt:5003
TTS_SERVICE_URL=http://tts:5004
AUTH_SERVICE_URL=http://auth:5005
CONNECTORS_URL=http://connectors:5006

# Base de données
DB_PATH=/data/hopper.db
VECTOR_DB_PATH=/data/vector_store

# Mode
DEBUG_MODE=false
OFFLINE_MODE=false
EOF
    echo -e "${GREEN}✓${NC} Fichier .env créé"
fi

echo ""
echo -e "${BLUE}[4/6]${NC} Modification de docker-compose.yml..."
if grep -q '"5050:5050"' docker-compose.yml; then
    echo -e "${YELLOW}⚠️  docker-compose.yml déjà configuré pour le port 5050${NC}"
else
    cp docker-compose.yml docker-compose.yml.backup
    sed -i.tmp 's/"5000:5000"/"5050:5050"/' docker-compose.yml
    rm -f docker-compose.yml.tmp
    echo -e "${GREEN}✓${NC} docker-compose.yml modifié (backup: docker-compose.yml.backup)"
fi

echo ""
echo -e "${BLUE}[5/6]${NC} Modification des tests d'intégration..."
if [ -f "tests/test_integration.py" ]; then
    if grep -q "localhost:5050" tests/test_integration.py; then
        echo -e "${YELLOW}⚠️  Tests déjà configurés pour le port 5050${NC}"
    else
        cp tests/test_integration.py tests/test_integration.py.backup
        sed -i.tmp 's|localhost:5000|localhost:5050|g' tests/test_integration.py
        sed -i.tmp 's|BASE_URL = "http://localhost:5000"|BASE_URL = "http://localhost:5050"|' tests/test_integration.py
        rm -f tests/test_integration.py.tmp
        echo -e "${GREEN}✓${NC} test_integration.py modifié (backup: test_integration.py.backup)"
    fi
else
    echo -e "${YELLOW}⚠️  test_integration.py non trouvé (non bloquant)${NC}"
fi

echo ""
echo -e "${BLUE}[6/6]${NC} Vérification de la configuration..."

# Vérifier .env
if grep -q "ORCHESTRATOR_PORT=5050" .env; then
    echo -e "${GREEN}✓${NC} .env: ORCHESTRATOR_PORT=5050"
else
    echo -e "${RED}✗${NC} .env: Port non configuré correctement"
fi

# Vérifier docker-compose.yml
if grep -q '"5050:5050"' docker-compose.yml; then
    echo -e "${GREEN}✓${NC} docker-compose.yml: Port 5050 configuré"
else
    echo -e "${RED}✗${NC} docker-compose.yml: Port non configuré correctement"
fi

# Vérifier tests
if [ -f "tests/test_integration.py" ] && grep -q "localhost:5050" tests/test_integration.py; then
    echo -e "${GREEN}✓${NC} test_integration.py: Port 5050 configuré"
else
    echo -e "${YELLOW}⚠${NC} test_integration.py: Non modifié ou absent"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✨ Changement de port appliqué avec succès! ✨${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "📝 Prochaines étapes:"
echo ""
echo "  1. Démarrer les services Docker:"
echo -e "     ${BLUE}make up${NC}"
echo "     ou"
echo -e "     ${BLUE}docker-compose up -d${NC}"
echo ""
echo "  2. Vérifier que l'orchestrateur répond:"
echo -e "     ${BLUE}curl http://localhost:5050/health${NC}"
echo ""
echo "  3. Lancer les tests d'intégration:"
echo -e "     ${BLUE}pytest tests/test_integration.py -v${NC}"
echo ""
echo "  4. Utiliser le CLI avec le nouveau port:"
echo -e "     ${BLUE}./hopper-cli.py --port 5050${NC}"
echo ""

echo "📚 Documentation:"
echo "   Guide complet: docs/DOCKER_INTEGRATION_FIX.md"
echo ""

echo "💡 Astuce: Pour revenir au port 5000:"
echo "   Restaurer les backups .backup créés"
echo ""
