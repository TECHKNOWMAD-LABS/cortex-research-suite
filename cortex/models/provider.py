"""Abstract model provider interface.

All LLM providers implement this interface for uniform skill execution.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelResponse:
    """Structured response from a model provider."""

    content: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return len(self.content.strip()) == 0


class ModelProvider(ABC):
    """Abstract base for all model providers."""

    @abstractmethod
    def generate(self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 4096) -> ModelResponse:
        """Generate a response from the model."""

    def generate_json(self, prompt: str, *, temperature: float = 0.1, max_tokens: int = 4096) -> ModelResponse:
        """Generate a JSON response. Appends JSON instruction to prompt."""
        json_prompt = prompt.rstrip() + "\n\nRespond with valid JSON only. No markdown fences."
        return self.generate(json_prompt, temperature=temperature, max_tokens=max_tokens)

    @staticmethod
    def _measure_latency(start: float) -> float:
        return round((time.time() - start) * 1000, 2)
