"""Regression detection for skill performance across versions.

Compares evaluation results across runs to detect performance
degradation beyond configurable tolerance thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cortex.utils.io import read_json, write_json


@dataclass(frozen=True)
class RegressionResult:
    """Result of a regression check."""

    metric: str
    baseline: float
    current: float
    delta: float
    tolerance: float
    regressed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "baseline": self.baseline,
            "current": self.current,
            "delta": round(self.delta, 4),
            "tolerance": self.tolerance,
            "regressed": self.regressed,
        }


class RegressionDetector:
    """Detects performance regressions across evaluation runs.

    Compares current evaluation scores against a stored baseline.
    A regression is flagged when score drops exceed the tolerance.
    """

    def __init__(self, baseline_dir: str | Path, tolerance: float = 0.05) -> None:
        self._baseline_dir = Path(baseline_dir)
        self._baseline_dir.mkdir(parents=True, exist_ok=True)
        self._tolerance = tolerance

    def check(self, skill: str, current_scores: dict[str, float]) -> list[RegressionResult]:
        """Check for regressions against stored baseline.

        Returns list of RegressionResult for each metric.
        """
        baseline = self._load_baseline(skill)
        if not baseline:
            # No baseline yet — store current as baseline
            self._save_baseline(skill, current_scores)
            return []

        results: list[RegressionResult] = []
        for metric, current_value in current_scores.items():
            baseline_value = baseline.get(metric, 0.0)
            delta = current_value - baseline_value
            regressed = delta < -self._tolerance

            results.append(
                RegressionResult(
                    metric=metric,
                    baseline=baseline_value,
                    current=current_value,
                    delta=delta,
                    tolerance=self._tolerance,
                    regressed=regressed,
                )
            )
        return results

    def update_baseline(self, skill: str, scores: dict[str, float]) -> None:
        """Explicitly update the baseline for a skill."""
        self._save_baseline(skill, scores)

    def _load_baseline(self, skill: str) -> dict[str, float] | None:
        path = self._baseline_dir / f"{skill}_baseline.json"
        if not path.exists():
            return None
        data = read_json(path)
        return data.get("scores", {})

    def _save_baseline(self, skill: str, scores: dict[str, float]) -> None:
        import time

        path = self._baseline_dir / f"{skill}_baseline.json"
        write_json(path, {"skill": skill, "scores": scores, "updated_at": time.time()})

    @property
    def tolerance(self) -> float:
        return self._tolerance
