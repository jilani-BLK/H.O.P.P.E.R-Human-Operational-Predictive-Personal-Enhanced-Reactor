"""
Test fixtures pour mocker les serveurs HTTP externes
Permet d'exécuter les tests Phase 2 sans serveurs réels
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

# Import conditionnel de responses (installé via requirements.txt)
try:
    import responses
    HAS_RESPONSES = True
except ImportError:
    HAS_RESPONSES = False
    responses = None  # type: ignore


@pytest.fixture
def mock_http_server():
    """Mock générique pour serveur HTTP"""
    if not HAS_RESPONSES:
        pytest.skip("responses library not installed")
    
    with responses.RequestsMock() as rsps:  # type: ignore
        # Mock endpoints courants
        rsps.add(
            responses.GET,  # type: ignore
            "http://localhost:5001/health",
            json={"status": "healthy"},
            status=200
        )
        rsps.add(
            responses.GET,  # type: ignore
            "http://localhost:5003/health",
            json={"status": "healthy"},
            status=200
        )
        rsps.add(
            responses.GET,  # type: ignore
            "http://localhost:5004/health",
            json={"status": "healthy"},
            status=200
        )
        yield rsps


@pytest.fixture
def mock_llm_service():
    """Mock service LLM"""
    if not HAS_RESPONSES:
        pytest.skip("responses library not installed")
    
    with responses.RequestsMock() as rsps:  # type: ignore
        rsps.add(
            responses.POST,  # type: ignore
            "http://localhost:5001/generate",
            json={
                "text": "Réponse mockée du LLM",
                "tokens": 10
            },
            status=200
        )
        yield rsps


@pytest.fixture
def mock_stt_service():
    """Mock service STT (Speech-to-Text)"""
    if not HAS_RESPONSES:
        pytest.skip("responses library not installed")
    
    with responses.RequestsMock() as rsps:  # type: ignore
        rsps.add(
            responses.POST,  # type: ignore
            "http://localhost:5003/transcribe",
            json={
                "text": "transcription mockée",
                "language": "fr",
                "confidence": 0.95
            },
            status=200
        )
        yield rsps


@pytest.fixture
def mock_tts_service():
    """Mock service TTS (Text-to-Speech)"""
    if not HAS_RESPONSES:
        pytest.skip("responses library not installed")
    
    with responses.RequestsMock() as rsps:  # type: ignore
        rsps.add(
            responses.POST,  # type: ignore
            "http://localhost:5004/synthesize",
            body=b"fake audio data",
            content_type="audio/wav",
            status=200
        )
        yield rsps


@pytest.fixture
def mock_all_services(mock_http_server, mock_llm_service, mock_stt_service, mock_tts_service):
    """Mock tous les services à la fois"""
    return {
        "http": mock_http_server,
        "llm": mock_llm_service,
        "stt": mock_stt_service,
        "tts": mock_tts_service
    }


@pytest.fixture
def skip_if_server_not_running():
    """Skip test si serveurs HTTP ne sont pas disponibles"""
    import requests
    
    def _check_server(url: str) -> bool:
        try:
            resp = requests.get(url, timeout=2)
            return resp.status_code == 200
        except Exception:
            return False
    
    def _decorator(func):
        """Décorateur pour skip"""
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not _check_server("http://localhost:5001/health"):
                pytest.skip("Serveur HTTP non disponible (utiliser mocks)")
            return func(*args, **kwargs)
        
        return wrapper
    
    return _decorator


# Configuration pytest pour auto-skip
def pytest_configure(config):
    """Configuration globale pytest"""
    config.addinivalue_line(
        "markers",
        "requires_http: mark test as requiring HTTP server (skip if not available)"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests nécessitant serveur HTTP"""
    import requests
    
    # Vérifier si serveurs disponibles
    servers_available = False
    try:
        resp = requests.get("http://localhost:5001/health", timeout=2)
        servers_available = (resp.status_code == 200)
    except Exception:
        pass
    
    if not servers_available:
        skip_http = pytest.mark.skip(reason="HTTP servers not available (use mocks or start servers)")
        for item in items:
            if "requires_http" in item.keywords:
                item.add_marker(skip_http)


# Helpers pour tests
class MockResponse:
    """Mock response HTTP"""
    def __init__(self, json_data=None, status_code=200, text=""):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def mock_requests_get(url, *args, **kwargs):
    """Mock global pour requests.get"""
    if "health" in url:
        return MockResponse({"status": "healthy"}, 200)
    elif "5001" in url:
        return MockResponse({"text": "Mock LLM response"}, 200)
    return MockResponse({}, 404)


def mock_requests_post(url, *args, **kwargs):
    """Mock global pour requests.post"""
    if "generate" in url:
        return MockResponse({"text": "Generated text", "tokens": 10}, 200)
    elif "transcribe" in url:
        return MockResponse({"text": "transcribed", "confidence": 0.9}, 200)
    elif "synthesize" in url:
        resp = MockResponse()
        resp.text = "audio data"
        return resp
    return MockResponse({}, 404)


@pytest.fixture(autouse=True)
def auto_mock_http_if_unavailable(monkeypatch):
    """
    Auto-mock HTTP requests si serveurs non disponibles
    autouse=True l'applique à TOUS les tests automatiquement
    """
    import requests
    
    # Vérifier si serveurs disponibles
    try:
        resp = requests.get("http://localhost:5001/health", timeout=1)
        servers_available = (resp.status_code == 200)
    except Exception:
        servers_available = False
    
    # Si serveurs pas disponibles, mock automatiquement
    if not servers_available:
        monkeypatch.setattr("requests.get", mock_requests_get)
        monkeypatch.setattr("requests.post", mock_requests_post)
