#!/bin/bash
###############################################################################
# Neo4j Restore Script
# Restore d'un backup Neo4j
###############################################################################

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/data/backups/neo4j}"
NEO4J_CONTAINER="${NEO4J_CONTAINER:-hopper-neo4j}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-hopper123}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Usage
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.dump.gz> [--force]"
    echo ""
    echo "Backups disponibles:"
    ls -lh "$BACKUP_DIR"/neo4j_backup_*.dump.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    exit 1
fi

BACKUP_FILE="$1"
FORCE="${2:-}"

# Vérifier que le fichier existe
if [ ! -f "$BACKUP_FILE" ]; then
    # Essayer dans le répertoire de backup
    if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
        BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
    else
        error "Backup introuvable: $BACKUP_FILE"
        exit 1
    fi
fi

log "=========================================="
log "Restore Neo4j"
log "=========================================="
log "Fichier: $(basename "$BACKUP_FILE")"
log "Taille: $(du -h "$BACKUP_FILE" | cut -f1)"

# Confirmation si pas --force
if [ "$FORCE" != "--force" ]; then
    warn "⚠️  ATTENTION: Cette opération va ÉCRASER la base de données actuelle!"
    read -p "Continuer? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "Restore annulé"
        exit 0
    fi
fi

# Vérifier container Neo4j
if ! docker ps | grep -q "$NEO4J_CONTAINER"; then
    error "Container Neo4j non trouvé ou pas running"
    exit 1
fi

# Arrêter Neo4j
log "🛑 Arrêt de Neo4j..."
docker exec "$NEO4J_CONTAINER" neo4j stop || true
sleep 5

# Décompresser si nécessaire
DUMP_FILE="$BACKUP_FILE"
if [[ "$BACKUP_FILE" == *.gz ]]; then
    log "🗜️  Décompression du backup..."
    DUMP_FILE="${BACKUP_FILE%.gz}"
    gunzip -c "$BACKUP_FILE" > "$DUMP_FILE"
fi

# Copier le dump dans le container
log "📥 Copie du backup dans le container..."
docker cp "$DUMP_FILE" "$NEO4J_CONTAINER:/backups/neo4j.dump"

# Restore
log "♻️  Restauration de la base de données..."
if docker exec "$NEO4J_CONTAINER" \
    neo4j-admin database load neo4j \
    --from-path=/backups \
    --overwrite-destination=true; then
    log "✅ Restore réussi"
else
    error "Échec du restore"
    exit 1
fi

# Redémarrer Neo4j
log "🚀 Redémarrage de Neo4j..."
docker exec "$NEO4J_CONTAINER" neo4j start
sleep 10

# Vérifier que Neo4j est up
log "🔍 Vérification de la connexion..."
if docker exec "$NEO4J_CONTAINER" \
    cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "RETURN 'Connection OK' AS status;" > /dev/null 2>&1; then
    log "✅ Neo4j restauré et opérationnel"
else
    error "Neo4j ne répond pas après restore"
    exit 1
fi

# Nettoyage
if [[ "$BACKUP_FILE" == *.gz ]]; then
    rm -f "$DUMP_FILE"
fi

log "=========================================="
log "✅ Restore terminé avec succès"
log "=========================================="

exit 0
