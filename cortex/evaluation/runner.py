"""Evaluation runner — orchestrates skill execution and scoring.

Runs skills against datasets, collects scores, and produces
structured evaluation reports.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cortex.evaluation.judge import LLMJudge, JudgeScore
from cortex.models.provider import ModelProvider
from cortex.telemetry.metrics import MetricsCollector
from cortex.utils.io import write_json


@dataclass
class EvalResult:
    """Result of evaluating a single prompt."""

    prompt: str
    response: str
    score: JudgeScore
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt[:200],  # Truncate for readability
            "response": self.response[:500],
            "score": self.score.to_dict(),
            "latency_ms": self.latency_ms,
        }


@dataclass
class EvalReport:
    """Aggregated evaluation report."""

    skill: str
    dataset: str
    total: int = 0
    results: list[EvalResult] = field(default_factory=list)
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def mean_scores(self) -> dict[str, float]:
        if not self.results:
            return {}
        scores = [r.score for r in self.results]
        n = len(scores)
        return {
            "accuracy": round(sum(s.accuracy for s in scores) / n, 4),
            "reasoning": round(sum(s.reasoning for s in scores) / n, 4),
            "completeness": round(sum(s.completeness for s in scores) / n, 4),
            "coherence": round(sum(s.coherence for s in scores) / n, 4),
            "overall": round(sum(s.overall for s in scores) / n, 4),
            "normalized": round(sum(s.normalized for s in scores) / n, 4),
        }

    @property
    def mean_latency_ms(self) -> float:
        if not self.results:
            return 0.0
        return round(sum(r.latency_ms for r in self.results) / len(self.results), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill": self.skill,
            "dataset": self.dataset,
            "total": self.total,
            "mean_scores": self.mean_scores,
            "mean_latency_ms": self.mean_latency_ms,
            "duration_seconds": round(self.completed_at - self.started_at, 2),
        }


class EvaluationRunner:
    """Orchestrates evaluation of skills against datasets."""

    def __init__(
        self,
        skill_provider: ModelProvider,
        judge: LLMJudge,
        metrics: MetricsCollector | None = None,
    ) -> None:
        self._skill_provider = skill_provider
        self._judge = judge
        self._metrics = metrics

    def evaluate(
        self,
        skill_name: str,
        skill_prompt: str,
        dataset: list[dict[str, Any]],
        dataset_name: str = "unnamed",
        max_items: int | None = None,
    ) -> EvalReport:
        """Run evaluation of a skill against a dataset.

        Args:
            skill_name: Identifier for the skill being evaluated.
            skill_prompt: The skill's system/instruction prompt.
            dataset: List of dicts with at least a "prompt" key.
            dataset_name: Name of the dataset for reporting.
            max_items: Optional limit on number of items to evaluate.
        """
        items = dataset[:max_items] if max_items else dataset
        report = EvalReport(
            skill=skill_name,
            dataset=dataset_name,
            total=len(items),
            started_at=time.time(),
        )

        for item in items:
            prompt = item.get("prompt", "")
            if not prompt:
                continue

            full_prompt = f"{skill_prompt}\n\n{prompt}"

            # Run skill
            start = time.time()
            response = self._skill_provider.generate(full_prompt)
            latency = (time.time() - start) * 1000

            # Judge response
            score = self._judge.score(prompt, response.content)

            result = EvalResult(
                prompt=prompt,
                response=response.content,
                score=score,
                latency_ms=round(latency, 2),
            )
            report.results.append(result)

            # Record metrics
            if self._metrics:
                self._metrics.record(skill_name, "accuracy", score.accuracy)
                self._metrics.record(skill_name, "reasoning", score.reasoning)
                self._metrics.record(skill_name, "latency_ms", latency)
                self._metrics.record(skill_name, "overall", score.overall)

        report.completed_at = time.time()
        return report

    def save_report(self, report: EvalReport, path: str | Path) -> None:
        """Save evaluation report to JSON."""
        write_json(path, report.to_dict())
