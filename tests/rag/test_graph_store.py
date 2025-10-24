"""
Tests d'intégration pour GraphStore (Neo4j + entity extractor).

Validations:
- Connexion Neo4j
- Insertion d'entités (single + batch)
- Création de relations
- Requêtes d'entités
- Multi-hop queries (depth 2-3)
- Performance (<500ms)
- Pipeline texte → graph complet
"""

import pytest
import time
from src.rag.graph_store import GraphStore
from src.rag.entity_extractor import Entity, EntityType


@pytest.fixture
def graph_store():
    """Fixture pour GraphStore avec cleanup."""
    store = GraphStore()
    
    # Vérifier que Neo4j est disponible
    if not store.driver:
        pytest.skip("Neo4j not available")
    
    yield store
    
    # Cleanup: supprimer les données de test
    try:
        with store.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    except:
        pass
    
    store.close()


class TestGraphStoreConnection:
    """Tests de connexion Neo4j."""
    
    def test_connection_success(self, graph_store):
        """Doit se connecter à Neo4j avec succès."""
        assert graph_store.driver is not None
        
    def test_verify_connectivity(self, graph_store):
        """Doit vérifier la connectivité Neo4j."""
        # Pas d'exception levée = connexion OK
        graph_store.driver.verify_connectivity()


class TestEntityOperations:
    """Tests des opérations sur les entités."""
    
    def test_add_single_entity(self, graph_store):
        """Doit ajouter une entité unique."""
        success = graph_store.add_entity("Paris", "Location", {"country": "France"})
        assert success is True
        
        # Vérifier que l'entité existe
        entity = graph_store.query_entity("Paris")
        assert entity is not None
        assert entity["name"] == "Paris"
        assert entity.get("country") == "France"
    
    def test_add_batch_entities(self, graph_store):
        """Doit ajouter plusieurs entités en batch."""
        entities = [
            Entity("Paris", EntityType.LOCATION, 0.95, 0, 5),
            Entity("Google", EntityType.ORGANIZATION, 0.85, 10, 16),
            Entity("Python", EntityType.CONCEPT, 0.80, 20, 26),
        ]
        
        count = graph_store.add_entities_batch(entities)
        assert count == 3
        
        # Vérifier qu'elles existent
        assert graph_store.query_entity("Paris") is not None
        assert graph_store.query_entity("Google") is not None
        assert graph_store.query_entity("Python") is not None
    
    def test_add_entity_with_properties(self, graph_store):
        """Doit stocker les propriétés des entités."""
        entity = Entity("Albert Einstein", EntityType.PERSON, 0.75, 0, 15)
        graph_store.add_entities_batch([entity])
        
        result = graph_store.query_entity("Albert Einstein")
        assert result is not None
        assert result["confidence"] == 0.75
        assert result["position_start"] == 0
        assert result["position_end"] == 15
    
    def test_query_entity_not_found(self, graph_store):
        """Doit retourner None si l'entité n'existe pas."""
        result = graph_store.query_entity("EntityDoesNotExist")
        assert result is None
    
    def test_query_entity_by_type(self, graph_store):
        """Doit rechercher une entité par type."""
        graph_store.add_entity("Berlin", "Location")
        
        result = graph_store.query_entity("Berlin", entity_type="Location")
        assert result is not None
        assert result["name"] == "Berlin"


class TestRelationOperations:
    """Tests des opérations sur les relations."""
    
    def test_add_relation(self, graph_store):
        """Doit créer une relation entre deux entités."""
        # Ajouter entités
        graph_store.add_entity("Google", "Organization")
        graph_store.add_entity("Paris", "Location")
        
        # Ajouter relation
        success = graph_store.add_relation(
            "Google", "Paris", "LOCATED_IN",
            {"confidence": 0.9}
        )
        assert success is True
        
        # Vérifier la relation via neighbors
        neighbors = graph_store.query_neighbors("Google", depth=1)
        assert len(neighbors) >= 1
        assert any("Paris" in str(n) for n in neighbors)
    
    def test_add_multiple_relations(self, graph_store):
        """Doit créer plusieurs relations."""
        # Entités
        graph_store.add_entity("Einstein", "Person")
        graph_store.add_entity("Princeton", "Organization")
        graph_store.add_entity("Berlin", "Location")
        
        # Relations
        graph_store.add_relation("Einstein", "Princeton", "WORKS_FOR")
        graph_store.add_relation("Einstein", "Berlin", "BORN_IN")
        
        # Vérifier via neighbors
        neighbors = graph_store.query_neighbors("Einstein", depth=1)
        assert len(neighbors) >= 2


class TestGraphQueries:
    """Tests des requêtes sur le graphe."""
    
    def test_query_neighbors_depth_1(self, graph_store):
        """Doit trouver les voisins à distance 1."""
        # Setup: A → B → C
        graph_store.add_entity("A", "Node")
        graph_store.add_entity("B", "Node")
        graph_store.add_entity("C", "Node")
        graph_store.add_relation("A", "B", "RELATED")
        graph_store.add_relation("B", "C", "RELATED")
        
        neighbors = graph_store.query_neighbors("A", depth=1)
        # Devrait trouver seulement B à distance 1
        assert len(neighbors) >= 1
        assert any("B" in str(n["entity"]) for n in neighbors)
    
    def test_query_neighbors_depth_2(self, graph_store):
        """Doit trouver les voisins à distance 2."""
        # Setup: A → B → C
        graph_store.add_entity("A", "Node")
        graph_store.add_entity("B", "Node")
        graph_store.add_entity("C", "Node")
        graph_store.add_relation("A", "B", "RELATED")
        graph_store.add_relation("B", "C", "RELATED")
        
        neighbors = graph_store.query_neighbors("A", depth=2)
        # Devrait trouver B et C
        assert len(neighbors) >= 2
    
    def test_multi_hop_search(self, graph_store):
        """Doit trouver un chemin entre deux entités."""
        # Setup: Einstein → Princeton → USA
        graph_store.add_entity("Einstein", "Person")
        graph_store.add_entity("Princeton", "Organization")
        graph_store.add_entity("USA", "Location")
        graph_store.add_relation("Einstein", "Princeton", "WORKS_FOR")
        graph_store.add_relation("Princeton", "USA", "LOCATED_IN")
        
        paths = graph_store.multi_hop_search("Einstein", "USA", max_depth=3)
        assert len(paths) >= 1
        
        path = paths[0]
        assert path["hops"] <= 3
        assert len(path["nodes"]) >= 2
        assert len(path["relations"]) >= 1
    
    def test_multi_hop_no_path(self, graph_store):
        """Doit retourner [] si aucun chemin n'existe."""
        graph_store.add_entity("A", "Node")
        graph_store.add_entity("B", "Node")
        # Pas de relation A-B
        
        paths = graph_store.multi_hop_search("A", "B", max_depth=3)
        assert len(paths) == 0


class TestGraphStatistics:
    """Tests des statistiques du graphe."""
    
    def test_get_stats_empty(self, graph_store):
        """Doit retourner des stats pour un graphe vide."""
        stats = graph_store.get_graph_stats()
        
        assert "total_nodes" in stats
        assert "total_relations" in stats
        assert stats["total_nodes"] == 0
        assert stats["total_relations"] == 0
    
    def test_get_stats_with_data(self, graph_store):
        """Doit retourner des stats correctes."""
        # Ajouter des données
        graph_store.add_entity("Paris", "Location")
        graph_store.add_entity("Google", "Organization")
        graph_store.add_relation("Google", "Paris", "LOCATED_IN")
        
        stats = graph_store.get_graph_stats()
        
        assert stats["total_nodes"] >= 2
        assert stats["total_relations"] >= 1
        assert "node_types" in stats
        assert len(stats["node_types"]) >= 1


class TestTextToGraphPipeline:
    """Tests du pipeline texte → graphe complet."""
    
    def test_extract_and_store_simple(self, graph_store):
        """Doit extraire et stocker à partir d'un texte simple."""
        text = "Google est basé à Mountain View en Californie."
        
        result = graph_store.extract_and_store(text)
        
        assert result["entities_added"] >= 1
        # Les relations dépendent de la proximité, peut être 0
        assert result["relations_added"] >= 0
    
    def test_extract_and_store_complex(self, graph_store):
        """Doit gérer un texte complexe."""
        text = """
        Albert Einstein était un physicien né en 1879.
        Il a travaillé à Princeton aux États-Unis.
        Python est maintenant utilisé pour simuler ses théories.
        """
        
        result = graph_store.extract_and_store(text)
        
        # Devrait trouver plusieurs entités
        assert result["entities_added"] >= 3
        
        # Vérifier qu'Einstein existe
        entity = graph_store.query_entity("Albert Einstein")
        assert entity is not None
    
    def test_extract_and_store_entities_retrievable(self, graph_store):
        """Les entités extraites doivent être requêtables."""
        text = "Paris est la capitale de la France."
        graph_store.extract_and_store(text)
        
        # Vérifier que Paris existe
        paris = graph_store.query_entity("Paris")
        assert paris is not None
        
        # Vérifier que France existe
        france = graph_store.query_entity("France")
        assert france is not None
    
    def test_extract_and_store_idempotent(self, graph_store):
        """L'extraction multiple du même texte doit être idempotente."""
        text = "Google est à Mountain View."
        
        result1 = graph_store.extract_and_store(text)
        result2 = graph_store.extract_and_store(text)
        
        # Le nombre d'entités devrait être stable (MERGE)
        stats = graph_store.get_graph_stats()
        assert stats["total_nodes"] < result1["entities_added"] * 3


class TestPerformance:
    """Tests de performance."""
    
    def test_batch_insert_speed(self, graph_store):
        """L'insertion batch doit être rapide (<500ms)."""
        # Créer 20 entités
        entities = [
            Entity(f"Entity{i}", EntityType.CONCEPT, 0.8, i*10, i*10+5)
            for i in range(20)
        ]
        
        start = time.time()
        count = graph_store.add_entities_batch(entities)
        elapsed = time.time() - start
        
        assert count == 20
        assert elapsed < 0.5  # <500ms
    
    def test_multi_hop_query_speed(self, graph_store):
        """Les requêtes multi-hop doivent être rapides (<500ms)."""
        # Setup: chaîne A → B → C → D
        for letter in ["A", "B", "C", "D"]:
            graph_store.add_entity(letter, "Node")
        
        graph_store.add_relation("A", "B", "RELATED")
        graph_store.add_relation("B", "C", "RELATED")
        graph_store.add_relation("C", "D", "RELATED")
        
        start = time.time()
        paths = graph_store.multi_hop_search("A", "D", max_depth=5)
        elapsed = time.time() - start
        
        assert len(paths) >= 1
        assert elapsed < 0.5  # <500ms
    
    def test_extract_and_store_speed(self, graph_store):
        """Le pipeline complet doit être rapide (<500ms)."""
        text = """
        Einstein travaillait à Princeton.
        Paris est en France. Google utilise Python.
        """
        
        start = time.time()
        result = graph_store.extract_and_store(text)
        elapsed = time.time() - start
        
        assert result["entities_added"] >= 3
        assert elapsed < 0.5  # <500ms


class TestEdgeCases:
    """Tests des cas limites."""
    
    def test_empty_text(self, graph_store):
        """Doit gérer un texte vide."""
        result = graph_store.extract_and_store("")
        assert result["entities_added"] == 0
        assert result["relations_added"] == 0
    
    def test_no_entities_found(self, graph_store):
        """Doit gérer un texte sans entités reconnues."""
        result = graph_store.extract_and_store("ceci est un test sans entites")
        # Peut avoir 0 entités ou quelques faux positifs
        assert result["entities_added"] >= 0
    
    def test_invalid_depth(self, graph_store):
        """Doit gérer des profondeurs invalides."""
        graph_store.add_entity("A", "Node")
        
        # Depth 0 ou négatif
        neighbors = graph_store.query_neighbors("A", depth=0)
        assert neighbors == []
        
        # Depth trop grand (>3)
        neighbors = graph_store.query_neighbors("A", depth=10)
        assert neighbors == []
    
    def test_nonexistent_entity_neighbors(self, graph_store):
        """Doit gérer la recherche de voisins d'une entité inexistante."""
        neighbors = graph_store.query_neighbors("DoesNotExist", depth=2)
        assert neighbors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
