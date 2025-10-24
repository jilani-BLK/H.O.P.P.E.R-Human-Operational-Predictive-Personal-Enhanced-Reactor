# 🎙️ Guide Rapide - Utiliser HOPPER en CLI

## 📋 Prérequis

L'orchestrateur HOPPER doit être démarré :

```bash
cd /Users/jilani/Projet/HOPPER/src/orchestrator
source ../../.venv/bin/activate
python main.py
```

Vous devriez voir :
```
✅ Learning Middleware (FastAPI) initialisé
✅ HOPPER Orchestrator prêt
🚀 Uvicorn running on http://0.0.0.0:5000
```

## 🚀 Utilisation

### 1. Commande simple

```bash
cd /Users/jilani/Projet/HOPPER
./hopper "Quel temps fait-il à Paris ?"
```

**Réponse attendue**:
```
Il fait 15°C avec quelques nuages à Paris
```

### 2. Mode interactif

```bash
./hopper -i
```

**Exemple de session**:
```
╔═══════════════════════════════════════════════════════╗
║       🎙️  HOPPER - Mode Interactif                   ║
╚═══════════════════════════════════════════════════════╝

Tapez vos commandes. Commandes spéciales:
  • 'exit' ou 'quit' - Quitter
  • 'feedback N' - Donner un feedback (1-5)
  • 'help' - Afficher l'aide

🎙️  Vous: Bonjour HOPPER
🤖 HOPPER: Bonjour ! Comment puis-je vous aider ?

🎙️  Vous: Quel temps fait-il ?
🤖 HOPPER: Il fait 15°C avec quelques nuages

💭 Comment était cette interaction ?
   Tapez: feedback <1-5>

🎙️  Vous: feedback 5
✅ Feedback 5/5 enregistré

🎙️  Vous: exit
👋 Au revoir !
```

### 3. Soumettre un feedback

```bash
./hopper --feedback 5 "Excellente réponse !"
```

**Réponse**:
```
✅ Feedback 5/5 enregistré
```

### 4. Mode debug

```bash
./hopper --debug "Test de commande"
```

Affiche des informations supplémentaires (données, actions, etc.)

## 📖 Options

| Option | Description |
|--------|-------------|
| `command` | Commande à exécuter (entre guillemets) |
| `-i, --interactive` | Mode interactif |
| `-u, --user USER` | ID utilisateur (défaut: cli_user) |
| `--url URL` | URL de l'orchestrateur (défaut: http://localhost:5000) |
| `--debug` | Mode debug (plus de détails) |
| `--feedback N` | Soumettre un feedback (1-5) |
| `-h, --help` | Afficher l'aide |

## 🎯 Exemples

### Questions générales
```bash
./hopper "Quelle heure est-il ?"
./hopper "Quel jour sommes-nous ?"
./hopper "Raconte-moi une blague"
```

### Météo
```bash
./hopper "Quel temps fait-il à Paris ?"
./hopper "Quelle est la température ?"
```

### Système
```bash
./hopper "Quel est l'état de la batterie ?"
./hopper "Quelle est l'utilisation du CPU ?"
```

### Email (si configuré)
```bash
./hopper "Envoie un email à Jean"
./hopper "Lis mes derniers emails"
```

## 🔧 Dépannage

### Erreur: "Impossible de se connecter"
➡️ L'orchestrateur n'est pas démarré. Lancez-le avec :
```bash
cd src/orchestrator && python main.py
```

### Erreur: "HTTP 403"
➡️ Problème d'authentification. Pour désactiver temporairement :
- Éditez `src/orchestrator/main.py`
- Commentez la ligne : `app.middleware("http")(security_middleware)`

### Erreur: "Timeout"
➡️ HOPPER met trop de temps à répondre
- Vérifiez que les services (LLM, etc.) sont actifs
- Augmentez le timeout dans `hopper_cli.py`

### Erreur: "Module not found"
➡️ Environnement virtuel non activé
```bash
source .venv/bin/activate
```

## ✨ Fonctionnalités

✅ **Commandes en langage naturel**
✅ **Mode interactif** avec historique
✅ **Feedback** en temps réel (Phase 4)
✅ **Apprentissage** automatique
✅ **Anonymisation RGPD** des données
✅ **Multi-utilisateurs** (option --user)

## 🎓 Tips

1. **Utilisez le mode interactif** pour des conversations suivies
2. **Donnez du feedback** pour améliorer HOPPER (Phase 4 !)
3. **Mode debug** utile pour comprendre ce qui se passe
4. **Multi-utilisateurs** : utilisez `--user` pour séparer les contextes

## 🚀 Démarrage Rapide (Tout-en-un)

Terminal 1 - Démarrer l'orchestrateur :
```bash
cd /Users/jilani/Projet/HOPPER/src/orchestrator
source ../../.venv/bin/activate
python main.py
```

Terminal 2 - Utiliser HOPPER :
```bash
cd /Users/jilani/Projet/HOPPER
./hopper -i
```

C'est tout ! 🎉
