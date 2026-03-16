#!/usr/bin/env python3
"""LLM-as-Judge evaluation with 5-dimension rubric scoring.

Uses the Anthropic SDK to score skill outputs on 5 dimensions:
  correctness, reasoning_depth, completeness, hallucination_risk, coherence

Reads rubrics from skills/skill-test-harness/rubrics/{skill}.yaml.
Compares against benchmarks/baselines/{skill}.json.

Usage:
    python eval_judge.py --skill security-audit --dataset datasets/synthetic/security-audit/shard_000.json
    python eval_judge.py --skill de-slop --dataset data.json --compare-baseline
    python eval_judge.py --skill agent-orchestrator --dataset data.json --offline
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

# ---------------------------------------------------------------------------
# Dimensions and weights
# ---------------------------------------------------------------------------

DIMENSIONS = (
    "correctness",
    "reasoning_depth",
    "completeness",
    "hallucination_risk",
    "coherence",
)

DEFAULT_WEIGHTS: dict[str, float] = {
    "correctness": 0.25,
    "reasoning_depth": 0.20,
    "completeness": 0.25,
    "hallucination_risk": 0.20,
    "coherence": 0.10,
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class RubricScore:
    """Individual evaluation result for one prompt/response pair."""

    prompt_id: str
    correctness: float = 0.0
    reasoning_depth: float = 0.0
    completeness: float = 0.0
    hallucination_risk: float = 0.0
    coherence: float = 0.0
    raw_response: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def overall(self) -> float:
        """Weighted overall score on 0-5 scale."""
        weights = self.metadata.get("weights", DEFAULT_WEIGHTS)
        return round(sum(weights[d] * getattr(self, d) for d in DIMENSIONS), 4)

    @property
    def normalized(self) -> float:
        """Overall score normalized to 0-1."""
        return round(self.overall / 5.0, 4)

    def to_dict(self) -> dict[str, Any]:
        result = {d: getattr(self, d) for d in DIMENSIONS}
        result["overall"] = self.overall
        result["normalized"] = self.normalized
        result["prompt_id"] = self.prompt_id
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class BenchmarkResult:
    """Aggregate result for a full benchmark run."""

    skill: str
    timestamp: str
    scores: list[dict[str, Any]]
    dimension_averages: dict[str, float]
    overall_average: float
    sample_count: int
    rubric_path: str = ""
    baseline_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill": self.skill,
            "timestamp": self.timestamp,
            "sample_count": self.sample_count,
            "overall_average": self.overall_average,
            "dimension_averages": self.dimension_averages,
            "scores": self.scores,
            "rubric_path": self.rubric_path,
            "baseline_path": self.baseline_path,
        }


# ---------------------------------------------------------------------------
# Rubric loader
# ---------------------------------------------------------------------------


def load_rubric(skill: str) -> dict[str, Any]:
    """Load skill-specific rubric from skills/skill-test-harness/rubrics/{skill}.yaml."""
    rubric_path = REPO_ROOT / "skills" / "skill-test-harness" / "rubrics" / f"{skill}.yaml"
    if not rubric_path.exists():
        return {"weights": DEFAULT_WEIGHTS, "skill_context": "", "rubric_path": ""}

    try:
        import yaml

        data = yaml.safe_load(rubric_path.read_text()) or {}
    except ImportError:
        # Fallback: simple YAML-like parsing for weight overrides
        data = {}
        text = rubric_path.read_text()
        for line in text.splitlines():
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key in DIMENSIONS:
                    try:
                        data.setdefault("weights", {})[key] = float(val)
                    except ValueError:
                        pass
                elif key == "skill_context":
                    data["skill_context"] = val

    weights = DEFAULT_WEIGHTS.copy()
    if "weights" in data:
        for dim in DIMENSIONS:
            if dim in data["weights"]:
                weights[dim] = float(data["weights"][dim])
        # Re-normalize weights to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

    return {
        "weights": weights,
        "skill_context": data.get("skill_context", ""),
        "rubric_path": str(rubric_path),
    }


# ---------------------------------------------------------------------------
# Baseline loader
# ---------------------------------------------------------------------------


def load_baseline(skill: str) -> dict[str, Any] | None:
    """Load baseline from benchmarks/baselines/{skill}.json."""
    baseline_path = REPO_ROOT / "benchmarks" / "baselines" / f"{skill}.json"
    if not baseline_path.exists():
        return None
    return json.loads(baseline_path.read_text())


# ---------------------------------------------------------------------------
# Judge rubric prompt
# ---------------------------------------------------------------------------

JUDGE_RUBRIC = """You are an expert evaluator for AI skill outputs. Score the following response on a 1-5 scale for each dimension.

## Dimensions

1. **Correctness** (1-5): Factual accuracy. Are claims verifiable and precise?
2. **Reasoning Depth** (1-5): Logical structure and depth. Are inferences valid, well-supported, and non-trivial?
3. **Completeness** (1-5): Coverage. Are all key aspects of the prompt addressed?
4. **Hallucination Risk** (1-5): Groundedness. 5 = fully grounded in evidence, 1 = contains fabricated claims.
5. **Coherence** (1-5): Clarity and organization. Is the response well-structured and readable?

{skill_context}

## Prompt
{prompt}

## Response
{response}

## Instructions
Score each dimension 1-5. Respond with ONLY valid JSON:
{{"correctness": <int>, "reasoning_depth": <int>, "completeness": <int>, "hallucination_risk": <int>, "coherence": <int>}}
"""


# ---------------------------------------------------------------------------
# Scoring engines
# ---------------------------------------------------------------------------


def _prompt_id(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()[:12]


def score_offline(prompt: str, response: str, weights: dict[str, float] | None = None) -> RubricScore:
    """Deterministic offline scoring for CI — heuristic-based."""
    pid = _prompt_id(prompt)
    words = response.split()
    word_count = len(words)
    unique_ratio = len(set(w.lower() for w in words)) / max(word_count, 1)
    has_structure = bool(re.search(r"(\n#+\s|\n-\s|\n\d+\.)", response))
    sentence_count = len(re.findall(r"[.!?]+", response))

    correctness = min(5.0, 2.0 + unique_ratio * 3.0)
    reasoning_depth = min(5.0, 2.0 + (sentence_count / max(word_count / 50, 1)) * 1.5 + (1.0 if has_structure else 0.0))
    completeness = min(5.0, 1.0 + min(word_count, 500) / 125.0)
    hallucination_risk = min(5.0, 3.0 + unique_ratio)
    coherence = min(5.0, 2.5 + (1.0 if has_structure else 0.0) + unique_ratio)

    meta: dict[str, Any] = {"method": "offline_heuristic"}
    if weights:
        meta["weights"] = weights

    return RubricScore(
        prompt_id=pid,
        correctness=round(correctness, 2),
        reasoning_depth=round(reasoning_depth, 2),
        completeness=round(completeness, 2),
        hallucination_risk=round(hallucination_risk, 2),
        coherence=round(coherence, 2),
        metadata=meta,
    )


def score_with_anthropic(
    prompt: str,
    response: str,
    skill_context: str = "",
    weights: dict[str, float] | None = None,
) -> RubricScore:
    """Score using the Anthropic SDK directly."""
    pid = _prompt_id(prompt)

    try:
        import anthropic

        client = anthropic.Anthropic()
    except ImportError:
        print("Warning: anthropic SDK not installed, falling back to offline", file=sys.stderr)
        return score_offline(prompt, response, weights)
    except anthropic.AuthenticationError:
        print("Warning: ANTHROPIC_API_KEY not set, falling back to offline", file=sys.stderr)
        return score_offline(prompt, response, weights)

    ctx = f"\n## Skill Context\n{skill_context}\n" if skill_context else ""
    judge_prompt = JUDGE_RUBRIC.format(prompt=prompt[:4000], response=response[:8000], skill_context=ctx)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            temperature=0.1,
            messages=[{"role": "user", "content": judge_prompt}],
        )
        content = message.content[0].text.strip()
    except Exception as e:
        print(f"Warning: API call failed ({e}), falling back to offline", file=sys.stderr)
        return score_offline(prompt, response, weights)

    json_match = re.search(r"\{[^}]+\}", content)
    if not json_match:
        return RubricScore(prompt_id=pid, raw_response=content, metadata={"parse_error": "no JSON found"})

    try:
        data = json.loads(json_match.group())
        meta: dict[str, Any] = {"method": "anthropic_sdk"}
        if weights:
            meta["weights"] = weights
        return RubricScore(
            prompt_id=pid,
            correctness=float(data.get("correctness", 0)),
            reasoning_depth=float(data.get("reasoning_depth", 0)),
            completeness=float(data.get("completeness", 0)),
            hallucination_risk=float(data.get("hallucination_risk", 0)),
            coherence=float(data.get("coherence", 0)),
            raw_response=content,
            metadata=meta,
        )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return RubricScore(prompt_id=pid, raw_response=content, metadata={"parse_error": str(e)})


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def run_benchmark(
    skill: str,
    dataset: list[dict[str, str]],
    *,
    offline: bool = False,
    output_dir: str | Path = "benchmarks/results",
) -> BenchmarkResult:
    """Run a full benchmark evaluation on a dataset."""
    rubric = load_rubric(skill)
    weights = rubric["weights"]
    skill_context = rubric.get("skill_context", "")

    scores: list[RubricScore] = []
    for item in dataset:
        prompt = item.get("prompt", "")
        response = item.get("response", item.get("expected_structure", ""))
        if offline:
            score = score_offline(prompt, response, weights)
        else:
            score = score_with_anthropic(prompt, response, skill_context, weights)
        scores.append(score)

    dim_avgs: dict[str, float] = {}
    for d in DIMENSIONS:
        vals = [getattr(s, d) for s in scores]
        dim_avgs[d] = round(sum(vals) / max(len(vals), 1), 4)

    overall_avg = round(sum(s.normalized for s in scores) / max(len(scores), 1), 4)

    ts = time.strftime("%Y%m%d_%H%M%S")
    result = BenchmarkResult(
        skill=skill,
        timestamp=ts,
        scores=[s.to_dict() for s in scores],
        dimension_averages=dim_avgs,
        overall_average=overall_avg,
        sample_count=len(scores),
        rubric_path=rubric.get("rubric_path", ""),
    )

    out = Path(output_dir) / skill
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{ts}.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2))
    return result


# ---------------------------------------------------------------------------
# Baseline comparison
# ---------------------------------------------------------------------------


def compare_baseline(result: BenchmarkResult, skill: str, threshold: float = 0.10) -> dict[str, Any]:
    """Compare benchmark result against the stored baseline."""
    baseline = load_baseline(skill)
    comparison: dict[str, Any] = {"has_baseline": baseline is not None}

    if baseline is None:
        comparison["status"] = "no_baseline"
        comparison["message"] = f"No baseline found at benchmarks/baselines/{skill}.json"
        return comparison

    baseline_score = baseline.get("overall_average", 0)
    delta = result.overall_average - baseline_score
    comparison["baseline_score"] = baseline_score
    comparison["current_score"] = result.overall_average
    comparison["delta"] = round(delta, 4)
    comparison["threshold"] = threshold

    # Per-dimension comparison
    dim_deltas: dict[str, float] = {}
    baseline_dims = baseline.get("dimension_averages", {})
    for dim in DIMENSIONS:
        b = baseline_dims.get(dim, 0)
        c = result.dimension_averages.get(dim, 0)
        dim_deltas[dim] = round(c - b, 4)
    comparison["dimension_deltas"] = dim_deltas

    if delta < -threshold:
        comparison["status"] = "regression"
        comparison["message"] = f"REGRESSION: score dropped {abs(delta):.4f} (threshold: {threshold})"
    else:
        comparison["status"] = "pass"
        comparison["message"] = f"No regression (delta: {delta:+.4f})"

    return comparison


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM-as-Judge 5-dimension evaluation (Anthropic SDK)")
    parser.add_argument("--skill", required=True, help="Skill name being evaluated")
    parser.add_argument("--dataset", required=True, type=Path, help="JSON/JSONL dataset path")
    parser.add_argument("--output-dir", default="benchmarks/results", help="Output directory")
    parser.add_argument("--offline", action="store_true", help="Use offline heuristic scoring (no API)")
    parser.add_argument("--compare-baseline", action="store_true", help="Compare against stored baseline")
    parser.add_argument("--threshold", type=float, default=0.10, help="Regression threshold (default: 0.10)")
    args = parser.parse_args()

    dataset_path = args.dataset
    if not dataset_path.exists():
        print(f"Error: dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    # Load dataset — supports both JSON array and JSONL
    text = dataset_path.read_text().strip()
    if text.startswith("["):
        dataset = json.loads(text)
    else:
        dataset = [json.loads(line) for line in text.splitlines() if line.strip()]

    if not dataset:
        print("Error: empty dataset", file=sys.stderr)
        return 1

    print(f"Evaluating: {args.skill} ({len(dataset)} items)")
    print(f"Mode: {'offline heuristic' if args.offline else 'Anthropic SDK'}")
    print("=" * 50)

    result = run_benchmark(args.skill, dataset, offline=args.offline, output_dir=args.output_dir)

    print(f"\nSkill: {result.skill}")
    print(f"Samples: {result.sample_count}")
    print(f"Overall: {result.overall_average:.4f}")
    for dim, avg in result.dimension_averages.items():
        print(f"  {dim}: {avg:.2f}/5")

    if args.compare_baseline:
        print(f"\n{'=' * 50}")
        print("Baseline comparison:")
        comparison = compare_baseline(result, args.skill, args.threshold)
        if comparison["has_baseline"]:
            print(f"  Baseline: {comparison['baseline_score']:.4f}")
            print(f"  Current:  {comparison['current_score']:.4f}")
            print(f"  Delta:    {comparison['delta']:+.4f}")
            for dim, delta in comparison.get("dimension_deltas", {}).items():
                indicator = "↑" if delta >= 0 else "↓"
                print(f"    {dim}: {delta:+.4f} {indicator}")
            print(f"\n  {comparison['message']}")
            if comparison["status"] == "regression":
                return 1
        else:
            print(f"  {comparison['message']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
