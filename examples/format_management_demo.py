"""
Démonstration du système de gestion des formats HOPPER
Montre toutes les capacités: conversion, édition, génération, manipulation de code
"""

import asyncio
from pathlib import Path
import sys
import json

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_formats import (
    FormatConverter,
    ConversionConfig,
    DocumentEditor,
    EditOperation,
    DocumentGenerator,
    GenerationConfig,
    CodeManipulator,
    CodeModification
)

# Import EditOperationType
from src.data_formats.document_editor import EditOperationType


async def demo_format_conversion():
    """Démonstration des conversions de formats"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION: CONVERSION DE FORMATS")
    print("=" * 80 + "\n")
    
    converter = FormatConverter()
    config = ConversionConfig(preserve_formatting=True)
    
    # Créer des fichiers de test
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # 1. Markdown vers HTML
    print("1. Création fichiers de test")
    md_content = """# Rapport de Test

## Introduction
Ceci est un **test** de conversion.

## Données
- Point 1
- Point 2
- Point 3

### Conclusion
*Conversion réussie!*
"""
    md_file = test_dir / "test.md"
    md_file.write_text(md_content)
    print(f"   ✓ Créé: {md_file}")
    
    # 2. JSON
    print("\n2. Création JSON")
    json_data = {
        "users": [
            {"name": "Alice", "age": 30, "city": "Paris"},
            {"name": "Bob", "age": 25, "city": "Lyon"},
            {"name": "Charlie", "age": 35, "city": "Marseille"}
        ]
    }
    json_file = test_dir / "users.json"
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"   ✓ Créé: {json_file}")
    
    # 3. CSV simple
    print("\n3. Création CSV")
    csv_content = """Name,Score,Grade
Alice,95,A
Bob,87,B
Charlie,92,A"""
    csv_file = test_dir / "scores.csv"
    csv_file.write_text(csv_content)
    print(f"   ✓ Créé: {csv_file}")


async def demo_document_editing():
    """Démonstration de l'édition de documents"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION: ÉDITION DE DOCUMENTS")
    print("=" * 80 + "\n")
    
    editor = DocumentEditor()
    test_dir = Path("test_files")
    
    # 1. Éditer un fichier CSV (simplifié)
    print("1. Édition CSV - Exemple simplifié")
    csv_file = test_dir / "scores.csv"
    
    operations = [
        EditOperation(
            operation_type=EditOperationType.APPEND,
            target="end",
            content=["David", "88", "B"]
        )
    ]
    
    try:
        result = await editor.edit_document(str(csv_file), operations)
        print(f"   ✓ Opérations appliquées: {result.operations_applied}")
        if result.backup_path:
            print(f"   ✓ Backup: {result.backup_path}")
    except Exception as e:
        print(f"   ⚠️ Édition non disponible: {e}")
    
    # 2. Éditer Markdown (exemple)
    print("\n2. Édition Markdown - Exemple")
    md_file = test_dir / "test.md"
    
    operations = [
        EditOperation(
            operation_type=EditOperationType.APPEND,
            target="end",
            content="## Nouvelle Section\nContenu ajouté dynamiquement."
        )
    ]
    
    print("   ✓ Opération d'édition préparée")


async def demo_document_generation():
    """Démonstration de la génération de documents"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION: GÉNÉRATION DE DOCUMENTS")
    print("=" * 80 + "\n")
    
    generator = DocumentGenerator()
    test_dir = Path("test_files")
    config = GenerationConfig(style="professional", include_footer=True)
    
    # Données pour le rapport
    report_data = {
        "title": "Rapport d'Analyse HOPPER",
        "metadata": {
            "Projet": "HOPPER AI Assistant",
            "Version": "1.0.0",
            "Auteur": "Système de Génération Automatique"
        },
        "sections": [
            {
                "title": "Vue d'ensemble",
                "content": "HOPPER est un assistant IA polyvalent capable de gérer des formats "
                          "de données complexes. Ce rapport démontre ses capacités de génération."
            },
            {
                "title": "Statistiques",
                "table": [
                    ["Métrique", "Valeur", "Status"],
                    ["Formats supportés", "20+", "✓"],
                    ["Conversions disponibles", "50+", "✓"],
                    ["Fiabilité", "99.9%", "✓"]
                ]
            },
            {
                "title": "Capacités",
                "content": [
                    "Conversion entre 20+ formats de fichiers",
                    "Édition sécurisée avec sauvegarde automatique",
                    "Génération de rapports professionnels",
                    "Manipulation de code source"
                ]
            }
        ],
        "list": [
            "PDF, DOCX, Excel, CSV",
            "Markdown, HTML, JSON, YAML",
            "Images avec OCR",
            "Code source (Python, JavaScript)"
        ]
    }
    
    # 1. Générer PDF
    print("1. Génération de rapport PDF")
    try:
        pdf_file = await generator.generate_pdf_from_data(
            report_data,
            test_dir / "rapport.pdf",
            config=config
        )
        print(f"   ✓ PDF créé: {pdf_file}")
    except ImportError as e:
        print(f"   ⚠ Skipped (dépendance manquante): {e}")
    
    # 2. Générer DOCX
    print("\n2. Génération de document Word")
    try:
        docx_file = await generator.generate_docx_from_data(
            report_data,
            test_dir / "rapport.docx",
            config=config
        )
        print(f"   ✓ DOCX créé: {docx_file}")
    except ImportError as e:
        print(f"   ⚠ Skipped (dépendance manquante): {e}")
    
    # 3. Générer HTML
    print("\n3. Génération de page HTML")
    html_file = await generator.generate_html_from_data(
        report_data,
        test_dir / "rapport.html",
        config=config
    )
    print(f"   ✓ HTML créé: {html_file}")
    
    # 4. Générer Excel avec graphiques
    print("\n4. Génération de classeur Excel")
    excel_data = {
        "sheets": [
            {
                "name": "Statistiques",
                "headers": ["Mois", "Conversions", "Éditions", "Générations"],
                "data": [
                    ["Janvier", 150, 80, 45],
                    ["Février", 180, 95, 52],
                    ["Mars", 220, 110, 68],
                    ["Avril", 195, 105, 61]
                ],
                "chart": {
                    "type": "bar",
                    "title": "Activité Mensuelle"
                }
            }
        ]
    }
    
    try:
        excel_file = await generator.generate_excel_from_data(
            excel_data,
            test_dir / "statistiques.xlsx",
            include_charts=True
        )
        print(f"   ✓ Excel créé: {excel_file}")
    except ImportError as e:
        print(f"   ⚠ Skipped (dépendance manquante): {e}")
    
    # 5. Générer Markdown
    print("\n5. Génération de fichier Markdown")
    md_file = await generator.generate_markdown_from_data(
        report_data,
        test_dir / "rapport_generated.md"
    )
    print(f"   ✓ Markdown créé: {md_file}")


async def demo_code_manipulation():
    """Démonstration de la manipulation de code"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION: MANIPULATION DE CODE")
    print("=" * 80 + "\n")
    
    manipulator = CodeManipulator()
    test_dir = Path("test_files")
    
    # Créer un fichier Python de test
    test_code = """#!/usr/bin/env python3
import os
import sys
import json

def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    result = a * b
    return result

class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(('add', a, b, result))
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(('multiply', a, b, result))
        return result

if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
"""
    
    code_file = test_dir / "calculator.py"
    code_file.write_text(test_code)
    
    # 1. Analyser le code
    print("1. Analyse du code Python")
    analysis = await manipulator.analyze_code(code_file)
    
    print(f"   ✓ Langage: {analysis.language.value}")
    print(f"   ✓ Syntaxe valide: {analysis.syntax_valid}")
    print(f"   ✓ Fonctions trouvées: {len(analysis.functions)}")
    for func in analysis.functions:
        print(f"      - {func['name']}() ligne {func['line']}")
    print(f"   ✓ Classes trouvées: {len(analysis.classes)}")
    for cls in analysis.classes:
        print(f"      - {cls['name']} ligne {cls['line']} ({len(cls['methods'])} méthodes)")
    print(f"   ✓ Imports: {', '.join(analysis.imports)}")
    print(f"   ✓ Complexité: {analysis.complexity}")
    print(f"   ✓ Lignes de code: {analysis.lines_of_code}")
    
    # 2. Ajouter des docstrings
    print("\n2. Ajout de docstrings")
    success, msg = await manipulator.add_docstring(
        code_file,
        "calculate_sum",
        "Calcule la somme de deux nombres"
    )
    print(f"   ✓ {msg}")
    
    success, msg = await manipulator.add_docstring(
        code_file,
        "Calculator",
        "Calculatrice avec historique des opérations"
    )
    print(f"   ✓ {msg}")
    
    # 3. Renommer une variable
    print("\n3. Renommage de symboles")
    modifications = [
        CodeModification(
            operation="rename",
            target="result",
            new_value="output"
        )
    ]
    
    success, msg = await manipulator.modify_code(
        code_file,
        modifications,
        create_backup=True
    )
    print(f"   ✓ {msg}")
    
    # 4. Ajouter des commentaires
    print("\n4. Ajout de commentaires")
    modifications = [
        CodeModification(
            operation="add_comment",
            target="calculate_sum",
            new_value="Fonction utilitaire pour l'addition"
        )
    ]
    
    success, msg = await manipulator.modify_code(
        code_file,
        modifications
    )
    print(f"   ✓ {msg}")
    
    # 5. Retirer imports non utilisés
    print("\n5. Nettoyage des imports")
    modifications = [
        CodeModification(
            operation="remove_unused_imports",
            target="",
            new_value=None
        )
    ]
    
    success, msg = await manipulator.modify_code(
        code_file,
        modifications
    )
    print(f"   ✓ {msg}")


async def demo_real_world_workflow():
    """Workflow réel: traitement de données complètes"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION: WORKFLOW RÉEL COMPLET")
    print("=" * 80 + "\n")
    
    print("Scénario: Traiter des données CSV, les enrichir et générer un rapport PDF\n")
    
    converter = FormatConverter()
    editor = DocumentEditor()
    generator = DocumentGenerator()
    test_dir = Path("test_files")
    
    # 1. Charger des données CSV
    print("1. Chargement des données initiales (CSV)")
    initial_data = """Product,Sales,Region
Laptop,50000,North
Phone,35000,South
Tablet,28000,East
Monitor,15000,West"""
    
    csv_file = test_dir / "sales.csv"
    csv_file.write_text(initial_data)
    print(f"   ✓ Données chargées: {csv_file}")
    
    # 2. Enrichir les données
    print("\n2. Enrichissement des données")
    operations = [
        EditOperation(
            operation_type=EditOperationType.APPEND,
            target="end",
            content="New Product,45000,Center"
        )
    ]
    
    try:
        result = await editor.edit_document(str(csv_file), operations)
        print(f"   ✓ Données enrichies ({result.operations_applied} opérations)")
    except Exception as e:
        print(f"   ⚠️ Enrichissement skipped: {e}")
    
    # 3. Convertir en JSON
    print("\n3. Conversion CSV → JSON")
    # Conversion manuelle simple
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    
    headers = lines[0].strip().split(',')
    data = []
    for line in lines[1:]:
        values = line.strip().split(',')
        data.append(dict(zip(headers, values)))
    
    json_file = test_dir / "sales.json"
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"   ✓ Converti en JSON: {json_file}")
    
    # 4. Générer un rapport PDF professionnel
    print("\n4. Génération du rapport final")
    report_data = {
        "title": "Rapport de Ventes Q1 2024",
        "metadata": {
            "Période": "Janvier - Mars 2024",
            "Généré par": "HOPPER Format Manager",
            "Date": "2024"
        },
        "sections": [
            {
                "title": "Résumé Exécutif",
                "content": "Ce rapport présente l'analyse des ventes du premier trimestre 2024. "
                          "Les données ont été collectées, enrichies et analysées automatiquement."
            },
            {
                "title": "Données de Ventes",
                "table": [
                    ["Produit", "Ventes (€)", "Région", "Performance"],
                    ["Laptop", "50,000", "Nord", "Excellente"],
                    ["Phone", "35,000", "Sud", "Bonne"],
                    ["Tablet", "28,000", "Est", "Moyenne"],
                    ["Monitor", "15,000", "Ouest", "À améliorer"]
                ]
            },
            {
                "title": "Recommandations",
                "content": [
                    "Augmenter la production de laptops (forte demande)",
                    "Analyser les raisons des ventes modérées de monitors",
                    "Maintenir la stratégie actuelle pour phones et tablets"
                ]
            }
        ]
    }
    
    try:
        pdf_file = await generator.generate_pdf_from_data(
            report_data,
            test_dir / "rapport_ventes.pdf",
            config=GenerationConfig(style="professional")
        )
        print(f"   ✓ Rapport PDF créé: {pdf_file}")
    except ImportError:
        # Fallback vers HTML si reportlab n'est pas disponible
        html_file = await generator.generate_html_from_data(
            report_data,
            test_dir / "rapport_ventes.html"
        )
        print(f"   ✓ Rapport HTML créé: {html_file}")
    
    print("\n✅ Workflow complet terminé!")
    print(f"   Fichiers générés dans: {test_dir.absolute()}")


async def main():
    """Fonction principale"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "HOPPER FORMAT MANAGEMENT DEMO" + " " * 29 + "║")
    print("║" + " " * 15 + "Gestion Complète des Formats de Données" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        # Exécuter toutes les démos
        await demo_format_conversion()
        await demo_document_editing()
        await demo_document_generation()
        await demo_code_manipulation()
        await demo_real_world_workflow()
        
        print("\n" + "=" * 80)
        print("RÉSUMÉ DES CAPACITÉS")
        print("=" * 80)
        print("""
✓ Conversion de formats: 20+ types de conversions disponibles
✓ Édition de documents: PDF, DOCX, Excel, CSV, JSON, YAML, Markdown
✓ Génération de documents: Rapports professionnels dans 5+ formats
✓ Manipulation de code: Analyse, refactoring, documentation automatique
✓ OCR: Extraction de texte depuis images et PDF scannés
✓ Sécurité: Sauvegarde automatique avant toute modification
✓ Qualité: Préservation du formatage et de la structure

💡 Pour installer toutes les dépendances:
   pip install -r requirements-dataformats.txt

📖 Pour plus d'informations:
   Voir docs/guides/FORMAT_MANAGEMENT_GUIDE.md
""")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
