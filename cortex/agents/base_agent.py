"""Base agent interface for the multi-agent runtime.

All specialized agents extend BaseAgent and implement the execute() method.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from cortex.models.provider import ModelProvider, ModelResponse
from cortex.utils.security import sanitize_input


@dataclass
class AgentResponse:
    """Structured response from an agent execution."""

    content: str
    agent_name: str
    role: str
    latency_ms: float = 0.0
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent_name,
            "role": self.role,
            "content": self.content,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
        }


class BaseAgent(ABC):
    """Abstract base agent with model provider integration."""

    def __init__(self, name: str, role: str, provider: ModelProvider, system_prompt: str = "") -> None:
        self.name = name
        self.role = role
        self._provider = provider
        self._system_prompt = system_prompt

    @abstractmethod
    def execute(self, input_text: str, context: dict[str, Any] | None = None) -> AgentResponse:
        """Execute the agent's task on the given input."""

    def _call_model(self, prompt: str, **kwargs) -> ModelResponse:
        """Call the underlying model with the system prompt prepended.

        Input is sanitized before being sent to the model provider.
        """
        prompt = sanitize_input(prompt)
        full_prompt = f"{self._system_prompt}\n\n{prompt}" if self._system_prompt else prompt
        return self._provider.generate(full_prompt, **kwargs)


class ResearcherAgent(BaseAgent):
    """Agent specialized in gathering information and producing insights."""

    def __init__(self, provider: ModelProvider) -> None:
        super().__init__(
            name="researcher",
            role="research",
            provider=provider,
            system_prompt=(
                "You are an expert research analyst. Your role is to:\n"
                "1. Identify key findings and evidence\n"
                "2. Assess source quality and reliability\n"
                "3. Synthesize information across multiple perspectives\n"
                "4. Highlight gaps in current knowledge\n\n"
                "Produce structured analysis with clear evidence chains."
            ),
        )

    def execute(self, input_text: str, context: dict[str, Any] | None = None) -> AgentResponse:
        start = time.time()
        response = self._call_model(f"Research the following topic:\n\n{input_text}")
        latency = (time.time() - start) * 1000
        return AgentResponse(
            content=response.content,
            agent_name=self.name,
            role=self.role,
            latency_ms=round(latency, 2),
            tokens_used=response.tokens_used,
        )


class CriticAgent(BaseAgent):
    """Agent specialized in critical evaluation and challenging assumptions."""

    def __init__(self, provider: ModelProvider) -> None:
        super().__init__(
            name="critic",
            role="critique",
            provider=provider,
            system_prompt=(
                "You are a rigorous academic critic. Your role is to:\n"
                "1. Identify logical fallacies and unsupported claims\n"
                "2. Challenge assumptions and biases\n"
                "3. Point out missing evidence or alternative explanations\n"
                "4. Assess the strength of reasoning chains\n\n"
                "Be constructive but thorough. Every claim needs justification."
            ),
        )

    def execute(self, input_text: str, context: dict[str, Any] | None = None) -> AgentResponse:
        start = time.time()
        critique_prompt = f"Critically evaluate the following analysis:\n\n{input_text}"
        if context and "research" in context:
            critique_prompt += f"\n\nOriginal research:\n{context['research'][:2000]}"
        response = self._call_model(critique_prompt)
        latency = (time.time() - start) * 1000
        return AgentResponse(
            content=response.content,
            agent_name=self.name,
            role=self.role,
            latency_ms=round(latency, 2),
            tokens_used=response.tokens_used,
        )


class StrategistAgent(BaseAgent):
    """Agent specialized in strategic recommendations and action plans."""

    def __init__(self, provider: ModelProvider) -> None:
        super().__init__(
            name="strategist",
            role="strategy",
            provider=provider,
            system_prompt=(
                "You are a senior strategic advisor. Your role is to:\n"
                "1. Translate research findings into actionable strategies\n"
                "2. Identify opportunities and risks\n"
                "3. Propose concrete action plans with priorities\n"
                "4. Consider resource constraints and trade-offs\n\n"
                "Produce clear, prioritized strategic recommendations."
            ),
        )

    def execute(self, input_text: str, context: dict[str, Any] | None = None) -> AgentResponse:
        start = time.time()
        strategy_prompt = f"Based on the following analysis, propose strategic recommendations:\n\n{input_text}"
        if context and "critique" in context:
            strategy_prompt += f"\n\nCritique to address:\n{context['critique'][:2000]}"
        response = self._call_model(strategy_prompt)
        latency = (time.time() - start) * 1000
        return AgentResponse(
            content=response.content,
            agent_name=self.name,
            role=self.role,
            latency_ms=round(latency, 2),
            tokens_used=response.tokens_used,
        )


class SynthesizerAgent(BaseAgent):
    """Agent specialized in combining multiple agent outputs into coherent reports."""

    def __init__(self, provider: ModelProvider) -> None:
        super().__init__(
            name="synthesizer",
            role="synthesis",
            provider=provider,
            system_prompt=(
                "You are an expert report synthesizer. Your role is to:\n"
                "1. Combine research, critique, and strategy into a coherent report\n"
                "2. Resolve contradictions between sources\n"
                "3. Produce executive-quality structured output\n"
                "4. Ensure all key findings and recommendations are preserved\n\n"
                "Produce a clear, well-organized final report."
            ),
        )

    def execute(self, input_text: str, context: dict[str, Any] | None = None) -> AgentResponse:
        start = time.time()
        parts = [f"Synthesize the following into a final report:\n\n{input_text}"]
        if context:
            for key in ("research", "critique", "strategy"):
                if key in context:
                    parts.append(f"\n## {key.title()}\n{context[key][:3000]}")

        response = self._call_model("\n".join(parts))
        latency = (time.time() - start) * 1000
        return AgentResponse(
            content=response.content,
            agent_name=self.name,
            role=self.role,
            latency_ms=round(latency, 2),
            tokens_used=response.tokens_used,
        )
