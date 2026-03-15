"""Multi-agent debate system for improved reasoning quality.

Two agents debate a topic through multiple rounds, producing
progressively refined analysis. A judge evaluates the final output.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from cortex.agents.base_agent import BaseAgent, AgentResponse
from cortex.models.provider import ModelProvider


@dataclass
class DebateRound:
    """A single round of debate between two agents."""

    round_num: int
    proposer_response: AgentResponse
    challenger_response: AgentResponse

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round_num,
            "proposer": self.proposer_response.to_dict(),
            "challenger": self.challenger_response.to_dict(),
        }


@dataclass
class DebateResult:
    """Complete result of a multi-round debate."""

    topic: str
    rounds: list[DebateRound] = field(default_factory=list)
    final_synthesis: str = ""
    total_latency_ms: float = 0.0
    total_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "num_rounds": len(self.rounds),
            "rounds": [r.to_dict() for r in self.rounds],
            "final_synthesis": self.final_synthesis[:2000],
            "total_latency_ms": self.total_latency_ms,
            "total_tokens": self.total_tokens,
        }


class _DebateAgent(BaseAgent):
    """Internal debate participant agent."""

    def __init__(self, name: str, role: str, provider: ModelProvider, stance: str) -> None:
        super().__init__(
            name=name,
            role=role,
            provider=provider,
            system_prompt=(
                f"You are participating in a structured analytical debate.\n"
                f"Your stance: {stance}\n\n"
                f"Rules:\n"
                f"1. Support your position with evidence and reasoning\n"
                f"2. Address counterarguments directly\n"
                f"3. Acknowledge valid points from the other side\n"
                f"4. Refine your position based on new arguments\n"
                f"5. Be intellectually honest — concede when warranted"
            ),
        )
        self._stance = stance

    def execute(self, input_text: str, context: dict[str, Any] | None = None) -> AgentResponse:
        start = time.time()
        response = self._call_model(input_text)
        latency = (time.time() - start) * 1000
        return AgentResponse(
            content=response.content,
            agent_name=self.name,
            role=self.role,
            latency_ms=round(latency, 2),
            tokens_used=response.tokens_used,
        )


class DebateArena:
    """Manages structured multi-round debates between agents.

    Improves reasoning quality by forcing iterative refinement
    through adversarial argumentation.
    """

    def __init__(self, provider: ModelProvider, num_rounds: int = 3) -> None:
        self._provider = provider
        self._num_rounds = min(num_rounds, 5)  # Cap at 5 to control costs

    def debate(self, topic: str) -> DebateResult:
        """Run a multi-round debate on the given topic."""
        proposer = _DebateAgent("proposer", "propose", self._provider, stance="Argue FOR the proposition")
        challenger = _DebateAgent("challenger", "challenge", self._provider, stance="Argue AGAINST the proposition")

        result = DebateResult(topic=topic)
        start = time.time()

        proposer_input = f"Topic for debate: {topic}\n\nPresent your opening argument."
        challenger_context = ""

        for round_num in range(1, self._num_rounds + 1):
            # Proposer argues
            prop_response = proposer.execute(proposer_input)
            result.total_tokens += prop_response.tokens_used

            # Challenger responds
            challenger_input = (
                f"Topic: {topic}\n\n"
                f"Round {round_num} — Proposer's argument:\n{prop_response.content}\n\n"
                f"Respond with your counterargument."
            )
            chall_response = challenger.execute(challenger_input)
            result.total_tokens += chall_response.tokens_used

            result.rounds.append(
                DebateRound(
                    round_num=round_num,
                    proposer_response=prop_response,
                    challenger_response=chall_response,
                )
            )

            # Set up next round
            proposer_input = (
                f"Topic: {topic}\n\n"
                f"Round {round_num} — Challenger's response:\n{chall_response.content}\n\n"
                f"Refine your argument, addressing the counterpoints."
            )

        # Final synthesis
        synthesis_prompt = (
            f"Topic: {topic}\n\n"
            f"After {self._num_rounds} rounds of debate, synthesize the strongest arguments "
            f"from both sides into a balanced, well-reasoned conclusion.\n\n"
            f"Final proposer argument:\n{result.rounds[-1].proposer_response.content[:2000]}\n\n"
            f"Final challenger argument:\n{result.rounds[-1].challenger_response.content[:2000]}"
        )
        synth_response = self._provider.generate(synthesis_prompt, temperature=0.2)
        result.final_synthesis = synth_response.content
        result.total_tokens += synth_response.tokens_used
        result.total_latency_ms = round((time.time() - start) * 1000, 2)

        return result
