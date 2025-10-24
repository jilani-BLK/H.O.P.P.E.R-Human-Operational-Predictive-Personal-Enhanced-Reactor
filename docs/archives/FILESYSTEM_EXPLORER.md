# FileSystem Explorer - Documentation

## 🎯 Vue d'ensemble

Le **FileSystem Explorer** permet à HOPPER de scanner, indexer et comprendre complètement le système de fichiers de votre machine.

## ✨ Fonctionnalités

### 1. Scan Récursif Intelligent
- Exploration complète avec profondeur configurable (max 10 niveaux)
- Exclusion automatique des répertoires build/cache (.git, node_modules, __pycache__, .venv)
- Ignore fichiers temporaires (.pyc, .log, .DS_Store)
- Limite de taille configurable (100MB par défaut)

### 2. Métadonnées Complètes
Pour chaque fichier :
- Nom, chemin complet, extension
- Taille (bytes)
- Type MIME
- Dates de création et modification
- Permissions (format octal)
- État caché (fichiers commençant par .)

### 3. Catégorisation Automatique
Fichiers classés par type :
- **code**: .py, .js, .ts, .java, .c, .cpp, .go, .rs, etc.
- **config**: .json, .yaml, .toml, .ini, .env
- **docs**: .md, .txt, .pdf, .doc
- **data**: .csv, .xml, .sql, .db
- **web**: .html, .css, .scss
- **image**: .jpg, .png, .svg, .webp
- **audio**: .mp3, .wav, .flac
- **video**: .mp4, .avi, .mkv
- **archive**: .zip, .tar, .gz
- **binary**: .exe, .dll, .so, .dylib

### 4. Recherche Multi-critères
- Par nom de fichier (recherche partielle)
- Par extension (.py, .js, etc.)
- Par catégorie (code, docs, etc.)
- Par taille (min/max)
- Par date de modification
- Limite de résultats configurable

### 5. Statistiques Détaillées
- Total fichiers/répertoires
- Taille totale
- Répartition par catégorie (count, taille, extensions)
- Top fichiers les plus gros
- Fichiers récemment modifiés

### 6. Cache Persistant
- Index sauvegardé en JSON : `data/filesystem/index.json`
- Chargement automatique au démarrage
- Évite rescans inutiles
- Mise à jour incrémentale

## 📦 Installation

Le module est déjà installé dans HOPPER :

```bash
# Aucune dépendance supplémentaire requise
# Utilise uniquement: pathlib, mimetypes (stdlib)
```

## 🚀 Utilisation

### CLI (Ligne de commande)

#### Scanner un répertoire

```bash
# Scan simple (non récursif)
./fs_explorer.py scan /path/to/dir

# Scan récursif
./fs_explorer.py scan /path/to/dir --recursive

# Mettre à jour fichiers existants
./fs_explorer.py scan /path/to/dir --recursive --update

# Mode verbeux (afficher erreurs)
./fs_explorer.py scan /path/to/dir --recursive --verbose
```

#### Rechercher

```bash
# Par nom
./fs_explorer.py search --query "config"

# Par extension
./fs_explorer.py search --extension .py

# Par catégorie
./fs_explorer.py search --category code

# Combiner critères
./fs_explorer.py search --query "test" --extension .py --limit 10

# Mode verbeux
./fs_explorer.py search --query "main" --verbose
```

#### Statistiques

```bash
# Stats basiques
./fs_explorer.py stats

# Stats détaillées (top fichiers, récents)
./fs_explorer.py stats --verbose
```

#### Vider l'index

```bash
# Avec confirmation
./fs_explorer.py clear

# Sans confirmation
./fs_explorer.py clear --yes
```

### Python API

```python
from src.filesystem import FileSystemExplorer

# Créer instance
explorer = FileSystemExplorer()

# Scanner
stats = explorer.scan(Path("/path/to/dir"), recursive=True)
print(f"Fichiers ajoutés: {stats['files_added']}")

# Rechercher
results = explorer.search(
    query="config",
    extension=".json",
    category="config",
    limit=20
)

for metadata in results:
    print(f"{metadata.name} - {metadata.size} bytes")

# Statistiques
category_stats = explorer.get_category_stats()
for category, stats in category_stats.items():
    print(f"{category}: {stats['count']} fichiers")

# Top fichiers
largest = explorer.get_largest_files(10)
recent = explorer.get_recent_files(10)

# Vider index
explorer.clear_index()
```

## 📊 Exemples Réels

### Scan du projet HOPPER

```bash
$ ./fs_explorer.py scan . --recursive

📊 Résultats du scan:
  ✅ Fichiers ajoutés: 190
  🔄 Fichiers mis à jour: 0
  ⏭️  Fichiers ignorés: 263

📈 Statistiques globales:
  Total fichiers: 190
  Total répertoires: 66
  Taille totale: 1.3 MB
```

### Stats détaillées

```bash
$ ./fs_explorer.py stats --verbose

📊 Statistiques globales
==================================================
Total fichiers: 190
Total répertoires: 66
Taille totale: 1.3 MB
Dernier scan: 2025-10-23T14:11:38.781741

📂 Par catégorie
==================================================

CODE
  Fichiers: 80
  Taille: 544.1 KB
  Extensions: .c, .py

DOCS
  Fichiers: 63
  Taille: 630.7 KB
  Extensions: .md, .txt

CONFIG
  Fichiers: 10
  Taille: 52.1 KB
  Extensions: .ini, .json, .yaml, .yml

📏 Top 10 fichiers les plus gros
==================================================
 1.    37.5 KB - faiss.index
 2.    36.0 KB - index.json
 3.    29.3 KB - PHASE2_PLAN.md
 4.    28.7 KB - PHASE1_FINAL_ANALYSIS.md
 5.    26.4 KB - PLAN_IMPLEMENTATION_RAG_AVANCE.md
```

### Recherche de fichiers

```bash
# Tous les fichiers Python
$ ./fs_explorer.py search --extension .py --limit 5

🔎 Résultats de recherche: 5 fichiers

1. server.py
   📁 /Users/jilani/Projet/HOPPER/src/connectors/server.py
   📊 6.7 KB | .py

2. local_system.py
   📁 /Users/jilani/Projet/HOPPER/src/connectors/local_system.py
   📊 18.9 KB | .py

# Fichiers contenant "security"
$ ./fs_explorer.py search --query security

🔎 Résultats de recherche: 1 fichiers

1. security.py
   📁 /Users/jilani/Projet/HOPPER/src/middleware/security.py
   📊 8.5 KB | .py
```

## ⚙️ Configuration

### Personnaliser l'explorateur

```python
from pathlib import Path
from src.filesystem import FileSystemExplorer

explorer = FileSystemExplorer(
    index_file=Path("custom/path/index.json"),  # Chemin index custom
    exclude_dirs={"custom_dir", ".cache"},      # Répertoires à exclure
    max_file_size=50 * 1024 * 1024,             # 50MB max
    max_depth=5                                 # Profondeur max 5
)
```

### Ajouter des catégories

```python
# Dans src/filesystem/explorer.py
CATEGORIES = {
    "code": {".py", ".js", ...},
    "custom_category": {".custom", ".ext"},  # Nouvelle catégorie
    ...
}
```

### Ajouter des exclusions

```python
# Répertoires
DEFAULT_EXCLUDE_DIRS = {
    ".git", "node_modules",
    "my_custom_dir",  # Nouveau
    ...
}

# Extensions
IGNORE_EXTENSIONS = {
    ".pyc", ".log",
    ".custom_temp",  # Nouveau
    ...
}
```

## 🔍 Cas d'usage

### 1. Audit de projet
```bash
# Voir tout le code Python
./fs_explorer.py search --category code --extension .py

# Fichiers récemment modifiés
./fs_explorer.py stats --verbose  # Section "Top 10 fichiers récents"
```

### 2. Nettoyage disque
```bash
# Trouver les plus gros fichiers
./fs_explorer.py stats --verbose  # Section "Top 10 fichiers les plus gros"
```

### 3. Documentation
```bash
# Lister toute la doc
./fs_explorer.py search --category docs
```

### 4. Analyse d'architecture
```python
from src.filesystem import explorer

# Scanner le projet
explorer.scan(Path("."), recursive=True)

# Analyser structure
category_stats = explorer.get_category_stats()
print(f"Ratio code/docs: {category_stats['code']['count'] / category_stats['docs']['count']:.2f}")
```

## 🧪 Tests

```bash
# Lancer les tests
python -m pytest tests/test_filesystem_explorer.py -v

# Avec couverture
python -m pytest tests/test_filesystem_explorer.py --cov=src.filesystem
```

## 📝 Format de l'index

L'index JSON a cette structure :

```json
{
  "version": "1.0",
  "stats": {
    "total_files": 190,
    "total_dirs": 66,
    "total_size": 1300000,
    "by_category": {...},
    "scanned_paths": ["/path1", "/path2"],
    "last_scan": "2025-10-23T14:11:38.781741"
  },
  "index": {
    "/path/to/file.py": {
      "path": "/path/to/file.py",
      "name": "file.py",
      "extension": ".py",
      "size": 1024,
      "mime_type": "text/x-python",
      "created_at": 1234567890.0,
      "modified_at": 1234567890.0,
      "is_directory": false,
      "is_hidden": false,
      "permissions": "644"
    }
  },
  "directories": {...}
}
```

## 🚀 Performance

### Benchmarks (projet HOPPER)

| Opération | Temps | Résultat |
|-----------|-------|----------|
| Scan récursif complet | ~0.02s | 190 fichiers |
| Recherche dans index | <0.01s | Instantané |
| Chargement index | ~0.01s | 190 fichiers |
| Sauvegarde index | ~0.01s | 1.3 MB |

### Optimisations

- **Cache persistant** : Évite rescans inutiles
- **Exclusions intelligentes** : Ignore node_modules, .venv, etc.
- **Limite de taille** : Skip fichiers >100MB
- **Lazy loading** : Index chargé à la demande

## 🔐 Sécurité

- Respecte les permissions système
- Gère les PermissionError gracieusement
- N'écrit JAMAIS dans les fichiers scannés (lecture seule)
- Index stocké localement (pas de cloud)

## 🐛 Debugging

```python
from loguru import logger

# Activer logs debug
logger.add(sys.stderr, level="DEBUG")

explorer = FileSystemExplorer()
explorer.scan(Path("."), recursive=True)
```

## 📚 Ressources

- Code source : `src/filesystem/explorer.py`
- Tests : `tests/test_filesystem_explorer.py`
- CLI : `fs_explorer.py`
- Index : `data/filesystem/index.json`

---

**Créé le :** 2025-10-23  
**Version :** 1.0  
**Auteur :** HOPPER Dev Team
