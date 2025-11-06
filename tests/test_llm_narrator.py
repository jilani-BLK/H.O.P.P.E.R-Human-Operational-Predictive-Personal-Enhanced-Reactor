"""
Test LLMActionNarrator avec vraie LLM

Valide la génération de narrations dynamiques
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from communication.llm_action_narrator import LLMActionNarrator


async def test_narrator():
    """Test génération narrations"""
    
    print("=" * 70)
    print("🧪 TEST LLM ACTION NARRATOR")
    print("=" * 70)
    print()
    
    narrator = LLMActionNarrator(llm_service_url="http://localhost:5001")
    
    # Test 1: Narration succès
    print("1️⃣ Test: Narration action filesystem réussie")
    print("-" * 70)
    
    narration1 = await narrator.generate_narration(
        action_type="system_action",
        action_details={
            "tool_id": "filesystem",
            "capability": "list_directory",
            "parameters": {"directory": "/Users/jilani/Downloads"},
            "reasoning": "L'utilisateur veut savoir combien de fichiers il y a"
        },
        execution_result={
            "success": True,
            "data": {"total": 42, "files": 38, "directories": 4}
        },
        tone="friendly"
    )
    
    print(f"Narration: {narration1}")
    print()
    
    # Test 2: Narration erreur
    print("2️⃣ Test: Message d'erreur")
    print("-" * 70)
    
    error_msg = await narrator.generate_error_message(
        error="Permission denied: /private/var",
        context={"tool": "filesystem", "operation": "read"},
        tone="empathetic"
    )
    
    print(f"Message: {error_msg}")
    print()
    
    # Test 3: Question simple
    print("3️⃣ Test: Question simple sans tools")
    print("-" * 70)
    
    narration3 = await narrator.generate_narration(
        action_type="question",
        action_details={
            "tool_id": "",
            "capability": "",
            "parameters": {},
            "reasoning": "Question factuelle"
        },
        execution_result=None,
        tone="neutral"
    )
    
    print(f"Narration: {narration3}")
    print()
    
    # Test 4: Confirmation demande
    print("4️⃣ Test: Demande de confirmation")
    print("-" * 70)
    
    confirmation = await narrator.generate_confirmation_request(
        action={"type": "delete_file", "target": "document.pdf"},
        risks=["Perte de données", "Action irréversible"],
        benefits=["Libère de l'espace"]
    )
    
    print(f"Confirmation: {confirmation}")
    print()
    
    await narrator.close()
    
    print("=" * 70)
    print("✅ Tests terminés!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_narrator())
