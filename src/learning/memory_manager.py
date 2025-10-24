"""
Gestionnaire de mémoire à long terme HOPPER
Stockage vectoriel local pour conversations, connaissances, préférences
"""

import json
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pickle


class MemoryType(Enum):
    """Types de mémoires"""
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    PREFERENCE = "preference"
    EXPERIENCE = "experience"
    DOCUMENT = "document"
    FEEDBACK = "feedback"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class Memory:
    """Unité de mémoire"""
    id: str
    type: MemoryType
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5  # 0-1
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversion en dictionnaire pour stockage"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "tags": self.tags,
            "source": self.source
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Memory':
        """Création depuis dictionnaire"""
        return Memory(
            id=data["id"],
            type=MemoryType(data["type"]),
            content=data["content"],
            embedding=np.array(data["embedding"]) if data.get("embedding") else None,
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=data.get("importance", 0.5),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            tags=data.get("tags", []),
            source=data.get("source")
        )


@dataclass
class MemoryQuery:
    """Requête de recherche en mémoire"""
    query: str
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    min_importance: float = 0.0
    max_results: int = 10
    time_range: Optional[Tuple[datetime, datetime]] = None
    similarity_threshold: float = 0.7


@dataclass
class MemoryResult:
    """Résultat de recherche en mémoire"""
    memory: Memory
    similarity: float
    relevance_score: float


class MemoryManager:
    """Gestionnaire de mémoire à long terme avec stockage vectoriel"""
    
    def __init__(self, storage_dir: str = "data/memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Base de mémoires
        self.memories: Dict[str, Memory] = {}
        
        # Index vectoriel (simple, peut être remplacé par FAISS)
        self.vector_index: Dict[str, np.ndarray] = {}
        
        # Index par type
        self.type_index: Dict[MemoryType, List[str]] = {
            mt: [] for mt in MemoryType
        }
        
        # Index par tag
        self.tag_index: Dict[str, List[str]] = {}
        
        # Statistiques
        self.stats = {
            "total_memories": 0,
            "total_queries": 0,
            "average_similarity": 0.0,
            "most_accessed": []
        }
        
        # Charger les mémoires existantes
        self._load_memories()
    
    def _generate_id(self, content: str, type: MemoryType) -> str:
        """Génère un ID unique pour une mémoire"""
        timestamp = datetime.now().isoformat()
        data = f"{content}{type.value}{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """
        Embedding simple basé sur TF-IDF ou comptage
        À remplacer par un vrai modèle d'embedding (sentence-transformers)
        """
        # Pour l'instant, embedding très simple basé sur hash de mots
        words = text.lower().split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Vecteur de dimension fixe (128)
        vector = np.zeros(128)
        for i, word in enumerate(sorted(word_counts.keys())[:128]):
            vector[i] = word_counts[word]
        
        # Normalisation
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None
    ) -> Memory:
        """Ajoute une nouvelle mémoire"""
        
        # Générer ID et embedding
        memory_id = self._generate_id(content, memory_type)
        embedding = self._simple_embedding(content)
        
        # Créer la mémoire
        memory = Memory(
            id=memory_id,
            type=memory_type,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            importance=importance,
            tags=tags or [],
            source=source
        )
        
        # Stocker
        self.memories[memory_id] = memory
        
        # Ajouter au vecteur index (embedding toujours présent ici car créé juste avant)
        self.vector_index[memory_id] = embedding
        
        # Indexer par type
        self.type_index[memory_type].append(memory_id)
        
        # Indexer par tags
        for tag in memory.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(memory_id)
        
        # Mettre à jour stats
        self.stats["total_memories"] += 1
        
        # Sauvegarder
        self._save_memory(memory)
        
        return memory
    
    def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Recherche sémantique dans les mémoires"""
        
        self.stats["total_queries"] += 1
        
        # Générer embedding de la requête
        query_embedding = self._simple_embedding(query.query)
        
        # Filtrer par type si spécifié
        candidate_ids = set(self.memories.keys())
        if query.memory_types:
            type_candidates = set()
            for mt in query.memory_types:
                type_candidates.update(self.type_index[mt])
            candidate_ids &= type_candidates
        
        # Filtrer par tags si spécifié
        if query.tags:
            tag_candidates = set()
            for tag in query.tags:
                if tag in self.tag_index:
                    tag_candidates.update(self.tag_index[tag])
            candidate_ids &= tag_candidates
        
        # Calculer similarités
        results = []
        for memory_id in candidate_ids:
            memory = self.memories[memory_id]
            
            # Filtrer par importance
            if memory.importance < query.min_importance:
                continue
            
            # Filtrer par date si spécifié
            if query.time_range:
                start, end = query.time_range
                if not (start <= memory.timestamp <= end):
                    continue
            
            # Calculer similarité cosine
            memory_embedding = self.vector_index[memory_id]
            similarity = np.dot(query_embedding, memory_embedding)
            
            if similarity >= query.similarity_threshold:
                # Score de pertinence combinant similarité, importance et récence
                days_old = (datetime.now() - memory.timestamp).days
                recency_factor = 1.0 / (1.0 + days_old / 30.0)  # Décroit sur 30 jours
                
                relevance_score = (
                    0.5 * similarity +
                    0.3 * memory.importance +
                    0.2 * recency_factor
                )
                
                results.append(MemoryResult(
                    memory=memory,
                    similarity=float(similarity),
                    relevance_score=relevance_score
                ))
                
                # Mettre à jour accès
                memory.access_count += 1
                memory.last_accessed = datetime.now()
        
        # Trier par pertinence
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        # Limiter résultats
        results = results[:query.max_results]
        
        # Mettre à jour stats
        if results:
            avg_sim = sum(r.similarity for r in results) / len(results)
            self.stats["average_similarity"] = (
                0.9 * self.stats["average_similarity"] + 0.1 * avg_sim
            )
        
        return results
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Récupère une mémoire par ID"""
        memory = self.memories.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
        return memory
    
    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Memory]:
        """Met à jour une mémoire existante"""
        
        memory = self.memories.get(memory_id)
        if not memory:
            return None
        
        if content is not None:
            memory.content = content
            memory.embedding = self._simple_embedding(content)
            self.vector_index[memory_id] = memory.embedding
        
        if metadata is not None:
            memory.metadata.update(metadata)
        
        if importance is not None:
            memory.importance = importance
        
        if tags is not None:
            # Retirer des anciens index
            for tag in memory.tags:
                if tag in self.tag_index:
                    self.tag_index[tag].remove(memory_id)
            
            # Ajouter aux nouveaux index
            memory.tags = tags
            for tag in tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(memory_id)
        
        self._save_memory(memory)
        return memory
    
    def delete_memory(self, memory_id: str) -> bool:
        """Supprime une mémoire"""
        
        if memory_id not in self.memories:
            return False
        
        memory = self.memories[memory_id]
        
        # Retirer des index
        self.type_index[memory.type].remove(memory_id)
        for tag in memory.tags:
            if tag in self.tag_index:
                self.tag_index[tag].remove(memory_id)
        
        # Supprimer
        del self.memories[memory_id]
        del self.vector_index[memory_id]
        
        # Supprimer du disque
        memory_file = self.storage_dir / f"{memory_id}.json"
        if memory_file.exists():
            memory_file.unlink()
        
        self.stats["total_memories"] -= 1
        return True
    
    def get_related_memories(
        self,
        memory_id: str,
        max_results: int = 5,
        min_similarity: float = 0.7
    ) -> List[MemoryResult]:
        """Trouve les mémoires similaires à une mémoire donnée"""
        
        memory = self.memories.get(memory_id)
        if not memory:
            return []
        
        query = MemoryQuery(
            query=memory.content,
            max_results=max_results + 1,  # +1 car on va exclure la mémoire elle-même
            similarity_threshold=min_similarity
        )
        
        results = self.search(query)
        
        # Exclure la mémoire source
        results = [r for r in results if r.memory.id != memory_id]
        
        return results[:max_results]
    
    def consolidate_memories(self, min_importance: float = 0.3) -> int:
        """
        Consolide les mémoires en supprimant les moins importantes
        et en fusionnant les similaires
        """
        
        memories_to_delete = []
        
        # Identifier les mémoires peu importantes et peu accédées
        for memory_id, memory in self.memories.items():
            if memory.importance < min_importance and memory.access_count < 2:
                memories_to_delete.append(memory_id)
        
        # Supprimer
        for memory_id in memories_to_delete:
            self.delete_memory(memory_id)
        
        return len(memories_to_delete)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques d'utilisation"""
        
        # Mémoires les plus accédées
        most_accessed = sorted(
            self.memories.values(),
            key=lambda m: m.access_count,
            reverse=True
        )[:10]
        
        # Statistiques par type
        type_stats = {}
        for memory_type, ids in self.type_index.items():
            type_stats[memory_type.value] = len(ids)
        
        return {
            "total_memories": self.stats["total_memories"],
            "total_queries": self.stats["total_queries"],
            "average_similarity": self.stats["average_similarity"],
            "memories_by_type": type_stats,
            "total_tags": len(self.tag_index),
            "most_accessed": [
                {
                    "id": m.id,
                    "type": m.type.value,
                    "access_count": m.access_count,
                    "importance": m.importance
                }
                for m in most_accessed
            ]
        }
    
    def export_memories(self, output_file: str) -> None:
        """Exporte toutes les mémoires"""
        data = {
            "memories": [m.to_dict() for m in self.memories.values()],
            "stats": self.get_statistics(),
            "export_date": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def import_memories(self, input_file: str) -> int:
        """Importe des mémoires depuis un fichier"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for memory_data in data["memories"]:
            memory = Memory.from_dict(memory_data)
            self.memories[memory.id] = memory
            
            # Ajouter au vecteur index seulement si embedding existe
            if memory.embedding is not None:
                self.vector_index[memory.id] = memory.embedding
            
            self.type_index[memory.type].append(memory.id)
            
            for tag in memory.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(memory.id)
            
            count += 1
        
        self.stats["total_memories"] = len(self.memories)
        return count
    
    def _save_memory(self, memory: Memory) -> None:
        """Sauvegarde une mémoire sur disque"""
        memory_file = self.storage_dir / f"{memory.id}.json"
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _load_memories(self) -> None:
        """Charge les mémoires depuis le disque"""
        if not self.storage_dir.exists():
            return
        
        for memory_file in self.storage_dir.glob("*.json"):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                memory = Memory.from_dict(data)
                self.memories[memory.id] = memory
                
                # Ajouter au vecteur index seulement si embedding existe
                if memory.embedding is not None:
                    self.vector_index[memory.id] = memory.embedding
                
                self.type_index[memory.type].append(memory.id)
                
                for tag in memory.tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = []
                    self.tag_index[tag].append(memory.id)
                
            except Exception as e:
                print(f"Erreur lors du chargement de {memory_file}: {e}")
        
        self.stats["total_memories"] = len(self.memories)


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer le gestionnaire
    manager = MemoryManager()
    
    # Ajouter des mémoires
    m1 = manager.add_memory(
        "L'utilisateur préfère des explications détaillées avec exemples",
        MemoryType.PREFERENCE,
        importance=0.9,
        tags=["style", "détail"]
    )
    
    m2 = manager.add_memory(
        "Document interne sur l'architecture système analysé",
        MemoryType.DOCUMENT,
        metadata={"source": "docs/architecture.pdf"},
        importance=0.8,
        tags=["architecture", "documentation"]
    )
    
    m3 = manager.add_memory(
        "Erreur corrigée: ne pas utiliser sudo dans les scripts",
        MemoryType.ERROR,
        importance=0.7,
        tags=["erreur", "script", "sécurité"]
    )
    
    # Rechercher
    query = MemoryQuery(
        query="préférences utilisateur pour les réponses",
        memory_types=[MemoryType.PREFERENCE],
        max_results=5
    )
    
    results = manager.search(query)
    print(f"\n{len(results)} résultats trouvés:")
    for r in results:
        print(f"  - {r.memory.content} (similarité: {r.similarity:.2f})")
    
    # Statistiques
    stats = manager.get_statistics()
    print(f"\nStatistiques:")
    print(f"  Total mémoires: {stats['total_memories']}")
    print(f"  Total requêtes: {stats['total_queries']}")
