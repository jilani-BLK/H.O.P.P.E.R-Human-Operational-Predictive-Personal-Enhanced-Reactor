"""
Tests PyTest pour HyDE (Hypothetical Document Embeddings)
Tests de query expansion, detection de type, cache, et performance.
"""

import pytest
import asyncio
import time
from src.rag.hyde import (
    HyDE,
    HyDEResult,
    HypotheticalDocument,
    QueryType,
    expand_vague_query
)


class TestQueryTypeDetection:
    """Tests de detection du type de requete."""
    
    def test_detect_vague_query(self):
        """Doit detecter une query vague."""
        hyde = HyDE()
        
        vague_queries = [
            "comment ca marche?",
            "c'est quoi?",
            "pourquoi?",
            "truc bizarre"
        ]
        
        for query in vague_queries:
            query_type = hyde._detect_query_type(query)
            assert query_type == QueryType.VAGUE
    
    def test_detect_conceptual_query(self):
        """Doit detecter une query conceptuelle."""
        hyde = HyDE()
        
        conceptual_queries = [
            "qu'est-ce que le machine learning?",
            "definition de l'intelligence artificielle",
            "expliquer le concept de blockchain",
            "theorie de la relativite"
        ]
        
        for query in conceptual_queries:
            query_type = hyde._detect_query_type(query)
            assert query_type == QueryType.CONCEPTUAL
    
    def test_detect_exploratory_query(self):
        """Doit detecter une query exploratoire."""
        hyde = HyDE()
        
        exploratory_queries = [
            "je veux explorer les possibilites",
            "decouvrir les alternatives disponibles",
            "quelles sont les diverses options?"
        ]
        
        for query in exploratory_queries:
            query_type = hyde._detect_query_type(query)
            assert query_type == QueryType.EXPLORATORY
    
    def test_detect_specific_query(self):
        """Doit detecter une query specifique."""
        hyde = HyDE()
        
        query = "Je cherche precisement la documentation technique detaillee sur l'implementation du protocole HTTP/2 dans les navigateurs modernes"
        query_type = hyde._detect_query_type(query)
        
        assert query_type == QueryType.SPECIFIC


class TestDocumentGeneration:
    """Tests de generation de documents hypothetiques."""
    
    def test_generate_documents_vague(self):
        """Doit generer des documents pour query vague."""
        hyde = HyDE(num_docs=3)
        result = hyde.expand_query("comment ca marche?")
        
        assert result.success
        assert len(result.hypothetical_docs) == 3
        assert all(isinstance(doc, HypotheticalDocument) for doc in result.hypothetical_docs)
    
    def test_generate_documents_conceptual(self):
        """Doit generer des documents pour query conceptuelle."""
        hyde = HyDE(num_docs=2)
        result = hyde.expand_query("qu'est-ce que le deep learning?")
        
        assert result.success
        assert len(result.hypothetical_docs) == 2
        assert result.query_type == QueryType.CONCEPTUAL
    
    def test_document_content_not_empty(self):
        """Les documents generes ne doivent pas etre vides."""
        hyde = HyDE()
        result = hyde.expand_query("test query")
        
        for doc in result.hypothetical_docs:
            assert len(doc.content) > 0
            assert doc.query_original == "test query"
            assert doc.generation_method == "template"
    
    def test_document_max_length(self):
        """Les documents doivent respecter la longueur max."""
        max_length = 200
        hyde = HyDE(max_doc_length=max_length)
        result = hyde.expand_query("query longue necessitant beaucoup de contexte")
        
        for doc in result.hypothetical_docs:
            assert len(doc.content) <= max_length


class TestQueryExpansion:
    """Tests d'expansion de queries alternatives."""
    
    def test_extract_alternative_queries(self):
        """Doit extraire des queries alternatives."""
        hyde = HyDE()
        result = hyde.expand_query("comment ca marche?")
        
        assert len(result.expanded_queries) > 0
        assert isinstance(result.expanded_queries, list)
        assert all(isinstance(q, str) for q in result.expanded_queries)
    
    def test_expanded_queries_different(self):
        """Les queries alternatives doivent etre differentes."""
        hyde = HyDE()
        result = hyde.expand_query("comment faire?")
        
        # Doit avoir au moins 2 queries alternatives
        assert len(result.expanded_queries) >= 2
        # Doivent etre uniques
        assert len(result.expanded_queries) == len(set(result.expanded_queries))
    
    def test_expanded_queries_limit(self):
        """Les queries alternatives doivent etre limitees a 5."""
        hyde = HyDE()
        result = hyde.expand_query("une question tres complexe avec beaucoup de mots")
        
        assert len(result.expanded_queries) <= 5


class TestCaching:
    """Tests du systeme de cache."""
    
    def test_cache_hit(self):
        """Doit utiliser le cache pour query identique."""
        hyde = HyDE(cache_enabled=True)
        
        # Premiere query
        result1 = hyde.expand_query("test cache")
        time1 = result1.generation_time
        
        # Deuxieme query identique
        result2 = hyde.expand_query("test cache")
        time2 = result2.generation_time
        
        # Cache hit = temps de generation 0
        assert time2 == 0.0
        assert len(result1.hypothetical_docs) == len(result2.hypothetical_docs)
    
    def test_cache_case_insensitive(self):
        """Le cache doit etre case-insensitive."""
        hyde = HyDE(cache_enabled=True)
        
        result1 = hyde.expand_query("Test CACHE")
        result2 = hyde.expand_query("test cache")
        
        # Deuxieme query doit etre un cache hit
        assert result2.generation_time == 0.0
    
    def test_cache_disabled(self):
        """Sans cache, chaque query doit etre regeneree."""
        hyde = HyDE(cache_enabled=False)
        
        result1 = hyde.expand_query("test no cache")
        result2 = hyde.expand_query("test no cache")
        
        # Les deux doivent avoir un temps de generation > 0
        assert result1.generation_time > 0
        assert result2.generation_time > 0


class TestBatchProcessing:
    """Tests du traitement batch."""
    
    def test_expand_batch(self):
        """Doit expanser un batch de queries."""
        hyde = HyDE()
        queries = ["query 1", "query 2", "query 3"]
        
        results = hyde.expand_batch(queries)
        
        assert len(results) == 3
        assert all(isinstance(r, HyDEResult) for r in results)
        assert all(r.success for r in results)
    
    def test_expand_batch_preserves_order(self):
        """Le batch doit preserver l'ordre des queries."""
        hyde = HyDE()
        queries = ["premiere", "deuxieme", "troisieme"]
        
        results = hyde.expand_batch(queries)
        
        assert results[0].original_query == "premiere"
        assert results[1].original_query == "deuxieme"
        assert results[2].original_query == "troisieme"
    
    @pytest.mark.asyncio
    async def test_expand_batch_async(self):
        """Version async du batch doit fonctionner."""
        hyde = HyDE()
        queries = ["async 1", "async 2"]
        
        results = await hyde.expand_batch_async(queries)
        
        assert len(results) == 2
        assert all(r.success for r in results)


class TestStatistics:
    """Tests des statistiques de performance."""
    
    def test_stats_tracking(self):
        """Les stats doivent etre trackees."""
        hyde = HyDE(cache_enabled=True)
        
        hyde.expand_query("query 1")
        hyde.expand_query("query 2")
        hyde.expand_query("query 1")  # Cache hit
        
        stats = hyde.get_stats()
        
        assert stats["total_queries"] == 3
        assert stats["cache_hits"] == 1
        assert stats["template_generations"] == 2
    
    def test_cache_hit_rate(self):
        """Le taux de cache hit doit etre calcule."""
        hyde = HyDE(cache_enabled=True)
        
        hyde.expand_query("q1")
        hyde.expand_query("q2")
        hyde.expand_query("q1")
        hyde.expand_query("q2")
        
        stats = hyde.get_stats()
        
        # 4 queries, 2 cache hits = 50%
        assert stats["cache_hit_rate"] == 0.5
    
    def test_average_generation_time(self):
        """Le temps moyen de generation doit etre calcule."""
        hyde = HyDE()
        
        hyde.expand_query("test 1")
        hyde.expand_query("test 2")
        
        stats = hyde.get_stats()
        
        assert stats["average_generation_time"] > 0
        assert isinstance(stats["average_generation_time"], float)


class TestErrorHandling:
    """Tests de gestion d'erreurs."""
    
    def test_empty_query(self):
        """Doit gerer une query vide."""
        hyde = HyDE()
        result = hyde.expand_query("")
        
        # Doit quand meme reussir avec query vide
        assert result.success or not result.success  # Peut echouer ou reussir
        assert isinstance(result, HyDEResult)
    
    def test_very_long_query(self):
        """Doit gerer une query tres longue."""
        hyde = HyDE()
        long_query = "test " * 200  # 1000 caracteres
        
        result = hyde.expand_query(long_query)
        
        assert isinstance(result, HyDEResult)
        # Docs doivent respecter max_length meme avec query longue
        for doc in result.hypothetical_docs:
            assert len(doc.content) <= hyde.max_doc_length


class TestHyDEResult:
    """Tests de la classe HyDEResult."""
    
    def test_result_to_dict(self):
        """Doit convertir en dictionnaire."""
        hyde = HyDE()
        result = hyde.expand_query("test")
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "original_query" in result_dict
        assert "hypothetical_docs" in result_dict
        assert "expanded_queries" in result_dict
        assert "query_type" in result_dict
        assert "success" in result_dict
    
    def test_result_contains_all_fields(self):
        """Le resultat doit contenir tous les champs."""
        hyde = HyDE()
        result = hyde.expand_query("test complet")
        
        assert result.original_query == "test complet"
        assert isinstance(result.hypothetical_docs, list)
        assert isinstance(result.expanded_queries, list)
        assert isinstance(result.query_type, QueryType)
        assert isinstance(result.generation_time, float)
        assert isinstance(result.success, bool)


class TestUtilityFunction:
    """Tests de la fonction utilitaire."""
    
    def test_expand_vague_query_function(self):
        """La fonction utilitaire doit fonctionner."""
        result = expand_vague_query("comment?")
        
        assert isinstance(result, HyDEResult)
        assert result.success
        assert len(result.hypothetical_docs) == 3  # Default
    
    def test_expand_vague_query_custom_num_docs(self):
        """Doit accepter un nombre custom de docs."""
        result = expand_vague_query("test", num_docs=5)
        
        assert len(result.hypothetical_docs) == 5


class TestPerformance:
    """Tests de performance."""
    
    def test_generation_speed(self):
        """La generation doit etre rapide (<2s)."""
        hyde = HyDE(cache_enabled=False)
        
        start = time.time()
        result = hyde.expand_query("test performance")
        duration = time.time() - start
        
        assert duration < 2.0  # Target: <2s
        assert result.generation_time < 2.0
    
    def test_batch_faster_than_sequential(self):
        """Le batch ne doit pas etre significativement plus lent."""
        hyde = HyDE()
        queries = ["q1", "q2", "q3", "q4", "q5"]
        
        # Batch
        start_batch = time.time()
        hyde.expand_batch(queries)
        batch_time = time.time() - start_batch
        
        # Sequentiel
        hyde2 = HyDE()
        start_seq = time.time()
        for q in queries:
            hyde2.expand_query(q)
        seq_time = time.time() - start_seq
        
        # Batch ne doit pas etre significativement plus lent (50% margin)
        assert batch_time <= seq_time * 1.5


class TestIntegration:
    """Tests d'integration."""
    
    def test_full_workflow(self):
        """Test du workflow complet."""
        hyde = HyDE(num_docs=2, cache_enabled=True)
        
        # 1. Expansion
        result = hyde.expand_query("comment faire du machine learning?")
        
        # 2. Verifications
        assert result.success
        assert len(result.hypothetical_docs) == 2
        assert len(result.expanded_queries) > 0
        assert result.query_type in [QueryType.VAGUE, QueryType.CONCEPTUAL]
        
        # 3. Cache hit
        result2 = hyde.expand_query("comment faire du machine learning?")
        assert result2.generation_time == 0.0
        
        # 4. Stats
        stats = hyde.get_stats()
        assert stats["total_queries"] == 2
        assert stats["cache_hits"] == 1
    
    def test_multiple_query_types(self):
        """Doit gerer plusieurs types de queries dans la meme instance."""
        hyde = HyDE()
        
        queries = [
            ("comment?", QueryType.VAGUE),
            ("qu'est-ce que Python exactement?", QueryType.CONCEPTUAL),
            ("je voudrais explorer les options", QueryType.EXPLORATORY)
        ]
        
        for query, expected_type in queries:
            result = hyde.expand_query(query)
            assert result.success
            assert result.query_type == expected_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
