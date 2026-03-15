#!/usr/bin/env python3
"""Run benchmark suites against skills.

Usage:
    python scripts/run_benchmark.py [--suite reasoning|strategy] [--max-items N]

Runs the specified benchmark suite and saves results.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cortex.evaluation.benchmarks import BenchmarkSuite
from cortex.evaluation.runner import EvaluationRunner
from cortex.evaluation.judge import LLMJudge
from cortex.evaluation.regression import RegressionDetector
from cortex.models.claude_provider import ClaudeProvider, MockProvider
from cortex.telemetry.metrics import MetricsCollector
from cortex.experiments import ExperimentTracker, Experiment
from cortex.utils.io import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluation benchmarks")
    parser.add_argument("--suite", type=str, default="reasoning", choices=["reasoning", "strategy"])
    parser.add_argument("--max-items", type=int, default=5, help="Max items to evaluate")
    parser.add_argument("--mock", action="store_true", help="Use mock provider (no API calls)")
    parser.add_argument("--output", type=str, default="experiments", help="Output directory")
    args = parser.parse_args()

    # Create benchmark suite
    if args.suite == "reasoning":
        suite = BenchmarkSuite.create_reasoning_benchmark()
    else:
        suite = BenchmarkSuite.create_strategy_benchmark()

    # Provider
    if args.mock:
        provider = MockProvider(["This is a detailed mock analysis with multiple points of evidence."])
    else:
        provider = ClaudeProvider()

    # Components
    judge = LLMJudge(provider)
    metrics = MetricsCollector(db_path=f"{args.output}/metrics.db")
    runner = EvaluationRunner(provider, judge, metrics)
    tracker = ExperimentTracker(args.output)
    regression = RegressionDetector(f"{args.output}/baselines")

    # Track experiment
    experiment = Experiment(
        name=f"benchmark_{args.suite}",
        skill="research_skill",
        dataset=suite.name,
        model="claude" if not args.mock else "mock",
    )

    # Run evaluation
    print(f"Running {suite.name} benchmark ({suite.size} cases, max {args.max_items})...")
    skill_prompt = "You are an expert analyst. Produce thorough, well-reasoned analysis."
    report = runner.evaluate(
        skill_name="research_skill",
        skill_prompt=skill_prompt,
        dataset=suite.to_dataset(),
        dataset_name=suite.name,
        max_items=args.max_items,
    )

    # Complete experiment
    experiment.complete(report.mean_scores)
    tracker.log_experiment(experiment)

    # Check regression
    regressions = regression.check("research_skill", report.mean_scores)
    has_regression = any(r.regressed for r in regressions)

    # Save report
    runner.save_report(report, f"{args.output}/{suite.name}_report.json")

    # Print results
    print(f"\nBenchmark Results: {suite.name}")
    print(f"  Items evaluated: {report.total}")
    for metric, value in report.mean_scores.items():
        print(f"  {metric}: {value}")
    print(f"  Mean latency: {report.mean_latency_ms}ms")

    if regressions:
        print(f"\nRegression Check:")
        for r in regressions:
            status = "REGRESSED" if r.regressed else "OK"
            print(f"  {r.metric}: {r.baseline:.4f} -> {r.current:.4f} ({r.delta:+.4f}) [{status}]")

    if has_regression:
        print("\nWARNING: Performance regressions detected!")
        sys.exit(1)


if __name__ == "__main__":
    main()
