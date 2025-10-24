#!/bin/bash

# Script de démarrage simplifié pour HOPPER

set -e  # Arrêter en cas d'erreur

echo "╔════════════════════════════════════════════════╗"
echo "║         HOPPER - Installation Rapide          ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Vérification des prérequis
echo "🔍 Vérification des prérequis..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    echo "   Installer depuis: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

echo "✅ Prérequis satisfaits"
echo ""

# Création des répertoires
echo "📁 Création des répertoires..."
mkdir -p data/models data/logs data/vector_store data/auth data/connectors
mkdir -p config
echo "✅ Répertoires créés"
echo ""

# Configuration
if [ ! -f .env ]; then
    echo "⚙️  Création du fichier .env..."
    cp .env.example .env
    echo "✅ Fichier .env créé"
else
    echo "ℹ️  Fichier .env déjà existant"
fi
echo ""

# Choix du mode
echo "Choisissez le mode d'installation:"
echo "  1) Rapide (sans modèle LLM - mode simulation)"
echo "  2) Complet (avec téléchargement de modèle)"
echo ""
read -p "Votre choix [1-2]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Lancement en mode simulation..."
        docker-compose up -d
        ;;
    2)
        echo ""
        echo "📥 Mode complet sélectionné"
        echo ""
        echo "Modèles disponibles:"
        echo "  1) Mistral 7B Instruct (~4.4 GB) - Recommandé"
        echo "  2) LLaMA 2 7B Chat (~4.1 GB)"
        echo "  3) LLaMA 2 13B Chat (~7.4 GB) - Nécessite 16GB+ RAM"
        echo ""
        read -p "Choisir un modèle [1-3]: " model_choice
        
        # Installation de huggingface-cli si nécessaire
        if ! command -v huggingface-cli &> /dev/null; then
            echo "📦 Installation de huggingface-cli..."
            pip3 install -q huggingface-hub
        fi
        
        echo ""
        echo "📥 Téléchargement du modèle (cela peut prendre du temps)..."
        
        case $model_choice in
            1)
                huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
                    mistral-7b-instruct-v0.2.Q4_K_M.gguf \
                    --local-dir data/models \
                    --local-dir-use-symlinks False
                echo "LLM_MODEL_PATH=/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf" >> .env
                ;;
            2)
                huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF \
                    llama-2-7b-chat.Q4_K_M.gguf \
                    --local-dir data/models \
                    --local-dir-use-symlinks False
                echo "LLM_MODEL_PATH=/models/llama-2-7b-chat.Q4_K_M.gguf" >> .env
                ;;
            3)
                huggingface-cli download TheBloke/Llama-2-13B-Chat-GGUF \
                    llama-2-13b-chat.Q4_K_M.gguf \
                    --local-dir data/models \
                    --local-dir-use-symlinks False
                echo "LLM_MODEL_PATH=/models/llama-2-13b-chat.Q4_K_M.gguf" >> .env
                ;;
            *)
                echo "❌ Choix invalide"
                exit 1
                ;;
        esac
        
        echo "✅ Modèle téléchargé"
        echo ""
        echo "🚀 Lancement des services..."
        docker-compose up -d
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

echo ""
echo "⏳ Attente du démarrage des services (30 secondes)..."
sleep 30

echo ""
echo "🏥 Vérification de l'état des services..."
health=$(curl -s http://localhost:5000/health || echo '{"status":"error"}')
echo "$health" | python3 -m json.tool

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║            ✅ Installation Terminée!           ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "🎯 Prochaines étapes:"
echo ""
echo "1. Tester le CLI:"
echo "   python3 hopper-cli.py -i"
echo ""
echo "2. Essayer une commande:"
echo "   python3 hopper-cli.py \"Bonjour HOPPER\""
echo ""
echo "3. Voir les logs:"
echo "   docker-compose logs -f"
echo ""
echo "4. Arrêter HOPPER:"
echo "   docker-compose down"
echo ""
echo "📚 Documentation: docs/README.md"
echo ""
