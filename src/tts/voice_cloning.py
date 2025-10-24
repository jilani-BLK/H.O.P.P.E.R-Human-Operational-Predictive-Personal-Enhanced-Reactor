"""
HOPPER - Voice Cloning Module
Clone la voix unique de HOPPER depuis un échantillon audio
Utilise Coqui TTS XTTS-v2 pour le clonage vocal
"""

from pathlib import Path
from typing import Optional
import torch
from loguru import logger
import numpy as np
from pydub import AudioSegment
import tempfile
import os

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("⚠️ TTS non installé - pip install TTS")


class HopperVoiceCloner:
    """
    Clonage de la voix unique de HOPPER
    
    Utilise XTTS-v2 qui nécessite seulement 6-22 secondes d'audio
    pour cloner une voix avec haute fidélité
    """
    
    def __init__(
        self,
        voice_sample_path: str = "Hopper_voix.wav.mp3",
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        device: str = "auto"
    ):
        """
        Args:
            voice_sample_path: Chemin vers l'échantillon vocal (22 sec)
            model_name: Modèle Coqui TTS à utiliser
            device: Device PyTorch ('cpu', 'cuda', 'mps', 'auto')
        """
        self.voice_sample_path = Path(voice_sample_path)
        self.model_name = model_name
        
        # Détection automatique du device
        if device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"  # Apple Silicon
            else:
                self.device = "cpu"
        else:
            self.device = device
        
        self.tts = None
        self.speaker_wav = None
        
        logger.info(f"🎤 HopperVoiceCloner initialisé (device: {self.device})")
    
    def load_model(self):
        """Charge le modèle TTS XTTS-v2"""
        if not TTS_AVAILABLE:
            raise ImportError("TTS non installé. Exécutez: pip install TTS")
        
        logger.info(f"📥 Chargement du modèle {self.model_name}...")
        self.tts = TTS(self.model_name).to(self.device)
        logger.success("✅ Modèle TTS chargé")
    
    def prepare_voice_sample(self) -> str:
        """
        Prépare l'échantillon vocal pour le clonage
        Convertit en WAV si nécessaire
        
        Returns:
            Chemin vers le fichier WAV préparé
        """
        if not self.voice_sample_path.exists():
            raise FileNotFoundError(f"Échantillon vocal non trouvé: {self.voice_sample_path}")
        
        logger.info(f"🔧 Préparation de l'échantillon: {self.voice_sample_path}")
        
        # Si déjà WAV, utiliser directement
        if self.voice_sample_path.suffix.lower() == ".wav":
            self.speaker_wav = str(self.voice_sample_path)
            logger.success("✅ Échantillon WAV prêt")
            return self.speaker_wav
        
        # Sinon, convertir en WAV
        try:
            audio = AudioSegment.from_file(str(self.voice_sample_path))
            
            # Normaliser l'audio pour le clonage
            # XTTS préfère: mono, 22050 Hz
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(22050)  # 22.05 kHz
            
            # Sauvegarder temporairement en WAV
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_wav.close()
            
            audio.export(temp_wav.name, format="wav")
            self.speaker_wav = temp_wav.name
            
            logger.success(f"✅ Échantillon converti en WAV: {len(audio)/1000:.1f}s")
            return self.speaker_wav
            
        except Exception as e:
            raise RuntimeError(f"Erreur conversion audio: {e}")
    
    def clone_voice(
        self,
        text: str,
        output_path: Optional[str] = None,
        language: str = "fr"
    ) -> str:
        """
        Clone la voix de HOPPER et génère l'audio
        
        Args:
            text: Texte à synthétiser avec la voix clonée
            output_path: Chemin de sortie (auto si None)
            language: Langue ('fr', 'en', 'es', etc.)
        
        Returns:
            Chemin vers le fichier audio généré
        """
        if self.tts is None:
            self.load_model()
        
        if self.speaker_wav is None:
            self.prepare_voice_sample()
        
        # Générer nom de fichier si non fourni
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav",
                prefix="hopper_voice_"
            ).name
        
        logger.info(f"🗣️ Génération avec la voix de HOPPER...")
        logger.info(f"   Texte: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        try:
            # Synthèse avec clonage vocal
            self.tts.tts_to_file(
                text=text,
                speaker_wav=self.speaker_wav,
                language=language,
                file_path=output_path
            )
            
            file_size = os.path.getsize(output_path)
            logger.success(f"✅ Audio généré: {output_path} ({file_size/1024:.1f} KB)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Erreur génération: {e}")
            raise
    
    def analyze_voice_sample(self) -> dict:
        """
        Analyse l'échantillon vocal
        
        Returns:
            Métadonnées de l'échantillon
        """
        if not self.voice_sample_path.exists():
            raise FileNotFoundError(f"Échantillon non trouvé: {self.voice_sample_path}")
        
        audio = AudioSegment.from_file(str(self.voice_sample_path))
        
        info = {
            "duration": len(audio) / 1000,  # secondes
            "channels": audio.channels,
            "sample_rate": audio.frame_rate,
            "sample_width": audio.sample_width,
            "file_size": self.voice_sample_path.stat().st_size,
            "format": self.voice_sample_path.suffix,
        }
        
        logger.info(f"📊 Analyse échantillon vocal:")
        logger.info(f"   Durée: {info['duration']:.1f}s")
        logger.info(f"   Format: {info['channels']}ch @ {info['sample_rate']}Hz")
        logger.info(f"   Taille: {info['file_size']/1024:.1f} KB")
        
        return info
    
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        if self.speaker_wav and self.speaker_wav != str(self.voice_sample_path):
            if os.path.exists(self.speaker_wav):
                os.remove(self.speaker_wav)
                logger.info("🧹 Fichiers temporaires nettoyés")


# Fonction helper pour usage simple
def clone_hopper_voice(
    text: str,
    output_path: Optional[str] = None,
    voice_sample: str = "Hopper_voix.wav.mp3"
) -> str:
    """
    Fonction simple pour cloner la voix de HOPPER
    
    Usage:
        audio_file = clone_hopper_voice("Bonjour, je suis HOPPER!")
        
    Args:
        text: Texte à dire
        output_path: Fichier de sortie (optionnel)
        voice_sample: Échantillon vocal de référence
    
    Returns:
        Chemin vers l'audio généré
    """
    cloner = HopperVoiceCloner(voice_sample)
    try:
        return cloner.clone_voice(text, output_path)
    finally:
        cloner.cleanup()


# Tests et démo
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🎤 HOPPER Voice Cloning - Demo")
    print("=" * 60)
    
    # Vérifier l'échantillon
    cloner = HopperVoiceCloner()
    
    try:
        # Analyser l'échantillon
        print("\n[1] Analyse de l'échantillon vocal...")
        info = cloner.analyze_voice_sample()
        
        if info['duration'] < 6:
            print(f"⚠️ Durée courte ({info['duration']:.1f}s) - Minimum recommandé: 6s")
        elif info['duration'] > 30:
            print(f"ℹ️ Durée longue ({info['duration']:.1f}s) - 10-22s est optimal")
        else:
            print(f"✅ Durée optimale: {info['duration']:.1f}s")
        
        # Test de clonage
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])
        else:
            text = (
                "Bonjour, je suis HOPPER, votre assistant personnel intelligent. "
                "Je suis là pour vous aider au quotidien avec vos tâches, "
                "vos questions et vos besoins."
            )
        
        print(f"\n[2] Test de clonage vocal...")
        print(f"   Texte: {text}")
        
        output = cloner.clone_voice(text, output_path="hopper_test_voice.wav")
        
        print(f"\n✅ Succès! Audio généré: {output}")
        print(f"\n💡 Écouter avec: afplay {output}  # macOS")
        print(f"💡 Ou ouvrir le fichier dans votre lecteur audio")
        
    except FileNotFoundError:
        print("\n❌ Erreur: Fichier Hopper_voix.wav.mp3 non trouvé")
        print("   Placez votre échantillon vocal (22 sec) dans le dossier racine")
        print("   Format supporté: WAV, MP3, M4A, etc.")
        
    except ImportError:
        print("\n❌ Erreur: TTS non installé")
        print("   Installation: pip install TTS pydub")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cloner.cleanup()
