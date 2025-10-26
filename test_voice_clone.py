#!/usr/bin/env python3
"""
Script de clonage vocal HOPPER avec TTS XTTS-v2
Clone parfaitement la voix depuis l'échantillon Hopper_voix.wav.mp3
"""

import sys
from pathlib import Path
import torch

# Ajouter le projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_voice_cloning():
    """Test de clonage vocal avec XTTS-v2"""
    
    print("=" * 70)
    print("🎤 CLONAGE VOCAL HOPPER AVEC XTTS-V2")
    print("=" * 70)
    print()
    
    # Vérifier TTS
    try:
        from TTS.api import TTS
    except ImportError:
        print("❌ TTS (Coqui) n'est pas installé")
        print()
        print("💡 Installation:")
        print("   ./venv_tts/bin/pip install TTS")
        return
    
    # Vérifier l'échantillon vocal - préférer l'ultra-nettoyé
    voice_sample_ultra = project_root / "Hopper_voix_ultra_clean.wav"
    voice_sample_clean = project_root / "Hopper_voix_clean.wav"
    voice_sample_24k = project_root / "Hopper_voix_24k.wav"
    voice_sample_hq = project_root / "Hopper_voix_hq.wav"
    voice_sample_mp3 = project_root / "Hopper_voix.wav.mp3"
    
    if voice_sample_ultra.exists():
        voice_sample = voice_sample_ultra
        print(f"✅ Échantillon vocal ultra-nettoyé: {voice_sample}")
    elif voice_sample_clean.exists():
        voice_sample = voice_sample_clean
        print(f"✅ Échantillon vocal nettoyé: {voice_sample}")
    elif voice_sample_24k.exists():
        voice_sample = voice_sample_24k
        print(f"✅ Échantillon vocal 24kHz: {voice_sample}")
    elif voice_sample_hq.exists():
        voice_sample = voice_sample_hq
        print(f"✅ Échantillon vocal HQ: {voice_sample}")
    elif voice_sample_mp3.exists():
        voice_sample = voice_sample_mp3
        print(f"✅ Échantillon vocal: {voice_sample}")
    else:
        print(f"❌ Échantillon vocal non trouvé")
        return
    
    size_mb = voice_sample.stat().st_size / (1024 * 1024)
    print(f"   Taille: {size_mb:.2f} MB")
    print()
    
    # Fix pour PyTorch 2.9+ - Patch torch.load pour accepter les modèles TTS
    # TTS/Coqui est une source de confiance (Mozilla/Coqui-AI)
    original_torch_load = torch.load
    
    def patched_torch_load(*args, **kwargs):
        """Version patchée de torch.load qui force weights_only=False pour TTS"""
        # Forcer weights_only=False pour les modèles TTS (source de confiance)
        kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    
    # Remplacer temporairement torch.load
    torch.load = patched_torch_load
    print("✅ PyTorch load patché pour accepter les modèles TTS")
    
    # Détection du device
    # Note: XTTS-v2 a des problèmes avec MPS, on utilise CPU pour la stabilité
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"  # CPU est plus stable pour XTTS-v2
    
    print(f"📱 Device: {device} (CPU recommandé pour XTTS-v2)")
    print()
    
    # Charger le modèle XTTS-v2
    print("📥 Chargement du modèle XTTS-v2...")
    print("   (Première fois: téléchargement ~2GB, peut prendre quelques minutes)")
    print()
    
    try:
        
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("✅ Modèle chargé avec succès")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        print()
        print("💡 Solution alternative: utilisez test_voice_direct.py")
        return
    
    print()
    print("=" * 70)
    print("🗣️  GÉNÉRATION AVEC LA VOIX CLONÉE DE HOPPER")
    print("=" * 70)
    print()
    
    # Textes de test
    test_texts = [
        "Bonjour, je suis HOPPER, votre assistant personnel intelligent.",
        "Je suis capable de comprendre et d'exécuter vos commandes de manière autonome.",
        "Analysons ensemble cette situation complexe.",
        "Comment puis-je vous aider aujourd'hui ?",
        "Je peux gérer vos fichiers, vos recherches et bien plus encore."
    ]
    
    # Créer le répertoire de sortie
    output_dir = project_root / "data" / "voice_cloning"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, text in enumerate(test_texts, 1):
        print(f"[{i}/{len(test_texts)}] '{text[:50]}...'")
        
        output_file = output_dir / f"hopper_clone_{i}.wav"
        
        try:
            # Générer avec paramètres optimisés - Configuration "ultra_stable"
            # Configuration ultra-stable pour voix fluide sans hésitation
            # Pour modifier ces paramètres, utilisez optimize_voice_params.py
            tts.tts_to_file(
                text=text,
                speaker_wav=str(voice_sample),
                language="fr",
                file_path=str(output_file),
                # Paramètres ultra-stables pour clarté maximale et fluidité
                temperature=0.45,  # Très faible = voix plus déterministe, fluide
                length_penalty=1.0,  
                repetition_penalty=3.0,  # Forte pénalité contre les répétitions
                top_k=10,  # Très sélectif = moins d'hésitation
                top_p=0.60,  # Très confiant = pas de recherche de mots
                speed=0.85,  # Légèrement ralenti pour articulation parfaite
                enable_text_splitting=True,
                split_sentences=True
            )
            
            size_kb = output_file.stat().st_size / 1024
            print(f"     ✅ Généré: {output_file.name} ({size_kb:.1f} KB)")
            
        except Exception as e:
            print(f"     ❌ Erreur: {e}")
    
    print()
    print("=" * 70)
    print("✅ CLONAGE TERMINÉ")
    print("=" * 70)
    print()
    print(f"📁 Fichiers générés dans: {output_dir}")
    print()
    print("💡 Pour écouter:")
    print(f"   open {output_dir}")
    print()
    print("💡 Pour jouer un fichier:")
    print(f"   afplay {output_dir}/hopper_clone_1.wav")
    print()

def clone_custom_text(text: str, emotion: str = "neutral"):
    """Clone avec un texte personnalisé"""
    
    try:
        from TTS.api import TTS
    except ImportError:
        print("❌ TTS non installé")
        return
    
    voice_sample = project_root / "Hopper_voix.wav.mp3"
    if not voice_sample.exists():
        print(f"❌ Échantillon vocal non trouvé: {voice_sample}")
        return
    
    print(f"🎤 Clonage de: '{text}'")
    print(f"   Émotion: {emotion}")
    print()
    
    # Device
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    
    print(f"📥 Chargement du modèle sur {device}...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    
    output_file = project_root / "data" / "voice_cloning" / "custom.wav"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("🎵 Génération en cours...")
    
    tts.tts_to_file(
        text=text,
        speaker_wav=str(voice_sample),
        language="fr",
        file_path=str(output_file),
        emotion=emotion,
        speed=1.0
    )
    
    print(f"✅ Généré: {output_file}")
    print(f"💡 Écouter: afplay {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clonage vocal HOPPER avec XTTS-v2")
    parser.add_argument("--text", type=str, help="Texte personnalisé à cloner")
    parser.add_argument(
        "--emotion",
        type=str,
        default="neutral",
        choices=["neutral", "happy", "sad", "angry", "surprised"],
        help="Émotion à appliquer"
    )
    
    args = parser.parse_args()
    
    if args.text:
        clone_custom_text(args.text, args.emotion)
    else:
        test_voice_cloning()
