"""
HOPPER - Wake Word Detection
Détecte le mot d'activation "Hopper" pour démarrer l'écoute
"""

import numpy as np
from typing import Optional, Callable
import threading
import queue
from loguru import logger

try:
    import pyaudio  # type: ignore[import-not-found]
    import webrtcvad  # type: ignore[import-not-found]
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("pyaudio ou webrtcvad non installé - Mode simulation")


class WakeWordDetector:
    """
    Détecteur de mot d'activation
    
    Utilise une approche simple basée sur:
    1. Détection d'activité vocale (VAD)
    2. Pattern matching sur "Hopper" (à améliorer avec ML)
    """
    
    def __init__(
        self,
        wake_word: str = "hopper",
        sample_rate: int = 16000,
        frame_duration: int = 30,  # ms
        sensitivity: float = 0.5,  # 0-1
    ):
        """
        Args:
            wake_word: Mot d'activation
            sample_rate: Fréquence d'échantillonnage (Hz)
            frame_duration: Durée des frames (ms)
            sensitivity: Sensibilité détection (0=moins sensible, 1=plus sensible)
        """
        self.wake_word = wake_word.lower()
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.sensitivity = sensitivity
        
        # Configuration audio
        self.chunk_size = int(sample_rate * frame_duration / 1000)
        self.audio_format = pyaudio.paInt16 if AUDIO_AVAILABLE else None  # type: ignore[possibly-unbound]
        self.channels = 1
        
        # VAD (Voice Activity Detection)
        self.vad = None
        if AUDIO_AVAILABLE:
            try:
                self.vad = webrtcvad.Vad(int(sensitivity * 3))  # type: ignore[possibly-unbound]  # 0-3
            except Exception as e:
                logger.warning(f"VAD non initialisé: {e}")
        
        # État
        self.is_listening = False
        self.callback: Optional[Callable] = None
        self.audio_queue: queue.Queue = queue.Queue()
        self.listen_thread: Optional[threading.Thread] = None
        
        logger.info(f"WakeWordDetector initialisé: '{self.wake_word}' (sensibilité: {sensitivity})")
    
    def start_listening(self, callback: Callable[[], None]):
        """
        Démarre l'écoute du wake word
        
        Args:
            callback: Fonction appelée quand wake word détecté
        """
        if not AUDIO_AVAILABLE:
            logger.warning("Audio non disponible - mode simulation")
            return
        
        if self.is_listening:
            logger.warning("Déjà en écoute")
            return
        
        self.callback = callback
        self.is_listening = True
        
        # Thread d'écoute
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        logger.info("🎤 Écoute du wake word démarrée")
    
    def stop_listening(self):
        """Arrête l'écoute"""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)
        logger.info("🎤 Écoute du wake word arrêtée")
    
    def _listen_loop(self):
        """Boucle d'écoute principale"""
        try:
            # Initialiser PyAudio
            p = pyaudio.PyAudio()  # type: ignore[possibly-unbound]
            
            # Ouvrir le stream audio
            stream = p.open(
                format=self.audio_format,  # type: ignore[arg-type]
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info(f"Stream audio ouvert: {self.sample_rate}Hz, {self.frame_duration}ms frames")
            
            voice_buffer = []
            silence_frames = 0
            max_silence_frames = 20  # ~600ms de silence
            
            while self.is_listening:
                try:
                    # Lire un chunk audio
                    audio_chunk = stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Détection d'activité vocale
                    is_speech = self._is_speech(audio_chunk)
                    
                    if is_speech:
                        voice_buffer.append(audio_chunk)
                        silence_frames = 0
                    else:
                        silence_frames += 1
                    
                    # Si on a de la voix suivie de silence, analyser
                    if len(voice_buffer) > 5 and silence_frames > max_silence_frames:
                        audio_data = b''.join(voice_buffer)
                        
                        # Vérifier si c'est le wake word
                        if self._check_wake_word(audio_data):
                            logger.success(f"✨ Wake word '{self.wake_word}' détecté!")
                            if self.callback:
                                self.callback()
                        
                        # Reset buffer
                        voice_buffer = []
                        silence_frames = 0
                    
                    # Limiter la taille du buffer
                    if len(voice_buffer) > 100:  # ~3 secondes
                        voice_buffer.pop(0)
                
                except Exception as e:
                    logger.error(f"Erreur lecture audio: {e}")
                    break
            
            # Nettoyer
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            logger.error(f"Erreur dans boucle d'écoute: {e}")
            self.is_listening = False
    
    def _is_speech(self, audio_chunk: bytes) -> bool:
        """
        Détecte si le chunk contient de la voix
        
        Args:
            audio_chunk: Données audio brutes
            
        Returns:
            True si voix détectée
        """
        if not self.vad:
            # Fallback: détection basique par énergie
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            energy = np.sum(audio_array ** 2) / len(audio_array)
            threshold = 1000000 * (1 - self.sensitivity)
            return bool(energy > threshold)
        
        try:
            return self.vad.is_speech(audio_chunk, self.sample_rate)
        except Exception as e:
            logger.debug(f"Erreur VAD: {e}")
            return False
    
    def _check_wake_word(self, audio_data: bytes) -> bool:
        """
        Vérifie si l'audio contient le wake word
        
        TODO: Implémenter avec ML (Porcupine, Snowboy, ou modèle custom)
        Pour l'instant: simulation simple
        
        Args:
            audio_data: Données audio à analyser
            
        Returns:
            True si wake word détecté
        """
        # Version simple: toujours déclencher après voix
        # À remplacer par vrai détection ML
        
        # Analyse basique d'énergie et durée
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        duration = len(audio_array) / self.sample_rate
        
        # Wake word attendu: ~0.5-1.5 secondes
        if 0.3 < duration < 2.0:
            energy = np.mean(np.abs(audio_array))
            # Seuil d'énergie adaptatif
            if energy > 500:
                logger.debug(f"Candidat wake word: durée={duration:.2f}s, énergie={energy:.0f}")
                return True
        
        return False
    
    def simulate_wake_word(self):
        """Simule la détection du wake word (pour tests)"""
        logger.info(f"🎭 Simulation wake word '{self.wake_word}'")
        if self.callback:
            self.callback()


# Mode simulation si packages non installés
if not AUDIO_AVAILABLE:
    # Mode simulation quand les bibliothèques audio ne sont pas disponibles
    class WakeWordDetectorSimulation:  # Renommé pour éviter la redéfinition
        """Version simulation"""
        def __init__(self, *args, **kwargs):
            logger.warning("WakeWordDetector en mode simulation")
        
        def start_listening(self, callback):
            logger.info("🎭 Mode simulation - utilisez simulate_wake_word()")
            self.callback = callback
        
        def stop_listening(self):
            pass
        
        def simulate_wake_word(self):
            logger.info("🎭 Simulation wake word")
            if hasattr(self, 'callback') and self.callback:
                self.callback()
    
    # Alias pour compatibilité
    WakeWordDetector = WakeWordDetectorSimulation  # type: ignore[misc]


# Exemple d'utilisation
if __name__ == "__main__":
    def on_wake_word_detected():
        print("🎉 Wake word détecté! Démarrage de l'écoute...")
    
    detector = WakeWordDetector(wake_word="hopper", sensitivity=0.7)
    
    if AUDIO_AVAILABLE:
        detector.start_listening(on_wake_word_detected)
        
        import time
        print("En écoute... Dites 'Hopper' (Ctrl+C pour arrêter)")
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            detector.stop_listening()
    else:
        print("Mode simulation - test:")
        detector.start_listening(on_wake_word_detected)
        detector.simulate_wake_word()
