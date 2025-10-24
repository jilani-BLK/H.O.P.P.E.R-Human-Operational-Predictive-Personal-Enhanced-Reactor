#!/bin/bash
# Script de démarrage rapide Phase 3.5 - RAG Avancé
# Installe et configure GraphRAG + ReAct + Self-RAG

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         HOPPER Phase 3.5 - RAG Avancé Setup                 ║${NC}"
echo -e "${BLUE}║   GraphRAG + ReAct Agent + Self-RAG + HyDE                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier Python
echo -e "${GREEN}[1/8] Vérification environnement Python...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python non trouvé. Installé Python 3.11+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION"
echo ""

# Créer structure de répertoires
echo -e "${GREEN}[2/8] Création structure modules...${NC}"
mkdir -p src/rag
mkdir -p src/agents/tools
mkdir -p tests/rag
mkdir -p tests/agents
touch src/rag/__init__.py
touch src/agents/__init__.py
touch src/agents/tools/__init__.py
echo "✅ Structure créée"
echo ""

# Installer dépendances
echo -e "${GREEN}[3/8] Installation dépendances...${NC}"
if [ -f "requirements-rag-advanced.txt" ]; then
    pip install -q -r requirements-rag-advanced.txt
    echo "✅ Dépendances installées"
else
    echo -e "${YELLOW}⚠️  Fichier requirements-rag-advanced.txt non trouvé${NC}"
fi
echo ""

# Télécharger modèle spaCy
echo -e "${GREEN}[4/8] Téléchargement modèle NER français...${NC}"
python -m spacy download fr_core_news_lg 2>&1 | grep -v "Requirement already satisfied" || true
echo "✅ Modèle spaCy fr_core_news_lg prêt"
echo ""

# Configurer Neo4j dans docker-compose
echo -e "${GREEN}[5/8] Configuration Neo4j...${NC}"

# Vérifier si Neo4j déjà dans docker-compose
if grep -q "neo4j:" docker-compose.yml; then
    echo "✅ Neo4j déjà configuré"
else
    echo -e "${YELLOW}⚠️  Ajout Neo4j au docker-compose.yml...${NC}"
    
    # Backup docker-compose
    cp docker-compose.yml docker-compose.yml.backup-rag
    
    # Ajouter service Neo4j
    cat >> docker-compose.yml << 'EOF'

  # Neo4j - GraphRAG Database (Phase 3.5)
  neo4j:
    image: neo4j:5.15-community
    container_name: hopper-neo4j
    ports:
      - "7474:7474"  # HTTP/Browser
      - "7687:7687"  # Bolt protocol
    environment:
      - NEO4J_AUTH=neo4j/hopper123
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - hopper-network
    healthcheck:
      test: ["CMD", "neo4j", "status"]
      interval: 10s
      timeout: 5s
      retries: 5
EOF

    # Ajouter volumes
    if ! grep -q "neo4j_data:" docker-compose.yml; then
        cat >> docker-compose.yml << 'EOF'

volumes:
  neo4j_data:
  neo4j_logs:
EOF
    fi
    
    echo "✅ Neo4j ajouté au docker-compose.yml"
fi
echo ""

# Démarrer Neo4j
echo -e "${GREEN}[6/8] Démarrage Neo4j...${NC}"
docker-compose up -d neo4j 2>&1 | grep -v "Network.*Creating" || true
sleep 5

# Vérifier Neo4j
if curl -s http://localhost:7474 > /dev/null; then
    echo "✅ Neo4j opérationnel sur http://localhost:7474"
    echo "   Credentials: neo4j / hopper123"
else
    echo -e "${YELLOW}⚠️  Neo4j en cours de démarrage (peut prendre 30s)${NC}"
fi
echo ""

# Créer fichiers de base
echo -e "${GREEN}[7/8] Création fichiers de base...${NC}"

# self_rag.py stub
cat > src/rag/self_rag.py << 'EOF'
"""
Self-RAG: Critique intelligente pour éviter récupération inutile
Voir: docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md (Semaine 1)
"""

from typing import Literal, Dict, Any
from loguru import logger

DecisionType = Literal["direct", "knowledge", "action", "fuzzy"]


class SelfRAG:
    """Décide si RAG est nécessaire avant de récupérer"""
    
    def __init__(self, llm_client=None, threshold: float = 0.7):
        self.llm = llm_client
        self.threshold = threshold
        logger.info("✅ Self-RAG initialisé")
    
    def decide(self, query: str, context: Dict[str, Any]) -> DecisionType:
        """
        Décide du type de traitement nécessaire
        
        TODO: Implémenter selon PLAN_IMPLEMENTATION_RAG_AVANCE.md
        """
        # Placeholder: toujours retourner "knowledge" pour l'instant
        return "knowledge"
EOF

# graph_store.py stub
cat > src/rag/graph_store.py << 'EOF'
"""
GraphRAG: Base de connaissances avec relations structurées
Voir: docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md (Semaine 2)
"""

from neo4j import GraphDatabase
from loguru import logger


class GraphRAG:
    """Store de connaissances en graphe"""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "hopper123"
    ):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info("✅ GraphRAG connecté à Neo4j")
        except Exception as e:
            logger.error(f"❌ Connexion Neo4j échouée: {e}")
            self.driver = None
    
    def close(self):
        if self.driver:
            self.driver.close()
EOF

# react_agent.py stub
cat > src/agents/react_agent.py << 'EOF'
"""
ReAct Agent: Reasoning + Acting
Voir: docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md (Semaine 3)
"""

from typing import Dict, Callable, Any
from loguru import logger


class ReActAgent:
    """Agent avec capacité de raisonnement et d'action"""
    
    def __init__(self, llm_client=None, tools: Dict[str, Callable] = None):
        self.llm = llm_client
        self.tools = tools or {}
        logger.info("✅ ReAct Agent initialisé")
    
    def run(self, query: str, max_steps: int = 5) -> str:
        """
        Cycle Thought → Action → Observation
        
        TODO: Implémenter selon PLAN_IMPLEMENTATION_RAG_AVANCE.md
        """
        return "ReAct Agent: TODO"
EOF

# hyde.py stub
cat > src/rag/hyde.py << 'EOF'
"""
HyDE: Hypothetical Document Embeddings
Voir: docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md (Semaine 4)
"""

from loguru import logger


class HyDE:
    """Expansion de requêtes floues via documents hypothétiques"""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        logger.info("✅ HyDE initialisé")
    
    def expand_query(self, vague_query: str) -> str:
        """
        Génère document hypothétique depuis requête floue
        
        TODO: Implémenter selon PLAN_IMPLEMENTATION_RAG_AVANCE.md
        """
        return vague_query  # Placeholder
EOF

echo "✅ Fichiers de base créés (stubs)"
echo ""

# Test de connexion Neo4j
echo -e "${GREEN}[8/8] Test de connexion Neo4j...${NC}"

python << 'PYEOF'
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "hopper123")
    )
    with driver.session() as session:
        result = session.run("RETURN 'Hello Neo4j!' as message")
        print(f"✅ {result.single()['message']}")
    driver.close()
except Exception as e:
    print(f"⚠️  Connexion Neo4j: {e}")
    print("   (Neo4j peut prendre jusqu'à 30s pour démarrer)")
PYEOF

echo ""

# Résumé
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    ✅ Setup Terminé                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}Prochaines étapes:${NC}"
echo ""
echo "1. 📚 Lire la documentation:"
echo "   - docs/ARCHITECTURE_RAG_AVANCEE.md"
echo "   - docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md"
echo "   - docs/ARCHITECTURE_RAG_VISUELLE.md"
echo ""
echo "2. 🌐 Neo4j Browser:"
echo "   - URL: http://localhost:7474"
echo "   - User: neo4j"
echo "   - Password: hopper123"
echo ""
echo "3. 🔨 Implémenter modules (4 semaines):"
echo "   - Semaine 1: src/rag/self_rag.py (critique RAG)"
echo "   - Semaine 2: src/rag/graph_store.py (GraphRAG)"
echo "   - Semaine 3: src/agents/react_agent.py (ReAct)"
echo "   - Semaine 4: src/rag/hyde.py + intégration"
echo ""
echo "4. 🧪 Tests:"
echo "   pytest tests/rag/ tests/agents/ -v"
echo ""
echo "5. 📊 Monitoring:"
echo "   docker stats hopper-neo4j"
echo "   docker logs hopper-neo4j"
echo ""

echo -e "${YELLOW}💡 Tips:${NC}"
echo "   - Copier implémentations depuis docs/PLAN_IMPLEMENTATION_RAG_AVANCE.md"
echo "   - Chaque module a des tests inclus dans le plan"
echo "   - Neo4j Browser permet de visualiser le graphe de connaissances"
echo ""

echo -e "${GREEN}🚀 HOPPER Phase 3.5 prêt à être développé !${NC}"
