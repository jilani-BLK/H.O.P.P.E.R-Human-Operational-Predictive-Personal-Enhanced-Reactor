# 🧠 Commande HOPPER

Commande simple et élégante pour lancer et contrôler HOPPER depuis n'importe où.

## 🚀 Installation

```bash
./scripts/install_hopper_command.sh
```

Le script propose 3 options :
1. **Lien symbolique** dans `/usr/local/bin` (recommandé)
2. **Alias** dans `~/.zshrc` ou `~/.bashrc`
3. **Les deux**

## 📋 Commandes Disponibles

### `hopper` (défaut: lance TUI)
Lance l'interface terminal interactive. Démarre automatiquement l'orchestrateur si nécessaire.

```bash
hopper
```

### `hopper tui`
Lance explicitement l'interface TUI.

```bash
hopper tui
```

### `hopper start`
Démarre uniquement l'orchestrateur en arrière-plan.

```bash
hopper start
```

### `hopper status`
Affiche le statut de HOPPER et des modules coordonnés.

```bash
hopper status
```

Exemple de sortie :
```
📊 Statut HOPPER
══════════════════════════════════════════════════

🟢 Orchestrateur: En ligne (http://localhost:5050)
📦 Modules: 17 coordonnés

   Types de modules:
   • intelligence: 5
   • security: 4
   • rag: 3
   • ...
```

### `hopper stop`
Arrête tous les processus HOPPER.

```bash
hopper stop
```

### `hopper web`
Lance l'interface web (à venir).

```bash
hopper web
```

## ⚙️ Options

### `--url`
Spécifie l'URL de l'orchestrateur (défaut: `http://localhost:5050`)

```bash
hopper tui --url http://192.168.1.100:5050
```

### `--no-banner`
N'affiche pas la bannière HOPPER au démarrage.

```bash
hopper status --no-banner
```

### `--help`
Affiche l'aide complète.

```bash
hopper --help
```

## 📖 Exemples d'Usage

### Lancement Rapide
```bash
# Juste taper 'hopper' pour tout démarrer
hopper
```

### Workflow Complet
```bash
# 1. Vérifier le statut
hopper status

# 2. Démarrer l'orchestrateur si nécessaire
hopper start

# 3. Lancer l'interface
hopper tui

# 4. Quand terminé, arrêter HOPPER
hopper stop
```

### Déploiement Distant
```bash
# Démarrer l'orchestrateur sur une machine
ssh serveur 'cd /path/to/HOPPER && hopper start'

# Connecter l'interface TUI depuis votre machine
hopper tui --url http://serveur:5050
```

## 🔧 Fonctionnement Interne

### Structure
```
hopper (commande)
  ↓
src/cli/hopper (script Python)
  ↓
  ├─ hopper start    → Lance src/orchestrator/main.py en arrière-plan
  ├─ hopper tui      → Lance src/cli/hopper_tui.py
  ├─ hopper status   → Interroge http://localhost:5050/health
  └─ hopper stop     → pkill -f orchestrator/main.py
```

### Détection Automatique

La commande détecte automatiquement :
- ✅ Si l'orchestrateur tourne déjà
- ✅ Si l'environnement virtuel existe
- ✅ La racine du projet HOPPER
- ✅ Le shell utilisé (zsh/bash)

### Démarrage Intelligent

Quand vous lancez `hopper` ou `hopper tui` :

1. Vérifie si l'orchestrateur est en ligne
2. Si non, propose de le démarrer automatiquement
3. Attend que l'orchestrateur soit prêt (10 tentatives)
4. Lance l'interface TUI

## 🎨 Personnalisation

### Couleurs

Les couleurs sont définies dans le script via les codes ANSI :
- 🟢 Vert : Succès, en ligne
- 🟡 Jaune : Avertissement, attente
- 🔴 Rouge : Erreur, hors ligne
- 🔵 Bleu : Information
- 🔷 Cyan : Titres, bannières

### Bannière

Pour désactiver la bannière par défaut :

```bash
# Dans ~/.zshrc ou ~/.bashrc
alias hopper='hopper --no-banner'
```

## 🐛 Dépannage

### Commande 'hopper' non trouvée

```bash
# Vérifier le lien symbolique
ls -la /usr/local/bin/hopper

# Réinstaller
./scripts/install_hopper_command.sh
```

### Orchestrateur ne démarre pas

```bash
# Vérifier les logs
python src/orchestrator/main.py

# Vérifier les dépendances
pip install -r requirements.txt
```

### Permission denied

```bash
# Rendre le script exécutable
chmod +x /usr/local/bin/hopper
chmod +x src/cli/hopper
```

### Port 5050 déjà utilisé

```bash
# Trouver le processus
lsof -i :5050

# Utiliser un autre port
export ORCHESTRATOR_PORT=5051
hopper start
```

## 📚 Documentation Complète

- [README TUI](./README_TUI.md) - Documentation de l'interface terminal
- [Architecture de Coordination](../../docs/COORDINATION_SUMMARY.md)
- [Guide de Démarrage Rapide](../../docs/QUICKSTART_COORDINATION.md)

## 🌟 Avantages

✅ **Une seule commande** : `hopper` pour tout  
✅ **Détection automatique** : Gestion intelligente de l'orchestrateur  
✅ **Accessible partout** : Commande globale dans le PATH  
✅ **Interface élégante** : Bannières et couleurs  
✅ **Gestion complète** : Start, stop, status, tui  

---

**🧠 Maintenant vous pouvez lancer HOPPER avec juste : `hopper` ✨**
