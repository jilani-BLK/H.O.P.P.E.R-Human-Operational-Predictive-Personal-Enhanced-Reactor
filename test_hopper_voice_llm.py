#!/usr/bin/env python3
"""
Test d'intégration : LLM HOPPER + Clonage vocal
Permet à HOPPER de répondre avec sa voix clonée
"""

import sys
from pathlib import Path
import torch

# Ajouter le projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_hopper_voice_with_llm():
    """Test de HOPPER avec voix clonée"""
    
    print("=" * 70)
    print("🤖 TEST HOPPER : LLM + CLONAGE VOCAL")
    print("=" * 70)
    print()
    
    # Fix PyTorch 2.9+ pour TTS
    original_torch_load = torch.load
    
    def patched_torch_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    
    torch.load = patched_torch_load
    
    # Vérifier TTS
    try:
        from TTS.api import TTS
    except ImportError:
        print("❌ TTS non installé")
        print("   Utilisez: ./venv_tts/bin/pip install TTS")
        return
    
    # Vérifier l'échantillon vocal
    voice_sample_hq = project_root / "Hopper_voix_hq.wav"
    voice_sample_mp3 = project_root / "Hopper_voix.wav.mp3"
    
    if voice_sample_hq.exists():
        voice_sample = voice_sample_hq
        print(f"✅ Échantillon vocal HQ: {voice_sample.name}")
    elif voice_sample_mp3.exists():
        voice_sample = voice_sample_mp3
        print(f"✅ Échantillon vocal: {voice_sample.name}")
    else:
        print(f"❌ Échantillon vocal non trouvé")
        return
    
    print()
    
    # Charger le modèle TTS
    print("📥 Chargement du modèle XTTS-v2...")
    device = "cpu"  # CPU recommandé pour stabilité
    
    try:
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("✅ Modèle vocal chargé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    print()
    
    # Importer l'orchestrateur HOPPER
    print("📥 Chargement de l'orchestrateur HOPPER...")
    try:
        from orchestrator.main import HopperOrchestrator
        orchestrator = HopperOrchestrator()
        print("✅ Orchestrateur chargé")
    except Exception as e:
        print(f"⚠️  Chargement sans orchestrateur: {e}")
        orchestrator = None
    
    print()
    print("=" * 70)
    print("🎤 CONVERSATION AVEC HOPPER")
    print("=" * 70)
    print()
    print("💡 Tapez 'quit' ou 'exit' pour quitter")
    print()
    
    # Répertoire de sortie
    output_dir = project_root / "data" / "hopper_conversations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    conversation_count = 0
    
    while True:
        try:
            # Demande utilisateur
            user_input = input("👤 Vous: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Au revoir !")
                break
            
            print()
            
            # Obtenir la réponse de HOPPER
            if orchestrator:
                try:
                    response = orchestrator.process_query(user_input)
                    hopper_text = response.get('response', response.get('text', str(response)))
                except Exception as e:
                    print(f"⚠️  Erreur orchestrateur: {e}")
                    hopper_text = generate_simple_response(user_input)
            else:
                hopper_text = generate_simple_response(user_input)
            
            print(f"🤖 HOPPER: {hopper_text}")
            print()
            
            # Générer l'audio avec la voix clonée
            conversation_count += 1
            output_file = output_dir / f"hopper_response_{conversation_count}.wav"
            
            print("🎙️  Génération de la voix...")
            
            try:
                tts.tts_to_file(
                    text=hopper_text,
                    speaker_wav=str(voice_sample),
                    language="fr",
                    file_path=str(output_file),
                    temperature=0.65,
                    length_penalty=1.0,
                    repetition_penalty=7.0,
                    top_k=40,
                    top_p=0.8,
                    speed=1.0,
                    enable_text_splitting=True
                )
                
                print(f"✅ Audio généré: {output_file.name}")
                
                # Jouer l'audio
                import subprocess
                subprocess.run(['afplay', str(output_file)], check=False)
                
            except Exception as e:
                print(f"❌ Erreur génération audio: {e}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            print()


def generate_simple_response(user_input: str) -> str:
    """Génère une réponse simple si l'orchestrateur n'est pas disponible"""
    
    user_lower = user_input.lower()
    
    # Réponses simples basées sur des mots-clés
    if any(word in user_lower for word in ['bonjour', 'salut', 'hello', 'hey']):
        return "Bonjour ! Je suis HOPPER, votre assistant personnel. Comment puis-je vous aider ?"
    
    elif any(word in user_lower for word in ['comment', 'va', 'ça va']):
        return "Je fonctionne parfaitement, merci ! Tous mes systèmes sont opérationnels."
    
    elif any(word in user_lower for word in ['qui es-tu', 'qui es tu', 'présente']):
        return "Je suis HOPPER, un assistant personnel intelligent capable de comprendre et d'exécuter vos commandes de manière autonome."
    
    elif any(word in user_lower for word in ['aide', 'help', 'quoi faire']):
        return "Je peux vous aider à gérer vos fichiers, effectuer des recherches, analyser des données, et bien plus encore. Que souhaitez-vous faire ?"
    
    elif any(word in user_lower for word in ['merci', 'thank']):
        return "Avec plaisir ! N'hésitez pas si vous avez besoin d'autre chose."
    
    elif any(word in user_lower for word in ['météo', 'weather', 'temps']):
        return "Je n'ai pas encore accès aux informations météorologiques en temps réel, mais cette fonctionnalité sera bientôt disponible."
    
    elif any(word in user_lower for word in ['fichier', 'file', 'document']):
        return "Je peux vous aider à gérer vos fichiers. Que souhaitez-vous faire ? Rechercher, ouvrir, organiser ?"
    
    else:
        return f"J'ai bien reçu votre demande : '{user_input}'. Je suis encore en phase d'apprentissage, mais je m'améliore constamment !"


if __name__ == "__main__":
    test_hopper_voice_with_llm()
