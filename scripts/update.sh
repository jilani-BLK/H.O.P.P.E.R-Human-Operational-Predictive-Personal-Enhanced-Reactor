#!/usr/bin/env bash
###############################################################################
# HOPPER - Update Script
# Mise à jour automatique de HOPPER (Docker, dépendances, signatures antivirus)
###############################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
HOPPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Fonctions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    🔄 HOPPER - Update System                                ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

###############################################################################
# Backup avant mise à jour
###############################################################################

pre_update_backup() {
    log_info "Création d'un backup de sécurité avant mise à jour..."
    
    if [ -f "${HOPPER_DIR}/scripts/backup.sh" ]; then
        bash "${HOPPER_DIR}/scripts/backup.sh"
        log_success "Backup de sécurité créé"
    else
        log_warning "Script de backup non trouvé, continuons sans backup"
    fi
}

###############################################################################
# Mise à jour du code source (Git)
###############################################################################

update_source_code() {
    log_info "Vérification des mises à jour du code source..."
    
    cd "${HOPPER_DIR}"
    
    if [ -d ".git" ]; then
        # Vérifier si des modifications locales existent
        if [[ -n $(git status -s) ]]; then
            log_warning "Modifications locales détectées"
            git status -s
            echo ""
            read -p "Voulez-vous sauvegarder ces modifications avant la mise à jour? (oui/non): " -r
            echo ""
            
            if [[ $REPLY =~ ^[Oo]ui$ ]]; then
                git stash save "Auto-stash before update $(date)"
                log_success "Modifications sauvegardées (git stash)"
            fi
        fi
        
        # Pull des dernières modifications
        log_info "Téléchargement des dernières modifications..."
        CURRENT_COMMIT=$(git rev-parse HEAD)
        
        git fetch origin
        git pull origin main
        
        NEW_COMMIT=$(git rev-parse HEAD)
        
        if [ "${CURRENT_COMMIT}" != "${NEW_COMMIT}" ]; then
            log_success "Code source mis à jour: ${CURRENT_COMMIT:0:7} -> ${NEW_COMMIT:0:7}"
        else
            log_info "Code source déjà à jour"
        fi
    else
        log_warning "Pas de dépôt Git trouvé, mise à jour du code ignorée"
    fi
}

###############################################################################
# Mise à jour des dépendances Python
###############################################################################

update_python_dependencies() {
    log_info "Mise à jour des dépendances Python..."
    
    cd "${HOPPER_DIR}"
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        
        # Mise à jour pip
        pip install --upgrade pip setuptools wheel
        
        # Mise à jour des packages
        if [ -f "requirements.txt" ]; then
            log_info "Installation des nouvelles dépendances..."
            pip install -r requirements.txt --upgrade
            log_success "Dépendances Python mises à jour"
        else
            log_warning "requirements.txt non trouvé"
        fi
        
        deactivate
    else
        log_warning "Environnement virtuel non trouvé, création..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        deactivate
        log_success "Environnement virtuel créé et dépendances installées"
    fi
}

###############################################################################
# Mise à jour des images Docker
###############################################################################

update_docker_images() {
    log_info "Mise à jour des images Docker..."
    
    cd "${HOPPER_DIR}"
    
    # Arrêter les services
    log_info "Arrêt des services..."
    docker-compose down
    
    # Pull des nouvelles images
    log_info "Téléchargement des nouvelles images (peut prendre du temps)..."
    docker-compose pull
    
    # Rebuild des images custom
    log_info "Reconstruction des images personnalisées..."
    docker-compose build --pull
    
    log_success "Images Docker mises à jour"
}

###############################################################################
# Mise à jour des signatures antivirus
###############################################################################

update_antivirus_signatures() {
    log_info "Mise à jour des signatures antivirus ClamAV..."
    
    OS_TYPE="$(uname -s)"
    
    if command -v freshclam &> /dev/null; then
        if [ "${OS_TYPE}" = "Darwin" ]; then
            # macOS
            freshclam
        else
            # Linux (nécessite sudo)
            sudo freshclam
        fi
        log_success "Signatures antivirus mises à jour"
    else
        log_warning "ClamAV non installé, mise à jour des signatures ignorée"
    fi
}

###############################################################################
# Nettoyage Docker
###############################################################################

cleanup_docker() {
    log_info "Nettoyage Docker..."
    
    # Supprimer les images non utilisées
    log_info "Suppression des images inutilisées..."
    docker image prune -f
    
    # Supprimer les volumes non utilisés
    log_info "Suppression des volumes inutilisés..."
    docker volume prune -f
    
    # Supprimer les conteneurs arrêtés
    docker container prune -f
    
    SPACE_SAVED=$(docker system df 2>/dev/null || echo "N/A")
    log_success "Nettoyage Docker terminé"
}

###############################################################################
# Redémarrage des services
###############################################################################

restart_services() {
    log_info "Redémarrage des services..."
    
    cd "${HOPPER_DIR}"
    docker-compose up -d
    
    # Attendre le démarrage
    log_info "Attente du démarrage des services (30s)..."
    sleep 30
    
    # Vérifier l'état
    log_info "Vérification de l'état des services..."
    docker-compose ps
    
    if docker-compose ps | grep -q "Up"; then
        log_success "Services redémarrés avec succès"
    else
        log_warning "Certains services n'ont pas démarré"
    fi
}

###############################################################################
# Vérifications post-mise à jour
###############################################################################

post_update_checks() {
    log_info "Vérifications post-mise à jour..."
    
    # Vérifier Neo4j
    log_info "Test Neo4j..."
    sleep 10
    if docker exec hopper-neo4j cypher-shell -u neo4j -p hopper123 "RETURN 1" &>/dev/null; then
        log_success "Neo4j opérationnel"
    else
        log_warning "Neo4j peut ne pas être prêt"
    fi
    
    # Vérifier les endpoints
    log_info "Test des endpoints..."
    
    # Orchestrator
    if curl -s http://localhost:8000/health &>/dev/null; then
        log_success "Orchestrator opérationnel (port 8000)"
    else
        log_warning "Orchestrator non accessible"
    fi
    
    # STT
    if curl -s http://localhost:5001/health &>/dev/null; then
        log_success "STT Service opérationnel (port 5001)"
    else
        log_warning "STT Service non accessible"
    fi
    
    # LLM
    if curl -s http://localhost:5002/health &>/dev/null; then
        log_success "LLM Service opérationnel (port 5002)"
    else
        log_warning "LLM Service non accessible"
    fi
    
    # TTS
    if curl -s http://localhost:5003/health &>/dev/null; then
        log_success "TTS Service opérationnel (port 5003)"
    else
        log_warning "TTS Service non accessible"
    fi
    
    # Antivirus
    if curl -s http://localhost:5007/status &>/dev/null; then
        log_success "Antivirus Service opérationnel (port 5007)"
    else
        log_warning "Antivirus Service non accessible"
    fi
    
    log_success "Vérifications terminées"
}

###############################################################################
# Affichage du changelog
###############################################################################

show_changelog() {
    log_info "Récupération du changelog..."
    
    cd "${HOPPER_DIR}"
    
    if [ -d ".git" ]; then
        echo ""
        echo -e "${BLUE}📋 Dernières modifications:${NC}"
        echo ""
        git log --oneline --decorate --color -10
        echo ""
    fi
}

###############################################################################
# Affichage résumé
###############################################################################

print_summary() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    ✅ MISE À JOUR TERMINÉE AVEC SUCCÈS                      ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${BLUE}✅ Éléments mis à jour:${NC}"
    echo "   - Code source (Git)"
    echo "   - Dépendances Python"
    echo "   - Images Docker"
    echo "   - Signatures antivirus ClamAV"
    echo ""
    echo -e "${BLUE}🚀 Prochaines étapes:${NC}"
    echo "   1. Vérifier les logs: ${YELLOW}docker-compose logs -f${NC}"
    echo "   2. Tester HOPPER: ${YELLOW}python3 src/orchestrator/main.py${NC}"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "   - Changelog: ${YELLOW}git log --oneline${NC}"
    echo "   - Status: ${YELLOW}docker-compose ps${NC}"
    echo ""
    echo -e "${GREEN}🎉 HOPPER est à jour !${NC}"
    echo ""
}

###############################################################################
# Script principal
###############################################################################

main() {
    print_header
    
    log_info "Démarrage de la mise à jour de HOPPER..."
    echo ""
    
    # Confirmation
    read -p "Voulez-vous continuer avec la mise à jour? (oui/non): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Oo]ui$ ]]; then
        log_info "Mise à jour annulée"
        exit 0
    fi
    
    pre_update_backup
    echo ""
    
    update_source_code
    echo ""
    
    update_python_dependencies
    echo ""
    
    update_docker_images
    echo ""
    
    update_antivirus_signatures
    echo ""
    
    cleanup_docker
    echo ""
    
    restart_services
    echo ""
    
    post_update_checks
    echo ""
    
    show_changelog
    
    print_summary
}

# Exécution
main "$@"
