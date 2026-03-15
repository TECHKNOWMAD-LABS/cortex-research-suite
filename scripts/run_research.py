#!/usr/bin/env python3
"""Run automated research on a topic using multi-agent pipeline.

Usage:
    python scripts/run_research.py "topic" [--mock] [--output PATH]

Executes the full research engine: multi-agent pipeline + quality evaluation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cortex.agents.research_engine import ResearchEngine
from cortex.models.claude_provider import ClaudeProvider, MockProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Run automated research")
    parser.add_argument("topic", type=str, help="Research topic")
    parser.add_argument("--mock", action="store_true", help="Use mock provider")
    parser.add_argument("--output", type=str, default="experiments/research_reports", help="Output directory")
    parser.add_argument("--min-quality", type=float, default=0.6, help="Minimum quality threshold (0-1)")
    args = parser.parse_args()

    if args.mock:
        provider = MockProvider([
            "Research findings: The topic has significant implications across multiple domains.",
            "Critique: The analysis lacks quantitative evidence.",
            "Strategy: Focus on high-impact areas first.",
            "Synthesis: Comprehensive report combining all perspectives.",
        ])
    else:
        provider = ClaudeProvider()

    engine = ResearchEngine(provider, min_quality=args.min_quality)

    print(f"Researching: {args.topic}")
    print("Running multi-agent pipeline (researcher -> critic -> strategist -> synthesizer)...")

    report = engine.research(args.topic)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = args.topic[:50].replace(" ", "_").replace("/", "_")
    output_path = output_dir / f"{safe_name}.json"
    engine.save_report(report, output_path)

    print(f"\nResearch Complete")
    print(f"  Stages: {len(report.pipeline_result.stages)}")
    print(f"  Tokens: {report.pipeline_result.total_tokens}")
    print(f"  Latency: {report.pipeline_result.total_latency_ms:.0f}ms")
    if report.quality_score:
        print(f"  Quality: {report.quality_score.normalized:.2f}/1.0")
        print(f"    Accuracy: {report.quality_score.accuracy}/5")
        print(f"    Reasoning: {report.quality_score.reasoning}/5")
        print(f"    Completeness: {report.quality_score.completeness}/5")
    print(f"\n  Report saved to: {output_path}")


if __name__ == "__main__":
    main()
