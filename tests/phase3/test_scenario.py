"""
Test du scénario complet Phase 3
Workflow: Activation → Transcription → LLM → Notifications → TTS
"""

import pytest
import requests
import time
from pathlib import Path
import io
import wave


ORCHESTRATOR_URL = "http://localhost:5050/api/v1"
STT_URL = "http://localhost:5003"
TTS_URL = "http://localhost:5004"
EMAIL_URL = "http://localhost:5008"


class TestCompleteScenario:
    """Tests du scénario complet Phase 3"""
    
    def test_00_services_health(self):
        """Vérifier que tous les services Phase 3 sont actifs"""
        services = {
            "Orchestrator": "http://localhost:5050/health",
            "Whisper STT": f"{STT_URL}/health",
            "Piper TTS": f"{TTS_URL}/health",
            "Email": f"{EMAIL_URL}/health",
        }
        
        for name, url in services.items():
            try:
                resp = requests.get(url, timeout=3)
                assert resp.status_code == 200, f"{name} not healthy"
                print(f"✅ {name}: {resp.json()}")
            except Exception as e:
                pytest.fail(f"❌ {name} unreachable: {e}")
    
    
    def test_01_phase3_stats(self):
        """Obtenir statistiques Phase 3"""
        resp = requests.get(f"{ORCHESTRATOR_URL}/phase3/stats")
        assert resp.status_code == 200
        
        stats = resp.json()
        print(f"Phase 3 Stats: {stats}")
        
        assert "voice_handler" in stats
        assert "notifications" in stats
    
    
    def test_02_text_to_speech(self):
        """Test synthèse vocale simple"""
        payload = {
            "text": "Bonjour, je suis Hopper. Bienvenue dans la phase 3.",
            "voice": "fr_FR-siwis-medium"
        }
        
        resp = requests.post(f"{ORCHESTRATOR_URL}/voice/speak", json=payload)
        assert resp.status_code == 200
        
        # Vérifier audio WAV
        assert resp.headers["content-type"] == "audio/wav"
        assert len(resp.content) > 1000
        
        print(f"✅ TTS: Generated {len(resp.content)} bytes of audio")
    
    
    @pytest.mark.skip("Nécessite fichier audio réel")
    def test_03_keyword_detection(self):
        """Test détection du mot-clé 'hopper'"""
        audio_path = Path("data/audio_samples/hopper_test.wav")
        
        if not audio_path.exists():
            pytest.skip("Fichier audio test non trouvé")
        
        with open(audio_path, "rb") as f:
            files = {"audio": ("test.wav", f, "audio/wav")}
            data = {"keyword": "hopper"}
            
            resp = requests.post(
                f"{ORCHESTRATOR_URL}/voice/detect-keyword",
                files=files,
                data=data
            )
        
        assert resp.status_code == 200
        result = resp.json()
        
        print(f"Keyword detection: {result}")
        assert result["detected"] == True
    
    
    @pytest.mark.skip("Nécessite fichier audio réel")
    def test_04_full_voice_command(self):
        """Test commande vocale complète"""
        audio_path = Path("data/audio_samples/command_test.wav")
        
        if not audio_path.exists():
            pytest.skip("Fichier audio test non trouvé")
        
        start_time = time.time()
        
        with open(audio_path, "rb") as f:
            files = {"audio": ("command.wav", f, "audio/wav")}
            data = {
                "user_id": "test_user",
                "verify_speaker": "false"
            }
            
            resp = requests.post(
                f"{ORCHESTRATOR_URL}/voice/command",
                files=files,
                data=data,
                timeout=15
            )
        
        duration = time.time() - start_time
        
        assert resp.status_code == 200
        result = resp.json()
        
        print(f"Voice command result: {result}")
        print(f"Duration: {duration:.2f}s")
        
        assert result["success"] == True
        assert "command" in result
        assert "response" in result
        assert duration < 10  # Objectif <10s
    
    
    def test_05_email_summary(self):
        """Test résumé des emails"""
        resp = requests.get(
            f"{ORCHESTRATOR_URL}/emails/summary",
            params={"limit": 5, "only_important": True}
        )
        
        assert resp.status_code == 200
        result = resp.json()
        
        print(f"Email summary: {result}")
        
        assert "count" in result
        assert "message" in result
        assert "emails" in result
        
        # Message devrait être synthétisable
        assert len(result["message"]) > 0
    
    
    def test_06_notifications_list(self):
        """Test liste des notifications"""
        resp = requests.get(
            f"{ORCHESTRATOR_URL}/notifications",
            params={"limit": 10}
        )
        
        assert resp.status_code == 200
        result = resp.json()
        
        print(f"Notifications: {result}")
        
        assert "total" in result
        assert "notifications" in result
        assert "stats" in result
    
    
    def test_07_start_notification_polling(self):
        """Démarrer le polling des notifications"""
        resp = requests.post(f"{ORCHESTRATOR_URL}/notifications/start-polling")
        assert resp.status_code == 200
        
        result = resp.json()
        print(f"Polling started: {result}")
        
        # Attendre un peu
        time.sleep(3)
        
        # Vérifier stats
        stats_resp = requests.get(f"{ORCHESTRATOR_URL}/phase3/stats")
        stats = stats_resp.json()
        
        assert stats["notifications"]["running"] == True
    
    
    def test_08_voice_health_check(self):
        """Test health check des services vocaux"""
        resp = requests.get(f"{ORCHESTRATOR_URL}/voice/health")
        assert resp.status_code == 200
        
        health = resp.json()
        print(f"Voice services health: {health}")
        
        assert "services" in health
        assert health["services"]["stt"] in ["healthy", "unreachable"]
        assert health["services"]["tts"] in ["healthy", "unreachable"]


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test du workflow complet: 'Hopper, qu'ai-je manqué aujourd'hui?'"""
    
    @pytest.mark.skip("Nécessite environnement complet et audio réel")
    def test_complete_workflow(self):
        """
        Scénario complet:
        1. User: "Hopper, qu'ai-je manqué aujourd'hui ?"
        2. Hopper détecte activation
        3. Hopper transcrit la question
        4. Hopper consulte les emails
        5. Hopper synthétise la réponse
        6. User reçoit l'audio
        """
        
        # Phase 1: Activation + Question
        audio_path = Path("data/audio_samples/hopper_question.wav")
        
        if not audio_path.exists():
            pytest.skip("Fichier audio test non trouvé")
        
        print("\n" + "="*70)
        print("🎯 Test du workflow complet Phase 3")
        print("="*70)
        
        # Étape 1: Détection activation
        print("\n1️⃣ Détection du mot-clé 'hopper'...")
        with open(audio_path, "rb") as f:
            files = {"audio": f}
            resp = requests.post(
                f"{ORCHESTRATOR_URL}/voice/listen",
                files=files,
                data={"user_id": "test_user"}
            )
        
        assert resp.status_code == 200
        result = resp.json()
        
        print(f"   Activated: {result.get('activated')}")
        print(f"   Command: {result.get('command_text')}")
        
        assert result["activated"] == True
        
        # Étape 2: Vérifier emails récents
        print("\n2️⃣ Consultation des emails...")
        email_resp = requests.get(f"{ORCHESTRATOR_URL}/emails/summary")
        emails = email_resp.json()
        
        print(f"   Emails importants: {emails['count']}")
        print(f"   Message: {emails['message'][:100]}...")
        
        # Étape 3: Synthèse vocale de la réponse
        print("\n3️⃣ Synthèse vocale de la réponse...")
        tts_resp = requests.post(
            f"{ORCHESTRATOR_URL}/voice/speak",
            json={"text": emails["message"]}
        )
        
        assert tts_resp.status_code == 200
        audio_size = len(tts_resp.content)
        print(f"   Audio généré: {audio_size} bytes")
        
        # Succès si tout s'est bien passé
        print("\n✅ Workflow complet réussi!")
        print("="*70)


def test_latency_targets():
    """Vérifier que les objectifs de latence sont atteints"""
    
    results: dict[str, float | None] = {
        "STT": None,
        "TTS": None,
        "Workflow": None
    }
    
    # Test STT latence
    print("\n🔍 Test des latences Phase 3...")
    
    # TTS latence
    print("Testing TTS...")
    start = time.time()
    resp = requests.post(
        f"{TTS_URL}/synthesize",
        json={"text": "Test de latence"}
    )
    tts_latency = time.time() - start
    results["TTS"] = tts_latency
    
    print(f"   TTS: {tts_latency:.2f}s (target: <1s)")
    assert tts_latency < 1.5, f"TTS trop lent: {tts_latency:.2f}s"
    
    # Rapport final
    print("\n📊 Résumé des latences:")
    for service, latency in results.items():
        if latency:
            status = "✅" if latency < 2 else "⚠️"
            print(f"   {status} {service}: {latency:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
