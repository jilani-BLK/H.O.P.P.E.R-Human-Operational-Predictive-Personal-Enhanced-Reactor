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
	@chmod +x scripts/install/install.sh
	@./scripts/install/install.sh

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
	@curl -s http://localhost:5050/api/v1/health | python3 -m json.tool || echo "❌ Services non accessibles"

cli: ## Lancer le CLI interactif
	@./bin/hopper --interactive

install-cli: ## Installer le CLI hopper dans ~/.local/bin
	@echo "📦 Installation du CLI HOPPER..."
	@mkdir -p ~/.local/bin
	@ln -sf $(PWD)/bin/hopper ~/.local/bin/hopper
	@echo "✅ CLI installé dans ~/.local/bin/hopper"
	@echo "💡 Ajoutez ~/.local/bin à votre PATH si nécessaire:"
	@echo "   export PATH=\"\$$HOME/.local/bin:\$$PATH\""

uninstall-cli: ## Désinstaller le CLI hopper
	@echo "🗑️  Désinstallation du CLI..."
	@rm -f ~/.local/bin/hopper
	@echo "✅ CLI désinstallé"

test: ## Lancer les tests
	@echo "🧪 Lancement des tests..."
	@pytest tests/ -v

test-phase2: ## Validation technique Phase 2
	@echo "🔍 Validation technique Phase 2..."
	@./scripts/validate_phase2_tech.py

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
	@echo "  5050 - Orchestrateur"
	@echo "  5001 - LLM Engine"
	@echo "  5002 - System Executor"
	@echo "  5003 - Whisper STT (Phase 3)"
	@echo "  5004 - Piper TTS (Phase 3)"
	@echo "  5005 - Auth"
	@echo "  5006 - Connectors"
	@echo "  5007 - Voice Auth (Phase 3)"
	@echo "  5008 - Email (Phase 3)"
	@echo "  6333 - Qdrant (Vector DB)"
	@echo "  7474 - Neo4j Browser"
	@echo "  7687 - Neo4j Bolt"

# ============================================
# PHASE 3 - Voice & Email Commands
# ============================================

phase3-build: ## Build Phase 3 services
	@echo "🔨 Building Phase 3 services..."
	@docker compose build whisper tts_piper auth_voice email
	@echo "✅ Phase 3 services built"

phase3-start: ## Start Phase 3 services only
	@echo "🚀 Starting Phase 3 services..."
	@docker compose up -d whisper tts_piper auth_voice email
	@echo "⏳ Waiting for models to load (60s)..."
	@sleep 60
	@$(MAKE) phase3-health

phase3-stop: ## Stop Phase 3 services
	@echo "🛑 Stopping Phase 3 services..."
	@docker compose stop whisper tts_piper auth_voice email

phase3-restart: ## Restart Phase 3 services
	@$(MAKE) phase3-stop
	@$(MAKE) phase3-start

phase3-health: ## Check Phase 3 services health
	@echo "🏥 Checking Phase 3 services..."
	@echo "  Whisper STT:"
	@curl -s http://localhost:5003/health | python3 -m json.tool || echo "    ❌ Not responding"
	@echo "  Piper TTS:"
	@curl -s http://localhost:5004/health | python3 -m json.tool || echo "    ❌ Not responding"
	@echo "  Voice Auth:"
	@curl -s http://localhost:5007/health | python3 -m json.tool || echo "    ❌ Not responding"
	@echo "  Email:"
	@curl -s http://localhost:5008/health | python3 -m json.tool || echo "    ❌ Not responding"

phase3-logs: ## Logs Phase 3 services
	@docker compose logs -f whisper tts_piper auth_voice email

phase3-test-stt: ## Test Whisper transcription
	@echo "🎤 Testing Whisper STT..."
	@echo "  Record 5s audio (speak now)..."
	@python3 -c "import pyaudio, wave; p = pyaudio.PyAudio(); s = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True); frames = [s.read(16000) for _ in range(5)]; s.close(); p.terminate(); w = wave.open('test_stt.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(b''.join(frames)); w.close(); print('✅ Recorded')"
	@curl -X POST http://localhost:5003/transcribe -F "audio=@test_stt.wav" | python3 -m json.tool
	@rm -f test_stt.wav

phase3-test-tts: ## Test Piper synthesis
	@echo "🔊 Testing Piper TTS..."
	@curl -X POST http://localhost:5004/synthesize \
		-H "Content-Type: application/json" \
		-d '{"text": "Bonjour, je suis HOPPER, votre assistant personnel intelligent"}' \
		--output test_tts.wav
	@echo "✅ Generated test_tts.wav"
	@echo "💡 Play with: afplay test_tts.wav (macOS) or aplay test_tts.wav (Linux)"

phase3-test-email: ## Test email reading
	@echo "📧 Testing Email connector..."
	@curl -s http://localhost:5008/emails/unread | python3 -m json.tool

phase3-setup-email: ## Setup email credentials
	@echo "📧 Setting up email credentials..."
	@if [ ! -f .env.email ]; then \
		cp .env.email.template .env.email; \
		echo "✅ Created .env.email from template"; \
		echo "⚠️  Edit .env.email with your credentials"; \
		echo "💡 Gmail: https://myaccount.google.com/apppasswords"; \
	else \
		echo "⚠️  .env.email already exists"; \
	fi

phase3-enroll-voice: ## Enroll voice profile (interactive)
	@echo "🎤 Voice Enrollment - Record 5 samples"
	@echo "  Say: 'Bonjour HOPPER, c'est moi [your name]'"
	@python3 scripts/phase3/enroll_voice.py

phase3-test-voice-auth: ## Test voice authentication
	@echo "🎤 Voice Authentication Test"
	@echo "  Speak for 3 seconds..."
	@python3 scripts/phase3/test_voice_auth.py

phase3-stats: ## Show Phase 3 statistics
	@echo "📊 Phase 3 Statistics..."
	@curl -s http://localhost:5050/api/v1/phase3/stats | python3 -m json.tool || echo "❌ Not responding"

phase3-voice-health: ## Check voice services comprehensive health
	@echo "🎤 Voice Services Health..."
	@curl -s http://localhost:5050/api/v1/voice/health | python3 -m json.tool || echo "❌ Not responding"

phase3-notifications: ## List recent notifications
	@echo "🔔 Recent Notifications..."
	@curl -s "http://localhost:5050/api/v1/notifications?limit=10" | python3 -m json.tool || echo "❌ Not responding"

phase3-start-polling: ## Start notification polling
	@echo "🔔 Starting notification polling..."
	@curl -s -X POST http://localhost:5050/api/v1/notifications/start-polling | python3 -m json.tool

phase3-email-summary: ## Get email summary
	@echo "📧 Email Summary..."
	@curl -s "http://localhost:5050/api/v1/emails/summary?limit=5&only_important=true" | python3 -m json.tool

phase3-workflow-test: ## Test complete Phase 3 workflow
	@echo "🧪 Testing Phase 3 workflow..."
	@./scripts/test_workflow.sh

phase3-monitor: ## Monitor Phase 3 services (interactive)
	@./scripts/monitor_phase3.sh

phase3-install-deps: ## Install Phase 3 system dependencies
	@echo "📦 Installing Phase 3 dependencies..."
	@echo "  Checking brew packages..."
	@command -v brew >/dev/null 2>&1 && brew install portaudio ffmpeg espeak-ng sox || echo "⚠️  Homebrew not found"
	@echo "  Installing Python packages..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed"

phase3-test: ## Run Phase 3 test suite
	@echo "🧪 Running Phase 3 tests..."
	@pytest tests/phase3/ -v

phase3-clean: ## Clean Phase 3 data
	@echo "🧹 Cleaning Phase 3 data..."
	@docker compose down whisper tts_piper auth_voice email
	@docker volume rm hopper_whisper_models hopper_piper_models hopper_voice_profiles hopper_email_cache 2>/dev/null || true
	@echo "✅ Phase 3 data cleaned"

version: ## Afficher la version
	@echo "HOPPER v0.3.0-alpha (Phase 3 - Voice & Email)"

# Raccourcis
up: start
down: stop
p3: phase3-start
p3-stop: phase3-stop
