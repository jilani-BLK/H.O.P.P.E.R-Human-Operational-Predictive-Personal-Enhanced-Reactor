"""
Mode Asynchrone pour ActionNarrator
Support des callbacks web pour les approbations en contexte FastAPI

Utilisation:
    narrator = AsyncActionNarrator(callback_url="http://localhost:8000/approval")
    approved = await narrator.narrate_async(action)
"""

import asyncio
import aiohttp
from typing import Optional, Callable, Awaitable
from loguru import logger
from dataclasses import asdict

from .action_narrator import (
    ActionNarrator,
    Action,
    ActionType,
    Urgency
)


class AsyncActionNarrator(ActionNarrator):
    """
    Version asynchrone d'ActionNarrator avec support callbacks web
    """
    
    def __init__(
        self,
        callback_url: Optional[str] = None,
        approval_callback: Optional[Callable[[Action], Awaitable[bool]]] = None,
        auto_approve_low_urgency: bool = True
    ):
        """
        Args:
            callback_url: URL pour les callbacks d'approbation (POST)
            approval_callback: Fonction async personnalisée pour approbation
            auto_approve_low_urgency: Auto-approuver les actions INFO/LOW
        """
        super().__init__()
        self.callback_url = callback_url
        self.approval_callback = approval_callback
        self.auto_approve_low_urgency = auto_approve_low_urgency
    
    async def narrate_async(self, action: Action) -> bool:
        """
        Version asynchrone de narrate()
        
        Args:
            action: Action à narrer
            
        Returns:
            True si approuvée, False sinon
        """
        # Construire le récit
        narrative = self._build_narrative(action)
        
        # Afficher le récit
        print(f"\n{narrative}")
        
        # Vérifier si approbation nécessaire
        if not action.requires_approval:
            return True
        
        # Auto-approuver les actions de faible urgence si configuré
        if self.auto_approve_low_urgency and action.urgency in [Urgency.INFO, Urgency.LOW]:
            logger.info("✅ Action auto-approuvée (faible urgence)")
            return True
        
        # Demander approbation asynchrone
        return await self._request_approval_async(action)
    
    async def _request_approval_async(self, action: Action) -> bool:
        """
        Demande approbation via callback ou URL
        
        Args:
            action: Action nécessitant approbation
            
        Returns:
            True si approuvée
        """
        # Priorité 1: Callback personnalisé
        if self.approval_callback:
            try:
                return await self.approval_callback(action)
            except Exception as e:
                logger.error(f"❌ Erreur callback approbation: {e}")
                return False
        
        # Priorité 2: Callback HTTP
        if self.callback_url:
            return await self._request_approval_http(action)
        
        # Fallback: Approbation synchrone (bloquante)
        logger.warning("⚠️ Pas de callback async configuré, utilisation mode synchrone")
        return self._request_approval(action, display=lambda msg: print(msg, end=""))
    
    async def _request_approval_http(self, action: Action) -> bool:
        """
        Demande approbation via HTTP POST
        
        Args:
            action: Action à approuver
            
        Returns:
            True si approuvée
        """
        if not self.callback_url:
            logger.error("❌ Callback URL non définie")
            return False
        
        payload = {
            "action_type": action.action_type.value,
            "description": action.description,
            "reason": action.reason,
            "urgency": action.urgency.value,
            "risks": action.risks,
            "benefits": action.benefits,
            "details": action.details,
            "estimated_duration": action.estimated_duration,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.callback_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        approved = result.get("approved", False)
                        
                        if approved:
                            logger.success("✅ Action approuvée via callback HTTP")
                        else:
                            logger.warning("⛔ Action refusée via callback HTTP")
                        
                        return approved
                    else:
                        logger.error(f"❌ Erreur HTTP callback: {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("❌ Timeout callback HTTP")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur callback HTTP: {e}")
            return False


# Helpers asynchrones

async def narrate_file_scan_async(
    narrator: AsyncActionNarrator,
    file_path: str,
    scan_type: str = "sécurité"
) -> bool:
    """Helper async: Narre un scan de fichier"""
    action = Action(
        action_type=ActionType.SECURITY_SCAN,
        description=f"Je vais vérifier le fichier '{file_path}'",
        reason=f"pour m'assurer qu'il ne contient aucune menace",
        urgency=Urgency.LOW,
        requires_approval=False,
        estimated_duration="quelques secondes",
        details={"file_path": file_path, "scan_type": scan_type},
    )
    return await narrator.narrate_async(action)


async def narrate_file_modification_async(
    narrator: AsyncActionNarrator,
    file_path: str,
    operation: str,
    backup_created: bool = True
) -> bool:
    """Helper async: Narre une modification de fichier"""
    action = Action(
        action_type=ActionType.FILE_OPERATION,
        description=f"Je vais {operation} le fichier '{file_path}'",
        reason="appliquer les modifications demandées",
        urgency=Urgency.MEDIUM,
        requires_approval=True,
        estimated_duration="quelques secondes",
        benefits=[
            "Modifications appliquées",
            "Sauvegarde créée" if backup_created else "Aucune sauvegarde"
        ],
        risks=["Modification irréversible"] if not backup_created else [],
        details={"file_path": file_path, "operation": operation, "backup": backup_created},
    )
    return await narrator.narrate_async(action)


async def narrate_system_command_async(
    narrator: AsyncActionNarrator,
    command: str,
    purpose: str
) -> bool:
    """Helper async: Narre une commande système"""
    action = Action(
        action_type=ActionType.SYSTEM_COMMAND,
        description=f"Je vais exécuter : {command}",
        reason=purpose,
        urgency=Urgency.HIGH,
        requires_approval=True,
        risks=["Modification du système", "Action potentiellement irréversible"],
        details={"command": command},
    )
    return await narrator.narrate_async(action)


async def narrate_data_analysis_async(
    narrator: AsyncActionNarrator,
    data_source: str,
    analysis_type: str
) -> bool:
    """Helper async: Narre une analyse de données"""
    action = Action(
        action_type=ActionType.DATA_ANALYSIS,
        description=f"Je vais analyser {data_source}",
        reason=f"effectuer une analyse {analysis_type}",
        urgency=Urgency.LOW,
        requires_approval=False,
        estimated_duration="quelques instants",
        details={"source": data_source, "type": analysis_type},
    )
    return await narrator.narrate_async(action)


# Exemple d'utilisation
if __name__ == "__main__":
    async def demo_async_narrator():
        """Démonstration du mode asynchrone"""
        print("\n" + "="*80)
        print("DÉMONSTRATION: ActionNarrator Mode Asynchrone")
        print("="*80 + "\n")
        
        # 1. Avec callback personnalisé
        print("1. Callback Personnalisé\n")
        
        async def custom_approval(action: Action) -> bool:
            print(f"\n📋 Demande d'approbation reçue:")
            print(f"   Action: {action.description}")
            print(f"   Urgence: {action.urgency.value}")
            
            # Simuler une décision (dans un vrai système: requête DB, UI, etc.)
            await asyncio.sleep(0.5)
            
            # Auto-approuver pour la démo
            print("   ✅ Approuvé automatiquement (démo)")
            return True
        
        narrator = AsyncActionNarrator(approval_callback=custom_approval)
        
        action = Action(
            action_type=ActionType.SYSTEM_COMMAND,
            description="Exécuter une commande système",
            reason="tester le mode asynchrone",
            urgency=Urgency.HIGH,
            requires_approval=True,
        )
        
        approved = await narrator.narrate_async(action)
        print(f"\nRésultat: {'✅ Approuvé' if approved else '⛔ Refusé'}")
        
        # 2. Auto-approbation faible urgence
        print("\n\n2. Auto-Approbation (Faible Urgence)\n")
        
        narrator2 = AsyncActionNarrator(auto_approve_low_urgency=True)
        
        await narrate_file_scan_async(narrator2, "test.txt", "sécurité")
        
        print("\n\n3. Scan Complet avec Narration\n")
        
        # Simuler un workflow complet
        files = ["document.pdf", "script.py", "data.csv"]
        
        for file in files:
            await narrate_file_scan_async(narrator2, file)
            await asyncio.sleep(0.2)  # Simuler le scan
            print(f"   ✅ Scan de '{file}' terminé\n")
        
        print("\n✅ Démonstration terminée!")
    
    # Exécuter la démo
    asyncio.run(demo_async_narrator())
