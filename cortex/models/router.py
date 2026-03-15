"""Intelligent model routing based on task type.

Routes tasks to optimal models based on complexity, cost, and capability.
"""

from __future__ import annotations

from cortex.config.settings import get_settings
from cortex.models.provider import ModelProvider, ModelResponse
from cortex.models.claude_provider import ClaudeProvider


# Model tier mapping: task_type -> model identifier
_DEFAULT_ROUTES: dict[str, str] = {
    "reasoning": "claude-sonnet-4-20250514",
    "evaluation": "claude-sonnet-4-20250514",
    "extraction": "claude-haiku-4-5-20251001",
    "generation": "claude-sonnet-4-20250514",
    "research": "claude-sonnet-4-20250514",
    "strategy": "claude-sonnet-4-20250514",
    "adversarial": "claude-sonnet-4-20250514",
}


class ModelRouter:
    """Routes requests to appropriate model providers based on task type."""

    def __init__(self, routes: dict[str, str] | None = None) -> None:
        self._routes = routes or _DEFAULT_ROUTES
        self._providers: dict[str, ModelProvider] = {}

    def _get_provider(self, model: str) -> ModelProvider:
        if model not in self._providers:
            self._providers[model] = ClaudeProvider(model=model)
        return self._providers[model]

    def route(self, prompt: str, task_type: str = "reasoning", **kwargs) -> ModelResponse:
        """Route a prompt to the appropriate model."""
        model = self._routes.get(task_type, self._routes.get("reasoning", "claude-sonnet-4-20250514"))
        provider = self._get_provider(model)
        return provider.generate(prompt, **kwargs)

    def register_route(self, task_type: str, model: str) -> None:
        """Register or update a routing rule."""
        self._routes[task_type] = model

    @property
    def routes(self) -> dict[str, str]:
        return dict(self._routes)
