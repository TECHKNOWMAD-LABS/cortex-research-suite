"""Tests for configuration system."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from cortex.config.settings import Settings, ModelConfig, DatasetConfig


class TestSettings:
    def test_default_settings(self):
        s = Settings()
        assert s.model.default == "claude"
        assert s.dataset.shard_size == 10_000
        assert s.evaluation.min_score_threshold == 0.6

    def test_from_yaml(self):
        yaml_content = """
model:
  default: claude
  temperature: 0.5
dataset:
  shard_size: 5000
evaluation:
  judge_model: claude
  metrics:
    - accuracy
    - reasoning
"""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            settings = Settings.from_yaml(f.name)
            assert settings.model.temperature == 0.5
            assert settings.dataset.shard_size == 5000
            os.unlink(f.name)

    def test_env_override(self):
        os.environ["CORTEX_MODEL_DEFAULT"] = "custom-model"
        try:
            settings = Settings._from_dict({})
            assert settings.model.default == "custom-model"
        finally:
            del os.environ["CORTEX_MODEL_DEFAULT"]

    def test_missing_yaml_returns_defaults(self):
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
        settings = Settings.from_yaml("/nonexistent/path.yaml")
        assert settings.model.default == "claude"


class TestModelConfig:
    def test_defaults(self):
        config = ModelConfig()
        assert config.default == "claude"
        assert config.temperature == 0.2
        assert config.max_tokens == 4096

    def test_frozen(self):
        config = ModelConfig()
        with pytest.raises(AttributeError):
            config.default = "other"  # type: ignore
