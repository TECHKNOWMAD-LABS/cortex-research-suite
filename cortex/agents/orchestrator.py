"""Agent orchestrator for sequential and parallel agent pipelines.

Manages the execution flow of multiple agents, passing context
between stages and aggregating results.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from cortex.agents.base_agent import (
    AgentResponse,
    BaseAgent,
    CriticAgent,
    ResearcherAgent,
    StrategistAgent,
    SynthesizerAgent,
)
from cortex.models.provider import ModelProvider
from cortex.telemetry.logger import get_logger


@dataclass
class PipelineResult:
    """Result of a full agent pipeline execution."""

    topic: str
    stages: list[AgentResponse] = field(default_factory=list)
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    final_output: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "stages": [s.to_dict() for s in self.stages],
            "total_latency_ms": self.total_latency_ms,
            "total_tokens": self.total_tokens,
            "final_output": self.final_output[:2000],
        }


class AgentOrchestrator:
    """Orchestrates multi-agent pipelines for complex analysis tasks.

    Default pipeline: Researcher -> Critic -> Strategist -> Synthesizer.
    Custom pipelines supported via the `agents` parameter.
    """

    def __init__(self, provider: ModelProvider, agents: list[BaseAgent] | None = None) -> None:
        self._provider = provider
        self._logger = get_logger()
        if agents:
            self._agents = agents
        else:
            # Default 4-stage research pipeline
            self._agents = [
                ResearcherAgent(provider),
                CriticAgent(provider),
                StrategistAgent(provider),
                SynthesizerAgent(provider),
            ]

    def run(self, topic: str) -> PipelineResult:
        """Execute the full agent pipeline on a topic."""
        result = PipelineResult(topic=topic)
        start = time.time()

        context: dict[str, Any] = {}
        current_input = topic

        for agent in self._agents:
            self._logger.info(
                "Agent executing",
                agent=agent.name,
                role=agent.role,
                topic=topic[:100],
            )

            response = agent.execute(current_input, context=context)
            result.stages.append(response)
            result.total_tokens += response.tokens_used

            # Pass output to next stage
            context[agent.role] = response.content
            current_input = response.content

            self._logger.info(
                "Agent completed",
                agent=agent.name,
                latency_ms=response.latency_ms,
                tokens=response.tokens_used,
            )

        result.total_latency_ms = round((time.time() - start) * 1000, 2)
        result.final_output = result.stages[-1].content if result.stages else ""
        return result

    def run_single(self, agent_name: str, input_text: str) -> AgentResponse | None:
        """Run a single named agent."""
        for agent in self._agents:
            if agent.name == agent_name:
                return agent.execute(input_text)
        return None

    @property
    def agent_names(self) -> list[str]:
        return [a.name for a in self._agents]
