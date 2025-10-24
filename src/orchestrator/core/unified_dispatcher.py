"""
Unified Dispatcher - Phase 3.5 Week 4
Orchestrateur central qui route les requetes via Self-RAG vers les bons modules.

Architecture:
    Query → Self-RAG classification → Dispatcher → [GraphRAG | ReAct | HyDE | Direct] → Response

Integration:
    - Week 1 (Self-RAG): Classification des requetes
    - Week 2 (GraphRAG): Recherche dans knowledge graph
    - Week 3 (ReAct Agent): Execution d'actions
    - Week 4 (HyDE): Expansion queries vagues

Auteur: Copilot + Jilani
Date: Octobre 2025
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

# Imports des modules Phase 3.5
from src.rag.self_rag import SelfRAG, ClassificationResult
from src.rag.hyde import HyDE, HyDEResult
# GraphRAG et ReAct seront importes dynamiquement si disponibles


class ResponseType(Enum):
    """Type de reponse generee."""
    DIRECT = "direct"              # Reponse directe (simple query)
    GRAPH = "graph"                # Via GraphRAG (recherche)
    AGENT = "agent"                # Via ReAct Agent (action)
    HYDE = "hyde"                  # Via HyDE + recherche (vague)
    ERROR = "error"                # Erreur de traitement


@dataclass
class UnifiedResponse:
    """Reponse unifiee du dispatcher."""
    query_original: str                    # Query originale
    query_classification: str              # Classification Self-RAG (category)
    response_type: ResponseType            # Type de reponse
    content: str                           # Contenu de la reponse
    metadata: Dict[str, Any] = field(default_factory=dict)  # Metadata additionnelle
    processing_time: float = 0.0           # Temps de traitement (s)
    success: bool = True                   # Succès ou echec
    error: Optional[str] = None            # Message d'erreur si echec
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_original": self.query_original,
            "query_classification": self.query_classification,
            "response_type": self.response_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "processing_time": self.processing_time,
            "success": self.success,
            "error": self.error
        }


class UnifiedDispatcher:
    """
    Dispatcher unifie pour router les requetes via Self-RAG.
    
    Workflow:
        1. Classify query via Self-RAG
        2. Route vers module approprie:
           - SIMPLE → Reponse directe
           - RECHERCHE → GraphRAG
           - ACTION → ReAct Agent
           - VAGUE → HyDE + recherche
        3. Format response unifiee
        4. Return avec metadata
    
    Exemple:
        >>> dispatcher = UnifiedDispatcher()
        >>> response = dispatcher.process_query("comment envoyer un email?")
        >>> print(response.response_type)  # ResponseType.AGENT
        >>> print(response.content)  # Resultat de l'action
    """
    
    def __init__(
        self,
        self_rag: Optional[SelfRAG] = None,
        hyde: Optional[HyDE] = None,
        enable_graph: bool = True,
        enable_agent: bool = True,
        enable_hyde: bool = True,
        timeout: float = 30.0
    ):
        """
        Initialise le dispatcher.
        
        Args:
            self_rag: Instance Self-RAG (cree si None)
            hyde: Instance HyDE (cree si None)
            enable_graph: Active GraphRAG
            enable_agent: Active ReAct Agent
            enable_hyde: Active HyDE
            timeout: Timeout global (secondes)
        """
        self.self_rag = self_rag or SelfRAG()
        self.hyde = hyde or HyDE(num_docs=3)
        self.enable_graph = enable_graph
        self.enable_agent = enable_agent
        self.enable_hyde = enable_hyde
        self.timeout = timeout
        
        # Modules optionnels (lazy loading)
        self._graph_rag = None
        self._react_agent = None
        
        # Stats
        self.stats = {
            "total_queries": 0,
            "direct_responses": 0,
            "graph_responses": 0,
            "agent_responses": 0,
            "hyde_responses": 0,
            "errors": 0,
            "total_processing_time": 0.0
        }
    
    def _load_graph_rag(self):
        """Charge GraphRAG (lazy loading)."""
        if self._graph_rag is None and self.enable_graph:
            try:
                from src.rag.graph_store import GraphStore
                self._graph_rag = GraphStore()
            except ImportError:
                print("GraphRAG not available")
                self._graph_rag = None
        return self._graph_rag
    
    def _load_react_agent(self):
        """Charge ReAct Agent (lazy loading)."""
        if self._react_agent is None and self.enable_agent:
            try:
                from src.agents.react_agent import ReActAgent
                self._react_agent = ReActAgent()
                # Register default tools
                self._register_default_tools()
            except ImportError:
                print("ReAct Agent not available")
                self._react_agent = None
        return self._react_agent
    
    def _register_default_tools(self):
        """Enregistre les outils par defaut pour ReAct Agent."""
        if not self._react_agent:
            return
        
        try:
            from src.agents.tools.email_tool import EmailTool
            from src.agents.tools.file_tool import ReadFileTool
            from src.agents.tools.notes_tool import CreateNoteTool
            
            # Email
            email_tool = EmailTool()
            meta = email_tool.metadata  # Property, not method
            self._react_agent.register_tool(meta.name, email_tool.execute, meta.description, meta.schema)
            
            # File
            read_tool = ReadFileTool()
            meta = read_tool.metadata  # Property, not method
            self._react_agent.register_tool(meta.name, read_tool.execute, meta.description, meta.schema)
            
            # Notes
            create_note = CreateNoteTool()
            meta = create_note.metadata  # Property, not method
            self._react_agent.register_tool(meta.name, create_note.execute, meta.description, meta.schema)
            
        except ImportError:
            pass
    
    def _process_simple_query(self, query: str) -> str:
        """Traite une query simple (reponse directe)."""
        # En production: utiliser un LLM leger pour reponse directe
        # Pour tests: reponse simple
        return f"Reponse directe: La question '{query}' est de type SIMPLE. Une reponse courte suffit."
    
    def _process_recherche_query(self, query: str) -> str:
        """Traite une query de recherche (GraphRAG)."""
        graph = self._load_graph_rag()
        
        if graph is None:
            return f"GraphRAG non disponible. Query: {query}"
        
        # Recherche dans le graph
        # Pour tests: reponse simulee
        return f"Resultat GraphRAG: Entites et relations trouvees pour '{query}'."
    
    def _process_action_query(self, query: str) -> str:
        """Traite une query d'action (ReAct Agent)."""
        agent = self._load_react_agent()
        
        if agent is None:
            return f"ReAct Agent non disponible. Query: {query}"
        
        # Execute l'action via agent (async wrapper)
        try:
            import asyncio
            # Check if we're in an event loop
            try:
                loop = asyncio.get_running_loop()
                # Already in async context - this shouldn't happen in sync dispatcher
                return "Erreur: dispatcher sync appele depuis contexte async"
            except RuntimeError:
                # No running loop - create one
                result = asyncio.run(agent.run(query))
            
            if result.get("success"):
                return result.get("answer", "Action executee avec succes")
            else:
                return f"Action incomplete: erreur dans l'execution"
        except Exception as e:
            return f"Erreur agent: {str(e)}"
    
    def _process_vague_query(self, query: str) -> str:
        """Traite une query vague (HyDE + recherche)."""
        if not self.enable_hyde:
            return self._process_simple_query(query)
        
        # Expanse la query via HyDE
        hyde_result = self.hyde.expand_query(query)
        
        if not hyde_result.success:
            return f"Erreur HyDE: {hyde_result.error}"
        
        # Utilise les queries expansees pour recherche
        # Pour tests: retourne les queries alternatives
        expanded = ", ".join(hyde_result.expanded_queries[:3])
        return f"Query expansee via HyDE: '{query}' → Alternatives: [{expanded}]"
    
    def process_query(self, query: str) -> UnifiedResponse:
        """
        Traite une query via le pipeline complet.
        
        Args:
            query: Query utilisateur
        
        Returns:
            UnifiedResponse avec resultat et metadata
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # 1. Classification via Self-RAG
            classification_result = self.self_rag.classify(query)
            decision = classification_result.decision
            
            # 2. Routing selon decision
            if decision.value == "no_retrieve":
                # Query simple, reponse directe
                content = self._process_simple_query(query)
                response_type = ResponseType.DIRECT
                self.stats["direct_responses"] += 1
                classification_str = "SIMPLE"
                
            elif decision.value == "retrieve":
                # Need retrieval - check type
                query_lower = query.lower()
                
                # Check for action words
                if any(word in query_lower for word in ["envoie", "cree", "execute", "lance", "fais"]):
                    content = self._process_action_query(query)
                    response_type = ResponseType.AGENT
                    self.stats["agent_responses"] += 1
                    classification_str = "ACTION"
                # Check for vague query (very short + interrogative)
                elif (len(query.split()) <= 4 and 
                      any(word in query_lower for word in ["comment", "quoi", "pourquoi", "ca", "ça", "truc"])):
                    content = self._process_vague_query(query)
                    response_type = ResponseType.HYDE
                    self.stats["hyde_responses"] += 1
                    classification_str = "VAGUE"
                else:
                    # Recherche query
                    content = self._process_recherche_query(query)
                    response_type = ResponseType.GRAPH
                    self.stats["graph_responses"] += 1
                    classification_str = "RECHERCHE"
                    
            else:  # uncertain
                # Query vague - use HyDE
                content = self._process_vague_query(query)
                response_type = ResponseType.HYDE
                self.stats["hyde_responses"] += 1
                classification_str = "VAGUE"
            
            # 3. Construction response
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time
            
            return UnifiedResponse(
                query_original=query,
                query_classification=classification_str,
                response_type=response_type,
                content=content,
                metadata={
                    "dispatcher_version": "1.0",
                    "modules_used": [response_type.value],
                    "self_rag_confidence": classification_result.confidence
                },
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats["errors"] += 1
            
            return UnifiedResponse(
                query_original=query,
                query_classification="ERROR",
                response_type=ResponseType.ERROR,
                content="",
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    async def process_query_async(self, query: str) -> UnifiedResponse:
        """Version async de process_query."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.process_query, query)
        return result
    
    def process_batch(self, queries: List[str]) -> List[UnifiedResponse]:
        """Traite un batch de queries."""
        return [self.process_query(q) for q in queries]
    
    async def process_batch_async(self, queries: List[str]) -> List[UnifiedResponse]:
        """Version async de process_batch."""
        tasks = [self.process_query_async(q) for q in queries]
        return await asyncio.gather(*tasks)
    
    def get_stats(self) -> Dict[str, Any]:
        """Recupere les statistiques."""
        total = self.stats["total_queries"]
        
        return {
            "total_queries": total,
            "direct_responses": self.stats["direct_responses"],
            "graph_responses": self.stats["graph_responses"],
            "agent_responses": self.stats["agent_responses"],
            "hyde_responses": self.stats["hyde_responses"],
            "errors": self.stats["errors"],
            "success_rate": (
                (total - self.stats["errors"]) / total if total > 0 else 0.0
            ),
            "average_processing_time": (
                self.stats["total_processing_time"] / total if total > 0 else 0.0
            )
        }


if __name__ == "__main__":
    print("=== Unified Dispatcher Manual Tests ===\n")
    
    dispatcher = UnifiedDispatcher()
    
    # Test 1: Query simple
    print("Test 1: Query SIMPLE")
    response = dispatcher.process_query("Bonjour, comment vas-tu?")
    print(f"  Classification: {response.query_classification}")
    print(f"  Response type: {response.response_type.value}")
    print(f"  Content: {response.content[:80]}...")
    print(f"  Processing time: {response.processing_time:.3f}s\n")
    
    # Test 2: Query recherche
    print("Test 2: Query RECHERCHE")
    response = dispatcher.process_query("Quels sont les evenements recents?")
    print(f"  Classification: {response.query_classification}")
    print(f"  Response type: {response.response_type.value}")
    print(f"  Content: {response.content[:80]}...\n")
    
    # Test 3: Query action
    print("Test 3: Query ACTION")
    response = dispatcher.process_query("Envoie un email a john@example.com")
    print(f"  Classification: {response.query_classification}")
    print(f"  Response type: {response.response_type.value}")
    print(f"  Content: {response.content[:80]}...\n")
    
    # Test 4: Query vague
    print("Test 4: Query VAGUE")
    response = dispatcher.process_query("comment ca marche?")
    print(f"  Classification: {response.query_classification}")
    print(f"  Response type: {response.response_type.value}")
    print(f"  Content: {response.content[:100]}...\n")
    
    # Test 5: Batch
    print("Test 5: Batch processing")
    queries = ["Salut!", "Qui est Einstein?", "Cree une note"]
    responses = dispatcher.process_batch(queries)
    print(f"  Batch size: {len(responses)}")
    print(f"  All successful: {all(r.success for r in responses)}\n")
    
    # Stats
    print("Stats finales:")
    stats = dispatcher.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
