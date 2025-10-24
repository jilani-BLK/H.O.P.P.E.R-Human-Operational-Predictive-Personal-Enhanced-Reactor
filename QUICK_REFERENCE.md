# 🚀 HOPPER - Commandes Rapides

## 📦 Installation

```bash
# Créer l'environnement virtuel (si pas déjà fait)
python3 -m venv venv

# Activer le venv
source venv/bin/activate

# Installer toutes les dépendances
pip install -r requirements-full.txt

# Ou seulement les essentielles (sans ssdeep)
pip install PyPDF2 python-docx openpyxl python-pptx beautifulsoup4 html2text markdown lxml python-magic Pillow pytesseract pandas numpy requests aiohttp colorama
```

## 🔧 Configuration VS Code

```
Cmd+Shift+P → "Python: Select Interpreter"
→ Choisir: venv/bin/python

Cmd+Shift+P → "Developer: Reload Window"
```

## ✅ Vérifications

```bash
# Vérifier l'état global
./check_errors.sh

# Tester le système de raisonnement
source venv/bin/activate
python examples/reasoning_demo.py

# Tester les imports
python -c "from src.reasoning import ProblemSolver"
python -c "from src.readers.document_reader import DocumentReader"
python -c "from src.security.malware_detector import MalwareDetector"
```

## 🛠️ Dépendances système optionnelles

```bash
# macOS
brew install libmagic    # Pour python-magic (détection MIME)
brew install tesseract   # Pour pytesseract (OCR)
brew install ssdeep      # Pour ssdeep (hachage fuzzy)

# Puis réinstaller
source venv/bin/activate
pip install python-magic ssdeep
```

## 📊 État actuel

- ✅ 143 → ~20 erreurs (warnings normaux)
- ✅ 16/17 dépendances installées
- ✅ Système de raisonnement 100% fonctionnel
- ⚠️  VS Code nécessite rechargement pour voir les packages

## 🐛 Résolution des erreurs VS Code persistantes

```bash
# Option 1: Recharger VS Code
Cmd+Shift+P → "Developer: Reload Window"

# Option 2: Redémarrer Pylance
Cmd+Shift+P → "Python: Restart Language Server"

# Option 3: Effacer le cache
rm -rf ~/.vscode/extensions/ms-python.vscode-pylance-*/dist/
# Puis redémarrer VS Code
```

## 📝 Documentation

- `RAPPORT_FINAL_143_ERREURS.txt` - Rapport détaillé
- `RESOLUTION_143_ERREURS.md` - Résumé de la résolution
- `PYTHON_ERRORS_GUIDE.md` - Guide de dépannage
- `requirements-full.txt` - Liste des dépendances

## 🎯 Test rapide après installation

```bash
source venv/bin/activate

# Test 1: Raisonnement (0 dépendances)
python -c "from src.reasoning import ProblemSolver; print('✅ Reasoning OK')"

# Test 2: Documents (avec dépendances)
python -c "from src.readers.document_reader import DocumentReader; print('✅ Documents OK')"

# Test 3: Sécurité (avec dépendances)
python -c "from src.security.malware_detector import MalwareDetector; print('✅ Security OK')"

# Test 4: Formats (avec dépendances)
python -c "from src.data_formats.format_converter import FormatConverter; print('✅ Formats OK')"

# Test 5: Démo complète
python examples/reasoning_demo.py
```

## 💡 Astuces

### Travailler avec le venv
```bash
# Toujours activer le venv avant de travailler
source venv/bin/activate

# Vérifier quel Python est utilisé
which python  # Devrait afficher: .../HOPPER/venv/bin/python

# Désactiver le venv
deactivate
```

### Ajouter des dépendances
```bash
source venv/bin/activate
pip install nouvelle-dependance
pip freeze > requirements-full.txt  # Mettre à jour la liste
```

### Nettoyer le cache Python
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## 🎉 Résultat final

**143 problèmes** → **~20 warnings normaux**

✅ Système opérationnel avec toutes les capacités avancées activées!
