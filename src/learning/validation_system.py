"""
Système de validation humaine pour HOPPER
Workflow pour valider adaptations importantes et garder contrôle humain
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ValidationType(Enum):
    """Types de validation"""
    ADAPTATION = "adaptation"  # Validation d'adaptation comportementale
    KNOWLEDGE = "knowledge"  # Validation de connaissance
    CORRECTION = "correction"  # Validation de correction
    SAFETY = "safety"  # Validation de sécurité
    PERMISSION = "permission"  # Demande de permission


class ValidationStatus(Enum):
    """Statuts de validation"""
    PENDING = "pending"  # En attente
    APPROVED = "approved"  # Approuvé
    REJECTED = "rejected"  # Rejeté
    NEEDS_REVIEW = "needs_review"  # Nécessite révision
    EXPIRED = "expired"  # Expiré (timeout)


class RiskLevel(Enum):
    """Niveaux de risque"""
    LOW = "low"  # Risque faible, auto-approuvable
    MEDIUM = "medium"  # Risque moyen, validation recommandée
    HIGH = "high"  # Risque élevé, validation requise
    CRITICAL = "critical"  # Risque critique, validation obligatoire


@dataclass
class ValidationRequest:
    """Requête de validation"""
    id: str
    validation_type: ValidationType
    risk_level: RiskLevel
    
    # Contenu
    title: str
    description: str
    proposed_change: Dict[str, Any]
    rationale: str
    
    # Contexte
    context: Dict[str, Any] = field(default_factory=dict)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # État
    status: ValidationStatus = ValidationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Décision
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_reason: Optional[str] = None
    
    # Révisions
    revisions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SafetyGuardrail:
    """Garde-fou de sécurité"""
    rule_id: str
    name: str
    description: str
    check_function: str  # Nom de la fonction de vérification
    risk_level: RiskLevel
    enabled: bool = True
    times_triggered: int = 0


class ValidationSystem:
    """
    Système de validation humaine
    - Gère les requêtes de validation
    - Applique des garde-fous de sécurité
    - Maintient audit trail
    - Permet auto-approbation pour risques faibles
    """
    
    def __init__(
        self,
        storage_path: str = "data/validation/",
        auto_approve_low_risk: bool = True,
        validation_timeout_hours: int = 24
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.auto_approve_low_risk = auto_approve_low_risk
        self.validation_timeout = timedelta(hours=validation_timeout_hours)
        
        # Requêtes de validation
        self.requests: Dict[str, ValidationRequest] = {}
        
        # Garde-fous de sécurité
        self.guardrails: Dict[str, SafetyGuardrail] = {}
        
        # Historique des décisions
        self.decision_history: List[Dict[str, Any]] = []
        
        # Statistiques
        self.stats = {
            "total_requests": 0,
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "expired": 0,
            "auto_approved": 0,
            "manual_approvals": 0,
            "safety_blocks": 0
        }
        
        # Initialiser garde-fous
        self._initialize_guardrails()
        
        # Charger état
        self._load_state()
    
    def submit_validation_request(
        self,
        validation_type: ValidationType,
        title: str,
        description: str,
        proposed_change: Dict[str, Any],
        rationale: str,
        context: Optional[Dict[str, Any]] = None,
        require_validation: bool = False
    ) -> str:
        """
        Soumet une requête de validation
        
        Returns:
            ID de la requête
        """
        
        # Analyser le risque
        risk_level = self._assess_risk(
            validation_type,
            proposed_change,
            context or {}
        )
        
        # Vérifier les garde-fous
        safety_check = self._check_safety(proposed_change, context or {})
        if not safety_check["safe"]:
            # Bloquer immédiatement
            self.stats["safety_blocks"] += 1
            raise ValueError(f"Bloqué par garde-fou: {safety_check['reason']}")
        
        # Créer requête
        request_id = f"val_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Analyser l'impact
        impact = self._analyze_impact(proposed_change, context or {})
        
        request = ValidationRequest(
            id=request_id,
            validation_type=validation_type,
            risk_level=risk_level,
            title=title,
            description=description,
            proposed_change=proposed_change,
            rationale=rationale,
            context=context or {},
            impact_analysis=impact,
            expires_at=datetime.now() + self.validation_timeout
        )
        
        self.requests[request_id] = request
        self.stats["total_requests"] += 1
        self.stats["pending"] += 1
        
        # Auto-approuver si risque faible et autorisé
        if (self.auto_approve_low_risk and 
            risk_level == RiskLevel.LOW and 
            not require_validation):
            
            self._auto_approve(request)
        
        # Sauvegarder
        self._save_state()
        
        return request_id
    
    def _assess_risk(
        self,
        validation_type: ValidationType,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> RiskLevel:
        """Évalue le niveau de risque"""
        
        risk_score = 0
        
        # Risque par type
        type_risks = {
            ValidationType.ADAPTATION: 2,
            ValidationType.KNOWLEDGE: 1,
            ValidationType.CORRECTION: 1,
            ValidationType.SAFETY: 3,
            ValidationType.PERMISSION: 2
        }
        risk_score += type_risks.get(validation_type, 1)
        
        # Risque par ampleur du changement
        if "scope" in proposed_change:
            scope = proposed_change["scope"]
            if scope == "global":
                risk_score += 2
            elif scope == "module":
                risk_score += 1
        
        # Risque par impact sur comportement
        if "behavior_change" in proposed_change:
            if proposed_change["behavior_change"] == "significant":
                risk_score += 2
            elif proposed_change["behavior_change"] == "moderate":
                risk_score += 1
        
        # Risque par confiance
        if "confidence" in proposed_change:
            confidence = proposed_change["confidence"]
            if confidence < 0.5:
                risk_score += 2
            elif confidence < 0.7:
                risk_score += 1
        
        # Mapper score à niveau
        if risk_score <= 2:
            return RiskLevel.LOW
        elif risk_score <= 4:
            return RiskLevel.MEDIUM
        elif risk_score <= 6:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _check_safety(
        self,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Vérifie les garde-fous de sécurité"""
        
        for guardrail in self.guardrails.values():
            if not guardrail.enabled:
                continue
            
            # Exécuter vérification
            check_result = self._execute_guardrail_check(
                guardrail,
                proposed_change,
                context
            )
            
            if not check_result["passed"]:
                guardrail.times_triggered += 1
                return {
                    "safe": False,
                    "reason": f"{guardrail.name}: {check_result['reason']}",
                    "guardrail_id": guardrail.rule_id
                }
        
        return {"safe": True}
    
    def _execute_guardrail_check(
        self,
        guardrail: SafetyGuardrail,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Exécute une vérification de garde-fou"""
        
        # Vérifications prédéfinies
        if guardrail.check_function == "check_data_access":
            # Vérifier qu'on n'accède pas à des données sensibles
            if "data_access" in proposed_change:
                access = proposed_change["data_access"]
                if any(s in access for s in ["password", "secret", "token", "key"]):
                    return {
                        "passed": False,
                        "reason": "Tentative d'accès à données sensibles"
                    }
        
        elif guardrail.check_function == "check_system_modification":
            # Vérifier qu'on ne modifie pas le système
            if "system_modification" in proposed_change:
                if proposed_change["system_modification"]:
                    return {
                        "passed": False,
                        "reason": "Modification système non autorisée"
                    }
        
        elif guardrail.check_function == "check_external_access":
            # Vérifier qu'on n'accède pas à l'extérieur sans permission
            if "external_access" in proposed_change:
                if proposed_change["external_access"] and not context.get("external_allowed"):
                    return {
                        "passed": False,
                        "reason": "Accès externe non autorisé"
                    }
        
        elif guardrail.check_function == "check_code_execution":
            # Vérifier exécution de code
            if "executes_code" in proposed_change:
                if proposed_change["executes_code"] and not context.get("code_execution_allowed"):
                    return {
                        "passed": False,
                        "reason": "Exécution de code non autorisée"
                    }
        
        return {"passed": True}
    
    def _analyze_impact(
        self,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyse l'impact du changement proposé"""
        
        impact = {
            "affected_components": [],
            "user_facing": False,
            "reversible": True,
            "performance_impact": "none",
            "data_impact": "none"
        }
        
        # Analyser composants affectés
        if "scope" in proposed_change:
            scope = proposed_change["scope"]
            if scope == "global":
                impact["affected_components"] = ["all"]
            elif "components" in proposed_change:
                impact["affected_components"] = proposed_change["components"]
        
        # Analyser si user-facing
        if "behavior_change" in proposed_change:
            impact["user_facing"] = True
        
        # Analyser réversibilité
        if "irreversible" in proposed_change:
            impact["reversible"] = not proposed_change["irreversible"]
        
        # Analyser impact performance
        if "performance_impact" in proposed_change:
            impact["performance_impact"] = proposed_change["performance_impact"]
        
        # Analyser impact données
        if "data_modification" in proposed_change:
            if proposed_change["data_modification"]:
                impact["data_impact"] = "modifies_data"
        
        return impact
    
    def _auto_approve(self, request: ValidationRequest) -> None:
        """Auto-approuve une requête à faible risque"""
        
        request.status = ValidationStatus.APPROVED
        request.decided_by = "system"
        request.decided_at = datetime.now()
        request.decision_reason = "Auto-approved (low risk)"
        
        self.stats["pending"] -= 1
        self.stats["approved"] += 1
        self.stats["auto_approved"] += 1
        
        # Enregistrer décision
        self._record_decision(request)
    
    def approve_request(
        self,
        request_id: str,
        decided_by: str = "user",
        reason: Optional[str] = None
    ) -> bool:
        """Approuve une requête"""
        
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        
        if request.status != ValidationStatus.PENDING:
            return False
        
        request.status = ValidationStatus.APPROVED
        request.decided_by = decided_by
        request.decided_at = datetime.now()
        request.decision_reason = reason or "Approved by user"
        
        self.stats["pending"] -= 1
        self.stats["approved"] += 1
        self.stats["manual_approvals"] += 1
        
        # Enregistrer décision
        self._record_decision(request)
        
        # Sauvegarder
        self._save_state()
        
        return True
    
    def reject_request(
        self,
        request_id: str,
        decided_by: str = "user",
        reason: Optional[str] = None
    ) -> bool:
        """Rejette une requête"""
        
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        
        if request.status != ValidationStatus.PENDING:
            return False
        
        request.status = ValidationStatus.REJECTED
        request.decided_by = decided_by
        request.decided_at = datetime.now()
        request.decision_reason = reason or "Rejected by user"
        
        self.stats["pending"] -= 1
        self.stats["rejected"] += 1
        
        # Enregistrer décision
        self._record_decision(request)
        
        # Sauvegarder
        self._save_state()
        
        return True
    
    def request_revision(
        self,
        request_id: str,
        feedback: str,
        decided_by: str = "user"
    ) -> bool:
        """Demande une révision"""
        
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        
        request.status = ValidationStatus.NEEDS_REVIEW
        request.revisions.append({
            "timestamp": datetime.now().isoformat(),
            "decided_by": decided_by,
            "feedback": feedback
        })
        
        # Sauvegarder
        self._save_state()
        
        return True
    
    def _record_decision(self, request: ValidationRequest) -> None:
        """Enregistre une décision"""
        
        self.decision_history.append({
            "request_id": request.id,
            "validation_type": request.validation_type.value,
            "risk_level": request.risk_level.value,
            "title": request.title,
            "status": request.status.value,
            "decided_by": request.decided_by,
            "decided_at": request.decided_at.isoformat() if request.decided_at else None,
            "reason": request.decision_reason
        })
        
        # Limiter historique
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
    
    def get_pending_requests(
        self,
        validation_type: Optional[ValidationType] = None,
        min_risk_level: Optional[RiskLevel] = None
    ) -> List[ValidationRequest]:
        """Retourne les requêtes en attente"""
        
        # Expirer les anciennes requêtes
        self._expire_old_requests()
        
        pending = [
            req for req in self.requests.values()
            if req.status == ValidationStatus.PENDING
        ]
        
        # Filtrer par type
        if validation_type:
            pending = [req for req in pending if req.validation_type == validation_type]
        
        # Filtrer par niveau de risque
        if min_risk_level:
            risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            min_index = risk_order.index(min_risk_level)
            pending = [
                req for req in pending
                if risk_order.index(req.risk_level) >= min_index
            ]
        
        # Trier par risque (plus haut en premier) puis date
        pending.sort(
            key=lambda r: (
                [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW].index(r.risk_level),
                r.created_at
            )
        )
        
        return pending
    
    def _expire_old_requests(self) -> None:
        """Expire les requêtes anciennes"""
        
        now = datetime.now()
        expired_count = 0
        
        for request in self.requests.values():
            if (request.status == ValidationStatus.PENDING and
                request.expires_at and
                now > request.expires_at):
                
                request.status = ValidationStatus.EXPIRED
                self.stats["pending"] -= 1
                self.stats["expired"] += 1
                expired_count += 1
        
        if expired_count > 0:
            self._save_state()
    
    def add_guardrail(
        self,
        name: str,
        description: str,
        check_function: str,
        risk_level: RiskLevel = RiskLevel.HIGH
    ) -> str:
        """Ajoute un garde-fou"""
        
        guardrail_id = f"gr_{len(self.guardrails)}"
        
        guardrail = SafetyGuardrail(
            rule_id=guardrail_id,
            name=name,
            description=description,
            check_function=check_function,
            risk_level=risk_level
        )
        
        self.guardrails[guardrail_id] = guardrail
        self._save_state()
        
        return guardrail_id
    
    def _initialize_guardrails(self) -> None:
        """Initialise les garde-fous par défaut"""
        
        self.add_guardrail(
            name="Data Access Protection",
            description="Empêche l'accès à des données sensibles",
            check_function="check_data_access",
            risk_level=RiskLevel.CRITICAL
        )
        
        self.add_guardrail(
            name="System Modification Protection",
            description="Empêche les modifications système non autorisées",
            check_function="check_system_modification",
            risk_level=RiskLevel.HIGH
        )
        
        self.add_guardrail(
            name="External Access Control",
            description="Contrôle les accès externes",
            check_function="check_external_access",
            risk_level=RiskLevel.HIGH
        )
        
        self.add_guardrail(
            name="Code Execution Control",
            description="Contrôle l'exécution de code",
            check_function="check_code_execution",
            risk_level=RiskLevel.MEDIUM
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        
        return {
            **self.stats,
            "pending_requests": self.stats["pending"],
            "approval_rate": self.stats["approved"] / max(self.stats["total_requests"], 1),
            "auto_approval_rate": self.stats["auto_approved"] / max(self.stats["approved"], 1) if self.stats["approved"] > 0 else 0,
            "active_guardrails": len([g for g in self.guardrails.values() if g.enabled]),
            "total_guardrails": len(self.guardrails)
        }
    
    def export_audit_trail(self, output_file: str) -> None:
        """Exporte le trail d'audit"""
        data = {
            "decision_history": self.decision_history,
            "statistics": self.get_statistics(),
            "guardrails": {
                gid: {
                    "name": g.name,
                    "description": g.description,
                    "times_triggered": g.times_triggered,
                    "enabled": g.enabled
                }
                for gid, g in self.guardrails.items()
            },
            "export_date": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_state(self) -> None:
        """Sauvegarde l'état"""
        
        # Sauvegarder requêtes
        requests_file = self.storage_path / "requests.json"
        requests_data = {
            req_id: {
                "validation_type": req.validation_type.value,
                "risk_level": req.risk_level.value,
                "title": req.title,
                "description": req.description,
                "proposed_change": req.proposed_change,
                "rationale": req.rationale,
                "context": req.context,
                "impact_analysis": req.impact_analysis,
                "status": req.status.value,
                "created_at": req.created_at.isoformat(),
                "expires_at": req.expires_at.isoformat() if req.expires_at else None,
                "decided_by": req.decided_by,
                "decided_at": req.decided_at.isoformat() if req.decided_at else None,
                "decision_reason": req.decision_reason,
                "revisions": req.revisions
            }
            for req_id, req in self.requests.items()
        }
        
        with open(requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder garde-fous
        guardrails_file = self.storage_path / "guardrails.json"
        guardrails_data = {
            gid: {
                "name": g.name,
                "description": g.description,
                "check_function": g.check_function,
                "risk_level": g.risk_level.value,
                "enabled": g.enabled,
                "times_triggered": g.times_triggered
            }
            for gid, g in self.guardrails.items()
        }
        
        with open(guardrails_file, 'w', encoding='utf-8') as f:
            json.dump(guardrails_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder historique
        history_file = self.storage_path / "decision_history.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.decision_history, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder stats
        stats_file = self.storage_path / "stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def _load_state(self) -> None:
        """Charge l'état"""
        
        try:
            # Charger requêtes
            requests_file = self.storage_path / "requests.json"
            if requests_file.exists():
                with open(requests_file, 'r', encoding='utf-8') as f:
                    requests_data = json.load(f)
                
                for req_id, req_data in requests_data.items():
                    req = ValidationRequest(
                        id=req_id,
                        validation_type=ValidationType(req_data["validation_type"]),
                        risk_level=RiskLevel(req_data["risk_level"]),
                        title=req_data["title"],
                        description=req_data["description"],
                        proposed_change=req_data["proposed_change"],
                        rationale=req_data["rationale"],
                        context=req_data.get("context", {}),
                        impact_analysis=req_data.get("impact_analysis", {}),
                        status=ValidationStatus(req_data["status"]),
                        created_at=datetime.fromisoformat(req_data["created_at"]),
                        expires_at=datetime.fromisoformat(req_data["expires_at"]) if req_data.get("expires_at") else None,
                        decided_by=req_data.get("decided_by"),
                        decided_at=datetime.fromisoformat(req_data["decided_at"]) if req_data.get("decided_at") else None,
                        decision_reason=req_data.get("decision_reason"),
                        revisions=req_data.get("revisions", [])
                    )
                    self.requests[req_id] = req
            
            # Charger garde-fous (ne pas écraser les défauts)
            guardrails_file = self.storage_path / "guardrails.json"
            if guardrails_file.exists():
                with open(guardrails_file, 'r', encoding='utf-8') as f:
                    guardrails_data = json.load(f)
                
                for gid, gdata in guardrails_data.items():
                    # Mettre à jour si existe, sinon créer
                    if gid in self.guardrails:
                        self.guardrails[gid].enabled = gdata.get("enabled", True)
                        self.guardrails[gid].times_triggered = gdata.get("times_triggered", 0)
            
            # Charger historique
            history_file = self.storage_path / "decision_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.decision_history = json.load(f)
            
            # Charger stats
            stats_file = self.storage_path / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.stats.update(json.load(f))
        
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    system = ValidationSystem()
    
    # Soumettre requête
    try:
        req_id = system.submit_validation_request(
            validation_type=ValidationType.ADAPTATION,
            title="Ajuster niveau de détail",
            description="Augmenter le niveau de détail pour utilisateur débutant",
            proposed_change={
                "scope": "session",
                "behavior_change": "moderate",
                "confidence": 0.8,
                "detail_level": "detailed"
            },
            rationale="Utilisateur a demandé plus d'explications 3 fois"
        )
        print(f"Requête soumise: {req_id}")
    except ValueError as e:
        print(f"Erreur: {e}")
    
    # Récupérer requêtes en attente
    pending = system.get_pending_requests()
    print(f"Requêtes en attente: {len(pending)}")
    
    # Statistiques
    stats = system.get_statistics()
    print(json.dumps(stats, indent=2))
