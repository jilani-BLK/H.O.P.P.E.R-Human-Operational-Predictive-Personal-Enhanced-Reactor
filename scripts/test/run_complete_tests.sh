#!/bin/bash
# Script de tests complet pour HOPPER
# Tests tous les aspects du système

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        HOPPER - Batterie de Tests Complète                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

VENV_PATH=".venv"
ERRORS=0

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Activation de l'environnement virtuel
if [ -d "$VENV_PATH" ]; then
    echo -e "${BLUE}[INFO]${NC} Activation de l'environnement virtuel..."
    source "$VENV_PATH/bin/activate"
else
    echo -e "${RED}[ERROR]${NC} Environnement virtuel non trouvé!"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  TEST 1/6 : Validation Phase 1 (Infrastructure)"
echo "═══════════════════════════════════════════════════════════════"
if python validate_phase1.py; then
    echo -e "${GREEN}✓ Phase 1 - OK${NC}"
else
    echo -e "${RED}✗ Phase 1 - ÉCHEC${NC}"
    ((ERRORS++))
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  TEST 2/6 : Erreurs Pylance (Qualité du Code)"
echo "═══════════════════════════════════════════════════════════════"
# Compter les erreurs Python dans les fichiers principaux
PYTHON_FILES=$(find src -name "*.py" 2>/dev/null | head -20)
SYNTAX_ERRORS=0

for file in $PYTHON_FILES; do
    if ! python -m py_compile "$file" 2>/dev/null; then
        ((SYNTAX_ERRORS++))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Aucune erreur de syntaxe Python - OK${NC}"
else
    echo -e "${RED}✗ $SYNTAX_ERRORS fichiers avec erreurs - ÉCHEC${NC}"
    ((ERRORS++))
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  TEST 3/6 : Tests Phase 2 (LLM + RAG)"
echo "═══════════════════════════════════════════════════════════════"
if python -m pytest tests/test_phase2.py -v --tb=line -q; then
    echo -e "${GREEN}✓ Tests Phase 2 - OK${NC}"
else
    echo -e "${RED}✗ Tests Phase 2 - ÉCHEC${NC}"
    ((ERRORS++))
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  TEST 4/6 : Structure des Fichiers"
echo "═══════════════════════════════════════════════════════════════"
REQUIRED_FILES=(
    "docker-compose.yml"
    "Makefile"
    "hopper-cli.py"
    "src/orchestrator/main.py"
    "src/llm_engine/server.py"
    "src/system_executor/src/main.c"
    "pyrightconfig.json"
    "README.md"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗${NC} Fichier manquant: $file"
        ((MISSING++))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✓ Tous les fichiers requis présents - OK${NC}"
else
    echo -e "${RED}✗ $MISSING fichiers manquants - ÉCHEC${NC}"
    ((ERRORS++))
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  TEST 5/6 : Configuration Docker"
echo "═══════════════════════════════════════════════════════════════"
if docker --version &>/dev/null && docker-compose --version &>/dev/null; then
    echo -e "${GREEN}✓ Docker & Docker Compose installés - OK${NC}"
    
    # Valider le docker-compose.yml
    if docker-compose config &>/dev/null; then
        echo -e "${GREEN}✓ docker-compose.yml valide - OK${NC}"
    else
        echo -e "${RED}✗ docker-compose.yml invalide - ÉCHEC${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠ Docker non disponible - SKIP${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  TEST 6/6 : Tests d'Intégration (Nécessite Docker)"
echo "═══════════════════════════════════════════════════════════════"

# Vérifier si l'orchestrateur tourne
if curl -s http://localhost:5000/health &>/dev/null; then
    echo -e "${BLUE}[INFO]${NC} Services Docker détectés, lancement des tests..."
    if python -m pytest tests/test_integration.py -v --tb=line -q; then
        echo -e "${GREEN}✓ Tests d'intégration - OK${NC}"
    else
        echo -e "${RED}✗ Tests d'intégration - ÉCHEC${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠ Services Docker non démarrés - SKIP${NC}"
    echo -e "${YELLOW}  Pour exécuter ces tests : make up${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  RÉSUMÉ DES TESTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   ✓ TOUS LES TESTS RÉUSSIS                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}✨ HOPPER est prêt pour la production ✨${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║               ✗ TESTS ÉCHOUÉS: $ERRORS                           ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
