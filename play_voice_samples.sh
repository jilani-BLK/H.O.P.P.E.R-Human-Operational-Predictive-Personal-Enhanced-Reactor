#!/bin/bash
# Script pour écouter et comparer les échantillons vocaux HOPPER

echo "======================================================================"
echo "🎧 ÉCOUTE DES ÉCHANTILLONS VOCAUX HOPPER"
echo "======================================================================"
echo ""

# Répertoire des fichiers
VOICE_DIR="/Users/jilani/Projet/HOPPER/data/voice_cloning"
ORIGINAL="/Users/jilani/Projet/HOPPER/Hopper_voix.wav.mp3"

echo "📂 Fichiers disponibles:"
ls -lh "$VOICE_DIR"/*.wav | awk '{print "   " $9 " (" $5 ")"}'
echo ""

# Menu interactif
while true; do
    echo "======================================================================"
    echo "Que voulez-vous écouter ?"
    echo "======================================================================"
    echo ""
    echo "  1) hopper_clone_1.wav - 'Bonjour, je suis HOPPER...'"
    echo "  2) hopper_clone_2.wav - 'Je suis capable de comprendre...'"
    echo "  3) hopper_clone_3.wav - 'Analysons ensemble...'"
    echo "  4) hopper_clone_4.wav - 'Comment puis-je vous aider...'"
    echo "  5) hopper_clone_5.wav - 'Je peux gérer vos fichiers...'"
    echo ""
    echo "  0) Échantillon ORIGINAL (Hopper_voix.wav.mp3)"
    echo "  a) Jouer TOUS les fichiers à la suite"
    echo "  q) Quitter"
    echo ""
    echo -n "Votre choix: "
    read choice
    echo ""
    
    case $choice in
        1)
            echo "▶️  Lecture de hopper_clone_1.wav..."
            afplay "$VOICE_DIR/hopper_clone_1.wav"
            echo "✅ Terminé"
            echo ""
            ;;
        2)
            echo "▶️  Lecture de hopper_clone_2.wav..."
            afplay "$VOICE_DIR/hopper_clone_2.wav"
            echo "✅ Terminé"
            echo ""
            ;;
        3)
            echo "▶️  Lecture de hopper_clone_3.wav..."
            afplay "$VOICE_DIR/hopper_clone_3.wav"
            echo "✅ Terminé"
            echo ""
            ;;
        4)
            echo "▶️  Lecture de hopper_clone_4.wav..."
            afplay "$VOICE_DIR/hopper_clone_4.wav"
            echo "✅ Terminé"
            echo ""
            ;;
        5)
            echo "▶️  Lecture de hopper_clone_5.wav..."
            afplay "$VOICE_DIR/hopper_clone_5.wav"
            echo "✅ Terminé"
            echo ""
            ;;
        0)
            echo "▶️  Lecture de l'échantillon ORIGINAL..."
            afplay "$ORIGINAL"
            echo "✅ Terminé"
            echo ""
            ;;
        a|A)
            echo "▶️  Lecture de TOUS les fichiers..."
            echo ""
            for i in 1 2 3 4 5; do
                echo "   [$i/5] hopper_clone_$i.wav"
                afplay "$VOICE_DIR/hopper_clone_$i.wav"
                sleep 0.5
            done
            echo ""
            echo "✅ Tous les fichiers ont été joués"
            echo ""
            ;;
        q|Q)
            echo "👋 Au revoir!"
            exit 0
            ;;
        *)
            echo "❌ Choix invalide. Veuillez choisir 0-5, a ou q"
            echo ""
            ;;
    esac
done
