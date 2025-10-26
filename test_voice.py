#!/usr/bin/env python3
"""
Script de test pour la voix clonée de HOPPER
"""

import sys
from pathlib import Path

# Ajouter le projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tts.voice_cloning import HopperVoiceCloner
from loguru import logger

def test_voice():
    """Test de génération vocale avec la voix de HOPPER"""
    
    print("=" * 70)
    print("🎤 TEST DE LA VOIX CLONÉE DE HOPPER")
    print("=" * 70)
    print()
    
    # Vérifier que l'échantillon vocal existe
    voice_sample = project_root / "Hopper_voix.wav.mp3"
    if not voice_sample.exists():
        print(f"❌ Échantillon vocal non trouvé: {voice_sample}")
        print(f"   Placez votre fichier audio à: {voice_sample}")
        return
    
    print(f"✅ Échantillon vocal trouvé: {voice_sample}")
    print()
    
    # Initialiser le cloner
    print("📦 Initialisation du Voice Cloner...")
    cloner = HopperVoiceCloner(
        voice_sample_path=str(voice_sample),
        device="auto"  # Détection automatique (CPU/CUDA/MPS)
    )
    
    # Charger le modèle
    print("📥 Chargement du modèle XTTS-v2 (cela peut prendre 1-2 minutes)...")
    try:
        cloner.load_model()
    except ImportError as e:
        print(f"\n❌ Erreur: {e}")
        print("\n💡 Installation requise:")
        print("   pip install TTS pydub")
        return
    
    # Préparer l'échantillon
    print("\n🎵 Préparation de l'échantillon vocal...")
    speaker_wav = cloner.prepare_voice_sample()
    print(f"✅ Échantillon préparé: {speaker_wav}")
    
    # Texte de test
    test_texts = [
        "Bonjour, je suis HOPPER, votre assistant personnel intelligent.",
        "Je suis capable de comprendre et d'exécuter vos commandes.",
        "Comment puis-je vous aider aujourd'hui ?",
        "Analysons ensemble cette situation complexe."
    ]
    
    print("\n" + "=" * 70)
    print("🗣️  GÉNÉRATION DE TESTS VOCAUX")
    print("=" * 70)
    
    output_dir = project_root / "data" / "voice_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n[{i}/{len(test_texts)}] Génération de: '{text[:50]}...'")
        
        output_file = output_dir / f"test_{i}.wav"
        
        try:
            cloner.generate_speech(
                text=text,
                output_path=str(output_file),
                language="fr",
                temperature=0.7,
                speed=1.0
            )
            print(f"     ✅ Généré: {output_file}")
        except Exception as e:
            print(f"     ❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("✅ TEST TERMINÉ")
    print("=" * 70)
    print(f"\n📁 Fichiers audio générés dans: {output_dir}")
    print("\n💡 Pour écouter les fichiers:")
    print(f"   open {output_dir}")
    print("\n💡 Pour tester avec un texte personnalisé:")
    print("   python test_voice.py --text \"Votre texte ici\"")
    print()

def test_custom_text(text: str):
    """Test avec un texte personnalisé"""
    
    voice_sample = project_root / "Hopper_voix.wav.mp3"
    if not voice_sample.exists():
        print(f"❌ Échantillon vocal non trouvé: {voice_sample}")
        return
    
    print(f"🎤 Génération de: '{text}'")
    print()
    
    cloner = HopperVoiceCloner(voice_sample_path=str(voice_sample))
    
    try:
        cloner.load_model()
    except ImportError as e:
        print(f"❌ {e}")
        print("💡 Installation: pip install TTS pydub")
        return
    
    speaker_wav = cloner.prepare_voice_sample()
    
    output_file = project_root / "data" / "voice_tests" / "custom.wav"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    cloner.generate_speech(
        text=text,
        output_path=str(output_file),
        language="fr",
        temperature=0.7,
        speed=1.0
    )
    
    print(f"✅ Généré: {output_file}")
    print(f"💡 Écouter: open {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test de la voix clonée de HOPPER")
    parser.add_argument("--text", type=str, help="Texte personnalisé à générer")
    
    args = parser.parse_args()
    
    if args.text:
        test_custom_text(args.text)
    else:
        test_voice()
