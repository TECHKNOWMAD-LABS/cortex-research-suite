"""LLM-as-Judge evaluation system.

Uses a separate LLM instance to score skill outputs against
structured rubrics. Supports multiple evaluation dimensions.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from cortex.models.provider import ModelProvider, ModelResponse


@dataclass(frozen=True)
class JudgeScore:
    """Structured evaluation score from the LLM judge."""

    accuracy: float = 0.0
    reasoning: float = 0.0
    completeness: float = 0.0
    coherence: float = 0.0
    raw_response: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def overall(self) -> float:
        """Weighted overall score (0-5 scale)."""
        return round(
            0.30 * self.accuracy
            + 0.30 * self.reasoning
            + 0.20 * self.completeness
            + 0.20 * self.coherence,
            3,
        )

    @property
    def normalized(self) -> float:
        """Overall score normalized to 0-1 range."""
        return round(self.overall / 5.0, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "reasoning": self.reasoning,
            "completeness": self.completeness,
            "coherence": self.coherence,
            "overall": self.overall,
            "normalized": self.normalized,
        }


_JUDGE_RUBRIC = """You are an expert evaluator. Score the following response on a scale of 1-5 for each dimension.

## Evaluation Dimensions

1. **Accuracy** (1-5): Factual correctness and precision of claims
2. **Reasoning** (1-5): Logical structure, valid inferences, and analytical depth
3. **Completeness** (1-5): Coverage of key aspects and thoroughness
4. **Coherence** (1-5): Clarity, organization, and readability

## Prompt Given
{prompt}

## Response to Evaluate
{response}

## Instructions
Score each dimension from 1-5. Respond with ONLY valid JSON:
{{"accuracy": <score>, "reasoning": <score>, "completeness": <score>, "coherence": <score>}}
"""


class LLMJudge:
    """LLM-based evaluation judge for scoring skill outputs."""

    def __init__(self, provider: ModelProvider, rubric: str | None = None) -> None:
        self._provider = provider
        self._rubric = rubric or _JUDGE_RUBRIC

    def score(self, prompt: str, response: str) -> JudgeScore:
        """Score a skill response against the evaluation rubric."""
        judge_prompt = self._rubric.format(prompt=prompt, response=response)
        result = self._provider.generate(judge_prompt, temperature=0.1, max_tokens=256)
        return self._parse_score(result)

    def _parse_score(self, result: ModelResponse) -> JudgeScore:
        """Parse structured scores from judge response."""
        content = result.content.strip()
        # Extract JSON from response (handle markdown fences)
        json_match = re.search(r"\{[^}]+\}", content)
        if not json_match:
            return JudgeScore(raw_response=content, metadata={"parse_error": "no JSON found"})

        try:
            data = json.loads(json_match.group())
            return JudgeScore(
                accuracy=float(data.get("accuracy", 0)),
                reasoning=float(data.get("reasoning", 0)),
                completeness=float(data.get("completeness", 0)),
                coherence=float(data.get("coherence", 0)),
                raw_response=content,
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            return JudgeScore(raw_response=content, metadata={"parse_error": str(e)})
