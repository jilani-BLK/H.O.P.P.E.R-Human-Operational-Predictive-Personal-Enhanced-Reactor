"""
HOPPER - System Tools Integration
Permet au LLM d'utiliser LocalSystem et FileSystem via langage naturel
"""

import re
import httpx
from typing import Dict, Any, Optional, List
from loguru import logger


class SystemToolsIntegration:
    """
    Intègre LocalSystem et FileSystem pour que le LLM puisse les appeler
    
    Le LLM peut demander:
    - "ouvre TextEdit"           → open_app
    - "liste mes applications"   → list_apps
    - "lis le fichier README"    → read_file
    - "cherche fichiers python"  → find_files ou search
    - "infos système"            → get_system_info
    - "exécute echo hello"       → execute_script
    """
    
    CONNECTORS_URL = "http://localhost:5006"
    ANTIVIRUS_URL = "http://localhost:5007"
    
    # Patterns de détection dans le texte du LLM
    # NOTE: L'ordre est important ! Les patterns plus spécifiques doivent venir en premier
    PATTERNS = {
        # Fichiers - Doit être AVANT open_app pour éviter conflit avec "ouvre"
        "read_file": [
            r"(?:lis|lire|affiche|afficher|montre(?:-moi)?|montrer)\s+(?:le\s+)?(?:fichier\s+)?['\"]?([^'\"]+\.[a-z0-9]{2,4})['\"]?",
            r"(?:lis|lire|affiche|afficher|montre(?:-moi)?|montrer)\s+(?:le\s+)?fichier\s+['\"]?([^'\"]+)['\"]?",
            r"(?:read|show|display)\s+(?:file\s+)?['\"]?([^'\"]+\.[a-z0-9]{2,4})['\"]?",
            r"(?:ouvre|ouvrir)\s+(?:le\s+)?fichier\s+['\"]?([^'\"]+)['\"]?"
        ],
        
        # Applications - Plus strict maintenant
        "open_app": [
            r"(?:ouvre|démarre|ouvrir|démarrer)\s+(?!le\s+fichier|fichier|la\s+porte|les?\s)([A-Z][A-Za-z0-9\s]{1,30}?)(?:\?|!|\.|$)",
            r"(?:lance|lancer)\s+(?!la\s+commande)(?:l'application\s+)?([A-Z][A-Za-z0-9\s]{1,30}?)(?:\?|!|\.|$)",
            r"(?:open|start)\s+(?:the\s+)?([A-Z][A-Za-z0-9\s]{1,30}?)(?:\?|!|\.|$)"
        ],
        "close_app": [
            r"(?:ferme|fermer|quitte|quitter)\s+(?:l'application\s+)?(.+)",
            r"(?:close|quit)\s+(.+)"
        ],
        "list_apps": [
            r"(?:liste|lister|affiche|afficher)\s+(?:mes\s+)?(?:les\s+)?(?:applications?|apps?)",
            r"(?:montre|montrer)(?:-moi)?\s+(?:les\s+)?(?:applications?|apps?)(?:\s+install)?",
            r"(?:list|show)\s+(?:my\s+)?(?:applications?|apps?)",
            r"quelles?\s+(?:applications?|apps?).*(?:install|disponible)"
        ],
        "list_directory": [
            r"(?:liste|lister|affiche|afficher)\s+(?:le\s+)?(?:contenu\s+(?:du\s+)?)?(?:dossier|répertoire|directory)\s+(.+)",
            r"(?:list|show)\s+(?:directory|folder)\s+(.+)"
        ],
        "find_files": [
            r"(?:cherche|chercher|trouve|trouver|recherche|rechercher)\s+(?:des\s+)?fichiers?\s+(.+)",
            r"(?:find|search)\s+files?\s+(.+)"
        ],
        
        # Système
        "get_system_info": [
            r"(?:infos?|informations?)\s+(?:du\s+|de\s+(?:la\s+)?)?(?:système|machine|ordinateur)",
            r"(?:system|machine|computer)\s+info",
            r"état\s+(?:de\s+)?(?:la\s+)?(?:machine|système)"
        ],
        "execute_script": [
            r"(?:exécute|exécuter)\s+(?:la\s+commande\s+)?['\"]?(.+)['\"]?",
            r"(?:lance|lancer)\s+(?:la\s+commande)\s+['\"]?(.+)['\"]?",
            r"(?:execute|run)\s+['\"]?(.+)['\"]?"
        ],
        
        # Antivirus - Scan
        "scan_system": [
            r"scann?e?\s+(?:mon\s+)?(?:système|ordinateur|pc|mac|machine)",
            r"(?:recherch(?:e|er)|cherch(?:e|er))\s+(?:des?\s+)?(?:virus|malware|menace)",
            r"vérifi(?:e|er)\s+(?:si|les)\s+(?:virus|malware|menace)",
            r"analys(?:e|er)\s+(?:mon\s+)?(?:système|ordinateur)",
            r"détect(?:e|er)\s+(?:des?\s+)?(?:virus|malware|menace)",
            r"y\s+a-t-il\s+des\s+(?:virus|malware|menace)"
        ],
        "scan_file": [
            r"scann?e?\s+(?:le\s+)?fichier\s+(.+)",
            r"vérifi(?:e|er)\s+(?:le\s+)?fichier\s+(.+)",
            r"analys(?:e|er)\s+(?:le\s+)?fichier\s+(.+)"
        ],
        "scan_quick": [
            r"scan\s+rapide",
            r"quick\s+scan",
            r"scann?e?\s+(?:zones?\s+)?critique"
        ],
        
        # Antivirus - Actions
        "quarantine_threat": [
            r"met(?:tre|s)?\s+en\s+quarantaine\s+(.+)",
            r"isol(?:e|er)\s+(?:le\s+)?(?:fichier|virus|menace)\s+(.+)",
            r"quarantaine\s+(.+)"
        ],
        "remove_virus": [
            r"supprim(?:e|er)\s+(?:le|les)\s+(?:virus|malware|menace)",
            r"élimin(?:e|er)\s+(?:le|les)\s+(?:virus|malware|menace)",
            r"nettoy(?:e|er)\s+(?:le|les)\s+(?:virus|malware)",
            r"détruit|effac(?:e|er)\s+(?:le|les)\s+(?:virus|malware)"
        ],
        
        # Antivirus - Status
        "check_protection": [
            r"(?:état|status)\s+(?:de\s+)?(?:la\s+)?protection",
            r"antivirus\s+(?:actif|activé|fonctionne)",
            r"suis-je\s+protégé",
            r"protection\s+(?:en\s+)?cours"
        ],
        "update_antivirus": [
            r"met(?:tre|s)?\s+à\s+jour\s+(?:l')?antivirus",
            r"met(?:tre|s)?\s+à\s+jour\s+(?:les\s+)?(?:définitions|signatures)",
            r"updat(?:e|er)\s+(?:antivirus|definitions)",
            r"actualise(?:r)?\s+(?:l')?antivirus"
        ]
    }
    
    async def detect_and_execute(self, llm_response: str, user_query: str) -> Optional[Dict[str, Any]]:
        """
        Détecte si le LLM veut utiliser un outil système et l'exécute
        
        Args:
            llm_response: Réponse du LLM
            user_query: Question originale de l'utilisateur
            
        Returns:
            Résultat de l'exécution ou None
        """
        # Chercher dans la réponse LLM ET la question utilisateur
        combined_text = f"{user_query} {llm_response}".lower()
        
        # Tester chaque pattern
        for action, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, combined_text, re.IGNORECASE)
                if match:
                    logger.info(f"🎯 Détecté: {action} via pattern: {pattern}")
                    
                    # Extraire paramètres
                    params = self._extract_params(action, match, combined_text)
                    
                    # Exécuter l'action
                    result = await self._execute_action(action, params)
                    
                    if result:
                        return {
                            "action": action,
                            "params": params,
                            "result": result
                        }
        
        return None
    
    def _extract_params(self, action: str, match: re.Match, text: str) -> Dict[str, Any]:
        """Extraire paramètres selon l'action"""
        params = {}
        
        if action == "open_app":
            app_name = match.group(1).strip()
            # Nettoyer le nom
            app_name = app_name.replace("l'application", "").replace("le fichier", "").strip()
            
            # Validation: pas de mots parasites
            invalid_words = ["fichier", "file", "dossier", "folder", "tout", "le", "la", "les"]
            app_words = app_name.lower().split()
            if any(word in invalid_words for word in app_words):
                logger.debug(f"⚠️ Nom d'app invalide: {app_name}")
                return {}
            
            # Validation: nom d'app commence par majuscule et contient 2-50 chars
            if not app_name or len(app_name) < 2 or len(app_name) > 50:
                logger.debug(f"⚠️ Longueur invalide: {app_name}")
                return {}
            
            params["app_name"] = app_name.title()  # TextEdit, VS Code, etc.
        
        elif action == "close_app":
            app_name = match.group(1).strip()
            if not app_name or len(app_name) < 2:
                return {}
            params["app_name"] = app_name.title()
        
        elif action == "read_file":
            file_path = match.group(1).strip()
            # Enlever guillemets si présents
            file_path = file_path.strip("'\"")
            
            # Validation: doit ressembler à un chemin de fichier
            if not file_path or len(file_path) < 2:
                return {}
            
            # Validation: ne doit pas contenir de mots d'actions
            invalid_in_path = ["ouvre", "lance", "liste", "affiche"]
            if any(word in file_path.lower() for word in invalid_in_path):
                logger.debug(f"⚠️ Chemin fichier invalide: {file_path}")
                return {}
            
            params["file_path"] = file_path
            params["max_lines"] = 50  # Limite pour ne pas surcharger
        
        elif action == "list_directory":
            dir_path = match.group(1).strip()
            params["path"] = dir_path
        
        elif action == "find_files":
            pattern = match.group(1).strip()
            # Extraire extension si mentionnée
            if "python" in pattern.lower() or ".py" in pattern:
                params["pattern"] = "*.py"
            elif "javascript" in pattern.lower() or ".js" in pattern:
                params["pattern"] = "*.js"
            else:
                params["pattern"] = f"*{pattern}*"
        
        elif action == "execute_script":
            script = match.group(1).strip()
            script = script.strip("'\"")
            params["script"] = script
        
        # Antivirus actions
        elif action == "scan_file":
            file_path = match.group(1).strip()
            params["file_path"] = file_path
        
        elif action == "quarantine_threat":
            file_path = match.group(1).strip()
            params["file_path"] = file_path
            params["reason"] = "Detected by user request"
        
        # Actions sans params
        elif action in ["scan_system", "scan_quick", "remove_virus", 
                       "check_protection", "update_antivirus"]:
            pass  # Pas de paramètres nécessaires
        
        return params
    
    async def _execute_action(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Exécuter l'action via le Connectors Service ou Antivirus Service"""
        
        # Actions antivirus → service antivirus
        antivirus_actions = [
            "scan_system", "scan_file", "scan_quick", 
            "quarantine_threat", "remove_virus",
            "check_protection", "update_antivirus"
        ]
        
        if action in antivirus_actions:
            return await self._execute_antivirus_action(action, params)
        
        # Actions système → connectors service
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.CONNECTORS_URL}/execute",
                    json={
                        "connector": "local_system",
                        "action": action,
                        "params": params,
                        "user_id": "llm_orchestrator"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.success(f"✅ Action {action} exécutée")
                    return result
                else:
                    logger.error(f"❌ Erreur {response.status_code}: {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"❌ Erreur exécution {action}: {e}")
            return None
    
    def format_result_for_llm(self, tool_result: Dict[str, Any]) -> str:
        """
        Formater le résultat d'un outil pour que le LLM puisse l'utiliser
        
        Returns:
            Contexte enrichi à ajouter au prompt
        """
        if not tool_result:
            return ""
        
        action = tool_result.get("action", "unknown")
        result = tool_result.get("result", {})
        
        if not result.get("success"):
            error = result.get("error", "Erreur inconnue")
            return f"\n[SYSTÈME] ❌ Échec {action}: {error}"
        
        data = result.get("data", {})
        
        # Formater selon l'action
        if action == "list_apps":
            apps = data.get("applications", [])
            apps_str = ", ".join(apps[:10])  # Limiter à 10
            return f"\n[SYSTÈME] ✅ Applications installées ({len(apps)}): {apps_str}"
        
        elif action == "open_app":
            app_name = tool_result["params"].get("app_name")
            return f"\n[SYSTÈME] ✅ Application '{app_name}' lancée avec succès"
        
        elif action == "close_app":
            app_name = tool_result["params"].get("app_name")
            return f"\n[SYSTÈME] ✅ Application '{app_name}' fermée"
        
        elif action == "read_file":
            content = data.get("content", "")
            lines = content.split("\n")
            preview = "\n".join(lines[:20])  # 20 premières lignes
            return f"\n[SYSTÈME] ✅ Contenu du fichier:\n{preview}\n[...{len(lines)} lignes au total]"
        
        elif action == "list_directory":
            files = data.get("files", [])
            dirs = data.get("directories", [])
            return f"\n[SYSTÈME] ✅ Contenu: {len(dirs)} dossiers, {len(files)} fichiers"
        
        elif action == "find_files":
            files = data.get("files", [])
            files_str = "\n".join([f"  - {f}" for f in files[:10]])
            return f"\n[SYSTÈME] ✅ Fichiers trouvés ({len(files)}):\n{files_str}"
        
        elif action == "get_system_info":
            info = data.get("system_info", {})
            return f"\n[SYSTÈME] ✅ Info: OS={info.get('os')}, RAM={info.get('ram_total')}, CPU={info.get('cpu_cores')} cores"
        
        elif action == "execute_script":
            stdout = data.get("stdout", "")
            stderr = data.get("stderr", "")
            returncode = data.get("returncode", -1)
            output = stdout if stdout else stderr
            return f"\n[SYSTÈME] ✅ Script exécuté (code {returncode}):\n{output[:500]}"
        
        # Antivirus actions
        elif action == "scan_system":
            threats = result.get("threats_found", 0)
            files = result.get("total_files_scanned", 0)
            if threats > 0:
                return f"\n[ANTIVIRUS] ⚠️ MENACES DÉTECTÉES ! {threats} menace(s) sur {files} fichiers scannés"
            return f"\n[ANTIVIRUS] ✅ Système sain: {files} fichiers scannés, aucune menace"
        
        elif action == "scan_file":
            clean = result.get("clean", True)
            threats = result.get("threats", [])
            if not clean:
                threat_names = [t.get("name") for t in threats]
                return f"\n[ANTIVIRUS] ⚠️ MENACE DÉTECTÉE: {', '.join(threat_names)}"
            return f"\n[ANTIVIRUS] ✅ Fichier sain, aucune menace détectée"
        
        elif action == "scan_quick":
            threats = result.get("threats_found", 0)
            if threats > 0:
                return f"\n[ANTIVIRUS] ⚠️ {threats} menace(s) trouvée(s) lors du scan rapide"
            return f"\n[ANTIVIRUS] ✅ Scan rapide terminé, aucune menace"
        
        elif action == "quarantine_threat":
            path = result.get("quarantine_path", "")
            return f"\n[ANTIVIRUS] ✅ Fichier mis en quarantaine: {path}"
        
        elif action == "remove_virus":
            return f"\n[ANTIVIRUS] ✅ Menace supprimée avec succès"
        
        elif action == "check_protection":
            enabled = result.get("enabled", False)
            threats_q = result.get("threats_quarantined", 0)
            threats_r = result.get("threats_removed", 0)
            return f"\n[ANTIVIRUS] ✅ Protection: {'Activée' if enabled else 'Désactivée'} | Quarantaine: {threats_q} | Supprimés: {threats_r}"
        
        elif action == "update_antivirus":
            return f"\n[ANTIVIRUS] ✅ Définitions mises à jour avec succès"
        
        return f"\n[SYSTÈME] ✅ Action {action} terminée"
    
    async def _execute_antivirus_action(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Exécute une action antivirus"""
        try:
            # Mapping action → endpoint
            endpoint_map = {
                "scan_system": "/scan/full",
                "scan_file": "/scan/file",
                "scan_quick": "/scan/quick",
                "quarantine_threat": "/quarantine",
                "remove_virus": "/threat/remove",
                "check_protection": "/status",
                "update_antivirus": "/update"
            }
            
            endpoint = endpoint_map.get(action)
            if not endpoint:
                logger.error(f"Unknown antivirus action: {action}")
                return None
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # Timeout plus long pour scans
                # GET ou POST selon l'endpoint
                if endpoint in ["/status"]:
                    response = await client.get(f"{self.ANTIVIRUS_URL}{endpoint}")
                else:
                    response = await client.post(
                        f"{self.ANTIVIRUS_URL}{endpoint}",
                        json=params
                    )
                
                response.raise_for_status()
                result_data = response.json()
                
                logger.info(f"✅ Antivirus action '{action}' executed successfully")
                
                return {
                    "success": True,
                    "data": result_data
                }
        
        except httpx.TimeoutException:
            logger.error(f"Timeout executing antivirus action: {action}")
            return {
                "success": False,
                "error": "Timeout - l'analyse prend trop de temps"
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error executing antivirus action: {e}")
            return {
                "success": False,
                "error": f"Erreur HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Error executing antivirus action: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Instance globale
system_tools = SystemToolsIntegration()
