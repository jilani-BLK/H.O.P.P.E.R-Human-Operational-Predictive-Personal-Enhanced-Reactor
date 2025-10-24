#!/bin/bash

# HOPPER Neural Interface - Quick Start Script
# Démarre le serveur neural interface et teste le système

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🧠 HOPPER NEURAL INTERFACE - QUICK START            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier Python
echo -e "${BLUE}[1/5]${NC} Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé. Installez Python 3.8+"
    exit 1
fi
echo -e "${GREEN}✅ Python $(python3 --version)${NC}"

# Vérifier venv
echo ""
echo -e "${BLUE}[2/5]${NC} Vérification de l'environnement virtuel..."
if [ ! -d "../../venv" ]; then
    echo "⚠️  venv non trouvé. Créez-le avec: python3 -m venv ../../venv"
    exit 1
fi
echo -e "${GREEN}✅ venv trouvé${NC}"

# Activer venv
source ../../venv/bin/activate

# Installer dépendances
echo ""
echo -e "${BLUE}[3/5]${NC} Installation des dépendances..."
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dépendances installées${NC}"

# Vérifier l'échantillon vocal
echo ""
echo -e "${BLUE}[4/5]${NC} Vérification de l'échantillon vocal..."
if [ ! -f "../../Hopper_voix.wav.mp3" ]; then
    echo -e "${YELLOW}⚠️  Hopper_voix.wav.mp3 non trouvé${NC}"
    echo "   Placez votre échantillon vocal (22 sec) à la racine du projet"
    echo "   Le serveur démarrera quand même, mais le clonage vocal ne fonctionnera pas"
else
    FILESIZE=$(stat -f%z "../../Hopper_voix.wav.mp3" 2>/dev/null || stat -c%s "../../Hopper_voix.wav.mp3")
    echo -e "${GREEN}✅ Échantillon vocal trouvé ($(($FILESIZE / 1024)) KB)${NC}"
fi

# Démarrer le serveur
echo ""
echo -e "${BLUE}[5/5]${NC} Démarrage du serveur neural interface..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🚀 Serveur neural interface démarré!${NC}"
echo ""
echo -e "📡 WebSocket: ${BLUE}ws://localhost:5050/ws/neural${NC}"
echo -e "🌐 Interface:  ${BLUE}http://localhost:5050/${NC}"
echo -e "📊 Health:     ${BLUE}http://localhost:5050/health${NC}"
echo -e "🎭 Mode démo:  ${BLUE}http://localhost:5050/?demo=true${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Conseils:"
echo "   • Ouvrez http://localhost:5050/ dans votre navigateur"
echo "   • Démarrez l'orchestrator dans un autre terminal"
echo "   • Les neurones s'animeront en temps réel!"
echo ""
echo "🛑 Pour arrêter: Ctrl+C"
echo ""

# Lancer le serveur
python3 neural_server.py
