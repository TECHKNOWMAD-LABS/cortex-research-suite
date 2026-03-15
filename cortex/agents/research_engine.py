"""Automated research engine for structured research workflows.

Combines the agent pipeline with evaluation to produce
quality-assessed research reports on any topic.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cortex.agents.orchestrator import AgentOrchestrator, PipelineResult
from cortex.evaluation.judge import LLMJudge, JudgeScore
from cortex.models.provider import ModelProvider
from cortex.utils.io import write_json


@dataclass
class ResearchReport:
    """A complete research report with quality assessment."""

    topic: str
    pipeline_result: PipelineResult
    quality_score: JudgeScore | None = None
    generated_at: float = field(default_factory=time.time)

    @property
    def content(self) -> str:
        return self.pipeline_result.final_output

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "topic": self.topic,
            "content": self.content[:5000],
            "pipeline": self.pipeline_result.to_dict(),
            "generated_at": self.generated_at,
        }
        if self.quality_score:
            result["quality_score"] = self.quality_score.to_dict()
        return result


class ResearchEngine:
    """Automated research workflow engine.

    Workflow:
    1. Run multi-agent pipeline on research topic
    2. Evaluate output quality via LLM judge
    3. If below threshold, refine and re-run
    4. Produce final research report

    Supports iterative refinement with configurable quality gates.
    """

    def __init__(
        self,
        provider: ModelProvider,
        min_quality: float = 0.6,
        max_iterations: int = 2,
    ) -> None:
        self._provider = provider
        self._orchestrator = AgentOrchestrator(provider)
        self._judge = LLMJudge(provider)
        self._min_quality = min_quality
        self._max_iterations = max_iterations

    def research(self, topic: str) -> ResearchReport:
        """Conduct automated research on a topic.

        Runs the full agent pipeline and evaluates quality.
        Re-runs with refinement if below quality threshold.
        """
        best_report: ResearchReport | None = None

        for iteration in range(self._max_iterations):
            if iteration == 0:
                prompt = topic
            else:
                # Refinement: include previous quality feedback
                assert best_report is not None
                assert best_report.quality_score is not None
                prompt = (
                    f"{topic}\n\n"
                    f"Previous attempt scored {best_report.quality_score.normalized:.2f}/1.0. "
                    f"Areas for improvement: accuracy={best_report.quality_score.accuracy}/5, "
                    f"reasoning={best_report.quality_score.reasoning}/5, "
                    f"completeness={best_report.quality_score.completeness}/5. "
                    f"Produce a significantly improved analysis."
                )

            pipeline_result = self._orchestrator.run(prompt)
            quality = self._judge.score(topic, pipeline_result.final_output)

            report = ResearchReport(
                topic=topic,
                pipeline_result=pipeline_result,
                quality_score=quality,
            )

            if best_report is None or quality.normalized > (best_report.quality_score.normalized if best_report.quality_score else 0):
                best_report = report

            if quality.normalized >= self._min_quality:
                break

        assert best_report is not None
        return best_report

    def save_report(self, report: ResearchReport, path: str | Path) -> None:
        """Save research report to JSON."""
        write_json(path, report.to_dict())
