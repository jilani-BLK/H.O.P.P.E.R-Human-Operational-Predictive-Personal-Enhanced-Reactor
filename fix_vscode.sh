#!/bin/bash
# Script pour réparer les fichiers blancs dans VS Code

echo "🔧 Réparation de VS Code - Fichiers blancs"
echo "=========================================="
echo ""

# Solution 1: Nettoyer le cache VS Code
echo "1️⃣  Nettoyage du cache VS Code..."
if [ -d "$HOME/Library/Application Support/Code/Cache" ]; then
    rm -rf "$HOME/Library/Application Support/Code/Cache"/*
    echo "   ✅ Cache nettoyé"
else
    echo "   ⚠️  Dossier de cache non trouvé"
fi

if [ -d "$HOME/Library/Application Support/Code/CachedData" ]; then
    rm -rf "$HOME/Library/Application Support/Code/CachedData"/*
    echo "   ✅ CachedData nettoyé"
fi

echo ""

# Solution 2: Nettoyer le workspace storage
echo "2️⃣  Nettoyage du workspace storage..."
if [ -d "$HOME/Library/Application Support/Code/User/workspaceStorage" ]; then
    # Sauvegarder avant de supprimer
    cp -r "$HOME/Library/Application Support/Code/User/workspaceStorage" \
          "$HOME/Library/Application Support/Code/User/workspaceStorage.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null
    rm -rf "$HOME/Library/Application Support/Code/User/workspaceStorage"/*
    echo "   ✅ Workspace storage nettoyé"
else
    echo "   ⚠️  Workspace storage non trouvé"
fi

echo ""

# Solution 3: Vérifier l'encodage des fichiers
echo "3️⃣  Vérification de l'encodage..."
cd /Users/jilani/Projet/HOPPER
file -I src/cli/hopper src/orchestrator/main.py test_voice_clone.py | head -5

echo ""

# Solution 4: Créer/Mettre à jour .vscode/settings.json
echo "4️⃣  Configuration VS Code du projet..."
mkdir -p /Users/jilani/Projet/HOPPER/.vscode

cat > /Users/jilani/Projet/HOPPER/.vscode/settings.json << 'EOF'
{
    "files.encoding": "utf8",
    "files.autoGuessEncoding": true,
    "files.associations": {
        "*.py": "python",
        "*.sh": "shellscript",
        "*.md": "markdown",
        "*.json": "json",
        "hopper": "python"
    },
    "editor.renderWhitespace": "boundary",
    "editor.rulers": [80, 120],
    "python.analysis.typeCheckingMode": "basic",
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.DS_Store": true
    }
}
EOF

echo "   ✅ Configuration créée dans .vscode/settings.json"

echo ""

# Solution 5: Lister les extensions problématiques potentielles
echo "5️⃣  Extensions VS Code installées:"
code --list-extensions 2>/dev/null | grep -i "python\|pylance\|encoding" || echo "   Impossible de lister les extensions"

echo ""
echo "=========================================="
echo "✅ Réparations terminées !"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. Fermez complètement VS Code (Cmd+Q)"
echo "   2. Relancez VS Code"
echo "   3. Ouvrez le projet HOPPER"
echo "   4. Si le problème persiste, essayez :"
echo "      - Cmd+Shift+P → 'Developer: Reload Window'"
echo "      - Ou désactivez temporairement les extensions"
echo ""
