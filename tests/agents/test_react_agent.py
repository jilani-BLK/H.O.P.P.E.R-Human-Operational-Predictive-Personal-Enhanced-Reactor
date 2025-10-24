"""
Tests unitaires pour le ReAct Agent.

Validations:
- Parsing des réponses LLM (Thought + Action)
- Exécution d'actions via tool registry
- Cycle complet Thought→Action→Observation
- Gestion des erreurs et timeouts
- Statistiques et success rate
"""

import pytest
import asyncio
from src.agents.react_agent import (
    ReActAgent,
    Action,
    Observation,
    ActionStatus,
    ReActStep,
    ToolRegistry
)


class TestToolRegistry:
    """Tests pour le registre d'outils."""
    
    def test_register_tool(self):
        """Doit enregistrer un outil."""
        registry = ToolRegistry()
        
        def test_tool(arg: str) -> str:
            return f"Result: {arg}"
        
        registry.register(
            name="test_tool",
            func=test_tool,
            description="A test tool",
            schema={"parameters": {"arg": {"type": "string"}}}
        )
        
        assert "test_tool" in registry.list_tools()
        assert registry.get_tool("test_tool") is not None
    
    def test_unregister_tool(self):
        """Doit désenregistrer un outil."""
        registry = ToolRegistry()
        
        def dummy():
            pass
        
        registry.register("dummy", dummy, "Dummy", {})
        assert registry.unregister("dummy") is True
        assert "dummy" not in registry.list_tools()
    
    def test_get_tool_prompt(self):
        """Doit générer un prompt décrivant les outils."""
        registry = ToolRegistry()
        
        registry.register(
            "search",
            lambda q: f"Results for {q}",
            "Search the internet",
            {"parameters": {"query": {"type": "string"}}}
        )
        
        prompt = registry.get_tool_prompt()
        assert "search" in prompt
        assert "Search the internet" in prompt
    
    def test_empty_registry(self):
        """Doit gérer un registre vide."""
        registry = ToolRegistry()
        assert registry.list_tools() == []
        assert registry.get_tool("nonexistent") is None


class TestReActParsing:
    """Tests pour le parsing des réponses LLM."""
    
    def test_parse_thought_and_action(self):
        """Doit parser Thought et Action."""
        agent = ReActAgent()
        
        response = """Thought: I need to search for information.
Action: search(query="Python programming")"""
        
        thought, action = agent.parse_llm_response(response)
        
        assert thought == "I need to search for information."
        assert action is not None
        assert action.tool_name == "search"
        assert action.arguments["query"] == "Python programming"
    
    def test_parse_thought_only(self):
        """Doit parser Thought sans Action (réponse finale)."""
        agent = ReActAgent()
        
        response = """Thought: I have found the answer.
Answer: The answer is 42."""
        
        thought, action = agent.parse_llm_response(response)
        
        assert "found the answer" in thought.lower()
        assert action is None
    
    def test_parse_arguments_string(self):
        """Doit parser des arguments string."""
        agent = ReActAgent()
        args_str = 'query="Python", limit="10"'
        
        arguments = agent._parse_arguments(args_str)
        
        assert arguments["query"] == "Python"
        # "10" est converti en int automatiquement
        assert arguments["limit"] == 10
    
    def test_parse_arguments_number(self):
        """Doit parser des arguments numériques."""
        agent = ReActAgent()
        args_str = 'count=5, timeout=30'
        
        arguments = agent._parse_arguments(args_str)
        
        assert arguments["count"] == 5
        assert arguments["timeout"] == 30
    
    def test_parse_arguments_boolean(self):
        """Doit parser des arguments booléens."""
        agent = ReActAgent()
        args_str = 'verbose=true, debug=false'
        
        arguments = agent._parse_arguments(args_str)
        
        assert arguments["verbose"] is True
        assert arguments["debug"] is False
    
    def test_parse_empty_arguments(self):
        """Doit gérer les arguments vides."""
        agent = ReActAgent()
        args_str = ''
        
        arguments = agent._parse_arguments(args_str)
        
        assert arguments == {}
    
    def test_parse_complex_action(self):
        """Doit parser une action complexe."""
        agent = ReActAgent()
        
        response = '''Thought: I'll send an email to the boss.
Action: send_email(to="boss@company.com", subject="Report", body="Here is the report")'''
        
        thought, action = agent.parse_llm_response(response)
        
        assert action.tool_name == "send_email"
        assert action.arguments["to"] == "boss@company.com"
        assert action.arguments["subject"] == "Report"
        assert action.arguments["body"] == "Here is the report"


class TestActionExecution:
    """Tests pour l'exécution d'actions."""
    
    @pytest.mark.asyncio
    async def test_execute_action_success(self):
        """Doit exécuter une action avec succès."""
        agent = ReActAgent()
        
        def test_tool(value: str) -> str:
            return f"Success: {value}"
        
        agent.register_tool(
            "test_tool",
            test_tool,
            "A test tool",
            {"parameters": {"value": {"type": "string"}}}
        )
        
        action = Action(
            tool_name="test_tool",
            arguments={"value": "hello"}
        )
        
        observation = await agent.execute_action(action)
        
        assert observation.status == ActionStatus.SUCCESS
        assert "Success: hello" in observation.result
    
    @pytest.mark.asyncio
    async def test_execute_action_tool_not_found(self):
        """Doit gérer une action avec outil inexistant."""
        agent = ReActAgent()
        
        action = Action(
            tool_name="nonexistent_tool",
            arguments={}
        )
        
        observation = await agent.execute_action(action)
        
        assert observation.status == ActionStatus.FAILURE
        assert "not found" in observation.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_action_tool_error(self):
        """Doit gérer une erreur d'exécution d'outil."""
        agent = ReActAgent()
        
        def failing_tool():
            raise ValueError("Tool failed")
        
        agent.register_tool(
            "failing_tool",
            failing_tool,
            "A failing tool",
            {"parameters": {}}
        )
        
        action = Action(tool_name="failing_tool", arguments={})
        observation = await agent.execute_action(action)
        
        assert observation.status == ActionStatus.FAILURE
        assert observation.error and "Tool failed" in observation.error
    
    @pytest.mark.asyncio
    async def test_execute_async_tool(self):
        """Doit supporter les outils async."""
        agent = ReActAgent()
        
        async def async_tool(value: str) -> str:
            await asyncio.sleep(0.01)
            return f"Async result: {value}"
        
        agent.register_tool(
            "async_tool",
            async_tool,
            "An async tool",
            {"parameters": {"value": {"type": "string"}}}
        )
        
        action = Action(tool_name="async_tool", arguments={"value": "test"})
        observation = await agent.execute_action(action)
        
        assert observation.status == ActionStatus.SUCCESS
        assert "Async result: test" in observation.result


class TestReActCycle:
    """Tests pour le cycle ReAct complet."""
    
    @pytest.mark.asyncio
    async def test_run_simple_task(self):
        """Doit exécuter une tâche simple (mode mock)."""
        agent = ReActAgent(llm_client=None, max_iterations=5)
        
        def search(query: str) -> str:
            return f"Results for: {query}"
        
        agent.register_tool(
            "search",
            search,
            "Search tool",
            {"parameters": {"query": {"type": "string"}}}
        )
        
        result = await agent.run("Find information about Python")
        
        assert result["success"] is True
        assert result["answer"] is not None
        assert len(result["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_run_max_iterations(self):
        """Doit s'arrêter après max_iterations."""
        agent = ReActAgent(llm_client=None, max_iterations=2)
        
        # Mock qui ne termine jamais
        agent._mock_llm_response = lambda step: """Thought: Continue.
Action: search(query="test")"""
        
        def search(query: str) -> str:
            return "Results"
        
        agent.register_tool("search", search, "Search", 
                          {"parameters": {"query": {"type": "string"}}})
        
        result = await agent.run("Infinite task")
        
        assert result["success"] is False
        assert "Max iterations" in result["error"]
    
    @pytest.mark.asyncio
    async def test_run_timeout(self):
        """Doit s'arrêter après timeout."""
        agent = ReActAgent(llm_client=None, timeout=0.1)
        
        async def slow_tool():
            await asyncio.sleep(0.5)
            return "Done"
        
        agent.register_tool("slow_tool", slow_tool, "Slow tool", {"parameters": {}})
        
        # Force l'utilisation du slow_tool
        agent._mock_llm_response = lambda step: """Thought: Use slow tool.
Action: slow_tool()"""
        
        result = await agent.run("Slow task")
        
        assert result["success"] is False
        assert "Timeout" in result["error"]
    
    @pytest.mark.asyncio
    async def test_run_with_history(self):
        """Doit tracker l'historique des étapes."""
        agent = ReActAgent(llm_client=None, max_iterations=5)
        
        def dummy():
            return "OK"
        
        agent.register_tool("dummy", dummy, "Dummy", {"parameters": {}})
        
        result = await agent.run("Test task")
        
        assert len(result["steps"]) > 0
        assert all("step" in step for step in result["steps"])
        assert all("thought" in step for step in result["steps"])


class TestStatistics:
    """Tests pour les statistiques."""
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Doit tracker les statistiques d'exécution."""
        agent = ReActAgent()
        
        def tool1():
            return "OK"
        
        agent.register_tool("tool1", tool1, "Tool 1", {"parameters": {}})
        
        # Exécuter quelques actions
        action = Action(tool_name="tool1", arguments={})
        await agent.execute_action(action)
        await agent.execute_action(action)
        
        stats = agent.get_stats()
        
        assert stats["total_actions"] == 2
        assert stats["successful_actions"] == 2
        assert stats["failed_actions"] == 0
        assert "100.0%" in stats["success_rate"]
    
    @pytest.mark.asyncio
    async def test_stats_with_failures(self):
        """Doit tracker les échecs."""
        agent = ReActAgent()
        
        def failing_tool():
            raise Exception("Error")
        
        agent.register_tool("failing", failing_tool, "Failing", {"parameters": {}})
        
        action = Action(tool_name="failing", arguments={})
        await agent.execute_action(action)
        await agent.execute_action(action)
        
        stats = agent.get_stats()
        
        assert stats["total_actions"] == 2
        assert stats["failed_actions"] == 2
        assert "0.0%" in stats["success_rate"]
    
    @pytest.mark.asyncio
    async def test_stats_average_duration(self):
        """Doit calculer la durée moyenne."""
        agent = ReActAgent()
        
        async def slow_tool():
            await asyncio.sleep(0.01)
            return "OK"
        
        agent.register_tool("slow", slow_tool, "Slow", {"parameters": {}})
        
        action = Action(tool_name="slow", arguments={})
        await agent.execute_action(action)
        
        stats = agent.get_stats()
        
        assert stats["average_duration"] > 0


class TestEdgeCases:
    """Tests pour les cas limites."""
    
    def test_format_prompt_empty_history(self):
        """Doit formater un prompt sans historique."""
        agent = ReActAgent()
        
        prompt = agent.format_prompt("Test task", [])
        
        assert "Test task" in prompt
        assert "Begin:" in prompt
    
    def test_format_prompt_with_history(self):
        """Doit formater un prompt avec historique."""
        agent = ReActAgent()
        
        action = Action(tool_name="test", arguments={})
        observation = Observation(
            action=action,
            result="OK",
            status=ActionStatus.SUCCESS
        )
        step = ReActStep(
            thought="Testing",
            action=action,
            observation=observation,
            step_number=1
        )
        
        prompt = agent.format_prompt("Test task", [step])
        
        assert "Previous steps" in prompt
        assert "Testing" in prompt
    
    def test_action_str_representation(self):
        """Doit formater une Action en string."""
        action = Action(
            tool_name="search",
            arguments={"query": "test", "limit": 10}
        )
        
        action_str = str(action)
        
        assert "search" in action_str
        assert "query=test" in action_str
        assert "limit=10" in action_str
    
    def test_observation_str_success(self):
        """Doit formater une Observation success."""
        action = Action(tool_name="test", arguments={})
        obs = Observation(
            action=action,
            result="Success!",
            status=ActionStatus.SUCCESS
        )
        
        obs_str = str(obs)
        
        assert "✅" in obs_str
        assert "Success!" in obs_str
    
    def test_observation_str_failure(self):
        """Doit formater une Observation failure."""
        action = Action(tool_name="test", arguments={})
        obs = Observation(
            action=action,
            result=None,
            status=ActionStatus.FAILURE,
            error="Something went wrong"
        )
        
        obs_str = str(obs)
        
        assert "❌" in obs_str
        assert "Something went wrong" in obs_str


class TestPerformance:
    """Tests de performance."""
    
    @pytest.mark.asyncio
    async def test_action_execution_speed(self):
        """L'exécution d'action doit être rapide (<1s)."""
        import time
        agent = ReActAgent()
        
        def fast_tool():
            return "OK"
        
        agent.register_tool("fast", fast_tool, "Fast", {"parameters": {}})
        
        action = Action(tool_name="fast", arguments={})
        
        start = time.time()
        observation = await agent.execute_action(action)
        elapsed = time.time() - start
        
        assert elapsed < 1.0
        assert observation.duration < 1.0
    
    @pytest.mark.asyncio
    async def test_parsing_speed(self):
        """Le parsing doit être rapide."""
        import time
        agent = ReActAgent()
        
        response = """Thought: I need to do something complex with multiple steps.
Action: complex_action(param1="value1", param2="value2", param3="value3")"""
        
        start = time.time()
        for _ in range(100):
            thought, action = agent.parse_llm_response(response)
        elapsed = time.time() - start
        
        # 100 parsing en <100ms
        assert elapsed < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
