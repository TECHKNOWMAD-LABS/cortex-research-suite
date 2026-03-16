"""ArenaConfig dataclass — reads ARENA.md YAML frontmatter for skill evolution.

Provides structured configuration for the autoresearch evolution loop,
including fitness metrics, experiment budgets, mutation strategies,
browser arena settings, and trilogy integration fields.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ArenaConfig:
    """Configuration for a skill's evolution arena."""

    skill_name: str = ""
    skill_dir: str = ""

    # Fitness metric
    primary_metric: str = "composite_score"
    formula: str = (
        "correctness×0.25 + reasoning_depth×0.20 + completeness×0.25 + hallucination_risk×0.20 + coherence×0.10"
    )
    improvement_threshold: float = 0.05
    regression_threshold: float = 0.10

    # Experiment budget
    eval_budget_seconds: int = 30
    eval_dataset: str = ""
    eval_n_items: int = 50
    max_experiments_per_generation: int = 12

    # Mutation strategies
    allowed_mutations: list[str] = field(
        default_factory=lambda: [
            "instruction_clarity",
            "example_replacement",
            "output_schema_tightening",
            "edge_case_handling",
            "reasoning_scaffolding",
        ]
    )

    # Transfer test
    transfer_dataset: str = ""
    transfer_n_items: int = 30
    transfer_pass_threshold: float = -0.15

    # Browser arena
    browser_demo_enabled: bool = True
    demo_eval_dimensions: list[str] = field(
        default_factory=lambda: [
            "correctness",
            "reasoning_depth",
            "completeness",
            "hallucination_risk",
            "coherence",
        ]
    )

    # Trilogy integration
    mindspider_feed_enabled: bool = False
    bettafish_engine_type: str | None = None
    mirofish_simulation_enabled: bool = False
    counterfactual_injection_points: list[str] = field(default_factory=list)

    # Notes
    notes: str = "Standard skill improvement via instruction clarity and example quality."

    @classmethod
    def load(cls, skill_dir: str | Path) -> ArenaConfig:
        """Load ArenaConfig from a skill directory's ARENA.md."""
        skill_dir = Path(skill_dir)
        arena_path = skill_dir / "ARENA.md"
        config = cls(skill_name=skill_dir.name, skill_dir=str(skill_dir))

        if not arena_path.exists():
            config.eval_dataset = f"datasets/synthetic/{skill_dir.name}/shard_000.json"
            config.transfer_dataset = f"datasets/synthetic/{skill_dir.name}/shard_001.json"
            return config

        text = arena_path.read_text()
        _kv = _parse_yaml_like(text)

        # Map parsed values to fields
        config.primary_metric = _kv.get("primary", config.primary_metric)
        config.formula = _kv.get("formula", config.formula)
        config.improvement_threshold = float(_kv.get("improvement_threshold", config.improvement_threshold))
        config.regression_threshold = float(_kv.get("regression_threshold", config.regression_threshold))
        config.eval_budget_seconds = int(_kv.get("eval_budget_seconds", config.eval_budget_seconds))
        config.eval_dataset = _kv.get("eval_dataset", f"datasets/synthetic/{skill_dir.name}/shard_000.json")
        config.eval_n_items = int(_kv.get("eval_n_items", config.eval_n_items))
        config.max_experiments_per_generation = int(
            _kv.get("max_experiments_per_generation", config.max_experiments_per_generation)
        )
        config.transfer_dataset = _kv.get("transfer_dataset", f"datasets/synthetic/{skill_dir.name}/shard_001.json")
        config.transfer_n_items = int(_kv.get("transfer_n_items", config.transfer_n_items))
        config.transfer_pass_threshold = float(_kv.get("transfer_pass_threshold", config.transfer_pass_threshold))
        config.browser_demo_enabled = _kv.get("browser_demo_enabled", "true").lower() == "true"
        config.mindspider_feed_enabled = _kv.get("mindspider_feed_enabled", "false").lower() == "true"
        config.mirofish_simulation_enabled = _kv.get("mirofish_simulation_enabled", "false").lower() == "true"
        bet = _kv.get("bettafish_engine_type", "null")
        config.bettafish_engine_type = None if bet in ("null", "None", "") else bet
        config.notes = _kv.get("notes", config.notes)

        # Parse list fields
        mutations_raw = _kv.get("allowed_mutations", "")
        if mutations_raw:
            config.allowed_mutations = _parse_yaml_list(text, "allowed_mutations")
        dims_raw = _kv.get("demo_eval_dimensions", "")
        if dims_raw:
            config.demo_eval_dimensions = [d.strip().strip("'\"") for d in dims_raw.strip("[]").split(",") if d.strip()]

        return config

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "primary_metric": self.primary_metric,
            "formula": self.formula,
            "improvement_threshold": self.improvement_threshold,
            "regression_threshold": self.regression_threshold,
            "eval_budget_seconds": self.eval_budget_seconds,
            "eval_dataset": self.eval_dataset,
            "eval_n_items": self.eval_n_items,
            "max_experiments_per_generation": self.max_experiments_per_generation,
            "allowed_mutations": self.allowed_mutations,
            "transfer_dataset": self.transfer_dataset,
            "transfer_n_items": self.transfer_n_items,
            "transfer_pass_threshold": self.transfer_pass_threshold,
            "browser_demo_enabled": self.browser_demo_enabled,
            "demo_eval_dimensions": self.demo_eval_dimensions,
            "mindspider_feed_enabled": self.mindspider_feed_enabled,
            "bettafish_engine_type": self.bettafish_engine_type,
            "mirofish_simulation_enabled": self.mirofish_simulation_enabled,
            "counterfactual_injection_points": self.counterfactual_injection_points,
            "notes": self.notes,
        }

    def to_browser_json(self) -> str:
        """Serialise for skill_arena_demo.html consumption."""
        return json.dumps(self.to_dict(), indent=2)


def _parse_yaml_like(text: str) -> dict[str, str]:
    """Simple YAML-like key: value parser (no full YAML dependency)."""
    kv: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#") or line.startswith("-") or not line:
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val:
                kv[key] = val
    return kv


def _parse_yaml_list(text: str, key: str) -> list[str]:
    """Extract a YAML list block (items prefixed with '  - ')."""
    items: list[str] = []
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{key}:"):
            in_block = True
            continue
        if in_block:
            if stripped.startswith("- "):
                items.append(stripped[2:].strip())
            elif stripped and not stripped.startswith("#"):
                break
    return items
