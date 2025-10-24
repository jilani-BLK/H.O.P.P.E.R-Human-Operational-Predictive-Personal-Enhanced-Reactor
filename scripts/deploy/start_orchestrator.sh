#!/bin/bash
# Script de démarrage de l'orchestrateur HOPPER

cd "$(dirname "$0")"
source .venv/bin/activate

# Charger les variables d'environnement depuis la racine
export $(grep -v '^#' .env | xargs)

cd src/orchestrator
python main.py
