#!/usr/bin/env bash
###############################################################################
# HOPPER - Backup Script
# Sauvegarde complète de Neo4j, configurations, et données critiques
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
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="hopper_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Fonctions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    💾 HOPPER - Backup System                                ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

###############################################################################
# Création du répertoire de backup
###############################################################################

create_backup_dir() {
    log_info "Création du répertoire de backup..."
    mkdir -p "${BACKUP_PATH}"
    log_success "Répertoire créé: ${BACKUP_PATH}"
}

###############################################################################
# Backup Neo4j
###############################################################################

backup_neo4j() {
    log_info "Sauvegarde de la base de données Neo4j..."
    
    # Vérifier si Neo4j tourne
    if docker ps | grep -q neo4j; then
        log_info "Neo4j est en cours d'exécution, export des données..."
        
        # Export de la base de données via cypher-shell
        docker exec hopper-neo4j cypher-shell -u neo4j -p hopper123 \
            "CALL apoc.export.json.all('/var/lib/neo4j/import/backup_${TIMESTAMP}.json', {useTypes:true})" \
            2>/dev/null || log_warning "Export JSON échoué (APOC peut ne pas être installé)"
        
        # Copier le dump
        docker cp hopper-neo4j:/var/lib/neo4j/import/backup_${TIMESTAMP}.json \
            "${BACKUP_PATH}/neo4j_data.json" 2>/dev/null || log_warning "Copie dump échouée"
        
        # Backup du répertoire data complet
        if [ -d "${HOPPER_DIR}/data/neo4j" ]; then
            log_info "Backup complet du répertoire Neo4j..."
            tar -czf "${BACKUP_PATH}/neo4j_full.tar.gz" -C "${HOPPER_DIR}/data" neo4j
            log_success "Neo4j data sauvegardé"
        fi
    else
        log_warning "Neo4j n'est pas en cours d'exécution"
        
        # Backup direct du répertoire
        if [ -d "${HOPPER_DIR}/data/neo4j" ]; then
            log_info "Backup du répertoire Neo4j (conteneur arrêté)..."
            tar -czf "${BACKUP_PATH}/neo4j_full.tar.gz" -C "${HOPPER_DIR}/data" neo4j
            log_success "Neo4j data sauvegardé"
        else
            log_warning "Aucune donnée Neo4j à sauvegarder"
        fi
    fi
}

###############################################################################
# Backup configurations
###############################################################################

backup_configurations() {
    log_info "Sauvegarde des configurations..."
    
    mkdir -p "${BACKUP_PATH}/config"
    
    # Copier docker-compose.yml
    if [ -f "${HOPPER_DIR}/docker-compose.yml" ]; then
        cp "${HOPPER_DIR}/docker-compose.yml" "${BACKUP_PATH}/config/"
        log_success "docker-compose.yml sauvegardé"
    fi
    
    # Copier .env si présent
    if [ -f "${HOPPER_DIR}/.env" ]; then
        cp "${HOPPER_DIR}/.env" "${BACKUP_PATH}/config/"
        log_success ".env sauvegardé"
    fi
    
    # Copier requirements.txt
    if [ -f "${HOPPER_DIR}/requirements.txt" ]; then
        cp "${HOPPER_DIR}/requirements.txt" "${BACKUP_PATH}/config/"
        log_success "requirements.txt sauvegardé"
    fi
    
    # Sauvegarder les fichiers de config dans src/
    if [ -d "${HOPPER_DIR}/src/config" ]; then
        cp -r "${HOPPER_DIR}/src/config" "${BACKUP_PATH}/config/"
        log_success "Configuration sources sauvegardées"
    fi
}

###############################################################################
# Backup logs
###############################################################################

backup_logs() {
    log_info "Sauvegarde des logs..."
    
    if [ -d "${HOPPER_DIR}/logs" ]; then
        mkdir -p "${BACKUP_PATH}/logs"
        
        # Copier les logs récents (derniers 7 jours)
        find "${HOPPER_DIR}/logs" -type f -mtime -7 -exec cp {} "${BACKUP_PATH}/logs/" \;
        
        # Compresser
        tar -czf "${BACKUP_PATH}/logs.tar.gz" -C "${BACKUP_PATH}" logs
        rm -rf "${BACKUP_PATH}/logs"
        
        log_success "Logs sauvegardés (7 derniers jours)"
    else
        log_warning "Aucun log à sauvegarder"
    fi
}

###############################################################################
# Backup quarantine (antivirus)
###############################################################################

backup_quarantine() {
    log_info "Sauvegarde de la quarantaine antivirus..."
    
    if [ -d "/var/hopper/quarantine" ] && [ "$(ls -A /var/hopper/quarantine 2>/dev/null)" ]; then
        sudo tar -czf "${BACKUP_PATH}/quarantine.tar.gz" -C /var/hopper quarantine
        log_success "Quarantaine sauvegardée"
    else
        log_info "Aucun fichier en quarantaine"
    fi
}

###############################################################################
# Backup modèles
###############################################################################

backup_models() {
    log_info "Sauvegarde des modèles..."
    
    if [ -d "${HOPPER_DIR}/models" ] && [ "$(ls -A ${HOPPER_DIR}/models)" ]; then
        log_warning "Modèles volumineux détectés, création d'une liste..."
        ls -lh "${HOPPER_DIR}/models" > "${BACKUP_PATH}/models_list.txt"
        log_info "Liste des modèles sauvegardée (pas les fichiers)"
        log_info "Les modèles peuvent être re-téléchargés automatiquement"
    else
        log_info "Aucun modèle à sauvegarder"
    fi
}

###############################################################################
# Créer le manifest
###############################################################################

create_manifest() {
    log_info "Création du manifest..."
    
    cat > "${BACKUP_PATH}/MANIFEST.txt" << EOF
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    HOPPER - Backup Manifest                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Date de création: $(date)
Nom du backup: ${BACKUP_NAME}
Chemin: ${BACKUP_PATH}

CONTENU DU BACKUP:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Données:
   - neo4j_full.tar.gz       : Base de données Neo4j complète
   - neo4j_data.json         : Export JSON de Neo4j (si disponible)

⚙️  Configurations:
   - config/docker-compose.yml
   - config/.env
   - config/requirements.txt
   - config/src/config/

📋 Logs:
   - logs.tar.gz             : Logs des 7 derniers jours

🛡️  Quarantaine:
   - quarantine.tar.gz       : Fichiers en quarantaine antivirus

🤖 Modèles:
   - models_list.txt         : Liste des modèles (non sauvegardés)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESTAURATION:
Pour restaurer ce backup, utilisez:
   ./scripts/restore.sh ${BACKUP_NAME}

TAILLE DU BACKUP:
EOF
    
    du -sh "${BACKUP_PATH}" >> "${BACKUP_PATH}/MANIFEST.txt"
    
    log_success "Manifest créé"
}

###############################################################################
# Compression finale
###############################################################################

compress_backup() {
    log_info "Compression du backup..."
    
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
    
    # Supprimer le répertoire non compressé
    rm -rf "${BACKUP_NAME}"
    
    FINAL_SIZE=$(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)
    log_success "Backup compressé: ${BACKUP_NAME}.tar.gz (${FINAL_SIZE})"
}

###############################################################################
# Nettoyage des anciens backups
###############################################################################

cleanup_old_backups() {
    log_info "Nettoyage des anciens backups (>30 jours)..."
    
    # Supprimer les backups de plus de 30 jours
    find "${BACKUP_DIR}" -name "hopper_backup_*.tar.gz" -type f -mtime +30 -delete
    
    BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/hopper_backup_*.tar.gz 2>/dev/null | wc -l)
    log_success "${BACKUP_COUNT} backup(s) conservé(s)"
}

###############################################################################
# Affichage résumé
###############################################################################

print_summary() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    ✅ BACKUP TERMINÉ AVEC SUCCÈS                            ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    FINAL_PATH="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    FINAL_SIZE=$(du -sh "${FINAL_PATH}" | cut -f1)
    
    echo -e "${BLUE}📦 Backup créé:${NC}"
    echo "   Fichier: ${BACKUP_NAME}.tar.gz"
    echo "   Taille: ${FINAL_SIZE}"
    echo "   Chemin: ${FINAL_PATH}"
    echo ""
    echo -e "${BLUE}📋 Restauration:${NC}"
    echo "   ${YELLOW}./scripts/restore.sh ${BACKUP_NAME}${NC}"
    echo ""
    echo -e "${BLUE}🗂️  Backups disponibles:${NC}"
    ls -lh "${BACKUP_DIR}"/hopper_backup_*.tar.gz 2>/dev/null | tail -5 || echo "   Aucun"
    echo ""
}

###############################################################################
# Script principal
###############################################################################

main() {
    print_header
    
    log_info "Démarrage du backup de HOPPER..."
    echo ""
    
    create_backup_dir
    backup_neo4j
    backup_configurations
    backup_logs
    backup_quarantine
    backup_models
    create_manifest
    compress_backup
    cleanup_old_backups
    
    print_summary
}

# Exécution
main "$@"
