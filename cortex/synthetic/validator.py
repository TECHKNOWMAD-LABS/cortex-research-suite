"""Dataset validation engine.

Ensures generated datasets meet quality standards:
- Deduplication via content hashing
- Prompt length constraints
- Schema compliance
- Statistical distribution checks
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from cortex.synthetic.base_generator import GeneratedPrompt


@dataclass
class ValidationReport:
    """Results of dataset validation."""

    total: int = 0
    valid: int = 0
    duplicates: int = 0
    too_short: int = 0
    too_long: int = 0
    empty: int = 0
    category_distribution: dict[str, int] = field(default_factory=dict)
    difficulty_distribution: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.valid / self.total if self.total > 0 else 0.0

    @property
    def is_valid(self) -> bool:
        return self.pass_rate >= 0.8 and len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "valid": self.valid,
            "pass_rate": round(self.pass_rate, 4),
            "duplicates": self.duplicates,
            "too_short": self.too_short,
            "too_long": self.too_long,
            "empty": self.empty,
            "category_distribution": self.category_distribution,
            "difficulty_distribution": self.difficulty_distribution,
            "errors": self.errors,
        }


class DatasetValidator:
    """Validates synthetic datasets for quality and correctness."""

    def __init__(
        self,
        min_length: int = 10,
        max_length: int = 10_000,
        dedup: bool = True,
    ) -> None:
        self._min_length = min_length
        self._max_length = max_length
        self._dedup = dedup

    def validate(self, prompts: list[GeneratedPrompt]) -> tuple[list[GeneratedPrompt], ValidationReport]:
        """Validate and filter a list of generated prompts.

        Returns:
            Tuple of (valid_prompts, validation_report).
        """
        report = ValidationReport(total=len(prompts))
        seen_fingerprints: set[str] = set()
        valid: list[GeneratedPrompt] = []

        for p in prompts:
            # Empty check
            if not p.prompt or not p.prompt.strip():
                report.empty += 1
                continue

            # Length checks
            if len(p.prompt) < self._min_length:
                report.too_short += 1
                continue
            if len(p.prompt) > self._max_length:
                report.too_long += 1
                continue

            # Deduplication
            if self._dedup:
                fp = p.fingerprint
                if fp in seen_fingerprints:
                    report.duplicates += 1
                    continue
                seen_fingerprints.add(fp)

            valid.append(p)

        report.valid = len(valid)
        report.category_distribution = dict(Counter(p.category for p in valid))
        report.difficulty_distribution = dict(Counter(p.difficulty for p in valid))

        # Distribution warnings
        if report.category_distribution:
            max_cat = max(report.category_distribution.values())
            min_cat = min(report.category_distribution.values())
            if max_cat > 0 and min_cat / max_cat < 0.1:
                report.errors.append(f"Severe category imbalance: {report.category_distribution}")

        return valid, report
