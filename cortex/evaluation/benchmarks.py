"""Benchmark suite management for standardized skill evaluation.

Defines reusable benchmark suites with fixed prompts and expected
quality thresholds for consistent cross-version comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cortex.utils.io import read_json, write_json


@dataclass
class BenchmarkCase:
    """A single benchmark evaluation case."""

    prompt: str
    category: str
    difficulty: str = "medium"
    min_score: float = 3.0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "category": self.category,
            "difficulty": self.difficulty,
            "min_score": self.min_score,
            "tags": self.tags,
        }


class BenchmarkSuite:
    """Collection of benchmark cases for systematic skill evaluation.

    Benchmarks are immutable evaluation sets that provide consistent
    measurement across skill versions.
    """

    def __init__(self, name: str, cases: list[BenchmarkCase] | None = None) -> None:
        self.name = name
        self._cases = cases or []

    def add_case(self, case: BenchmarkCase) -> None:
        self._cases.append(case)

    @property
    def cases(self) -> list[BenchmarkCase]:
        return list(self._cases)

    @property
    def size(self) -> int:
        return len(self._cases)

    def filter_by_category(self, category: str) -> list[BenchmarkCase]:
        return [c for c in self._cases if c.category == category]

    def filter_by_difficulty(self, difficulty: str) -> list[BenchmarkCase]:
        return [c for c in self._cases if c.difficulty == difficulty]

    def to_dataset(self) -> list[dict[str, Any]]:
        """Convert to evaluation dataset format."""
        return [{"prompt": c.prompt, "category": c.category, "difficulty": c.difficulty} for c in self._cases]

    def save(self, path: str | Path) -> None:
        write_json(path, {"name": self.name, "cases": [c.to_dict() for c in self._cases]})

    @classmethod
    def load(cls, path: str | Path) -> BenchmarkSuite:
        data = read_json(path)
        cases = [
            BenchmarkCase(
                prompt=c["prompt"],
                category=c["category"],
                difficulty=c.get("difficulty", "medium"),
                min_score=c.get("min_score", 3.0),
                tags=c.get("tags", []),
            )
            for c in data.get("cases", [])
        ]
        return cls(name=data.get("name", "unnamed"), cases=cases)

    @classmethod
    def create_reasoning_benchmark(cls) -> BenchmarkSuite:
        """Factory: Create standard reasoning benchmark suite."""
        cases = [
            BenchmarkCase(
                prompt="Explain the second-order effects of widespread AI automation on labor markets, education systems, and social mobility. Trace at least three causal chains.",
                category="reasoning",
                difficulty="hard",
                min_score=3.5,
                tags=["multi-step", "causal"],
            ),
            BenchmarkCase(
                prompt="A company discovers that increasing prices by 10% leads to a 5% decrease in unit sales but a 15% increase in customer support costs. Analyze whether the price increase is beneficial, considering direct and indirect effects.",
                category="reasoning",
                difficulty="medium",
                min_score=3.0,
                tags=["quantitative", "business"],
            ),
            BenchmarkCase(
                prompt="If quantum computers become commercially viable within 5 years, what are the cascading implications for cybersecurity, cryptocurrency, pharmaceutical R&D, and international security? Construct a dependency graph.",
                category="reasoning",
                difficulty="hard",
                min_score=3.5,
                tags=["counterfactual", "multi-domain"],
            ),
            BenchmarkCase(
                prompt="Evaluate the following argument: 'Since remote work increases productivity and reduces office costs, all companies should switch to fully remote work.' Identify logical gaps and unstated assumptions.",
                category="reasoning",
                difficulty="medium",
                min_score=3.0,
                tags=["critical-thinking", "logic"],
            ),
            BenchmarkCase(
                prompt="Design a decision framework for a hospital choosing between investing in AI diagnostics, expanding telemedicine, or hiring more specialists. Define criteria, weights, and evaluation methodology.",
                category="reasoning",
                difficulty="hard",
                min_score=3.5,
                tags=["decision-framework", "healthcare"],
            ),
        ]
        return cls(name="reasoning_benchmark_v1", cases=cases)

    @classmethod
    def create_strategy_benchmark(cls) -> BenchmarkSuite:
        """Factory: Create standard strategy benchmark suite."""
        cases = [
            BenchmarkCase(
                prompt="A mid-stage SaaS company faces increasing competition from AI-native startups. Propose a 3-year strategic plan addressing product differentiation, talent acquisition, and market positioning.",
                category="strategy",
                difficulty="hard",
                min_score=3.5,
                tags=["competitive", "planning"],
            ),
            BenchmarkCase(
                prompt="Analyze the strategic implications of the EU AI Act on US-based AI companies. Identify regulatory arbitrage opportunities and compliance strategies.",
                category="strategy",
                difficulty="medium",
                min_score=3.0,
                tags=["regulatory", "geopolitical"],
            ),
            BenchmarkCase(
                prompt="Map the competitive landscape of the electric vehicle charging infrastructure market. Identify potential moats, switching costs, and winner-take-all dynamics.",
                category="strategy",
                difficulty="medium",
                min_score=3.0,
                tags=["market-analysis", "infrastructure"],
            ),
        ]
        return cls(name="strategy_benchmark_v1", cases=cases)
