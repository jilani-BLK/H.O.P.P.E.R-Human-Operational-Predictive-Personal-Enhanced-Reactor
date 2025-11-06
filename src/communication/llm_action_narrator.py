"""
LLM-Based Action Narrator - Génération dynamique de narrations via LLM

Remplace les templates statiques par des narrations générées dynamiquement
par le LLM, adaptées au contexte et aux préférences utilisateur.
"""

from typing import Dict, Any, Optional
from loguru import logger
import httpx
import json


class LLMActionNarrator:
    """
    Narrateur d'actions basé sur LLM
    
    Génère des messages naturels et contextuels pour expliquer
    les actions de HOPPER à l'utilisateur.
    """
    
    def __init__(self, llm_service_url: str = "http://localhost:5001"):
        """
        Args:
            llm_service_url: URL du service LLM
        """
        self.llm_service_url = llm_service_url
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"✅ LLMActionNarrator initialisé (LLM: {llm_service_url})")
    
    
    async def generate_narration(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        execution_result: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        tone: str = "neutral"
    ) -> str:
        """
        Génère une narration naturelle via LLM
        
        Args:
            action_type: Type d'action (system_action, email, search, etc)
            action_details: Détails de l'action (tool, params, reasoning)
            execution_result: Résultat de l'exécution (succès, erreur, data)
            user_preferences: Préférences utilisateur (verbosité, langue)
            tone: Ton souhaité (neutral, friendly, formal, playful)
            
        Returns:
            Message naturel généré par le LLM
        """
        
        try:
            prompt = self._build_narration_prompt(
                action_type=action_type,
                action_details=action_details,
                execution_result=execution_result,
                user_preferences=user_preferences,
                tone=tone
            )
            
            # Appel LLM
            response = await self.client.post(
                f"{self.llm_service_url}/generate",
                json={
                    "prompt": prompt,
                    "temperature": 0.7,
                    "max_tokens": 150
                }
            )
            
            if response.status_code != 200:
                logger.error(f"LLM error: {response.status_code}")
                return self._fallback_narration(action_type, action_details)
            
            data = response.json()
            narration = data.get("text", "").strip()
            
            logger.debug(f"Narration générée: {narration[:100]}...")
            return narration
            
        except Exception as e:
            logger.error(f"Erreur génération narration: {e}")
            return self._fallback_narration(action_type, action_details)
    
    
    def _build_narration_prompt(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        execution_result: Optional[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]],
        tone: str
    ) -> str:
        """Construit le prompt pour génération de narration"""
        
        # Extraction des détails
        tool = action_details.get("tool_id", "")
        capability = action_details.get("capability", "")
        parameters = action_details.get("parameters", {})
        reasoning = action_details.get("reasoning", "")
        
        # Résultat
        success = execution_result.get("success", True) if execution_result else None
        error = execution_result.get("error") if execution_result else None
        data = execution_result.get("data") if execution_result else None
        
        # Verbosité
        verbosity = user_preferences.get("verbosity", "normal") if user_preferences else "normal"
        
        # Construction prompt
        prompt_parts = [
            f"Tu es HOPPER, un assistant IA. Génère un message {tone} en français pour expliquer une action à l'utilisateur.",
            f"\nTon: {tone}",
            f"Verbosité: {verbosity}",
            f"\nAction:",
            f"  Type: {action_type}",
            f"  Tool: {tool}",
            f"  Capability: {capability}",
        ]
        
        if parameters:
            prompt_parts.append(f"  Paramètres: {json.dumps(parameters, ensure_ascii=False)}")
        
        if reasoning:
            prompt_parts.append(f"  Raisonnement: {reasoning}")
        
        if execution_result:
            if success:
                prompt_parts.append(f"\nRésultat: Succès")
                if data:
                    # Limiter la taille des data
                    data_str = str(data)[:200]
                    prompt_parts.append(f"  Données: {data_str}")
            else:
                prompt_parts.append(f"\nRésultat: Échec")
                if error:
                    prompt_parts.append(f"  Erreur: {error}")
        
        prompt_parts.extend([
            "\nGénère UN SEUL message court (1-2 phrases maximum) expliquant:",
            "- CE QUE tu as fait (ou vas faire)",
            "- LE RÉSULTAT (si applicable)",
            "",
            "Règles:",
            "- Utilise 'Je' (première personne)",
            "- Sois naturel et conversationnel",
            "- Évite le jargon technique",
            f"- Ton: {tone}",
            f"- Longueur: {'très court' if verbosity == 'minimal' else 'court' if verbosity == 'normal' else 'détaillé'}",
            "",
            "Message:"
        ])
        
        return "\n".join(prompt_parts)
    
    
    def _fallback_narration(
        self,
        action_type: str,
        action_details: Dict[str, Any]
    ) -> str:
        """Narration de secours si LLM échoue"""
        
        tool = action_details.get("tool_id", "")
        capability = action_details.get("capability", "")
        
        # Messages génériques par type
        fallback_messages = {
            "system_action": f"J'exécute une action système ({tool}.{capability})",
            "question": "Je recherche la réponse à votre question",
            "email": "Je consulte vos emails",
            "search": "Je recherche les informations demandées",
            "general": "Je traite votre demande"
        }
        
        return fallback_messages.get(action_type, "Je traite votre demande")
    
    
    async def generate_error_message(
        self,
        error: str,
        context: Dict[str, Any],
        tone: str = "empathetic"
    ) -> str:
        """
        Génère un message d'erreur user-friendly
        
        Args:
            error: Message d'erreur technique
            context: Contexte de l'erreur
            tone: Ton (empathetic, neutral, formal)
            
        Returns:
            Message d'erreur compréhensible
        """
        
        prompt = f"""Tu es HOPPER, un assistant IA. Reformule cette erreur technique en message user-friendly.

Erreur technique: {error}
Contexte: {json.dumps(context, ensure_ascii=False)}

Génère un message {tone} qui:
1. Explique CE QUI s'est passé (sans jargon)
2. Pourquoi cela a échoué (si pertinent)
3. Suggère une SOLUTION ou alternative

Ton: {tone}
Longueur: 2-3 phrases maximum

Message:"""
        
        try:
            response = await self.client.post(
                f"{self.llm_service_url}/generate",
                json={
                    "prompt": prompt,
                    "temperature": 0.5,
                    "max_tokens": 150
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("text", "").strip()
            
        except Exception as e:
            logger.error(f"Erreur génération message d'erreur: {e}")
        
        # Fallback
        return f"Une erreur s'est produite. Pouvez-vous réessayer ou reformuler votre demande?"
    
    
    async def generate_confirmation_request(
        self,
        action: Dict[str, Any],
        risks: list,
        benefits: list
    ) -> str:
        """
        Génère une demande de confirmation pour action risquée
        
        Args:
            action: Action à confirmer
            risks: Liste des risques
            benefits: Liste des bénéfices
            
        Returns:
            Message demandant confirmation
        """
        
        prompt = f"""Tu es HOPPER. Génère une demande de permission claire pour cette action.

Action: {json.dumps(action, ensure_ascii=False)}
Risques: {', '.join(risks)}
Bénéfices: {', '.join(benefits)}

Génère un message qui:
1. Explique CE QUE tu veux faire
2. Liste les RISQUES brièvement
3. Demande explicitement la permission

Ton: respectueux et transparent
Longueur: 3-4 phrases

Message:"""
        
        try:
            response = await self.client.post(
                f"{self.llm_service_url}/generate",
                json={
                    "prompt": prompt,
                    "temperature": 0.4,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("text", "").strip()
                return f"{message}\n\nPuis-je continuer? (oui/non)"
            
        except Exception as e:
            logger.error(f"Erreur génération confirmation: {e}")
        
        # Fallback
        return f"Je souhaite effectuer une action sensible. Puis-je continuer? (oui/non)"
    
    
    async def close(self):
        """Ferme le client HTTP"""
        await self.client.aclose()
        logger.debug("LLMActionNarrator client fermé")
