"""Tests for experiment tracking."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cortex.experiments import Experiment, ExperimentTracker


class TestExperiment:
    def test_create_experiment(self):
        exp = Experiment(name="test", skill="research", dataset="bench1")
        assert exp.name == "test"
        assert exp.status == "running"
        assert exp.model == "claude"
        assert exp.prompt_version == "v1"

    def test_experiment_id_deterministic(self):
        exp = Experiment(name="test", skill="research", dataset="bench1", started_at=1000.0)
        id1 = exp.experiment_id
        id2 = exp.experiment_id
        assert id1 == id2
        assert len(id1) == 12

    def test_duration_not_completed(self):
        exp = Experiment(name="test", skill="research", dataset="bench1")
        assert exp.duration_seconds == 0.0

    def test_complete(self):
        exp = Experiment(name="test", skill="research", dataset="bench1")
        exp.complete({"accuracy": 0.9})
        assert exp.status == "completed"
        assert exp.metrics == {"accuracy": 0.9}
        assert exp.completed_at > 0

    def test_duration_after_complete(self):
        exp = Experiment(name="test", skill="research", dataset="bench1", started_at=1000.0)
        exp.completed_at = 1005.0
        assert exp.duration_seconds == 5.0

    def test_fail(self):
        exp = Experiment(name="test", skill="research", dataset="bench1")
        exp.fail("some error")
        assert exp.status == "failed"
        assert exp.config["error"] == "some error"

    def test_to_dict(self):
        exp = Experiment(name="test", skill="research", dataset="bench1")
        d = exp.to_dict()
        assert d["name"] == "test"
        assert d["skill"] == "research"
        assert "experiment_id" in d
        assert "duration_seconds" in d


class TestExperimentTracker:
    def test_log_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(tmpdir)
            exp = Experiment(name="test", skill="research", dataset="bench1")
            exp_id = tracker.log_experiment(exp)
            retrieved = tracker.get_experiment(exp_id)
            assert retrieved is not None
            assert retrieved["name"] == "test"

    def test_get_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(tmpdir)
            assert tracker.get_experiment("nonexistent") is None

    def test_list_experiments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(tmpdir)
            for i in range(3):
                exp = Experiment(name=f"exp_{i}", skill="research", dataset="bench1")
                tracker.log_experiment(exp)
            results = tracker.list_experiments()
            assert len(results) == 3

    def test_list_filter_by_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(tmpdir)
            exp1 = Experiment(name="a", skill="research", dataset="d1")
            exp2 = Experiment(name="b", skill="strategy", dataset="d1")
            tracker.log_experiment(exp1)
            tracker.log_experiment(exp2)
            results = tracker.list_experiments(skill="research")
            assert len(results) == 1
            assert results[0]["skill"] == "research"

    def test_compare(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(tmpdir)
            exp1 = Experiment(name="a", skill="research", dataset="d1")
            exp2 = Experiment(name="b", skill="research", dataset="d1")
            id1 = tracker.log_experiment(exp1)
            id2 = tracker.log_experiment(exp2)
            compared = tracker.compare([id1, id2])
            assert len(compared) == 2

    def test_compare_missing_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(tmpdir)
            compared = tracker.compare(["nonexistent"])
            assert len(compared) == 0

    def test_best_experiment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(tmpdir)
            exp1 = Experiment(name="a", skill="research", dataset="d1")
            exp1.complete({"overall": 0.7})
            exp2 = Experiment(name="b", skill="research", dataset="d1")
            exp2.complete({"overall": 0.9})
            tracker.log_experiment(exp1)
            tracker.log_experiment(exp2)
            best = tracker.best_experiment("research", "overall")
            assert best is not None
            assert best["metrics"]["overall"] == 0.9

    def test_best_experiment_no_completed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(tmpdir)
            exp = Experiment(name="a", skill="research", dataset="d1")
            tracker.log_experiment(exp)  # still "running"
            assert tracker.best_experiment("research") is None
