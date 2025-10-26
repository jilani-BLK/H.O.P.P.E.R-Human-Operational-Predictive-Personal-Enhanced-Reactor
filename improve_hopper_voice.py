#!/usr/bin/env python3
"""
🎤 HOPPER Voice Improvement Tool
Optimise les échantillons vocaux et les paramètres TTS pour une voix parfaite
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile

# Import optionnel de loguru avec fallback sur logging
try:
    from loguru import logger
    # Configuration de loguru
    logger.remove()
    logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # type: ignore

# Imports optionnels avec gestion d'erreur
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("⚠️  numpy non installé - pip install numpy")

try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None  # type: ignore
    logger.warning("⚠️  pydub non installé - pip install pydub")

try:
    import noisereduce as nr
    NOISE_REDUCE_AVAILABLE = True
except ImportError:
    NOISE_REDUCE_AVAILABLE = False

try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class HopperVoiceImprover:
    """
    Améliore la qualité des échantillons vocaux pour le clonage HOPPER
    
    Optimisations:
    - Normalisation audio
    - Réduction de bruit
    - Égalisation pour la voix
    - Conversion format optimal pour XTTS-v2
    - Compression dynamique
    """
    
    # Configuration optimale pour XTTS-v2
    OPTIMAL_SAMPLE_RATE = 22050  # Hz - Préférence XTTS-v2
    OPTIMAL_CHANNELS = 1  # Mono
    OPTIMAL_DURATION_MIN = 6  # secondes
    OPTIMAL_DURATION_MAX = 30  # secondes
    
    def __init__(self, source_path: str):
        """
        Args:
            source_path: Chemin vers l'échantillon vocal source
        """
        if not PYDUB_AVAILABLE:
            raise ImportError(
                "pydub est requis pour l'amélioration audio.\n"
                "Installation: pip install pydub\n"
                "Sur macOS, vous devez aussi: brew install ffmpeg"
            )
            
        self.source_path = Path(source_path)
        if not self.source_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {source_path}")
        
        self.audio: Optional[Any] = None
        self.original_stats: Dict[str, Any] = {}
        
    def analyze(self) -> Dict[str, Any]:
        """Analyse l'échantillon vocal et retourne ses caractéristiques"""
        logger.info(f"📊 Analyse de: {self.source_path.name}")
        
        assert AudioSegment is not None
        self.audio = AudioSegment.from_file(str(self.source_path))
        
        stats = {
            "file": str(self.source_path),
            "duration": len(self.audio) / 1000,  # secondes
            "sample_rate": self.audio.frame_rate,
            "channels": self.audio.channels,
            "sample_width": self.audio.sample_width,
            "frame_width": self.audio.frame_width,
            "file_size_kb": self.source_path.stat().st_size / 1024,
            "bit_depth": self.audio.sample_width * 8,
            "dBFS": self.audio.dBFS,  # Niveau moyen
            "max_dBFS": self.audio.max_dBFS,  # Niveau max
        }
        
        self.original_stats = stats
        
        # Afficher les stats
        logger.info(f"   Durée: {stats['duration']:.2f}s")
        logger.info(f"   Format: {stats['channels']}ch @ {stats['sample_rate']}Hz, {stats['bit_depth']}-bit")
        logger.info(f"   Taille: {stats['file_size_kb']:.1f} KB")
        logger.info(f"   Niveau: {stats['dBFS']:.1f} dBFS (max: {stats['max_dBFS']:.1f} dBFS)")
        
        # Recommandations
        issues = []
        if stats['duration'] < self.OPTIMAL_DURATION_MIN:
            issues.append(f"⚠️  Durée courte ({stats['duration']:.1f}s) - Min recommandé: {self.OPTIMAL_DURATION_MIN}s")
        if stats['duration'] > self.OPTIMAL_DURATION_MAX:
            issues.append(f"ℹ️  Durée longue ({stats['duration']:.1f}s) - Optimal: 10-22s")
        if stats['sample_rate'] != self.OPTIMAL_SAMPLE_RATE:
            issues.append(f"ℹ️  Sample rate: {stats['sample_rate']}Hz (XTTS-v2 préfère {self.OPTIMAL_SAMPLE_RATE}Hz)")
        if stats['channels'] != self.OPTIMAL_CHANNELS:
            issues.append(f"ℹ️  Stéréo détecté - Conversion mono recommandée")
        if stats['dBFS'] < -20:
            issues.append(f"⚠️  Volume faible ({stats['dBFS']:.1f} dBFS) - Normalisation recommandée")
        if stats['dBFS'] > -3:
            issues.append(f"⚠️  Volume élevé ({stats['dBFS']:.1f} dBFS) - Risque de saturation")
        
        if issues:
            logger.info("")
            for issue in issues:
                logger.warning(issue)
        else:
            logger.success("✅ Configuration optimale pour XTTS-v2")  # type: ignore
        
        return stats
    
    def improve(
        self,
        output_path: Optional[str] = None,
        normalize_audio: bool = True,
        reduce_noise: bool = True,
        equalize: bool = True,
        compress_dynamics: bool = True,
        target_level: float = -16.0  # dBFS
    ) -> str:
        """
        Applique toutes les améliorations à l'audio
        
        Args:
            output_path: Chemin de sortie (auto si None)
            normalize_audio: Normaliser le volume
            reduce_noise: Réduire le bruit de fond
            equalize: Égaliser pour la voix
            compress_dynamics: Compresser la dynamique
            target_level: Niveau cible en dBFS
        
        Returns:
            Chemin du fichier amélioré
        """
        if self.audio is None:
            self.analyze()
        
        logger.info("")
        logger.info("🔧 Application des améliorations...")
        
        improved = self.audio
        
        # 1. Conversion en mono si nécessaire
        if improved.channels > 1:
            logger.info("   → Conversion en mono")
            improved = improved.set_channels(1)
        
        # 2. Réduction de bruit
        if reduce_noise and NOISE_REDUCE_AVAILABLE:
            logger.info("   → Réduction de bruit")
            improved = self._reduce_noise(improved)
        elif reduce_noise:
            logger.warning("   ⚠️  noisereduce non disponible - sautée")
        
        # 3. Égalisation pour la voix
        if equalize:
            logger.info("   → Égalisation vocale")
            improved = self._equalize_voice(improved)
        
        # 4. Compression dynamique
        if compress_dynamics:
            logger.info("   → Compression dynamique")
            improved = compress_dynamic_range(
                improved,
                threshold=-20.0,
                ratio=3.0,
                attack=5.0,
                release=50.0
            )
        
        # 5. Normalisation
        if normalize_audio:
            logger.info(f"   → Normalisation à {target_level} dBFS")
            improved = normalize(improved, headroom=abs(target_level))
        
        # 6. Conversion au sample rate optimal
        if improved.frame_rate != self.OPTIMAL_SAMPLE_RATE:
            logger.info(f"   → Conversion à {self.OPTIMAL_SAMPLE_RATE}Hz")
            improved = improved.set_frame_rate(self.OPTIMAL_SAMPLE_RATE)
        
        # Générer nom de fichier si non fourni
        output_file: Path
        if output_path is None:
            stem = self.source_path.stem
            output_file = self.source_path.parent / f"{stem}_improved.wav"
        else:
            output_file = Path(output_path)
        
        # Exporter en WAV haute qualité
        logger.info(f"   → Export vers {output_file.name}")
        improved.export(
            str(output_file),
            format="wav",
            parameters=["-acodec", "pcm_s16le"]  # 16-bit PCM
        )
        
        # Stats finales
        final_size = output_file.stat().st_size / 1024
        logger.success(f"✅ Audio amélioré: {output_file}")  # type: ignore
        logger.info(f"   Durée: {len(improved)/1000:.2f}s")
        logger.info(f"   Taille: {final_size:.1f} KB")
        logger.info(f"   Niveau: {improved.dBFS:.1f} dBFS")
        
        return str(output_file)
    
    def _reduce_noise(self, audio: Any) -> Any:
        """Réduit le bruit de fond en utilisant noisereduce"""
        if not NOISE_REDUCE_AVAILABLE or not NUMPY_AVAILABLE:
            return audio
        
        import numpy as np
        
        # Convertir en numpy array
        samples = np.array(audio.get_array_of_samples())
        
        # Normaliser pour scipy
        if audio.sample_width == 2:  # 16-bit
            samples = samples.astype(np.float32) / 32768.0
        elif audio.sample_width == 4:  # 32-bit
            samples = samples.astype(np.float32) / 2147483648.0
        
        # Appliquer réduction de bruit
        try:
            reduced = nr.reduce_noise(
                y=samples,
                sr=audio.frame_rate,
                stationary=True,
                prop_decrease=0.8,
            )
        except Exception as e:
            logger.warning(f"   ⚠️  Erreur réduction bruit: {e}")
            return audio
        
        # Reconvertir en AudioSegment
        if audio.sample_width == 2:
            reduced = (reduced * 32768.0).astype(np.int16)
        elif audio.sample_width == 4:
            reduced = (reduced * 2147483648.0).astype(np.int32)
        
        assert AudioSegment is not None
        return AudioSegment(
            data=reduced.tobytes(),
            sample_width=audio.sample_width,
            frame_rate=audio.frame_rate,
            channels=1
        )
    
    def _equalize_voice(self, audio: Any) -> Any:
        """Égalise l'audio pour améliorer la clarté vocale"""
        # Filtre passe-haut léger à 80Hz
        audio = audio.high_pass_filter(80)
        
        # Filtre passe-bas à 8000Hz
        audio = audio.low_pass_filter(8000)
        
        return audio
    
    def compare_versions(self, versions: list) -> Dict[str, Dict[str, Any]]:
        """Compare plusieurs versions du même échantillon"""
        logger.info("")
        logger.info("📊 Comparaison des versions")
        logger.info("=" * 70)
        
        results: Dict[str, Dict[str, Any]] = {}
        assert AudioSegment is not None
        
        for version_path in versions:
            if not Path(version_path).exists():
                logger.warning(f"⚠️  Fichier non trouvé: {version_path}")
                continue
            
            audio = AudioSegment.from_file(version_path)
            name = Path(version_path).name
            
            results[name] = {
                "duration": len(audio) / 1000,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "dBFS": audio.dBFS,
                "max_dBFS": audio.max_dBFS,
                "size_kb": Path(version_path).stat().st_size / 1024
            }
            
            logger.info(f"\n{name}:")
            logger.info(f"  Durée: {results[name]['duration']:.2f}s")
            logger.info(f"  Format: {results[name]['channels']}ch @ {results[name]['sample_rate']}Hz")
            logger.info(f"  Niveau: {results[name]['dBFS']:.1f} dBFS")
            logger.info(f"  Taille: {results[name]['size_kb']:.1f} KB")
        
        return results


def main() -> None:
    """Interface CLI pour l'amélioration vocale"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🎤 Améliore les échantillons vocaux HOPPER pour un clonage optimal"
    )
    parser.add_argument(
        "source",
        type=str,
        nargs="?",
        default="Hopper_voix.wav.mp3",
        help="Fichier audio source (défaut: Hopper_voix.wav.mp3)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Fichier de sortie (défaut: source_improved.wav)"
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Désactiver la normalisation"
    )
    parser.add_argument(
        "--no-denoise",
        action="store_true",
        help="Désactiver la réduction de bruit"
    )
    parser.add_argument(
        "--no-eq",
        action="store_true",
        help="Désactiver l'égalisation"
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Désactiver la compression dynamique"
    )
    parser.add_argument(
        "--target-level",
        type=float,
        default=-16.0,
        help="Niveau cible en dBFS (défaut: -16.0)"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Comparer toutes les versions Hopper_voix_*"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Analyser sans améliorer"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎤 HOPPER VOICE IMPROVEMENT TOOL")
    print("=" * 70)
    print()
    
    # Mode comparaison
    if args.compare:
        versions = list(Path(".").glob("Hopper_voix*.wav")) + list(Path(".").glob("Hopper_voix*.mp3"))
        versions_str = [str(v) for v in versions]
        
        if not versions_str:
            logger.error("❌ Aucun fichier Hopper_voix_* trouvé")
            return
        
        improver = HopperVoiceImprover(versions_str[0])
        improver.compare_versions(versions_str)
        return
    
    # Mode normal
    try:
        improver = HopperVoiceImprover(args.source)
        
        # Analyser
        stats = improver.analyze()
        
        if args.analyze_only:
            logger.info("")
            logger.info("✅ Analyse terminée (mode --analyze-only)")
            return
        
        # Améliorer
        output_path = improver.improve(
            output_path=args.output,
            normalize_audio=not args.no_normalize,
            reduce_noise=not args.no_denoise,
            equalize=not args.no_eq,
            compress_dynamics=not args.no_compress,
            target_level=args.target_level
        )
        
        print()
        print("=" * 70)
        print("✅ AMÉLIORATION TERMINÉE")
        print("=" * 70)
        print()
        print(f"📁 Fichier amélioré: {output_path}")
        print()
        print("💡 Prochaines étapes:")
        print(f"   1. Écouter: afplay '{output_path}'")
        print(f"   2. Tester avec: python test_voice_clone.py")
        print(f"   3. Comparer: python improve_hopper_voice.py --compare")
        print()
        
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        print()
        print("💡 Fichiers disponibles:")
        for f in Path(".").glob("Hopper_voix*"):
            print(f"   - {f.name}")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
