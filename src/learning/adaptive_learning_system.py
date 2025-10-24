"""
Système d'apprentissage adaptatif intégré pour HOPPER
Orchestre tous les composants pour un apprentissage continu sous contrôle humain
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Imports des composants
from .memory_manager import MemoryManager, MemoryType
from .preference_manager import PreferenceManager, PreferenceCategory
from .feedback_system import FeedbackSystem, FeedbackType
from .adaptation_engine_contextual import AdaptationEngine, ContextType
from .knowledge_base import KnowledgeBase, KnowledgeType, SourceType
from .validation_system import ValidationSystem, ValidationType, RiskLevel


class AdaptiveLearningSystem:
    """
    Système d'apprentissage adaptatif complet
    Intègre tous les composants pour un apprentissage continu
    """
    
    def __init__(
        self,
        storage_path: str = "data/",
        auto_approve_low_risk: bool = True
    ):
        """
        Initialise le système complet
        
        Args:
            storage_path: Chemin de base pour le stockage
            auto_approve_low_risk: Auto-approuver les adaptations à faible risque
        """
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialiser tous les composants
        print("Initialisation du système d'apprentissage adaptatif...")
        
        # 1. Mémoire à long terme
        self.memory = MemoryManager(
            str(self.storage_path / "memory")
        )
        
        # 2. Gestionnaire de préférences
        self.preferences = PreferenceManager(
            storage_path=str(self.storage_path / "preferences" / "user_preferences.json")
        )
        
        # 3. Système de feedback
        self.feedback = FeedbackSystem(
            storage_path=str(self.storage_path / "feedback"),
            memory_manager=self.memory,
            preference_manager=self.preferences
        )
        
        # 4. Moteur d'adaptation
        self.adaptation = AdaptationEngine(
            memory_manager=self.memory,
            preference_manager=self.preferences,
            feedback_system=self.feedback,
            storage_path=str(self.storage_path / "adaptation")
        )
        
        # 5. Base de connaissances
        self.knowledge = KnowledgeBase(
            storage_path=str(self.storage_path / "knowledge"),
            memory_manager=self.memory
        )
        
        # 6. Système de validation
        self.validation = ValidationSystem(
            storage_path=str(self.storage_path / "validation"),
            auto_approve_low_risk=auto_approve_low_risk
        )
        
        print("✓ Tous les composants initialisés")
    
    # ===== API PRINCIPALE =====
    
    def process_interaction(
        self,
        user_prompt: str,
        assistant_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Traite une interaction complète
        - Met à jour le contexte
        - Enregistre en mémoire
        - Observe pour préférences
        - Extrait connaissances
        
        Returns:
            Informations sur le traitement
        """
        
        context = context or {}
        interaction_id = f"int_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 1. Mettre à jour le contexte d'adaptation
        self.adaptation.update_context(
            task_type=context.get("task_type", "general"),
            user_expertise=context.get("user_expertise", "intermediate"),
            conversation_depth=context.get("conversation_depth", 0),
            user_sentiment=context.get("user_sentiment", "neutral")
        )
        
        # 2. Enregistrer en mémoire
        self.memory.add_memory(
            content=f"User: {user_prompt}\nAssistant: {assistant_response}",
            memory_type=MemoryType.CONVERSATION,
            importance=0.6,
            tags=["interaction"],
            metadata={
                "interaction_id": interaction_id,
                "task_type": context.get("task_type")
            }
        )
        
        # 3. Observer pour préférences
        self.preferences.observe_interaction({
            "response_length": len(assistant_response),
            "topic": context.get("task_type", "general")
        })
        
        # 4. Extraire connaissances de la conversation
        knowledge_ids = self.knowledge.extract_from_conversation(
            [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_response}
            ],
            source_ref=interaction_id
        )
        
        return {
            "interaction_id": interaction_id,
            "knowledge_extracted": len(knowledge_ids),
            "current_behavior": self.adaptation.get_current_behavior()
        }
    
    def submit_feedback(
        self,
        interaction_id: str,
        prompt: str,
        response: str,
        feedback_type: FeedbackType,
        comment: Optional[str] = None,
        correction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Soumet un feedback utilisateur
        
        Returns:
            Résultat du traitement du feedback
        """
        
        feedback_id = self.feedback.submit_feedback(
            interaction_id=interaction_id,
            prompt=prompt,
            response=response,
            feedback_type=feedback_type,
            comment=comment,
            correction=correction
        )
        
        # Analyser si adaptation nécessaire
        problematic = self.feedback.get_problematic_patterns(min_occurrences=2)
        
        result = {
            "feedback_id": feedback_id,
            "problematic_patterns": len(problematic)
        }
        
        # Si patterns problématiques identifiés, proposer adaptation
        if problematic:
            adaptation_suggestions = self._suggest_adaptations(problematic)
            result["adaptation_suggestions"] = adaptation_suggestions
        
        return result
    
    def _suggest_adaptations(
        self,
        problematic_patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggère des adaptations basées sur les patterns problématiques"""
        
        suggestions = []
        
        for pattern in problematic_patterns[:3]:  # Top 3
            pattern_id = pattern["pattern"]
            
            # Déterminer adaptation appropriée
            if "too_short" in pattern_id:
                suggestion = {
                    "adjustment": {"detail_level": "detailed"},
                    "reason": f"Pattern '{pattern_id}' détecté {pattern['occurrences']} fois"
                }
            elif "too_long" in pattern_id:
                suggestion = {
                    "adjustment": {"detail_level": "concise"},
                    "reason": f"Pattern '{pattern_id}' détecté {pattern['occurrences']} fois"
                }
            elif "clarity" in pattern_id:
                suggestion = {
                    "adjustment": {"explanation_depth": "thorough"},
                    "reason": f"Problème de clarté détecté"
                }
            else:
                continue
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def apply_adaptation(
        self,
        adjustments: Dict[str, Any],
        reason: str,
        require_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Applique une adaptation avec validation si nécessaire
        
        Returns:
            Résultat de l'adaptation
        """
        
        # Soumettre pour validation
        request_id = self.validation.submit_validation_request(
            validation_type=ValidationType.ADAPTATION,
            title="Adaptation comportementale",
            description=f"Ajuster: {', '.join(adjustments.keys())}",
            proposed_change={
                "scope": "session",
                "behavior_change": "moderate",
                "confidence": 0.7,
                **adjustments
            },
            rationale=reason,
            require_validation=require_validation
        )
        
        # Vérifier si auto-approuvé
        request = self.validation.requests[request_id]
        
        if request.status.value == "approved":
            # Appliquer l'adaptation
            for key, value in adjustments.items():
                if key in self.adaptation.current_behavior:
                    self.adaptation.current_behavior[key] = value
            
            return {
                "status": "applied",
                "request_id": request_id,
                "adjustments": adjustments
            }
        else:
            return {
                "status": "pending_validation",
                "request_id": request_id,
                "adjustments": adjustments
            }
    
    def process_document(
        self,
        document_content: str,
        source_ref: str,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Traite un document pour en extraire les connaissances
        
        Returns:
            Résumé de l'extraction
        """
        
        # Extraire connaissances
        knowledge_ids = self.knowledge.extract_from_document(
            document_content,
            source_ref,
            domain
        )
        
        # Enregistrer en mémoire
        self.memory.add_memory(
            content=f"Document traité: {source_ref}",
            memory_type=MemoryType.DOCUMENT,
            importance=0.7,
            tags=[domain] if domain else [],
            metadata={
                "source_ref": source_ref,
                "knowledge_count": len(knowledge_ids)
            }
        )
        
        return {
            "source_ref": source_ref,
            "knowledge_extracted": len(knowledge_ids),
            "knowledge_ids": knowledge_ids
        }
    
    def search_knowledge(
        self,
        query: str,
        knowledge_type: Optional[KnowledgeType] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans la base de connaissances
        
        Returns:
            Résultats de recherche
        """
        
        results = self.knowledge.search(
            query=query,
            knowledge_type=knowledge_type,
            domain=domain,
            max_results=10
        )
        
        return [
            {
                "id": entry.id,
                "type": entry.knowledge_type.value,
                "content": entry.content,
                "confidence": entry.confidence,
                "source": entry.source.value,
                "tags": entry.tags
            }
            for entry in results
        ]
    
    def get_relevant_context(
        self,
        query: str,
        max_memories: int = 5,
        max_knowledge: int = 3
    ) -> Dict[str, Any]:
        """
        Récupère le contexte pertinent pour une requête
        Combine mémoires et connaissances
        
        Returns:
            Contexte pertinent
        """
        
        # Chercher dans mémoires
        from .memory_manager import MemoryQuery
        
        memory_results = self.memory.search(
            MemoryQuery(query=query)
        )[:max_memories]
        
        # Chercher dans connaissances
        knowledge = self.knowledge.search(
            query=query,
            max_results=max_knowledge
        )
        
        # Récupérer comportement adapté
        behavior = self.adaptation.get_current_behavior()
        
        # Récupérer préférences
        preferences = self.preferences.get_all_preferences(min_confidence=0.7)
        
        return {
            "memories": [
                {
                    "content": result.memory.content,
                    "type": result.memory.type.value,
                    "importance": result.memory.importance,
                    "timestamp": result.memory.timestamp.isoformat(),
                    "relevance": result.relevance_score
                }
                for result in memory_results
            ],
            "knowledge": [
                {
                    "content": entry.content,
                    "type": entry.knowledge_type.value,
                    "confidence": entry.confidence
                }
                for entry in knowledge
            ],
            "current_behavior": behavior,
            "user_preferences": preferences
        }
    
    def get_pending_validations(self) -> List[Dict[str, Any]]:
        """
        Récupère les validations en attente
        
        Returns:
            Liste des requêtes nécessitant validation
        """
        
        pending = self.validation.get_pending_requests(min_risk_level=RiskLevel.MEDIUM)
        
        return [
            {
                "request_id": req.id,
                "type": req.validation_type.value,
                "risk_level": req.risk_level.value,
                "title": req.title,
                "description": req.description,
                "proposed_change": req.proposed_change,
                "rationale": req.rationale,
                "impact": req.impact_analysis,
                "created_at": req.created_at.isoformat()
            }
            for req in pending
        ]
    
    def approve_validation(
        self,
        request_id: str,
        decided_by: str = "user"
    ) -> bool:
        """Approuve une requête de validation"""
        
        success = self.validation.approve_request(request_id, decided_by)
        
        if success:
            # Appliquer l'adaptation si c'est une adaptation
            request = self.validation.requests[request_id]
            if request.validation_type == ValidationType.ADAPTATION:
                proposed = request.proposed_change
                for key, value in proposed.items():
                    if key in self.adaptation.current_behavior:
                        self.adaptation.current_behavior[key] = value
        
        return success
    
    def reject_validation(
        self,
        request_id: str,
        reason: Optional[str] = None,
        decided_by: str = "user"
    ) -> bool:
        """Rejette une requête de validation"""
        
        return self.validation.reject_request(request_id, decided_by, reason)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de tous les composants
        
        Returns:
            Statistiques complètes du système
        """
        
        return {
            "memory": self.memory.get_statistics(),
            "preferences": self.preferences.get_statistics(),
            "feedback": self.feedback.get_statistics(),
            "adaptation": self.adaptation.get_statistics(),
            "knowledge": self.knowledge.get_statistics(),
            "validation": self.validation.get_statistics()
        }
    
    def export_learning_data(self, output_dir: str) -> Dict[str, str]:
        """
        Exporte toutes les données d'apprentissage
        
        Returns:
            Chemins des fichiers exportés
        """
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        files = {}
        
        # Exporter mémoires
        memory_file = output_path / "memories.json"
        self.memory.export_memories(str(memory_file))
        files["memories"] = str(memory_file)
        
        # Exporter préférences
        prefs_file = output_path / "preferences.json"
        self.preferences.export_preferences(str(prefs_file))
        files["preferences"] = str(prefs_file)
        
        # Exporter connaissances
        knowledge_file = output_path / "knowledge.json"
        self.knowledge.export_knowledge(str(knowledge_file))
        files["knowledge"] = str(knowledge_file)
        
        # Exporter audit trail
        audit_file = output_path / "audit_trail.json"
        self.validation.export_audit_trail(str(audit_file))
        files["audit_trail"] = str(audit_file)
        
        return files
    
    def reset_to_default(self) -> None:
        """Réinitialise le système aux paramètres par défaut"""
        
        self.adaptation.reset_to_default()
        print("Système réinitialisé aux paramètres par défaut")


# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser le système complet
    system = AdaptiveLearningSystem(storage_path="data/learning_system")
    
    # Traiter une interaction
    result = system.process_interaction(
        user_prompt="Comment fonctionne Python?",
        assistant_response="Python est un langage interprété...",
        context={
            "task_type": "explanation",
            "user_expertise": "beginner"
        }
    )
    print(f"\nInteraction traitée: {result}")
    
    # Soumettre feedback
    feedback_result = system.submit_feedback(
        interaction_id=result["interaction_id"],
        prompt="Comment fonctionne Python?",
        response="Python est un langage interprété...",
        feedback_type=FeedbackType.POSITIVE,
        comment="Bonne explication"
    )
    print(f"\nFeedback soumis: {feedback_result}")
    
    # Récupérer contexte pertinent
    context = system.get_relevant_context("python langage")
    print(f"\nContexte trouvé: {len(context['memories'])} mémoires, {len(context['knowledge'])} connaissances")
    
    # Statistiques
    stats = system.get_system_statistics()
    print(f"\nStatistiques:")
    print(json.dumps(stats, indent=2, default=str))
