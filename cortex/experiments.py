"""Experiment tracking for reproducible evaluation runs.

Records experiment configurations, results, and metadata
for comparison across skill versions and prompt iterations.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cortex.utils.io import read_json, write_json


@dataclass
class Experiment:
    """A single tracked experiment run."""

    name: str
    skill: str
    dataset: str
    model: str = "claude"
    prompt_version: str = "v1"
    config: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    status: str = "running"

    @property
    def experiment_id(self) -> str:
        """Deterministic ID based on experiment parameters."""
        key = f"{self.name}:{self.skill}:{self.dataset}:{self.model}:{self.prompt_version}:{self.started_at}"
        return hashlib.sha256(key.encode()).hexdigest()[:12]

    @property
    def duration_seconds(self) -> float:
        if self.completed_at == 0:
            return 0.0
        return round(self.completed_at - self.started_at, 2)

    def complete(self, metrics: dict[str, float]) -> None:
        """Mark experiment as completed with final metrics."""
        self.metrics = metrics
        self.completed_at = time.time()
        self.status = "completed"

    def fail(self, error: str) -> None:
        """Mark experiment as failed."""
        self.completed_at = time.time()
        self.status = "failed"
        self.config["error"] = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "skill": self.skill,
            "dataset": self.dataset,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "config": self.config,
            "metrics": self.metrics,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
        }


class ExperimentTracker:
    """Manages experiment history and comparison.

    Stores all experiment runs in a JSON-based log for
    reproducibility and cross-version comparison.
    """

    def __init__(self, experiments_dir: str | Path = "experiments") -> None:
        self._dir = Path(experiments_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._dir / "experiment_log.json"

    def log_experiment(self, experiment: Experiment) -> str:
        """Save an experiment to the log. Returns experiment ID."""
        log = self._load_log()
        log[experiment.experiment_id] = experiment.to_dict()
        write_json(self._log_path, log)
        return experiment.experiment_id

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        """Retrieve a specific experiment by ID."""
        log = self._load_log()
        return log.get(experiment_id)

    def list_experiments(self, skill: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """List recent experiments, optionally filtered by skill."""
        log = self._load_log()
        experiments = list(log.values())
        if skill:
            experiments = [e for e in experiments if e.get("skill") == skill]
        experiments.sort(key=lambda e: e.get("started_at", 0), reverse=True)
        return experiments[:limit]

    def compare(self, experiment_ids: list[str]) -> list[dict[str, Any]]:
        """Compare metrics across multiple experiments."""
        log = self._load_log()
        return [log[eid] for eid in experiment_ids if eid in log]

    def best_experiment(self, skill: str, metric: str = "overall") -> dict[str, Any] | None:
        """Find the best-performing experiment for a skill."""
        experiments = self.list_experiments(skill=skill)
        completed = [e for e in experiments if e.get("status") == "completed"]
        if not completed:
            return None
        return max(completed, key=lambda e: e.get("metrics", {}).get(metric, 0))

    def _load_log(self) -> dict[str, Any]:
        if not self._log_path.exists():
            return {}
        return read_json(self._log_path)
