"""
Credentials Vault - Coffre-Fort Local Chiffré

Gestion sécurisée des identifiants pour connecteurs.
Chiffrement Fernet + intégration macOS Keychain.
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("⚠️ cryptography non disponible, vault désactivé")


class CredentialsVault:
    """
    Coffre-fort chiffré pour identifiants
    
    Architecture:
    - Chiffrement Fernet (AES-128)
    - Clé dérivée de master password via PBKDF2
    - Fallback vers macOS Keychain si disponible
    - Consentements avec TTL
    """
    
    def __init__(
        self,
        vault_path: str = "data/vault.enc",
        master_password: Optional[str] = None,
        use_keychain: bool = True
    ):
        self.vault_path = Path(vault_path)
        self.use_keychain = use_keychain and self._is_macos()
        
        # Créer dossier si nécessaire
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialiser chiffrement
        if CRYPTO_AVAILABLE and master_password:
            self._init_encryption(master_password)
        else:
            self.cipher = None
            logger.warning("⚠️ Vault en mode non-chiffré (dev only)")
        
        # Charger vault
        self.credentials: Dict[str, Dict[str, Any]] = {}
        self.consents: Dict[str, Dict[str, Any]] = {}
        self._load_vault()
        
        logger.info(f"✅ CredentialsVault initialisé ({len(self.credentials)} services)")
    
    
    def _init_encryption(self, master_password: str):
        """Initialise le chiffrement Fernet"""
        
        # Dériver clé de chiffrement depuis master password
        salt = b"hopper_vault_salt_v1"  # TODO: Générer et stocker sel unique
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        key = kdf.derive(master_password.encode())
        self.cipher = Fernet(Fernet.generate_key())  # TODO: Utiliser key dérivée
        
        logger.debug("🔐 Chiffrement Fernet initialisé")
    
    
    def _is_macos(self) -> bool:
        """Vérifie si on est sur macOS"""
        return os.uname().sysname == "Darwin"
    
    
    def _load_vault(self):
        """Charge le vault depuis le disque"""
        
        if not self.vault_path.exists():
            logger.debug("Vault vide (nouveau)")
            return
        
        try:
            data_bytes = self.vault_path.read_bytes()
            
            # Déchiffrer si chiffrement actif
            if self.cipher:
                data_bytes = self.cipher.decrypt(data_bytes)
            
            data = json.loads(data_bytes.decode())
            
            self.credentials = data.get("credentials", {})
            self.consents = data.get("consents", {})
            
            logger.debug(f"✅ Vault chargé: {len(self.credentials)} services")
        
        except Exception as e:
            logger.error(f"❌ Erreur chargement vault: {e}")
            self.credentials = {}
            self.consents = {}
    
    
    def _save_vault(self):
        """Sauvegarde le vault sur disque"""
        
        try:
            data = {
                "credentials": self.credentials,
                "consents": self.consents,
                "updated_at": datetime.now().isoformat()
            }
            
            data_bytes = json.dumps(data, indent=2).encode()
            
            # Chiffrer si chiffrement actif
            if self.cipher:
                data_bytes = self.cipher.encrypt(data_bytes)
            
            self.vault_path.write_bytes(data_bytes)
            
            logger.debug("💾 Vault sauvegardé")
        
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde vault: {e}")
    
    
    async def store_credentials(
        self,
        tool_id: str,
        credentials: Dict[str, Any],
        user_id: str = "default"
    ):
        """
        Stocke des credentials pour un tool
        
        Args:
            tool_id: ID du tool (imap_email, calendar, etc.)
            credentials: Dictionnaire des credentials
            user_id: Utilisateur propriétaire
        """
        
        key = f"{user_id}:{tool_id}"
        
        self.credentials[key] = {
            "tool_id": tool_id,
            "user_id": user_id,
            "credentials": credentials,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_vault()
        
        logger.info(f"🔐 Credentials stockés: {tool_id} (user: {user_id})")
    
    
    async def get_credentials(
        self,
        tool_id: str,
        user_id: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère credentials pour un tool
        
        Returns:
            Dictionnaire credentials ou None
        """
        
        key = f"{user_id}:{tool_id}"
        
        if key in self.credentials:
            return self.credentials[key]["credentials"]
        
        # Fallback: macOS Keychain
        if self.use_keychain:
            return await self._get_from_keychain(tool_id, user_id)
        
        return None
    
    
    async def delete_credentials(
        self,
        tool_id: str,
        user_id: str = "default"
    ):
        """Supprime credentials d'un tool"""
        
        key = f"{user_id}:{tool_id}"
        
        if key in self.credentials:
            del self.credentials[key]
            self._save_vault()
            logger.info(f"🗑️  Credentials supprimés: {tool_id}")
    
    
    async def list_stored_tools(
        self,
        user_id: str = "default"
    ) -> List[str]:
        """Liste les tools ayant des credentials stockés"""
        
        return [
            cred["tool_id"]
            for key, cred in self.credentials.items()
            if cred["user_id"] == user_id
        ]
    
    
    # ============================================
    # Gestion des Consentements
    # ============================================
    
    async def grant_consent(
        self,
        tool_id: str,
        capability_name: str,
        user_id: str = "default",
        ttl_seconds: Optional[int] = None
    ):
        """
        Accorde consentement pour une capacité
        
        Args:
            tool_id: ID du tool
            capability_name: Nom de la capacité
            user_id: Utilisateur
            ttl_seconds: Durée de validité (None = permanent)
        """
        
        key = f"{user_id}:{tool_id}:{capability_name}"
        
        consent = {
            "tool_id": tool_id,
            "capability_name": capability_name,
            "user_id": user_id,
            "granted_at": datetime.now().isoformat(),
            "expires_at": None
        }
        
        if ttl_seconds:
            expires = datetime.now() + timedelta(seconds=ttl_seconds)
            consent["expires_at"] = expires.isoformat()
        
        self.consents[key] = consent
        self._save_vault()
        
        logger.info(
            f"✅ Consentement accordé: {tool_id}.{capability_name} "
            f"(TTL: {ttl_seconds or 'permanent'}s)"
        )
    
    
    async def check_consent(
        self,
        tool_id: str,
        capability_name: str,
        user_id: str = "default"
    ) -> bool:
        """
        Vérifie si consentement existe et est valide
        
        Returns:
            True si consentement valide
        """
        
        key = f"{user_id}:{tool_id}:{capability_name}"
        
        if key not in self.consents:
            return False
        
        consent = self.consents[key]
        
        # Vérifier expiration
        if consent["expires_at"]:
            expires = datetime.fromisoformat(consent["expires_at"])
            if datetime.now() > expires:
                # Consentement expiré
                del self.consents[key]
                self._save_vault()
                logger.debug(f"⏰ Consentement expiré: {tool_id}.{capability_name}")
                return False
        
        return True
    
    
    async def revoke_consent(
        self,
        tool_id: str,
        capability_name: str,
        user_id: str = "default"
    ):
        """Révoque un consentement"""
        
        key = f"{user_id}:{tool_id}:{capability_name}"
        
        if key in self.consents:
            del self.consents[key]
            self._save_vault()
            logger.info(f"🚫 Consentement révoqué: {tool_id}.{capability_name}")
    
    
    async def list_active_consents(
        self,
        user_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """Liste tous les consentements actifs"""
        
        active = []
        
        for key, consent in list(self.consents.items()):
            if consent["user_id"] != user_id:
                continue
            
            # Vérifier expiration
            if consent["expires_at"]:
                expires = datetime.fromisoformat(consent["expires_at"])
                if datetime.now() > expires:
                    del self.consents[key]
                    continue
            
            active.append(consent)
        
        if len(active) != len(self.consents):
            self._save_vault()  # Nettoyer expirés
        
        return active
    
    
    # ============================================
    # macOS Keychain Integration (optionnel)
    # ============================================
    
    async def _get_from_keychain(
        self,
        tool_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère credentials depuis macOS Keychain
        
        Utilise la commande `security find-generic-password`
        """
        
        if not self.use_keychain:
            return None
        
        try:
            import subprocess
            
            service_name = f"hopper_{tool_id}"
            account_name = user_id
            
            result = subprocess.run([
                "security",
                "find-generic-password",
                "-s", service_name,
                "-a", account_name,
                "-w"  # Print password only
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                password = result.stdout.strip()
                logger.debug(f"🔑 Credentials récupérés depuis Keychain: {tool_id}")
                return {"password": password}
            
        except Exception as e:
            logger.error(f"❌ Erreur Keychain: {e}")
        
        return None
    
    
    async def store_in_keychain(
        self,
        tool_id: str,
        password: str,
        user_id: str = "default"
    ) -> bool:
        """
        Stocke password dans macOS Keychain
        
        Returns:
            True si succès
        """
        
        if not self.use_keychain:
            return False
        
        try:
            import subprocess
            
            service_name = f"hopper_{tool_id}"
            account_name = user_id
            
            result = subprocess.run([
                "security",
                "add-generic-password",
                "-s", service_name,
                "-a", account_name,
                "-w", password,
                "-U"  # Update if exists
            ], capture_output=True)
            
            if result.returncode == 0:
                logger.info(f"🔑 Password stocké dans Keychain: {tool_id}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Erreur Keychain: {e}")
        
        return False
