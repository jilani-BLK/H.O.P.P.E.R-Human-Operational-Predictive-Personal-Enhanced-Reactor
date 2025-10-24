"""
Système de Feedback Utilisateur - Phase 4
Collecte et analyse la satisfaction utilisateur en temps réel
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics


@dataclass
class FeedbackEntry:
    """Une entrée de feedback utilisateur"""
    timestamp: str
    score: int  # 1-5
    comment: Optional[str] = None
    context: Optional[str] = None  # morning, evening, urgent, etc.
    interaction_type: Optional[str] = None  # voice, text, auto
    response_time_ms: Optional[int] = None
    error_occurred: bool = False
    tags: Optional[List[str]] = None


class FeedbackManager:
    """Gestionnaire de feedback utilisateur"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialise le gestionnaire de feedback
        
        Args:
            data_dir: Dossier de stockage du feedback
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / "data" / "feedback"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache en mémoire pour feedback du jour
        self.today_feedback: List[FeedbackEntry] = []
        self.load_today_feedback()
    
    def add_feedback(self, score: int, comment: Optional[str] = None,
                    context: Optional[str] = None,
                    interaction_type: Optional[str] = None,
                    response_time_ms: Optional[int] = None,
                    error_occurred: bool = False,
                    tags: Optional[List[str]] = None) -> bool:
        """
        Ajoute un feedback utilisateur
        
        Args:
            score: Score de satisfaction (1-5)
            comment: Commentaire optionnel
            context: Contexte (morning, evening, etc.)
            interaction_type: Type d'interaction
            response_time_ms: Temps de réponse en ms
            error_occurred: Si une erreur s'est produite
            tags: Tags pour catégoriser
            
        Returns:
            True si ajouté avec succès
        """
        # Valider le score
        if not 1 <= score <= 5:
            print(f"⚠️  Score invalide: {score} (doit être 1-5)")
            return False
        
        # Créer l'entrée
        feedback = FeedbackEntry(
            timestamp=datetime.now().isoformat(),
            score=score,
            comment=comment,
            context=context,
            interaction_type=interaction_type,
            response_time_ms=response_time_ms,
            error_occurred=error_occurred,
            tags=tags or []
        )
        
        # Ajouter au cache
        self.today_feedback.append(feedback)
        
        # Sauvegarder
        self._save_feedback(feedback)
        
        # Analyser si score faible
        if score <= 2:
            self._analyze_low_score(feedback)
        
        print(f"✅ Feedback enregistré: {score}/5 {f'({comment})' if comment else ''}")
        return True
    
    def _save_feedback(self, feedback: FeedbackEntry) -> None:
        """Sauvegarde un feedback dans le fichier du jour"""
        date_str = datetime.now().strftime("%Y%m%d")
        filepath = self.data_dir / f"feedback_{date_str}.jsonl"
        
        # Append au fichier JSONL
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(feedback), ensure_ascii=False) + '\n')
    
    def load_today_feedback(self) -> List[FeedbackEntry]:
        """Charge le feedback du jour depuis le fichier"""
        date_str = datetime.now().strftime("%Y%m%d")
        filepath = self.data_dir / f"feedback_{date_str}.jsonl"
        
        self.today_feedback = []
        
        if not filepath.exists():
            return self.today_feedback
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        feedback = FeedbackEntry(**data)
                        self.today_feedback.append(feedback)
        except Exception as e:
            print(f"⚠️  Erreur chargement feedback: {e}")
        
        return self.today_feedback
    
    def _analyze_low_score(self, feedback: FeedbackEntry) -> None:
        """Analyse un feedback avec score faible pour identifier le problème"""
        print(f"\n⚠️  ALERTE: Score faible détecté ({feedback.score}/5)")
        
        # Analyser le contexte
        issues = []
        
        if feedback.error_occurred:
            issues.append("Erreur système")
        
        if feedback.response_time_ms and feedback.response_time_ms > 5000:
            issues.append(f"Temps de réponse élevé ({feedback.response_time_ms}ms)")
        
        if feedback.context == "morning" and feedback.score <= 2:
            issues.append("Problème récurrent le matin")
        
        if feedback.comment:
            # Recherche de mots-clés dans le commentaire
            keywords = {
                'lent': 'Performance',
                'slow': 'Performance',
                'erreur': 'Erreur',
                'error': 'Erreur',
                'comprend pas': 'Compréhension',
                'understand': 'Compréhension',
                'répond mal': 'Qualité réponse',
            }
            
            comment_lower = feedback.comment.lower()
            for keyword, issue_type in keywords.items():
                if keyword in comment_lower:
                    issues.append(issue_type)
        
        if issues:
            print(f"   Problèmes identifiés: {', '.join(set(issues))}")
        
        # Logger pour analyse ultérieure
        self._log_issue(feedback, issues)
    
    def _log_issue(self, feedback: FeedbackEntry, issues: List[str]) -> None:
        """Log un problème identifié"""
        issue_log = self.data_dir / "issues.jsonl"
        
        issue_entry = {
            'timestamp': feedback.timestamp,
            'score': feedback.score,
            'issues': issues,
            'comment': feedback.comment,
            'context': feedback.context
        }
        
        with open(issue_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(issue_entry, ensure_ascii=False) + '\n')
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Retourne un résumé du feedback d'une journée
        
        Args:
            date: Date au format YYYYMMDD (aujourd'hui par défaut)
            
        Returns:
            Dictionnaire avec statistiques
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
            feedback_list = self.today_feedback
        else:
            feedback_list = self._load_feedback_for_date(date)
        
        if not feedback_list:
            return {
                'date': date,
                'total_feedback': 0,
                'avg_score': None,
                'distribution': {},
                'low_score_count': 0,
                'high_score_count': 0
            }
        
        scores = [f.score for f in feedback_list]
        
        # Distribution des scores
        distribution = defaultdict(int)
        for score in scores:
            distribution[score] += 1
        
        # Compter scores bas/hauts
        low_score_count = sum(1 for s in scores if s <= 2)
        high_score_count = sum(1 for s in scores if s >= 4)
        
        return {
            'date': date,
            'total_feedback': len(feedback_list),
            'avg_score': round(statistics.mean(scores), 2),
            'median_score': statistics.median(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'distribution': dict(distribution),
            'low_score_count': low_score_count,
            'high_score_count': high_score_count,
            'satisfaction_rate': round(high_score_count / len(feedback_list) * 100, 1),
            'with_errors': sum(1 for f in feedback_list if f.error_occurred)
        }
    
    def _load_feedback_for_date(self, date: str) -> List[FeedbackEntry]:
        """Charge le feedback pour une date donnée"""
        filepath = self.data_dir / f"feedback_{date}.jsonl"
        
        if not filepath.exists():
            return []
        
        feedback_list = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        feedback_list.append(FeedbackEntry(**data))
        except Exception as e:
            print(f"⚠️  Erreur chargement feedback {date}: {e}")
        
        return feedback_list
    
    def get_weekly_summary(self, weeks: int = 1) -> Dict[str, Any]:
        """
        Retourne un résumé sur N semaines
        
        Args:
            weeks: Nombre de semaines
            
        Returns:
            Statistiques agrégées
        """
        today = datetime.now()
        all_feedback = []
        
        # Charger feedback des N dernières semaines
        for i in range(weeks * 7):
            date = (today - timedelta(days=i)).strftime("%Y%m%d")
            feedback_list = self._load_feedback_for_date(date)
            all_feedback.extend(feedback_list)
        
        if not all_feedback:
            return {'period': f'{weeks} week(s)', 'total_feedback': 0}
        
        scores = [f.score for f in all_feedback]
        
        return {
            'period': f'{weeks} week(s)',
            'total_feedback': len(all_feedback),
            'avg_score': round(statistics.mean(scores), 2),
            'trend': self._calculate_trend(all_feedback),
            'most_common_issues': self._extract_common_issues(all_feedback),
            'best_context': self._find_best_context(all_feedback),
            'worst_context': self._find_worst_context(all_feedback)
        }
    
    def _calculate_trend(self, feedback_list: List[FeedbackEntry]) -> str:
        """Calcule la tendance (amélioration/dégradation)"""
        if len(feedback_list) < 2:
            return "insufficient_data"
        
        # Diviser en deux moitiés
        mid = len(feedback_list) // 2
        first_half = [f.score for f in feedback_list[:mid]]
        second_half = [f.score for f in feedback_list[mid:]]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        diff = avg_second - avg_first
        
        if diff > 0.3:
            return "improving"
        elif diff < -0.3:
            return "declining"
        else:
            return "stable"
    
    def _extract_common_issues(self, feedback_list: List[FeedbackEntry]) -> List[str]:
        """Extrait les problèmes les plus fréquents"""
        issue_counts = defaultdict(int)
        
        for feedback in feedback_list:
            if feedback.comment:
                # Recherche de mots-clés
                comment_lower = feedback.comment.lower()
                
                if 'lent' in comment_lower or 'slow' in comment_lower:
                    issue_counts['performance'] += 1
                if 'erreur' in comment_lower or 'error' in comment_lower:
                    issue_counts['errors'] += 1
                if 'comprend' in comment_lower or 'understand' in comment_lower:
                    issue_counts['comprehension'] += 1
        
        # Retourner top 3
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return [issue for issue, _ in sorted_issues[:3]]
    
    def _find_best_context(self, feedback_list: List[FeedbackEntry]) -> Optional[str]:
        """Trouve le contexte avec le meilleur score moyen"""
        context_scores = defaultdict(list)
        
        for feedback in feedback_list:
            if feedback.context:
                context_scores[feedback.context].append(feedback.score)
        
        if not context_scores:
            return None
        
        avg_by_context = {ctx: statistics.mean(scores) 
                         for ctx, scores in context_scores.items()}
        
        return max(avg_by_context.keys(), key=lambda k: avg_by_context[k])
    
    def _find_worst_context(self, feedback_list: List[FeedbackEntry]) -> Optional[str]:
        """Trouve le contexte avec le pire score moyen"""
        context_scores = defaultdict(list)
        
        for feedback in feedback_list:
            if feedback.context:
                context_scores[feedback.context].append(feedback.score)
        
        if not context_scores:
            return None
        
        avg_by_context = {ctx: statistics.mean(scores) 
                         for ctx, scores in context_scores.items()}
        
        return min(avg_by_context.keys(), key=lambda k: avg_by_context[k])
    
    def should_request_feedback(self) -> bool:
        """
        Détermine s'il faut demander du feedback maintenant
        
        Returns:
            True si feedback doit être demandé
        """
        # Vérifier si déjà feedback aujourd'hui
        if len(self.today_feedback) >= 3:
            return False  # Max 3 feedback par jour
        
        # Vérifier l'heure (idéal: soir)
        now = datetime.now()
        if 20 <= now.hour <= 22:
            return True
        
        # Si aucun feedback de la journée et après 18h
        if len(self.today_feedback) == 0 and now.hour >= 18:
            return True
        
        return False
    
    def get_feedback_prompt(self) -> str:
        """Retourne le prompt pour demander du feedback"""
        prompts = [
            "Comment évaluez-vous mon aide aujourd'hui ? (1-5 étoiles)",
            "Êtes-vous satisfait de mes réponses aujourd'hui ? (1-5)",
            "Sur une échelle de 1 à 5, comment ai-je performé aujourd'hui ?",
            "Aidez-moi à m'améliorer : notez ma performance aujourd'hui (1-5)"
        ]
        
        # Alterner les prompts
        index = len(self.today_feedback) % len(prompts)
        return prompts[index]


# Test du module
if __name__ == "__main__":
    print("="*60)
    print("TEST GESTIONNAIRE DE FEEDBACK")
    print("="*60)
    
    # Créer gestionnaire
    manager = FeedbackManager()
    
    # Simuler quelques feedbacks
    print("\n📝 Ajout de feedbacks...")
    manager.add_feedback(5, "Excellente réponse rapide!", context="morning", response_time_ms=250)
    manager.add_feedback(4, "Bien mais un peu lent", context="afternoon", response_time_ms=3500)
    manager.add_feedback(2, "Ne comprend pas ma question", context="evening", error_occurred=False)
    manager.add_feedback(5, None, context="evening", response_time_ms=180)
    
    # Résumé du jour
    print("\n📊 Résumé du jour:")
    summary = manager.get_daily_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Vérifier si demander feedback
    print(f"\n🔔 Demander feedback maintenant ? {manager.should_request_feedback()}")
    print(f"   Prompt: \"{manager.get_feedback_prompt()}\"")
    
    # Résumé hebdomadaire
    print("\n📈 Résumé hebdomadaire:")
    weekly = manager.get_weekly_summary(weeks=1)
    for key, value in weekly.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)
