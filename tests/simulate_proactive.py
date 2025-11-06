"""
Test de Simulation - Architecture Proactive

Simule des événements et valide le pipeline complet:
PerceptionBus → RelevanceEngine → ProactiveNarrator
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestrator"))

from core.models import PerceptionEvent  # type: ignore[import-not-found]
from core.perception_bus import PerceptionBus  # type: ignore[import-not-found]
from core.relevance_engine import RelevanceEngine  # type: ignore[import-not-found]
from core.proactive_narrator import ProactiveNarrator  # type: ignore[import-not-found]


async def simulate_proactive_pipeline():
    """
    Simule le pipeline proactif avec événements de test
    """
    
    print("🚀 Démarrage simulation pipeline proactif...\n")
    
    # 1. Initialiser composants
    perception_bus = PerceptionBus(max_queue_size=100)
    await perception_bus.start()
    print("✅ PerceptionBus démarré\n")
    
    relevance_engine = RelevanceEngine(
        llm_service_url="http://localhost:5001",
        user_preferences={
            "vip_email_senders": ["boss@company.com"],
            "vip_email_domains": ["urgent.com"]
        }
    )
    print("✅ RelevanceEngine initialisé\n")
    
    proactive_narrator = ProactiveNarrator(
        llm_service_url="http://localhost:5001",
        context_manager=None,
        tts_service_url=None  # Pas de TTS pour test
    )
    print("✅ ProactiveNarrator initialisé\n")
    
    # 2. Simuler événements de test
    test_events = [
        # Événement 1: Email VIP (devrait être annoncé)
        PerceptionEvent(
            source="email_connector",
            event_type="new_email",
            data={
                "sender": "boss@company.com",
                "subject": "Urgent: Deadline demain",
                "importance": "high"
            },
            priority=8,
            timestamp=datetime.now()
        ),
        
        # Événement 2: Menace sécurité (devrait être annoncé CRITICAL)
        PerceptionEvent(
            source="malware_detector",
            event_type="malware_detected",
            data={
                "file": "/Downloads/suspect.exe",
                "threat_level": "HIGH",
                "confidence": 0.92
            },
            priority=10,
            timestamp=datetime.now(),
            requires_immediate_response=True
        ),
        
        # Événement 3: CPU élevé (devrait être annoncé)
        PerceptionEvent(
            source="system_monitor",
            event_type="cpu_high",
            data={
                "cpu_percent": 92,
                "threshold": 80,
                "processes": [
                    {"name": "Chrome", "cpu_percent": 45},
                    {"name": "Docker", "cpu_percent": 30}
                ]
            },
            priority=7,
            timestamp=datetime.now()
        ),
        
        # Événement 4: Fichier temporaire supprimé (NE devrait PAS être annoncé)
        PerceptionEvent(
            source="filesystem_tools",
            event_type="file_deleted",
            data={
                "path": "/tmp/cache_12345.tmp"
            },
            priority=2,
            timestamp=datetime.now()
        ),
        
        # Événement 5: Email normal (cas ambigu, demande LLM)
        PerceptionEvent(
            source="email_connector",
            event_type="new_email",
            data={
                "sender": "newsletter@website.com",
                "subject": "Weekly digest",
                "importance": "normal"
            },
            priority=3,
            timestamp=datetime.now()
        )
    ]
    
    print("📋 5 événements de test créés\n")
    print("=" * 70)
    
    # 3. Traiter chaque événement
    for i, event in enumerate(test_events, 1):
        print(f"\n🔄 ÉVÉNEMENT {i}/{len(test_events)}")
        print(f"   Source: {event.source}")
        print(f"   Type: {event.event_type}")
        print(f"   Priorité: {event.priority}/10")
        print(f"   Données: {event.data}")
        print()
        
        # Publier sur le bus
        await perception_bus.publish(event)
        
        # Récupérer et traiter
        received_event = await perception_bus.get_next_event(timeout=0.1)
        
        if not received_event:
            print("   ❌ Événement non reçu du bus")
            continue
        
        # Scorer la pertinence
        print("   📊 Scoring pertinence...")
        scored_event = await relevance_engine.score_event(received_event)
        
        print(f"   → Score: {scored_event.relevance_score.value}")
        print(f"   → Valeur: {scored_event.score_value:.2f}")
        print(f"   → Raisonnement: {scored_event.reasoning}")
        print(f"   → Annonce: {'✅ OUI' if scored_event.should_announce else '❌ NON'}")
        print(f"   → Priorité: {scored_event.priority}/10")
        
        # Si doit être annoncé, générer narration
        if scored_event.should_announce:
            # Rate limiting check
            if relevance_engine.should_rate_limit(scored_event):
                print("   ⏸️  Rate-limited (déduplication)")
                continue
            
            print("\n   🎤 Génération narration...")
            narration = await proactive_narrator.narrate_event(scored_event, "test_user")
            
            print(f"   📢 Message: {narration['message']}")
            print(f"   🔊 Vocale: {'✅ OUI' if narration['should_speak'] else '❌ NON'}")
            print(f"   🎯 Urgence: {narration['urgency']}")
            print(f"   ⚠️  Confirmation: {'✅ OUI' if narration['requires_confirmation'] else '❌ NON'}")
            
            if narration.get('suggested_actions'):
                print(f"   🛠️  Actions suggérées:")
                for action in narration['suggested_actions']:
                    print(f"      - {action.get('label', action.get('action'))}")
        
        print("\n" + "-" * 70)
        
        # Pause entre événements
        await asyncio.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("✅ Simulation terminée!")
    print(f"\n📊 Statistiques PerceptionBus:")
    stats = perception_bus.get_stats()
    print(f"   - Total événements: {stats['total_events']}")
    print(f"   - Par source: {stats['events_by_source']}")
    print(f"   - Par type: {stats['events_by_type']}")
    
    # Cleanup
    await perception_bus.stop()


if __name__ == "__main__":
    """
    Lancer la simulation:
    python3 tests/simulate_proactive.py
    """
    asyncio.run(simulate_proactive_pipeline())
