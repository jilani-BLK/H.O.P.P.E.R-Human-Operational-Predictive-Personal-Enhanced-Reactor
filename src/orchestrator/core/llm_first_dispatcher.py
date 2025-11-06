"""
LLM-First Dispatcher - Nouvelle architecture
Délègue toute la planification au LLM via LlmAgent
Remplace les règles regex par intelligence générative
"""

from typing import Dict, Any, Optional
from loguru import logger

from core.service_registry import ServiceRegistry
from core.context_manager import ContextManager
from core.llm_agent import LlmAgent
from core.prompt_assembler import PromptAssembler
from core.models import (
    InteractionEnvelope,
    InteractionType,
    create_interaction_envelope
)

try:
    from ..config import settings
except ImportError:
    from config import settings  # type: ignore[import-not-found]


class LlmFirstDispatcher:
    """
    Dispatcher LLM-first
    Délègue toute décision au LLM - pas de règles codées
    """
    
    def __init__(
        self,
        service_registry: ServiceRegistry,
        context_manager: ContextManager,
        llm_agent: LlmAgent,
        use_legacy_fallback: bool = True
    ):
        self.service_registry = service_registry
        self.context_manager = context_manager
        self.llm_agent = llm_agent
        self.use_legacy_fallback = use_legacy_fallback
        
        # Stats
        self.stats = {
            "total_requests": 0,
            "llm_success": 0,
            "llm_failures": 0,
            "fallback_used": 0
        }
        
        logger.info("✅ LlmFirstDispatcher initialisé - Planification LLM activée")
    
    async def dispatch(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any],
        session_id: str = ""
    ) -> Dict[str, Any]:
        """
        Dispatche une commande via LLM (architecture LLM-first)
        
        Flow:
        1. Normalise input → InteractionEnvelope
        2. Appelle LlmAgent.process() → SystemPlan
        3. LlmAgent exécute tools → résultats
        4. Retourne réponse naturelle générée
        
        Args:
            text: Texte de la commande
            user_id: ID utilisateur
            context: Contexte actuel
            session_id: ID session
            
        Returns:
            Résultat avec message naturel LLM
        """
        
        self.stats["total_requests"] += 1
        
        logger.info(f"🧠 LLM-First Dispatch: '{text[:50]}...' (user={user_id})")
        
        try:
            # 1. Normaliser l'input
            envelope = create_interaction_envelope(
                type=InteractionType.TEXT,
                payload={"text": text},
                user_id=user_id,
                session_id=session_id,
                metadata=context
            )
            
            logger.debug(f"📦 Envelope créée: type={envelope.type}")
            
            # 2. Pipeline ReAct complet via LlmAgent
            result = await self.llm_agent.process(
                user_input=text,
                user_id=user_id,
                session_id=session_id
            )
            
            if result.get("success"):
                self.stats["llm_success"] += 1
                logger.success(f"✅ LLM pipeline success")
            else:
                self.stats["llm_failures"] += 1
                logger.warning(f"⚠️ LLM pipeline partial failure")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM-First Dispatch error: {e}")
            self.stats["llm_failures"] += 1
            
            # Fallback si LLM échoue
            if self.use_legacy_fallback:
                return await self._legacy_fallback(text, user_id, context)
            else:
                return {
                    "success": False,
                    "message": "Je rencontre une difficulté technique. Pouvez-vous reformuler ?",
                    "data": {"error": str(e)},
                    "actions_taken": ["error"]
                }
    
    async def _legacy_fallback(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback vers ancien système si LLM échoue
        Heuristiques simples pour urgences
        """
        
        self.stats["fallback_used"] += 1
        logger.warning("🔄 Using legacy fallback (LLM failed)")
        
        text_lower = text.lower()
        
        # Règle 1: Apprendre un fait
        if any(word in text_lower for word in ["apprends", "retiens", "mémorise", "learn"]):
            return await self._fallback_learn(text, user_id)
        
        # Règle 2: Question simple
        if text.strip().endswith("?") or text_lower.startswith(("quel", "qui", "comment", "pourquoi")):
            return await self._fallback_question(text, user_id)
        
        # Règle 3: Action système (détection basique)
        if any(word in text_lower for word in ["crée", "supprime", "liste", "ouvre"]):
            return await self._fallback_system_action(text, user_id)
        
        # Défaut: Message générique
        return {
            "success": False,
            "message": "Je suis temporairement indisponible. Mode dégradé activé.",
            "data": {"mode": "fallback", "original_text": text},
            "actions_taken": ["fallback_generic"]
        }
    
    async def _fallback_learn(self, text: str, user_id: str) -> Dict[str, Any]:
        """Fallback pour apprentissage de fait"""
        
        try:
            # Extraire le fait (après le verbe)
            fact = text
            for verb in ["apprends que", "retiens que", "mémorise que", "learn that"]:
                if verb in text.lower():
                    fact = text.lower().split(verb, 1)[1].strip()
                    break
            
            # Appeler service LLM /learn
            result = await self.service_registry.call_service(
                service_name="llm",
                endpoint="/learn",
                method="POST",
                data={"text": fact}
            )
            
            if result.get("status") == "success":
                return {
                    "success": True,
                    "message": f"J'ai appris: {fact}",
                    "data": result,
                    "actions_taken": ["learn_fallback"]
                }
        
        except Exception as e:
            logger.error(f"Fallback learn error: {e}")
        
        return {
            "success": False,
            "message": "Je n'ai pas pu apprendre cette information.",
            "actions_taken": ["learn_fallback_failed"]
        }
    
    async def _fallback_question(self, text: str, user_id: str) -> Dict[str, Any]:
        """Fallback pour question simple"""
        
        try:
            # Recherche RAG
            rag_results = await self.service_registry.call_service(
                service_name="llm",
                endpoint="/search",
                method="POST",
                data={"query": text, "top_k": 3}
            )
            
            # Génération simple
            result = await self.service_registry.call_service(
                service_name="llm",
                endpoint="/generate",
                method="POST",
                data={
                    "prompt": f"Question: {text}\nRéponds brièvement en français.",
                    "max_tokens": 200
                }
            )
            
            response_text = result.get("text", "Je ne peux pas répondre pour le moment.")
            
            return {
                "success": True,
                "message": response_text,
                "data": {
                    "rag_used": len(rag_results.get("results", [])) > 0,
                    "mode": "fallback_question"
                },
                "actions_taken": ["question_fallback"]
            }
        
        except Exception as e:
            logger.error(f"Fallback question error: {e}")
        
        return {
            "success": False,
            "message": "Je ne peux pas répondre à cette question pour le moment.",
            "actions_taken": ["question_fallback_failed"]
        }
    
    async def _fallback_system_action(self, text: str, user_id: str) -> Dict[str, Any]:
        """Fallback pour action système basique"""
        
        # Détection très simple
        text_lower = text.lower()
        
        if "crée" in text_lower or "créer" in text_lower:
            # Extraire nom de fichier (heuristique)
            words = text.split()
            filename = "hopper_file.txt"  # Défaut
            for i, word in enumerate(words):
                if word.lower() in ["fichier", "file"]:
                    if i + 1 < len(words):
                        filename = words[i + 1]
                        break
            
            try:
                result = await self.service_registry.call_service(
                    service_name="system_executor",
                    endpoint="/execute",
                    method="POST",
                    data={
                        "action": "create_file",
                        "path": f"/tmp/{filename}"
                    }
                )
                
                return {
                    "success": True,
                    "message": f"J'ai créé le fichier {filename} (mode dégradé)",
                    "data": result,
                    "actions_taken": ["system_fallback"]
                }
            
            except Exception as e:
                logger.error(f"Fallback system error: {e}")
        
        return {
            "success": False,
            "message": "Je ne peux pas effectuer cette action pour le moment.",
            "actions_taken": ["system_fallback_failed"]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du dispatcher"""
        
        total = self.stats["total_requests"]
        if total == 0:
            success_rate = 0
        else:
            success_rate = (self.stats["llm_success"] / total) * 100
        
        return {
            **self.stats,
            "success_rate": f"{success_rate:.1f}%",
            "llm_mode": "primary" if not self.use_legacy_fallback else "with_fallback"
        }


# ==================== EXPORT ====================

__all__ = ['LlmFirstDispatcher']
