"""
Collecteur de conversations pour fine-tuning - Phase 4
Enregistre les conversations pour créer un dataset d'entraînement
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import re


@dataclass
class ConversationTurn:
    """Un tour de conversation (user input + assistant response)"""
    timestamp: str
    user_input: str
    assistant_response: str
    intent: Optional[str] = None
    satisfaction_score: Optional[int] = None  # 1-5
    context: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ConversationCollector:
    """Collecte et stocke les conversations pour le fine-tuning"""
    
    def __init__(self, data_dir: Optional[Path] = None, anonymize: bool = True):
        """
        Initialise le collecteur
        
        Args:
            data_dir: Dossier de stockage des conversations
            anonymize: Anonymiser les données sensibles
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / "data" / "conversations"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.anonymize = anonymize
        
        # Patterns pour anonymisation
        self.sensitive_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
            (r'\b\d{10}\b', '[PHONE]'),  # Téléphone FR (10 chiffres)
            (r'\b\d{2}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}\b', '[PHONE]'),  # Tel formaté
            (r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '[DATE]'),  # Date
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),  # Carte bancaire
        ]
        
        self.current_conversation: List[ConversationTurn] = []
        self.conversation_id: Optional[str] = None
    
    def start_conversation(self) -> str:
        """
        Démarre une nouvelle conversation
        
        Returns:
            ID de la conversation
        """
        timestamp = datetime.now().isoformat()
        self.conversation_id = hashlib.md5(timestamp.encode()).hexdigest()[:12]
        self.current_conversation = []
        
        print(f"📝 Nouvelle conversation: {self.conversation_id}")
        return self.conversation_id
    
    def add_turn(self, user_input: str, assistant_response: str,
                 intent: Optional[str] = None,
                 satisfaction_score: Optional[int] = None,
                 context: Optional[Dict[str, Any]] = None,
                 error: Optional[str] = None) -> None:
        """
        Ajoute un tour de conversation
        
        Args:
            user_input: Entrée utilisateur
            assistant_response: Réponse de l'assistant
            intent: Intention détectée
            satisfaction_score: Score de satisfaction (1-5)
            context: Contexte additionnel
            error: Erreur éventuelle
        """
        # Anonymiser si nécessaire
        if self.anonymize:
            user_input = self._anonymize_text(user_input)
            assistant_response = self._anonymize_text(assistant_response)
        
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            assistant_response=assistant_response,
            intent=intent,
            satisfaction_score=satisfaction_score,
            context=context,
            error=error
        )
        
        self.current_conversation.append(turn)
        print(f"  ✅ Tour ajouté ({len(self.current_conversation)} tours)")
    
    def _anonymize_text(self, text: str) -> str:
        """
        Anonymise un texte en remplaçant les données sensibles
        
        Args:
            text: Texte à anonymiser
            
        Returns:
            Texte anonymisé
        """
        anonymized = text
        
        for pattern, replacement in self.sensitive_patterns:
            anonymized = re.sub(pattern, replacement, anonymized, flags=re.IGNORECASE)
        
        return anonymized
    
    def end_conversation(self, save: bool = True) -> Optional[str]:
        """
        Termine la conversation en cours
        
        Args:
            save: Sauvegarder la conversation
            
        Returns:
            Chemin du fichier sauvegardé ou None
        """
        if not self.current_conversation:
            print("⚠️  Aucune conversation à terminer")
            return None
        
        if save:
            filepath = self._save_conversation()
            print(f"💾 Conversation sauvegardée: {filepath}")
            
            # Réinitialiser
            self.current_conversation = []
            self.conversation_id = None
            
            return str(filepath)
        
        return None
    
    def _save_conversation(self) -> Path:
        """
        Sauvegarde la conversation courante
        
        Returns:
            Path du fichier sauvegardé
        """
        if not self.conversation_id:
            self.conversation_id = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:12]
        
        # Nom de fichier avec date et ID
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"conv_{date_str}_{self.conversation_id}.json"
        filepath = self.data_dir / filename
        
        # Préparer les données
        data = {
            'conversation_id': self.conversation_id,
            'start_time': self.current_conversation[0].timestamp if self.current_conversation else None,
            'end_time': self.current_conversation[-1].timestamp if self.current_conversation else None,
            'turns': [asdict(turn) for turn in self.current_conversation],
            'metadata': {
                'num_turns': len(self.current_conversation),
                'anonymized': self.anonymize,
                'avg_satisfaction': self._calculate_avg_satisfaction()
            }
        }
        
        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def _calculate_avg_satisfaction(self) -> Optional[float]:
        """Calcule la satisfaction moyenne de la conversation"""
        scores = [turn.satisfaction_score for turn in self.current_conversation 
                 if turn.satisfaction_score is not None]
        
        if not scores:
            return None
        
        return sum(scores) / len(scores)
    
    def load_conversations(self, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Charge les conversations depuis le stockage
        
        Args:
            start_date: Date de début (format YYYYMMDD)
            end_date: Date de fin (format YYYYMMDD)
            
        Returns:
            Liste des conversations
        """
        conversations = []
        
        # Lister les fichiers JSON
        for filepath in self.data_dir.glob("conv_*.json"):
            # Filtrer par date si nécessaire
            if start_date or end_date:
                date_str = filepath.stem.split('_')[1]  # conv_YYYYMMDD_id
                
                if start_date and date_str < start_date:
                    continue
                if end_date and date_str > end_date:
                    continue
            
            # Charger la conversation
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    conv = json.load(f)
                    conversations.append(conv)
            except Exception as e:
                print(f"⚠️  Erreur chargement {filepath}: {e}")
        
        print(f"📚 {len(conversations)} conversations chargées")
        return conversations
    
    def export_for_finetuning(self, output_file: Optional[Path] = None,
                              min_satisfaction: float = 3.0) -> Path:
        """
        Exporte les conversations au format fine-tuning
        
        Args:
            output_file: Fichier de sortie
            min_satisfaction: Score minimum de satisfaction
            
        Returns:
            Path du fichier exporté
        """
        if output_file is None:
            output_file = self.data_dir.parent / "training" / "finetuning_dataset.jsonl"
        
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Charger toutes les conversations
        conversations = self.load_conversations()
        
        # Préparer le dataset au format fine-tuning
        dataset = []
        
        for conv in conversations:
            avg_satisfaction = conv.get('metadata', {}).get('avg_satisfaction')
            
            # Filtrer par satisfaction
            if avg_satisfaction is not None and avg_satisfaction < min_satisfaction:
                continue
            
            # Extraire les paires instruction-réponse
            for turn in conv.get('turns', []):
                # Filtrer les tours avec erreur
                if turn.get('error'):
                    continue
                
                # Format fine-tuning (style ChatML)
                entry = {
                    "messages": [
                        {"role": "user", "content": turn['user_input']},
                        {"role": "assistant", "content": turn['assistant_response']}
                    ]
                }
                
                # Ajouter metadata si disponible
                if turn.get('intent'):
                    entry['metadata'] = [{'intent': turn['intent']}]
                
                dataset.append(entry)
        
        # Sauvegarder au format JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in dataset:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ Dataset fine-tuning exporté: {output_file}")
        print(f"   {len(dataset)} exemples (satisfaction ≥ {min_satisfaction})")
        
        return output_file
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques des conversations collectées"""
        conversations = self.load_conversations()
        
        total_turns = sum(conv['metadata']['num_turns'] for conv in conversations)
        
        satisfactions = [conv['metadata']['avg_satisfaction'] 
                        for conv in conversations 
                        if conv['metadata']['avg_satisfaction'] is not None]
        
        avg_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else None
        
        return {
            'total_conversations': len(conversations),
            'total_turns': total_turns,
            'avg_turns_per_conversation': total_turns / len(conversations) if conversations else 0,
            'avg_satisfaction': round(avg_satisfaction, 2) if avg_satisfaction else None,
            'conversations_with_errors': sum(
                1 for conv in conversations 
                if any(turn.get('error') for turn in conv.get('turns', []))
            )
        }


# Test du module
if __name__ == "__main__":
    print("="*60)
    print("TEST COLLECTEUR DE CONVERSATIONS")
    print("="*60)
    
    # Créer collecteur
    collector = ConversationCollector(anonymize=True)
    
    # Démarrer conversation
    conv_id = collector.start_conversation()
    
    # Ajouter quelques tours
    collector.add_turn(
        user_input="Quel temps fait-il aujourd'hui à Paris?",
        assistant_response="Il fait 15°C avec quelques nuages à Paris.",
        intent="weather_query",
        satisfaction_score=5
    )
    
    collector.add_turn(
        user_input="Envoie un email à jean.dupont@example.com",
        assistant_response="Email envoyé à [EMAIL]",
        intent="send_email",
        satisfaction_score=4
    )
    
    collector.add_turn(
        user_input="Appelle mon contact: 0612345678",
        assistant_response="Appel initié vers [PHONE]",
        intent="make_call",
        satisfaction_score=5
    )
    
    # Terminer et sauvegarder
    filepath = collector.end_conversation(save=True)
    
    # Afficher statistiques
    print("\n📊 Statistiques:")
    stats = collector.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Exporter pour fine-tuning
    print("\n📤 Export dataset fine-tuning...")
    dataset_file = collector.export_for_finetuning(min_satisfaction=3.0)
    
    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)
