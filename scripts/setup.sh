#!/usr/bin/env bash
###############################################################################
# HOPPER - Setup Script
# Installation complète et automatisée de HOPPER sur macOS/Linux
###############################################################################

set -e  # Exit on error

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
HOPPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${HOPPER_DIR}/.venv"
QUARANTINE_DIR="/var/hopper/quarantine"
NEO4J_DATA_DIR="${HOPPER_DIR}/data/neo4j"

###############################################################################
# Fonctions utilitaires
###############################################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    🚀 HOPPER - Installation Setup                           ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 est installé"
        return 0
    else
        log_warning "$1 n'est pas installé"
        return 1
    fi
}

###############################################################################
# Vérifications système
###############################################################################

check_system() {
    log_info "Vérification du système..."
    
    # Détection OS
    OS="$(uname -s)"
    case "${OS}" in
        Darwin*)    OS_TYPE="macOS";;
        Linux*)     OS_TYPE="Linux";;
        *)          OS_TYPE="UNKNOWN";;
    esac
    
    log_info "Système détecté: ${OS_TYPE}"
    
    if [ "${OS_TYPE}" = "UNKNOWN" ]; then
        log_error "Système d'exploitation non supporté: ${OS}"
        exit 1
    fi
    
    # Vérification Python 3.10+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            log_success "Python ${PYTHON_VERSION} détecté"
        else
            log_error "Python 3.10+ requis (trouvé: ${PYTHON_VERSION})"
            exit 1
        fi
    else
        log_error "Python 3 n'est pas installé"
        exit 1
    fi
    
    # Vérification Docker
    if ! check_command docker; then
        log_error "Docker n'est pas installé. Installez Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    # Vérification Docker Compose
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    log_success "Toutes les vérifications système ont réussi"
}

###############################################################################
# Installation des dépendances système
###############################################################################

install_system_dependencies() {
    log_info "Installation des dépendances système..."
    
    if [ "${OS_TYPE}" = "macOS" ]; then
        # Vérifier Homebrew
        if ! check_command brew; then
            log_warning "Homebrew n'est pas installé. Installation..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # Installer ClamAV pour l'antivirus
        if ! check_command clamscan; then
            log_info "Installation de ClamAV..."
            brew install clamav
            
            # Configuration ClamAV
            log_info "Configuration de ClamAV..."
            if [ ! -f /opt/homebrew/etc/clamav/freshclam.conf ]; then
                cp /opt/homebrew/etc/clamav/freshclam.conf.sample /opt/homebrew/etc/clamav/freshclam.conf
                sed -i '' 's/^Example/#Example/' /opt/homebrew/etc/clamav/freshclam.conf
            fi
            
            # Mise à jour des signatures
            log_info "Mise à jour des signatures antivirus (peut prendre plusieurs minutes)..."
            freshclam || log_warning "Échec de la mise à jour des signatures (continuons quand même)"
        else
            log_success "ClamAV est déjà installé"
        fi
        
        # Installer PortAudio pour PyAudio
        if ! brew list portaudio &> /dev/null; then
            log_info "Installation de PortAudio..."
            brew install portaudio
        fi
        
        # Installer FFmpeg pour audio processing
        if ! check_command ffmpeg; then
            log_info "Installation de FFmpeg..."
            brew install ffmpeg
        fi
        
    elif [ "${OS_TYPE}" = "Linux" ]; then
        log_info "Installation sur Linux..."
        
        # Détecter le package manager
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y clamav clamav-daemon portaudio19-dev ffmpeg python3-dev build-essential
            
            # Mise à jour signatures ClamAV
            sudo freshclam || log_warning "Échec mise à jour signatures"
        elif command -v yum &> /dev/null; then
            sudo yum install -y clamav clamav-update portaudio-devel ffmpeg python3-devel gcc
            sudo freshclam || log_warning "Échec mise à jour signatures"
        else
            log_warning "Package manager non reconnu. Installation manuelle requise."
        fi
    fi
    
    log_success "Dépendances système installées"
}

###############################################################################
# Création de l'environnement virtuel Python
###############################################################################

setup_python_environment() {
    log_info "Configuration de l'environnement Python..."
    
    cd "${HOPPER_DIR}"
    
    # Créer venv si nécessaire
    if [ ! -d "${VENV_DIR}" ]; then
        log_info "Création de l'environnement virtuel..."
        python3 -m venv "${VENV_DIR}"
        log_success "Environnement virtuel créé"
    else
        log_success "Environnement virtuel existe déjà"
    fi
    
    # Activer venv
    source "${VENV_DIR}/bin/activate"
    
    # Mise à jour pip
    log_info "Mise à jour de pip..."
    pip install --upgrade pip setuptools wheel
    
    # Installer les dépendances
    if [ -f "${HOPPER_DIR}/requirements.txt" ]; then
        log_info "Installation des dépendances Python (peut prendre plusieurs minutes)..."
        pip install -r "${HOPPER_DIR}/requirements.txt"
        log_success "Dépendances Python installées"
    else
        log_warning "requirements.txt non trouvé"
    fi
}

###############################################################################
# Création des répertoires système
###############################################################################

setup_directories() {
    log_info "Création des répertoires système..."
    
    # Quarantine directory (nécessite sudo sur macOS)
    if [ ! -d "${QUARANTINE_DIR}" ]; then
        log_info "Création du répertoire de quarantaine..."
        sudo mkdir -p "${QUARANTINE_DIR}"
        sudo chmod 700 "${QUARANTINE_DIR}"
        log_success "Répertoire de quarantaine créé: ${QUARANTINE_DIR}"
    else
        log_success "Répertoire de quarantaine existe: ${QUARANTINE_DIR}"
    fi
    
    # Neo4j data directory
    if [ ! -d "${NEO4J_DATA_DIR}" ]; then
        log_info "Création du répertoire Neo4j..."
        mkdir -p "${NEO4J_DATA_DIR}"
        log_success "Répertoire Neo4j créé: ${NEO4J_DATA_DIR}"
    fi
    
    # Logs directory
    mkdir -p "${HOPPER_DIR}/logs"
    
    # Models directory
    mkdir -p "${HOPPER_DIR}/models"
    
    log_success "Répertoires système créés"
}

###############################################################################
# Configuration Docker
###############################################################################

setup_docker() {
    log_info "Configuration Docker..."
    
    cd "${HOPPER_DIR}"
    
    # Vérifier docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml non trouvé"
        exit 1
    fi
    
    # Pull des images
    log_info "Téléchargement des images Docker (peut prendre du temps)..."
    docker-compose pull || log_warning "Certaines images n'ont pas pu être téléchargées"
    
    # Build des services customs
    log_info "Construction des images personnalisées..."
    docker-compose build
    
    log_success "Docker configuré"
}

###############################################################################
# Téléchargement des modèles
###############################################################################

download_models() {
    log_info "Vérification des modèles LLM..."
    
    # Le modèle sera téléchargé au premier lancement
    log_info "Le modèle Llama-3.2-3B sera téléchargé au premier démarrage"
    log_warning "Note: Le téléchargement peut prendre 10-30 minutes selon votre connexion"
}

###############################################################################
# Tests de santé
###############################################################################

health_check() {
    log_info "Vérifications de santé..."
    
    # Vérifier que Docker tourne
    if ! docker info &> /dev/null; then
        log_error "Docker n'est pas en cours d'exécution"
        return 1
    fi
    
    # Vérifier Python imports critiques
    source "${VENV_DIR}/bin/activate"
    python3 -c "import fastapi, torch, transformers, neo4j, whisper" 2>/dev/null
    if [ $? -eq 0 ]; then
        log_success "Imports Python critiques OK"
    else
        log_warning "Certains imports Python ont échoué"
    fi
    
    log_success "Vérifications de santé terminées"
}

###############################################################################
# Affichage des informations finales
###############################################################################

print_summary() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    ✅ INSTALLATION TERMINÉE AVEC SUCCÈS                     ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${BLUE}📋 Prochaines étapes:${NC}"
    echo ""
    echo "1. Activer l'environnement virtuel:"
    echo -e "   ${YELLOW}source ${VENV_DIR}/bin/activate${NC}"
    echo ""
    echo "2. Démarrer les services Docker:"
    echo -e "   ${YELLOW}docker-compose up -d${NC}"
    echo ""
    echo "3. Démarrer HOPPER:"
    echo -e "   ${YELLOW}python3 src/orchestrator/main.py${NC}"
    echo ""
    echo "4. Surveiller les logs:"
    echo -e "   ${YELLOW}docker-compose logs -f${NC}"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "   - README.md"
    echo "   - docs/USER_GUIDE.md"
    echo "   - docs/ARCHITECTURE.md"
    echo ""
    echo -e "${BLUE}🔧 Scripts utilitaires:${NC}"
    echo "   - scripts/backup.sh    - Sauvegarde complète"
    echo "   - scripts/restore.sh   - Restauration"
    echo "   - scripts/update.sh    - Mise à jour système"
    echo "   - scripts/monitor.sh   - Surveillance ressources"
    echo "   - scripts/test_e2e.sh  - Tests end-to-end"
    echo ""
    echo -e "${GREEN}🎉 HOPPER est prêt à l'emploi !${NC}"
    echo ""
}

###############################################################################
# Script principal
###############################################################################

main() {
    print_header
    
    log_info "Démarrage de l'installation de HOPPER..."
    log_info "Répertoire d'installation: ${HOPPER_DIR}"
    echo ""
    
    # Exécution des étapes
    check_system
    echo ""
    
    install_system_dependencies
    echo ""
    
    setup_python_environment
    echo ""
    
    setup_directories
    echo ""
    
    setup_docker
    echo ""
    
    download_models
    echo ""
    
    health_check
    echo ""
    
    print_summary
}

# Exécution
main "$@"
