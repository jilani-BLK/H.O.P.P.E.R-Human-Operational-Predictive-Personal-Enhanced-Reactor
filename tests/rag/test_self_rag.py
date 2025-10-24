"""
Unit tests for Self-RAG module
Phase 3.5 - Week 1
"""

import pytest
import time
from src.rag.self_rag import (
    SelfRAG, 
    RetrievalDecision, 
    RelevanceScore,
    ClassificationResult,
    CritiqueResult
)


class TestSelfRAGClassification:
    """Test classification functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.rag = SelfRAG(use_llm_fallback=False)
    
    def test_questions_should_retrieve(self):
        """Questions should trigger retrieval"""
        questions = [
            "Qui est le président?",
            "Comment fonctionne asyncio?",
            "Quelle est la capitale?",
            "Pourquoi le ciel est bleu?",
            "Quand a eu lieu la révolution?",
            "What is Python?",
            "How does it work?",
        ]
        
        for query in questions:
            result = self.rag.classify(query)
            assert result.decision == RetrievalDecision.RETRIEVE
            assert result.confidence >= 0.85
    
    def test_greetings_no_retrieve(self):
        """Greetings should not trigger retrieval"""
        greetings = [
            "Bonjour",
            "Salut!",
            "Hello",
            "Hi there",
            "Bonsoir",
        ]
        
        for query in greetings:
            result = self.rag.classify(query)
            assert result.decision == RetrievalDecision.NO_RETRIEVE
            assert result.confidence >= 0.90
    
    def test_confirmations_no_retrieve(self):
        """Simple confirmations should not trigger retrieval"""
        confirmations = [
            "Oui",
            "Non",
            "Ok",
            "Merci",
            "D'accord",
        ]
        
        for query in confirmations:
            result = self.rag.classify(query)
            assert result.decision == RetrievalDecision.NO_RETRIEVE
            assert result.confidence >= 0.85
    
    def test_factual_keywords_retrieve(self):
        """Factual queries should trigger retrieval"""
        factual = [
            "Définition de Python",
            "Explication de asyncio",
            "Histoire de la France",
            "Date de naissance de Einstein",
        ]
        
        for query in factual:
            result = self.rag.classify(query)
            assert result.decision == RetrievalDecision.RETRIEVE
            assert result.confidence >= 0.75
    
    def test_latency_heuristic(self):
        """Heuristic classification should be fast (<10ms)"""
        query = "Comment fonctionne Python?"
        
        start = time.time()
        result = self.rag.classify(query)
        latency = (time.time() - start) * 1000
        
        assert latency < 10  # Should be <10ms
        assert result.method == "heuristic"
    
    def test_classification_metadata(self):
        """Classification should return complete metadata"""
        result = self.rag.classify("Test query?")
        
        assert isinstance(result, ClassificationResult)
        assert result.decision in RetrievalDecision
        assert 0 <= result.confidence <= 1
        assert isinstance(result.reasoning, str)
        assert result.latency_ms >= 0
        assert result.method in ["heuristic", "llm"]


class TestSelfRAGCritique:
    """Test document critique functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.rag = SelfRAG()
    
    def test_highly_relevant_document(self):
        """Document with high overlap should be highly relevant"""
        query = "Python asyncio tutorial"
        docs = ["Python asyncio is a great tutorial for learning asynchronous programming"]
        
        critiques = self.rag.critique_documents(query, docs)
        
        assert len(critiques) == 1
        assert critiques[0].relevance in [
            RelevanceScore.HIGHLY_RELEVANT, 
            RelevanceScore.RELEVANT
        ]
        assert critiques[0].confidence >= 0.70
    
    def test_not_relevant_document(self):
        """Document with no overlap should be not relevant"""
        query = "Python asyncio"
        docs = ["Java Spring Boot framework for web applications"]
        
        critiques = self.rag.critique_documents(query, docs)
        
        assert len(critiques) == 1
        assert critiques[0].relevance == RelevanceScore.NOT_RELEVANT
        assert critiques[0].confidence >= 0.70
    
    def test_multiple_documents(self):
        """Should critique all documents"""
        query = "Python programming"
        docs = [
            "Python is a programming language",
            "Java is also a language",
            "The sky is blue"
        ]
        
        critiques = self.rag.critique_documents(query, docs)
        
        assert len(critiques) == 3
        assert all(isinstance(c, CritiqueResult) for c in critiques)
        
        # First doc should be most relevant
        assert critiques[0].relevance.value in ["highly_relevant", "relevant"]
        # Last doc should be least relevant
        assert critiques[2].relevance.value in ["not_relevant", "barely"]


class TestSelfRAGStatistics:
    """Test statistics tracking"""
    
    def setup_method(self):
        """Setup for each test"""
        self.rag = SelfRAG()
    
    def test_stats_initialization(self):
        """Stats should start at zero"""
        stats = self.rag.get_stats()
        
        assert stats["total_queries"] == 0
        assert stats["retrieve_rate"] == 0.0
        assert stats["avg_latency_ms"] == 0.0
    
    def test_stats_update_on_classify(self):
        """Stats should update after classification"""
        self.rag.classify("Test query?")
        
        stats = self.rag.get_stats()
        assert stats["total_queries"] == 1
    
    def test_stats_retrieve_rate(self):
        """Stats should track retrieve rate correctly"""
        # 2 retrieves, 1 no-retrieve
        self.rag.classify("Qui est le président?")  # retrieve
        self.rag.classify("Comment ça marche?")      # retrieve
        self.rag.classify("Bonjour")                 # no-retrieve
        
        stats = self.rag.get_stats()
        
        assert stats["total_queries"] == 3
        assert stats["retrieve_rate"] == pytest.approx(2/3, rel=0.01)
        assert stats["no_retrieve_rate"] == pytest.approx(1/3, rel=0.01)
    
    def test_stats_method_tracking(self):
        """Stats should track heuristic vs LLM usage"""
        self.rag.classify("Test query 1")
        self.rag.classify("Test query 2")
        
        stats = self.rag.get_stats()
        
        # Without LLM client, should be all heuristic
        assert stats["heuristic_usage_rate"] == 1.0
        assert stats["llm_usage_rate"] == 0.0
    
    def test_stats_reset(self):
        """Stats should reset correctly"""
        self.rag.classify("Query 1")
        self.rag.classify("Query 2")
        
        self.rag.reset_stats()
        stats = self.rag.get_stats()
        
        assert stats["total_queries"] == 0


class TestSelfRAGEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Setup for each test"""
        self.rag = SelfRAG()
    
    def test_empty_query(self):
        """Empty query should be handled"""
        result = self.rag.classify("")
        assert isinstance(result, ClassificationResult)
    
    def test_very_long_query(self):
        """Very long query should be handled"""
        query = " ".join(["word"] * 100)
        result = self.rag.classify(query)
        
        assert result.decision == RetrievalDecision.RETRIEVE
        assert result.confidence >= 0.70
    
    def test_special_characters(self):
        """Query with special characters should be handled"""
        query = "Qu'est-ce que c'est? @#$%"
        result = self.rag.classify(query)
        
        assert isinstance(result, ClassificationResult)
    
    def test_multilingual_query(self):
        """Mixed language query should be handled"""
        query = "What is Python en français?"
        result = self.rag.classify(query)
        
        # Should detect "What" as question word
        assert result.decision == RetrievalDecision.RETRIEVE


# ============================================
# Performance Tests
# ============================================

class TestSelfRAGPerformance:
    """Test performance requirements"""
    
    def setup_method(self):
        """Setup for each test"""
        self.rag = SelfRAG()
    
    def test_heuristic_latency_requirement(self):
        """Heuristic should be <10ms (Phase 3.5 requirement)"""
        queries = [
            "Qui est le président?",
            "Bonjour",
            "Comment ça marche?",
        ]
        
        for query in queries:
            start = time.time()
            self.rag.classify(query)
            latency = (time.time() - start) * 1000
            
            assert latency < 10, f"Latency {latency:.2f}ms exceeds 10ms requirement"
    
    def test_batch_classification_performance(self):
        """Should handle batch classification efficiently"""
        queries = [f"Query {i}?" for i in range(100)]
        
        start = time.time()
        for query in queries:
            self.rag.classify(query)
        total_time = (time.time() - start) * 1000
        
        avg_latency = total_time / len(queries)
        assert avg_latency < 5, f"Average latency {avg_latency:.2f}ms too high"


# ============================================
# Integration Tests
# ============================================

class TestSelfRAGIntegration:
    """Test integration scenarios"""
    
    def test_typical_conversation_flow(self):
        """Test typical conversation with mixed queries"""
        rag = SelfRAG()
        
        conversation = [
            ("Bonjour!", RetrievalDecision.NO_RETRIEVE),
            ("Qui est Einstein?", RetrievalDecision.RETRIEVE),
            ("Merci", RetrievalDecision.NO_RETRIEVE),
            ("Comment fonctionne la relativité?", RetrievalDecision.RETRIEVE),
        ]
        
        for query, expected_decision in conversation:
            result = rag.classify(query)
            assert result.decision == expected_decision
        
        # Check stats
        stats = rag.get_stats()
        assert stats["total_queries"] == 4
        assert stats["retrieve_rate"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
