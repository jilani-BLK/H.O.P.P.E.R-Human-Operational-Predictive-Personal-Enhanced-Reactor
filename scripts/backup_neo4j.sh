#!/bin/bash
###############################################################################
# Neo4j Backup Script
# Backup automatisé de la base de données Neo4j avec rotation
###############################################################################

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/data/backups/neo4j}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
NEO4J_CONTAINER="${NEO4J_CONTAINER:-hopper-neo4j}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-hopper123}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="neo4j_backup_${TIMESTAMP}.dump"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Créer répertoire backup si nécessaire
mkdir -p "$BACKUP_DIR"

log "=========================================="
log "Démarrage backup Neo4j"
log "=========================================="

# Vérifier que le container Neo4j existe et est running
if ! docker ps | grep -q "$NEO4J_CONTAINER"; then
    error "Container Neo4j '$NEO4J_CONTAINER' non trouvé ou pas running"
    exit 1
fi

log "✅ Container Neo4j trouvé: $NEO4J_CONTAINER"

# Effectuer le backup avec neo4j-admin dump
log "📦 Création du backup..."
if docker exec "$NEO4J_CONTAINER" \
    neo4j-admin database dump neo4j \
    --to-path=/backups \
    --overwrite-destination=true \
    2>&1 | tee -a "$LOG_FILE"; then
    
    log "✅ Dump Neo4j créé avec succès"
else
    error "Échec du dump Neo4j"
    exit 1
fi

# Copier le dump depuis le container
log "📤 Copie du backup depuis le container..."
if docker cp "$NEO4J_CONTAINER:/backups/neo4j.dump" "${BACKUP_DIR}/${BACKUP_FILE}"; then
    log "✅ Backup copié: ${BACKUP_FILE}"
else
    error "Échec de la copie du backup"
    exit 1
fi

# Compresser le backup
log "🗜️  Compression du backup..."
if gzip "${BACKUP_DIR}/${BACKUP_FILE}"; then
    BACKUP_FILE="${BACKUP_FILE}.gz"
    log "✅ Backup compressé: ${BACKUP_FILE}"
else
    warn "Échec de la compression (non bloquant)"
fi

# Vérifier taille du backup
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
log "📊 Taille du backup: $BACKUP_SIZE"

# Rotation des backups anciens (garder RETENTION_DAYS jours)
log "🗑️  Rotation des backups (rétention: ${RETENTION_DAYS} jours)..."
DELETED_COUNT=0
find "$BACKUP_DIR" -name "neo4j_backup_*.dump.gz" -mtime +${RETENTION_DAYS} -type f | while read -r old_backup; do
    log "  Suppression: $(basename "$old_backup")"
    rm -f "$old_backup"
    DELETED_COUNT=$((DELETED_COUNT + 1))
done

if [ "$DELETED_COUNT" -gt 0 ]; then
    log "✅ $DELETED_COUNT ancien(s) backup(s) supprimé(s)"
else
    log "ℹ️  Aucun backup ancien à supprimer"
fi

# Lister les backups existants
log "📋 Backups disponibles:"
ls -lh "$BACKUP_DIR"/neo4j_backup_*.dump.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' | tee -a "$LOG_FILE"

# Statistiques finales
TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/neo4j_backup_*.dump.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "=========================================="
log "✅ Backup terminé avec succès"
log "📊 Statistiques:"
log "  - Backup: ${BACKUP_FILE} (${BACKUP_SIZE})"
log "  - Total backups: ${TOTAL_BACKUPS}"
log "  - Espace total: ${TOTAL_SIZE}"
log "=========================================="

# Test de restore optionnel (dry-run)
if [ "${TEST_RESTORE:-false}" = "true" ]; then
    log "🧪 Test de restore (dry-run)..."
    if docker exec "$NEO4J_CONTAINER" \
        neo4j-admin database load neo4j \
        --from-path=/backups \
        --overwrite-destination=false \
        --dry-run=true \
        2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Test de restore réussi"
    else
        error "Échec du test de restore"
        exit 1
    fi
fi

# Alerting (optionnel - webhook)
if [ -n "${WEBHOOK_URL}" ]; then
    log "📢 Envoi notification webhook..."
    curl -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"Neo4j backup completed: ${BACKUP_FILE} (${BACKUP_SIZE})\", \"status\": \"success\"}" \
        2>&1 | tee -a "$LOG_FILE" || warn "Échec envoi webhook (non bloquant)"
fi

log "🎉 Script terminé"
exit 0
