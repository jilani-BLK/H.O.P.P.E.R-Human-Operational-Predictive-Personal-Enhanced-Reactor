"""
HOPPER - FileSystem Explorer
Scanner et indexation intelligente du système de fichiers
"""

import os
import json
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class FileMetadata:
    """Métadonnées d'un fichier"""
    path: str
    name: str
    extension: str
    size: int  # bytes
    mime_type: Optional[str]
    created_at: float
    modified_at: float
    is_directory: bool
    is_hidden: bool
    permissions: str  # format: rwxrwxrwx
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DirectoryInfo:
    """Information sur un répertoire"""
    path: str
    file_count: int
    dir_count: int
    total_size: int  # bytes
    depth: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FileSystemExplorer:
    """
    Explorateur intelligent du système de fichiers
    
    Fonctionnalités:
    - Scan récursif avec exclusions configurables
    - Indexation métadonnées (taille, dates, MIME)
    - Détection types de fichiers
    - Cache pour performances
    - Export JSON de l'index
    """
    
    # Extensions par catégorie
    CATEGORIES = {
        "code": {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".rb", ".php", ".swift", ".kt"},
        "config": {".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".env", ".config"},
        "docs": {".md", ".txt", ".pdf", ".doc", ".docx", ".rtf", ".tex"},
        "data": {".csv", ".xml", ".sql", ".db", ".sqlite"},
        "web": {".html", ".css", ".scss", ".sass", ".less"},
        "image": {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico"},
        "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
        "video": {".mp4", ".avi", ".mkv", ".mov", ".webm"},
        "archive": {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"},
        "binary": {".exe", ".dll", ".so", ".dylib", ".app"}
    }
    
    # Répertoires à exclure par défaut (performances + sécurité)
    DEFAULT_EXCLUDE_DIRS = {
        ".git", ".svn", ".hg",  # VCS
        "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",  # Build artifacts
        "venv", ".venv", "env", ".env",  # Virtual environments
        ".idea", ".vscode", ".vs",  # IDE
        "Library", "System",  # macOS system
        "AppData", "Windows",  # Windows system
    }
    
    # Extensions à ignorer (binaires lourds, temporaires)
    IGNORE_EXTENSIONS = {
        ".pyc", ".pyo", ".class", ".o", ".obj",  # Compiled
        ".log", ".tmp", ".temp", ".cache",  # Temporary
        ".DS_Store", ".localized",  # System
    }
    
    def __init__(
        self,
        index_file: Path = Path("data/filesystem/index.json"),
        exclude_dirs: Optional[Set[str]] = None,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB max
        max_depth: int = 10
    ):
        self.index_file = index_file
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.exclude_dirs = exclude_dirs or self.DEFAULT_EXCLUDE_DIRS
        self.max_file_size = max_file_size
        self.max_depth = max_depth
        
        # Index en mémoire
        self.index: Dict[str, FileMetadata] = {}
        self.directories: Dict[str, DirectoryInfo] = {}
        
        # Statistiques
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_size": 0,
            "by_category": {},
            "scanned_paths": [],
            "last_scan": None
        }
        
        # Charger index existant
        self._load_index()
    
    def scan(
        self,
        root_path: Path,
        recursive: bool = True,
        update_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Scanner un répertoire
        
        Args:
            root_path: Chemin racine à scanner
            recursive: Scanner récursivement
            update_existing: Mettre à jour fichiers existants
            
        Returns:
            Statistiques du scan
        """
        root_path = Path(root_path).resolve()
        
        if not root_path.exists():
            logger.error(f"Chemin inexistant: {root_path}")
            return {"error": "Path not found"}
        
        logger.info(f"🔍 Scan: {root_path} (recursive={recursive})")
        
        scan_stats = {
            "files_added": 0,
            "files_updated": 0,
            "files_skipped": 0,
            "errors": []
        }
        
        try:
            if root_path.is_file():
                # Scanner un seul fichier
                self._index_file(root_path, scan_stats, update_existing)
            else:
                # Scanner répertoire
                self._scan_directory(root_path, 0, scan_stats, recursive, update_existing)
            
            # Mettre à jour statistiques globales
            self._update_stats(root_path)
            
            # Sauvegarder index
            self._save_index()
            
            logger.success(f"✅ Scan terminé: {scan_stats['files_added']} ajoutés, {scan_stats['files_updated']} mis à jour")
            
        except Exception as e:
            logger.error(f"❌ Erreur scan: {e}")
            scan_stats["errors"].append(str(e))
        
        return scan_stats
    
    def _scan_directory(
        self,
        dir_path: Path,
        depth: int,
        scan_stats: Dict[str, Any],
        recursive: bool,
        update_existing: bool
    ):
        """Scanner un répertoire récursivement"""
        if depth > self.max_depth:
            logger.warning(f"⚠️ Profondeur max atteinte: {dir_path}")
            return
        
        if dir_path.name in self.exclude_dirs:
            logger.debug(f"⏭️ Exclu: {dir_path}")
            return
        
        try:
            entries = list(dir_path.iterdir())
        except PermissionError:
            logger.warning(f"⚠️ Permission refusée: {dir_path}")
            scan_stats["errors"].append(f"Permission denied: {dir_path}")
            return
        except Exception as e:
            logger.error(f"❌ Erreur lecture {dir_path}: {e}")
            scan_stats["errors"].append(f"Error reading {dir_path}: {e}")
            return
        
        dir_info = DirectoryInfo(
            path=str(dir_path),
            file_count=0,
            dir_count=0,
            total_size=0,
            depth=depth
        )
        
        for entry in entries:
            try:
                if entry.is_file():
                    # Indexer fichier
                    metadata = self._index_file(entry, scan_stats, update_existing)
                    if metadata:
                        dir_info.file_count += 1
                        dir_info.total_size += metadata.size
                
                elif entry.is_dir() and recursive:
                    # Scanner sous-répertoire
                    if entry.name not in self.exclude_dirs:
                        dir_info.dir_count += 1
                        self._scan_directory(entry, depth + 1, scan_stats, recursive, update_existing)
            
            except Exception as e:
                logger.debug(f"⏭️ Erreur {entry}: {e}")
                scan_stats["errors"].append(f"Error processing {entry}: {e}")
        
        # Enregistrer info répertoire
        self.directories[str(dir_path)] = dir_info
    
    def _index_file(
        self,
        file_path: Path,
        scan_stats: Dict[str, Any],
        update_existing: bool
    ) -> Optional[FileMetadata]:
        """Indexer un fichier"""
        file_key = str(file_path)
        
        # Vérifier si déjà indexé
        if file_key in self.index and not update_existing:
            scan_stats["files_skipped"] += 1
            return self.index[file_key]
        
        # Ignorer certaines extensions
        if file_path.suffix.lower() in self.IGNORE_EXTENSIONS:
            scan_stats["files_skipped"] += 1
            return None
        
        try:
            stat = file_path.stat()
            
            # Ignorer fichiers trop gros
            if stat.st_size > self.max_file_size:
                logger.debug(f"⏭️ Fichier trop gros: {file_path} ({stat.st_size / 1024 / 1024:.1f}MB)")
                scan_stats["files_skipped"] += 1
                return None
            
            # Créer métadonnées
            metadata = FileMetadata(
                path=str(file_path),
                name=file_path.name,
                extension=file_path.suffix.lower(),
                size=stat.st_size,
                mime_type=mimetypes.guess_type(str(file_path))[0],
                created_at=stat.st_ctime,
                modified_at=stat.st_mtime,
                is_directory=False,
                is_hidden=file_path.name.startswith('.'),
                permissions=oct(stat.st_mode)[-3:]
            )
            
            # Ajouter à l'index
            self.index[file_key] = metadata
            
            if file_key in self.index:
                scan_stats["files_updated"] += 1
            else:
                scan_stats["files_added"] += 1
            
            return metadata
        
        except Exception as e:
            logger.debug(f"⏭️ Erreur indexation {file_path}: {e}")
            scan_stats["errors"].append(f"Error indexing {file_path}: {e}")
            return None
    
    def search(
        self,
        query: str = "",
        extension: Optional[str] = None,
        category: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        modified_after: Optional[float] = None,
        limit: int = 100
    ) -> List[FileMetadata]:
        """
        Rechercher dans l'index
        
        Args:
            query: Recherche dans le nom de fichier
            extension: Filtrer par extension (.py, .js, etc.)
            category: Filtrer par catégorie (code, docs, etc.)
            min_size: Taille minimum (bytes)
            max_size: Taille maximum (bytes)
            modified_after: Modifié après timestamp
            limit: Nombre max de résultats
            
        Returns:
            Liste de métadonnées correspondantes
        """
        results = []
        query_lower = query.lower()
        
        # Extensions de la catégorie
        if category and category in self.CATEGORIES:
            valid_extensions = self.CATEGORIES[category]
        else:
            valid_extensions = None
        
        for metadata in self.index.values():
            # Filtre nom
            if query and query_lower not in metadata.name.lower():
                continue
            
            # Filtre extension
            if extension and metadata.extension != extension.lower():
                continue
            
            # Filtre catégorie
            if valid_extensions and metadata.extension not in valid_extensions:
                continue
            
            # Filtre taille
            if min_size and metadata.size < min_size:
                continue
            if max_size and metadata.size > max_size:
                continue
            
            # Filtre date
            if modified_after and metadata.modified_at < modified_after:
                continue
            
            results.append(metadata)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """Statistiques par catégorie"""
        category_stats = {}
        
        for category, extensions in self.CATEGORIES.items():
            files = [m for m in self.index.values() if m.extension in extensions]
            
            if files:
                category_stats[category] = {
                    "count": len(files),
                    "total_size": sum(f.size for f in files),
                    "avg_size": sum(f.size for f in files) / len(files),
                    "extensions": list(set(f.extension for f in files))
                }
        
        return category_stats
    
    def get_largest_files(self, limit: int = 10) -> List[FileMetadata]:
        """Fichiers les plus gros"""
        return sorted(self.index.values(), key=lambda m: m.size, reverse=True)[:limit]
    
    def get_recent_files(self, limit: int = 10) -> List[FileMetadata]:
        """Fichiers récemment modifiés"""
        return sorted(self.index.values(), key=lambda m: m.modified_at, reverse=True)[:limit]
    
    def _update_stats(self, scanned_path: Path):
        """Mettre à jour statistiques globales"""
        self.stats["total_files"] = len(self.index)
        self.stats["total_dirs"] = len(self.directories)
        self.stats["total_size"] = sum(m.size for m in self.index.values())
        self.stats["by_category"] = self.get_category_stats()
        self.stats["last_scan"] = datetime.now().isoformat()
        
        if str(scanned_path) not in self.stats["scanned_paths"]:
            self.stats["scanned_paths"].append(str(scanned_path))
    
    def _save_index(self):
        """Sauvegarder index sur disque"""
        try:
            data = {
                "version": "1.0",
                "stats": self.stats,
                "index": {path: metadata.to_dict() for path, metadata in self.index.items()},
                "directories": {path: dir_info.to_dict() for path, dir_info in self.directories.items()}
            }
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Index sauvegardé: {self.index_file}")
        
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde index: {e}")
    
    def _load_index(self):
        """Charger index depuis disque"""
        if not self.index_file.exists():
            logger.debug("📂 Pas d'index existant")
            return
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Charger stats
            self.stats = data.get("stats", self.stats)
            
            # Charger index
            index_data = data.get("index", {})
            for path, metadata_dict in index_data.items():
                self.index[path] = FileMetadata(**metadata_dict)
            
            # Charger directories
            dirs_data = data.get("directories", {})
            for path, dir_dict in dirs_data.items():
                self.directories[path] = DirectoryInfo(**dir_dict)
            
            logger.success(f"✅ Index chargé: {len(self.index)} fichiers")
        
        except Exception as e:
            logger.error(f"❌ Erreur chargement index: {e}")
    
    def clear_index(self):
        """Vider l'index"""
        self.index.clear()
        self.directories.clear()
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_size": 0,
            "by_category": {},
            "scanned_paths": [],
            "last_scan": None
        }
        logger.info("🗑️ Index vidé")


# Instance globale
explorer = FileSystemExplorer()
