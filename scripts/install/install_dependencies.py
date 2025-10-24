#!/usr/bin/env python3
"""
Script d'installation des dépendances HOPPER
Installe toutes les bibliothèques nécessaires pour les fonctionnalités avancées
"""

import subprocess
import sys
from pathlib import Path


def install_package(package_name, pip_name=None):
    """Installe un package avec pip"""
    pip_name = pip_name or package_name
    print(f"📦 Installation de {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        print(f"   ✅ {package_name} installé")
        return True
    except subprocess.CalledProcessError:
        print(f"   ❌ Erreur lors de l'installation de {package_name}")
        return False


def main():
    """Installation de toutes les dépendances"""
    print("╔════════════════════════════════════════════════════════╗")
    print("║   INSTALLATION DES DÉPENDANCES HOPPER                 ║")
    print("╚════════════════════════════════════════════════════════╝\n")
    
    # Dépendances par catégorie
    dependencies = {
        "📄 Traitement de documents": [
            ("PyPDF2", "PyPDF2"),
            ("python-docx", "python-docx"),
            ("openpyxl", "openpyxl"),
            ("python-pptx", "python-pptx"),
        ],
        "🌐 Web et HTML": [
            ("BeautifulSoup4", "beautifulsoup4"),
            ("html2text", "html2text"),
            ("markdown", "markdown"),
            ("lxml", "lxml"),
        ],
        "🔒 Sécurité": [
            ("python-magic", "python-magic"),
            ("ssdeep", "ssdeep"),
        ],
        "🖼️ Images et OCR": [
            ("Pillow", "Pillow"),
            ("pytesseract", "pytesseract"),
        ],
        "📊 Données": [
            ("pandas", "pandas"),
            ("numpy", "numpy"),
        ],
        "🔧 Utilitaires": [
            ("requests", "requests"),
            ("aiohttp", "aiohttp"),
            ("colorama", "colorama"),
        ],
    }
    
    total = 0
    success = 0
    failed = []
    
    for category, packages in dependencies.items():
        print(f"\n{category}")
        print("─" * 56)
        for display_name, pip_name in packages:
            total += 1
            if install_package(display_name, pip_name):
                success += 1
            else:
                failed.append(display_name)
    
    # Résumé
    print("\n" + "═" * 56)
    print("RÉSUMÉ DE L'INSTALLATION")
    print("═" * 56)
    print(f"✅ Succès: {success}/{total}")
    
    if failed:
        print(f"❌ Échecs: {len(failed)}")
        print("\nPackages non installés:")
        for pkg in failed:
            print(f"   • {pkg}")
        print("\n💡 Certains packages peuvent nécessiter des dépendances système.")
        print("   Consultez la documentation de chaque package pour plus d'infos.")
    else:
        print("\n🎉 Toutes les dépendances ont été installées avec succès!")
    
    print("\n📝 Notes importantes:")
    print("   • pytesseract nécessite Tesseract OCR installé sur le système")
    print("   • python-magic peut nécessiter libmagic sur certains systèmes")
    print("   • ssdeep peut nécessiter des outils de compilation")
    
    return len(failed) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
