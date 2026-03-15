"""Base generator interface for synthetic data creation.

All generators extend BaseGenerator and implement the generate() method.
Supports seeded randomness for reproducibility.
"""

from __future__ import annotations

import hashlib
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GeneratedPrompt:
    """A single generated evaluation prompt."""

    prompt: str
    category: str
    difficulty: str = "medium"  # easy, medium, hard, adversarial
    expected_structure: str = ""
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Content-addressable hash for deduplication."""
        return hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "category": self.category,
            "difficulty": self.difficulty,
            "expected_structure": self.expected_structure,
            "tags": list(self.tags),
            "fingerprint": self.fingerprint,
            "metadata": self.metadata,
        }


class BaseGenerator(ABC):
    """Abstract base for all synthetic data generators."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._seed = seed

    @abstractmethod
    def generate(self, n: int) -> list[GeneratedPrompt]:
        """Generate n synthetic prompts."""

    @property
    @abstractmethod
    def category(self) -> str:
        """Generator category identifier."""

    def _pick(self, items: list[Any]) -> Any:
        """Thread-safe random choice using instance RNG."""
        return self._rng.choice(items)

    def _pick_n(self, items: list[Any], n: int) -> list[Any]:
        """Pick n items with replacement."""
        return [self._pick(items) for _ in range(n)]

    def _shuffle(self, items: list[Any]) -> list[Any]:
        """Return a shuffled copy."""
        copy = list(items)
        self._rng.shuffle(copy)
        return copy

    def _weighted_difficulty(self) -> str:
        """Return difficulty level with realistic distribution."""
        return self._rng.choices(
            ["easy", "medium", "hard"],
            weights=[0.2, 0.5, 0.3],
            k=1,
        )[0]
