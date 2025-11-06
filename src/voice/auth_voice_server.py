"""
Voice Authentication Server - Phase 3
Service d'identification du locuteur avec SpeechBrain
"""

import io
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Auth Service", version="3.0.0")

# Configuration
PROFILES_DIR = Path("/app/profiles")
PROFILES_DIR.mkdir(exist_ok=True)

SIMILARITY_THRESHOLD = 0.75  # Seuil de confiance

# Global model
speaker_model = None
device = "cpu"


class EnrollRequest(BaseModel):
    user_id: str
    description: Optional[str] = None


class VerifyResponse(BaseModel):
    verified: bool
    user_id: Optional[str]
    confidence: float
    message: str


@app.on_event("startup")
async def load_model():
    """Charger le modèle SpeechBrain au démarrage"""
    global speaker_model, device
    
    logger.info("Loading SpeechBrain speaker recognition model")
    
    try:
        from speechbrain.pretrained import SpeakerRecognition
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        speaker_model = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="/app/models/speaker_rec",
            run_opts={"device": device}
        )
        
        logger.info(f"✅ SpeechBrain model loaded on {device}")
        
    except Exception as e:
        logger.error(f"❌ Failed to load SpeechBrain model: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    num_profiles = len(list(PROFILES_DIR.glob("*.pkl")))
    
    return {
        "status": "healthy" if speaker_model is not None else "unhealthy",
        "model": "ECAPA-TDNN",
        "device": device,
        "enrolled_users": num_profiles
    }


@app.post("/enroll")
async def enroll_user(
    user_id: str,
    samples: List[UploadFile] = File(...)
):
    """
    Enregistrer un profil vocal utilisateur
    
    Args:
        user_id: Identifiant utilisateur
        samples: Liste de fichiers audio (min 3, recommandé 5+)
    
    Returns:
        Confirmation d'enregistrement
    """
    if speaker_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(samples) < 3:
        raise HTTPException(
            status_code=400,
            detail="Minimum 3 audio samples required (5+ recommended)"
        )
    
    try:
        logger.info(f"Enrolling user {user_id} with {len(samples)} samples")
        
        embeddings = []
        
        for i, sample in enumerate(samples):
            audio_bytes = await sample.read()
            
            # Sauvegarder temporairement
            temp_path = f"/tmp/enroll_{user_id}_{i}.wav"
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)
            
            # Extraire embedding
            embedding = speaker_model.encode_batch(
                torch.tensor([temp_path])
            )
            embeddings.append(embedding.squeeze().cpu().numpy())
            
            logger.info(f"  Sample {i+1}/{len(samples)}: embedding shape {embedding.shape}")
        
        # Moyenner les embeddings
        avg_embedding = np.mean(embeddings, axis=0)
        
        # Sauvegarder profil
        profile_path = PROFILES_DIR / f"{user_id}.pkl"
        with open(profile_path, "wb") as f:
            pickle.dump({
                "user_id": user_id,
                "embedding": avg_embedding,
                "num_samples": len(samples)
            }, f)
        
        logger.info(f"✅ User {user_id} enrolled successfully")
        
        return {
            "success": True,
            "user_id": user_id,
            "num_samples": len(samples),
            "embedding_dim": avg_embedding.shape[0]
        }
        
    except Exception as e:
        logger.error(f"❌ Enrollment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify")
async def verify_speaker(audio: UploadFile = File(...)) -> VerifyResponse:
    """
    Vérifier l'identité du locuteur
    
    Args:
        audio: Fichier audio à vérifier
    
    Returns:
        Résultat de vérification avec confiance
    """
    if speaker_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Vérifier qu'il y a des profils enregistrés
    profiles = list(PROFILES_DIR.glob("*.pkl"))
    if not profiles:
        return VerifyResponse(
            verified=False,
            user_id=None,
            confidence=0.0,
            message="No enrolled users"
        )
    
    try:
        # Lire audio
        audio_bytes = await audio.read()
        temp_path = "/tmp/verify.wav"
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        
        # Extraire embedding
        test_embedding = speaker_model.encode_batch(
            torch.tensor([temp_path])
        ).squeeze().cpu().numpy()
        
        # Comparer avec tous les profils
        best_match = None
        best_similarity = 0.0
        
        for profile_path in profiles:
            with open(profile_path, "rb") as f:
                profile = pickle.load(f)
            
            # Similarité cosinus
            similarity = np.dot(test_embedding, profile["embedding"]) / (
                np.linalg.norm(test_embedding) * np.linalg.norm(profile["embedding"])
            )
            
            logger.info(f"  {profile['user_id']}: similarity = {similarity:.3f}")
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = profile["user_id"]
        
        # Vérification
        verified = best_similarity >= SIMILARITY_THRESHOLD
        
        if verified:
            message = f"Utilisateur reconnu: {best_match}"
        else:
            message = "Voix non reconnue"
        
        logger.info(f"✅ Verification: {message} (confidence: {best_similarity:.3f})")
        
        return VerifyResponse(
            verified=verified,
            user_id=best_match if verified else None,
            confidence=float(best_similarity),
            message=message
        )
        
    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profiles")
async def list_profiles():
    """Liste des profils vocaux enregistrés"""
    profiles = []
    
    for profile_path in PROFILES_DIR.glob("*.pkl"):
        with open(profile_path, "rb") as f:
            profile = pickle.load(f)
        
        profiles.append({
            "user_id": profile["user_id"],
            "num_samples": profile["num_samples"],
            "embedding_dim": profile["embedding"].shape[0]
        })
    
    return {"profiles": profiles, "count": len(profiles)}


@app.delete("/profile/{user_id}")
async def delete_profile(user_id: str):
    """Supprimer un profil vocal"""
    profile_path = PROFILES_DIR / f"{user_id}.pkl"
    
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile_path.unlink()
    logger.info(f"✅ Profile {user_id} deleted")
    
    return {"success": True, "user_id": user_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5007)
