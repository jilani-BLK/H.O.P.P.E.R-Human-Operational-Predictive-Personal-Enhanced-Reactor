"""
Dispatcher d'intentions
Analyse les commandes et les route vers les services appropriés
Phase 2: Intégration LLM complet avec RAG et PromptBuilder
"""

import re
from typing import Dict, Any, Optional
from loguru import logger

from core.service_registry import ServiceRegistry
from core.context_manager import ContextManager
from core.prompt_builder import PromptBuilder

# Import ActionNarrator pour communication transparente
try:
    from src.communication import ActionNarrator, narrate_system_command, ActionType, Action, Urgency
    logger.info("✅ ActionNarrator importé")
except ImportError:
    logger.warning("⚠️ ActionNarrator non disponible")
    ActionNarrator = None
    narrate_system_command = None

try:
    from ..config import settings
except ImportError:
    from config import settings  # type: ignore[import-not-found]


class IntentDispatcher:
    """Route les commandes vers les services appropriés"""
    
    def __init__(self, service_registry: ServiceRegistry, context_manager: ContextManager):
        self.service_registry = service_registry
        self.context_manager = context_manager
        
        # Initialiser ActionNarrator pour communication transparente
        if ActionNarrator:
            self.narrator = ActionNarrator(verbose=True, auto_approve_low_risk=True)
            logger.info("✅ ActionNarrator initialisé - Communication transparente activée")
        else:
            self.narrator = None
            logger.warning("⚠️ ActionNarrator non disponible")
        
        # Initialiser PromptBuilder pour Phase 2
        try:
            self.prompt_builder = PromptBuilder()
            logger.info("✅ PromptBuilder initialisé")
        except Exception as e:
            logger.warning(f"⚠️ PromptBuilder non disponible: {e}")
            self.prompt_builder = None
        
        # Initialiser System Tools (Phase 5)
        try:
            from tools.system_integration import system_tools
            from tools.filesystem_integration import fs_tools
            self.system_tools = system_tools
            self.fs_tools = fs_tools
            logger.info("✅ System Tools intégrés (LocalSystem + FileSystem)")
        except Exception as e:
            logger.warning(f"⚠️ System Tools non disponibles: {e}")
            self.system_tools = None
            self.fs_tools = None
        
        # Patterns d'intentions simples (Phase 1)
        self.intent_patterns = {
            "system_action": [
                r"\b(ouvre|ouvrir|lance|lancer|démarre|démarrer)\b.*\b(fichier|application|app|programme)\b",
                r"\b(crée|créer|nouveau)\b.*\bfichier\b",
                r"\b(supprime|supprimer|efface|effacer)\b.*\bfichier\b",
                r"\b(liste|lister|affiche|afficher)\b.*\b(fichiers|répertoire|dossier)\b"
            ],
            "learn": [
                r"\b(apprends?|retiens?|mémorise|note)\b",
                r"\b(learn|remember)\b"
            ],
            "question": [
                r"^(quel|quelle|quels|quelles|qui|quoi|où|comment|pourquoi|combien)",
                r"\?$"
            ],
            "email": [
                r"\b(email|mail|message|courrier)\b",
                r"\b(inbox|boîte de réception)\b"
            ],
            "control": [
                r"\b(éteins|allume|active|désactive)\b.*\b(lumière|lampe)\b",
                r"\b(volume|son)\b"
            ]
        }
    
    async def dispatch(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route une commande vers le bon service
        
        Args:
            text: Texte de la commande
            user_id: Identifiant utilisateur
            context: Contexte actuel
            
        Returns:
            Résultat de l'exécution
        """
        logger.info(f"🔍 Analyse de l'intention pour: '{text}'")
        
        # Détection de l'intention
        intent = self._detect_intent(text)
        logger.info(f"💡 Intention détectée: {intent}")
        
        # Routage selon l'intention
        if intent == "system_action":
            return await self._handle_system_action(text, user_id, context)
        
        elif intent == "learn":
            return await self._handle_learn(text, user_id, context)
        
        elif intent == "question":
            return await self._handle_question(text, user_id, context)
        
        elif intent == "email":
            return await self._handle_email(text, user_id, context)
        
        elif intent == "control":
            return await self._handle_control(text, user_id, context)
        
        else:
            # Par défaut, envoyer au LLM pour traitement général
            return await self._handle_general(text, user_id, context)
    
    def _detect_intent(self, text: str) -> str:
        """
        Détecte l'intention d'une commande
        
        Args:
            text: Texte à analyser
            
        Returns:
            Type d'intention détectée
        """
        text_lower = text.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent
        
        return "general"
    
    async def _generate_action_narration(self, text: str, action_type: str) -> str:
        """
        Génère une narration de ce que HOPPER est en train de faire
        
        Args:
            text: Commande utilisateur
            action_type: Type d'action (system_action, learn, control, etc.)
            
        Returns:
            Phrase décrivant l'action en cours
        """
        logger.debug(f"🎬 Génération narration pour: {text} (type: {action_type})")
        
        # Templates de narration selon le type d'action
        narration_templates = {
            "system_action": "Je m'occupe de {action}...",
            "learn": "Je mémorise cette information...",
            "control": "J'effectue le contrôle demandé...",
            "email": "Je consulte vos emails...",
            "search": "Je recherche l'information..."
        }
        
        # Utiliser le LLM pour générer une narration naturelle
        try:
            logger.debug("🤖 Appel LLM pour narration...")
            prompt = f"""Tu es HOPPER, un assistant. L'utilisateur te demande: "{text}"

Réponds en UNE SEULE phrase courte (maximum 15 mots) pour dire ce que tu es EN TRAIN DE FAIRE.
Commence par "Je" et utilise le présent continu.

Exemples:
- Pour "ouvre mon fichier test.txt" → "J'ouvre le fichier test.txt pour vous"
- Pour "crée un dossier projets" → "Je crée le dossier projets"
- Pour "liste les fichiers" → "Je liste les fichiers du répertoire"
- Pour "apprends que Paris est la capitale" → "Je mémorise cette information"
- Pour "allume la lumière du salon" → "J'allume la lumière du salon"

Ta réponse (une seule phrase, maximum 15 mots):"""

            result = await self.service_registry.call_service(
                "llm",
                "/generate",
                method="POST",
                data={
                    "prompt": prompt,
                    "max_tokens": 50,
                    "temperature": 0.3  # Basse température pour réponses cohérentes
                }
            )
            
            narration = result.get("text", "").strip()
            logger.debug(f"✨ Narration générée: {narration}")
            if narration and len(narration) < 200:  # Vérification sécurité
                return narration
                
        except Exception as e:
            logger.debug(f"⚠️ Fallback template (LLM indispo): {e}")
        
        # Fallback : template simple
        template = narration_templates.get(action_type, "Je traite votre demande...")
        fallback = template.format(action=text.lower()[:50])
        logger.debug(f"📝 Template utilisé: {fallback}")
        return fallback
    
    async def _handle_system_action(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gère les actions système avec narration transparente"""
        logger.info("⚙️ Traitement d'une action système")
        
        # Narration transparente avec ActionNarrator
        if self.narrator and narrate_system_command:
            # Créer action détaillée
            action = Action(
                action_type=ActionType.SYSTEM_COMMAND,
                description=f"Exécuter : {text}",
                reason="traiter votre demande",
                estimated_duration="quelques secondes",
                urgency=Urgency.MEDIUM,
                requires_approval=False,  # Peut être True selon la commande
                benefits=["Exécution de votre commande"],
            )
            
            # Narrer l'action
            approved = self.narrator.narrate(action)
            
            if not approved:
                return {
                    "message": "Action annulée par l'utilisateur",
                    "data": None,
                    "actions": ["cancelled"]
                }
        else:
            # Fallback : Génération simple
            narration = await self._generate_action_narration(text, "system_action")
        
        try:
            # Appel au module d'exécution système
            result = await self.service_registry.call_service(
                "system_executor",
                "/exec",
                method="POST",
                data={"command": text, "args": [], "timeout": 30}
            )
            
            # Message de succès
            success_msg = f"✅ Action terminée avec succès"
            
            return {
                "message": success_msg,
                "data": result,
                "actions": ["system_execution"],
                "narration": action.description if self.narrator else narration
            }
            
        except Exception as e:
            logger.error(f"Erreur d'exécution système: {str(e)}")
            return {
                "message": f"❌ Erreur lors de l'exécution: {str(e)}",
                "data": None,
                "actions": []
            }
    
    async def _handle_question(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gère les questions nécessitant le LLM avec RAG (Retrieval-Augmented Generation)
        Phase 2: Utilise PromptBuilder et enrichit avec Knowledge Base
        Phase 5: Détecte et exécute automatiquement les outils système
        """
        logger.info("🤖 Traitement d'une question via LLM + RAG + System Tools")
        
        try:
            # 1. Enrichir avec Knowledge Base (RAG)
            knowledge_context = await self._enrich_with_knowledge(text)
            
            # 2. Récupérer historique conversationnel
            history = self.context_manager.get_history_for_prompt(user_id, max_exchanges=5)
            
            # 3. Construire prompt avec PromptBuilder
            if self.prompt_builder:
                prompt = self.prompt_builder.build_prompt(
                    user_input=text,
                    history=history,
                    knowledge_context=knowledge_context
                )
                generation_params = self.prompt_builder.get_generation_params()
            else:
                # Fallback si PromptBuilder indisponible
                logger.warning("⚠️ PromptBuilder indisponible, utilisation prompt simple")
                history_text = self.context_manager.format_history_for_llm(user_id)
                prompt = f"{history_text}\n\nUser: {text}\nAssistant:"
                generation_params: Dict[str, Any] = {"max_tokens": 500, "temperature": 0.7}
            
            # 4. Appel au LLM
            result = await self.service_registry.call_service(
                "llm",
                "/generate",
                method="POST",
                data={
                    "prompt": prompt,
                    **generation_params
                },
                timeout=settings.LLM_TIMEOUT
            )
            
            # 5. Extraire réponse
            response_text = result.get("text", result.get("response", ""))
            
            # 6. PHASE 5: Détecter et exécuter outils système
            tool_results = []
            actions_executed = ["llm_generation"]
            
            if self.system_tools:
                try:
                    # Détecter dans la réponse LLM et la question utilisateur
                    tool_result = await self.system_tools.detect_and_execute(response_text, text)
                    if tool_result:
                        logger.success(f"🔧 Outil exécuté: {tool_result['action']}")
                        tool_results.append(tool_result)
                        actions_executed.append(f"tool_{tool_result['action']}")
                        
                        # Enrichir la réponse avec le résultat
                        tool_context = self.system_tools.format_result_for_llm(tool_result)
                        response_text += tool_context
                except Exception as e:
                    logger.warning(f"⚠️ Erreur exécution outil système: {e}")
            
            # 7. Sauvegarder dans historique
            self.context_manager.add_to_history(user_id, text, response_text)
            
            logger.success(f"✅ Réponse LLM générée: {result.get('tokens_generated', 0)} tokens, {len(tool_results)} outils exécutés")
            
            return {
                "message": response_text,
                "data": result,
                "tools_executed": tool_results,
                "actions": actions_executed + (["rag_enrichment"] if knowledge_context else [])
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur LLM: {str(e)}")
            return {
                "message": f"Désolé, je n'ai pas pu traiter votre question: {str(e)}",
                "data": None,
                "actions": []
            }
    
    async def _enrich_with_knowledge(self, query: str) -> Optional[str]:
        """
        Enrichit le prompt avec la Knowledge Base (RAG)
        
        Args:
            query: Requête utilisateur
            
        Returns:
            Contexte pertinent ou None
        """
        try:
            # Rechercher dans KB
            result = await self.service_registry.call_service(
                "llm",
                "/search",
                method="POST",
                data={"query": query, "k": 3, "threshold": 0.5},
                timeout=5
            )
            
            if result and result.get('results'):
                # Construire contexte à partir des résultats
                knowledge_items = [
                    f"- {item['text']}"
                    for item in result['results']
                    if item.get('score', 0) > 0.5
                ]
                
                if knowledge_items:
                    knowledge_text = "\n".join(knowledge_items)
                    logger.info(f"🧠 Knowledge enrichment: {len(knowledge_items)} éléments trouvés")
                    return knowledge_text
            
        except Exception as e:
            logger.debug(f"Pas de knowledge enrichment: {e}")
        
        return None
    
    async def _handle_learn(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gère l'apprentissage de nouveaux faits dans la Knowledge Base
        
        Args:
            text: Texte à apprendre
            user_id: ID utilisateur
            context: Contexte
            
        Returns:
            Résultat de l'apprentissage
        """
        logger.info(f"📚 Apprentissage d'un nouveau fait: {text}")
        
        try:
            # Générer narration de l'action
            narration = await self._generate_action_narration(text, "learn")
            
            # Extraire le fait à apprendre (enlever "apprends que", etc.)
            fact = re.sub(r'^(apprends?|retiens?|mémorise|note)\s+(que\s+)?', '', text, flags=re.IGNORECASE).strip()
            
            # Appeler endpoint /learn du service LLM
            result = await self.service_registry.call_service(
                "llm",
                "/learn",
                method="POST",
                data={"text": fact},
                timeout=10
            )
            
            response_message = f"{narration} — {result.get('total_knowledge', 0)} faits en mémoire."
            
            logger.success(f"✅ Fait appris: {fact}")
            
            return {
                "message": response_message,
                "data": result,
                "actions": ["knowledge_learn"]
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur apprentissage: {e}")
            return {
                "message": f"Je n'ai pas pu mémoriser cette information: {str(e)}",
                "data": None,
                "actions": []
            }
    
    async def _handle_email(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gère les demandes liées aux emails"""
        logger.info("📧 Traitement d'une demande email")
        
        try:
            # Appel au connecteur email
            result = await self.service_registry.call_service(
                "connectors",
                "/email/query",
                method="POST",
                data={"query": text, "user_id": user_id}
            )
            
            return {
                "message": result.get("message", ""),
                "data": result,
                "actions": ["email_query"]
            }
            
        except Exception as e:
            logger.error(f"Erreur email: {str(e)}")
            return {
                "message": f"Erreur d'accès aux emails: {str(e)}",
                "data": None,
                "actions": []
            }
    
    async def _handle_control(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gère les commandes de contrôle (IoT, etc.)"""
        logger.info("🏠 Traitement d'une commande de contrôle")
        
        try:
            # Appel au connecteur IoT
            result = await self.service_registry.call_service(
                "connectors",
                "/iot/control",
                method="POST",
                data={"command": text, "user_id": user_id}
            )
            
            return {
                "message": result.get("message", ""),
                "data": result,
                "actions": ["iot_control"]
            }
            
        except Exception as e:
            logger.error(f"Erreur de contrôle: {str(e)}")
            return {
                "message": f"Erreur de contrôle: {str(e)}",
                "data": None,
                "actions": []
            }
    
    async def _handle_general(
        self,
        text: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gère les requêtes générales via le LLM"""
        logger.info("💬 Traitement général via LLM")
        
        # Similaire à _handle_question mais avec moins de contraintes
        return await self._handle_question(text, user_id, context)
