"""
Tests pour FileSystem Explorer
"""

import os
import tempfile
from pathlib import Path
import pytest
from src.filesystem.explorer import FileSystemExplorer, FileMetadata


@pytest.fixture
def temp_workspace():
    """Créer un workspace temporaire pour tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "test_workspace"
        workspace.mkdir()
        
        # Créer structure de test
        # Répertoires
        (workspace / "src").mkdir()
        (workspace / "src" / "utils").mkdir()
        (workspace / "docs").mkdir()
        (workspace / "data").mkdir()
        (workspace / ".git").mkdir()  # Devrait être exclu
        
        # Fichiers Python
        (workspace / "main.py").write_text("print('hello')")
        (workspace / "src" / "app.py").write_text("def main(): pass")
        (workspace / "src" / "utils" / "helper.py").write_text("# Helper")
        
        # Fichiers config
        (workspace / "config.json").write_text('{"key": "value"}')
        (workspace / ".env").write_text("SECRET=test")
        
        # Fichiers docs
        (workspace / "README.md").write_text("# Project")
        (workspace / "docs" / "guide.md").write_text("## Guide")
        
        # Fichiers data
        (workspace / "data" / "data.csv").write_text("a,b,c\n1,2,3")
        
        # Fichiers cachés/à ignorer
        (workspace / ".DS_Store").write_text("system")
        (workspace / "test.pyc").write_text("compiled")
        
        yield workspace


def test_scan_basic(temp_workspace):
    """Test scan basique d'un répertoire"""
    explorer = FileSystemExplorer()
    
    stats = explorer.scan(temp_workspace, recursive=False)
    
    assert stats["files_added"] > 0
    assert len(explorer.index) > 0
    assert explorer.stats["total_files"] > 0


def test_scan_recursive(temp_workspace):
    """Test scan récursif"""
    explorer = FileSystemExplorer()
    
    stats = explorer.scan(temp_workspace, recursive=True)
    
    # Devrait trouver fichiers dans src/ et docs/
    assert stats["files_added"] >= 6  # Au moins 6 fichiers valides
    
    # Vérifier que .git est exclu
    git_files = [path for path in explorer.index.keys() if ".git" in path]
    assert len(git_files) == 0


def test_file_metadata(temp_workspace):
    """Test extraction métadonnées"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace / "main.py")
    
    metadata = explorer.index.get(str(temp_workspace / "main.py"))
    assert metadata is not None
    assert metadata.name == "main.py"
    assert metadata.extension == ".py"
    assert metadata.size > 0
    assert metadata.is_directory is False


def test_search_by_name(temp_workspace):
    """Test recherche par nom"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    results = explorer.search(query="main")
    assert len(results) >= 1
    assert any("main.py" in r.name for r in results)


def test_search_by_extension(temp_workspace):
    """Test recherche par extension"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    # Chercher fichiers Python
    results = explorer.search(extension=".py")
    assert len(results) >= 3  # main.py, app.py, helper.py
    assert all(r.extension == ".py" for r in results)


def test_search_by_category(temp_workspace):
    """Test recherche par catégorie"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    # Catégorie "code"
    code_files = explorer.search(category="code")
    assert len(code_files) >= 3
    assert all(f.extension == ".py" for f in code_files)
    
    # Catégorie "docs"
    doc_files = explorer.search(category="docs")
    assert len(doc_files) >= 2  # README.md, guide.md
    assert all(f.extension == ".md" for f in doc_files)


def test_category_stats(temp_workspace):
    """Test statistiques par catégorie"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    stats = explorer.get_category_stats()
    
    assert "code" in stats
    assert stats["code"]["count"] >= 3
    assert ".py" in stats["code"]["extensions"]
    
    assert "docs" in stats
    assert stats["docs"]["count"] >= 2


def test_largest_files(temp_workspace):
    """Test recherche fichiers les plus gros"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    largest = explorer.get_largest_files(limit=3)
    
    assert len(largest) > 0
    # Vérifier ordre décroissant
    for i in range(len(largest) - 1):
        assert largest[i].size >= largest[i + 1].size


def test_recent_files(temp_workspace):
    """Test recherche fichiers récents"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    recent = explorer.get_recent_files(limit=5)
    
    assert len(recent) > 0
    # Vérifier ordre décroissant de modification
    for i in range(len(recent) - 1):
        assert recent[i].modified_at >= recent[i + 1].modified_at


def test_exclude_dirs(temp_workspace):
    """Test exclusion de répertoires"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    # .git devrait être exclu
    git_files = [f for f in explorer.index.values() if ".git" in f.path]
    assert len(git_files) == 0


def test_ignore_extensions(temp_workspace):
    """Test exclusion d'extensions"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    # .pyc et .DS_Store devraient être exclus
    pyc_files = [f for f in explorer.index.values() if f.extension == ".pyc"]
    ds_files = [f for f in explorer.index.values() if ".DS_Store" in f.name]
    
    assert len(pyc_files) == 0
    assert len(ds_files) == 0


def test_save_and_load_index(temp_workspace):
    """Test sauvegarde et chargement de l'index"""
    index_file = Path(tempfile.gettempdir()) / "test_index.json"
    
    # Scanner et sauvegarder
    explorer1 = FileSystemExplorer(index_file=index_file)
    explorer1.scan(temp_workspace, recursive=True)
    files_count = len(explorer1.index)
    
    # Recharger dans nouvelle instance
    explorer2 = FileSystemExplorer(index_file=index_file)
    
    assert len(explorer2.index) == files_count
    assert explorer2.stats["total_files"] == files_count
    
    # Cleanup
    index_file.unlink(missing_ok=True)


def test_update_existing(temp_workspace):
    """Test mise à jour de fichiers existants"""
    explorer = FileSystemExplorer()
    
    # Scan initial
    stats1 = explorer.scan(temp_workspace / "main.py")
    assert stats1["files_added"] == 1
    
    # Rescan sans update
    stats2 = explorer.scan(temp_workspace / "main.py", update_existing=False)
    assert stats2["files_skipped"] == 1
    
    # Rescan avec update
    stats3 = explorer.scan(temp_workspace / "main.py", update_existing=True)
    assert stats3["files_updated"] == 1


def test_search_with_size_filter(temp_workspace):
    """Test recherche avec filtre de taille"""
    explorer = FileSystemExplorer()
    explorer.scan(temp_workspace, recursive=True)
    
    # Fichiers > 0 bytes
    results = explorer.search(min_size=1)
    assert all(r.size > 0 for r in results)
    
    # Fichiers < 1KB
    results = explorer.search(max_size=1024)
    assert all(r.size <= 1024 for r in results)


def test_clear_index():
    """Test vidage de l'index"""
    explorer = FileSystemExplorer()
    
    # Ajouter données fictives
    explorer.index["test"] = FileMetadata(
        path="/test",
        name="test.py",
        extension=".py",
        size=100,
        mime_type="text/x-python",
        created_at=0,
        modified_at=0,
        is_directory=False,
        is_hidden=False,
        permissions="644"
    )
    
    assert len(explorer.index) > 0
    
    explorer.clear_index()
    
    assert len(explorer.index) == 0
    assert explorer.stats["total_files"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
