"""Evaluation Lab — LLM-as-judge scoring, benchmarks, and regression testing.

Provides automated evaluation of skill outputs using structured rubrics,
benchmark suites, and regression detection across versions.
"""

from cortex.evaluation.judge import LLMJudge, JudgeScore
from cortex.evaluation.runner import EvaluationRunner, EvalResult
from cortex.evaluation.regression import RegressionDetector
from cortex.evaluation.benchmarks import BenchmarkSuite

__all__ = [
    "LLMJudge",
    "JudgeScore",
    "EvaluationRunner",
    "EvalResult",
    "RegressionDetector",
    "BenchmarkSuite",
]
