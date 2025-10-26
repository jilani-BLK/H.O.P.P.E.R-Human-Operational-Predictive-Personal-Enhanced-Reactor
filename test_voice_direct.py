#!/usr/bin/env python3
"""
Test direct de la voix HOPPER avec la commande say de macOS
"""

import subprocess
from pathlib import Path

def test_voice_direct():
    """Test avec la commande say native de macOS"""
    
    print("=" * 70)
    print("🎤 TEST DIRECT DE LA VOIX HOPPER")
    print("=" * 70)
    print()
    
    # Créer le répertoire de sortie
    output_dir = Path("/Users/jilani/Projet/HOPPER/data/voice_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Textes de test
    test_texts = [
        "Bonjour, je suis HOPPER, votre assistant personnel intelligent.",
        "Je suis prêt à vous aider avec vos tâches quotidiennes.",
        "Analysons ensemble cette situation complexe.",
        "Comment puis-je vous assister aujourd'hui ?"
    ]
    
    print("🗣️  Génération des fichiers audio...")
    print()
    
    # Voix françaises disponibles sur macOS
    voices = ["Thomas", "Amelie"]  # Thomas est masculin, Amelie est féminin
    
    for voice in voices:
        print(f"📢 Test avec la voix: {voice}")
        
        for i, text in enumerate(test_texts, 1):
            output_file = output_dir / f"test_{voice}_{i}.aiff"
            
            print(f"   [{i}/{len(test_texts)}] '{text[:40]}...'")
            
            try:
                result = subprocess.run(
                    ['say', '-v', voice, text, '-o', str(output_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=True
                )
                
                size_kb = output_file.stat().st_size / 1024
                print(f"        ✅ Généré: {output_file.name} ({size_kb:.1f} KB)")
                
            except subprocess.CalledProcessError as e:
                print(f"        ❌ Erreur: {e.stderr}")
            except Exception as e:
                print(f"        ❌ Erreur: {e}")
        
        print()
    
    print("=" * 70)
    print("✅ TEST TERMINÉ")
    print("=" * 70)
    print(f"\n📁 Fichiers audio générés dans: {output_dir}")
    print(f"\n💡 Pour écouter tous les fichiers:")
    print(f"   open {output_dir}")
    print()
    print(f"💡 Pour écouter un fichier spécifique:")
    print(f"   afplay {output_dir}/test_Thomas_1.aiff")
    print()
    print("💡 Voix disponibles sur macOS:")
    print("   Pour voir toutes les voix: say -v '?'")
    print()

def list_available_voices():
    """Liste toutes les voix disponibles"""
    
    print("=" * 70)
    print("🔊 VOIX DISPONIBLES SUR MACOS")
    print("=" * 70)
    print()
    
    result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True)
    
    # Filtrer les voix françaises
    print("📢 Voix françaises:")
    print()
    for line in result.stdout.split('\n'):
        if 'fr_' in line or 'French' in line:
            print(f"   {line}")
    
    print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test direct de la voix HOPPER")
    parser.add_argument("--list-voices", action="store_true", help="Liste les voix disponibles")
    parser.add_argument("--text", type=str, help="Texte personnalisé à générer")
    parser.add_argument("--voice", type=str, default="Thomas", help="Voix à utiliser (défaut: Thomas)")
    
    args = parser.parse_args()
    
    if args.list_voices:
        list_available_voices()
    elif args.text:
        output_dir = Path("/Users/jilani/Projet/HOPPER/data/voice_tests")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "custom.aiff"
        
        print(f"🎤 Génération avec voix {args.voice}: '{args.text}'")
        
        subprocess.run(
            ['say', '-v', args.voice, args.text, '-o', str(output_file)],
            check=True
        )
        
        print(f"✅ Généré: {output_file}")
        print(f"💡 Écouter: afplay {output_file}")
    else:
        test_voice_direct()
