"""
HOPPER - Knowledge Base avec Qdrant
Base de connaissances vectorielle avec Qdrant (Phase 2 concrétisation)
Fallback vers FAISS si Qdrant indisponible
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from loguru import logger
import os

# Qdrant client
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    logger.warning("qdrant-client non installé, fallback FAISS")
    QDRANT_AVAILABLE = False
    QdrantClient = None

# Sentence Transformers pour embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers non installé")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

# FAISS fallback
try:
    import faiss
    import pickle
    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("faiss non installé")
    FAISS_AVAILABLE = False
    faiss = None


class KnowledgeBase:
    """
    Base de connaissances vectorielle
    Priorité: Qdrant > FAISS > Simulation
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        persist_path: Optional[str] = None,
        qdrant_host: Optional[str] = None,
        qdrant_port: int = 6333,
        collection_name: str = "hopper_knowledge"
    ):
        """
        Initialize Knowledge Base
        
        Args:
            embedding_model: Modèle sentence-transformers
            persist_path: Chemin pour persistence FAISS (fallback)
            qdrant_host: Host Qdrant (None = auto-detect from env)
            qdrant_port: Port Qdrant
            collection_name: Nom collection Qdrant
        """
        self.persist_path = persist_path
        self.collection_name = collection_name
        self.dimension = 384  # all-MiniLM-L6-v2
        
        # Détecter host Qdrant depuis env si non spécifié
        if qdrant_host is None:
            qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        
        # Initialiser encoder
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ Mode simulation KB - sentence-transformers manquant")
            self.simulation_mode = True
            self.texts = []
            return
        
        self.simulation_mode = False
        
        logger.info(f"📥 Chargement modèle embeddings: {embedding_model}")
        try:
            self.encoder = SentenceTransformer(embedding_model)  # type: ignore
            self.dimension = self.encoder.get_sentence_embedding_dimension()
            logger.success(f"✅ Modèle chargé, dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            self.simulation_mode = True
            self.texts = []
            return
        
        # Tenter connexion Qdrant
        self.use_qdrant = False
        self.qdrant_client = None
        
        if QDRANT_AVAILABLE:
            try:
                self.qdrant_client = QdrantClient(  # type: ignore
                    host=self.qdrant_host,
                    port=self.qdrant_port,
                    timeout=5
                )
                
                # Vérifier connexion
                collections = self.qdrant_client.get_collections()
                logger.success(f"✅ Qdrant connecté: {self.qdrant_host}:{self.qdrant_port}")
                
                # Créer ou récupérer collection
                self._ensure_collection()
                
                self.use_qdrant = True
                logger.info("✅ Mode: QDRANT (production)")
                
            except Exception as e:
                logger.warning(f"⚠️ Qdrant indisponible: {e}")
                logger.info("→ Fallback vers FAISS")
        
        # Fallback FAISS si Qdrant indisponible
        if not self.use_qdrant:
            if FAISS_AVAILABLE:
                logger.info("📊 Mode: FAISS (fallback)")
                self.index = faiss.IndexFlatIP(self.dimension)
                self.texts = []
                
                # Charger FAISS persisté si existe
                if persist_path and os.path.exists(f"{persist_path}/faiss.index"):
                    try:
                        self._load_faiss(persist_path)
                    except Exception as e:
                        logger.warning(f"Impossible de charger FAISS: {e}")
            else:
                logger.error("❌ Ni Qdrant ni FAISS disponibles - mode simulation")
                self.simulation_mode = True
                self.texts = []
    
    def _ensure_collection(self):
        """Crée la collection Qdrant si elle n'existe pas"""
        try:
            collections = self.qdrant_client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                logger.info(f"📦 Création collection Qdrant: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.success(f"✅ Collection créée: {self.collection_name}")
            else:
                logger.info(f"✅ Collection existante: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Erreur création collection: {e}")
            raise
    
    def add(self, texts: List[str]) -> int:
        """Ajoute des documents à la KB"""
        if not texts:
            return 0
        
        # Mode simulation
        if self.simulation_mode:
            if not hasattr(self, 'texts'):
                self.texts = []
            self.texts.extend(texts)
            logger.info(f"[SIMULATION] Ajouté {len(texts)} documents")
            return len(texts)
        
        logger.info(f"📝 Ajout {len(texts)} documents à la KB")
        
        try:
            # Générer embeddings
            embeddings = self.encoder.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True  # Normalisation pour cosine
            )
            
            # Qdrant
            if self.use_qdrant:
                # Récupérer dernier ID
                try:
                    scroll_result = self.qdrant_client.scroll(
                        collection_name=self.collection_name,
                        limit=1,
                        with_payload=False,
                        with_vectors=False
                    )
                    if scroll_result[0]:
                        last_id = max([p.id for p in scroll_result[0]])
                        start_id = last_id + 1
                    else:
                        start_id = 1
                except:
                    start_id = 1
                
                # Créer points
                points = [
                    PointStruct(
                        id=start_id + i,
                        vector=embedding.tolist(),
                        payload={"text": text}
                    )
                    for i, (text, embedding) in enumerate(zip(texts, embeddings))
                ]
                
                # Upsert dans Qdrant
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                # Stats
                count = self.qdrant_client.count(collection_name=self.collection_name).count
                logger.success(f"✅ KB Qdrant size: {count} documents")
                
            # FAISS fallback
            else:
                # Normaliser pour cosine
                import faiss as f
                f.normalize_L2(embeddings)
                
                if self.index is not None:
                    self.index.add(embeddings.astype('float32'))  # type: ignore
                self.texts.extend(texts)
                
                logger.success(f"✅ KB FAISS size: {len(self.texts)} documents")
                
                # Sauvegarder
                if self.persist_path:
                    self._save_faiss(self.persist_path)
            
            return len(texts)
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout KB: {e}")
            return 0
    
    def search(self, query: str, k: int = 3, threshold: float = 0.5) -> List[Tuple[str, float]]:
        """Cherche les k documents les plus similaires"""
        
        # Mode simulation
        if self.simulation_mode:
            if not hasattr(self, 'texts') or len(self.texts) == 0:
                return []
            query_lower = query.lower()
            results = []
            for text in self.texts:
                if any(word in text.lower() for word in query_lower.split()):
                    results.append((text, 0.8))
            logger.info(f"[SIMULATION] Recherche '{query}': {len(results)} résultats")
            return results[:k]
        
        try:
            # Encoder query
            query_embedding = self.encoder.encode(
                [query],
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            
            # Qdrant
            if self.use_qdrant:
                results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding[0].tolist(),
                    limit=k,
                    score_threshold=threshold
                )
                
                formatted = [
                    (hit.payload["text"], hit.score)
                    for hit in results
                ]
                
                logger.debug(f"🔍 Qdrant '{query}': {len(formatted)} résultats")
                return formatted
            
            # FAISS fallback
            else:
                if len(self.texts) == 0:
                    return []
                
                import faiss as f
                f.normalize_L2(query_embedding)
                
                k_search = min(k, len(self.texts))
                if self.index is not None:
                    scores, indices = self.index.search(query_embedding.astype('float32'), k_search)  # type: ignore
                else:
                    return []
                
                results = [
                    (self.texts[idx], float(score))
                    for idx, score in zip(indices[0], scores[0])
                    if score >= threshold
                ]
                
                logger.debug(f"🔍 FAISS '{query}': {len(results)} résultats")
                return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche KB: {e}")
            return []
    
    def clear(self):
        """Vide la KB"""
        try:
            if self.use_qdrant:
                self.qdrant_client.delete_collection(collection_name=self.collection_name)
                self._ensure_collection()
                logger.info("🗑️ KB Qdrant vidée")
            elif hasattr(self, 'index'):
                import faiss as f
                self.index = f.IndexFlatIP(self.dimension)
                self.texts = []
                if self.persist_path:
                    self._save_faiss(self.persist_path)
                logger.info("🗑️ KB FAISS vidée")
            else:
                self.texts = []
                logger.info("🗑️ KB simulation vidée")
        except Exception as e:
            logger.error(f"❌ Erreur clear KB: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne statistiques KB"""
        if self.use_qdrant:
            try:
                count = self.qdrant_client.count(collection_name=self.collection_name).count
                return {
                    "backend": "qdrant",
                    "total_documents": count,
                    "embedding_dimension": self.dimension,
                    "collection_name": self.collection_name,
                    "qdrant_host": self.qdrant_host
                }
            except:
                return {"backend": "qdrant", "error": "unavailable"}
        
        elif hasattr(self, 'index'):
            return {
                "backend": "faiss",
                "total_documents": len(self.texts),
                "embedding_dimension": self.dimension,
                "persist_path": self.persist_path
            }
        
        else:
            return {
                "backend": "simulation",
                "total_documents": len(self.texts) if hasattr(self, 'texts') else 0,
                "embedding_dimension": self.dimension
            }
    
    def _save_faiss(self, path: str):
        """Sauvegarde FAISS sur disque"""
        try:
            os.makedirs(path, exist_ok=True)
            import faiss as f
            import pickle
            f.write_index(self.index, f"{path}/faiss.index")
            with open(f"{path}/texts.pkl", 'wb') as file:
                pickle.dump(self.texts, file)
            logger.info(f"💾 FAISS sauvegardé: {path}")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde FAISS: {e}")
    
    def _load_faiss(self, path: str):
        """Charge FAISS depuis disque"""
        try:
            import faiss as f
            import pickle
            self.index = f.read_index(f"{path}/faiss.index")
            with open(f"{path}/texts.pkl", 'rb') as file:
                self.texts = pickle.load(file)
            logger.success(f"📂 FAISS chargé: {len(self.texts)} documents")
        except Exception as e:
            logger.error(f"❌ Erreur chargement FAISS: {e}")
            raise
