"""
HOPPER - Knowledge Base
Base de connaissances vectorielle avec FAISS et Sentence Transformers
Phase 2: RAG (Retrieval-Augmented Generation)
"""

import faiss  # type: ignore[import-not-found,import-untyped]
import numpy as np  # type: ignore[import-not-found]
from typing import List, Tuple, Optional
from loguru import logger
import pickle
import os

try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
except ImportError:
    logger.warning("sentence-transformers non installé")
    SentenceTransformer = None  # type: ignore[assignment, misc]


class KnowledgeBase:
    """
    Base de connaissances vectorielle utilisant FAISS pour la recherche sémantique
    """
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", persist_path: Optional[str] = None):
        """
        Initialize Knowledge Base
        
        Args:
            embedding_model: Modèle sentence-transformers (défaut: all-MiniLM-L6-v2, 384 dims, multilangue)
            persist_path: Chemin pour persistence (None = in-memory only)
        """
        self.persist_path = persist_path
        self.encoder = None
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
        # Mode simulation si sentence-transformers pas installé
        if SentenceTransformer is None:
            logger.warning("⚠️ Mode simulation KB - sentence-transformers manquant")
            self.simulation_mode = True
            self.texts = []
            return
        
        self.simulation_mode = False
        
        # Charger modèle embeddings
        logger.info(f"📥 Chargement modèle embeddings: {embedding_model}")
        try:
            self.encoder = SentenceTransformer(embedding_model)
            self.dimension = self.encoder.get_sentence_embedding_dimension()
            logger.success(f"✅ Modèle chargé, dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            self.simulation_mode = True
            self.texts = []
            return
        
        # FAISS index (Inner Product pour similarité cosine)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Stockage textes originaux
        self.texts = []
        
        # Charger KB persistée si existe
        if persist_path and os.path.exists(f"{persist_path}/faiss.index"):
            try:
                self.load(persist_path)
            except Exception as e:
                logger.warning(f"Impossible de charger KB: {e}")
        
        logger.info("✅ Knowledge Base initialisée")
    
    def add(self, texts: List[str]) -> int:
        """
        Ajoute des documents à la KB
        
        Args:
            texts: Liste de textes à ajouter
            
        Returns:
            Nombre de documents ajoutés
        """
        if not texts:
            return 0
        
        # Mode simulation
        if self.simulation_mode:
            self.texts.extend(texts)
            logger.info(f"[SIMULATION] Ajouté {len(texts)} documents")
            return len(texts)
        
        logger.info(f"📝 Ajout {len(texts)} documents à la KB")
        
        try:
            # Générer embeddings
            embeddings = self.encoder.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Normaliser pour similarité cosine
            faiss.normalize_L2(embeddings)
            
            # Ajouter à l'index FAISS
            self.index.add(embeddings.astype('float32'))  # type: ignore[call-arg]
            
            # Stocker textes
            self.texts.extend(texts)
            
            logger.success(f"✅ KB size: {len(self.texts)} documents")
            
            # Sauvegarder si persistence activée
            if self.persist_path:
                self.save(self.persist_path)
            
            return len(texts)
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout KB: {e}")
            return 0
    
    def search(self, query: str, k: int = 3, threshold: float = 0.5) -> List[Tuple[str, float]]:
        """
        Cherche les k documents les plus similaires
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats
            threshold: Seuil de similarité minimum (0-1)
            
        Returns:
            [(texte, score), ...] triés par score décroissant
        """
        if len(self.texts) == 0:
            return []
        
        # Mode simulation
        if self.simulation_mode:
            # Recherche simple par mots-clés
            query_lower = query.lower()
            results = []
            for text in self.texts:
                if any(word in text.lower() for word in query_lower.split()):
                    results.append((text, 0.8))  # Score factice
            logger.info(f"[SIMULATION] Recherche '{query}': {len(results)} résultats")
            return results[:k]
        
        try:
            # Encoder query
            query_embedding = self.encoder.encode(
                [query],
                convert_to_numpy=True,
                show_progress_bar=False
            )
            faiss.normalize_L2(query_embedding)
            
            # Recherche
            k_search = min(k, len(self.texts))
            scores, indices = self.index.search(query_embedding.astype('float32'), k_search)  # type: ignore[call-arg]
            
            # Filtrer par threshold et formater résultats
            results = [
                (self.texts[idx], float(score))
                for idx, score in zip(indices[0], scores[0])
                if score >= threshold
            ]
            
            logger.debug(f"🔍 Recherche '{query}': {len(results)} résultats (threshold={threshold})")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche KB: {e}")
            return []
    
    def clear(self):
        """Vide la KB"""
        if self.simulation_mode:
            self.texts = []
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.texts = []
        
        logger.info("🗑️ KB vidée")
        
        if self.persist_path:
            self.save(self.persist_path)
    
    def save(self, path: str):
        """
        Sauvegarde la KB sur disque
        
        Args:
            path: Dossier de sauvegarde
        """
        if self.simulation_mode:
            return
        
        try:
            os.makedirs(path, exist_ok=True)
            
            # Sauver index FAISS
            faiss.write_index(self.index, f"{path}/faiss.index")
            
            # Sauver textes
            with open(f"{path}/texts.pkl", 'wb') as f:
                pickle.dump(self.texts, f)
            
            logger.info(f"💾 KB sauvegardée: {path} ({len(self.texts)} documents)")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde KB: {e}")
    
    def load(self, path: str):
        """
        Charge la KB depuis disque
        
        Args:
            path: Dossier source
        """
        if self.simulation_mode:
            return
        
        try:
            # Charger index FAISS
            self.index = faiss.read_index(f"{path}/faiss.index")
            
            # Charger textes
            with open(f"{path}/texts.pkl", 'rb') as f:
                self.texts = pickle.load(f)
            
            logger.success(f"📂 KB chargée: {len(self.texts)} documents depuis {path}")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement KB: {e}")
            raise
    
    def get_stats(self) -> dict:
        """
        Retourne statistiques KB
        
        Returns:
            Dict avec stats
        """
        return {
            "total_documents": len(self.texts),
            "embedding_dimension": self.dimension,
            "simulation_mode": self.simulation_mode,
            "persist_path": self.persist_path,
            "has_persistence": self.persist_path is not None
        }
