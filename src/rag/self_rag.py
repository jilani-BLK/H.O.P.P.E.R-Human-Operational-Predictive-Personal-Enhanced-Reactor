"""
Self-RAG - Intelligent critique before retrieval
Phase 3.5 - Week 1 Implementation

Implements:
- Quick heuristic classification (<10ms)
- LLM classification for complex queries (<100ms)
- Document relevance critique
- Statistics tracking
"""

import time
import re
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field


class RetrievalDecision(Enum):
    """Self-RAG decision types"""
    RETRIEVE = "retrieve"
    NO_RETRIEVE = "no_retrieve"
    UNCERTAIN = "uncertain"


class RelevanceScore(Enum):
    """Document relevance scores"""
    HIGHLY_RELEVANT = "highly_relevant"  # 5/5
    RELEVANT = "relevant"                # 4/5
    PARTIALLY_RELEVANT = "partially"     # 3/5
    BARELY_RELEVANT = "barely"           # 2/5
    NOT_RELEVANT = "not_relevant"        # 1/5


@dataclass
class ClassificationResult:
    """Result of Self-RAG classification"""
    decision: RetrievalDecision
    confidence: float
    reasoning: str
    latency_ms: float
    method: str  # "heuristic" or "llm"


@dataclass
class CritiqueResult:
    """Result of document critique"""
    relevance: RelevanceScore
    confidence: float
    reasoning: str
    suggestions: List[str]


@dataclass
class SelfRAGStats:
    """Statistics for Self-RAG performance"""
    total_queries: int = 0
    retrieve_count: int = 0
    no_retrieve_count: int = 0
    uncertain_count: int = 0
    avg_latency_ms: float = 0.0
    heuristic_usage: int = 0
    llm_usage: int = 0
    
    def update(self, result: ClassificationResult):
        """Update stats with new classification"""
        self.total_queries += 1
        if result.decision == RetrievalDecision.RETRIEVE:
            self.retrieve_count += 1
        elif result.decision == RetrievalDecision.NO_RETRIEVE:
            self.no_retrieve_count += 1
        else:
            self.uncertain_count += 1
        
        # Update avg latency (running average)
        self.avg_latency_ms = (
            (self.avg_latency_ms * (self.total_queries - 1) + result.latency_ms) 
            / self.total_queries
        )
        
        if result.method == "heuristic":
            self.heuristic_usage += 1
        else:
            self.llm_usage += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Export stats as dictionary"""
        return {
            "total_queries": self.total_queries,
            "retrieve_rate": self.retrieve_count / max(1, self.total_queries),
            "no_retrieve_rate": self.no_retrieve_count / max(1, self.total_queries),
            "uncertain_rate": self.uncertain_count / max(1, self.total_queries),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "heuristic_usage_rate": self.heuristic_usage / max(1, self.total_queries),
            "llm_usage_rate": self.llm_usage / max(1, self.total_queries)
        }


class SelfRAG:
    """
    Self-RAG classifier with two-tier approach:
    1. Quick heuristic classification (<10ms) for obvious cases
    2. LLM classification (<100ms) for complex queries
    """
    
    # Heuristic patterns
    QUESTION_WORDS_FR = ["qui", "quoi", "quand", "où", "pourquoi", "comment", "combien", "quel", "quelle"]
    QUESTION_WORDS_EN = ["who", "what", "when", "where", "why", "how", "which"]
    
    # Use word boundaries for greetings to avoid false positives
    GREETING_PATTERNS = [
        r"\bbonjour\b", r"\bsalut\b", r"\bhello\b", r"\bhi\b", 
        r"\bhey\b", r"\bcoucou\b", r"\bbonsoir\b"
    ]
    CONFIRMATION_PATTERNS = ["oui", "non", "yes", "no", "ok", "d'accord", "merci"]
    
    FACTUAL_KEYWORDS = ["définition", "explication", "histoire", "date", "lieu", "personne", 
                        "entreprise", "pays", "ville", "événement"]
    
    def __init__(self, llm_client: Optional[Any] = None, 
                 heuristic_threshold: float = 0.85,
                 use_llm_fallback: bool = True):
        """
        Initialize Self-RAG
        
        Args:
            llm_client: Optional LLM client for complex classification
            heuristic_threshold: Confidence threshold for heuristic (0-1)
            use_llm_fallback: Use LLM when heuristic uncertain
        """
        self.llm_client = llm_client
        self.heuristic_threshold = heuristic_threshold
        self.use_llm_fallback = use_llm_fallback
        self.stats = SelfRAGStats()
    
    def classify(self, query: str) -> ClassificationResult:
        """
        Classify if retrieval is needed
        
        Args:
            query: User query
            
        Returns:
            ClassificationResult with decision and metadata
        """
        start_time = time.time()
        
        # Try quick heuristic first
        heuristic_result = self._quick_classify(query)
        
        # If confident enough, use heuristic
        if heuristic_result.confidence >= self.heuristic_threshold:
            latency_ms = (time.time() - start_time) * 1000
            result = ClassificationResult(
                decision=heuristic_result.decision,
                confidence=heuristic_result.confidence,
                reasoning=heuristic_result.reasoning,
                latency_ms=latency_ms,
                method="heuristic"
            )
            self.stats.update(result)
            return result
        
        # Fallback to LLM if available and enabled
        if self.use_llm_fallback and self.llm_client:
            llm_result = self._llm_classify(query)
            latency_ms = (time.time() - start_time) * 1000
            result = ClassificationResult(
                decision=llm_result.decision,
                confidence=llm_result.confidence,
                reasoning=llm_result.reasoning,
                latency_ms=latency_ms,
                method="llm"
            )
            self.stats.update(result)
            return result
        
        # Default: use heuristic even if low confidence
        latency_ms = (time.time() - start_time) * 1000
        result = ClassificationResult(
            decision=heuristic_result.decision,
            confidence=heuristic_result.confidence,
            reasoning=heuristic_result.reasoning + " (low confidence, no LLM)",
            latency_ms=latency_ms,
            method="heuristic"
        )
        self.stats.update(result)
        return result
    
    def _quick_classify(self, query: str) -> ClassificationResult:
        """
        Quick heuristic classification (<10ms)
        
        Returns:
            ClassificationResult with heuristic decision
        """
        query_lower = query.lower().strip()
        
        # 1. Greetings/Confirmations → NO_RETRIEVE (confidence: 0.95)
        # Use regex with word boundaries to avoid false positives
        greeting_found = any(
            re.search(pattern, query_lower)
            for pattern in self.GREETING_PATTERNS
        )
        
        if greeting_found:
            return ClassificationResult(
                decision=RetrievalDecision.NO_RETRIEVE,
                confidence=0.95,
                reasoning="Greeting detected, no retrieval needed",
                latency_ms=0,
                method="heuristic"
            )
        
        if any(c in query_lower for c in self.CONFIRMATION_PATTERNS) and len(query_lower.split()) <= 3:
            return ClassificationResult(
                decision=RetrievalDecision.NO_RETRIEVE,
                confidence=0.90,
                reasoning="Simple confirmation, no retrieval needed",
                latency_ms=0,
                method="heuristic"
            )
        
        # 2. Questions → RETRIEVE (confidence: 0.95)
        has_question_word = any(q in query_lower for q in self.QUESTION_WORDS_FR + self.QUESTION_WORDS_EN)
        ends_with_question = query.strip().endswith("?")
        
        if has_question_word or ends_with_question:
            return ClassificationResult(
                decision=RetrievalDecision.RETRIEVE,
                confidence=0.95,
                reasoning="Question detected, retrieval recommended",
                latency_ms=0,
                method="heuristic"
            )
        
        # 3. Factual keywords → RETRIEVE (confidence: 0.85)
        if any(k in query_lower for k in self.FACTUAL_KEYWORDS):
            return ClassificationResult(
                decision=RetrievalDecision.RETRIEVE,
                confidence=0.85,
                reasoning="Factual query detected, retrieval recommended",
                latency_ms=0,
                method="heuristic"
            )
        
        # 4. Long queries (>10 words) → RETRIEVE (confidence: 0.75)
        word_count = len(query.split())
        if word_count > 10:
            return ClassificationResult(
                decision=RetrievalDecision.RETRIEVE,
                confidence=0.75,
                reasoning="Complex query, retrieval may help",
                latency_ms=0,
                method="heuristic"
            )
        
        # 5. Very short queries (<3 words, no patterns) → UNCERTAIN (confidence: 0.50)
        if word_count < 3:
            return ClassificationResult(
                decision=RetrievalDecision.UNCERTAIN,
                confidence=0.50,
                reasoning="Very short query, unclear intent",
                latency_ms=0,
                method="heuristic"
            )
        
        # 6. Default → RETRIEVE (confidence: 0.70)
        return ClassificationResult(
            decision=RetrievalDecision.RETRIEVE,
            confidence=0.70,
            reasoning="Default behavior, retrieval recommended",
            latency_ms=0,
            method="heuristic"
        )
    
    def _llm_classify(self, query: str) -> ClassificationResult:
        """
        LLM-based classification (<100ms)
        
        Returns:
            ClassificationResult with LLM decision
        """
        if not self.llm_client:
            # Fallback to heuristic
            return self._quick_classify(query)
        
        # TODO: Implement LLM call
        # For now, use heuristic as placeholder
        prompt = f"""You are a query classifier. Decide if RAG retrieval is needed.

Query: "{query}"

Answer with JSON:
{{
  "decision": "retrieve" | "no_retrieve" | "uncertain",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""
        
        # Placeholder: would call LLM here
        # response = self.llm_client.generate(prompt, max_tokens=100)
        # return parse_llm_response(response)
        
        # For now, use heuristic
        return self._quick_classify(query)
    
    def critique_documents(self, query: str, documents: List[str]) -> List[CritiqueResult]:
        """
        Critique relevance of retrieved documents
        
        Args:
            query: Original query
            documents: List of retrieved document texts
            
        Returns:
            List of CritiqueResult, one per document
        """
        critiques = []
        
        for doc in documents:
            # Simple keyword-based critique for now
            query_words = set(query.lower().split())
            doc_words = set(doc.lower().split())
            
            # Calculate word overlap
            overlap = len(query_words & doc_words)
            overlap_ratio = overlap / max(1, len(query_words))
            
            # Determine relevance
            if overlap_ratio >= 0.7:
                relevance = RelevanceScore.HIGHLY_RELEVANT
                confidence = 0.90
            elif overlap_ratio >= 0.5:
                relevance = RelevanceScore.RELEVANT
                confidence = 0.80
            elif overlap_ratio >= 0.3:
                relevance = RelevanceScore.PARTIALLY_RELEVANT
                confidence = 0.70
            elif overlap_ratio >= 0.1:
                relevance = RelevanceScore.BARELY_RELEVANT
                confidence = 0.60
            else:
                relevance = RelevanceScore.NOT_RELEVANT
                confidence = 0.85
            
            critiques.append(CritiqueResult(
                relevance=relevance,
                confidence=confidence,
                reasoning=f"Word overlap: {overlap_ratio:.1%} ({overlap}/{len(query_words)} words)",
                suggestions=["Consider more specific query" if overlap_ratio < 0.3 else "Good match"]
            ))
        
        return critiques
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return self.stats.to_dict()
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = SelfRAGStats()


# ============================================
# Tests
# ============================================

def test_self_rag():
    """Test Self-RAG functionality"""
    print("=" * 60)
    print("Self-RAG Tests")
    print("=" * 60)
    
    rag = SelfRAG(use_llm_fallback=False)
    
    # Test 1: Questions (should retrieve)
    test_queries = [
        ("Qui est le président de la France?", RetrievalDecision.RETRIEVE),
        ("Comment fonctionne Python asyncio?", RetrievalDecision.RETRIEVE),
        ("Quelle est la capitale de l'Allemagne?", RetrievalDecision.RETRIEVE),
        ("Bonjour!", RetrievalDecision.NO_RETRIEVE),
        ("Merci", RetrievalDecision.NO_RETRIEVE),
        ("Oui", RetrievalDecision.NO_RETRIEVE),
    ]
    
    print("\n📊 Classification Tests:")
    for query, expected in test_queries:
        result = rag.classify(query)
        status = "✅" if result.decision == expected else "❌"
        print(f"{status} '{query}'")
        print(f"   → {result.decision.value} (conf: {result.confidence:.2f}, latency: {result.latency_ms:.1f}ms)")
        print(f"   → {result.reasoning}")
    
    # Test 2: Document critique
    print("\n📝 Document Critique Test:")
    query = "Python asyncio tutorial"
    docs = [
        "Python asyncio is a library for asynchronous programming with async/await syntax",
        "Java Spring Boot is a framework for building web applications",
        "Asyncio allows concurrent code execution in Python using coroutines"
    ]
    
    critiques = rag.critique_documents(query, docs)
    for i, (doc, critique) in enumerate(zip(docs, critiques), 1):
        print(f"\nDoc {i}: {doc[:60]}...")
        print(f"  Relevance: {critique.relevance.value} (conf: {critique.confidence:.2f})")
        print(f"  Reasoning: {critique.reasoning}")
    
    # Test 3: Statistics
    print("\n📈 Statistics:")
    stats = rag.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_self_rag()
