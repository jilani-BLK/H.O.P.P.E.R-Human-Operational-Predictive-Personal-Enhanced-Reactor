"""
HOPPER - Moteur LLM
Serveur d'inférence pour le modèle de langage
Phase 2: Intégration complète avec Ollama et Knowledge Base
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import httpx
from loguru import logger

# Import Knowledge Base
try:
    from knowledge_base import KnowledgeBase
except ImportError:
    logger.warning("knowledge_base module non trouvé")
    KnowledgeBase = None

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
CONTEXT_SIZE = int(os.getenv("LLM_CONTEXT_SIZE", "4096"))

# Client HTTP pour Ollama
ollama_client = None

# Instance Knowledge Base
kb = None


class GenerateRequest(BaseModel):
    """Requête de génération"""
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95
    stop: List[str] = ["User:", "Utilisateur:", "\n\n"]


class GenerateResponse(BaseModel):
    """Réponse de génération"""
    text: str
    tokens_generated: int
    finish_reason: str
    model: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    global ollama_client, kb
    
    # Startup
    logger.info("🚀 Démarrage du moteur LLM (Ollama)")
    
    # Initialiser client HTTP Ollama
    ollama_client = httpx.AsyncClient(timeout=60.0)
    
    # Vérifier Ollama disponible
    try:
        response = await ollama_client.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            logger.success(f"✅ Ollama connecté - Modèles disponibles: {model_names}")
            
            if OLLAMA_MODEL not in model_names and f"{OLLAMA_MODEL}:latest" not in model_names:
                logger.warning(f"⚠️ Modèle {OLLAMA_MODEL} non trouvé - tentative de pull...")
        else:
            logger.error(f"❌ Ollama non disponible sur {OLLAMA_HOST}")
    except Exception as e:
        logger.error(f"❌ Erreur connexion Ollama: {e}")
        logger.info("💡 Assurez-vous qu'Ollama tourne: ollama serve")
    
    # Initialiser Knowledge Base
    if KnowledgeBase:
        kb_path = os.getenv("KB_PERSIST_PATH", "./data/vector_store")
        try:
            kb = KnowledgeBase(persist_path=kb_path)
            logger.success("✅ Knowledge Base initialisée")
        except Exception as e:
            logger.error(f"❌ Erreur init KB: {e}")
    
    yield
    
    # Shutdown
    await ollama_client.aclose()
    logger.info("🛑 Arrêt du moteur LLM")


app = FastAPI(
    title="HOPPER LLM Engine",
    lifespan=lifespan
)


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Vérification de santé"""
    ollama_available = ollama_client is not None
    return {
        "status": "healthy" if ollama_available else "degraded",
        "model": OLLAMA_MODEL,
        "ollama_host": OLLAMA_HOST,
        "context_size": CONTEXT_SIZE,
        "kb_available": kb is not None,
        "mode": "ollama"
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Génère une réponse à partir d'un prompt via Ollama
    
    Args:
        request: Paramètres de génération (prompt, max_tokens, temperature)
        
    Returns:
        Réponse générée par le LLM
    """
    logger.info(f"📥 Requête génération: {len(request.prompt)} chars, max_tokens={request.max_tokens}")
    
    if ollama_client is None:
        raise HTTPException(status_code=503, detail="Ollama non disponible")
    
    try:
        # Génération avec Ollama
        logger.debug(f"🔄 Appel Ollama: {OLLAMA_MODEL}")
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens,
                "stop": request.stop
            }
        }
        
        response = await ollama_client.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=60.0
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur Ollama: {response.text}"
            )
        
        data = response.json()
        response_text = data.get("response", "").strip()
        tokens_generated = data.get("eval_count", 0)
        
        logger.success(f"✅ Généré {tokens_generated} tokens")
        
        return GenerateResponse(
            text=response_text,
            tokens_generated=tokens_generated,
            finish_reason="stop" if data.get("done") else "length",
            model=OLLAMA_MODEL
        )
        
    except httpx.TimeoutException:
        logger.error("❌ Timeout Ollama")
        raise HTTPException(status_code=504, detail="Timeout génération LLM")
    except Exception as e:
        logger.error(f"❌ Erreur génération: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur LLM: {str(e)}")


@app.post("/embed")
async def embed_text(text: str) -> Dict[str, Any]:
    """
    Crée un embedding vectoriel d'un texte
    (Pour la base de connaissances)
    """
    # TODO: Implémenter avec sentence-transformers
    return {
        "embedding": [0.0] * 768,  # Placeholder
        "dimension": 768
    }


# ===== KNOWLEDGE BASE ENDPOINTS =====

class LearnRequest(BaseModel):
    """Requête d'apprentissage KB"""
    text: str


class SearchRequest(BaseModel):
    """Requête de recherche KB"""
    query: str
    k: int = 3
    threshold: float = 0.5


@app.post("/learn")
async def learn(request: LearnRequest) -> Dict[str, Any]:
    """
    Apprend un nouveau fait/document dans la KB
    
    Args:
        request: Texte à apprendre
        
    Returns:
        Statut et nombre total de documents
    """
    if kb is None:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponible")
    
    logger.info(f"📚 Apprentissage: {request.text[:100]}...")
    
    try:
        count = kb.add([request.text])
        stats = kb.get_stats()
        
        logger.success(f"✅ Document appris, total: {stats['total_documents']}")
        
        return {
            "status": "success",
            "message": f"Fait appris: {request.text[:50]}...",
            "total_knowledge": stats['total_documents'],
            "added": count
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur apprentissage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_knowledge(request: SearchRequest) -> Dict[str, Any]:
    """
    Cherche dans la knowledge base
    
    Args:
        request: Query, k résultats, threshold similarité
        
    Returns:
        Liste de résultats avec scores
    """
    if kb is None:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponible")
    
    logger.info(f"🔍 Recherche KB: '{request.query}' (k={request.k}, threshold={request.threshold})")
    
    try:
        results = kb.search(request.query, k=request.k, threshold=request.threshold)
        
        logger.info(f"✅ {len(results)} résultats trouvés")
        
        return {
            "query": request.query,
            "results": [
                {"text": text, "score": score}
                for text, score in results
            ],
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge/stats")
async def knowledge_stats() -> Dict[str, Any]:
    """
    Statistiques de la Knowledge Base
    
    Returns:
        Stats KB (total docs, dimension, etc.)
    """
    if kb is None:
        return {"available": False}
    
    return {
        "available": True,
        **kb.get_stats()
    }


@app.delete("/knowledge/clear")
async def clear_knowledge():
    """
    Vide la Knowledge Base
    
    Returns:
        Confirmation
    """
    if kb is None:
        raise HTTPException(status_code=503, detail="Knowledge Base non disponible")
    
    kb.clear()
    logger.info("🗑️ Knowledge Base vidée")
    
    return {"status": "success", "message": "Knowledge Base vidée"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LLM_SERVICE_PORT", 5001))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
