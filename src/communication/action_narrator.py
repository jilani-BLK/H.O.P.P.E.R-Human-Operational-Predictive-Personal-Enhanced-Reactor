"""
Action Narrator - Communication Naturelle et Transparente des Actions HOPPER

Ce module permet à HOPPER d'expliquer ses actions en langage naturel,
sans jargon technique, pour une transparence totale avec l'utilisateur.

Principe: Chaque action importante est narrée AVANT exécution avec une
explication claire du pourquoi et du comment.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import asyncio


class ActionType(Enum):
    """Types d'actions narrables"""
    SECURITY_SCAN = "security_scan"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"
    DATA_ANALYSIS = "data_analysis"
    LEARNING = "learning"
    SEARCH = "search"
    COMMUNICATION = "communication"
    REASONING = "reasoning"
    CODE_EXECUTION = "code_execution"
    PERMISSION_REQUEST = "permission_request"


class Urgency(Enum):
    """Niveau d'urgence de l'action"""
    INFO = "info"  # Information simple
    LOW = "low"  # Peut attendre
    MEDIUM = "medium"  # Important
    HIGH = "high"  # Critique
    BLOCKING = "blocking"  # Nécessite approbation immédiate


@dataclass
class Action:
    """Représente une action à narrer"""
    action_type: ActionType
    description: str  # Description utilisateur-friendly
    reason: str  # Pourquoi cette action ?
    details: Optional[Dict[str, Any]] = None
    urgency: Urgency = Urgency.INFO
    requires_approval: bool = False
    estimated_duration: Optional[str] = None  # "quelques secondes", "~1 minute"
    risks: Optional[List[str]] = None
    benefits: Optional[List[str]] = None


class ActionNarrator:
    """
    Système de narration naturelle des actions HOPPER
    
    Transforme les actions techniques en explications compréhensibles
    par un utilisateur non-technique.
    
    Exemple:
        Au lieu de: "Executing antivirus scan on file.pdf"
        Dit: "Je vais vérifier ce fichier PDF pour m'assurer qu'il ne contient
              rien de dangereux. Cela prendra quelques secondes."
    """
    
    def __init__(self, verbose: bool = True, auto_approve_low_risk: bool = True):
        """
        Args:
            verbose: Si True, affiche toutes les narrations (sinon que MEDIUM+)
            auto_approve_low_risk: Approuve automatiquement actions à faible risque
        """
        self.verbose = verbose
        self.auto_approve_low_risk = auto_approve_low_risk
        self.action_history: List[Action] = []
        
        # Templates de narration par type d'action
        self.templates = {
            ActionType.SECURITY_SCAN: {
                "intro": "Je vais vérifier {target}",
                "reason": "pour m'assurer qu'il ne présente aucun danger",
                "duration": "Cela prendra {duration}",
            },
            ActionType.FILE_OPERATION: {
                "intro": "Je m'apprête à {operation} {target}",
                "reason": "pour {purpose}",
                "safety": "Une sauvegarde sera créée avant toute modification",
            },
            ActionType.SYSTEM_COMMAND: {
                "intro": "Je vais exécuter la commande : {command}",
                "reason": "afin de {purpose}",
                "caution": "Cette action modifiera le système",
            },
            ActionType.DATA_ANALYSIS: {
                "intro": "Je vais analyser {data}",
                "reason": "pour {purpose}",
                "steps": "Voici mon plan : {steps}",
            },
            ActionType.LEARNING: {
                "intro": "J'ai remarqué {observation}",
                "action": "Je vais apprendre {what} pour m'améliorer",
                "benefit": "Cela me permettra de {benefit}",
            },
            ActionType.SEARCH: {
                "intro": "Je vais d'abord chercher {what}",
                "reason": "pour obtenir les informations les plus récentes",
                "then": "Puis j'analyserai comment cela s'applique à votre situation",
            },
            ActionType.REASONING: {
                "intro": "Laissez-moi réfléchir à {problem}",
                "plan": "Mon approche : {steps}",
                "confidence": "Niveau de confiance : {confidence}",
            },
            ActionType.CODE_EXECUTION: {
                "intro": "Je vais exécuter le code : {code}",
                "reason": "pour {purpose}",
                "safety": "Le code sera exécuté dans un environnement isolé",
            },
            ActionType.PERMISSION_REQUEST: {
                "intro": "J'ai besoin de votre permission pour {action}",
                "reason": "Raison : {reason}",
                "approval": "Voulez-vous que je continue ? (oui/non)",
            },
        }
    
    def narrate(
        self,
        action: Action,
        callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Narre une action en langage naturel
        
        Args:
            action: L'action à narrer
            callback: Fonction pour afficher le message (print par défaut)
        
        Returns:
            True si action approuvée (ou pas besoin d'approbation)
            False si action refusée
        """
        # Enregistrer dans historique
        self.action_history.append(action)
        
        # Filtrer par verbosité
        if not self.verbose and action.urgency in [Urgency.INFO, Urgency.LOW]:
            logger.debug(f"Action silencieuse: {action.description}")
            return True
        
        # Construire le message
        message = self._build_narrative(action)
        
        # Afficher
        display = callback or print
        display(message)
        
        # Log technique en parallèle (pour debug)
        logger.info(f"Action narrée: {action.action_type.value} - {action.description}")
        
        # Demander approbation si nécessaire
        if action.requires_approval:
            # Auto-approve si faible risque et option activée
            if self.auto_approve_low_risk and action.urgency == Urgency.LOW:
                display("✓ Action automatiquement approuvée (faible risque)")
                return True
            
            # Sinon, demander confirmation
            return self._request_approval(action, display)
        
        return True
    
    def _build_narrative(self, action: Action) -> str:
        """Construit un message naturel pour l'action"""
        parts = []
        
        # Emoji selon urgence
        emoji_map = {
            Urgency.INFO: "ℹ️",
            Urgency.LOW: "💡",
            Urgency.MEDIUM: "⚡",
            Urgency.HIGH: "⚠️",
            Urgency.BLOCKING: "🛑",
        }
        emoji = emoji_map.get(action.urgency, "ℹ️")
        
        # Introduction
        parts.append(f"{emoji} **{action.description}**")
        
        # Raison
        if action.reason:
            parts.append(f"\n   Pourquoi : {action.reason}")
        
        # Durée estimée
        if action.estimated_duration:
            parts.append(f"\n   Durée : {action.estimated_duration}")
        
        # Risques
        if action.risks:
            parts.append("\n   ⚠️  Risques :")
            for risk in action.risks:
                parts.append(f"      • {risk}")
        
        # Bénéfices
        if action.benefits:
            parts.append("\n   ✓ Bénéfices :")
            for benefit in action.benefits:
                parts.append(f"      • {benefit}")
        
        # Détails supplémentaires
        if action.details:
            if "steps" in action.details:
                parts.append("\n   📋 Étapes :")
                for i, step in enumerate(action.details["steps"], 1):
                    parts.append(f"      {i}. {step}")
        
        return "".join(parts)
    
    def _request_approval(self, action: Action, display: Callable) -> bool:
        """
        Demande l'approbation utilisateur
        
        Note: Dans une interface CLI, on peut utiliser input()
        Dans une API web, cela nécessite un système de callbacks
        """
        display("\n   🤔 Puis-je continuer ? (oui/non)")
        
        # Pour l'instant, auto-approve en mode non-interactif
        # TODO: Implémenter système de permissions async
        logger.warning("Approbation requise mais mode non-interactif")
        return True
    
    def explain_uncertainty(self, topic: str, confidence: float, limitations: List[str]):
        """
        Explique les incertitudes et limitations
        
        Args:
            topic: Le sujet concerné
            confidence: Score de confiance (0-1)
            limitations: Liste des limitations
        """
        confidence_level = (
            "très élevé" if confidence > 0.9 else
            "élevé" if confidence > 0.7 else
            "moyen" if confidence > 0.5 else
            "faible"
        )
        
        message = [
            f"ℹ️  **Transparence sur {topic}**",
            f"\n   Niveau de confiance : {confidence_level} ({confidence:.0%})",
        ]
        
        if limitations:
            message.append("\n   ⚠️  Limitations à prendre en compte :")
            for limitation in limitations:
                message.append(f"      • {limitation}")
        
        message.append("\n   💡 Si vous avez des doutes, n'hésitez pas à demander des précisions.")
        
        print("".join(message))
        logger.info(f"Incertitude expliquée: {topic} (confiance={confidence})")
    
    def share_reasoning(self, question: str, steps: List[str], conclusion: str):
        """
        Partage le processus de raisonnement
        
        Args:
            question: La question/problème
            steps: Les étapes de réflexion
            conclusion: La conclusion
        """
        message = [
            f"🧠 **Mon raisonnement sur : {question}**",
            "\n   📝 Voici comment j'y réfléchis :",
        ]
        
        for i, step in enumerate(steps, 1):
            message.append(f"\n      {i}. {step}")
        
        message.append(f"\n\n   ✓ Conclusion : {conclusion}")
        
        print("".join(message))
        logger.info(f"Raisonnement partagé: {question}")
    
    def get_action_summary(self, last_n: int = 10) -> str:
        """Résumé des dernières actions narrées"""
        recent = self.action_history[-last_n:]
        
        summary = [f"📊 **Résumé des {len(recent)} dernières actions :**\n"]
        
        for i, action in enumerate(recent, 1):
            summary.append(f"{i}. {action.action_type.value}: {action.description}")
        
        return "\n".join(summary)


# ============================================================================
# Helpers pour actions courantes
# ============================================================================

def narrate_file_scan(narrator: ActionNarrator, filepath: str) -> bool:
    """Helper: Narre un scan antivirus de fichier"""
    action = Action(
        action_type=ActionType.SECURITY_SCAN,
        description=f"Je vais vérifier le fichier '{filepath}'",
        reason="pour m'assurer qu'il ne contient aucune menace",
        estimated_duration="quelques secondes",
        urgency=Urgency.MEDIUM,
        benefits=["Protection contre les malwares", "Sécurité de vos données"],
    )
    return narrator.narrate(action)


def narrate_file_modification(
    narrator: ActionNarrator,
    filepath: str,
    operation: str,
    purpose: str,
    requires_approval: bool = True
) -> bool:
    """Helper: Narre une modification de fichier"""
    action = Action(
        action_type=ActionType.FILE_OPERATION,
        description=f"Je m'apprête à {operation} '{filepath}'",
        reason=purpose,
        estimated_duration="quelques secondes",
        urgency=Urgency.MEDIUM,
        requires_approval=requires_approval,
        benefits=["Sauvegarde automatique créée", "Modification réversible"],
        risks=["Modification du contenu du fichier"],
    )
    return narrator.narrate(action)


def narrate_system_command(
    narrator: ActionNarrator,
    command: str,
    purpose: str
) -> bool:
    """Helper: Narre une commande système"""
    action = Action(
        action_type=ActionType.SYSTEM_COMMAND,
        description=f"Je vais exécuter : {command}",
        reason=purpose,
        urgency=Urgency.HIGH,
        requires_approval=True,
        risks=["Modification du système", "Action potentiellement irréversible"],
        details={"command": command},
    )
    return narrator.narrate(action)


def narrate_learning(
    narrator: ActionNarrator,
    observation: str,
    what: str,
    benefit: str
) -> bool:
    """Helper: Narre un apprentissage"""
    action = Action(
        action_type=ActionType.LEARNING,
        description=f"J'ai remarqué : {observation}",
        reason=f"Je vais apprendre {what}",
        urgency=Urgency.LOW,
        benefits=[benefit, "Amélioration continue de mes capacités"],
    )
    return narrator.narrate(action)


def narrate_reasoning(
    narrator: ActionNarrator,
    problem: str,
    steps: List[str],
    confidence: float
) -> bool:
    """Helper: Narre un processus de raisonnement"""
    confidence_text = (
        "Très élevée" if confidence > 0.9 else
        "Élevée" if confidence > 0.7 else
        "Moyenne" if confidence > 0.5 else
        "Faible"
    )
    
    action = Action(
        action_type=ActionType.REASONING,
        description=f"Réflexion sur : {problem}",
        reason="Voici mon approche",
        urgency=Urgency.INFO,
        details={
            "steps": steps,
            "confidence": f"{confidence_text} ({confidence:.0%})"
        },
    )
    return narrator.narrate(action)


# ============================================================================
# Exemple d'utilisation
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("DÉMONSTRATION: Communication Naturelle et Transparente")
    print("=" * 80)
    print()
    
    # Créer narrateur
    narrator = ActionNarrator(verbose=True, auto_approve_low_risk=False)
    
    # 1. Scan antivirus
    print("1️⃣  Scan de sécurité\n")
    narrate_file_scan(narrator, "document_suspect.pdf")
    print("\n" + "-" * 80 + "\n")
    
    # 2. Modification fichier
    print("2️⃣  Modification de fichier\n")
    narrate_file_modification(
        narrator,
        filepath="rapport.docx",
        operation="modifier",
        purpose="corriger les fautes d'orthographe détectées",
    )
    print("\n" + "-" * 80 + "\n")
    
    # 3. Raisonnement
    print("3️⃣  Partage de raisonnement\n")
    narrator.share_reasoning(
        question="Comment optimiser ce code Python ?",
        steps=[
            "Analyser la complexité actuelle (O(n²))",
            "Identifier les boucles imbriquées inutiles",
            "Proposer une structure de données plus efficace (dict au lieu de list)",
            "Vérifier que les tests passent toujours"
        ],
        conclusion="Utiliser un dictionnaire réduira la complexité à O(n)"
    )
    print("\n" + "-" * 80 + "\n")
    
    # 4. Incertitude
    print("4️⃣  Transparence sur les limites\n")
    narrator.explain_uncertainty(
        topic="cette question juridique",
        confidence=0.6,
        limitations=[
            "Mes informations datent de 2023",
            "Le droit peut varier selon votre région",
            "Je recommande de consulter un avocat pour confirmation"
        ]
    )
    print("\n" + "-" * 80 + "\n")
    
    # 5. Apprentissage
    print("5️⃣  Apprentissage continu\n")
    narrate_learning(
        narrator,
        observation="Vous utilisez souvent la commande 'git status'",
        what="vos habitudes Git",
        benefit="Je pourrai vous suggérer des raccourcis et automatisations"
    )
    print("\n" + "-" * 80 + "\n")
    
    # 6. Résumé
    print("6️⃣  Résumé des actions\n")
    print(narrator.get_action_summary())
    print()
