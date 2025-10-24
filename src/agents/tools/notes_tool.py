"""
Notes Tool - Create and manage notes/memos.
"""

from src.agents.tools.base_tool import BaseTool, ToolMetadata
from typing import List, Dict, Optional
import json
import os
from datetime import datetime


class NotesStore:
    """Simple in-memory notes store (can be persisted to file)."""
    
    def __init__(self, storage_path: str = "/tmp/hopper_notes.json"):
        self.storage_path = storage_path
        self.notes: Dict[str, Dict] = {}
        self.load()
    
    def load(self):
        """Load notes from file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.notes = json.load(f)
            except:
                self.notes = {}
    
    def save(self):
        """Save notes to file."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.notes, f, indent=2)
        except:
            pass
    
    def add_note(self, title: str, content: str, tags: Optional[List[str]] = None) -> str:
        """Add a new note."""
        note_id = f"note_{len(self.notes) + 1}"
        self.notes[note_id] = {
            "id": note_id,
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.save()
        return note_id
    
    def get_note(self, note_id: str) -> Optional[Dict]:
        """Get a note by ID."""
        return self.notes.get(note_id)
    
    def search_notes(self, query: str) -> List[Dict]:
        """Search notes by title or content."""
        results = []
        query_lower = query.lower()
        for note in self.notes.values():
            if (query_lower in note["title"].lower() or 
                query_lower in note["content"].lower() or
                any(query_lower in tag.lower() for tag in note["tags"])):
                results.append(note)
        return results
    
    def list_all_notes(self) -> List[Dict]:
        """List all notes."""
        return list(self.notes.values())


# Singleton store
_notes_store = NotesStore()


class CreateNoteTool(BaseTool):
    """
    Outil pour créer une nouvelle note.
    
    Usage:
        create_note(title="Meeting Notes", content="Discussed Q4 goals", tags="work,meetings")
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="create_note",
            description="Create a new note/memo with title and content",
            schema={
                "parameters": {
                    "title": {
                        "type": "string",
                        "description": "Note title",
                        "required": True
                    },
                    "content": {
                        "type": "string",
                        "description": "Note content",
                        "required": True
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags",
                        "required": False
                    }
                }
            },
            category="notes",
            requires_confirmation=False
        )
    
    async def execute(self, title: str, content: str, tags: str = "") -> str:
        """
        Crée une nouvelle note.
        
        Args:
            title: Titre de la note
            content: Contenu de la note
            tags: Tags séparés par virgule
            
        Returns:
            ID de la note créée
        """
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        note_id = _notes_store.add_note(title, content, tag_list)
        
        return f"✅ Note created: {note_id} - '{title}'"


class SearchNotesTool(BaseTool):
    """
    Outil pour rechercher des notes.
    
    Usage:
        search_notes(query="meeting")
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="search_notes",
            description="Search notes by keyword in title, content or tags",
            schema={
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                        "required": True
                    }
                }
            },
            category="notes",
            requires_confirmation=False
        )
    
    async def execute(self, query: str) -> str:
        """
        Recherche des notes.
        
        Args:
            query: Mot-clé de recherche
            
        Returns:
            Liste des notes trouvées
        """
        results = _notes_store.search_notes(query)
        
        if not results:
            return f"❌ No notes found for query: '{query}'"
        
        output = f"✅ Found {len(results)} note(s) for '{query}':\n"
        for note in results[:5]:  # Limit to 5
            output += f"\n  • {note['id']}: {note['title']}\n"
            output += f"    {note['content'][:100]}{'...' if len(note['content']) > 100 else ''}\n"
            if note['tags']:
                output += f"    Tags: {', '.join(note['tags'])}\n"
        
        if len(results) > 5:
            output += f"\n  ... and {len(results) - 5} more"
        
        return output


class ListNotesTool(BaseTool):
    """
    Outil pour lister toutes les notes.
    
    Usage:
        list_notes()
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="list_notes",
            description="List all notes",
            schema={
                "parameters": {}
            },
            category="notes",
            requires_confirmation=False
        )
    
    async def execute(self) -> str:
        """
        Liste toutes les notes.
        
        Returns:
            Liste des notes
        """
        notes = _notes_store.list_all_notes()
        
        if not notes:
            return "❌ No notes found"
        
        output = f"✅ Total {len(notes)} note(s):\n"
        for note in notes[:10]:  # Limit to 10
            output += f"\n  • {note['id']}: {note['title']}\n"
            output += f"    Created: {note['created_at']}\n"
        
        if len(notes) > 10:
            output += f"\n  ... and {len(notes) - 10} more"
        
        return output


# Tests
async def test_notes_tools():
    """Test des outils notes."""
    print("="*60)
    print("Testing Notes Tools")
    print("="*60)
    
    # Cleanup
    if os.path.exists("/tmp/hopper_notes.json"):
        os.remove("/tmp/hopper_notes.json")
    
    # Test 1: Create note
    print("\n📝 Test 1: Create note")
    create_tool = CreateNoteTool()
    result = await create_tool.execute(
        title="Weekly Goals",
        content="1. Finish Phase 3.5\n2. Test GraphRAG\n3. Document ReAct Agent",
        tags="work,goals"
    )
    print(f"  {result}")
    
    # Test 2: Create another note
    print("\n📝 Test 2: Create another note")
    result = await create_tool.execute(
        title="Meeting Notes - Q4 Planning",
        content="Discussed budget allocation and team expansion.",
        tags="meetings,planning"
    )
    print(f"  {result}")
    
    # Test 3: List notes
    print("\n📋 Test 3: List notes")
    list_tool = ListNotesTool()
    result = await list_tool.execute()
    print(f"  {result}")
    
    # Test 4: Search notes
    print("\n🔍 Test 4: Search notes")
    search_tool = SearchNotesTool()
    result = await search_tool.execute(query="goals")
    print(f"  {result}")
    
    # Test 5: Search by tag
    print("\n🔍 Test 5: Search by tag")
    result = await search_tool.execute(query="meetings")
    print(f"  {result}")
    
    # Test 6: No results
    print("\n🔍 Test 6: No results")
    result = await search_tool.execute(query="nonexistent")
    print(f"  {result}")
    
    print("\n" + "="*60)
    print("✅ Notes tools tests completed!")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_notes_tools())
