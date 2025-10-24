"""
ReAct Agent - Reasoning and Acting in Language Models
Implements the Thought→Action→Observation cycle for autonomous task execution.

Architecture:
1. Thought: Agent raisonne sur la tâche
2. Action: Agent choisit et exécute un outil
3. Observation: Agent observe le résultat
4. Répétition jusqu'à résolution

References:
- ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022)
- Toolformer: Language Models Can Teach Themselves to Use Tools (Schick et al., 2023)
"""

import re
import asyncio
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class ActionStatus(Enum):
    """Status d'exécution d'une action."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class Action:
    """Représente une action à exécuter."""
    tool_name: str
    arguments: Dict[str, Any]
    reasoning: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def __str__(self) -> str:
        args_str = ", ".join(f"{k}={v}" for k, v in self.arguments.items())
        return f"{self.tool_name}({args_str})"


@dataclass
class Observation:
    """Résultat d'une action."""
    action: Action
    result: Any
    status: ActionStatus
    error: Optional[str] = None
    duration: float = 0.0
    
    def __str__(self) -> str:
        if self.status == ActionStatus.SUCCESS:
            return f"✅ {self.action.tool_name}: {self.result}"
        else:
            return f"❌ {self.action.tool_name}: {self.error}"


@dataclass
class ReActStep:
    """Une étape complète du cycle ReAct."""
    thought: str
    action: Optional[Action]
    observation: Optional[Observation]
    step_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "thought": self.thought,
            "action": str(self.action) if self.action else None,
            "observation": str(self.observation) if self.observation else None,
            "status": self.observation.status.value if self.observation else "pending"
        }


class ToolRegistry:
    """
    Registre des outils disponibles pour l'agent.
    Permet l'ajout/suppression dynamique d'outils.
    """
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_descriptions: Dict[str, str] = {}
        self.tool_schemas: Dict[str, Dict] = {}
    
    def register(self, name: str, func: Callable, description: str, 
                 schema: Dict[str, Any]) -> None:
        """
        Enregistre un nouvel outil.
        
        Args:
            name: Nom de l'outil
            func: Fonction à exécuter
            description: Description pour le LLM
            schema: Schéma des arguments (JSON Schema style)
        """
        self.tools[name] = func
        self.tool_descriptions[name] = description
        self.tool_schemas[name] = schema
    
    def unregister(self, name: str) -> bool:
        """Désenregistre un outil."""
        if name in self.tools:
            del self.tools[name]
            del self.tool_descriptions[name]
            del self.tool_schemas[name]
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Récupère un outil par son nom."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """Liste tous les outils disponibles."""
        return list(self.tools.keys())
    
    def get_tool_prompt(self) -> str:
        """
        Génère un prompt décrivant tous les outils disponibles.
        Format pour le LLM.
        """
        if not self.tools:
            return "No tools available."
        
        prompt = "Available tools:\n\n"
        for name, desc in self.tool_descriptions.items():
            schema = self.tool_schemas[name]
            params = ", ".join(f"{k}: {v['type']}" for k, v in schema.get("parameters", {}).items())
            prompt += f"• {name}({params})\n  {desc}\n\n"
        return prompt


class ReActAgent:
    """
    Agent ReAct implémentant le cycle Thought→Action→Observation.
    
    Features:
    - Parse LLM responses to extract thoughts and actions
    - Execute actions via tool registry
    - Handle multi-step reasoning
    - Track execution history
    - Timeout and max iterations protection
    """
    
    def __init__(self, llm_client: Optional[Any] = None, max_iterations: int = 10,
                 timeout: float = 30.0):
        """
        Args:
            llm_client: Client LLM pour générer thoughts/actions
            max_iterations: Nombre max d'itérations ReAct
            timeout: Timeout global en secondes
        """
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.tool_registry = ToolRegistry()
        self.history: List[ReActStep] = []
        
        # Statistiques
        self.stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "total_thoughts": 0,
            "average_duration": 0.0
        }
    
    def register_tool(self, name: str, func: Callable, description: str,
                     schema: Dict[str, Any]) -> None:
        """Enregistre un outil dans le registre."""
        self.tool_registry.register(name, func, description, schema)
    
    def parse_llm_response(self, response: str) -> tuple[str, Optional[Action]]:
        """
        Parse la réponse du LLM pour extraire Thought et Action.
        
        Format attendu:
        Thought: <reasoning>
        Action: tool_name(arg1="value1", arg2="value2")
        
        ou pour terminer:
        Thought: <reasoning>
        Answer: <final answer>
        
        Args:
            response: Réponse brute du LLM
            
        Returns:
            (thought, action) où action peut être None si réponse finale
        """
        thought = ""
        action = None
        
        # Extraire Thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=\n(?:Action|Answer):|$)', 
                                 response, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()
        
        # Extraire Action (si pas de Answer)
        if "Answer:" not in response:
            action_match = re.search(r'Action:\s*(\w+)\(([^)]*)\)', 
                                    response, re.IGNORECASE)
            if action_match:
                tool_name = action_match.group(1)
                args_str = action_match.group(2)
                
                # Parser les arguments
                arguments = self._parse_arguments(args_str)
                action = Action(
                    tool_name=tool_name,
                    arguments=arguments,
                    reasoning=thought
                )
        
        return thought, action
    
    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """
        Parse les arguments d'une action.
        Format: arg1="value1", arg2=123, arg3=true
        """
        arguments = {}
        if not args_str.strip():
            return arguments
        
        # Pattern pour capturer arg="value" ou arg=value (sans virgules)
        pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^,\s)]+))'
        matches = re.finditer(pattern, args_str)
        
        for match in matches:
            key = match.group(1)
            # Prendre la première valeur non-None parmi les groupes
            value = match.group(2) or match.group(3) or match.group(4)
            
            # Conversion de type
            if value and value.lower() == "true":
                value = True
            elif value and value.lower() == "false":
                value = False
            elif value and value.isdigit():
                value = int(value)
            
            arguments[key] = value
        
        return arguments
    
    async def execute_action(self, action: Action) -> Observation:
        """
        Exécute une action via le tool registry.
        
        Args:
            action: Action à exécuter
            
        Returns:
            Observation avec résultat ou erreur
        """
        start_time = time.time()
        
        # Récupérer l'outil
        tool = self.tool_registry.get_tool(action.tool_name)
        if not tool:
            return Observation(
                action=action,
                result=None,
                status=ActionStatus.FAILURE,
                error=f"Tool '{action.tool_name}' not found",
                duration=time.time() - start_time
            )
        
        # Exécuter l'outil
        try:
            # Support async et sync
            if asyncio.iscoroutinefunction(tool):
                result = await tool(**action.arguments)
            else:
                result = tool(**action.arguments)
            
            duration = time.time() - start_time
            
            # Mise à jour stats
            self.stats["total_actions"] += 1
            self.stats["successful_actions"] += 1
            self.stats["average_duration"] = (
                (self.stats["average_duration"] * (self.stats["total_actions"] - 1) + duration)
                / self.stats["total_actions"]
            )
            
            return Observation(
                action=action,
                result=result,
                status=ActionStatus.SUCCESS,
                duration=duration
            )
        
        except Exception as e:
            duration = time.time() - start_time
            self.stats["total_actions"] += 1
            self.stats["failed_actions"] += 1
            
            return Observation(
                action=action,
                result=None,
                status=ActionStatus.FAILURE,
                error=str(e),
                duration=duration
            )
    
    def format_prompt(self, task: str, step_history: List[ReActStep]) -> str:
        """
        Formate le prompt pour le LLM avec historique.
        
        Args:
            task: Tâche à accomplir
            step_history: Historique des étapes précédentes
            
        Returns:
            Prompt formaté pour le LLM
        """
        prompt = f"""You are an autonomous agent that can use tools to accomplish tasks.

Task: {task}

{self.tool_registry.get_tool_prompt()}

Use this format:
Thought: [your reasoning about what to do next]
Action: tool_name(arg1="value1", arg2="value2")

Or when you have the final answer:
Thought: [your reasoning]
Answer: [your final answer]

"""
        
        # Ajouter l'historique
        if step_history:
            prompt += "Previous steps:\n"
            for step in step_history:
                prompt += f"\nStep {step.step_number}:\n"
                prompt += f"Thought: {step.thought}\n"
                if step.action:
                    prompt += f"Action: {step.action}\n"
                if step.observation:
                    prompt += f"Observation: {step.observation}\n"
            prompt += "\nNow continue:\n"
        else:
            prompt += "Begin:\n"
        
        return prompt
    
    async def run(self, task: str) -> Dict[str, Any]:
        """
        Exécute le cycle ReAct complet pour une tâche.
        
        Args:
            task: Description de la tâche à accomplir
            
        Returns:
            Dict avec résultat final et métadonnées
        """
        start_time = time.time()
        self.history = []
        step_number = 0
        final_answer = None
        
        try:
            for iteration in range(self.max_iterations):
                step_number += 1
                
                # Timeout check
                if time.time() - start_time > self.timeout:
                    return {
                        "success": False,
                        "answer": None,
                        "error": f"Timeout after {self.timeout}s",
                        "steps": [step.to_dict() for step in self.history],
                        "stats": self.stats
                    }
                
                # 1. Générer Thought + Action via LLM
                prompt = self.format_prompt(task, self.history)
                
                if self.llm_client:
                    llm_response = await self._call_llm(prompt)
                else:
                    # Mode mock pour tests
                    llm_response = self._mock_llm_response(step_number)
                
                thought, action = self.parse_llm_response(llm_response)
                self.stats["total_thoughts"] += 1
                
                # 2. Check si réponse finale
                if "Answer:" in llm_response:
                    answer_match = re.search(r'Answer:\s*(.+)', llm_response, re.DOTALL)
                    if answer_match:
                        final_answer = answer_match.group(1).strip()
                        
                        # Enregistrer l'étape finale
                        final_step = ReActStep(
                            thought=thought,
                            action=None,
                            observation=None,
                            step_number=step_number
                        )
                        self.history.append(final_step)
                        
                        return {
                            "success": True,
                            "answer": final_answer,
                            "steps": [step.to_dict() for step in self.history],
                            "stats": self.stats,
                            "duration": time.time() - start_time
                        }
                
                # 3. Exécuter l'action
                if action:
                    observation = await self.execute_action(action)
                else:
                    observation = None
                
                # 4. Enregistrer l'étape
                step = ReActStep(
                    thought=thought,
                    action=action,
                    observation=observation,
                    step_number=step_number
                )
                self.history.append(step)
                
                # 5. Check si échec critique
                if observation and observation.status == ActionStatus.FAILURE:
                    # Continuer pour laisser l'agent réessayer ou trouver une alternative
                    pass
            
            # Max iterations atteintes
            return {
                "success": False,
                "answer": None,
                "error": f"Max iterations ({self.max_iterations}) reached",
                "steps": [step.to_dict() for step in self.history],
                "stats": self.stats,
                "duration": time.time() - start_time
            }
        
        except Exception as e:
            return {
                "success": False,
                "answer": None,
                "error": str(e),
                "steps": [step.to_dict() for step in self.history],
                "stats": self.stats,
                "duration": time.time() - start_time
            }
    
    async def _call_llm(self, prompt: str) -> str:
        """Appelle le LLM (à implémenter avec vrai client)."""
        # TODO: Intégrer avec le LLM réel
        raise NotImplementedError("LLM client not implemented yet")
    
    def _mock_llm_response(self, step: int) -> str:
        """Réponse mock pour tests sans LLM."""
        if step == 1:
            return """Thought: I need to search for information about the task.
Action: search(query="test query")"""
        elif step == 2:
            return """Thought: I found the information I needed.
Answer: This is the final answer based on the search results."""
        else:
            return """Thought: Task completed.
Answer: Done."""
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'exécution."""
        success_rate = (
            self.stats["successful_actions"] / self.stats["total_actions"] * 100
            if self.stats["total_actions"] > 0 else 0
        )
        
        return {
            **self.stats,
            "success_rate": f"{success_rate:.1f}%"
        }


# Test basique
async def test_react_agent():
    """Test de base du ReAct Agent."""
    print("="*60)
    print("Testing ReAct Agent")
    print("="*60)
    
    # Créer agent
    agent = ReActAgent(llm_client=None, max_iterations=5)
    
    # Enregistrer un outil simple
    def search(query: str) -> str:
        return f"Search results for: {query}"
    
    agent.register_tool(
        name="search",
        func=search,
        description="Search for information on the internet",
        schema={
            "parameters": {
                "query": {"type": "string", "description": "Search query"}
            }
        }
    )
    
    # Test 1: Parse LLM response
    print("\n📝 Test 1: Parse LLM response")
    response = 'Thought: I need to search.\nAction: search(query="Python programming")'
    thought, action = agent.parse_llm_response(response)
    print(f"  Thought: {thought}")
    print(f"  Action: {action}")
    
    # Test 2: Execute action
    print("\n⚡ Test 2: Execute action")
    if action:
        observation = await agent.execute_action(action)
        print(f"  {observation}")
    
    # Test 3: Run full cycle (mock mode)
    print("\n🔄 Test 3: Full ReAct cycle (mock mode)")
    result = await agent.run("Find information about Python")
    print(f"  Success: {result['success']}")
    print(f"  Answer: {result.get('answer', 'N/A')}")
    print(f"  Steps: {len(result['steps'])}")
    print(f"  Stats: {agent.get_stats()}")
    
    print("\n" + "="*60)
    print("✅ Tests completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_react_agent())
