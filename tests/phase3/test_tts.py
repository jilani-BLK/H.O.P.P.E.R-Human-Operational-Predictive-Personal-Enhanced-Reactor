"""
Tests pour le service TTS (Piper)
"""

import pytest
import requests
import wave
import io


BASE_URL = "http://localhost:5004"


def test_piper_health():
    """Test health check du service Piper"""
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["status"] == "healthy"
    assert "voice" in data


def test_synthesize_simple():
    """Test synthèse simple"""
    payload = {
        "text": "Bonjour, je suis Hopper.",
        "voice": "fr_FR-siwis-medium"
    }
    
    resp = requests.post(f"{BASE_URL}/synthesize", json=payload)
    assert resp.status_code == 200
    
    # Vérifier que c'est bien de l'audio
    audio_data = resp.content
    assert len(audio_data) > 0
    
    # Devrait commencer par header WAV
    assert audio_data[:4] == b"RIFF"


def test_synthesize_long_text():
    """Test synthèse texte long"""
    text = "Ceci est un test de synthèse vocale avec un texte relativement long. " * 3
    
    payload = {"text": text}
    resp = requests.post(f"{BASE_URL}/synthesize", json=payload)
    
    assert resp.status_code == 200
    assert len(resp.content) > 10000  # Audio assez long


def test_synthesize_empty_text():
    """Test synthèse texte vide"""
    payload = {"text": ""}
    resp = requests.post(f"{BASE_URL}/synthesize", json=payload)
    
    # Devrait gérer gracieusement
    assert resp.status_code in [400, 422, 200]


def test_synthesize_special_characters():
    """Test synthèse avec caractères spéciaux"""
    payload = {
        "text": "Email de jean-pierre@example.com : 42% de réduction !"
    }
    
    resp = requests.post(f"{BASE_URL}/synthesize", json=payload)
    assert resp.status_code == 200


def test_synthesize_numbers():
    """Test synthèse avec nombres"""
    payload = {
        "text": "Il est 14 heures 30. Température : 23 degrés."
    }
    
    resp = requests.post(f"{BASE_URL}/synthesize", json=payload)
    assert resp.status_code == 200


def test_audio_format():
    """Test format audio WAV"""
    payload = {"text": "Test format audio"}
    resp = requests.post(f"{BASE_URL}/synthesize", json=payload)
    
    assert resp.status_code == 200
    
    # Vérifier structure WAV
    audio_bytes = io.BytesIO(resp.content)
    
    try:
        with wave.open(audio_bytes, 'rb') as wav:
            assert wav.getnchannels() == 1  # Mono
            assert wav.getsampwidth() == 2  # 16-bit
            assert wav.getframerate() == 22050  # Sample rate Piper
    except wave.Error:
        pytest.fail("Audio n'est pas un fichier WAV valide")


def test_synthesize_latency():
    """Test latence de synthèse"""
    import time
    
    payload = {"text": "Test de latence"}
    
    start = time.time()
    resp = requests.post(f"{BASE_URL}/synthesize", json=payload, timeout=5)
    duration = time.time() - start
    
    assert resp.status_code == 200
    assert duration < 1.0  # Objectif <1s


@pytest.mark.parametrize("text", [
    "Bonjour",
    "Comment allez-vous ?",
    "Voici vos emails importants.",
    "Email de Marie : Réunion à 15h.",
    "Vous avez 3 nouveaux messages."
])
def test_synthesize_various_texts(text):
    """Test synthèse avec différents textes"""
    payload = {"text": text}
    resp = requests.post(f"{BASE_URL}/synthesize", json=payload)
    
    assert resp.status_code == 200
    assert len(resp.content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
