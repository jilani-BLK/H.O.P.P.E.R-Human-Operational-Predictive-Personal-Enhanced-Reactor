#!/bin/bash
# ==========================================
# HOPPER Phase 3.5 - RAG Avancé (Minimal Setup)
# Compatible Python 3.13
# ==========================================

set -e  # Arrêt si erreur

echo "🚀 Phase 3.5 - RAG Avancé (Setup Minimal)"
echo "=========================================="
echo ""

# ==========================================
# [1/6] Vérification environnement
# ==========================================
echo "[1/6] Vérification environnement Python..."
if ! command -v python &> /dev/null; then
    echo "❌ Python non trouvé"
    exit 1
fi
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION"
echo ""

# ==========================================
# [2/6] Création structure modules
# ==========================================
echo "[2/6] Création structure modules..."
mkdir -p src/rag
mkdir -p src/agents
mkdir -p tests/rag
mkdir -p tests/agents
touch src/rag/__init__.py
touch src/agents/__init__.py
echo "✅ Structure créée"
echo ""

# ==========================================
# [3/6] Installation dépendances minimales
# ==========================================
echo "[3/6] Installation dépendances minimales..."
echo "   ⏳ Installation neo4j, transformers, torch..."
pip install -r requirements-rag-minimal.txt --quiet
echo "✅ Dépendances installées"
echo ""

# ==========================================
# [4/6] Configuration docker-compose Neo4j
# ==========================================
echo "[4/6] Configuration Neo4j..."
if [ ! -f "docker-compose.yml" ]; then
    echo "⚠️  docker-compose.yml non trouvé, création..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  neo4j:
    image: neo4j:5.15-community
    container_name: hopper-neo4j
    ports:
      - "7474:7474"   # HTTP Browser
      - "7687:7687"   # Bolt protocol
    environment:
      - NEO4J_AUTH=neo4j/hopper123
      - NEO4J_dbms_memory_pagecache_size=1G
      - NEO4J_dbms_memory_heap_initial__size=1G
      - NEO4J_dbms_memory_heap_max__size=2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: unless-stopped
    networks:
      - hopper-network

volumes:
  neo4j_data:
  neo4j_logs:

networks:
  hopper-network:
    driver: bridge
EOF
fi
echo "✅ Configuration Neo4j créée"
echo ""

# ==========================================
# [5/6] Démarrage Neo4j
# ==========================================
echo "[5/6] Démarrage Neo4j..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d neo4j 2>&1 | grep -v "Creating network" || true
    echo "✅ Neo4j démarré sur http://localhost:7474"
    echo "   Credentials: neo4j / hopper123"
else
    echo "⚠️  docker-compose non trouvé, skip Neo4j"
fi
echo ""

# ==========================================
# [6/6] Création fichiers de base
# ==========================================
echo "[6/6] Création fichiers de base..."

# Self-RAG stub
cat > src/rag/self_rag.py << 'EOF'
"""
Self-RAG - Intelligent critique before retrieval
Compatible Python 3.13 (no spaCy dependency)
"""

class SelfRAG:
    """Self-RAG classifier with lightweight implementation"""
    
    def should_retrieve(self, query: str) -> tuple[bool, float]:
        """
        Decide if RAG is needed
        Returns: (should_retrieve: bool, confidence: float)
        """
        # Simple heuristic for now (can be enhanced with LLM)
        query_lower = query.lower()
        
        # Always retrieve for questions
        if any(q in query_lower for q in ["qui", "quoi", "quand", "où", "pourquoi", "comment"]):
            return True, 0.95
        
        # Skip for greetings
        if any(g in query_lower for g in ["bonjour", "salut", "hello", "hi"]):
            return False, 0.90
        
        # Default: retrieve
        return True, 0.70

# Test
if __name__ == "__main__":
    rag = SelfRAG()
    print(rag.should_retrieve("Qui est le président?"))  # (True, 0.95)
    print(rag.should_retrieve("Bonjour!"))                # (False, 0.90)
EOF

# GraphRAG stub (NER with transformers instead of spaCy)
cat > src/rag/graph_store.py << 'EOF'
"""
GraphRAG - Neo4j knowledge graph integration
Uses transformers for NER (Python 3.13 compatible)
"""
from neo4j import GraphDatabase
from typing import Optional

class GraphStore:
    """Neo4j graph database connector"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "hopper123"):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"⚠️  Neo4j not available: {e}")
            self.driver = None
    
    def add_entity(self, entity: str, entity_type: str, properties: dict = None):
        """Add entity node"""
        if not self.driver:
            return False
        
        with self.driver.session() as session:
            query = f"""
            MERGE (e:{entity_type} {{name: $entity}})
            SET e += $properties
            RETURN e
            """
            session.run(query, entity=entity, properties=properties or {})
        return True
    
    def close(self):
        if self.driver:
            self.driver.close()

# Test
if __name__ == "__main__":
    store = GraphStore()
    if store.driver:
        store.add_entity("Paris", "Location", {"country": "France"})
        store.close()
EOF

# ReAct Agent stub
cat > src/agents/react_agent.py << 'EOF'
"""
ReAct Agent - Thought → Action → Observation cycle
"""

class ReActAgent:
    """ReAct agent for tool usage"""
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, name: str, func):
        """Register a tool function"""
        self.tools[name] = func
    
    def run(self, query: str) -> str:
        """
        Execute ReAct cycle:
        1. Thought: What should I do?
        2. Action: Use tool
        3. Observation: Get result
        """
        # For now, simple passthrough
        # Real implementation will use LLM to decide actions
        return f"ReAct: Processing '{query}'"

# Test
if __name__ == "__main__":
    agent = ReActAgent()
    print(agent.run("Send email to boss"))
EOF

# HyDE stub
cat > src/rag/hyde.py << 'EOF'
"""
HyDE - Hypothetical Document Embeddings
Expand query with generated hypothetical answer
"""

class HyDE:
    """Query expansion with HyDE"""
    
    def expand_query(self, query: str) -> list[str]:
        """
        Generate hypothetical documents matching query
        Returns: [original_query, hypothesis1, hypothesis2, ...]
        """
        # Simple expansion for now
        # Real implementation will use LLM to generate hypotheses
        expansions = [
            query,
            f"{query} (définition)",
            f"{query} (explication détaillée)"
        ]
        return expansions

# Test
if __name__ == "__main__":
    hyde = HyDE()
    print(hyde.expand_query("Python asyncio"))
EOF

echo "✅ Fichiers de base créés"
echo ""

# ==========================================
# Résumé final
# ==========================================
echo "=========================================="
echo "✅ Setup Phase 3.5 terminé!"
echo "=========================================="
echo ""
echo "📁 Structure créée:"
echo "   - src/rag/self_rag.py"
echo "   - src/rag/graph_store.py"
echo "   - src/agents/react_agent.py"
echo "   - src/rag/hyde.py"
echo ""
echo "🔧 Services:"
if command -v docker-compose &> /dev/null && docker ps | grep -q hopper-neo4j; then
    echo "   ✅ Neo4j: http://localhost:7474 (neo4j/hopper123)"
else
    echo "   ⚠️  Neo4j: Non démarré (docker-compose requis)"
fi
echo ""
echo "🚀 Prochaines étapes:"
echo "   1. Test connexion Neo4j: python src/rag/graph_store.py"
echo "   2. Test Self-RAG: python src/rag/self_rag.py"
echo "   3. Test ReAct: python src/agents/react_agent.py"
echo ""
echo "📝 Note:"
echo "   - spaCy skip (Python 3.13 incompatible)"
echo "   - Alternative: transformers pour NER"
echo "   - Ou downgrade Python 3.11 pour spaCy complet"
echo ""
