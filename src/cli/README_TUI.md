# 🧠 HOPPER Terminal User Interface (TUI)

Interface interactive élégante dans le terminal pour communiquer avec HOPPER.

## ✨ Fonctionnalités

- **Interface en temps réel** : Conversation fluide avec HOPPER
- **Monitoring système** : Visualisation de l'état des modules
- **Statistiques live** : Mise à jour automatique toutes les 3 secondes
- **Design moderne** : Interface TUI avec Rich et Textual
- **Raccourcis clavier** : Navigation rapide

## 🎯 Aperçu

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                  🧠 HOPPER TUI Interface                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

┌─ Système ────────────────┐  ┌─ Modules Coordonnés ──────┐
│ 🧠 HOPPER Status         │  │  Module      Type    État │
│                          │  │  llm_engine  intel   ✅   │
│ État: 🟢 En ligne        │  │  self_rag    rag     ✅   │
│ Modules: 17              │  │  react_agent agent   ✅   │
│ Dernière MAJ: 14:30:15   │  │  ...                      │
└──────────────────────────┘  └───────────────────────────┘

┌─ Conversation ─────────────────────────────────────────────┐
│ 14:30:10 👤 USER: Bonjour HOPPER                          │
│ 14:30:11 🤖 HOPPER: Bonjour ! Comment puis-je vous aider?│
│ 14:30:15 👤 USER: Quel est ton statut?                   │
│ 14:30:16 🤖 HOPPER: Tous mes modules sont opérationnels  │
│                                                            │
│ ▼ Parlez à HOPPER...                     [Envoyer]       │
└────────────────────────────────────────────────────────────┘

q: Quitter | Ctrl+L: Effacer | Ctrl+R: Actualiser
```

## 📦 Installation

Les dépendances sont déjà installées :

```bash
pip install rich textual aiohttp
```

## 🚀 Lancement

### Méthode 1 : Script rapide

```bash
./scripts/start_tui.sh
```

### Méthode 2 : Manuel

```bash
# 1. Démarrer l'orchestrateur (dans un terminal)
python src/orchestrator/main.py

# 2. Lancer l'interface TUI (dans un autre terminal)
python src/cli/hopper_tui.py
```

### Méthode 3 : Avec URL personnalisée

```bash
python src/cli/hopper_tui.py --url http://localhost:5050
```

## ⌨️ Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| `Enter` | Envoyer le message |
| `q` | Quitter l'application |
| `Ctrl+C` | Quitter l'application |
| `Ctrl+L` | Effacer le journal de conversation |
| `Ctrl+R` | Actualiser le statut système |

## 🎨 Sections de l'Interface

### 1. Panneau Système (en haut à gauche)
- État de connexion à l'orchestrateur
- Nombre de modules coordonnés
- Horodatage de la dernière mise à jour

### 2. Panneau Modules (en haut à droite)
- Liste des 10 premiers modules
- Type de chaque module
- État d'activité

### 3. Journal de Conversation (en bas)
- Historique complet des échanges
- Horodatage de chaque message
- Distinction visuelle utilisateur/HOPPER

### 4. Champ de Saisie (tout en bas)
- Zone de texte pour écrire vos messages
- Bouton d'envoi

## 🔧 Configuration

### URL de l'Orchestrateur

Par défaut : `http://localhost:5050`

Pour changer :
```bash
python src/cli/hopper_tui.py --url http://votre-serveur:port
```

### Intervalle de Mise à Jour

Modifiable dans le code (`hopper_tui.py`, ligne 234) :
```python
self.set_interval(3.0, self.update_status)  # 3 secondes
```

## 🐛 Dépannage

### L'interface ne démarre pas

```bash
# Vérifier que rich et textual sont installés
pip list | grep -E "(rich|textual)"

# Réinstaller si nécessaire
pip install --force-reinstall rich textual
```

### Impossible de se connecter à l'orchestrateur

```bash
# Vérifier que l'orchestrateur tourne
curl http://localhost:5050/health

# Démarrer l'orchestrateur si nécessaire
cd src/orchestrator
python main.py
```

### Les modules ne s'affichent pas

L'endpoint `/coordination/stats` doit être disponible. Vérifiez :

```bash
curl http://localhost:5050/coordination/stats
```

## 📊 API Utilisée

L'interface TUI communique avec ces endpoints :

### GET /health
```json
{
  "status": "healthy",
  "services": {...}
}
```

### GET /coordination/stats
```json
{
  "total_modules": 17,
  "modules_by_type": {
    "intelligence": 5,
    "security": 4,
    ...
  }
}
```

### POST /process
```json
{
  "query": "votre message"
}
```

## 🎯 Exemples d'Utilisation

### Conversation Simple

```
👤 USER: Bonjour HOPPER
🤖 HOPPER: Bonjour ! Comment puis-je vous aider aujourd'hui ?

👤 USER: Quel temps fait-il ?
🤖 HOPPER: Je vérifie les informations météo pour vous...
```

### Vérification du Système

```
👤 USER: Quel est ton statut ?
🤖 HOPPER: ✅ Tous mes modules sont opérationnels :
- 🧠 Intelligence : LLM, RAG, Agents
- 🔒 Sécurité : Permissions, Malware Detector
- ⚙️ Exécution : System Executor
...
```

### Commandes Système

```
👤 USER: Liste les fichiers du dossier courant
🤖 HOPPER: Voici les fichiers :
- main.py
- coordination_hub.py
- module_registry.py
...
```

## 🌟 Avantages

✅ **Léger** : Fonctionne entièrement dans le terminal  
✅ **Rapide** : Pas de navigateur nécessaire  
✅ **Élégant** : Interface moderne avec Rich/Textual  
✅ **Temps réel** : Mise à jour automatique du statut  
✅ **Pratique** : Raccourcis clavier efficaces  

## 🔮 Futures Améliorations

- [ ] Mode sombre/clair
- [ ] Historique de conversation persistant
- [ ] Autocomplétion des commandes
- [ ] Graphique de l'activité des modules
- [ ] Notifications pour événements importants
- [ ] Support multi-utilisateurs
- [ ] Export de conversation

## 📚 Documentation

- [Rich Documentation](https://rich.readthedocs.io/)
- [Textual Documentation](https://textual.textualize.io/)
- [HOPPER Architecture](../docs/COORDINATION_SUMMARY.md)

---

**Développé avec ❤️ pour HOPPER**  
*Human Operational Predictive Personal Enhanced Reactor*
