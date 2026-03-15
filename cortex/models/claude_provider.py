"""Claude model provider via Anthropic SDK.

Uses the official anthropic Python SDK for direct API access.
Falls back to subprocess claude CLI if SDK unavailable.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Any

from cortex.models.provider import ModelProvider, ModelResponse

try:
    import anthropic

    _HAS_SDK = True
except ImportError:
    _HAS_SDK = False


class ClaudeProvider(ModelProvider):
    """Claude model provider with SDK and CLI fallback."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
        timeout: int = 120,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client: Any = None
        if _HAS_SDK and self._api_key:
            self._client = anthropic.Anthropic(api_key=self._api_key)

    def generate(self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 4096) -> ModelResponse:
        """Generate response via SDK or CLI fallback."""
        if self._client is not None:
            return self._generate_sdk(prompt, temperature=temperature, max_tokens=max_tokens)
        return self._generate_cli(prompt, max_tokens=max_tokens)

    def _generate_sdk(self, prompt: str, *, temperature: float, max_tokens: int) -> ModelResponse:
        """Generate via Anthropic Python SDK."""
        start = time.time()
        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = self._measure_latency(start)
        content = ""
        for block in message.content:
            if hasattr(block, "text"):
                content += block.text
        return ModelResponse(
            content=content,
            model=self.model,
            tokens_used=message.usage.input_tokens + message.usage.output_tokens,
            latency_ms=latency,
            metadata={
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "stop_reason": message.stop_reason,
            },
        )

    def _generate_cli(self, prompt: str, *, max_tokens: int) -> ModelResponse:
        """Fallback: generate via claude CLI subprocess."""
        start = time.time()
        try:
            result = subprocess.run(
                ["claude", "--print", "--model", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True,
            )
            latency = self._measure_latency(start)
            return ModelResponse(
                content=result.stdout.strip(),
                model=self.model,
                latency_ms=latency,
                metadata={"method": "cli"},
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            latency = self._measure_latency(start)
            return ModelResponse(
                content="",
                model=self.model,
                latency_ms=latency,
                metadata={"error": str(e), "method": "cli"},
            )


class MockProvider(ModelProvider):
    """Mock provider for testing without API calls."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = responses or ["Mock response"]
        self._call_count = 0

    def generate(self, prompt: str, *, temperature: float = 0.2, max_tokens: int = 4096) -> ModelResponse:
        idx = self._call_count % len(self._responses)
        self._call_count += 1
        return ModelResponse(
            content=self._responses[idx],
            model="mock",
            tokens_used=len(prompt.split()) + len(self._responses[idx].split()),
            latency_ms=1.0,
            metadata={"call_count": self._call_count},
        )
