"""
HyDE (Hypothetical Document Embeddings) - Phase 3.5 Week 4
Ameliore la recherche pour les requetes vagues via documents hypothetiques.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib


class QueryType(Enum):
    """Types de requetes pour HyDE."""
    VAGUE = "vague"
    CONCEPTUAL = "conceptual"
    EXPLORATORY = "exploratory"
    SPECIFIC = "specific"


@dataclass
class HypotheticalDocument:
    """Represente un document hypothetique genere."""
    content: str
    query_original: str
    generation_method: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "query_original": self.query_original,
            "generation_method": self.generation_method,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class HyDEResult:
    """Resultat de l'expansion HyDE."""
    original_query: str
    hypothetical_docs: List[HypotheticalDocument]
    expanded_queries: List[str]
    query_type: QueryType
    generation_time: float
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "hypothetical_docs": [doc.to_dict() for doc in self.hypothetical_docs],
            "expanded_queries": self.expanded_queries,
            "query_type": self.query_type.value,
            "generation_time": self.generation_time,
            "success": self.success,
            "error": self.error
        }


class HyDE:
    """HyDE pour ameliorer les requetes vagues."""
    
    TEMPLATES = {
        QueryType.VAGUE: [
            "Pour repondre a cette question, il faut comprendre que {query}. Voici une explication detaillee.",
            "La question '{query}' peut etre interpretee de plusieurs facons. Voici les aspects principaux.",
            "Concernant {query}, les elements cles sont les suivants."
        ],
        QueryType.CONCEPTUAL: [
            "Le concept de {query} repose sur plusieurs principes fondamentaux.",
            "D'un point de vue theorique, {query} s'explique par les mecanismes suivants.",
            "La theorie derriere {query} inclut plusieurs aspects importants."
        ],
        QueryType.EXPLORATORY: [
            "En explorant {query}, on decouvre plusieurs dimensions interessantes.",
            "Pour approfondir {query}, il est utile d'examiner differents angles.",
            "L'analyse de {query} revele plusieurs facettes a considerer."
        ]
    }
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        num_docs: int = 3,
        max_doc_length: int = 500,
        cache_enabled: bool = True,
        timeout: float = 2.0
    ):
        self.llm_client = llm_client
        self.num_docs = num_docs
        self.max_doc_length = max_doc_length
        self.cache_enabled = cache_enabled
        self.timeout = timeout
        self._cache: Dict[str, HyDEResult] = {}
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "generation_time_total": 0.0,
            "llm_generations": 0,
            "template_generations": 0
        }
    
    def _get_query_hash(self, query: str) -> str:
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def _detect_query_type(self, query: str) -> QueryType:
        query_lower = query.lower().strip()
        
        # Specific: requete longue et detaillee (check first)
        if len(query_lower.split()) > 10 and any(
            word in query_lower for word in ["precisement", "exactement", "specifiquement"]
        ):
            return QueryType.SPECIFIC
        
        # Vague (queries TRES courtes first - priority)
        if len(query_lower.split()) <= 3:
            return QueryType.VAGUE
        
        # Conceptuelle (check before other types)
        if any(word in query_lower for word in [
            "theorie", "concept", "principe", "fondement", "definition",
            "qu'est-ce que", "expliquer"
        ]):
            return QueryType.CONCEPTUAL
        
        # Exploratoire
        if any(word in query_lower for word in [
            "explorer", "decouvrir", "possibilites", "options", "alternatives"
        ]):
            return QueryType.EXPLORATORY
        
        # Vague (fallback for interrogative words)
        if any(word in query_lower for word in ["comment", "quoi", "ça", "ca", "truc", "chose", "pourquoi"]):
            return QueryType.VAGUE
        
        return QueryType.VAGUE
        
        if any(word in query_lower for word in [
            "explorer", "decouvrir", "possibilites", "options", "alternatives"
        ]):
            return QueryType.EXPLORATORY
        
        if len(query_lower.split()) <= 5 or any(
            word in query_lower for word in ["comment", "quoi", "ça", "ca", "truc", "chose"]
        ):
            return QueryType.VAGUE
        
        return QueryType.VAGUE
    
    def _generate_with_templates(self, query: str, query_type: QueryType) -> List[str]:
        templates = self.TEMPLATES.get(query_type, self.TEMPLATES[QueryType.VAGUE])
        docs = []
        # Generate up to num_docs, but limited by available templates
        num_to_generate = min(self.num_docs, len(templates))
        for template in templates[:num_to_generate]:
            doc = template.format(query=query)
            docs.append(doc[:self.max_doc_length])
        
        # If num_docs > len(templates), reuse templates
        while len(docs) < self.num_docs:
            template = templates[len(docs) % len(templates)]
            doc = template.format(query=query)
            docs.append(doc[:self.max_doc_length])
        
        self.stats["template_generations"] += 1
        return docs
    
    def _extract_alternative_queries(self, query: str, hypothetical_docs: List[str]) -> List[str]:
        queries = []
        query_words = query.lower().split()
        stop_words = {"comment", "quoi", "que", "quel", "quelle", "pourquoi", 
                      "est-ce", "c'est", "ça", "ca", "truc", "chose"}
        meaningful_words = [w for w in query_words if w not in stop_words]
        
        if meaningful_words:
            queries.append(" ".join(meaningful_words))
            if "comment" in query_words:
                queries.append(f"fonctionnement {' '.join(meaningful_words)}")
            queries.append(f"explication {' '.join(meaningful_words)}")
        
        all_words = " ".join(hypothetical_docs).lower().split()
        word_freq = {}
        for word in all_words:
            if len(word) > 4:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_words:
            queries.append(" ".join([w[0] for w in top_words]))
        
        queries = list(dict.fromkeys(queries))
        return queries[:5]
    
    def expand_query(self, query: str) -> HyDEResult:
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        query_hash = self._get_query_hash(query)
        if self.cache_enabled and query_hash in self._cache:
            self.stats["cache_hits"] += 1
            cached_result = self._cache[query_hash]
            cached_result.generation_time = 0.0
            return cached_result
        
        try:
            query_type = self._detect_query_type(query)
            doc_texts = self._generate_with_templates(query, query_type)
            
            hypothetical_docs = [
                HypotheticalDocument(
                    content=doc,
                    query_original=query,
                    generation_method="template",
                    confidence=0.7,
                    metadata={"query_type": query_type.value, "doc_index": i}
                )
                for i, doc in enumerate(doc_texts)
            ]
            
            expanded_queries = self._extract_alternative_queries(query, doc_texts)
            generation_time = time.time() - start_time
            self.stats["generation_time_total"] += generation_time
            
            result = HyDEResult(
                original_query=query,
                hypothetical_docs=hypothetical_docs,
                expanded_queries=expanded_queries,
                query_type=query_type,
                generation_time=generation_time,
                success=True
            )
            
            if self.cache_enabled:
                self._cache[query_hash] = result
            
            return result
            
        except Exception as e:
            generation_time = time.time() - start_time
            return HyDEResult(
                original_query=query,
                hypothetical_docs=[],
                expanded_queries=[],
                query_type=QueryType.VAGUE,
                generation_time=generation_time,
                success=False,
                error=str(e)
            )
    
    async def expand_query_async(self, query: str) -> HyDEResult:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.expand_query, query)
        return result
    
    def expand_batch(self, queries: List[str]) -> List[HyDEResult]:
        return [self.expand_query(q) for q in queries]
    
    async def expand_batch_async(self, queries: List[str]) -> List[HyDEResult]:
        tasks = [self.expand_query_async(q) for q in queries]
        return await asyncio.gather(*tasks)
    
    def get_stats(self) -> Dict[str, Any]:
        total_queries = self.stats["total_queries"]
        cache_hits = self.stats["cache_hits"]
        
        return {
            "total_queries": total_queries,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hits / total_queries if total_queries > 0 else 0.0,
            "average_generation_time": (
                self.stats["generation_time_total"] / (total_queries - cache_hits)
                if (total_queries - cache_hits) > 0 else 0.0
            ),
            "llm_generations": self.stats["llm_generations"],
            "template_generations": self.stats["template_generations"]
        }
    
    def clear_cache(self):
        self._cache.clear()


def expand_vague_query(query: str, num_docs: int = 3, llm_client: Optional[Any] = None) -> HyDEResult:
    hyde = HyDE(llm_client=llm_client, num_docs=num_docs)
    return hyde.expand_query(query)


if __name__ == "__main__":
    print("=== HyDE Manual Tests ===\n")
    
    hyde = HyDE(num_docs=3, cache_enabled=True)
    
    print("Test 1: Query vague")
    result = hyde.expand_query("comment ca marche?")
    print(f"  Query type: {result.query_type.value}")
    print(f"  Hypothetical docs: {len(result.hypothetical_docs)}")
    print(f"  Expanded queries: {result.expanded_queries}")
    print(f"  Generation time: {result.generation_time:.3f}s")
    print(f"  Success: {result.success}\n")
    
    print("Test 2: Query conceptuelle")
    result = hyde.expand_query("qu'est-ce que le machine learning?")
    print(f"  Query type: {result.query_type.value}")
    print(f"  Hypothetical docs: {len(result.hypothetical_docs)}")
    print(f"  First doc preview: {result.hypothetical_docs[0].content[:80]}...")
    print(f"  Expanded queries: {result.expanded_queries}\n")
    
    print("Test 3: Cache hit")
    result_cached = hyde.expand_query("comment ca marche?")
    print(f"  Generation time (cached): {result_cached.generation_time:.3f}s")
    print(f"  Cache hit: {result_cached.generation_time == 0.0}\n")
    
    print("Test 4: Batch expansion")
    queries = ["pourquoi?", "c'est quoi ca?", "comment faire?"]
    results = hyde.expand_batch(queries)
    print(f"  Batch size: {len(results)}")
    print(f"  All successful: {all(r.success for r in results)}\n")
    
    print("Stats finales:")
    stats = hyde.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
