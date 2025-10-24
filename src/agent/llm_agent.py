"""
HOPPER - Agent LLM Avancé
Architecture agentique avec planification, mémoire et orchestration d'outils
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
from loguru import logger
from enum import Enum


class TaskStatus(Enum):
    """Statut d'une tâche"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ToolCategory(Enum):
    """Catégories d'outils disponibles"""
    SEARCH = "search"
    CODE_EXECUTION = "code_execution"
    FILE_ANALYSIS = "file_analysis"
    SYSTEM_CONTROL = "system_control"
    KNOWLEDGE_BASE = "knowledge_base"
    COMMUNICATION = "communication"
    COMPUTATION = "computation"


@dataclass
class Task:
    """Tâche atomique dans un plan d'action"""
    id: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


@dataclass
class Plan:
    """Plan d'action pour accomplir un objectif"""
    id: str
    objective: str
    tasks: List[Task]
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"


@dataclass
class Memory:
    """Mémoire contextuelle de l'agent"""
    short_term: List[Dict[str, Any]] = field(default_factory=list)  # Dernières interactions
    long_term: Dict[str, Any] = field(default_factory=dict)  # Connaissances persistantes
    working_memory: Dict[str, Any] = field(default_factory=dict)  # État actuel de travail
    episodic: List[Dict[str, Any]] = field(default_factory=list)  # Épisodes passés
    
    def add_to_short_term(self, item: Dict[str, Any], max_size: int = 10):
        """Ajoute un élément à la mémoire court terme"""
        self.short_term.append(item)
        if len(self.short_term) > max_size:
            # Transférer l'élément le plus ancien vers mémoire épisodique
            oldest = self.short_term.pop(0)
            self.episodic.append(oldest)
    
    def store_long_term(self, key: str, value: Any):
        """Stocke une information en mémoire long terme"""
        self.long_term[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
    
    def recall(self, query: str) -> List[Dict[str, Any]]:
        """Rappelle des informations pertinentes"""
        relevant = []
        
        # Chercher dans mémoire court terme
        for item in self.short_term:
            if query.lower() in str(item).lower():
                relevant.append({"source": "short_term", "data": item})
        
        # Chercher dans mémoire long terme
        for key, data in self.long_term.items():
            if query.lower() in key.lower() or query.lower() in str(data["value"]).lower():
                relevant.append({"source": "long_term", "key": key, "data": data})
        
        return relevant


@dataclass
class Tool:
    """Outil utilisable par l'agent"""
    name: str
    category: ToolCategory
    description: str
    function: Callable
    parameters_schema: Dict[str, Any]
    examples: List[str] = field(default_factory=list)


class LLMAgent:
    """
    Agent LLM avancé avec capacités de planification, mémoire et orchestration
    
    Architecture:
    1. Planning: Décompose objectifs complexes en sous-tâches
    2. Memory: Maintient contexte et apprentissage
    3. Tool Use: Invoque outils spécialisés
    4. Reflection: Auto-évalue ses actions
    """
    
    def __init__(
        self,
        llm_endpoint: str = "http://localhost:5001",
        orchestrator_endpoint: str = "http://localhost:5050"
    ):
        self.llm_endpoint = llm_endpoint
        self.orchestrator_endpoint = orchestrator_endpoint
        self.memory = Memory()
        self.tools: Dict[str, Tool] = {}
        self.active_plans: List[Plan] = []
        self.reflection_enabled = True
        
        # Initialiser les outils de base
        self._register_default_tools()
        
        logger.info("Agent LLM initialisé avec capacités avancées")
    
    def _register_default_tools(self):
        """Enregistre les outils par défaut"""
        
        # Outil de recherche
        self.register_tool(Tool(
            name="search_knowledge",
            category=ToolCategory.KNOWLEDGE_BASE,
            description="Recherche dans la base de connaissances Neo4j",
            function=self._search_knowledge,
            parameters_schema={
                "query": {"type": "string", "required": True},
                "limit": {"type": "integer", "default": 5}
            },
            examples=[
                "Rechercher des informations sur Python",
                "Trouver des documents sur l'IA"
            ]
        ))
        
        # Outil d'exécution de code
        self.register_tool(Tool(
            name="execute_code",
            category=ToolCategory.CODE_EXECUTION,
            description="Exécute du code Python dans un environnement sécurisé",
            function=self._execute_code,
            parameters_schema={
                "code": {"type": "string", "required": True},
                "language": {"type": "string", "default": "python"}
            },
            examples=[
                "Calculer la somme de 1 à 100",
                "Analyser un fichier CSV"
            ]
        ))
        
        # Outil d'analyse de fichiers
        self.register_tool(Tool(
            name="analyze_file",
            category=ToolCategory.FILE_ANALYSIS,
            description="Analyse le contenu d'un fichier",
            function=self._analyze_file,
            parameters_schema={
                "file_path": {"type": "string", "required": True},
                "analysis_type": {"type": "string", "default": "auto"}
            },
            examples=[
                "Analyser structure.json",
                "Lire le contenu de README.md"
            ]
        ))
        
        # Outil de contrôle système
        self.register_tool(Tool(
            name="system_action",
            category=ToolCategory.SYSTEM_CONTROL,
            description="Exécute une action système (ouvrir app, fichier, etc.)",
            function=self._system_action,
            parameters_schema={
                "action": {"type": "string", "required": True},
                "target": {"type": "string", "required": True}
            },
            examples=[
                "Ouvrir Safari",
                "Lire le fichier ~/Documents/note.txt"
            ]
        ))
        
        # Outil de calcul
        self.register_tool(Tool(
            name="compute",
            category=ToolCategory.COMPUTATION,
            description="Effectue des calculs mathématiques complexes",
            function=self._compute,
            parameters_schema={
                "expression": {"type": "string", "required": True}
            },
            examples=[
                "Calculer sqrt(144) + 5^2",
                "Résoudre l'équation 2x + 5 = 15"
            ]
        ))
    
    def register_tool(self, tool: Tool):
        """Enregistre un nouvel outil"""
        self.tools[tool.name] = tool
        logger.info(f"Outil enregistré: {tool.name} ({tool.category.value})")
    
    async def process_request(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Traite une requête utilisateur avec architecture agentique complète
        
        Flux:
        1. Analyse de l'intention
        2. Création d'un plan d'action
        3. Exécution séquentielle des tâches
        4. Synthèse des résultats
        5. Réflexion et apprentissage
        """
        
        logger.info(f"Traitement requête: {user_input[:100]}...")
        
        # Ajouter à la mémoire court terme
        self.memory.add_to_short_term({
            "type": "user_input",
            "content": user_input,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        })
        
        try:
            # 1. Analyser l'intention et créer un plan
            plan = await self._create_plan(user_input, context)
            self.active_plans.append(plan)
            
            logger.info(f"Plan créé avec {len(plan.tasks)} tâches")
            
            # 2. Exécuter le plan
            results = await self._execute_plan(plan)
            
            # 3. Synthétiser la réponse
            response = await self._synthesize_response(plan, results)
            
            # 4. Réflexion (si activée)
            if self.reflection_enabled:
                reflection = await self._reflect_on_execution(plan, results)
                response["reflection"] = reflection
            
            # Ajouter à la mémoire
            self.memory.add_to_short_term({
                "type": "agent_response",
                "plan_id": plan.id,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": await self._fallback_response(user_input)
            }
    
    async def _create_plan(self, objective: str, context: Optional[Dict] = None) -> Plan:
        """
        Crée un plan d'action pour atteindre l'objectif
        
        Utilise le LLM pour:
        1. Décomposer l'objectif en sous-tâches
        2. Identifier les outils nécessaires
        3. Établir les dépendances entre tâches
        """
        
        # Rappeler le contexte pertinent de la mémoire
        memory_context = self.memory.recall(objective)
        
        # Construire le prompt pour le LLM
        prompt = self._build_planning_prompt(objective, context, memory_context)
        
        # Demander au LLM de créer le plan
        llm_response = await self._call_llm(prompt, mode="planning")
        
        # Parser la réponse du LLM en tâches structurées
        tasks = self._parse_plan(llm_response)
        
        plan = Plan(
            id=f"plan_{datetime.now().timestamp()}",
            objective=objective,
            tasks=tasks,
            context=context or {}
        )
        
        return plan
    
    def _build_planning_prompt(
        self,
        objective: str,
        context: Optional[Dict],
        memory_context: List[Dict]
    ) -> str:
        """Construit le prompt pour la phase de planification"""
        
        # Liste des outils disponibles
        tools_description = "\n".join([
            f"- {tool.name}: {tool.description} (Catégorie: {tool.category.value})"
            for tool in self.tools.values()
        ])
        
        prompt = f"""Tu es HOPPER, un agent IA avancé capable de planifier et d'exécuter des tâches complexes.

OBJECTIF: {objective}

CONTEXTE ACTUEL:
{json.dumps(context, indent=2) if context else "Aucun contexte spécifique"}

MÉMOIRE PERTINENTE:
{json.dumps(memory_context, indent=2) if memory_context else "Aucun souvenir pertinent"}

OUTILS DISPONIBLES:
{tools_description}

INSTRUCTIONS:
1. Analyse l'objectif et décompose-le en tâches atomiques
2. Pour chaque tâche, identifie l'outil le plus approprié
3. Établis les dépendances entre tâches (quelle tâche doit être complétée avant une autre)
4. Crée un plan d'action structuré

RÉPONDS AU FORMAT JSON:
{{
  "analysis": "Ton analyse de l'objectif",
  "strategy": "Ta stratégie globale",
  "tasks": [
    {{
      "id": "task_1",
      "description": "Description de la tâche",
      "tool": "nom_outil",
      "parameters": {{}},
      "dependencies": []
    }}
  ]
}}
"""
        return prompt
    
    def _parse_plan(self, llm_response: str) -> List[Task]:
        """Parse la réponse du LLM en liste de tâches"""
        try:
            data = json.loads(llm_response)
            tasks = []
            
            for task_data in data.get("tasks", []):
                task = Task(
                    id=task_data["id"],
                    description=task_data["description"],
                    tool=task_data["tool"],
                    parameters=task_data.get("parameters", {}),
                    dependencies=task_data.get("dependencies", [])
                )
                tasks.append(task)
            
            return tasks
            
        except json.JSONDecodeError:
            logger.warning("Réponse LLM non-JSON, parsing manuel")
            # Fallback: créer une tâche unique
            return [Task(
                id="task_fallback",
                description="Tâche simple",
                tool="search_knowledge",
                parameters={"query": llm_response[:100]}
            )]
    
    async def _execute_plan(self, plan: Plan) -> Dict[str, Any]:
        """
        Exécute un plan en respectant les dépendances
        
        Utilise un graphe de dépendances pour exécuter les tâches
        dans le bon ordre, en parallélisant quand possible
        """
        
        results = {}
        completed_tasks = set()
        
        while len(completed_tasks) < len(plan.tasks):
            # Trouver les tâches prêtes à être exécutées
            ready_tasks = [
                task for task in plan.tasks
                if task.status == TaskStatus.PENDING
                and all(dep in completed_tasks for dep in task.dependencies)
            ]
            
            if not ready_tasks:
                # Vérifier si il reste des tâches bloquées
                pending = [t for t in plan.tasks if t.status == TaskStatus.PENDING]
                if pending:
                    logger.error("Deadlock détecté dans le plan")
                    break
                else:
                    break
            
            # Exécuter les tâches prêtes
            for task in ready_tasks:
                task.status = TaskStatus.IN_PROGRESS
                
                try:
                    result = await self._execute_task(task, results)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now().isoformat()
                    completed_tasks.add(task.id)
                    results[task.id] = result
                    
                    logger.success(f"Tâche {task.id} complétée")
                    
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    logger.error(f"Tâche {task.id} échouée: {e}")
                    
                    # Bloquer les tâches dépendantes
                    for t in plan.tasks:
                        if task.id in t.dependencies:
                            t.status = TaskStatus.BLOCKED
        
        plan.status = "completed"
        return results
    
    async def _execute_task(self, task: Task, previous_results: Dict) -> Any:
        """Exécute une tâche unique en utilisant l'outil approprié"""
        
        tool = self.tools.get(task.tool)
        if not tool:
            raise ValueError(f"Outil inconnu: {task.tool}")
        
        # Résoudre les références aux résultats précédents
        params = self._resolve_parameters(task.parameters, previous_results)
        
        # Stocker dans la working memory
        self.memory.working_memory[task.id] = {
            "status": "executing",
            "tool": task.tool,
            "params": params
        }
        
        # Exécuter l'outil
        result = await tool.function(**params)
        
        # Mettre à jour la working memory
        self.memory.working_memory[task.id]["status"] = "completed"
        self.memory.working_memory[task.id]["result"] = result
        
        return result
    
    def _resolve_parameters(self, params: Dict, previous_results: Dict) -> Dict:
        """Résout les références aux résultats de tâches précédentes"""
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$task_"):
                # Référence à un résultat précédent
                task_id = value[1:]  # Enlever le $
                if task_id in previous_results:
                    resolved[key] = previous_results[task_id]
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    async def _synthesize_response(self, plan: Plan, results: Dict) -> Dict[str, Any]:
        """Synthétise les résultats en une réponse cohérente"""
        
        # Compter les succès/échecs
        completed = len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in plan.tasks if t.status == TaskStatus.FAILED])
        
        # Demander au LLM de synthétiser
        synthesis_prompt = f"""
Tu as exécuté un plan d'action pour atteindre cet objectif: {plan.objective}

RÉSULTATS DES TÂCHES:
{json.dumps(results, indent=2)}

STATISTIQUES:
- Tâches complétées: {completed}/{len(plan.tasks)}
- Tâches échouées: {failed}

Synthétise ces résultats en une réponse claire et actionnable pour l'utilisateur.
"""
        
        synthesis = await self._call_llm(synthesis_prompt, mode="synthesis")
        
        return {
            "success": failed == 0,
            "objective": plan.objective,
            "tasks_completed": completed,
            "tasks_total": len(plan.tasks),
            "response": synthesis,
            "details": results
        }
    
    async def _reflect_on_execution(self, plan: Plan, results: Dict) -> Dict[str, Any]:
        """
        Réflexion sur l'exécution pour apprentissage
        
        Questions:
        - Le plan était-il optimal?
        - Y a-t-il eu des erreurs évitables?
        - Quels apprentissages tirer?
        """
        
        reflection_prompt = f"""
En tant qu'agent autoréflexif, analyse ton exécution:

PLAN INITIAL: {plan.objective}
TÂCHES: {len(plan.tasks)}
RÉSULTATS: {json.dumps(results, indent=2)}

QUESTIONS:
1. Le plan était-il optimal ou aurais-tu pu faire différemment?
2. Y a-t-il eu des inefficacités ou erreurs évitables?
3. Quels apprentissages tirer pour les prochaines fois?
4. Quelles connaissances stocker en mémoire long terme?

Réponds de manière structurée.
"""
        
        reflection = await self._call_llm(reflection_prompt, mode="reflection")
        
        # Extraire les apprentissages à stocker
        learnings = self._extract_learnings(reflection)
        for learning in learnings:
            self.memory.store_long_term(learning["key"], learning["value"])
        
        return {
            "reflection": reflection,
            "learnings_stored": len(learnings)
        }
    
    def _extract_learnings(self, reflection: str) -> List[Dict]:
        """Extrait les apprentissages structurés de la réflexion"""
        # Simplified extraction
        return []
    
    async def _call_llm(self, prompt: str, mode: str = "general") -> str:
        """Appelle le LLM avec le prompt"""
        # TODO: Implémenter l'appel réel au LLM
        logger.info(f"Appel LLM (mode: {mode})")
        return '{"analysis": "...", "strategy": "...", "tasks": []}'
    
    async def _fallback_response(self, user_input: str) -> str:
        """Réponse de secours en cas d'erreur"""
        return f"Je rencontre des difficultés à traiter votre demande: {user_input[:100]}"
    
    # Implémentations des outils de base
    
    async def _search_knowledge(self, query: str, limit: int = 5) -> Dict:
        """Recherche dans la base de connaissances"""
        logger.info(f"Recherche: {query}")
        return {"results": [], "count": 0}
    
    async def _execute_code(self, code: str, language: str = "python") -> Dict:
        """Exécute du code"""
        logger.info(f"Exécution code ({language})")
        return {"output": "", "success": True}
    
    async def _analyze_file(self, file_path: str, analysis_type: str = "auto") -> Dict:
        """Analyse un fichier"""
        logger.info(f"Analyse: {file_path}")
        return {"content": "", "metadata": {}}
    
    async def _system_action(self, action: str, target: str) -> Dict:
        """Exécute une action système"""
        logger.info(f"Action système: {action} {target}")
        return {"success": True}
    
    async def _compute(self, expression: str) -> Dict:
        """Effectue un calcul"""
        logger.info(f"Calcul: {expression}")
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return {"result": result, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}
