"""
HOPPER - Prompt Builder
Construction de prompts structurés pour le LLM
Phase 2: Gestion contexte conversationnel et system prompts
"""

import yaml  # type: ignore[import-not-found]
from pathlib import Path
from typing import List, Dict, Optional, Any
from loguru import logger


class PromptBuilder:
    """
    Constructeur de prompts pour le LLM avec gestion du contexte conversationnel
    """
    
    def __init__(self, config_path: str = "/config/prompts.yaml"):
        """
        Initialize Prompt Builder
        
        Args:
            config_path: Chemin vers prompts.yaml
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        logger.info(f"✅ PromptBuilder initialisé depuis {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Charge configuration prompts depuis YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info("📄 Configuration prompts chargée")
                return config
        except FileNotFoundError:
            logger.warning(f"⚠️ {self.config_path} non trouvé, utilisation defaults")
            return self._default_config()
        except Exception as e:
            logger.error(f"❌ Erreur lecture prompts.yaml: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuration par défaut si fichier manquant"""
        return {
            'system_prompt': (
                "Tu es HOPPER, un assistant IA personnel local. "
                "Tu réponds en français de manière concise et utile."
            ),
            'conversation_template': "{system_prompt}\n\n{history}\n\nUtilisateur: {user_input}\nHOPPER:",
            'user_prefix': "Utilisateur:",
            'assistant_prefix': "HOPPER:",
            'default_max_tokens': 512,
            'default_temperature': 0.7,
            'max_history_tokens': 2048
        }
    
    def build_prompt(
        self, 
        user_input: str, 
        history: Optional[List[Dict[str, str]]] = None,
        knowledge_context: Optional[str] = None,
        max_history_tokens: Optional[int] = None
    ) -> str:
        """
        Construit le prompt complet pour le LLM
        
        Args:
            user_input: Question/commande utilisateur
            history: Historique [{"role": "user"/"assistant", "content": "..."}]
            knowledge_context: Contexte from Knowledge Base (RAG)
            max_history_tokens: Limite tokens contexte (défaut depuis config)
        
        Returns:
            Prompt formaté prêt pour le LLM
        """
        # Limite tokens historique
        max_hist_tokens: int = max_history_tokens if max_history_tokens is not None else self.config.get('max_history_tokens', 2048)
        
        # Formater historique conversationnel
        history_text = ""
        if history:
            history = self._truncate_history(history, max_hist_tokens * 4)  # ~4 chars/token
            
            for exchange in history:
                if exchange['role'] == 'user':
                    history_text += f"{self.config['user_prefix']} {exchange['content']}\n"
                elif exchange['role'] == 'assistant':
                    history_text += f"{self.config['assistant_prefix']} {exchange['content']}\n"
        
        # Ajouter knowledge context (RAG) si présent
        if knowledge_context:
            history_text += f"\n[Contexte pertinent de la base de connaissances]\n{knowledge_context}\n"
        
        # Construire prompt complet
        prompt = self.config['conversation_template'].format(
            system_prompt=self.config['system_prompt'],
            history=history_text.strip(),
            user_input=user_input
        )
        
        logger.debug(f"📝 Prompt construit: {len(prompt)} caractères")
        
        return prompt
    
    def _truncate_history(self, history: List[Dict[str, str]], max_chars: int) -> List[Dict[str, str]]:
        """
        Garde seulement les N derniers échanges qui tiennent dans max_chars
        
        Args:
            history: Liste complète historique
            max_chars: Limite caractères
            
        Returns:
            Historique tronqué (les plus récents)
        """
        total_chars = 0
        truncated = []
        
        # Parcourir à l'envers (garder les plus récents)
        for exchange in reversed(history):
            exchange_chars = len(exchange['content'])
            
            # Vérifier si on dépasse
            if total_chars + exchange_chars > max_chars:
                break
            
            truncated.insert(0, exchange)
            total_chars += exchange_chars
        
        if len(truncated) < len(history):
            logger.info(
                f"📊 Historique tronqué: {len(history)} → {len(truncated)} échanges "
                f"({total_chars} chars)"
            )
        
        return truncated
    
    def get_generation_params(self) -> Dict[str, Any]:
        """
        Retourne paramètres de génération par défaut
        
        Returns:
            Dict avec max_tokens, temperature, etc.
        """
        return {
            'max_tokens': self.config.get('default_max_tokens', 512),
            'temperature': self.config.get('default_temperature', 0.7),
            'top_p': self.config.get('default_top_p', 0.95)
        }
    
    def reload_config(self):
        """Recharge la configuration depuis le fichier"""
        self.config = self._load_config()
        logger.info("🔄 Configuration prompts rechargée")
