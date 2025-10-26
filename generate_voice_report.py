#!/usr/bin/env python3
"""
📊 Génère un rapport de synthèse de l'amélioration vocale HOPPER
"""

from pathlib import Path
from datetime import datetime
import json

def generate_improvement_report():
    """Génère un rapport complet de l'amélioration"""
    
    report = []
    report.append("=" * 70)
    report.append("🎤 RAPPORT D'AMÉLIORATION DE LA VOIX HOPPER")
    report.append("=" * 70)
    report.append(f"\nDate: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    report.append(f"Générateur: Système d'amélioration vocale HOPPER v1.0\n")
    
    # Section 1: Fichiers créés
    report.append("\n" + "=" * 70)
    report.append("📁 NOUVEAUX OUTILS CRÉÉS")
    report.append("=" * 70)
    
    tools = [
        ("improve_hopper_voice.py", "Amélioration qualité audio de l'échantillon"),
        ("optimize_voice_params.py", "Optimisation des paramètres TTS"),
        ("test_voice_quality.py", "Test rapide de qualité comparative"),
        ("improve_voice_workflow.sh", "Workflow automatisé complet"),
        ("docs/VOICE_IMPROVEMENT_GUIDE.md", "Guide complet d'utilisation"),
        ("VOICE_IMPROVEMENT_README.md", "Guide de démarrage rapide"),
    ]
    
    for tool, description in tools:
        path = Path(tool)
        if path.exists():
            size = path.stat().st_size / 1024
            report.append(f"\n✅ {tool}")
            report.append(f"   {description}")
            report.append(f"   Taille: {size:.1f} KB")
        else:
            report.append(f"\n⚠️  {tool} - Non trouvé")
    
    # Section 2: Échantillons disponibles
    report.append("\n\n" + "=" * 70)
    report.append("🎵 ÉCHANTILLONS VOCAUX DISPONIBLES")
    report.append("=" * 70)
    
    samples = list(Path(".").glob("Hopper_voix*.wav")) + list(Path(".").glob("Hopper_voix*.mp3"))
    
    if samples:
        report.append(f"\n{len(samples)} échantillon(s) trouvé(s):\n")
        for sample in sorted(samples):
            size = sample.stat().st_size / 1024
            
            # Recommandations
            if "ultra_clean" in sample.name:
                badge = "⭐ RECOMMANDÉ"
            elif "clean" in sample.name or "24k" in sample.name:
                badge = "✅ Excellent"
            elif sample.suffix == ".mp3":
                badge = "⚠️  À convertir"
            else:
                badge = "✓ Bon"
            
            report.append(f"{badge} {sample.name} ({size:.1f} KB)")
    else:
        report.append("\n⚠️  Aucun échantillon trouvé")
    
    # Section 3: Résultats de tests
    report.append("\n\n" + "=" * 70)
    report.append("📊 RÉSULTATS DES TESTS")
    report.append("=" * 70)
    
    test_dirs = [
        "data/voice_tests",
        "data/voice_tests/quality_comparison",
        "data/voice_tests/sample_comparison",
    ]
    
    for test_dir in test_dirs:
        path = Path(test_dir)
        if path.exists():
            wav_files = list(path.glob("*.wav"))
            json_files = list(path.glob("*.json"))
            
            if wav_files or json_files:
                report.append(f"\n📁 {test_dir}/")
                if wav_files:
                    report.append(f"   {len(wav_files)} fichier(s) audio généré(s)")
                if json_files:
                    report.append(f"   {len(json_files)} rapport(s) JSON")
    
    # Section 4: Configurations disponibles
    report.append("\n\n" + "=" * 70)
    report.append("🎚️  CONFIGURATIONS DE PARAMÈTRES DISPONIBLES")
    report.append("=" * 70)
    
    configs = {
        "ultra_stable": "Clarté maximale - Idéal pour compréhension",
        "balanced": "⭐ RECOMMANDÉ - Équilibre naturalité/stabilité",
        "natural": "Plus naturel avec variations",
        "expressive": "Maximum d'émotions",
        "slow_clear": "Parfait pour tutoriels et explications"
    }
    
    report.append("")
    for name, desc in configs.items():
        report.append(f"• {name}")
        report.append(f"  {desc}")
    
    # Section 5: Prochaines étapes
    report.append("\n\n" + "=" * 70)
    report.append("🚀 PROCHAINES ÉTAPES RECOMMANDÉES")
    report.append("=" * 70)
    report.append("""
1. EXÉCUTER LE WORKFLOW COMPLET
   ./improve_voice_workflow.sh
   
   OU étape par étape:
   
2. ANALYSER LES ÉCHANTILLONS
   python improve_hopper_voice.py --compare
   
3. TESTER LA QUALITÉ
   python test_voice_quality.py
   → Écouter dans: data/voice_tests/quality_comparison/
   
4. OPTIMISER LES PARAMÈTRES
   python optimize_voice_params.py
   → Écouter dans: data/voice_tests/
   
5. CHOISIR ET NOTER
   - Meilleur échantillon: _______________________
   - Meilleure configuration: ____________________
   
6. METTRE À JOUR test_voice_clone.py
   - Ligne ~30: Utiliser votre échantillon choisi
   - Ligne ~127: Utiliser vos paramètres choisis
   
7. TESTER EN PRODUCTION
   python test_voice_clone.py
""")
    
    # Section 6: Ressources
    report.append("\n" + "=" * 70)
    report.append("📚 RESSOURCES ET DOCUMENTATION")
    report.append("=" * 70)
    report.append("""
• Guide de démarrage rapide:
  cat VOICE_IMPROVEMENT_README.md
  
• Guide complet:
  cat docs/VOICE_IMPROVEMENT_GUIDE.md
  
• Documentation TTS originale:
  cat VOICE_CLONING.md
  
• Troubleshooting:
  cat TROUBLESHOOTING.md
""")
    
    # Section 7: Métriques de succès
    report.append("\n" + "=" * 70)
    report.append("✅ CRITÈRES DE SUCCÈS")
    report.append("=" * 70)
    report.append("""
Votre amélioration est réussie si vous obtenez:

✓ CLARTÉ
  Chaque mot est parfaitement compréhensible
  
✓ NATURALITÉ
  La voix sonne humaine, pas robotique
  
✓ CONSISTANCE
  Qualité stable sur différentes phrases
  
✓ ÉMOTION
  Capable d'exprimer différentes tonalités
  
✓ PERFORMANCE
  Génération rapide (<5 secondes par phrase)
""")
    
    # Générer le rapport
    report_text = "\n".join(report)
    
    # Sauvegarder
    report_file = Path("VOICE_IMPROVEMENT_REPORT.txt")
    report_file.write_text(report_text, encoding='utf-8')
    
    # Afficher
    print(report_text)
    print("\n" + "=" * 70)
    print(f"📄 Rapport sauvegardé: {report_file}")
    print("=" * 70)
    print()


if __name__ == "__main__":
    generate_improvement_report()
