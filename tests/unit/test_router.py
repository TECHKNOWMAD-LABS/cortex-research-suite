"""Tests for model router."""

from __future__ import annotations

import pytest

from cortex.models.router import ModelRouter
from cortex.models.claude_provider import MockProvider


class TestModelRouter:
    def test_default_routes(self):
        router = ModelRouter()
        assert "reasoning" in router.routes
        assert "evaluation" in router.routes

    def test_custom_routes(self):
        router = ModelRouter(routes={"custom": "model-x"})
        assert router.routes == {"custom": "model-x"}

    def test_register_route(self):
        router = ModelRouter()
        router.register_route("new_task", "new-model")
        assert router.routes["new_task"] == "new-model"

    def test_routes_returns_copy(self):
        router = ModelRouter()
        routes = router.routes
        routes["injected"] = "bad"
        assert "injected" not in router.routes
