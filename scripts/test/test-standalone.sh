#!/bin/bash
# Test rapide HOPPER - Sans Docker
# Lance l'orchestrateur en standalone pour tester la Phase 1

echo "=== HOPPER Phase 1 - Test Standalone ==="
echo ""

cd /Users/jilani/Projet/HOPPER

# Activer l'environnement virtuel
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Environnement Python activé"
else
    echo "❌ .venv non trouvé - Exécutez d'abord: python3 -m venv .venv"
    exit 1
fi

# Installer dépendances orchestrateur
echo "Installation dépendances..."
pip install -q -r src/orchestrator/requirements.txt

echo "✓ Dépendances OK"
echo ""

# Lancer l'orchestrateur
echo "Démarrage orchestrateur sur http://localhost:5000"
echo "Arrêter avec Ctrl+C"
echo ""

cd src/orchestrator
python main.py
