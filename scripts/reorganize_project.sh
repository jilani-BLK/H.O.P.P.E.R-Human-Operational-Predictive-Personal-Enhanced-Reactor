#!/bin/bash
# Script de réorganisation automatique du projet HOPPER
# Date: 24 octobre 2025

set -e  # Arrêter si erreur

echo "=========================================="
echo "🔧 Réorganisation Architecture HOPPER"
echo "=========================================="
echo ""

# Couleurs
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Fonction de confirmation
confirm() {
    read -p "$1 [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Sauvegarder état actuel
echo -e "${YELLOW}📦 Création backup...${NC}"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Backup créé: $BACKUP_DIR"
echo ""

# PHASE 1: CRITIQUE - Exclure data/models/ de Git
echo -e "${RED}🔴 PHASE 1: Exclure data/models/ (4.1 GB) de Git${NC}"
echo ""

if confirm "Voulez-vous exclure data/models/ de Git ?"; then
    echo "1. Ajout à .gitignore..."
    
    # Vérifier si déjà présent
    if ! grep -q "data/models/\*" .gitignore 2>/dev/null; then
        cat >> .gitignore << 'EOF'

# Large model files (excluded from Git)
data/models/*
!data/models/.gitkeep
!data/models/README.md
EOF
        echo -e "${GREEN}✅ Ajouté à .gitignore${NC}"
    else
        echo -e "${GREEN}✅ Déjà présent dans .gitignore${NC}"
    fi
    
    echo "2. Ajout à .dockerignore..."
    if ! grep -q "data/models/\*" .dockerignore 2>/dev/null; then
        cat >> .dockerignore << 'EOF'

# Model files (use volumes instead)
data/models/*
!data/models/.gitkeep
!data/models/README.md
EOF
        echo -e "${GREEN}✅ Ajouté à .dockerignore${NC}"
    else
        echo -e "${GREEN}✅ Déjà présent dans .dockerignore${NC}"
    fi
    
    echo "3. Création data/models/.gitkeep..."
    touch data/models/.gitkeep
    
    echo "4. Création data/models/README.md..."
    cat > data/models/README.md << 'EOF'
# 🤖 Modèles LLM HOPPER

Les modèles LLM ne sont **pas versionnés dans Git** en raison de leur taille (4+ GB).

## 📥 Téléchargement

### Mistral 7B (Recommandé - 4.1 GB)

```bash
# Télécharger depuis Hugging Face
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf \
  -O data/models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
```

### LLaMA 2 7B (Alternative - 3.8 GB)

```bash
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf \
  -O data/models/llama-2-7b-chat.Q4_K_M.gguf
```

## 🐳 Docker

Les modèles sont montés via volumes dans `docker-compose.yml`:

```yaml
volumes:
  - ./data/models:/app/data/models:ro
```

## 📋 Modèles Supportés

- ✅ Mistral 7B Instruct (Recommandé)
- ✅ LLaMA 2 7B Chat
- ✅ Tout modèle GGUF compatible llama.cpp
EOF
    
    echo "5. Suppression du cache Git (conserve les fichiers locaux)..."
    if confirm "Supprimer data/models/ du cache Git ? (fichiers locaux conservés)"; then
        git rm -r --cached data/models/ 2>/dev/null || true
        git add .gitignore .dockerignore data/models/.gitkeep data/models/README.md
        echo -e "${GREEN}✅ Supprimé du cache Git${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  N'oubliez pas de commit:${NC}"
        echo "   git commit -m '🔧 Exclude data/models/ from Git (4.1 GB)'"
    fi
    
    echo ""
fi

# PHASE 2: Réorganisation fichiers racine
echo -e "${YELLOW}🟡 PHASE 2: Réorganisation fichiers racine${NC}"
echo ""

if confirm "Voulez-vous réorganiser les fichiers à la racine ?"; then
    
    # Créer structure scripts/
    echo "1. Création structure scripts/..."
    mkdir -p scripts/{install,test,deploy,monitoring,backup}
    
    # Déplacer scripts shell
    echo "2. Déplacement scripts shell..."
    
    # Scripts installation
    [ -f "install.sh" ] && mv install.sh scripts/install/
    [ -f "corrections_145.sh" ] && mv corrections_145.sh scripts/install/
    [ -f "setup_rag_advanced.sh" ] && mv setup_rag_advanced.sh scripts/install/
    [ -f "setup_rag_minimal.sh" ] && mv setup_rag_minimal.sh scripts/install/
    
    # Scripts déploiement
    [ -f "start-phase1.sh" ] && mv start-phase1.sh scripts/deploy/
    [ -f "start_orchestrator.sh" ] && mv start_orchestrator.sh scripts/deploy/
    [ -f "apply_port_change.sh" ] && mv apply_port_change.sh scripts/deploy/
    
    # Scripts tests
    [ -f "test-standalone.sh" ] && mv test-standalone.sh scripts/test/
    [ -f "test_interactive_stream.sh" ] && mv test_interactive_stream.sh scripts/test/
    [ -f "test_summary.sh" ] && mv test_summary.sh scripts/test/
    [ -f "demo_interactive.sh" ] && mv demo_interactive.sh scripts/test/
    [ -f "run_complete_tests.sh" ] && mv run_complete_tests.sh scripts/test/
    
    # Scripts monitoring
    [ -f "check_errors.sh" ] && mv check_errors.sh scripts/monitoring/
    [ -f "diagnose_port.sh" ] && mv diagnose_port.sh scripts/monitoring/
    
    # Fichiers Python utilitaires
    [ -f "validate_phase1.py" ] && mv validate_phase1.py scripts/test/
    [ -f "validate_phase3.py" ] && mv validate_phase3.py scripts/test/
    [ -f "test_system_integration.py" ] && mv test_system_integration.py scripts/test/
    [ -f "test_antivirus.py" ] && mv test_antivirus.py scripts/test/
    [ -f "test_streaming.py" ] && mv test_streaming.py scripts/test/
    [ -f "test_patterns.py" ] && mv test_patterns.py scripts/test/
    [ -f "install_dependencies.py" ] && mv install_dependencies.py scripts/install/
    
    echo -e "${GREEN}✅ Scripts réorganisés${NC}"
    
    # Créer structure docs/reports/
    echo "3. Consolidation documentation..."
    mkdir -p docs/reports docs/troubleshooting
    
    # Déplacer rapports
    [ -f "ADAPTIVE_LEARNING_SUMMARY.md" ] && mv ADAPTIVE_LEARNING_SUMMARY.md docs/reports/
    [ -f "CORRECTIONS_APPLIQUEES.md" ] && mv CORRECTIONS_APPLIQUEES.md docs/reports/
    [ -f "RESOLUTION_143_ERREURS.md" ] && mv RESOLUTION_143_ERREURS.md docs/reports/
    [ -f "INSTRUCTIONS_145.md" ] && mv INSTRUCTIONS_145.md docs/reports/
    [ -f "RAPPORT_CORRECTIONS_145.txt" ] && mv RAPPORT_CORRECTIONS_145.txt docs/reports/
    [ -f "RAPPORT_FINAL_143_ERREURS.txt" ] && mv RAPPORT_FINAL_143_ERREURS.txt docs/reports/
    [ -f "ANALYSIS_SUMMARY.txt" ] && mv ANALYSIS_SUMMARY.txt docs/reports/
    
    # Déplacer guides troubleshooting
    [ -f "PYTHON_ERRORS_GUIDE.md" ] && mv PYTHON_ERRORS_GUIDE.md docs/troubleshooting/
    [ -f "TROUBLESHOOTING.md" ] && mv TROUBLESHOOTING.md docs/troubleshooting/
    
    echo -e "${GREEN}✅ Documentation consolidée${NC}"
    echo ""
fi

# PHASE 3: Nettoyage logs
echo -e "${GREEN}🟢 PHASE 3: Nettoyage logs${NC}"
echo ""

if confirm "Voulez-vous nettoyer les anciens logs ?"; then
    echo "Nettoyage data/logs/..."
    find data/logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true
    echo -e "${GREEN}✅ Logs >30 jours supprimés${NC}"
    echo ""
fi

# Résumé
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Réorganisation terminée !${NC}"
echo "=========================================="
echo ""
echo "📊 Prochaines étapes:"
echo ""
echo "1. Vérifier les changements:"
echo "   git status"
echo ""
echo "2. Commit les changements:"
echo "   git add ."
echo "   git commit -m '🗂️ Reorganize project structure'"
echo ""
echo "3. Télécharger les modèles LLM:"
echo "   cat data/models/README.md"
echo ""
echo "4. Tester que tout fonctionne:"
echo "   python hopper-cli.py -i"
echo ""
echo -e "${YELLOW}⚠️  N'oubliez pas de mettre à jour les chemins dans:${NC}"
echo "   - README.md"
echo "   - Makefile"
echo "   - Documentation"
echo ""
