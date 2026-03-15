"""Tests for evaluation system."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from cortex.evaluation.judge import LLMJudge, JudgeScore
from cortex.evaluation.runner import EvaluationRunner, EvalResult
from cortex.evaluation.regression import RegressionDetector
from cortex.evaluation.benchmarks import BenchmarkSuite, BenchmarkCase
from cortex.models.claude_provider import MockProvider


class TestJudgeScore:
    def test_overall_weighted(self):
        score = JudgeScore(accuracy=4.0, reasoning=3.0, completeness=5.0, coherence=4.0)
        # 0.30*4 + 0.30*3 + 0.20*5 + 0.20*4 = 1.2+0.9+1.0+0.8 = 3.9
        assert score.overall == pytest.approx(3.9, rel=0.01)

    def test_normalized(self):
        score = JudgeScore(accuracy=5.0, reasoning=5.0, completeness=5.0, coherence=5.0)
        assert score.normalized == pytest.approx(1.0, rel=0.01)

    def test_to_dict(self):
        score = JudgeScore(accuracy=3.0, reasoning=4.0, completeness=3.5, coherence=4.5)
        d = score.to_dict()
        assert "accuracy" in d
        assert "overall" in d
        assert "normalized" in d


class TestLLMJudge:
    def test_score_with_mock(self):
        mock = MockProvider([json.dumps({"accuracy": 4, "reasoning": 3, "completeness": 4, "coherence": 3})])
        judge = LLMJudge(mock)
        score = judge.score("test prompt", "test response")
        assert score.accuracy == 4.0
        assert score.reasoning == 3.0

    def test_handles_malformed_response(self):
        mock = MockProvider(["This is not JSON at all"])
        judge = LLMJudge(mock)
        score = judge.score("test", "response")
        assert "parse_error" in score.metadata


class TestRegressionDetector:
    def test_no_baseline_stores_current(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = RegressionDetector(tmpdir, tolerance=0.05)
            results = detector.check("skill_a", {"accuracy": 0.9, "reasoning": 0.8})
            assert results == []  # No baseline to compare against

    def test_detects_regression(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = RegressionDetector(tmpdir, tolerance=0.05)
            # First run sets baseline
            detector.check("skill_a", {"accuracy": 0.9})
            # Second run with lower score
            results = detector.check("skill_a", {"accuracy": 0.8})
            assert len(results) == 1
            assert results[0].regressed is True
            assert results[0].delta == pytest.approx(-0.1, rel=0.01)

    def test_no_regression_within_tolerance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = RegressionDetector(tmpdir, tolerance=0.05)
            detector.check("skill_a", {"accuracy": 0.9})
            results = detector.check("skill_a", {"accuracy": 0.87})
            assert results[0].regressed is False  # -0.03 < 0.05 tolerance


class TestBenchmarkSuite:
    def test_create_reasoning_benchmark(self):
        suite = BenchmarkSuite.create_reasoning_benchmark()
        assert suite.size > 0
        assert all(c.category == "reasoning" for c in suite.cases)

    def test_create_strategy_benchmark(self):
        suite = BenchmarkSuite.create_strategy_benchmark()
        assert suite.size > 0
        assert all(c.category == "strategy" for c in suite.cases)

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "benchmark.json"
            suite = BenchmarkSuite.create_reasoning_benchmark()
            suite.save(path)
            loaded = BenchmarkSuite.load(path)
            assert loaded.name == suite.name
            assert loaded.size == suite.size

    def test_to_dataset(self):
        suite = BenchmarkSuite.create_reasoning_benchmark()
        dataset = suite.to_dataset()
        assert len(dataset) == suite.size
        assert all("prompt" in d for d in dataset)

    def test_filter_by_difficulty(self):
        suite = BenchmarkSuite.create_reasoning_benchmark()
        hard = suite.filter_by_difficulty("hard")
        assert all(c.difficulty == "hard" for c in hard)
