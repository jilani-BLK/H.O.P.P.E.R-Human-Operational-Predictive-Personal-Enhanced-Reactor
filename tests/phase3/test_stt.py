"""
Tests pour le service STT (Whisper)
"""

import pytest
import requests
from pathlib import Path
import wave
import numpy as np


BASE_URL = "http://localhost:5003"


@pytest.fixture
def audio_sample():
    """Créer un échantillon audio pour tests"""
    # Audio 1 seconde, 16kHz, mono
    sample_rate = 16000
    duration = 1
    frequency = 440  # La (A4)
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convertir en int16
    audio_data = (audio_data * 32767).astype(np.int16)
    
    return audio_data.tobytes()


def test_whisper_health():
    """Test health check du service Whisper"""
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["status"] == "healthy"
    assert "model" in data


def test_whisper_stats():
    """Test statistiques du modèle"""
    resp = requests.get(f"{BASE_URL}/stats")
    assert resp.status_code == 200
    
    data = resp.json()
    assert "model" in data
    assert "device" in data
    assert "compute_type" in data
    assert data["status"] == "ready"


def test_transcribe_silence(audio_sample):
    """Test transcription audio silencieux"""
    files = {"audio": ("test.wav", audio_sample, "audio/wav")}
    resp = requests.post(f"{BASE_URL}/transcribe", files=files)
    
    assert resp.status_code == 200
    data = resp.json()
    
    assert "text" in data
    assert "language" in data
    # Audio synthétique → peu de texte attendu
    assert len(data["text"]) < 100


def test_transcribe_with_language(audio_sample):
    """Test transcription avec langue spécifiée"""
    files = {"audio": ("test.wav", audio_sample, "audio/wav")}
    data = {"language": "fr"}
    
    resp = requests.post(f"{BASE_URL}/transcribe", files=files, data=data)
    assert resp.status_code == 200
    
    result = resp.json()
    assert result["language"] == "fr"


def test_detect_keyword_no_match(audio_sample):
    """Test détection mot-clé (pas de match)"""
    files = {"audio": ("test.wav", audio_sample, "audio/wav")}
    data = {"keyword": "hopper"}
    
    resp = requests.post(f"{BASE_URL}/detect-keyword", files=files, data=data)
    assert resp.status_code == 200
    
    result = resp.json()
    assert "detected" in result
    # Audio synthétique → pas de mot-clé
    assert result["detected"] == False


def test_transcribe_invalid_audio():
    """Test avec audio invalide"""
    files = {"audio": ("test.wav", b"invalid audio data", "audio/wav")}
    resp = requests.post(f"{BASE_URL}/transcribe", files=files)
    
    # Devrait gérer l'erreur gracieusement
    assert resp.status_code in [400, 422, 500]


@pytest.mark.skip("Nécessite fichier audio réel")
def test_transcribe_real_audio():
    """Test transcription avec fichier audio réel"""
    audio_path = Path("data/audio_samples/test_fr.wav")
    
    if not audio_path.exists():
        pytest.skip("Fichier audio non trouvé")
    
    with open(audio_path, "rb") as f:
        files = {"audio": ("test.wav", f, "audio/wav")}
        resp = requests.post(f"{BASE_URL}/transcribe", files=files)
    
    assert resp.status_code == 200
    data = resp.json()
    
    assert len(data["text"]) > 0
    print(f"Transcription: {data['text']}")


@pytest.mark.skip("Nécessite audio avec 'hopper'")
def test_detect_keyword_real():
    """Test détection avec vrai audio contenant 'hopper'"""
    audio_path = Path("data/audio_samples/hopper_activation.wav")
    
    if not audio_path.exists():
        pytest.skip("Fichier audio non trouvé")
    
    with open(audio_path, "rb") as f:
        files = {"audio": ("test.wav", f, "audio/wav")}
        data = {"keyword": "hopper"}
        resp = requests.post(f"{BASE_URL}/detect-keyword", files=files, data=data)
    
    assert resp.status_code == 200
    result = resp.json()
    
    assert result["detected"] == True
    assert "hopper" in result["transcribed_text"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
