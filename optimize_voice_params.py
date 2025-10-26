#!/usr/bin/env python3
"""
🎚️ HOPPER Voice Parameters Optimizer
Teste différents paramètres TTS pour trouver la configuration optimale
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

# Import optionnel de torch avec gestion d'erreur
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore

# Import optionnel de loguru avec fallback
try:
    from loguru import logger
    # Configuration de loguru
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
    logger.error("❌ TTS non installé - pip install TTS")


# Configurations de paramètres à tester
PARAMETER_CONFIGS = {
    "ultra_stable": {
        "name": "Ultra Stable (Clarté maximale)",
        "temperature": 0.5,
        "length_penalty": 1.0,
        "repetition_penalty": 3.0,
        "top_k": 20,
        "top_p": 0.7,
        "speed": 0.85,
        "description": "Voix très stable et claire, idéale pour compréhension"
    },
    "balanced": {
        "name": "Équilibré (Recommandé)",
        "temperature": 0.65,
        "length_penalty": 1.0,
        "repetition_penalty": 2.5,
        "top_k": 30,
        "top_p": 0.75,
        "speed": 0.9,
        "description": "Bon équilibre entre naturalité et stabilité"
    },
    "natural": {
        "name": "Naturel",
        "temperature": 0.75,
        "length_penalty": 1.0,
        "repetition_penalty": 2.0,
        "top_k": 40,
        "top_p": 0.8,
        "speed": 1.0,
        "description": "Voix plus naturelle avec variations"
    },
    "expressive": {
        "name": "Expressif",
        "temperature": 0.85,
        "length_penalty": 1.0,
        "repetition_penalty": 1.8,
        "top_k": 50,
        "top_p": 0.85,
        "speed": 1.0,
        "description": "Maximum d'expressivité et d'émotions"
    },
    "slow_clear": {
        "name": "Lent et Clair",
        "temperature": 0.6,
        "length_penalty": 1.0,
        "repetition_penalty": 2.8,
        "top_k": 25,
        "top_p": 0.72,
        "speed": 0.8,
        "description": "Parfait pour tutoriels et explications"
    },
}


class VoiceParameterOptimizer:
    """Optimise les paramètres de génération vocale HOPPER"""
    
    def __init__(self, voice_sample_path: Optional[str] = None):
        """
        Args:
            voice_sample_path: Chemin vers l'échantillon vocal
        """
        if not TORCH_AVAILABLE:
            raise ImportError("torch est requis - pip install torch")
        if not TTS_AVAILABLE:
            raise ImportError("TTS est requis - pip install TTS")
            
        # Chercher le meilleur échantillon disponible
        if voice_sample_path is None:
            candidates = [
                "Hopper_voix_ultra_clean.wav",
                "Hopper_voix_improved.wav",
                "Hopper_voix_clean.wav",
                "Hopper_voix_24k.wav",
                "Hopper_voix_hq.wav",
                "Hopper_voix.wav.mp3",
            ]
            
            for candidate in candidates:
                if Path(candidate).exists():
                    voice_sample_path = candidate
                    logger.info(f"✅ Échantillon trouvé: {candidate}")
                    break
        
        if voice_sample_path is None:
            raise FileNotFoundError("Aucun échantillon vocal trouvé")
        
        self.voice_sample_path = Path(voice_sample_path)
        self.tts: Optional[Any] = None
        
        # Détection du device
        assert torch is not None
        if torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        
        logger.info(f"📱 Device: {self.device}")
    
    def load_model(self) -> None:
        """Charge le modèle TTS"""
        if not TTS_AVAILABLE:
            raise ImportError("TTS non installé")
        
        assert torch is not None
        assert TTS is not None
        
        logger.info("📥 Chargement du modèle XTTS-v2...")
        
        # Patch torch.load pour accepter les modèles TTS
        original_torch_load = torch.load
        def patched_torch_load(*args: Any, **kwargs: Any) -> Any:
            kwargs['weights_only'] = False
            return original_torch_load(*args, **kwargs)
        torch.load = patched_torch_load  # type: ignore
        
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        logger.success("✅ Modèle chargé")  # type: ignore
    
    def test_config(
        self,
        config_name: str,
        text: str,
        output_dir: Path
    ) -> str:
        """
        Teste une configuration de paramètres
        
        Args:
            config_name: Nom de la configuration
            text: Texte à synthétiser
            output_dir: Dossier de sortie
        
        Returns:
            Chemin du fichier généré
        """
        if config_name not in PARAMETER_CONFIGS:
            raise ValueError(f"Configuration inconnue: {config_name}")
        
        config = PARAMETER_CONFIGS[config_name]
        logger.info(f"🎚️  Test: {config['name']}")
        logger.info(f"   {config['description']}")
        
        output_file = output_dir / f"hopper_voice_{config_name}.wav"
        
        try:
            self.tts.tts_to_file(
                text=text,
                speaker_wav=str(self.voice_sample_path),
                language="fr",
                file_path=str(output_file),
                temperature=config['temperature'],
                length_penalty=config['length_penalty'],
                repetition_penalty=config['repetition_penalty'],
                top_k=config['top_k'],
                top_p=config['top_p'],
                speed=config['speed'],
                enable_text_splitting=True,
                split_sentences=True
            )
            
            size_kb = output_file.stat().st_size / 1024
            logger.success(f"   ✅ Généré: {output_file.name} ({size_kb:.1f} KB)")
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"   ❌ Erreur: {e}")
            raise
    
    def test_all_configs(
        self,
        text: Optional[str] = None,
        output_dir: str = "data/voice_tests"
    ) -> Dict[str, Any]:
        """
        Teste toutes les configurations
        
        Args:
            text: Texte à synthétiser (texte par défaut si None)
            output_dir: Dossier de sortie
        
        Returns:
            Dictionnaire des résultats
        """
        if text is None:
            text = (
                "Bonjour, je suis HOPPER, votre assistant personnel intelligent. "
                "Je peux vous aider avec vos tâches quotidiennes, "
                "répondre à vos questions et gérer vos fichiers."
            )
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.tts is None:
            self.load_model()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("🎚️  TEST DE TOUTES LES CONFIGURATIONS")
        logger.info("=" * 70)
        logger.info(f"Texte: {text}")
        logger.info("")
        
        results = {}
        
        for config_name in PARAMETER_CONFIGS:
            try:
                output_file = self.test_config(config_name, text, output_path)
                results[config_name] = {
                    "status": "success",
                    "file": output_file,
                    "config": PARAMETER_CONFIGS[config_name]
                }
            except Exception as e:
                results[config_name] = {
                    "status": "error",
                    "error": str(e),
                    "config": PARAMETER_CONFIGS[config_name]
                }
            
            logger.info("")
        
        # Sauvegarder les résultats
        results_file = output_path / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Résultats sauvegardés: {results_file}")
        
        return results
    
    def compare_samples(
        self,
        sample_paths: list,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare différents échantillons vocaux avec les mêmes paramètres
        
        Args:
            sample_paths: Liste des chemins d'échantillons à comparer
            text: Texte à synthétiser
        
        Returns:
            Dictionnaire des résultats
        """
        if text is None:
            text = "Bonjour, je suis HOPPER."
        
        output_dir = Path("data/voice_tests/sample_comparison")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.tts is None:
            self.load_model()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("🔬 COMPARAISON DES ÉCHANTILLONS VOCAUX")
        logger.info("=" * 70)
        logger.info("")
        
        # Configuration optimale pour le test
        config = PARAMETER_CONFIGS["balanced"]
        
        results = {}
        
        for sample_path in sample_paths:
            sample_path = Path(sample_path)
            if not sample_path.exists():
                logger.warning(f"⚠️  Échantillon non trouvé: {sample_path}")
                continue
            
            logger.info(f"🎤 Test avec: {sample_path.name}")
            
            output_file = output_dir / f"output_{sample_path.stem}.wav"
            
            try:
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=str(sample_path),
                    language="fr",
                    file_path=str(output_file),
                    **{k: v for k, v in config.items() if k not in ['name', 'description']}
                )
                
                size_kb = output_file.stat().st_size / 1024
                logger.success(f"   ✅ Généré: {output_file.name} ({size_kb:.1f} KB)")
                
                results[sample_path.name] = {
                    "status": "success",
                    "file": str(output_file)
                }
                
            except Exception as e:
                logger.error(f"   ❌ Erreur: {e}")
                results[sample_path.name] = {
                    "status": "error",
                    "error": str(e)
                }
            
            logger.info("")
        
        return results


def main():
    """Interface CLI pour l'optimisation des paramètres vocaux"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🎚️ Optimise les paramètres de génération vocale HOPPER"
    )
    parser.add_argument(
        "--sample",
        type=str,
        help="Échantillon vocal à utiliser (auto si non spécifié)"
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Texte à synthétiser (texte par défaut si non spécifié)"
    )
    parser.add_argument(
        "--config",
        type=str,
        choices=list(PARAMETER_CONFIGS.keys()),
        help="Tester une configuration spécifique uniquement"
    )
    parser.add_argument(
        "--compare-samples",
        action="store_true",
        help="Comparer tous les échantillons Hopper_voix_*"
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="Lister toutes les configurations disponibles"
    )
    
    args = parser.parse_args()
    
    # Lister les configurations
    if args.list_configs:
        print("=" * 70)
        print("📋 CONFIGURATIONS DISPONIBLES")
        print("=" * 70)
        print()
        for name, config in PARAMETER_CONFIGS.items():
            print(f"• {name}: {config['name']}")
            print(f"  {config['description']}")
            print(f"  Temperature: {config['temperature']}, Speed: {config['speed']}")
            print()
        return
    
    print("=" * 70)
    print("🎚️  HOPPER VOICE PARAMETER OPTIMIZER")
    print("=" * 70)
    print()
    
    try:
        optimizer = VoiceParameterOptimizer(args.sample)
        
        # Mode comparaison d'échantillons
        if args.compare_samples:
            samples = list(Path(".").glob("Hopper_voix*.wav")) + list(Path(".").glob("Hopper_voix*.mp3"))
            samples = [str(s) for s in samples]
            
            if not samples:
                logger.error("❌ Aucun échantillon trouvé")
                return
            
            optimizer.compare_samples(samples, args.text)
            
            print()
            print("✅ Comparaison terminée")
            print(f"📁 Résultats dans: data/voice_tests/sample_comparison/")
            print()
            return
        
        # Test d'une configuration spécifique
        if args.config:
            optimizer.load_model()
            output_dir = Path("data/voice_tests")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            text = args.text or "Bonjour, je suis HOPPER."
            optimizer.test_config(args.config, text, output_dir)
            
            print()
            print(f"✅ Test terminé: {args.config}")
            print(f"📁 Fichier dans: data/voice_tests/")
            print()
            return
        
        # Test de toutes les configurations
        results = optimizer.test_all_configs(text=args.text)
        
        print()
        print("=" * 70)
        print("✅ TESTS TERMINÉS")
        print("=" * 70)
        print()
        print("📁 Fichiers générés dans: data/voice_tests/")
        print()
        print("💡 Pour écouter:")
        print("   open data/voice_tests/")
        print()
        print("💡 Pour comparer:")
        for name, result in results.items():
            if result['status'] == 'success':
                config = PARAMETER_CONFIGS[name]
                print(f"   • {config['name']}: afplay '{result['file']}'")
        print()
        print("📊 Recommandations:")
        print("   1. Écoutez chaque version")
        print("   2. Choisissez celle qui sonne le mieux")
        print("   3. Mettez à jour test_voice_clone.py avec ces paramètres")
        print()
        
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        
    except ImportError:
        logger.error("❌ TTS non installé")
        print()
        print("💡 Installation:")
        print("   ./venv_tts/bin/pip install TTS")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
