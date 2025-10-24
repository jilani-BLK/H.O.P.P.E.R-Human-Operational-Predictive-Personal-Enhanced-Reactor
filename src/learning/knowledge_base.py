"""
Base de connaissances évolutive pour HOPPER
Extraction, stockage et indexation des connaissances
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class KnowledgeType(Enum):
    """Types de connaissances"""
    FACT = "fact"  # Fait établi
    CONCEPT = "concept"  # Concept ou définition
    PROCEDURE = "procedure"  # Procédure ou méthode
    RELATIONSHIP = "relationship"  # Relation entre entités
    EXAMPLE = "example"  # Exemple concret
    RULE = "rule"  # Règle ou contrainte


class SourceType(Enum):
    """Sources de connaissances"""
    DOCUMENT = "document"
    CONVERSATION = "conversation"
    CODE_ANALYSIS = "code_analysis"
    USER_CORRECTION = "user_correction"
    EXTERNAL_API = "external_api"


@dataclass
class KnowledgeEntry:
    """Entrée de connaissance"""
    id: str
    knowledge_type: KnowledgeType
    content: str
    
    # Métadonnées
    source: SourceType
    source_ref: str  # Référence à la source
    confidence: float = 0.8  # 0-1
    
    # Relations
    related_concepts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Temporalité
    created_at: datetime = field(default_factory=datetime.now)
    last_verified: Optional[datetime] = None
    times_used: int = 0
    
    # Contexte
    domain: Optional[str] = None
    language: str = "fr"
    
    # Validité
    valid: bool = True
    corrections: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class KnowledgeGraph:
    """Graphe de connaissances simplifié"""
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)  # (source, target, relation_type)


class KnowledgeBase:
    """
    Base de connaissances évolutive
    - Extrait connaissances de documents, conversations, code
    - Indexe par type, domaine, tags
    - Construit graphe de relations
    - Permet recherche et retrieval
    """
    
    def __init__(
        self,
        storage_path: str = "data/knowledge/",
        memory_manager: Optional[Any] = None
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.memory_manager = memory_manager
        
        # Stockage des connaissances
        self.knowledge: Dict[str, KnowledgeEntry] = {}
        
        # Index par type
        self.type_index: Dict[KnowledgeType, Set[str]] = {
            kt: set() for kt in KnowledgeType
        }
        
        # Index par tag
        self.tag_index: Dict[str, Set[str]] = {}
        
        # Index par domaine
        self.domain_index: Dict[str, Set[str]] = {}
        
        # Graphe de connaissances
        self.graph = KnowledgeGraph()
        
        # Statistiques
        self.stats = {
            "total_entries": 0,
            "facts": 0,
            "concepts": 0,
            "procedures": 0,
            "relationships": 0,
            "extractions": 0,
            "queries": 0
        }
        
        # Charger état
        self._load_state()
    
    def add_knowledge(
        self,
        content: str,
        knowledge_type: KnowledgeType,
        source: SourceType,
        source_ref: str,
        confidence: float = 0.8,
        tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        related_concepts: Optional[List[str]] = None
    ) -> str:
        """Ajoute une nouvelle connaissance"""
        
        # Générer ID
        knowledge_id = f"k_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Créer entrée
        entry = KnowledgeEntry(
            id=knowledge_id,
            knowledge_type=knowledge_type,
            content=content,
            source=source,
            source_ref=source_ref,
            confidence=confidence,
            tags=tags or [],
            domain=domain,
            related_concepts=related_concepts or []
        )
        
        # Stocker
        self.knowledge[knowledge_id] = entry
        
        # Indexer
        self.type_index[knowledge_type].add(knowledge_id)
        
        for tag in entry.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(knowledge_id)
        
        if domain:
            if domain not in self.domain_index:
                self.domain_index[domain] = set()
            self.domain_index[domain].add(knowledge_id)
        
        # Ajouter au graphe
        self._add_to_graph(entry)
        
        # Statistiques
        self.stats["total_entries"] += 1
        self.stats[knowledge_type.value + "s"] = self.stats.get(knowledge_type.value + "s", 0) + 1
        
        # Intégrer avec memory_manager si disponible
        if self.memory_manager:
            from .memory_manager import MemoryType
            self.memory_manager.add_memory(
                content=content,
                memory_type=MemoryType.KNOWLEDGE,
                importance=confidence,
                tags=tags or [],
                metadata={
                    "knowledge_id": knowledge_id,
                    "knowledge_type": knowledge_type.value,
                    "domain": domain
                }
            )
        
        # Sauvegarder
        self._save_state()
        
        return knowledge_id
    
    def extract_from_document(
        self,
        document_content: str,
        source_ref: str,
        domain: Optional[str] = None
    ) -> List[str]:
        """Extrait des connaissances d'un document"""
        
        extracted_ids = []
        self.stats["extractions"] += 1
        
        # Extraire définitions/concepts
        concepts = self._extract_concepts(document_content)
        for concept, definition in concepts:
            kid = self.add_knowledge(
                content=f"{concept}: {definition}",
                knowledge_type=KnowledgeType.CONCEPT,
                source=SourceType.DOCUMENT,
                source_ref=source_ref,
                tags=[concept],
                domain=domain
            )
            extracted_ids.append(kid)
        
        # Extraire procédures (étapes numérotées)
        procedures = self._extract_procedures(document_content)
        for proc_name, steps in procedures:
            kid = self.add_knowledge(
                content=f"Procédure {proc_name}: {steps}",
                knowledge_type=KnowledgeType.PROCEDURE,
                source=SourceType.DOCUMENT,
                source_ref=source_ref,
                tags=[proc_name, "procedure"],
                domain=domain
            )
            extracted_ids.append(kid)
        
        # Extraire exemples
        examples = self._extract_examples(document_content)
        for example_desc, example_code in examples:
            kid = self.add_knowledge(
                content=f"Exemple: {example_desc}\n{example_code}",
                knowledge_type=KnowledgeType.EXAMPLE,
                source=SourceType.DOCUMENT,
                source_ref=source_ref,
                tags=["example"],
                domain=domain
            )
            extracted_ids.append(kid)
        
        return extracted_ids
    
    def _extract_concepts(self, text: str) -> List[Tuple[str, str]]:
        """Extrait concepts et définitions"""
        concepts = []
        
        # Pattern: "X est Y" ou "X: Y"
        patterns = [
            r"([A-Z][a-zA-Zéèêàâôù]+)\s+(?:est|sont|désigne|représente)\s+(.+?)(?:\.|$)",
            r"([A-Z][a-zA-Zéèêàâôù]+)\s*:\s*(.+?)(?:\n|$)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                concept = match.group(1).strip()
                definition = match.group(2).strip()
                if len(definition) > 10 and len(definition) < 200:
                    concepts.append((concept, definition))
        
        return concepts[:10]  # Limiter à 10
    
    def _extract_procedures(self, text: str) -> List[Tuple[str, str]]:
        """Extrait procédures (étapes numérotées)"""
        procedures = []
        
        # Chercher sections avec étapes numérotées
        lines = text.split('\n')
        current_proc = None
        steps = []
        
        for line in lines:
            # Titre de procédure
            if any(keyword in line.lower() for keyword in ["procédure", "étapes", "méthode", "comment"]):
                if current_proc and steps:
                    procedures.append((current_proc, "; ".join(steps)))
                current_proc = line.strip()
                steps = []
            
            # Étape numérotée
            elif re.match(r'^\s*\d+[\.)]\s+', line):
                step = re.sub(r'^\s*\d+[\.)]\s+', '', line).strip()
                steps.append(step)
        
        if current_proc and steps:
            procedures.append((current_proc, "; ".join(steps)))
        
        return procedures
    
    def _extract_examples(self, text: str) -> List[Tuple[str, str]]:
        """Extrait exemples de code"""
        examples = []
        
        # Chercher blocs de code avec description
        pattern = r"(Exemple|Example|Par exemple)[^\n]*\n```([a-z]*)\n(.*?)\n```"
        matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            description = match.group(1)
            code = match.group(3).strip()
            if code:
                examples.append((description, code))
        
        return examples[:5]  # Limiter à 5
    
    def extract_from_conversation(
        self,
        conversation: List[Dict[str, str]],
        source_ref: str
    ) -> List[str]:
        """Extrait connaissances d'une conversation"""
        
        extracted_ids = []
        
        for turn in conversation:
            role = turn.get("role", "")
            content = turn.get("content", "")
            
            # Extraire corrections utilisateur
            if role == "user" and any(word in content.lower() for word in ["non", "erreur", "faux", "correction"]):
                kid = self.add_knowledge(
                    content=content,
                    knowledge_type=KnowledgeType.FACT,
                    source=SourceType.USER_CORRECTION,
                    source_ref=source_ref,
                    confidence=0.9,
                    tags=["correction"]
                )
                extracted_ids.append(kid)
            
            # Extraire faits mentionnés par l'assistant
            elif role == "assistant":
                facts = self._extract_facts(content)
                for fact in facts:
                    kid = self.add_knowledge(
                        content=fact,
                        knowledge_type=KnowledgeType.FACT,
                        source=SourceType.CONVERSATION,
                        source_ref=source_ref,
                        confidence=0.7,
                        tags=["conversation"]
                    )
                    extracted_ids.append(kid)
        
        return extracted_ids
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extrait faits d'un texte"""
        facts = []
        
        # Phrases déclaratives courtes
        sentences = re.split(r'[.!?]\s+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            # Critères: assertion, longueur raisonnable
            if (len(sentence) > 20 and len(sentence) < 150 and 
                not sentence.startswith(("Comment", "Pourquoi", "Que", "Quel"))):
                facts.append(sentence)
        
        return facts[:5]  # Limiter
    
    def search(
        self,
        query: str,
        knowledge_type: Optional[KnowledgeType] = None,
        tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        min_confidence: float = 0.5,
        max_results: int = 10
    ) -> List[KnowledgeEntry]:
        """Recherche dans la base de connaissances"""
        
        self.stats["queries"] += 1
        
        # Candidats
        candidates = set(self.knowledge.keys())
        
        # Filtrer par type
        if knowledge_type:
            candidates &= self.type_index[knowledge_type]
        
        # Filtrer par tags
        if tags:
            for tag in tags:
                if tag in self.tag_index:
                    candidates &= self.tag_index[tag]
        
        # Filtrer par domaine
        if domain and domain in self.domain_index:
            candidates &= self.domain_index[domain]
        
        # Filtrer par confiance
        candidates = [
            kid for kid in candidates
            if self.knowledge[kid].confidence >= min_confidence
        ]
        
        # Scoring basé sur query
        query_lower = query.lower()
        scored_results = []
        
        for kid in candidates:
            entry = self.knowledge[kid]
            content_lower = entry.content.lower()
            
            # Score de similarité simple
            score = 0.0
            
            # Mots communs
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            common_words = query_words & content_words
            if query_words:
                score += len(common_words) / len(query_words)
            
            # Bonus pour confiance et usage
            score += entry.confidence * 0.2
            score += min(entry.times_used / 10, 0.2)
            
            scored_results.append((score, entry))
        
        # Trier et limiter
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [entry for score, entry in scored_results[:max_results]]
        
        # Mettre à jour times_used
        for entry in results:
            entry.times_used += 1
        
        return results
    
    def get_related_knowledge(
        self,
        knowledge_id: str,
        max_results: int = 5
    ) -> List[KnowledgeEntry]:
        """Retourne connaissances liées"""
        
        if knowledge_id not in self.knowledge:
            return []
        
        entry = self.knowledge[knowledge_id]
        related_ids = set()
        
        # Via related_concepts
        for concept in entry.related_concepts:
            if concept in self.tag_index:
                related_ids.update(self.tag_index[concept])
        
        # Via tags communs
        for tag in entry.tags:
            if tag in self.tag_index:
                related_ids.update(self.tag_index[tag])
        
        # Via graphe
        for source, target, relation in self.graph.edges:
            if source == knowledge_id:
                related_ids.add(target)
            elif target == knowledge_id:
                related_ids.add(source)
        
        # Retirer l'entrée elle-même
        related_ids.discard(knowledge_id)
        
        # Récupérer entrées
        results = [self.knowledge[rid] for rid in related_ids if rid in self.knowledge]
        
        # Trier par confiance
        results.sort(key=lambda e: e.confidence, reverse=True)
        
        return results[:max_results]
    
    def _add_to_graph(self, entry: KnowledgeEntry) -> None:
        """Ajoute une entrée au graphe"""
        
        # Ajouter nœud
        self.graph.nodes[entry.id] = {
            "type": entry.knowledge_type.value,
            "content": entry.content[:100],  # Extrait
            "domain": entry.domain
        }
        
        # Ajouter arêtes vers concepts liés
        for concept in entry.related_concepts:
            # Chercher concepts existants
            for other_id, other_entry in self.knowledge.items():
                if concept.lower() in other_entry.content.lower():
                    self.graph.edges.append((entry.id, other_id, "relates_to"))
    
    def update_confidence(
        self,
        knowledge_id: str,
        new_confidence: float,
        reason: Optional[str] = None
    ) -> bool:
        """Met à jour la confiance d'une connaissance"""
        
        if knowledge_id not in self.knowledge:
            return False
        
        entry = self.knowledge[knowledge_id]
        old_confidence = entry.confidence
        entry.confidence = new_confidence
        entry.last_verified = datetime.now()
        
        if reason:
            entry.corrections.append({
                "timestamp": datetime.now().isoformat(),
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
                "reason": reason
            })
        
        self._save_state()
        return True
    
    def invalidate_knowledge(
        self,
        knowledge_id: str,
        reason: str
    ) -> bool:
        """Invalide une connaissance"""
        
        if knowledge_id not in self.knowledge:
            return False
        
        entry = self.knowledge[knowledge_id]
        entry.valid = False
        entry.corrections.append({
            "timestamp": datetime.now().isoformat(),
            "action": "invalidated",
            "reason": reason
        })
        
        self._save_state()
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        
        return {
            **self.stats,
            "knowledge_by_type": {
                kt.value: len(self.type_index[kt])
                for kt in KnowledgeType
            },
            "domains": len(self.domain_index),
            "tags": len(self.tag_index),
            "graph_nodes": len(self.graph.nodes),
            "graph_edges": len(self.graph.edges),
            "average_confidence": sum(e.confidence for e in self.knowledge.values()) / len(self.knowledge) if self.knowledge else 0
        }
    
    def export_knowledge(self, output_file: str) -> None:
        """Exporte la base de connaissances"""
        data = {
            "knowledge": {
                kid: {
                    "type": entry.knowledge_type.value,
                    "content": entry.content,
                    "confidence": entry.confidence,
                    "source": entry.source.value,
                    "tags": entry.tags,
                    "domain": entry.domain,
                    "created_at": entry.created_at.isoformat()
                }
                for kid, entry in self.knowledge.items()
                if entry.valid
            },
            "stats": self.get_statistics(),
            "export_date": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_state(self) -> None:
        """Sauvegarde l'état"""
        
        # Sauvegarder connaissances
        knowledge_file = self.storage_path / "knowledge.json"
        knowledge_data = {
            kid: {
                "knowledge_type": entry.knowledge_type.value,
                "content": entry.content,
                "source": entry.source.value,
                "source_ref": entry.source_ref,
                "confidence": entry.confidence,
                "related_concepts": entry.related_concepts,
                "tags": entry.tags,
                "created_at": entry.created_at.isoformat(),
                "last_verified": entry.last_verified.isoformat() if entry.last_verified else None,
                "times_used": entry.times_used,
                "domain": entry.domain,
                "language": entry.language,
                "valid": entry.valid,
                "corrections": entry.corrections
            }
            for kid, entry in self.knowledge.items()
        }
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder graphe
        graph_file = self.storage_path / "graph.json"
        graph_data = {
            "nodes": self.graph.nodes,
            "edges": self.graph.edges
        }
        
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder stats
        stats_file = self.storage_path / "stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def _load_state(self) -> None:
        """Charge l'état"""
        
        try:
            # Charger connaissances
            knowledge_file = self.storage_path / "knowledge.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge_data = json.load(f)
                
                for kid, kdata in knowledge_data.items():
                    entry = KnowledgeEntry(
                        id=kid,
                        knowledge_type=KnowledgeType(kdata["knowledge_type"]),
                        content=kdata["content"],
                        source=SourceType(kdata["source"]),
                        source_ref=kdata["source_ref"],
                        confidence=kdata["confidence"],
                        related_concepts=kdata.get("related_concepts", []),
                        tags=kdata.get("tags", []),
                        created_at=datetime.fromisoformat(kdata["created_at"]),
                        last_verified=datetime.fromisoformat(kdata["last_verified"]) if kdata.get("last_verified") else None,
                        times_used=kdata.get("times_used", 0),
                        domain=kdata.get("domain"),
                        language=kdata.get("language", "fr"),
                        valid=kdata.get("valid", True),
                        corrections=kdata.get("corrections", [])
                    )
                    
                    self.knowledge[kid] = entry
                    
                    # Reconstruire index
                    self.type_index[entry.knowledge_type].add(kid)
                    
                    for tag in entry.tags:
                        if tag not in self.tag_index:
                            self.tag_index[tag] = set()
                        self.tag_index[tag].add(kid)
                    
                    if entry.domain:
                        if entry.domain not in self.domain_index:
                            self.domain_index[entry.domain] = set()
                        self.domain_index[entry.domain].add(kid)
            
            # Charger graphe
            graph_file = self.storage_path / "graph.json"
            if graph_file.exists():
                with open(graph_file, 'r', encoding='utf-8') as f:
                    graph_data = json.load(f)
                self.graph.nodes = graph_data.get("nodes", {})
                self.graph.edges = [tuple(e) for e in graph_data.get("edges", [])]
            
            # Charger stats
            stats_file = self.storage_path / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.stats.update(json.load(f))
        
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    kb = KnowledgeBase()
    
    # Ajouter connaissance
    kid = kb.add_knowledge(
        content="Python est un langage de programmation interprété",
        knowledge_type=KnowledgeType.CONCEPT,
        source=SourceType.DOCUMENT,
        source_ref="doc_python_intro.md",
        tags=["python", "programming"],
        domain="programming"
    )
    
    # Rechercher
    results = kb.search("python langage", domain="programming")
    print(f"Résultats: {len(results)}")
    
    # Statistiques
    stats = kb.get_statistics()
    print(json.dumps(stats, indent=2))
