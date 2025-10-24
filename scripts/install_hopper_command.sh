#!/bin/bash

# 🧠 Script d'installation de la commande HOPPER
# Crée un alias/lien global pour la commande 'hopper'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
HOPPER_CLI="$PROJECT_ROOT/src/cli/hopper"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}║          ${GREEN}Installation de la commande HOPPER${BLUE}         ║${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier que le fichier existe
if [ ! -f "$HOPPER_CLI" ]; then
    echo -e "${RED}❌ Fichier hopper non trouvé: $HOPPER_CLI${NC}"
    exit 1
fi

# Rendre le fichier exécutable
chmod +x "$HOPPER_CLI"

echo -e "${YELLOW}🔍 Choix de la méthode d'installation:${NC}"
echo ""
echo "1) Lien symbolique dans /usr/local/bin (recommandé)"
echo "2) Alias dans ~/.zshrc ou ~/.bashrc"
echo "3) Les deux"
echo "4) Annuler"
echo ""
read -p "Votre choix (1-4): " choice

case $choice in
    1|3)
        # Créer un lien symbolique
        echo ""
        echo -e "${YELLOW}📦 Installation du lien symbolique...${NC}"
        
        if [ -L "/usr/local/bin/hopper" ]; then
            echo -e "${YELLOW}⚠️  Lien symbolique existant détecté${NC}"
            read -p "   Écraser? (o/N): " overwrite
            if [[ ! $overwrite =~ ^[Oo]$ ]]; then
                echo -e "${YELLOW}   Lien symbolique conservé${NC}"
            else
                sudo rm /usr/local/bin/hopper
                sudo ln -s "$HOPPER_CLI" /usr/local/bin/hopper
                echo -e "${GREEN}✅ Lien symbolique mis à jour${NC}"
            fi
        else
            sudo ln -s "$HOPPER_CLI" /usr/local/bin/hopper
            echo -e "${GREEN}✅ Lien symbolique créé: /usr/local/bin/hopper${NC}"
        fi
        ;;
esac

case $choice in
    2|3)
        # Ajouter un alias
        echo ""
        echo -e "${YELLOW}📝 Configuration de l'alias...${NC}"
        
        # Détecter le shell
        if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
            RC_FILE="$HOME/.zshrc"
        else
            RC_FILE="$HOME/.bashrc"
        fi
        
        ALIAS_LINE="alias hopper='$HOPPER_CLI'"
        
        # Vérifier si l'alias existe déjà
        if grep -q "alias hopper=" "$RC_FILE" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Alias existant détecté dans $RC_FILE${NC}"
            read -p "   Écraser? (o/N): " overwrite
            if [[ $overwrite =~ ^[Oo]$ ]]; then
                # Supprimer l'ancien alias
                sed -i.bak '/alias hopper=/d' "$RC_FILE"
                # Ajouter le nouveau
                echo "" >> "$RC_FILE"
                echo "# HOPPER - Assistant Personnel Intelligent" >> "$RC_FILE"
                echo "$ALIAS_LINE" >> "$RC_FILE"
                echo -e "${GREEN}✅ Alias mis à jour dans $RC_FILE${NC}"
            else
                echo -e "${YELLOW}   Alias conservé${NC}"
            fi
        else
            # Ajouter l'alias
            echo "" >> "$RC_FILE"
            echo "# HOPPER - Assistant Personnel Intelligent" >> "$RC_FILE"
            echo "$ALIAS_LINE" >> "$RC_FILE"
            echo -e "${GREEN}✅ Alias ajouté à $RC_FILE${NC}"
        fi
        
        echo -e "${YELLOW}   Rechargez votre shell avec: source $RC_FILE${NC}"
        ;;
    4)
        echo -e "${YELLOW}❌ Installation annulée${NC}"
        exit 0
        ;;
esac

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║                  ✅ Installation réussie !                ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}🚀 Commandes disponibles:${NC}"
echo ""
echo -e "  ${GREEN}hopper${NC}              Lance l'interface TUI"
echo -e "  ${GREEN}hopper tui${NC}          Lance l'interface terminal"
echo -e "  ${GREEN}hopper start${NC}        Démarre l'orchestrateur"
echo -e "  ${GREEN}hopper status${NC}       Affiche le statut"
echo -e "  ${GREEN}hopper stop${NC}         Arrête HOPPER"
echo ""
echo -e "${YELLOW}💡 Testez maintenant: ${GREEN}hopper${NC}"
echo ""
