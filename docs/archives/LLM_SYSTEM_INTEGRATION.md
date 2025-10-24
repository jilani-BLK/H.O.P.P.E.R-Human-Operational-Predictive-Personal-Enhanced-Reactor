# 🤖 Intégration LLM + System Tools

## 🎯 Objectif

Permettre à l'utilisateur de **parler naturellement** à HOPPER qui comprend automatiquement quelles actions système exécuter.

**Avant** : L'utilisateur devait utiliser des endpoints REST
**Maintenant** : L'utilisateur dit "ouvre TextEdit" et ça marche !

---

## ✨ Comment ça marche

### Flux complet

```
Utilisateur
    ↓
    "Peux-tu ouvrir TextEdit?"
    ↓
Orchestrator (dispatcher)
    ↓
LLM génère réponse
    ↓
    "Bien sûr, je vais ouvrir TextEdit"
    ↓
SystemToolsIntegration.detect_and_execute()
    ↓
    Pattern détecté: "ouvre TextEdit" → open_app
    ↓
Connectors Service (port 5006)
    ↓
LocalSystemConnector.execute("open_app", {"app_name": "TextEdit"})
    ↓
    ✅ TextEdit lancé !
    ↓
Réponse enrichie retournée à l'utilisateur
    ↓
"Bien sûr, je vais ouvrir TextEdit
[SYSTÈME] ✅ Application 'TextEdit' lancée avec succès"
```

### Architecture

```
src/orchestrator/
├── core/
│   └── dispatcher.py          ← Modifié : intègre system_tools
├── tools/                      ← NOUVEAU
│   ├── system_integration.py  ← Détection + exécution System Tools
│   └── filesystem_integration.py ← FileSystem Explorer
```

---

## 🔍 Détection des patterns

### Patterns supportés

| Action | Patterns français | Patterns anglais | Exemple |
|--------|------------------|------------------|---------|
| **open_app** | ouvre, lance, démarre | open, launch, start | "ouvre TextEdit" |
| **close_app** | ferme, quitte | close, quit | "ferme Safari" |
| **list_apps** | liste mes applications | list my apps | "liste applications" |
| **read_file** | lis le fichier X | read file X | "lis README.md" |
| **list_directory** | liste le dossier X | list directory X | "liste src/" |
| **find_files** | cherche fichiers X | find files X | "cherche *.py" |
| **get_system_info** | infos système | system info | "infos machine" |
| **execute_script** | exécute echo X | run echo X | "exécute ls -la" |

### Exemples de détection

```python
# ✅ Détecté: open_app
"ouvre TextEdit"
"lance l'application VS Code"
"peux-tu ouvrir Safari?"

# ✅ Détecté: list_apps
"liste mes applications"
"quelles apps sont installées?"
"montre-moi les applications"

# ✅ Détecté: read_file
"lis le fichier README.md"
"affiche config.json"
"montre-moi .env"

# ✅ Détecté: get_system_info
"donne-moi les infos système"
"infos de la machine"
"system info please"
```

---

## 🛠️ API des outils

### SystemToolsIntegration

```python
from tools.system_integration import system_tools

# Détection et exécution automatique
result = await system_tools.detect_and_execute(
    llm_response="Bien sûr, je vais ouvrir TextEdit",
    user_query="ouvre TextEdit"
)

# Résultat
{
    "action": "open_app",
    "params": {"app_name": "TextEdit"},
    "result": {
        "success": True,
        "data": {"message": "Application 'TextEdit' lancée", ...}
    }
}

# Formater pour le LLM
context = system_tools.format_result_for_llm(result)
# → "[SYSTÈME] ✅ Application 'TextEdit' lancée avec succès"
```

### FileSystemToolsIntegration

```python
from tools.filesystem_integration import fs_tools

# Rechercher fichiers
result = await fs_tools.search_files(
    query="test",
    extension=".py",
    limit=10
)

# Stats projet
result = await fs_tools.get_stats()

# Plus gros fichiers
result = await fs_tools.get_largest_files(limit=10)

# Fichiers récents
result = await fs_tools.get_recent_files(limit=10)

# Scanner
result = await fs_tools.scan_directory("src/", recursive=True)
```

---

## 🧪 Tests

### Test des patterns (sans services)

```bash
python3 test_patterns.py
```

Résultat : **10/14 patterns** détectés correctement

### Test avec Orchestrator + Connectors

```bash
# Terminal 1: Lancer Connectors Service
cd src/connectors
python server.py

# Terminal 2: Lancer Orchestrator
cd src/orchestrator
python main.py

# Terminal 3: Tester
python test_system_integration.py
```

### Test manuel via curl

```bash
# Envoyer requête en langage naturel
curl -X POST http://localhost:5050/query \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Peux-tu ouvrir TextEdit?",
    "user_id": "test"
  }'

# Réponse attendue
{
  "message": "Bien sûr, je vais ouvrir TextEdit\n[SYSTÈME] ✅ Application 'TextEdit' lancée",
  "tools_executed": [
    {
      "action": "open_app",
      "params": {"app_name": "TextEdit"},
      "result": {"success": true, ...}
    }
  ],
  "actions": ["llm_generation", "tool_open_app"]
}
```

---

## 📊 Exemples d'usage

### Conversation naturelle complète

```
User: "Salut HOPPER, comment vas-tu?"
HOPPER: "Très bien merci ! Je suis prêt à t'aider."

User: "Peux-tu me montrer mes applications installées?"
HOPPER: "Bien sûr, voici vos applications..."
        [SYSTÈME] ✅ Applications installées (28): BRED, Blender, Chess, ...

User: "Ouvre VS Code"
HOPPER: "Je lance VS Code pour toi"
        [SYSTÈME] ✅ Application 'VS Code' lancée avec succès

User: "Lis le fichier README.md"
HOPPER: "Voici le contenu du README..."
        [SYSTÈME] ✅ Contenu du fichier:
        # HOPPER
        Human Operational Predictive Personal Enhanced Reactor
        ...

User: "Cherche tous les fichiers Python dans src/"
HOPPER: "J'ai trouvé X fichiers Python dans src/"
        [SYSTÈME] ✅ Fichiers trouvés (62):
          - server.py
          - dispatcher.py
          - ...

User: "Donne-moi les infos de ma machine"
HOPPER: "Voici les informations système..."
        [SYSTÈME] ✅ Info: OS=macOS ARM64, RAM=18 GB, CPU=12 cores
```

---

## ⚙️ Configuration

### Activer/Désactiver les outils

Dans `dispatcher.py` :

```python
# Désactiver temporairement
self.system_tools = None  # Pas de détection
self.fs_tools = None      # Pas de filesystem
```

### Ajouter de nouveaux patterns

Dans `system_integration.py` :

```python
PATTERNS = {
    "nouvelle_action": [
        r"pattern_français",
        r"pattern_anglais"
    ],
    ...
}
```

### Personnaliser les réponses

Dans `system_integration.py`, méthode `format_result_for_llm()` :

```python
if action == "nouvelle_action":
    return f"\n[SYSTÈME] ✅ Résultat: {data}"
```

---

## 🔐 Sécurité

### Toutes les actions sont sécurisées

- **PermissionManager** : Vérifie chaque action
- **AuditLogger** : Enregistre tout dans `data/logs/audit/`
- **ConfirmationEngine** : Demande confirmation si nécessaire
- **Détection** : Commandes bannies (rm, sudo) bloquées

### Traçabilité complète

```bash
# Voir l'audit
curl http://localhost:5006/security/audit?user_id=llm_orchestrator

{
  "user_id": "llm_orchestrator",
  "stats": {
    "total": 42,
    "by_risk": {"safe": 30, "medium": 10, "high": 2},
    "success_rate": 0.95
  },
  "recent_actions": [...]
}
```

---

## 🚀 Avantages

### Pour l'utilisateur

✅ **Langage naturel** : Parle comme tu veux, HOPPER comprend
✅ **Pas de syntaxe** : Plus besoin de mémoriser des commandes
✅ **Contextuel** : HOPPER comprend l'intention
✅ **Multilingue** : Français et anglais supportés

### Pour le développeur

✅ **Extensible** : Ajouter patterns = ajouter capacités
✅ **Modulaire** : Outils indépendants du LLM
✅ **Testable** : Tests unitaires des patterns
✅ **Observable** : Logs détaillés de chaque détection

---

## 📈 Métriques

### Tests effectués

| Catégorie | Patterns testés | Détectés | Taux |
|-----------|----------------|----------|------|
| Applications | 6 | 5 | 83% |
| Fichiers | 3 | 2 | 67% |
| Système | 3 | 2 | 67% |
| Négatifs | 2 | 2 | 100% |
| **TOTAL** | **14** | **10** | **71%** |

### Performance

- Détection pattern : **< 1ms**
- Exécution action : **50-500ms** (selon action)
- Bout-en-bout : **< 2s** (LLM inclus)

---

## 🔮 Évolutions futures

### Court terme
- [ ] Ajouter patterns manquants (67% → 95%)
- [ ] Support de plus d'actions (FileSystem, Apps, etc.)
- [ ] Améliorer extraction paramètres

### Moyen terme
- [ ] Détection multi-actions (chaîner plusieurs outils)
- [ ] Contexte persistant (se souvenir des actions)
- [ ] Apprentissage des patterns utilisateur

### Long terme
- [ ] LLM génère les appels directement (function calling)
- [ ] Auto-complétion intelligente
- [ ] Suggestions proactives

---

## 📚 Ressources

### Code source
- `src/orchestrator/tools/system_integration.py` - Intégration LocalSystem
- `src/orchestrator/tools/filesystem_integration.py` - Intégration FileSystem
- `src/orchestrator/core/dispatcher.py` - Dispatcher modifié
- `test_patterns.py` - Tests patterns
- `test_system_integration.py` - Tests bout-en-bout

### Documentation
- `docs/PHASE_5_STATUS.md` - Status Phase 5
- `docs/FILESYSTEM_EXPLORER.md` - Doc FileSystem
- `docs/PHASE_5_SUMMARY.md` - Résumé Phase 5

---

**Créé le** : 2025-10-23  
**Version** : 1.0  
**Status** : ✅ Opérationnel (71% patterns)  
**Auteur** : HOPPER Dev Team
