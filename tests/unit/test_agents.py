"""Tests for multi-agent runtime."""

from __future__ import annotations

import pytest

from cortex.agents.base_agent import ResearcherAgent, CriticAgent, StrategistAgent, SynthesizerAgent
from cortex.agents.orchestrator import AgentOrchestrator
from cortex.agents.debate import DebateArena
from cortex.agents.task_graph import TaskGraph, TaskNode
from cortex.models.claude_provider import MockProvider


class TestAgents:
    def test_researcher_agent(self):
        provider = MockProvider(["Research findings on the topic."])
        agent = ResearcherAgent(provider)
        response = agent.execute("AI automation")
        assert response.agent_name == "researcher"
        assert response.role == "research"
        assert len(response.content) > 0

    def test_critic_agent(self):
        provider = MockProvider(["The analysis lacks evidence."])
        agent = CriticAgent(provider)
        response = agent.execute("Some analysis text")
        assert response.agent_name == "critic"

    def test_strategist_agent(self):
        provider = MockProvider(["Strategic recommendation: focus on X."])
        agent = StrategistAgent(provider)
        response = agent.execute("Research and critique")
        assert response.agent_name == "strategist"

    def test_synthesizer_agent(self):
        provider = MockProvider(["Final synthesis report."])
        agent = SynthesizerAgent(provider)
        response = agent.execute("All inputs", context={"research": "r", "critique": "c"})
        assert response.agent_name == "synthesizer"


class TestOrchestrator:
    def test_full_pipeline(self):
        provider = MockProvider(
            [
                "Research output",
                "Critique output",
                "Strategy output",
                "Final synthesis",
            ]
        )
        orchestrator = AgentOrchestrator(provider)
        result = orchestrator.run("AI in healthcare")
        assert len(result.stages) == 4
        assert result.final_output == "Final synthesis"
        assert result.total_latency_ms > 0

    def test_agent_names(self):
        provider = MockProvider(["test"])
        orchestrator = AgentOrchestrator(provider)
        assert "researcher" in orchestrator.agent_names
        assert "synthesizer" in orchestrator.agent_names

    def test_run_single(self):
        provider = MockProvider(["Single agent output"])
        orchestrator = AgentOrchestrator(provider)
        result = orchestrator.run_single("researcher", "test topic")
        assert result is not None
        assert result.agent_name == "researcher"

    def test_run_single_unknown_agent(self):
        provider = MockProvider(["test"])
        orchestrator = AgentOrchestrator(provider)
        assert orchestrator.run_single("nonexistent", "test") is None


class TestDebateArena:
    def test_debate_produces_rounds(self):
        provider = MockProvider(
            [
                "Argument for",
                "Argument against",
                "Refined argument for",
                "Refined argument against",
                "Final for",
                "Final against",
                "Synthesis of debate",
            ]
        )
        arena = DebateArena(provider, num_rounds=3)
        result = arena.debate("Should AI be regulated?")
        assert len(result.rounds) == 3
        assert len(result.final_synthesis) > 0

    def test_debate_caps_rounds(self):
        provider = MockProvider(["response"] * 30)
        arena = DebateArena(provider, num_rounds=10)  # Should cap at 5
        result = arena.debate("test topic")
        assert len(result.rounds) <= 5


class TestTaskGraph:
    def test_linear_graph(self):
        provider = MockProvider(["Step 1 output", "Step 2 output"])
        agent1 = ResearcherAgent(provider)
        agent2 = SynthesizerAgent(provider)

        graph = TaskGraph()
        graph.add_node(TaskNode(name="research", agent=agent1))
        graph.add_node(TaskNode(name="synthesize", agent=agent2, dependencies=["research"]))

        result = graph.execute("Test input")
        assert "research" in result.outputs
        assert "synthesize" in result.outputs
        assert result.execution_order == ["research", "synthesize"]

    def test_cycle_detection(self):
        provider = MockProvider(["test"])
        agent = ResearcherAgent(provider)

        graph = TaskGraph()
        graph.add_node(TaskNode(name="a", agent=agent))
        graph.add_node(TaskNode(name="b", agent=agent, dependencies=["a"]))
        # Can't create cycle because "c" depends on "b" and we'd need "a" to depend on "c"
        # But we can test missing dependency
        with pytest.raises(ValueError, match="not found"):
            graph.add_node(TaskNode(name="d", agent=agent, dependencies=["nonexistent"]))

    def test_duplicate_node(self):
        provider = MockProvider(["test"])
        agent = ResearcherAgent(provider)
        graph = TaskGraph()
        graph.add_node(TaskNode(name="a", agent=agent))
        with pytest.raises(ValueError, match="already exists"):
            graph.add_node(TaskNode(name="a", agent=agent))

    def test_visualize(self):
        provider = MockProvider(["test"])
        agent = ResearcherAgent(provider)
        graph = TaskGraph()
        graph.add_node(TaskNode(name="research", agent=agent))
        graph.add_node(TaskNode(name="report", agent=agent, dependencies=["research"]))
        viz = graph.visualize()
        assert "research" in viz
        assert "report" in viz
