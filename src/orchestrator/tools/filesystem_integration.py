"""
HOPPER - FileSystem Tools Integration
Permet au LLM d'utiliser le FileSystem Explorer
"""

import httpx
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger

# Import robuste du FileSystem Explorer
try:
    from src.filesystem import explorer
except ImportError:
    # Fallback: utiliser chemin absolu si import relatif échoue
    import sys
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.filesystem import explorer


class FileSystemToolsIntegration:
    """
    Permet au LLM d'utiliser FileSystem Explorer
    
    Commandes détectées:
    - "cherche fichiers Python dans src/"
    - "quels sont les plus gros fichiers?"
    - "fichiers récemment modifiés"
    - "stats du projet"
    - "scanne le répertoire src/"
    """
    
    async def search_files(
        self,
        query: str = "",
        extension: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Rechercher dans l'index"""
        try:
            # Vérifier que le FileSystem Explorer est initialisé
            if not hasattr(explorer, 'stats') or explorer.stats.get("total_files", 0) == 0:
                logger.warning("⚠️ FileSystem Explorer non scanné, scan automatique...")
                from pathlib import Path
                explorer.scan(Path.cwd(), recursive=True)
            
            results = explorer.search(
                query=query,
                extension=extension,
                category=category,
                limit=limit
            )
            
            files_info = [
                {
                    "name": f.name,
                    "path": f.path,
                    "size": f.size,
                    "extension": f.extension
                }
                for f in results
            ]
            
            return {
                "success": True,
                "count": len(results),
                "files": files_info
            }
        
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtenir statistiques du projet"""
        try:
            category_stats = explorer.get_category_stats()
            
            return {
                "success": True,
                "total_files": explorer.stats["total_files"],
                "total_size": explorer.stats["total_size"],
                "categories": {
                    cat: {
                        "count": stats["count"],
                        "total_size": stats["total_size"]
                    }
                    for cat, stats in category_stats.items()
                }
            }
        
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_largest_files(self, limit: int = 10) -> Dict[str, Any]:
        """Fichiers les plus gros"""
        try:
            largest = explorer.get_largest_files(limit)
            
            files_info = [
                {
                    "name": f.name,
                    "path": f.path,
                    "size": f.size,
                    "size_mb": round(f.size / 1024 / 1024, 2)
                }
                for f in largest
            ]
            
            return {
                "success": True,
                "files": files_info
            }
        
        except Exception as e:
            logger.error(f"Erreur largest: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_recent_files(self, limit: int = 10) -> Dict[str, Any]:
        """Fichiers récemment modifiés"""
        try:
            recent = explorer.get_recent_files(limit)
            
            from datetime import datetime
            
            files_info = [
                {
                    "name": f.name,
                    "path": f.path,
                    "modified": datetime.fromtimestamp(f.modified_at).strftime("%Y-%m-%d %H:%M")
                }
                for f in recent
            ]
            
            return {
                "success": True,
                "files": files_info
            }
        
        except Exception as e:
            logger.error(f"Erreur recent: {e}")
            return {"success": False, "error": str(e)}
    
    async def scan_directory(self, path: str = ".", recursive: bool = True) -> Dict[str, Any]:
        """Scanner un répertoire"""
        try:
            stats = explorer.scan(Path(path), recursive=recursive)
            
            return {
                "success": True,
                "files_added": stats["files_added"],
                "files_updated": stats["files_updated"],
                "files_skipped": stats["files_skipped"]
            }
        
        except Exception as e:
            logger.error(f"Erreur scan: {e}")
            return {"success": False, "error": str(e)}
    
    def format_result_for_llm(self, action: str, result: Dict[str, Any]) -> str:
        """Formater résultat pour le LLM"""
        if not result.get("success"):
            return f"\n[FILESYSTEM] ❌ Erreur: {result.get('error')}"
        
        if action == "search":
            files = result.get("files", [])
            if not files:
                return "\n[FILESYSTEM] Aucun fichier trouvé"
            files_str = "\n".join([f"  - {f['name']} ({f['path']})" for f in files[:5]])
            return f"\n[FILESYSTEM] ✅ {result['count']} fichiers trouvés:\n{files_str}"
        
        elif action == "stats":
            total = result.get("total_files", 0)
            size_mb = round(result.get("total_size", 0) / 1024 / 1024, 2)
            cats = result.get("categories", {})
            cats_str = ", ".join([f"{cat}: {info['count']}" for cat, info in cats.items()])
            return f"\n[FILESYSTEM] ✅ Stats: {total} fichiers, {size_mb} MB\nCatégories: {cats_str}"
        
        elif action == "largest":
            files = result.get("files", [])
            files_str = "\n".join([f"  - {f['name']}: {f['size_mb']} MB" for f in files[:5]])
            return f"\n[FILESYSTEM] ✅ Plus gros fichiers:\n{files_str}"
        
        elif action == "recent":
            files = result.get("files", [])
            files_str = "\n".join([f"  - {f['name']} ({f['modified']})" for f in files[:5]])
            return f"\n[FILESYSTEM] ✅ Fichiers récents:\n{files_str}"
        
        elif action == "scan":
            added = result.get("files_added", 0)
            updated = result.get("files_updated", 0)
            return f"\n[FILESYSTEM] ✅ Scan terminé: {added} ajoutés, {updated} mis à jour"
        
        return f"\n[FILESYSTEM] ✅ Action {action} terminée"


# Instance globale
fs_tools = FileSystemToolsIntegration()
