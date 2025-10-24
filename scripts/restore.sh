#!/usr/bin/env bash
###############################################################################
# HOPPER - Restore Script
# Restauration complète depuis un backup
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
BACKUP_DIR="${HOPPER_DIR}/backups"

# Fonctions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    🔄 HOPPER - Restore System                               ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

###############################################################################
# Vérification des arguments
###############################################################################

check_arguments() {
    if [ $# -eq 0 ]; then
        log_error "Aucun backup spécifié"
        echo ""
        echo "Usage: $0 <backup_name>"
        echo ""
        echo "Backups disponibles:"
        ls -1 "${BACKUP_DIR}"/hopper_backup_*.tar.gz 2>/dev/null | xargs -n 1 basename | sed 's/.tar.gz//' || echo "  Aucun backup trouvé"
        echo ""
        exit 1
    fi
    
    BACKUP_NAME="$1"
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    if [ ! -f "${BACKUP_FILE}" ]; then
        log_error "Backup non trouvé: ${BACKUP_FILE}"
        echo ""
        echo "Backups disponibles:"
        ls -1 "${BACKUP_DIR}"/hopper_backup_*.tar.gz 2>/dev/null | xargs -n 1 basename | sed 's/.tar.gz//' || echo "  Aucun"
        exit 1
    fi
    
    log_success "Backup trouvé: ${BACKUP_FILE}"
}

###############################################################################
# Confirmation de l'utilisateur
###############################################################################

confirm_restore() {
    echo ""
    log_warning "⚠️  ATTENTION: Cette opération va:"
    echo "   - Arrêter tous les services HOPPER"
    echo "   - Supprimer les données actuelles"
    echo "   - Restaurer depuis le backup: ${BACKUP_NAME}"
    echo ""
    read -p "Êtes-vous sûr de vouloir continuer? (oui/non): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Oo]ui$ ]]; then
        log_info "Restauration annulée"
        exit 0
    fi
    
    log_success "Confirmation reçue, démarrage de la restauration..."
}

###############################################################################
# Arrêt des services
###############################################################################

stop_services() {
    log_info "Arrêt des services Docker..."
    
    cd "${HOPPER_DIR}"
    
    if docker-compose ps | grep -q "Up"; then
        docker-compose down
        log_success "Services arrêtés"
    else
        log_info "Aucun service en cours d'exécution"
    fi
}

###############################################################################
# Extraction du backup
###############################################################################

extract_backup() {
    log_info "Extraction du backup..."
    
    cd "${BACKUP_DIR}"
    tar -xzf "${BACKUP_FILE}"
    
    EXTRACT_DIR="${BACKUP_DIR}/${BACKUP_NAME}"
    
    if [ ! -d "${EXTRACT_DIR}" ]; then
        log_error "Échec de l'extraction"
        exit 1
    fi
    
    log_success "Backup extrait: ${EXTRACT_DIR}"
    
    # Afficher le manifest
    if [ -f "${EXTRACT_DIR}/MANIFEST.txt" ]; then
        echo ""
        cat "${EXTRACT_DIR}/MANIFEST.txt"
        echo ""
    fi
}

###############################################################################
# Restauration Neo4j
###############################################################################

restore_neo4j() {
    log_info "Restauration de Neo4j..."
    
    # Sauvegarder l'ancien répertoire
    if [ -d "${HOPPER_DIR}/data/neo4j" ]; then
        log_warning "Sauvegarde de l'ancienne base Neo4j..."
        mv "${HOPPER_DIR}/data/neo4j" "${HOPPER_DIR}/data/neo4j.old.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Restaurer depuis le backup
    if [ -f "${EXTRACT_DIR}/neo4j_full.tar.gz" ]; then
        log_info "Extraction des données Neo4j..."
        mkdir -p "${HOPPER_DIR}/data"
        tar -xzf "${EXTRACT_DIR}/neo4j_full.tar.gz" -C "${HOPPER_DIR}/data"
        log_success "Neo4j restauré"
    else
        log_warning "Aucune donnée Neo4j dans le backup"
    fi
}

###############################################################################
# Restauration des configurations
###############################################################################

restore_configurations() {
    log_info "Restauration des configurations..."
    
    if [ -d "${EXTRACT_DIR}/config" ]; then
        # docker-compose.yml
        if [ -f "${EXTRACT_DIR}/config/docker-compose.yml" ]; then
            cp "${EXTRACT_DIR}/config/docker-compose.yml" "${HOPPER_DIR}/"
            log_success "docker-compose.yml restauré"
        fi
        
        # .env
        if [ -f "${EXTRACT_DIR}/config/.env" ]; then
            cp "${EXTRACT_DIR}/config/.env" "${HOPPER_DIR}/"
            log_success ".env restauré"
        fi
        
        # requirements.txt
        if [ -f "${EXTRACT_DIR}/config/requirements.txt" ]; then
            cp "${EXTRACT_DIR}/config/requirements.txt" "${HOPPER_DIR}/"
            log_success "requirements.txt restauré"
        fi
        
        # src/config/
        if [ -d "${EXTRACT_DIR}/config/config" ]; then
            mkdir -p "${HOPPER_DIR}/src"
            cp -r "${EXTRACT_DIR}/config/config" "${HOPPER_DIR}/src/"
            log_success "Configuration sources restaurées"
        fi
    else
        log_warning "Aucune configuration dans le backup"
    fi
}

###############################################################################
# Restauration des logs
###############################################################################

restore_logs() {
    log_info "Restauration des logs..."
    
    if [ -f "${EXTRACT_DIR}/logs.tar.gz" ]; then
        mkdir -p "${HOPPER_DIR}/logs"
        tar -xzf "${EXTRACT_DIR}/logs.tar.gz" -C "${HOPPER_DIR}"
        log_success "Logs restaurés"
    else
        log_info "Aucun log dans le backup"
    fi
}

###############################################################################
# Restauration de la quarantaine
###############################################################################

restore_quarantine() {
    log_info "Restauration de la quarantaine..."
    
    if [ -f "${EXTRACT_DIR}/quarantine.tar.gz" ]; then
        sudo mkdir -p /var/hopper
        sudo tar -xzf "${EXTRACT_DIR}/quarantine.tar.gz" -C /var/hopper
        sudo chmod 700 /var/hopper/quarantine
        log_success "Quarantaine restaurée"
    else
        log_info "Aucune quarantaine dans le backup"
    fi
}

###############################################################################
# Nettoyage
###############################################################################

cleanup() {
    log_info "Nettoyage des fichiers temporaires..."
    
    rm -rf "${EXTRACT_DIR}"
    
    log_success "Nettoyage terminé"
}

###############################################################################
# Redémarrage des services
###############################################################################

restart_services() {
    log_info "Redémarrage des services..."
    
    cd "${HOPPER_DIR}"
    docker-compose up -d
    
    # Attendre que les services démarrent
    log_info "Attente du démarrage des services (30s)..."
    sleep 30
    
    # Vérifier l'état
    if docker-compose ps | grep -q "Up"; then
        log_success "Services démarrés"
    else
        log_warning "Certains services n'ont pas démarré correctement"
        docker-compose ps
    fi
}

###############################################################################
# Vérification post-restauration
###############################################################################

post_restore_check() {
    log_info "Vérifications post-restauration..."
    
    # Vérifier Neo4j
    log_info "Vérification Neo4j..."
    sleep 10  # Attendre que Neo4j soit prêt
    
    if docker exec hopper-neo4j cypher-shell -u neo4j -p hopper123 "MATCH (n) RETURN count(n) as total" 2>/dev/null; then
        log_success "Neo4j opérationnel"
    else
        log_warning "Neo4j peut ne pas être complètement démarré"
    fi
    
    log_success "Vérifications terminées"
}

###############################################################################
# Affichage résumé
###############################################################################

print_summary() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    ✅ RESTAURATION TERMINÉE AVEC SUCCÈS                     ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${BLUE}📦 Backup restauré:${NC}"
    echo "   ${BACKUP_NAME}"
    echo ""
    echo -e "${BLUE}✅ Éléments restaurés:${NC}"
    echo "   - Base de données Neo4j"
    echo "   - Configurations Docker"
    echo "   - Logs système"
    echo "   - Quarantaine antivirus"
    echo ""
    echo -e "${BLUE}🚀 Prochaines étapes:${NC}"
    echo "   1. Vérifier les logs: ${YELLOW}docker-compose logs -f${NC}"
    echo "   2. Tester HOPPER: ${YELLOW}python3 src/orchestrator/main.py${NC}"
    echo "   3. Vérifier Neo4j: ${YELLOW}http://localhost:7474${NC}"
    echo ""
    echo -e "${GREEN}🎉 HOPPER a été restauré avec succès !${NC}"
    echo ""
}

###############################################################################
# Script principal
###############################################################################

main() {
    print_header
    
    check_arguments "$@"
    confirm_restore
    
    echo ""
    
    stop_services
    extract_backup
    restore_neo4j
    restore_configurations
    restore_logs
    restore_quarantine
    cleanup
    restart_services
    post_restore_check
    
    print_summary
}

# Exécution
main "$@"
