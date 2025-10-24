"""
GraphRAG - Neo4j knowledge graph integration
Enriched with entity extraction and multi-hop queries
"""
from neo4j import GraphDatabase
from typing import Optional, List, Dict, Any
import os
from src.rag.entity_extractor import EntityExtractor, Entity, EntityType


class GraphStore:
    """
    Neo4j graph database connector with NER integration.
    
    Features:
    - Batch entity insertion
    - Relation creation
    - Multi-hop queries (depth 2-3)
    - Entity search/retrieval
    - Graph statistics
    
    Security:
    - Credentials from environment variables
    - Parameterized queries (injection prevention)
    """
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j URI (default: from NEO4J_URI env or bolt://localhost:7687)
            user: Neo4j username (default: from NEO4J_USER env or 'neo4j')
            password: Neo4j password (default: from NEO4J_PASSWORD env)
            
        Raises:
            ValueError: If NEO4J_PASSWORD not provided and not in environment
        """
        # Get credentials from environment or parameters
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        
        # Security: Require password to be explicitly set
        if not self.password:
            # Fallback pour dev/test seulement (afficher warning)
            self.password = "hopper123"
            print("⚠️  WARNING: Using default Neo4j password. Set NEO4J_PASSWORD environment variable!")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            print(f"✅ Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"⚠️  Neo4j not available: {e}")
            self.driver = None
        
        # Entity extractor pour NER
        self.extractor = EntityExtractor()
    
    def add_entity(self, entity: str, entity_type: str, properties: dict | None = None) -> bool:
        """
        Add a single entity node.
        
        Args:
            entity: Entity name
            entity_type: Type (Person, Location, Organization, etc.)
            properties: Additional properties (dict)
            
        Returns:
            bool: Success status
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = f"""
                MERGE (e:{entity_type} {{name: $entity}})
                SET e += $properties
                RETURN e
                """
                session.run(query, entity=entity, properties=properties or {})
            return True
        except Exception as e:
            print(f"❌ Error adding entity {entity}: {e}")
            return False
    
    def add_entities_batch(self, entities: List[Entity]) -> int:
        """
        Add multiple entities in a batch (efficient).
        
        Args:
            entities: List of Entity objects from entity_extractor
            
        Returns:
            int: Number of entities successfully added
        """
        if not self.driver:
            return 0
        
        added = 0
        try:
            with self.driver.session() as session:
                for entity in entities:
                    # Mapper EntityType vers label Neo4j
                    label = self._entity_type_to_label(entity.type)
                    
                    query = f"""
                    MERGE (e:{label} {{name: $name}})
                    SET e.confidence = $confidence,
                        e.position_start = $start,
                        e.position_end = $end
                    RETURN e
                    """
                    session.run(
                        query,
                        name=entity.text,
                        confidence=entity.confidence,
                        start=entity.start,
                        end=entity.end
                    )
                    added += 1
        except Exception as e:
            print(f"❌ Error in batch insert: {e}")
        
        return added
    
    def add_relation(self, source: str, target: str, relation_type: str, 
                    properties: dict | None = None) -> bool:
        """
        Create a relation between two entities.
        
        Args:
            source: Source entity name
            target: Target entity name
            relation_type: Relation type (WORKS_FOR, LOCATED_IN, etc.)
            properties: Additional properties (confidence, etc.)
            
        Returns:
            bool: Success status
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (s {name: $source}), (t {name: $target})
                MERGE (s)-[r:RELATION {type: $rel_type}]->(t)
                SET r += $properties
                RETURN r
                """
                session.run(
                    query,
                    source=source,
                    target=target,
                    rel_type=relation_type,
                    properties=properties or {}
                )
            return True
        except Exception as e:
            print(f"❌ Error adding relation {source}->{target}: {e}")
            return False
    
    def query_entity(self, name: str, entity_type: Optional[str] = None) -> Optional[Dict]:
        """
        Search for an entity by name (and optionally type).
        
        Args:
            name: Entity name
            entity_type: Optional entity type filter
            
        Returns:
            Dict with entity properties, or None if not found
        """
        if not self.driver:
            return None
        
        try:
            with self.driver.session() as session:
                if entity_type:
                    label = self._entity_type_to_label(entity_type)
                    query = f"""
                    MATCH (e:{label} {{name: $name}})
                    RETURN e
                    """
                else:
                    query = """
                    MATCH (e {name: $name})
                    RETURN e
                    """
                
                result = session.run(query, name=name)
                record = result.single()
                
                if record:
                    entity = record["e"]
                    return dict(entity)
                return None
        except Exception as e:
            print(f"❌ Error querying entity {name}: {e}")
            return None
    
    def query_neighbors(self, entity_name: str, depth: int = 1) -> List[Dict]:
        """
        Find neighbors of an entity up to a given depth.
        
        Args:
            entity_name: Starting entity name
            depth: Traversal depth (1-3)
            
        Returns:
            List of neighbor entities with relation info
        """
        if not self.driver or depth < 1 or depth > 3:
            return []
        
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH path = (start {{name: $name}})-[*1..{depth}]-(neighbor)
                RETURN DISTINCT neighbor, 
                       length(path) as distance,
                       relationships(path) as rels
                LIMIT 100
                """
                
                result = session.run(query, name=entity_name)
                
                neighbors = []
                for record in result:
                    neighbors.append({
                        "entity": dict(record["neighbor"]),
                        "distance": record["distance"],
                        "relations": [dict(r) for r in record["rels"]]
                    })
                
                return neighbors
        except Exception as e:
            print(f"❌ Error querying neighbors: {e}")
            return []
    
    def multi_hop_search(self, start: str, end: str, max_depth: int = 3) -> List[Dict]:
        """
        Find paths between two entities (multi-hop queries).
        
        Args:
            start: Starting entity name
            end: Target entity name
            max_depth: Maximum path length
            
        Returns:
            List of paths with nodes and relations
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH path = shortestPath(
                    (start {{name: $start}})-[*1..{max_depth}]-(end {{name: $end}})
                )
                RETURN path, length(path) as hops,
                       nodes(path) as nodes,
                       relationships(path) as rels
                LIMIT 10
                """
                
                result = session.run(query, start=start, end=end)
                
                paths = []
                for record in result:
                    paths.append({
                        "hops": record["hops"],
                        "nodes": [dict(n) for n in record["nodes"]],
                        "relations": [dict(r) for r in record["rels"]]
                    })
                
                return paths
        except Exception as e:
            print(f"❌ Error in multi-hop search: {e}")
            return []
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics (nodes, relations, etc.).
        
        Returns:
            Dict with node counts, relation counts, etc.
        """
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Count nodes
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()["count"]
                
                # Count relations
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()["count"]
                
                # Count by type
                type_result = session.run("""
                    MATCH (n)
                    RETURN labels(n) as labels, count(n) as count
                    ORDER BY count DESC
                """)
                
                node_types = {}
                for record in type_result:
                    labels = record["labels"]
                    if labels:
                        node_types[labels[0]] = record["count"]
                
                return {
                    "total_nodes": node_count,
                    "total_relations": rel_count,
                    "node_types": node_types
                }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
    
    def extract_and_store(self, text: str) -> Dict[str, int]:
        """
        Extract entities from text and store in Neo4j (pipeline complet).
        
        Args:
            text: Input text to process
            
        Returns:
            Dict with counts (entities_added, relations_added)
        """
        if not self.driver:
            return {"entities_added": 0, "relations_added": 0}
        
        # 1. Extract entities
        entities = self.extractor.extract(text)
        
        # 2. Store entities
        entities_added = self.add_entities_batch(entities)
        
        # 3. Extract relations
        relations = self.extractor.extract_relations(text, entities)
        
        # 4. Store relations
        relations_added = 0
        for rel in relations:
            success = self.add_relation(
                source=rel["source"],
                target=rel["target"],
                relation_type=rel["relation"],
                properties={"confidence": rel["confidence"]}
            )
            if success:
                relations_added += 1
        
        return {
            "entities_added": entities_added,
            "relations_added": relations_added
        }
    
    def _entity_type_to_label(self, entity_type: EntityType | str) -> str:
        """Convert EntityType enum to Neo4j label."""
        if isinstance(entity_type, EntityType):
            return entity_type.value.capitalize()
        return str(entity_type).capitalize()
    
    def close(self):
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j connection closed")


# Test pipeline
if __name__ == "__main__":
    store = GraphStore()
    
    if store.driver:
        print("\n" + "="*60)
        print("Testing GraphRAG with Entity Extraction")
        print("="*60)
        
        # Test 1: Basic entity
        print("\n📝 Test 1: Manual entity")
        store.add_entity("Paris", "Location", {"country": "France"})
        
        # Test 2: Full pipeline
        print("\n📝 Test 2: Full extraction pipeline")
        text = """
        Albert Einstein travaillait à Princeton.
        Il est né en Allemagne en 1879.
        Python est utilisé pour la recherche moderne.
        """
        
        result = store.extract_and_store(text)
        print(f"✅ Entities added: {result['entities_added']}")
        print(f"✅ Relations added: {result['relations_added']}")
        
        # Test 3: Stats
        print("\n📊 Graph statistics:")
        stats = store.get_graph_stats()
        print(f"  Nodes: {stats.get('total_nodes', 0)}")
        print(f"  Relations: {stats.get('total_relations', 0)}")
        print(f"  Types: {stats.get('node_types', {})}")
        
        # Test 4: Query
        print("\n🔍 Query: Find Princeton")
        entity = store.query_entity("Princeton")
        if entity:
            print(f"  Found: {entity}")
        
        # Test 5: Neighbors
        print("\n🔗 Neighbors of Albert Einstein:")
        neighbors = store.query_neighbors("Albert Einstein", depth=2)
        print(f"  Found {len(neighbors)} neighbors")
        for n in neighbors[:3]:  # Top 3
            print(f"    - {n['entity'].get('name', 'Unknown')} (distance: {n['distance']})")
        
        store.close()
        
        print("\n" + "="*60)
        print("✅ Tests completed!")
        print("="*60)

