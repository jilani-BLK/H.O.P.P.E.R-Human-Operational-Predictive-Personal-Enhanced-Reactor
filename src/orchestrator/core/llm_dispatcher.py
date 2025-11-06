"""
HOPPER - LLM Dispatcher
Gère le routing intelligent vers LLM pour conversations naturelles
Phase 2: Intégration prompts et contexte
"""

from typing import Dict, Any, Optional, List
import requests
from loguru import logger


class LLMDispatcher:
    """
    Dispatcher intelligent pour conversations LLM
    Gère templates de prompts et contexte
    """
    
    # Template système pour HOPPER
    SYSTEM_PROMPT = """Tu es HOPPER, un assistant personnel intelligent et local fonctionnant entièrement hors ligne sur macOS.

Tes capacités:
- Répondre aux questions en français
- Exécuter des commandes système (liste fichiers, créer fichiers, ouvrir applications)
- Accéder à une base de connaissances locale
- Maintenir une conversation naturelle

Personnalité:
- Professionnel mais chaleureux
- Concis et précis
- Toujours en français
- Tu te présentes comme "HOPPER" si on te demande

Réponds de manière claire et directe."""

    # Mots-clés pour commandes conversationnelles (priorité haute - toujours LLM)
    CONVERSATION_KEYWORDS = [
        "apprends", "retiens", "retenir", "souviens", "savoir",
        "qui es-tu", "qui es tu", "présente-toi", "présente toi",
        "explique", "raconte", "parle-moi", "parle moi",
        "penses-tu", "penses tu", "qu'est-ce que", "quest-ce que",
        "comment ça marche", "pourquoi", "comment", "dis-moi"
    ]
    
    # Mots-clés indiquant une commande système (pas LLM)
    SYSTEM_KEYWORDS = [
        "liste", "affiche", "montre", "voir",
        "crée", "créer", "nouveau", "touch",
        "ouvre", "ouvrir", "lance", "lancer",
        "lis", "lire", "cat", "contenu",
        "date", "heure", "pwd"
    ]
    
    def __init__(self, llm_service_url: str = "http://llm:5001"):
        """
        Initialise le dispatcher LLM
        
        Args:
            llm_service_url: URL du service LLM
        """
        self.llm_url = llm_service_url
        logger.info(f"🎯 LLMDispatcher initialisé (Phase 2) -> {llm_service_url}")
    
    def is_system_command(self, text: str) -> bool:
        """
        Détecte si le texte est une commande système
        
        Args:
            text: Texte à analyser
            
        Returns:
            True si c'est une commande système
        """
        text_lower = text.lower()
        
        # PRIORITÉ 1: Vérifier d'abord si c'est conversationnel (pas système)
        # Si contient mot-clé conversation, c'est TOUJOURS LLM
        for keyword in self.CONVERSATION_KEYWORDS:
            if keyword in text_lower:
                logger.debug(f"🗣️ Conversation détectée ('{keyword}'): {text[:50]}")
                return False  # Pas système, c'est conversationnel
        
        # PRIORITÉ 2: Vérifier mots-clés système
        for keyword in self.SYSTEM_KEYWORDS:
            if keyword in text_lower:
                logger.debug(f"⚙️ Système détecté ('{keyword}'): {text[:50]}")
                return True
        
        # PRIORITÉ 3: Heuristique - court + "fichier/dossier"
        words = text_lower.split()
        if len(words) < 8 and ("fichier" in text_lower or "dossier" in text_lower):
            logger.debug(f"📁 Système détecté (heuristique fichier): {text[:50]}")
            return True
        
        # Par défaut: conversationnel
        logger.debug(f"💬 Conversationnel par défaut: {text[:50]}")
        return False
    
    def build_prompt(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Construit le prompt complet pour le LLM
        
        Args:
            user_message: Message de l'utilisateur
            conversation_history: Historique des échanges
            context: Contexte additionnel (KB, etc.)
            
        Returns:
            Prompt formaté
        """
        parts = [self.SYSTEM_PROMPT, ""]
        
        # Ajouter contexte de la base de connaissances si disponible
        if context:
            parts.append(f"Contexte pertinent:\n{context}\n")
        
        # Ajouter historique de conversation
        if conversation_history:
            parts.append("Historique de la conversation:")
            for exchange in conversation_history[-5:]:  # Limiter à 5 derniers échanges
                role = exchange.get("role", "user")
                content = exchange.get("content", "")
                if role == "user":
                    parts.append(f"Utilisateur: {content}")
                elif role == "assistant":
                    parts.append(f"HOPPER: {content}")
            parts.append("")
        
        # Ajouter le message actuel
        parts.append(f"Utilisateur: {user_message}")
        parts.append("HOPPER:")
        
        return "\n".join(parts)
    
    def generate(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[str] = None,
        max_tokens: int = 300,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Génère une réponse via le LLM
        
        Args:
            user_message: Message utilisateur
            conversation_history: Historique conversation
            context: Contexte additionnel
            max_tokens: Nombre max de tokens
            temperature: Température de génération
            
        Returns:
            Réponse du LLM
        """
        logger.info(f"📝 Génération réponse LLM: {user_message[:50]}...")
        
        # Construire le prompt
        prompt = self.build_prompt(user_message, conversation_history, context)
        
        logger.debug(f"Prompt: {len(prompt)} chars")
        
        try:
            # Appeler le service LLM
            response = requests.post(
                f"{self.llm_url}/generate",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stop": ["Utilisateur:", "\nUtilisateur:", "User:"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("text", "").strip()
                
                logger.success(f"✅ Réponse générée: {len(answer)} chars")
                
                return {
                    "success": True,
                    "response": answer,
                    "tokens": data.get("tokens_generated", 0),
                    "model": data.get("model", "unknown")
                }
            else:
                logger.error(f"❌ Erreur LLM: {response.status_code}")
                return {
                    "success": False,
                    "error": f"LLM error: {response.status_code}",
                    "response": "Désolé, je rencontre un problème technique."
                }
                
        except Exception as e:
            logger.error(f"❌ Exception LLM: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Désolé, je ne peux pas répondre pour le moment."
            }
    
    def route(self, command: str) -> Dict[str, Any]:
        """
        Route la commande vers le bon dispatcher
        
        Args:
            command: Commande/question utilisateur
            
        Returns:
            Résultat du routing avec type (system/llm)
        """
        if self.is_system_command(command):
            return {
                "type": "system",
                "reason": "detected_system_keywords"
            }
        else:
            return {
                "type": "llm",
                "reason": "conversational_query"
            }


# Test standalone
if __name__ == "__main__":
    dispatcher = LLMDispatcher("http://localhost:5001")
    
    test_cases = [
        "liste les fichiers du dossier /tmp",
        "comment vas-tu aujourd'hui ?",
        "crée un fichier test.txt",
        "qu'est-ce que tu penses de l'intelligence artificielle ?",
        "ouvre l'application Calculator",
        "explique-moi ce qu'est un LLM"
    ]
    
    print("\n🧪 Test du routing:\n")
    for test in test_cases:
        result = dispatcher.route(test)
        print(f"📝 '{test}'")
        print(f"   → Type: {result['type']} ({result['reason']})")
        print()
