#!/usr/bin/env python3
"""
🔬 HOPPER Voice Quality Tester
Compare rapidement différentes versions de voix pour choisir la meilleure
"""

import sys
from pathlib import Path
from typing import Optional, Any

# Import optionnel de torch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore

# Import optionnel de loguru
try:
    from loguru import logger
    # Configuration
    logger.remove()
    logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # type: ignore

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    TTS = None  # type: ignore


def test_voice_quality() -> None:
    """Test rapide de qualité vocale avec différentes configurations"""
    
    if not TTS_AVAILABLE:
        print("❌ TTS non installé - pip install TTS")
        return
    
    if not TORCH_AVAILABLE:
        print("❌ torch non installé - pip install torch")
        return
    
    assert torch is not None
    assert TTS is not None
    
    print("=" * 70)
    print("🔬 HOPPER VOICE QUALITY TESTER")
    print("=" * 70)
    print()
    
    # Trouver tous les échantillons disponibles
    samples = []
    for pattern in ["Hopper_voix*.wav", "Hopper_voix*.mp3"]:
        samples.extend(Path(".").glob(pattern))
    
    if not samples:
        print("❌ Aucun échantillon vocal trouvé")
        return
    
    print(f"✅ {len(samples)} échantillon(s) trouvé(s):")
    for i, sample in enumerate(samples, 1):
        size_kb = sample.stat().st_size / 1024
        print(f"   {i}. {sample.name} ({size_kb:.1f} KB)")
    print()
    
    # Phrase de test
    test_text = "Bonjour, je suis HOPPER. Comment puis-je vous aider aujourd'hui ?"
    
    print(f"📝 Phrase de test:")
    print(f"   '{test_text}'")
    print()
    
    # Device
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    
    print(f"📱 Device: {device}")
    print()
    
    # Charger le modèle
    print("📥 Chargement du modèle XTTS-v2...")
    
    # Patch torch.load
    original_torch_load = torch.load
    def patched_torch_load(*args: Any, **kwargs: Any) -> Any:
        kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    torch.load = patched_torch_load  # type: ignore
    
    try:
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("✅ Modèle chargé")
    except Exception as e:
        print(f"❌ Erreur chargement: {e}")
        return
    
    print()
    print("=" * 70)
    print("🎤 GÉNÉRATION DES TESTS")
    print("=" * 70)
    print()
    
    # Créer le dossier de sortie
    output_dir = Path("data/voice_tests/quality_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Tester chaque échantillon avec les meilleurs paramètres
    results = []
    
    for sample in samples:
        print(f"🔊 Test avec: {sample.name}")
        
        output_file = output_dir / f"test_{sample.stem}.wav"
        
        try:
            tts.tts_to_file(
                text=test_text,
                speaker_wav=str(sample),
                language="fr",
                file_path=str(output_file),
                # Paramètres équilibrés pour test de qualité
                temperature=0.65,
                length_penalty=1.0,
                repetition_penalty=2.5,
                top_k=30,
                top_p=0.75,
                speed=0.9,
                enable_text_splitting=True,
                split_sentences=True
            )
            
            size_kb = output_file.stat().st_size / 1024
            print(f"   ✅ Généré: {output_file.name} ({size_kb:.1f} KB)")
            
            results.append({
                "sample": sample.name,
                "output": str(output_file),
                "success": True
            })
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results.append({
                "sample": sample.name,
                "success": False,
                "error": str(e)
            })
        
        print()
    
    # Résumé
    print("=" * 70)
    print("✅ TESTS TERMINÉS")
    print("=" * 70)
    print()
    print(f"📁 Fichiers générés dans: {output_dir}/")
    print()
    print("💡 Pour écouter et comparer:")
    print()
    
    for i, result in enumerate(results, 1):
        if result['success']:
            print(f"   {i}. {result['sample']}")
            print(f"      afplay '{result['output']}'")
            print()
    
    print("🎯 RECOMMANDATIONS:")
    print()
    print("   1. Écoutez chaque version ci-dessus")
    print("   2. Notez laquelle sonne le mieux (clarté, naturalité)")
    print("   3. Utilisez cet échantillon pour la production")
    print()
    print("   Les échantillons *_ultra_clean.wav et *_improved.wav")
    print("   devraient généralement donner les meilleurs résultats.")
    print()


if __name__ == "__main__":
    test_voice_quality()
