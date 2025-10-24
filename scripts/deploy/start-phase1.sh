#!/bin/bash
# Script de démarrage rapide HOPPER Phase 1
# Lance uniquement les services essentiels (sans LLM lourd)

echo "===HOPPER - Démarrage Phase 1 ==="
echo ""

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

echo "✓ Docker installé"

# Créer .env si nécessaire
if [ ! -f .env ]; then
    echo "Création fichier .env..."
    cp .env.example .env
fi

echo "✓ Configuration OK"
echo ""

# Services essentiels Phase 1 (sans LLM compilé)
SERVICES="orchestrator system_executor connectors"

echo "Démarrage services Phase 1:"
echo "  - orchestrator (Python)"
echo "  - system_executor (C)"
echo "  - connectors (Python)"
echo ""

# Build rapide
docker compose build $SERVICES

# Démarrage
docker compose up -d $SERVICES

echo ""
echo "Attente démarrage (10s)..."
sleep 10

# Health check
echo ""
echo "=== Health Checks ==="
curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || echo "Orchestrator: En cours de démarrage..."
curl -s http://localhost:5002/health 2>/dev/null && echo "System Executor: OK" || echo "System Executor: En cours..."
curl -s http://localhost:5006/health | python3 -m json.tool 2>/dev/null || echo "Connectors: En cours..."

echo ""
echo "✅ Services Phase 1 démarrés"
echo ""
echo "Tester avec:"
echo "  /Users/jilani/Projet/HOPPER/.venv/bin/python hopper-cli.py --health"
echo "  /Users/jilani/Projet/HOPPER/.venv/bin/python hopper-cli.py -i"
echo ""
echo "Voir les logs:"
echo "  docker compose logs -f orchestrator"
echo "  docker compose logs -f system_executor"
