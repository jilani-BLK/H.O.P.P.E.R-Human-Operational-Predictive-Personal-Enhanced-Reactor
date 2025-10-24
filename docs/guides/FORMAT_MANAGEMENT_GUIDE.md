# 📄 Guide de Gestion des Formats HOPPER

## Vue d'ensemble

Le système de gestion des formats HOPPER permet de manipuler plus de 20 types de fichiers différents avec 4 modules complémentaires:

- **FormatConverter**: Convertir entre différents formats
- **DocumentEditor**: Éditer des documents de manière sécurisée
- **DocumentGenerator**: Créer des documents à partir de données
- **CodeManipulator**: Analyser et modifier du code source

## 🔧 Installation

```bash
# Installation des dépendances
pip install -r requirements-dataformats.txt

# Dépendances optionnelles pour OCR
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Télécharger depuis https://github.com/UB-Mannheim/tesseract/wiki
```

## 📦 Formats Supportés

### Documents
- **PDF**: Lecture, conversion, édition, génération
- **DOCX**: Lecture, conversion, édition, génération
- **ODT**: Conversion

### Données
- **Excel** (.xlsx): Lecture, conversion, édition, génération avec graphiques
- **CSV**: Lecture, conversion, édition
- **JSON**: Conversion, édition
- **YAML**: Conversion, édition

### Web et Texte
- **HTML**: Conversion, génération
- **Markdown**: Conversion bidirectionnelle, génération
- **TXT**: Extraction depuis tous formats

### Code Source
- **Python**: Analyse AST, refactoring, documentation
- **JavaScript**: Analyse basique, édition
- **TypeScript**: Détection et édition

### Images
- **JPG/PNG**: Conversion, OCR
- **PDF scannés**: OCR pour extraction de texte

---

## 🔄 Module 1: FormatConverter

### Utilisation de Base

```python
from src.data_formats import FormatConverter, ConversionConfig

# Initialiser le convertisseur
converter = FormatConverter()

# Configuration pour haute qualité
config = ConversionConfig(
    quality=95,
    preserve_formatting=True,
    preserve_images=True,
    preserve_tables=True,
    dpi=300,
    ocr_language='fra'
)
```

### Conversions Disponibles

#### PDF → Autres Formats

```python
# PDF vers JSON (structure complète)
json_data = await converter.pdf_to_json('document.pdf', config)

# PDF vers texte brut
text_file = await converter.pdf_to_text('document.pdf', 'output.txt', config)

# PDF vers Word
docx_file = await converter.pdf_to_docx('document.pdf', 'output.docx', config)

# PDF vers images (une par page)
images = await converter.pdf_to_images('document.pdf', 'output_dir/', config)
```

#### DOCX → Autres Formats

```python
# Word vers PDF
pdf_file = await converter.docx_to_pdf('document.docx', 'output.pdf', config)

# Word vers Markdown
md_file = await converter.docx_to_markdown('document.docx', 'output.md', config)

# Word vers HTML
html_file = await converter.docx_to_html('document.docx', 'output.html', config)
```

#### Excel → Autres Formats

```python
# Excel vers CSV (première feuille)
csv_file = await converter.excel_to_csv('data.xlsx', 'output.csv')

# Excel vers JSON (structure complète)
json_data = await converter.excel_to_json('data.xlsx', config)

# Excel vers PDF
pdf_file = await converter.excel_to_pdf('data.xlsx', 'output.pdf', config)
```

#### Markdown et HTML

```python
# Markdown vers HTML
html_file = await converter.markdown_to_html('README.md', 'index.html', config)

# HTML vers Markdown
md_file = await converter.html_to_markdown('page.html', 'output.md')

# HTML vers texte
text_file = await converter.html_to_text('page.html', 'output.txt')
```

#### OCR (Images → Texte)

```python
# Extraire texte d'une image
text = await converter.image_to_text('scan.jpg', config)

# Avec langue spécifique
config.ocr_language = 'fra+eng'  # Français + Anglais
text = await converter.image_to_text('multilingual.png', config)
```

#### JSON/CSV

```python
# CSV vers Excel
excel_file = await converter.csv_to_excel('data.csv', 'output.xlsx')

# CSV vers JSON
json_file = await converter.csv_to_json('data.csv', 'output.json')

# JSON vers Excel
data = {"users": [{"name": "Alice", "age": 30}]}
excel_file = await converter.json_to_excel(data, 'users.xlsx')
```

### Conversion Universelle

```python
# Auto-détection du format source
output = await converter.convert(
    source='input.pdf',
    target_format='docx',
    config=config
)
```

### Conversion par Lot

```python
# Convertir plusieurs fichiers
files = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']
results = await converter.batch_convert(
    files,
    target_format='docx',
    output_dir='converted/',
    config=config
)
```

---

## ✏️ Module 2: DocumentEditor

### Principe de Sécurité

Toutes les opérations d'édition créent automatiquement une sauvegarde avant modification.

```python
from src.data_formats import DocumentEditor, EditOperation

editor = DocumentEditor()

# En cas d'erreur, le fichier original est restauré
# Backup disponible dans result.backup_path
```

### Éditer des PDF

```python
# Opérations disponibles
operations = [
    # Fusionner des pages
    EditOperation(
        operation_type="merge_pages",
        target="page",
        parameters={"pages": [1, 2, 3]}
    ),
    
    # Diviser en plusieurs fichiers
    EditOperation(
        operation_type="split_pages",
        target="page",
        parameters={"ranges": [(1, 5), (6, 10)]}
    ),
    
    # Rotation
    EditOperation(
        operation_type="rotate_page",
        target="page",
        parameters={"page_number": 1, "angle": 90}
    ),
    
    # Filigrane
    EditOperation(
        operation_type="add_watermark",
        target="all",
        content="CONFIDENTIEL",
        parameters={"opacity": 0.3}
    ),
    
    # Métadonnées
    EditOperation(
        operation_type="modify_metadata",
        target="metadata",
        content={"title": "Nouveau titre", "author": "HOPPER"}
    )
]

result = await editor.edit_pdf('document.pdf', operations)
print(result.message)  # Résultat
print(result.backup_path)  # Chemin du backup
```

### Éditer des Documents Word

```python
operations = [
    # Remplacer du texte
    EditOperation(
        operation_type="replace_text",
        target="ancien_texte",
        content="nouveau_texte"
    ),
    
    # Ajouter un paragraphe
    EditOperation(
        operation_type="add_paragraph",
        target="end",
        content="Nouveau paragraphe",
        parameters={"style": "Heading 1"}
    ),
    
    # Modifier le formatage
    EditOperation(
        operation_type="change_formatting",
        target="paragraph",
        parameters={
            "paragraph_index": 0,
            "bold": True,
            "font_size": 14,
            "color": "blue"
        }
    ),
    
    # Ajouter un tableau
    EditOperation(
        operation_type="add_table",
        target="end",
        content=[
            ["Nom", "Âge", "Ville"],
            ["Alice", "30", "Paris"],
            ["Bob", "25", "Lyon"]
        ]
    )
]

result = await editor.edit_docx('document.docx', operations)
```

### Éditer des Fichiers Excel

```python
operations = [
    # Mettre à jour une cellule
    EditOperation(
        operation_type="update_cell",
        target="A1",
        content="Nouveau titre"
    ),
    
    # Mettre à jour une plage
    EditOperation(
        operation_type="update_range",
        target="B2:D4",
        content=[
            [100, 200, 300],
            [400, 500, 600],
            [700, 800, 900]
        ]
    ),
    
    # Ajouter une formule
    EditOperation(
        operation_type="add_formula",
        target="E2",
        content="=SUM(B2:D2)"
    ),
    
    # Ajouter une feuille
    EditOperation(
        operation_type="add_sheet",
        target="Nouvelle Feuille",
        content=None
    ),
    
    # Formater des cellules
    EditOperation(
        operation_type="format_cells",
        target="A1:D1",
        parameters={
            "bold": True,
            "background_color": "blue",
            "font_color": "white"
        }
    )
]

result = await editor.edit_excel('data.xlsx', operations)
```

### Éditer des CSV

```python
operations = [
    # Ajouter une ligne
    EditOperation(
        operation_type="add_row",
        target="end",
        content=["Alice", "30", "Paris"]
    ),
    
    # Mettre à jour une ligne
    EditOperation(
        operation_type="update_row",
        target="1",  # Index de ligne
        content=["Bob", "25", "Lyon"]
    ),
    
    # Supprimer une ligne
    EditOperation(
        operation_type="delete_row",
        target="2"
    ),
    
    # Ajouter une colonne
    EditOperation(
        operation_type="add_column",
        target="Email",
        parameters={"position": "end"}
    ),
    
    # Trier les données
    EditOperation(
        operation_type="sort_data",
        target="Age",  # Colonne de tri
        parameters={"ascending": False}
    )
]

result = await editor.edit_csv('data.csv', operations)
```

### Fusionner des Documents

```python
# Fusionner plusieurs PDF
output = await editor.merge_pdf_files(
    files=['doc1.pdf', 'doc2.pdf', 'doc3.pdf'],
    output='merged.pdf'
)

# Fusionner plusieurs Word
output = await editor.merge_docx_files(
    files=['doc1.docx', 'doc2.docx'],
    output='merged.docx'
)
```

### Restaurer un Backup

```python
# Si quelque chose s'est mal passé
result = await editor.edit_pdf('document.pdf', operations)

if not result.success:
    # Restaurer manuellement
    await editor.restore_backup(
        backup_path=result.backup_path,
        original_path='document.pdf'
    )
```

---

## 📝 Module 3: DocumentGenerator

### Génération de PDF

```python
from src.data_formats import DocumentGenerator, GenerationConfig

generator = DocumentGenerator()

# Configuration
config = GenerationConfig(
    page_size="A4",
    orientation="portrait",
    style="professional",  # professional, modern, minimal, colorful
    include_header=True,
    include_footer=True,
    include_page_numbers=True
)

# Structure des données
data = {
    "title": "Rapport Annuel 2024",
    "metadata": {
        "Auteur": "Équipe HOPPER",
        "Date": "2024",
        "Version": "1.0"
    },
    "sections": [
        {
            "title": "Introduction",
            "content": "Contenu de l'introduction..."
        },
        {
            "title": "Résultats",
            "content": [
                "Premier paragraphe",
                "Deuxième paragraphe"
            ],
            "table": [
                ["Métrique", "Q1", "Q2", "Q3", "Q4"],
                ["Ventes", "100K", "150K", "180K", "200K"],
                ["Profit", "20K", "35K", "45K", "55K"]
            ]
        },
        {
            "title": "Graphiques",
            "image": "chart.png"  # Chemin vers une image
        }
    ],
    "list": [
        "Point important 1",
        "Point important 2",
        "Point important 3"
    ]
}

# Générer le PDF
pdf_file = await generator.generate_pdf_from_data(
    data,
    output='rapport.pdf',
    config=config
)
```

### Génération de Word

```python
# Même structure de données
docx_file = await generator.generate_docx_from_data(
    data,
    output='rapport.docx',
    config=config
)
```

### Génération d'Excel avec Graphiques

```python
excel_data = {
    "sheets": [
        {
            "name": "Ventes 2024",
            "headers": ["Mois", "Ventes", "Objectif"],
            "data": [
                ["Janvier", 50000, 45000],
                ["Février", 60000, 55000],
                ["Mars", 75000, 65000]
            ],
            "chart": {
                "type": "bar",  # bar, line, pie
                "title": "Évolution des Ventes"
            }
        },
        {
            "name": "Clients",
            "headers": ["Nom", "Commandes", "Total"],
            "data": [
                ["Entreprise A", 15, 75000],
                ["Entreprise B", 12, 60000]
            ]
        }
    ]
}

excel_file = await generator.generate_excel_from_data(
    excel_data,
    output='rapport.xlsx',
    include_charts=True
)
```

### Génération HTML

```python
# Avec template Jinja2 (optionnel)
html_template = """
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ title }}</h1>
    {% for section in sections %}
        <h2>{{ section.title }}</h2>
        <p>{{ section.content }}</p>
    {% endfor %}
</body>
</html>
"""

html_file = await generator.generate_html_from_data(
    data,
    output='rapport.html',
    template=html_template,  # Ou chemin vers fichier .html
    config=config
)
```

### Génération Markdown

```python
md_file = await generator.generate_markdown_from_data(
    data,
    output='rapport.md'
)
```

### Génération Rapide

```python
# Créer un rapport dans n'importe quel format
output = await generator.create_report_from_dict(
    data,
    output_format='pdf',  # pdf, docx, html, xlsx, md
    output='rapport.pdf',
    config=config
)
```

### Styles Prédéfinis

```python
# 4 styles disponibles:

# 1. Professional (bleu foncé, élégant)
config = GenerationConfig(style="professional")

# 2. Modern (couleurs vives, contemporain)
config = GenerationConfig(style="modern")

# 3. Minimal (noir et blanc, épuré)
config = GenerationConfig(style="minimal")

# 4. Colorful (multicolore, dynamique)
config = GenerationConfig(style="colorful")
```

---

## 🔍 Module 4: CodeManipulator

### Analyse de Code

```python
from src.data_formats import CodeManipulator

manipulator = CodeManipulator()

# Analyser un fichier Python
analysis = await manipulator.analyze_code('script.py')

print(f"Langage: {analysis.language.value}")
print(f"Syntaxe valide: {analysis.syntax_valid}")
print(f"Complexité: {analysis.complexity}")
print(f"Lignes de code: {analysis.lines_of_code}")

# Fonctions trouvées
for func in analysis.functions:
    print(f"- {func['name']}() ligne {func['line']}")
    print(f"  Args: {func['args']}")
    print(f"  Doc: {func['docstring']}")

# Classes trouvées
for cls in analysis.classes:
    print(f"- {cls['name']} ligne {cls['line']}")
    print(f"  Méthodes: {cls['methods']}")
    print(f"  Doc: {cls['docstring']}")

# Imports
print(f"Imports: {analysis.imports}")

# Erreurs
if analysis.errors:
    for error in analysis.errors:
        print(f"❌ {error}")
```

### Détection de Langage

```python
# Automatique depuis le fichier
language = manipulator.detect_language(file_path='script.js')

# Ou depuis le contenu
code = """
function hello() {
    console.log('Hello');
}
"""
language = manipulator.detect_language(code=code)
```

### Modification de Code

```python
from src.data_formats import CodeModification

# Renommer un symbole
modifications = [
    CodeModification(
        operation="rename",
        target="old_function_name",
        new_value="new_function_name"
    )
]

success, message = await manipulator.modify_code(
    'script.py',
    modifications,
    create_backup=True
)
```

### Ajouter des Commentaires

```python
# Commentaire avant une fonction
modifications = [
    CodeModification(
        operation="add_comment",
        target="calculate_sum",
        new_value="Cette fonction calcule la somme"
    )
]

# Commentaire à une ligne spécifique
modifications = [
    CodeModification(
        operation="add_comment",
        target="",
        new_value="Important: vérifier la validité",
        line_number=42
    )
]

success, msg = await manipulator.modify_code('script.py', modifications)
```

### Retirer Imports Non Utilisés

```python
modifications = [
    CodeModification(
        operation="remove_unused_imports",
        target="",
        new_value=None
    )
]

success, msg = await manipulator.modify_code('script.py', modifications)
```

### Ajouter des Docstrings

```python
# Docstring pour une fonction
success, msg = await manipulator.add_docstring(
    'script.py',
    target='calculate_sum',
    docstring='Calcule la somme de deux nombres et retourne le résultat'
)

# Docstring pour une classe
success, msg = await manipulator.add_docstring(
    'script.py',
    target='Calculator',
    docstring='Classe pour effectuer des calculs mathématiques de base'
)
```

### Extraire une Fonction

```python
# Extraire les lignes 10-20 dans une nouvelle fonction
success, msg = await manipulator.extract_function(
    'script.py',
    start_line=10,
    end_line=20,
    function_name='extracted_logic'
)
```

### Formater du Code

```python
modifications = [
    CodeModification(
        operation="format",
        target="",
        new_value={"max_line_length": 80}
    )
]

success, msg = await manipulator.modify_code('script.py', modifications)
```

---

## 💡 Cas d'Usage Réels

### 1. Pipeline de Traitement de Données

```python
async def process_data_pipeline():
    """Convertir CSV → enrichir → générer rapport"""
    
    # 1. Charger et enrichir
    editor = DocumentEditor()
    operations = [
        EditOperation("add_column", "Profit", parameters={"position": "end"})
    ]
    await editor.edit_csv('sales.csv', operations)
    
    # 2. Convertir pour analyse
    converter = FormatConverter()
    json_data = await converter.csv_to_json('sales.csv', 'sales.json')
    
    # 3. Générer rapport
    generator = DocumentGenerator()
    report_data = {
        "title": "Rapport de Ventes",
        "sections": [...]
    }
    await generator.generate_pdf_from_data(report_data, 'rapport.pdf')
```

### 2. Documentation Automatique de Code

```python
async def auto_document_code():
    """Analyser le code et générer documentation"""
    
    manipulator = CodeManipulator()
    
    # Analyser
    analysis = await manipulator.analyze_code('projet.py')
    
    # Créer documentation
    doc_data = {
        "title": "Documentation du Projet",
        "sections": []
    }
    
    # Fonctions
    for func in analysis.functions:
        doc_data["sections"].append({
            "title": f"Fonction: {func['name']}",
            "content": f"Arguments: {func['args']}\n{func['docstring']}"
        })
    
    # Générer
    generator = DocumentGenerator()
    await generator.generate_markdown_from_data(doc_data, 'API.md')
```

### 3. Migration de Format en Masse

```python
async def batch_convert_documents():
    """Convertir tous les PDF d'un dossier en Word"""
    
    from pathlib import Path
    
    converter = FormatConverter()
    config = ConversionConfig(quality=95)
    
    pdf_files = list(Path('documents/').glob('*.pdf'))
    
    results = await converter.batch_convert(
        pdf_files,
        target_format='docx',
        output_dir='converted/',
        config=config
    )
    
    for result in results:
        print(f"✓ {result}")
```

### 4. Génération de Rapports Automatisés

```python
async def generate_monthly_report(data):
    """Rapport mensuel automatique"""
    
    generator = DocumentGenerator()
    
    report = {
        "title": f"Rapport {data['month']} {data['year']}",
        "metadata": {
            "Période": f"{data['month']} {data['year']}",
            "Généré": datetime.now().strftime("%d/%m/%Y")
        },
        "sections": [
            {
                "title": "Métriques Clés",
                "table": data['metrics_table']
            },
            {
                "title": "Tendances",
                "image": data['trend_chart']
            }
        ]
    }
    
    # Générer dans plusieurs formats
    await generator.generate_pdf_from_data(report, f"rapport_{data['month']}.pdf")
    await generator.generate_html_from_data(report, f"rapport_{data['month']}.html")
```

---

## ⚠️ Bonnes Pratiques

### Sécurité

1. **Toujours activer les backups lors de l'édition**
   ```python
   result = await editor.edit_pdf('important.pdf', operations)
   # Backup automatique créé à result.backup_path
   ```

2. **Valider les données avant génération**
   ```python
   if not data.get('title'):
       raise ValueError("Titre requis")
   ```

3. **Gérer les erreurs d'import**
   ```python
   try:
       await converter.pdf_to_docx('file.pdf', 'out.docx')
   except ImportError as e:
       print(f"Dépendance manquante: {e}")
   ```

### Performance

1. **Utiliser la conversion par lot pour plusieurs fichiers**
   ```python
   # ✓ Bon
   await converter.batch_convert(files, 'pdf')
   
   # ✗ Moins efficace
   for file in files:
       await converter.convert(file, 'pdf')
   ```

2. **Ajuster la qualité selon le besoin**
   ```python
   # Haute qualité pour documents officiels
   config = ConversionConfig(quality=95, dpi=300)
   
   # Qualité standard pour preview
   config = ConversionConfig(quality=75, dpi=150)
   ```

3. **OCR: utiliser uniquement quand nécessaire**
   ```python
   # OCR coûteux, seulement pour scans
   if is_scanned_document(file):
       text = await converter.image_to_text(file, config)
   ```

### Qualité

1. **Préserver le formatage lors des conversions**
   ```python
   config = ConversionConfig(
       preserve_formatting=True,
       preserve_images=True,
       preserve_tables=True
   )
   ```

2. **Tester les modifications sur une copie d'abord**
   ```python
   # Copier avant test
   import shutil
   shutil.copy('original.pdf', 'test.pdf')
   await editor.edit_pdf('test.pdf', operations)
   ```

3. **Valider le code après modifications**
   ```python
   success, msg = await manipulator.modify_code('script.py', mods)
   if success:
       # Re-analyser pour vérifier
       analysis = await manipulator.analyze_code('script.py')
       assert analysis.syntax_valid
   ```

---

## 🐛 Dépannage

### Erreur: Module Not Found

```bash
# Installer toutes les dépendances
pip install -r requirements-dataformats.txt

# Ou installer individuellement
pip install PyPDF2 python-docx openpyxl reportlab pandas
```

### OCR Ne Fonctionne Pas

```bash
# Vérifier tesseract
tesseract --version

# Installer si absent (macOS)
brew install tesseract tesseract-lang

# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-fra
```

### Erreur de Conversion PDF

```python
# Vérifier que le PDF n'est pas protégé
from PyPDF2 import PdfReader
reader = PdfReader('file.pdf')
if reader.is_encrypted:
    print("PDF protégé par mot de passe")
```

### Excel: Erreur de Format

```python
# S'assurer que le fichier est .xlsx (pas .xls)
# Convertir .xls en .xlsx d'abord
import pandas as pd
df = pd.read_excel('old.xls')
df.to_excel('new.xlsx', index=False)
```

### Code: Erreur de Syntaxe Après Modification

```python
# Restaurer le backup
await editor.restore_backup(backup_path, original_path)

# Vérifier la syntaxe avant de modifier
analysis = await manipulator.analyze_code('script.py')
if not analysis.syntax_valid:
    print("Code déjà invalide!")
```

---

## 📚 Exemples Supplémentaires

Voir le fichier `examples/format_management_demo.py` pour des exemples complets et fonctionnels.

```bash
# Exécuter la démo
python examples/format_management_demo.py
```

---

## 🤝 Intégration avec Agent LLM

```python
from src.agent.llm_agent import LLMAgent
from src.data_formats import FormatConverter, DocumentGenerator

agent = LLMAgent()

# L'agent peut maintenant utiliser les outils de format
@agent.register_tool
async def convert_document(source: str, target_format: str):
    """Convertir un document"""
    converter = FormatConverter()
    return await converter.convert(source, target_format)

@agent.register_tool
async def generate_report(data: dict, output: str):
    """Générer un rapport"""
    generator = DocumentGenerator()
    return await generator.create_report_from_dict(data, 'pdf', output)
```

---

## 📊 Performances

| Opération | Fichier 10MB | Fichier 100MB | Notes |
|-----------|--------------|---------------|-------|
| PDF → DOCX | ~2s | ~15s | Dépend du nombre de pages |
| Excel → JSON | ~0.5s | ~5s | Rapide avec pandas |
| OCR (1 page) | ~3s | N/A | Variable selon qualité |
| Edit CSV | ~0.1s | ~1s | Très rapide |
| Generate PDF | ~1s | N/A | Dépend du contenu |

---

## 🔮 Fonctionnalités À Venir

- [ ] Support pour plus de langages (Ruby, Go, Rust)
- [ ] Conversion vidéo/audio vers texte
- [ ] Templates de documents professionnels
- [ ] Batch processing parallèle optimisé
- [ ] Interface CLI interactive
- [ ] API REST pour services distants

---

## 📞 Support

Pour toute question ou problème:
- Voir les exemples dans `examples/`
- Consulter le code source dans `src/data_formats/`
- Ouvrir une issue sur le projet

---

**Version**: 1.0.0  
**Dernière mise à jour**: 2024  
**Auteur**: Équipe HOPPER
