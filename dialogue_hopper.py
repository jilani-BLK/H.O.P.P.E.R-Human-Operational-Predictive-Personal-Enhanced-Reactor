#!/usr/bin/env python3
"""
Dialogue interactif avec HOPPER
HOPPER répond avec sa voix clonée
"""

import sys
from pathlib import Path
import torch
import subprocess
import time

# Ajouter le projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def setup_tts():
    """Configure le système TTS"""
    # Fix PyTorch 2.9+
    original_torch_load = torch.load
    
    def patched_torch_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    
    torch.load = patched_torch_load
    
    try:
        from TTS.api import TTS
    except ImportError:
        print("❌ TTS non installé dans venv_tts")
        return None, None
    
    # Échantillon vocal - préférer l'ultra-nettoyé
    voice_sample_ultra = project_root / "Hopper_voix_ultra_clean.wav"
    voice_sample_clean = project_root / "Hopper_voix_clean.wav"
    voice_sample_24k = project_root / "Hopper_voix_24k.wav"
    voice_sample_hq = project_root / "Hopper_voix_hq.wav"
    voice_sample_mp3 = project_root / "Hopper_voix.wav.mp3"
    
    if voice_sample_ultra.exists():
        voice_sample = voice_sample_ultra
    elif voice_sample_clean.exists():
        voice_sample = voice_sample_clean
    elif voice_sample_24k.exists():
        voice_sample = voice_sample_24k
    elif voice_sample_hq.exists():
        voice_sample = voice_sample_hq
    elif voice_sample_mp3.exists():
        voice_sample = voice_sample_mp3
    else:
        print("❌ Échantillon vocal non trouvé")
        return None, None
    
    # Charger TTS
    print("📥 Chargement du modèle vocal HOPPER...")
    device = "cpu"
    
    try:
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("✅ Modèle vocal prêt")
        return tts, voice_sample
    except Exception as e:
        print(f"❌ Erreur chargement TTS: {e}")
        return None, None


def speak_text(tts, voice_sample, text, output_file):
    """Génère et joue l'audio avec paramètres ultra-stables"""
    try:
        # Générer l'audio avec paramètres pour clarté maximale
        tts.tts_to_file(
            text=text,
            speaker_wav=str(voice_sample),
            language="fr",
            file_path=str(output_file),
            temperature=0.65,  # Stabilité maximale
            length_penalty=1.0,  
            repetition_penalty=2.5,  # Réduit pour fluidité
            top_k=30,  # Plus conservateur
            top_p=0.75,  # Cohérence accrue
            speed=0.9,  # Ralenti pour clarté
            enable_text_splitting=True,
            split_sentences=True
        )
        
        # Jouer l'audio
        subprocess.run(['afplay', str(output_file)], check=False)
        return True
        
    except Exception as e:
        print(f"❌ Erreur génération audio: {e}")
        return False


def get_hopper_response(user_input):
    """Génère une réponse HOPPER intelligente"""
    user_lower = user_input.lower()
    
    # Salutations
    if any(word in user_lower for word in ['bonjour', 'salut', 'hello', 'hey', 'coucou']):
        responses = [
            "Bonjour ! Je suis HOPPER, votre assistant personnel intelligent. Comment puis-je vous aider aujourd'hui ?",
            "Salut ! Ravi de vous retrouver. Que puis-je faire pour vous ?",
            "Bonjour ! Je suis à votre écoute. Quelle est votre demande ?"
        ]
        import random
        return random.choice(responses)
    
    # Présentation
    elif any(word in user_lower for word in ['qui es-tu', 'qui es tu', 'présente', 'c\'est quoi hopper']):
        return "Je suis HOPPER, un assistant personnel intelligent autonome. Je suis capable de comprendre et d'exécuter vos commandes, d'analyser des données, de gérer vos fichiers, et bien plus encore. Je suis constamment en train d'apprendre pour mieux vous servir."
    
    # État
    elif any(word in user_lower for word in ['comment vas-tu', 'comment va', 'ça va', 'ca va']):
        return "Je fonctionne parfaitement, merci de demander ! Tous mes systèmes sont opérationnels et je suis prêt à vous assister."
    
    # Capacités
    elif any(word in user_lower for word in ['que peux-tu faire', 'tes capacités', 'compétences', 'fonctions']):
        return "Je peux vous aider de nombreuses façons : gérer vos fichiers, effectuer des recherches, analyser des données, automatiser des tâches, et dialoguer avec vous naturellement. Mes capacités s'étendent constamment grâce à mon architecture modulaire."
    
    # Aide
    elif any(word in user_lower for word in ['aide', 'help', 'comment', 'quoi faire']):
        return "Je suis là pour vous aider ! Vous pouvez me demander de gérer des fichiers, faire des recherches, analyser des informations, ou simplement discuter. Posez-moi des questions ou donnez-moi des instructions, je ferai de mon mieux pour vous assister."
    
    # Nom JARVIS
    elif 'jarvis' in user_lower:
        return "Je m'appelle HOPPER, pas JARVIS. HOPPER signifie Human Operational Predictive Personal Enhanced Reactor. Je suis votre assistant personnel intelligent, développé spécialement pour vous."
    
    # Fichiers
    elif any(word in user_lower for word in ['fichier', 'file', 'document', 'dossier']):
        return "Je peux vous aider à gérer vos fichiers ! Je suis capable de rechercher, organiser, ouvrir et analyser vos documents. Que souhaitez-vous faire précisément ?"
    
    # Temps/Météo
    elif any(word in user_lower for word in ['météo', 'weather', 'temps qu\'il fait']):
        return "Je n'ai pas encore accès aux informations météorologiques en temps réel, mais cette fonctionnalité sera bientôt disponible dans mes prochaines mises à jour."
    
    # Heure
    elif any(word in user_lower for word in ['heure', 'quelle heure', 'time']):
        import datetime
        now = datetime.datetime.now()
        return f"Il est actuellement {now.strftime('%H heures %M')}."
    
    # Date
    elif any(word in user_lower for word in ['date', 'quel jour', 'aujourd\'hui']):
        import datetime
        now = datetime.datetime.now()
        return f"Nous sommes le {now.strftime('%d %B %Y')}."
    
    # Remerciements
    elif any(word in user_lower for word in ['merci', 'thank', 'thanks']):
        return "Avec grand plaisir ! C'est un honneur de vous assister. N'hésitez pas si vous avez besoin d'autre chose."
    
    # Blague
    elif any(word in user_lower for word in ['blague', 'joke', 'rigole', 'drôle']):
        return "Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant ? Parce que sinon ils tombent dans le bateau ! Je travaille encore sur mon sens de l'humour."
    
    # Au revoir
    elif any(word in user_lower for word in ['au revoir', 'bye', 'salut', 'ciao', 'à plus']):
        return "Au revoir ! Ce fut un plaisir de vous assister. À bientôt !"
    
    # Question sur lui-même
    elif any(word in user_lower for word in ['ton créateur', 'qui t\'a créé', 'ton développeur']):
        return "J'ai été développé par votre équipe pour être votre assistant personnel. Mon architecture est basée sur des technologies avancées d'intelligence artificielle et de traitement du langage naturel."
    
    # Voix
    elif any(word in user_lower for word in ['voix', 'voice', 'parle', 'son']):
        return "Ma voix a été clonée à partir d'un échantillon vocal en utilisant le modèle XTTS version 2 de Coqui. Je peux parler naturellement en français avec une intonation expressive."
    
    # Défaut
    else:
        return f"J'ai bien entendu votre demande concernant '{user_input}'. Je travaille constamment à améliorer ma compréhension. Pouvez-vous reformuler ou me donner plus de détails ?"


def main():
    """Dialogue principal"""
    print("=" * 70)
    print("🤖 DIALOGUE AVEC HOPPER")
    print("   Assistant Personnel Intelligent avec Voix Clonée")
    print("=" * 70)
    print()
    
    # Setup TTS
    tts, voice_sample = setup_tts()
    
    if not tts:
        print("\n⚠️  Mode texte uniquement (TTS non disponible)")
        tts_enabled = False
    else:
        tts_enabled = True
    
    print()
    print("=" * 70)
    print("💬 CONVERSATION")
    print("=" * 70)
    print()
    print("💡 Tapez 'quit', 'exit' ou 'q' pour quitter")
    print("💡 Tapez 'mute' pour désactiver la voix")
    print("💡 Tapez 'unmute' pour réactiver la voix")
    print()
    
    # Répertoire de sortie
    output_dir = project_root / "data" / "dialogue_hopper"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    conversation_count = 0
    voice_enabled = tts_enabled
    
    # Message de bienvenue
    welcome_msg = "Bonjour ! Je suis HOPPER, votre assistant personnel intelligent. Comment puis-je vous aider ?"
    print(f"🤖 HOPPER: {welcome_msg}")
    
    if voice_enabled:
        output_file = output_dir / "welcome.wav"
        print("🎙️  ", end="", flush=True)
        speak_text(tts, voice_sample, welcome_msg, output_file)
    
    print()
    
    # Boucle de conversation
    while True:
        try:
            # Demande utilisateur
            user_input = input("👤 Vous: ").strip()
            
            if not user_input:
                continue
            
            # Commandes spéciales
            if user_input.lower() in ['quit', 'exit', 'q']:
                goodbye = "Au revoir ! Ce fut un plaisir de vous assister."
                print(f"\n🤖 HOPPER: {goodbye}")
                
                if voice_enabled:
                    output_file = output_dir / "goodbye.wav"
                    print("🎙️  ", end="", flush=True)
                    speak_text(tts, voice_sample, goodbye, output_file)
                
                print("\n👋 À bientôt !\n")
                break
            
            elif user_input.lower() == 'mute':
                voice_enabled = False
                print("🔇 Voix désactivée (mode texte uniquement)\n")
                continue
            
            elif user_input.lower() == 'unmute':
                if tts_enabled:
                    voice_enabled = True
                    print("🔊 Voix réactivée\n")
                else:
                    print("⚠️  TTS non disponible\n")
                continue
            
            print()
            
            # Générer la réponse
            hopper_response = get_hopper_response(user_input)
            print(f"🤖 HOPPER: {hopper_response}")
            
            # Générer et jouer l'audio
            if voice_enabled:
                conversation_count += 1
                output_file = output_dir / f"response_{conversation_count}.wav"
                
                print("🎙️  ", end="", flush=True)
                speak_text(tts, voice_sample, hopper_response, output_file)
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir !\n")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}\n")


if __name__ == "__main__":
    main()
