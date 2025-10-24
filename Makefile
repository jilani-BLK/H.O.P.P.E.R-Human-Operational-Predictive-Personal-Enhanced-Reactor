.PHONY: help install start stop restart logs health test clean build

help: ## Affiche cette aide
	@echo "╔════════════════════════════════════════════════╗"
	@echo "║         HOPPER - Commandes Disponibles        ║"
	@echo "╚════════════════════════════════════════════════╝"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Installation complète avec script automatique
	@echo "🚀 Lancement de l'installation..."
	@chmod +x install.sh
	@./install.sh

start: ## Démarrer tous les services
	@echo "🚀 Démarrage de HOPPER..."
	@docker compose up -d
	@echo "⏳ Attente du démarrage (30s)..."
	@sleep 30
	@$(MAKE) health

stop: ## Arrêter tous les services
	@echo "🛑 Arrêt de HOPPER..."
	@docker compose down

restart: ## Redémarrer tous les services
	@$(MAKE) stop
	@$(MAKE) start

logs: ## Voir les logs de tous les services
	@docker compose logs -f

logs-orchestrator: ## Logs de l'orchestrateur
	@docker compose logs -f orchestrator

logs-llm: ## Logs du moteur LLM
	@docker compose logs -f llm

logs-system: ## Logs du module système
	@docker compose logs -f system_executor

health: ## Vérifier l'état des services
	@echo "🏥 Vérification de l'état des services..."
	@curl -s http://localhost:5000/health | python3 -m json.tool || echo "❌ Services non accessibles"

cli: ## Lancer le CLI interactif
	@python3 hopper-cli.py -i

test: ## Lancer les tests
	@echo "🧪 Lancement des tests..."
	@pytest tests/ -v

test-integration: ## Tests d'intégration (nécessite services actifs)
	@echo "🧪 Tests d'intégration..."
	@pytest tests/test_integration.py -v

build: ## Rebuild tous les services
	@echo "🔨 Rebuild des services..."
	@docker compose build

build-no-cache: ## Rebuild sans cache
	@echo "🔨 Rebuild sans cache..."
	@docker compose build --no-cache

clean: ## Nettoyage complet
	@echo "🧹 Nettoyage..."
	@docker compose down -v
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Nettoyage terminé"

ps: ## Afficher les conteneurs actifs
	@docker compose ps

stats: ## Statistiques des conteneurs
	@docker stats --no-stream

shell-orchestrator: ## Shell dans l'orchestrateur
	@docker compose exec orchestrator /bin/bash

shell-system: ## Shell dans le module système
	@docker compose exec system_executor /bin/sh

dev: ## Mode développement (rebuild + start + logs)
	@$(MAKE) build
	@$(MAKE) start
	@$(MAKE) logs

format: ## Formater le code Python
	@echo "🎨 Formatage du code..."
	@black src/
	@echo "✅ Code formaté"

lint: ## Vérifier le style du code
	@echo "🔍 Vérification du style..."
	@flake8 src/ --max-line-length=100

count: ## Compter les lignes de code
	@echo "📊 Statistiques du code:"
	@find src -name "*.py" | xargs wc -l | tail -1
	@find src -name "*.c" | xargs wc -l | tail -1

docs: ## Ouvrir la documentation
	@echo "📚 Documentation disponible dans docs/"
	@ls -lh docs/

backup: ## Créer une sauvegarde
	@echo "💾 Création d'une sauvegarde..."
	@tar -czf hopper-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='.git' \
		--exclude='data/models' \
		--exclude='__pycache__' \
		.
	@echo "✅ Sauvegarde créée"

update: ## Mettre à jour les dépendances
	@echo "📦 Mise à jour des dépendances..."
	@pip install --upgrade -r src/orchestrator/requirements.txt

ports: ## Afficher les ports utilisés
	@echo "🔌 Ports HOPPER:"
	@echo "  5000 - Orchestrateur"
	@echo "  5001 - LLM Engine"
	@echo "  5002 - System Executor"
	@echo "  5003 - STT (Speech-to-Text)"
	@echo "  5004 - TTS (Text-to-Speech)"
	@echo "  5005 - Auth"
	@echo "  5006 - Connectors"

version: ## Afficher la version
	@echo "HOPPER v0.1.0-alpha"

# Raccourcis
up: start
down: stop
