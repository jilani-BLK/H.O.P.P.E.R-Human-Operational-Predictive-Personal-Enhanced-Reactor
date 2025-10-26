#!/usr/bin/env python3
"""
Script de test simple pour la voix de HOPPER
Teste avec le serveur TTS existant
"""

import sys
from pathlib import Path
import asyncio
import httpx

project_root = Path(__file__).parent

async def test_tts_server():
    """Test du serveur TTS de HOPPER"""
    
    print("=" * 70)
    print("🎤 TEST DU SERVEUR TTS DE HOPPER")
    print("=" * 70)
    print()
    
    # URL du serveur TTS
    tts_url = "http://localhost:5004"
    
    # Vérifier si le serveur est accessible
    print(f"📡 Vérification du serveur TTS sur {tts_url}...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{tts_url}/health")
            
            if response.status_code == 200:
                print(f"✅ Serveur TTS accessible")
                data = response.json()
                print(f"   Status: {data.get('status')}")
                print(f"   Voice: {data.get('voice', 'default')}")
            else:
                print(f"⚠️  Serveur répond avec code {response.status_code}")
    
    except httpx.ConnectError:
        print(f"❌ Serveur TTS non accessible")
        print()
        print("💡 Pour démarrer le serveur TTS:")
        print("   cd src/tts")
        print("   python server.py")
        print()
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Textes de test
    test_texts = [
        "Bonjour, je suis HOPPER, votre assistant personnel intelligent.",
        "Je suis prêt à vous aider avec vos tâches quotidiennes.",
        "Que puis-je faire pour vous aujourd'hui ?"
    ]
    
    print("\n" + "=" * 70)
    print("🗣️  GÉNÉRATION DE TESTS VOCAUX")
    print("=" * 70)
    
    output_dir = project_root / "data" / "voice_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n[{i}/{len(test_texts)}] Texte: '{text[:50]}...'")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{tts_url}/synthesize",
                    json={
                        "text": text,
                        "voice": "hopper"
                    }
                )
                
                if response.status_code == 200:
                    output_file = output_dir / f"test_{i}.wav"
                    output_file.write_bytes(response.content)
                    print(f"     ✅ Audio généré: {output_file}")
                else:
                    print(f"     ⚠️  Erreur serveur: {response.status_code}")
                    print(f"     {response.text}")
        
        except Exception as e:
            print(f"     ❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("✅ TEST TERMINÉ")
    print("=" * 70)
    print(f"\n📁 Fichiers audio dans: {output_dir}")
    print(f"\n💡 Pour écouter:")
    print(f"   open {output_dir}")
    print()
    
    return True

async def test_custom_text(text: str):
    """Test avec un texte personnalisé"""
    
    tts_url = "http://localhost:5004"
    
    print(f"🎤 Génération de: '{text}'")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Vérifier le serveur
            health = await client.get(f"{tts_url}/health")
            if health.status_code != 200:
                print(f"❌ Serveur TTS non accessible sur {tts_url}")
                print("\n💡 Démarrer le serveur: cd src/tts && python server.py")
                return
            
            print("✅ Serveur TTS accessible")
            print("🎵 Génération en cours...")
            
            # Générer
            response = await client.post(
                f"{tts_url}/synthesize",
                json={"text": text, "voice": "hopper"}
            )
            
            if response.status_code == 200:
                output_file = project_root / "data" / "voice_tests" / "custom.wav"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(response.content)
                
                print(f"✅ Audio généré: {output_file}")
                print(f"💡 Écouter: open {output_file}")
            else:
                print(f"❌ Erreur: {response.status_code}")
                print(response.text)
    
    except httpx.ConnectError:
        print(f"❌ Impossible de se connecter au serveur TTS")
        print(f"\n💡 Démarrer le serveur:")
        print(f"   cd src/tts")
        print(f"   python server.py")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def check_voice_sample():
    """Vérifie la présence de l'échantillon vocal"""
    
    voice_sample = project_root / "Hopper_voix.wav.mp3"
    
    print("🔍 Vérification de l'échantillon vocal...")
    
    if voice_sample.exists():
        size_mb = voice_sample.stat().st_size / (1024 * 1024)
        print(f"✅ Échantillon trouvé: {voice_sample}")
        print(f"   Taille: {size_mb:.2f} MB")
        return True
    else:
        print(f"⚠️  Échantillon vocal non trouvé: {voice_sample}")
        print(f"\n💡 Pour cloner la voix de HOPPER:")
        print(f"   1. Placez votre fichier audio (6-22 secondes) à:")
        print(f"      {voice_sample}")
        print(f"   2. Le serveur TTS utilisera automatiquement cet échantillon")
        return False

def main():
    """Point d'entrée principal"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Test de la voix de HOPPER")
    parser.add_argument("--text", type=str, help="Texte personnalisé à générer")
    parser.add_argument("--check", action="store_true", help="Vérifier seulement l'échantillon vocal")
    
    args = parser.parse_args()
    
    if args.check:
        check_voice_sample()
        return
    
    # Vérifier l'échantillon
    check_voice_sample()
    print()
    
    # Test
    if args.text:
        asyncio.run(test_custom_text(args.text))
    else:
        asyncio.run(test_tts_server())

if __name__ == "__main__":
    main()
