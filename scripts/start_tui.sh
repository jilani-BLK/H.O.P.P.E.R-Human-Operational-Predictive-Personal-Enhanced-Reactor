#!/bin/bash

# 🧠 HOPPER TUI Launcher
# Démarre l'interface terminal interactive pour HOPPER

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}║          ${GREEN}🧠 HOPPER Terminal Interface${BLUE}               ║${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier si l'orchestrateur est en cours d'exécution
echo -e "${YELLOW}🔍 Vérification de l'orchestrateur...${NC}"
if curl -s http://localhost:5050/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Orchestrateur détecté sur http://localhost:5050${NC}"
else
    echo -e "${YELLOW}⚠️  L'orchestrateur n'est pas en cours d'exécution${NC}"
    echo -e "${YELLOW}   Démarrez-le avec: python src/orchestrator/main.py${NC}"
    echo ""
    read -p "Continuer quand même? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}🚀 Lancement de l'interface TUI...${NC}"
echo ""

# Activer l'environnement virtuel si disponible
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Lancer l'interface TUI
python src/cli/hopper_tui.py "$@"
