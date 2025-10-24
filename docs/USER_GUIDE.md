# 📖 HOPPER - Guide Utilisateur

> Guide complet pour utiliser HOPPER au quotidien comme assistant personnel virtuel local

---

## 🎯 Bienvenue dans HOPPER !

HOPPER (Human Operational Predictive Personal Enhanced Reactor) est votre assistant personnel virtuel **100% local** qui:
- 🎤 **Écoute** vos commandes vocales (français)
- 🧠 **Comprend** le contexte grâce à l'IA
- 🔧 **Agit** sur votre système (fichiers, applications, musique)
- 🛡️ **Protège** votre machine contre les virus
- 🗣️ **Répond** par synthèse vocale
- 🔐 **Respecte** votre vie privée (aucune donnée envoyée sur Internet)

---

## 📑 Table des Matières

1. [Installation Rapide](#installation-rapide)
2. [Premier Démarrage](#premier-démarrage)
3. [Utilisation Quotidienne](#utilisation-quotidienne)
4. [Commandes Vocales](#commandes-vocales)
5. [Gestion des Fichiers](#gestion-des-fichiers)
6. [Contrôle Système](#contrôle-système)
7. [Antivirus](#antivirus)
8. [Musique (Spotify)](#musique-spotify)
9. [Résolution de Problèmes](#résolution-de-problèmes)
10. [Conseils & Astuces](#conseils--astuces)

---

## 🚀 Installation Rapide

### Prérequis

- **macOS 11+** / Linux Ubuntu 20.04+ / Windows 10+ (WSL2)
- **Python 3.10+**
- **Docker Desktop**
- **8GB RAM minimum** (16GB recommandé)
- **20GB espace disque**

### Installation Automatique

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-repo/HOPPER.git
cd HOPPER

# 2. Lancer le script d'installation
./scripts/setup.sh
```

Le script installe automatiquement:
- ✅ ClamAV (antivirus)
- ✅ Dépendances Python
- ✅ Services Docker
- ✅ Modèles LLM/STT/TTS
- ✅ Base de données Neo4j

**Durée**: 15-30 minutes (téléchargement des modèles)

### Vérification

```bash
# Vérifier que tous les services tournent
docker-compose ps

# Résultat attendu:
# ✅ hopper-neo4j      (port 7474)
# ✅ hopper-orchestrator (port 8000)
# ✅ hopper-stt         (port 5001)
# ✅ hopper-llm         (port 5002)
# ✅ hopper-tts         (port 5003)
# ✅ hopper-spotify     (port 5006)
# ✅ hopper-antivirus   (port 5007)
```

---

## 🎬 Premier Démarrage

### 1. Activer l'environnement

```bash
source .venv/bin/activate
```

### 2. Démarrer HOPPER

```bash
python3 src/orchestrator/main.py
```

**Affichage attendu**:

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║            🤖 HOPPER - Démarrage...                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

[✓] Orchestrator démarré (port 8000)
[✓] STT Service connecté
[✓] LLM Service connecté  
[✓] TTS Service connecté
[✓] Neo4j connecté
[✓] Antivirus actif

🎤 HOPPER est prêt ! Dites "Hopper" pour commencer...
```

### 3. Première Interaction

**Vous**: "Hopper, bonjour !"  
**HOPPER**: 🎙️ _[transcription affichée]_ "Honjour, bonjour !"  
**HOPPER**: 🤖 _[réponse générée]_ "Bonjour ! Je suis HOPPER, votre assistant personnel. Comment puis-je vous aider aujourd'hui ?"  
**HOPPER**: 🔊 _[synthèse vocale]_

---

## 💬 Utilisation Quotidienne

### Conversation Naturelle

HOPPER comprend le **langage naturel français**. Parlez-lui comme à une personne :

✅ **Bon**:
- "Hopper, quelle heure est-il ?"
- "Peux-tu ouvrir Safari ?"
- "Scanne mon ordinateur pour les virus"

❌ **Pas nécessaire**:
- "HOPPER.OPEN.APP.SAFARI" (syntaxe robot)
- "Exécute la commande open -a Safari" (commande technique)

### Mot d'Activation

HOPPER écoute en continu mais répond seulement si vous dites:
- **"Hopper"** (recommandé)
- **"Hey Hopper"**
- **"OK Hopper"**

### Mode de Fonctionnement

1. **🎤 Écoute**: Détection vocale en continu
2. **📝 Transcription**: Speech-to-Text (Whisper)
3. **🧠 Compréhension**: LLM analyse l'intention
4. **⚙️ Action**: Exécution de la commande
5. **💬 Réponse**: Génération de la réponse
6. **🔊 Synthèse**: Text-to-Speech

**Latence totale**: 1-3 secondes

---

## 🎤 Commandes Vocales

### Informations Système

```
"Hopper, quelle heure est-il ?"
"Quel jour sommes-nous ?"
"Quelle est la météo ?" (simulation)
"Quel est l'état de la batterie ?"
```

### Applications

```
"Ouvre Safari"
"Lance Chrome"
"Ferme Firefox"
"Ouvre Visual Studio Code"
"Démarre Spotify"
```

### Fichiers & Dossiers

```
"Crée un fichier nommé notes.txt"
"Ouvre le dossier Documents"
"Supprime le fichier test.pdf" (confirmation requise)
"Cherche mes photos de vacances"
"Quel est le contenu de mon dossier Téléchargements ?"
```

### Musique (Spotify)

```
"Mets de la musique"
"Joue Bohemian Rhapsody"
"Pause"
"Continue"
"Piste suivante"
"Volume à 50%"
"Qu'est-ce qui joue ?"
```

### Antivirus

```
"Scanne mon ordinateur"
"Recherche les virus"
"Mets à jour l'antivirus"
"Qu'est-ce qui est en quarantaine ?"
"Supprime le virus" (après détection)
```

### Scripts & Automatisation

```
"Exécute le script backup.sh"
"Lance la sauvegarde"
"Nettoie le système"
```

---

## 📁 Gestion des Fichiers

### Recherche Intelligente

HOPPER comprend les requêtes sémantiques :

**Vous**: "Hopper, cherche mes documents Python"  
**HOPPER**: 🔍 Analyse de 190 fichiers...  
**Résultat**:
```
Trouvé 12 fichiers Python:
1. src/orchestrator/main.py (245 lignes)
2. src/services/stt/service.py (180 lignes)
3. test_antivirus.py (300 lignes)
...
```

### Création de Fichiers

**Vous**: "Créer un fichier README.md avec le contenu 'Hello World'"  
**HOPPER**: ✅ Fichier créé : `/Users/votre-nom/README.md`

### Permissions & Sécurité

Certaines actions nécessitent **confirmation** :

**Vous**: "Supprime tous mes fichiers .txt"  
**HOPPER**: ⚠️ **Confirmation requise** : Cette action va supprimer 45 fichiers. Confirmez-vous ? (oui/non)  
**Vous**: "Oui"  
**HOPPER**: ✅ 45 fichiers supprimés

**Niveaux de risque**:
- 🟢 **SAFE**: Aucune confirmation (lecture, recherche)
- 🟡 **LOW/MEDIUM**: Confirmation optionnelle (création, ouverture)
- 🔴 **HIGH/CRITICAL**: Confirmation obligatoire (suppression, exécution scripts)

---

## 🖥️ Contrôle Système

### Applications

HOPPER peut gérer toutes vos applications:

```bash
# Ouvrir
"Lance Safari"
"Ouvre Visual Studio Code"
"Démarre Docker Desktop"

# Fermer
"Ferme Chrome"
"Arrête toutes les applications"

# Vérifier
"Est-ce que Spotify est ouvert ?"
"Quelles applications sont en cours d'exécution ?"
```

### Infos Système

```bash
"Quel est le nom de ma machine ?"
"Combien de RAM ai-je ?"
"Quel est mon adresse IP locale ?"
"Quel est l'espace disque disponible ?"
```

### Scripts

```bash
# Exécuter un script
"Lance le script backup.sh"
"Exécute monitor.sh"

# Scripts disponibles:
./scripts/setup.sh      # Installation
./scripts/backup.sh     # Sauvegarde complète
./scripts/restore.sh    # Restauration
./scripts/update.sh     # Mise à jour
./scripts/monitor.sh    # Surveillance
./scripts/profile.sh    # Profiling
./scripts/test_e2e.sh   # Tests complets
```

---

## 🛡️ Antivirus

### Protection en Temps Réel

HOPPER intègre un système antivirus **3 couches** :

1. **Signature**: 10M+ signatures ClamAV
2. **Heuristique**: Détection patterns suspects
3. **Comportemental**: Analyse actions dangereuses

### Scan Manuel

```bash
# Scan rapide (zones critiques)
"Hopper, scanne rapidement mon système"

# Scan complet
"Scanne tout mon ordinateur"

# Scan d'un fichier
"Vérifie le fichier téléchargement.exe"
```

**Durée**:
- Scan rapide: 30 secondes
- Scan complet: 5-15 minutes

### Détection de Menace

**Scénario 1: Virus Détecté**

```
🛡️ HOPPER: ⚠️ MENACE DÉTECTÉE !

Fichier: /Users/vous/Downloads/virus.exe
Type: Trojan.Generic
Niveau: CRITIQUE

Actions disponibles:
1. Mettre en quarantaine (recommandé)
2. Supprimer définitivement
3. Ignorer (déconseillé)

Que voulez-vous faire ?
```

**Vous**: "Mets-le en quarantaine"  
**HOPPER**: ✅ Fichier isolé dans /var/hopper/quarantine/  
**HOPPER**: 🔒 Permissions supprimées (chmod 000)

**Scénario 2: Suppression**

**Vous**: "Supprime ce virus"  
**HOPPER**: ⚠️ **Confirmation obligatoire** : Supprimer définitivement virus.exe ?  
**Vous**: "Oui, confirme"  
**HOPPER**: ✅ Fichier écrasé 3× puis supprimé (shred)

### Gestion Quarantaine

```bash
# Voir fichiers en quarantaine
"Qu'est-ce qui est en quarantaine ?"

# Restaurer un fichier (faux positif)
"Restaure document.pdf depuis la quarantaine"

# Vider la quarantaine
"Nettoie la quarantaine"
```

### Mise à Jour

```bash
# Mise à jour signatures (recommandé: quotidien)
"Mets à jour l'antivirus"

# Vérifier version
"Quelle est la version de ClamAV ?"
```

**Signatures**: ~10M, téléchargement ~200MB, mise à jour quotidienne automatique

---

## 🎵 Musique (Spotify)

### Configuration

Par défaut, Spotify est en **mode simulation**. Pour activer la vraie intégration:

1. Créer une app Spotify: https://developer.spotify.com/dashboard
2. Ajouter les credentials:

```bash
# .env
SPOTIFY_CLIENT_ID=votre_client_id
SPOTIFY_CLIENT_SECRET=votre_secret
SPOTIFY_REDIRECT_URI=http://localhost:5006/callback
```

3. Redémarrer HOPPER

### Commandes

```bash
# Lecture
"Joue Despacito"
"Mets du jazz"
"Joue ma playlist Workout"

# Contrôle
"Pause"
"Continue"
"Piste suivante"
"Piste précédente"
"Stop"

# Volume
"Volume à 50%"
"Monte le son"
"Baisse le volume"
"Coupe le son"

# Info
"Qu'est-ce qui joue ?"
"Qui chante ?"
"Montre ma playlist"
```

---

## 🐛 Résolution de Problèmes

### HOPPER ne démarre pas

```bash
# Vérifier Docker
docker ps
# Si vide: docker-compose up -d

# Vérifier les logs
docker-compose logs -f

# Redémarrer tous les services
docker-compose down && docker-compose up -d
```

### HOPPER ne m'entend pas

```bash
# Vérifier le micro
python3 -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_device_count())"

# Tester STT directement
curl -X POST http://localhost:5001/transcribe \
  -H "Content-Type: application/json" \
  -d '{"audio": "..."}'

# Vérifier les permissions micro (macOS)
# Paramètres → Confidentialité → Micro → Terminal (cocher)
```

### Latence élevée

```bash
# Profiler les services
./scripts/profile.sh

# Optimiser (voir OPTIMIZATION_GUIDE.md)
# 1. Quantization LLM 4-bit
# 2. Modèle Whisper "base"
# 3. GPU si disponible
```

### Erreur Neo4j

```bash
# Redémarrer Neo4j
docker restart hopper-neo4j

# Vérifier connexion
curl http://localhost:7474

# Backup/Restore si corrompu
./scripts/backup.sh
./scripts/restore.sh hopper_backup_YYYYMMDD_HHMMSS
```

### Antivirus ne fonctionne pas

```bash
# Vérifier ClamAV
clamscan --version

# Mettre à jour signatures
freshclam

# Tester avec EICAR
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > /tmp/eicar.txt
curl -X POST http://localhost:5007/scan/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/tmp/eicar.txt"}'
```

---

## 💡 Conseils & Astuces

### 1. Sauvegarde Régulière

```bash
# Backup quotidien automatique
crontab -e

# Ajouter:
0 2 * * * /Users/vous/HOPPER/scripts/backup.sh
```

### 2. Optimisation Performances

```bash
# Profiler avant/après
./scripts/profile.sh

# Appliquer optimisations (voir docs/OPTIMIZATION_GUIDE.md)
# Gains: -50% RAM, -75% latence
```

### 3. Monitoring Continu

```bash
# Terminal 1: HOPPER
python3 src/orchestrator/main.py

# Terminal 2: Monitoring
./scripts/monitor.sh --live

# Terminal 3: Logs
docker-compose logs -f
```

### 4. Raccourcis Clavier (optionnel)

Créer un alias dans `.zshrc` ou `.bashrc`:

```bash
alias hopper-start='cd ~/HOPPER && source .venv/bin/activate && python3 src/orchestrator/main.py'
alias hopper-stop='docker-compose down'
alias hopper-backup='cd ~/HOPPER && ./scripts/backup.sh'
```

### 5. Personnalisation

```python
# src/orchestrator/config.py

# Changer la voix TTS
TTS_VOICE = "fr-FR-DeniseNeural"  # Voix française féminine

# Ajuster sensibilité micro
MIC_SENSITIVITY = 0.5  # 0-1

# Timeout confirmation
CONFIRMATION_TIMEOUT = 60  # secondes
```

### 6. Extensions

```bash
# Ajouter un nouveau connecteur
# Voir: docs/DEV_GUIDE.md

# Exemple: Email connector
cd src/connectors
mkdir email
touch email/connector.py email/__init__.py
```

---

## 📊 Statistiques d'Utilisation

HOPPER enregistre des statistiques (privées, locales) :

```bash
# Consulter les stats
curl http://localhost:8000/stats

# Résultat:
{
  "conversations_total": 245,
  "commandes_executees": 189,
  "virus_detectes": 3,
  "fichiers_scannes": 12580,
  "temps_uptime": "72h 15m",
  "requetes_llm": 245,
  "latence_moyenne": "0.8s"
}
```

---

## 🆘 Support

### Documentation

- **Guide Utilisateur**: `docs/USER_GUIDE.md` (ce fichier)
- **Guide Développeur**: `docs/DEV_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Optimisation**: `docs/OPTIMIZATION_GUIDE.md`
- **Antivirus**: `docs/ANTIVIRUS_ARCHITECTURE.md`

### Logs

```bash
# Logs Docker
docker-compose logs -f

# Logs Python (si mode dev)
tail -f logs/orchestrator.log

# Audit de sécurité
cat logs/security_audit.log
```

### Tests

```bash
# Tests end-to-end complets
./scripts/test_e2e.sh

# Tests antivirus
python3 test_antivirus.py

# Tests manuels
curl http://localhost:8000/health
```

---

## 🎓 Prochaines Étapes

Une fois HOPPER maîtrisé:

1. **Personnaliser** les réponses (voir `DEV_GUIDE.md`)
2. **Ajouter** des connecteurs (email, calendrier, domotique)
3. **Optimiser** les performances (`OPTIMIZATION_GUIDE.md`)
4. **Contribuer** au projet (GitHub)

---

## ⚖️ Licence & Vie Privée

- **Licence**: MIT (open source)
- **Données**: 100% locales, aucune donnée envoyée sur Internet
- **Vie privée**: Vos conversations restent sur votre machine
- **Modèles**: Llama, Whisper, CoquiTTS (open source)

---

## 📞 Contact

- **GitHub**: https://github.com/votre-repo/HOPPER
- **Issues**: https://github.com/votre-repo/HOPPER/issues
- **Email**: support@hopper-ai.local

---

**Bienvenue dans le futur de l'assistance personnelle !** 🚀

HOPPER Team - Octobre 2025
