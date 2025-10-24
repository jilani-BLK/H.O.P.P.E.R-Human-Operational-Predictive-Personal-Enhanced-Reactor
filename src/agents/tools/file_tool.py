"""
File Tool - Read, write, and manipulate files.

Security:
    - Path traversal validation (CWE-22)
    - Sandboxing to allowed directories
    - No access to system files
"""

from src.agents.tools.base_tool import BaseTool, ToolMetadata
from typing import Optional
import os
from pathlib import Path


# Configuration sécurité
ALLOWED_BASE_PATHS = [
    "/tmp",
    "/data",
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
]

FORBIDDEN_PATHS = [
    "/etc",
    "/sys",
    "/proc",
    "/root",
    "/boot",
    "/dev",
    "/var/log",
]


def validate_path(path: str) -> tuple[bool, Optional[str]]:
    """
    Valide un chemin pour prévenir path traversal (CWE-22)
    
    Args:
        path: Chemin à valider
        
    Returns:
        (is_valid, error_message)
    """
    try:
        # Résoudre le chemin absolu (résout .., symlinks, etc.)
        resolved_path = Path(path).resolve()
        resolved_str = str(resolved_path)
        
        # Vérifier que le chemin résolu ne contient pas de traversal
        if ".." in path:
            return False, "Path traversal detected (..)"
        
        # Vérifier chemins interdits
        for forbidden in FORBIDDEN_PATHS:
            if resolved_str.startswith(forbidden):
                return False, f"Access to {forbidden} is forbidden"
        
        # Vérifier chemins autorisés
        allowed = False
        for allowed_base in ALLOWED_BASE_PATHS:
            try:
                allowed_base_resolved = str(Path(allowed_base).resolve())
                if resolved_str.startswith(allowed_base_resolved):
                    allowed = True
                    break
            except Exception:
                continue
        
        if not allowed:
            return False, f"Path must be in allowed directories: {', '.join(ALLOWED_BASE_PATHS)}"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


class ReadFileTool(BaseTool):
    """
    Outil pour lire le contenu d'un fichier.
    
    Usage:
        read_file(path="/path/to/file.txt")
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="read_file",
            description="Read the contents of a file",
            schema={
                "parameters": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                        "required": True
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "required": False
                    }
                }
            },
            category="files",
            requires_confirmation=False
        )
    
    async def execute(self, path: str, encoding: str = "utf-8") -> str:
        """
        Lit un fichier.
        
        Args:
            path: Chemin du fichier
            encoding: Encodage du fichier
            
        Returns:
            Contenu du fichier ou erreur
            
        Security:
            - Path traversal validation
            - Sandboxing to allowed directories
        """
        # Validation sécurité
        is_valid, error = validate_path(path)
        if not is_valid:
            return f"🚫 Security: {error}"
        
        try:
            if not os.path.exists(path):
                return f"❌ File not found: {path}"
            
            if not os.path.isfile(path):
                return f"❌ Not a file: {path}"
            
            # Limite taille fichier (10MB max)
            file_size = os.path.getsize(path)
            MAX_SIZE = 10 * 1024 * 1024  # 10MB
            
            if file_size > MAX_SIZE:
                return f"❌ File too large: {file_size} bytes (max {MAX_SIZE})"
            
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            lines = len(content.split('\n'))
            chars = len(content)
            
            # Limiter l'output pour pas surcharger
            if len(content) > 1000:
                preview = content[:1000] + f"\n... (truncated, total {chars} chars, {lines} lines)"
            else:
                preview = content
            
            return f"✅ Read {path} ({lines} lines, {chars} chars):\n{preview}"
        
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"


class WriteFileTool(BaseTool):
    """
    Outil pour écrire dans un fichier.
    
    Usage:
        write_file(path="/path/to/file.txt", content="Hello World")
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="write_file",
            description="Write content to a file (creates or overwrites)",
            schema={
                "parameters": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write",
                        "required": True
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                        "required": True
                    },
                    "mode": {
                        "type": "string",
                        "description": "Write mode: 'write' (overwrite) or 'append'",
                        "required": False
                    }
                }
            },
            category="files",
            requires_confirmation=True
        )
    
    async def execute(self, path: str, content: str, mode: str = "write") -> str:
        """
        Écrit dans un fichier.
        
        Args:
            path: Chemin du fichier
            content: Contenu à écrire
            mode: 'write' (écrase) ou 'append' (ajoute)
            
        Returns:
            Message de confirmation ou erreur
            
        Security:
            - Path traversal validation
            - Content size limit
        """
        # Validation sécurité
        is_valid, error = validate_path(path)
        if not is_valid:
            return f"🚫 Security: {error}"
        
        # Limite taille contenu (5MB max)
        MAX_CONTENT_SIZE = 5 * 1024 * 1024  # 5MB
        if len(content) > MAX_CONTENT_SIZE:
            return f"❌ Content too large: {len(content)} bytes (max {MAX_CONTENT_SIZE})"
        
        try:
            write_mode = 'w' if mode == "write" else 'a'
            
            # Créer répertoire parent si nécessaire
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(path, write_mode, encoding='utf-8') as f:
                f.write(content)
            
            size = os.path.getsize(path)
            action = "Written to" if mode == "write" else "Appended to"
            
            return f"✅ {action} {path} ({size} bytes)"
        
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"


class ListDirectoryTool(BaseTool):
    """
    Outil pour lister les fichiers d'un répertoire.
    
    Usage:
        list_directory(path="/path/to/dir")
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="list_directory",
            description="List files and directories in a path",
            schema={
                "parameters": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list",
                        "required": True
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files (starting with .)",
                        "required": False
                    }
                }
            },
            category="files",
            requires_confirmation=False
        )
    
    async def execute(self, path: str, show_hidden: bool = False) -> str:
        """
        Liste les fichiers d'un répertoire.
        
        Args:
            path: Chemin du répertoire
            show_hidden: Inclure les fichiers cachés
            
        Returns:
            Liste des fichiers ou erreur
            
        Security:
            - Path traversal validation
        """
        # Validation sécurité
        is_valid, error = validate_path(path)
        if not is_valid:
            return f"🚫 Security: {error}"
        
        try:
            if not os.path.exists(path):
                return f"❌ Directory not found: {path}"
            
            if not os.path.isdir(path):
                return f"❌ Not a directory: {path}"
            
            items = os.listdir(path)
            
            if not show_hidden:
                items = [item for item in items if not item.startswith('.')]
            
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
            files = [item for item in items if os.path.isfile(os.path.join(path, item))]
            
            result = f"✅ Contents of {path}:\n"
            result += f"  Directories ({len(dirs)}): {', '.join(dirs[:10])}\n"
            if len(dirs) > 10:
                result += f"    ... and {len(dirs)-10} more\n"
            result += f"  Files ({len(files)}): {', '.join(files[:10])}\n"
            if len(files) > 10:
                result += f"    ... and {len(files)-10} more\n"
            
            return result
        
        except Exception as e:
            return f"❌ Error listing directory: {str(e)}"


# Tests
async def test_file_tools():
    """Test des outils fichier."""
    print("="*60)
    print("Testing File Tools")
    print("="*60)
    
    # Test 1: Write file
    print("\n📝 Test 1: Write file")
    write_tool = WriteFileTool()
    result = await write_tool.execute(
        path="/tmp/hopper_test.txt",
        content="Hello from HOPPER ReAct Agent!"
    )
    print(f"  {result}")
    
    # Test 2: Read file
    print("\n📖 Test 2: Read file")
    read_tool = ReadFileTool()
    result = await read_tool.execute(path="/tmp/hopper_test.txt")
    print(f"  {result}")
    
    # Test 3: Append to file
    print("\n➕ Test 3: Append to file")
    result = await write_tool.execute(
        path="/tmp/hopper_test.txt",
        content="\nSecond line appended!",
        mode="append"
    )
    print(f"  {result}")
    
    # Test 4: Read again
    print("\n📖 Test 4: Read after append")
    result = await read_tool.execute(path="/tmp/hopper_test.txt")
    print(f"  {result}")
    
    # Test 5: List directory
    print("\n📂 Test 5: List directory")
    list_tool = ListDirectoryTool()
    result = await list_tool.execute(path="/tmp")
    print(f"  {result[:300]}...")  # Truncate output
    
    # Test 6: Non-existent file
    print("\n❌ Test 6: Non-existent file")
    result = await read_tool.execute(path="/tmp/does_not_exist.txt")
    print(f"  {result}")
    
    # Cleanup
    try:
        os.remove("/tmp/hopper_test.txt")
    except:
        pass
    
    print("\n" + "="*60)
    print("✅ File tools tests completed!")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_file_tools())
