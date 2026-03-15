#!/usr/bin/env python3
"""Generate synthetic evaluation datasets.

Usage:
    python scripts/generate_dataset.py [--count N] [--categories CAT1,CAT2] [--seed SEED]

Generates datasets across all categories by default.
Output goes to datasets/ directory with automatic sharding.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cortex.synthetic import (
    ReasoningGenerator,
    ResearchGenerator,
    StrategyGenerator,
    DomainGenerator,
    AdversarialGenerator,
)
from cortex.pipelines.dataset_pipeline import DatasetPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic evaluation datasets")
    parser.add_argument("--count", type=int, default=100, help="Prompts per category (default: 100)")
    parser.add_argument(
        "--categories",
        type=str,
        default="reasoning,research,strategy,healthcare,adversarial",
        help="Comma-separated list of categories",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="datasets", help="Output directory")
    parser.add_argument("--shard-size", type=int, default=10000, help="Prompts per shard file")
    args = parser.parse_args()

    categories = [c.strip() for c in args.categories.split(",")]

    # Build generator list
    generator_map = {
        "reasoning": lambda: ReasoningGenerator(seed=args.seed),
        "research": lambda: ResearchGenerator(seed=args.seed),
        "strategy": lambda: StrategyGenerator(seed=args.seed),
        "healthcare": lambda: DomainGenerator(domain="healthcare", seed=args.seed),
        "finance": lambda: DomainGenerator(domain="finance", seed=args.seed),
        "technology": lambda: DomainGenerator(domain="technology", seed=args.seed),
        "policy": lambda: DomainGenerator(domain="policy", seed=args.seed),
        "adversarial": lambda: AdversarialGenerator(seed=args.seed),
    }

    generators = []
    for cat in categories:
        if cat not in generator_map:
            print(f"Unknown category: {cat}. Available: {list(generator_map)}")
            sys.exit(1)
        generators.append((generator_map[cat](), args.count))

    # Run pipeline
    pipeline = DatasetPipeline(
        output_dir=args.output,
        shard_size=args.shard_size,
    )
    report = pipeline.run(generators)

    print(f"\nDataset Generation Complete")
    print(f"  Generated: {report.total_generated}")
    print(f"  Valid:     {report.total_valid}")
    print(f"  Shards:    {report.shards_created}")
    print(f"  Duration:  {report.duration_seconds:.1f}s")

    if report.validation_report:
        vr = report.validation_report
        print(f"  Pass rate: {vr.pass_rate:.1%}")
        if vr.duplicates > 0:
            print(f"  Duplicates removed: {vr.duplicates}")
        print(f"  Categories: {vr.category_distribution}")


if __name__ == "__main__":
    main()
