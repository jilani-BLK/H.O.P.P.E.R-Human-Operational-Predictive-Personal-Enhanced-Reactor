"""
HOPPER - System Executor
Service d'exécution sécurisée de commandes système
Utilise une whitelist YAML pour les commandes autorisées

Communication Transparente:
- Explique chaque commande avant exécution
- Communique les résultats de manière naturelle
- Demande approbation pour commandes sensibles
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import subprocess
import os
import yaml
from loguru import logger
from pathlib import Path

# Import du système de communication naturelle
try:
    from src.communication import (
        ActionNarrator,
        Action,
        ActionType,
        Urgency,
        narrate_system_command
    )
    HAS_NARRATOR = True
except ImportError:
    HAS_NARRATOR = False
    logger.warning("⚠️ ActionNarrator non disponible - mode narration désactivé")


# Configuration
WHITELIST_PATH = os.getenv("SYSTEM_EXECUTOR_WHITELIST", "./config/command_whitelist.yaml")
ALLOWED_DIRS = ["/tmp", str(Path.home())]  # Répertoires autorisés


class CommandRequest(BaseModel):
    """Requête d'exécution de commande"""
    command: str
    args: List[str] = []
    timeout: int = 30
    cwd: Optional[str] = None


class CommandResponse(BaseModel):
    """Réponse d'exécution"""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command_executed: str


class SystemExecutor:
    """Exécuteur de commandes système sécurisé"""
    
    def __init__(self, whitelist_path: str, narrator: Optional['ActionNarrator'] = None):
        self.whitelist_path = whitelist_path
        self.whitelist = {}
        self.load_whitelist()
        
        # Initialiser le narrateur pour communication transparente
        if HAS_NARRATOR:
            self.narrator = narrator or ActionNarrator()
            logger.info("✅ Communication naturelle activée pour System Executor")
        else:
            self.narrator = None
    
    def load_whitelist(self):
        """Charge la whitelist depuis le fichier YAML"""
        try:
            if not os.path.exists(self.whitelist_path):
                logger.warning(f"⚠️ Whitelist non trouvée: {self.whitelist_path}")
                logger.info("📝 Création whitelist par défaut...")
                self.create_default_whitelist()
            
            with open(self.whitelist_path, 'r') as f:
                data = yaml.safe_load(f)
                self.whitelist = data.get('commands', {})
            
            logger.success(f"✅ Whitelist chargée: {len(self.whitelist)} commandes autorisées")
            logger.info(f"📋 Commandes: {list(self.whitelist.keys())}")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement whitelist: {e}")
            self.whitelist = {}
    
    def create_default_whitelist(self):
        """Crée une whitelist par défaut"""
        default_whitelist = {
            'commands': {
                'ls': {
                    'description': 'Liste fichiers',
                    'allowed_args': ['-la', '-lh', '-R', '-a', '-l'],
                    'max_depth': 3
                },
                'pwd': {
                    'description': 'Affiche répertoire courant',
                    'allowed_args': []
                },
                'echo': {
                    'description': 'Affiche texte',
                    'allowed_args': []
                },
                'date': {
                    'description': 'Affiche date/heure',
                    'allowed_args': []
                },
                'whoami': {
                    'description': 'Affiche utilisateur',
                    'allowed_args': []
                },
                'find': {
                    'description': 'Recherche fichiers',
                    'allowed_args': ['-name', '-type', '-maxdepth'],
                    'max_depth': 5
                },
                'cat': {
                    'description': 'Affiche contenu fichier',
                    'allowed_args': [],
                    'file_access': 'read'
                },
                'grep': {
                    'description': 'Recherche dans fichiers',
                    'allowed_args': ['-r', '-i', '-n', '-v', '-E'],
                },
                'head': {
                    'description': 'Premières lignes fichier',
                    'allowed_args': ['-n']
                },
                'tail': {
                    'description': 'Dernières lignes fichier',
                    'allowed_args': ['-n', '-f']
                },
                'wc': {
                    'description': 'Compte lignes/mots',
                    'allowed_args': ['-l', '-w', '-c']
                }
            }
        }
        
        os.makedirs(os.path.dirname(self.whitelist_path), exist_ok=True)
        with open(self.whitelist_path, 'w') as f:
            yaml.dump(default_whitelist, f, default_flow_style=False)
        
        logger.success(f"✅ Whitelist créée: {self.whitelist_path}")
    
    def is_command_allowed(self, command: str, args: List[str]) -> tuple[bool, str]:
        """
        Vérifie si une commande est autorisée
        
        Returns:
            (allowed: bool, reason: str)
        """
        if command not in self.whitelist:
            return False, f"Commande '{command}' non autorisée"
        
        cmd_config = self.whitelist[command]
        allowed_args = cmd_config.get('allowed_args', [])
        
        # Vérifier les arguments si whitelist définie
        if allowed_args:
            for arg in args:
                # Ignorer les arguments qui sont des chemins/valeurs
                if arg.startswith('-') or arg.startswith('--'):
                    if arg not in allowed_args:
                        return False, f"Argument '{arg}' non autorisé pour '{command}'"
        
        return True, "OK"
    
    def execute(self, command: str, args: List[str], timeout: int = 30, cwd: Optional[str] = None) -> CommandResponse:
        """
        Exécute une commande de manière sécurisée
        
        Args:
            command: Commande à exécuter
            args: Arguments
            timeout: Timeout en secondes
            cwd: Répertoire de travail
            
        Returns:
            CommandResponse avec résultat
        """
        # Construire commande complète pour la narration
        full_command = [command] + args
        command_str = ' '.join(full_command)
        
        # Narrer l'action AVANT exécution
        if self.narrator and HAS_NARRATOR:
            approved = narrate_system_command(
                self.narrator,
                command_str,
                purpose="traiter votre demande"
            )
            
            if not approved:
                logger.warning(f"⛔ Commande refusée par l'utilisateur: {command_str}")
                raise HTTPException(
                    status_code=403,
                    detail="Commande refusée par l'utilisateur"
                )
        
        # Vérifier autorisation
        allowed, reason = self.is_command_allowed(command, args)
        if not allowed:
            logger.warning(f"⛔ Commande refusée: {command} {' '.join(args)} - {reason}")
            
            # Communiquer le refus de manière transparente
            if self.narrator:
                print(f"\n🛑 **Commande Bloquée**")
                print(f"   Raison : {reason}")
                print(f"   Commande : `{command_str}`")
                print(f"\n   💡 Cette commande n'est pas dans la liste des commandes autorisées.")
            
            raise HTTPException(status_code=403, detail=reason)
        
        # Vérifier répertoire de travail
        if cwd and not any(cwd.startswith(allowed_dir) for allowed_dir in ALLOWED_DIRS):
            error_msg = f"Répertoire non autorisé: {cwd}"
            
            if self.narrator:
                print(f"\n🛑 **Accès Refusé**")
                print(f"   Répertoire demandé : {cwd}")
                print(f"   Répertoires autorisés : {', '.join(ALLOWED_DIRS)}")
            
            raise HTTPException(status_code=403, detail=error_msg)
        
        logger.info(f"⚙️  Exécution: {command_str}")
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                shell=False  # Important: pas de shell pour sécurité
            )
            
            # Communiquer le résultat de manière transparente
            if self.narrator and HAS_NARRATOR:
                if result.returncode == 0:
                    print(f"\n✅ **Commande Exécutée avec Succès**")
                    print(f"   Commande : `{command_str}`")
                    if result.stdout.strip():
                        preview = result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout
                        print(f"   Résultat :\n{preview}")
                else:
                    print(f"\n⚠️  **Commande Terminée avec Erreur**")
                    print(f"   Commande : `{command_str}`")
                    print(f"   Code de sortie : {result.returncode}")
                    if result.stderr.strip():
                        print(f"   Erreur : {result.stderr[:200]}")
            
            logger.success(f"✅ Commande terminée (exit={result.returncode})")
            
            return CommandResponse(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                command_executed=command_str
            )
            
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout: {command_str}"
            logger.error(f"❌ {error_msg}")
            
            if self.narrator:
                print(f"\n⏱️  **Commande Expirée**")
                print(f"   La commande a dépassé le délai maximum de {timeout} secondes")
                print(f"   Commande : `{command_str}`")
            
            raise HTTPException(status_code=408, detail=error_msg)
        except Exception as e:
            logger.error(f"❌ Erreur exécution: {e}")
            
            if self.narrator:
                print(f"\n❌ **Erreur d'Exécution**")
                print(f"   Erreur : {str(e)}")
                print(f"   Commande : `{command_str}`")
            
            raise HTTPException(status_code=500, detail=str(e))


# Instance globale
executor = SystemExecutor(WHITELIST_PATH)

# FastAPI app
app = FastAPI(title="HOPPER System Executor")


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "whitelist_loaded": len(executor.whitelist) > 0,
        "allowed_commands": list(executor.whitelist.keys()),
        "whitelist_path": executor.whitelist_path
    }


@app.post("/exec", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """
    Exécute une commande système de manière sécurisée
    
    Args:
        request: Commande et arguments
        
    Returns:
        Résultat d'exécution
    """
    return executor.execute(
        command=request.command,
        args=request.args,
        timeout=request.timeout,
        cwd=request.cwd
    )


@app.get("/commands")
async def list_commands():
    """Liste les commandes autorisées"""
    return {
        "commands": executor.whitelist,
        "count": len(executor.whitelist)
    }


@app.post("/whitelist/reload")
async def reload_whitelist():
    """Recharge la whitelist depuis le fichier"""
    executor.load_whitelist()
    return {
        "status": "reloaded",
        "commands_count": len(executor.whitelist)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SYSTEM_EXECUTOR_PORT", 5002))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
