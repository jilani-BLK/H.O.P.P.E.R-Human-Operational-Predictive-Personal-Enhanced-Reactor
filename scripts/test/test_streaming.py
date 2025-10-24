#!/usr/bin/env python3
"""
Test du streaming de pensées HOPPER
"""

import httpx
import json
import asyncio


async def test_streaming():
    """Test du streaming SSE"""
    url = "http://localhost:5050/command/stream"
    
    data = {
        "text": "Quelle est la capitale de France?",
        "user_id": "test_user"
    }
    
    print("🚀 Envoi de la commande:", data["text"])
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", url, json=data) as response:
            print(f"📡 Status: {response.status_code}")
            print(f"📡 Headers: {response.headers.get('content-type')}")
            print("=" * 60)
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    # Extraire le JSON après "data: "
                    json_str = line[6:]
                    try:
                        thought = json.loads(json_str)
                        
                        # Afficher la pensée
                        thought_type = thought.get("type", "unknown")
                        message = thought.get("message", "")
                        
                        print(f"{thought_type.upper()}: {message}")
                        
                        # Si c'est une réponse finale, c'est fini
                        if thought_type in ["response", "done", "error"]:
                            print("=" * 60)
                            print("✅ Streaming terminé")
                            break
                    except json.JSONDecodeError as e:
                        print(f"❌ Erreur JSON: {e}")


if __name__ == "__main__":
    asyncio.run(test_streaming())
