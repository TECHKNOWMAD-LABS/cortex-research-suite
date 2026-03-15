"""Centralized configuration with validation and environment overrides.

Loads from settings.yaml with environment variable overrides (CORTEX_ prefix).
Thread-safe singleton pattern for production use.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ModelConfig:
    """Model provider configuration."""

    default: str = "claude"
    reasoning: str = "claude"
    evaluation: str = "claude"
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: int = 120


@dataclass(frozen=True)
class DatasetConfig:
    """Dataset storage configuration."""

    root: str = "datasets/"
    shard_size: int = 10_000
    max_prompt_length: int = 10_000
    min_prompt_length: int = 10
    dedup_enabled: bool = True


@dataclass(frozen=True)
class EvaluationConfig:
    """Evaluation system configuration."""

    judge_model: str = "claude"
    metrics: tuple[str, ...] = ("accuracy", "reasoning", "completeness", "coherence")
    min_score_threshold: float = 0.6
    regression_tolerance: float = 0.05
    max_parallel_evals: int = 4


@dataclass(frozen=True)
class SecurityConfig:
    """Security and safety configuration."""

    enable_input_sanitization: bool = True
    max_input_length: int = 50_000
    blocked_patterns: tuple[str, ...] = (
        "ignore all previous",
        "system prompt",
        "reveal secrets",
        "disregard instructions",
    )
    enable_output_validation: bool = True
    audit_log_enabled: bool = True


@dataclass(frozen=True)
class TelemetryConfig:
    """Telemetry and logging configuration."""

    log_level: str = "INFO"
    log_format: str = "json"
    log_dir: str = "logs/"
    max_log_size_mb: int = 50
    retention_days: int = 90
    enable_metrics: bool = True


@dataclass(frozen=True)
class Settings:
    """Root configuration object for Cortex Research Suite."""

    model: ModelConfig = field(default_factory=ModelConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Settings:
        """Load settings from a YAML file with env var overrides."""
        if yaml is None:
            raise ImportError("PyYAML required: pip install pyyaml")
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        return cls._from_dict(raw)

    @classmethod
    def _from_dict(cls, raw: dict[str, Any]) -> Settings:
        """Build Settings from a raw dict, applying env overrides."""

        def _env(key: str, default: Any) -> Any:
            env_key = f"CORTEX_{key.upper()}"
            val = os.environ.get(env_key)
            if val is None:
                return default
            if isinstance(default, bool):
                return val.lower() in ("true", "1", "yes")
            if isinstance(default, int):
                return int(val)
            if isinstance(default, float):
                return float(val)
            return val

        m = raw.get("model", {})
        model = ModelConfig(
            default=_env("model_default", m.get("default", "claude")),
            reasoning=_env("model_reasoning", m.get("reasoning", "claude")),
            evaluation=_env("model_evaluation", m.get("evaluation", "claude")),
            temperature=_env("model_temperature", m.get("temperature", 0.2)),
            max_tokens=_env("model_max_tokens", m.get("max_tokens", 4096)),
            timeout_seconds=_env("model_timeout", m.get("timeout_seconds", 120)),
        )

        d = raw.get("dataset", {})
        dataset = DatasetConfig(
            root=_env("dataset_root", d.get("root", "datasets/")),
            shard_size=_env("dataset_shard_size", d.get("shard_size", 10_000)),
            max_prompt_length=_env("dataset_max_prompt_length", d.get("max_prompt_length", 10_000)),
            min_prompt_length=_env("dataset_min_prompt_length", d.get("min_prompt_length", 10)),
        )

        e = raw.get("evaluation", {})
        metrics_raw = e.get("metrics", ["accuracy", "reasoning", "completeness", "coherence"])
        evaluation = EvaluationConfig(
            judge_model=_env("eval_judge_model", e.get("judge_model", "claude")),
            metrics=tuple(metrics_raw),
            min_score_threshold=_env("eval_min_score", e.get("min_score_threshold", 0.6)),
            regression_tolerance=_env("eval_regression_tol", e.get("regression_tolerance", 0.05)),
        )

        s = raw.get("security", {})
        security = SecurityConfig(
            enable_input_sanitization=s.get("enable_input_sanitization", True),
            max_input_length=s.get("max_input_length", 50_000),
            enable_output_validation=s.get("enable_output_validation", True),
            audit_log_enabled=s.get("audit_log_enabled", True),
        )

        t = raw.get("telemetry", {})
        telemetry = TelemetryConfig(
            log_level=_env("log_level", t.get("log_level", "INFO")),
            log_dir=t.get("log_dir", "logs/"),
            max_log_size_mb=t.get("max_log_size_mb", 50),
            retention_days=t.get("retention_days", 90),
        )

        return cls(
            model=model,
            dataset=dataset,
            evaluation=evaluation,
            security=security,
            telemetry=telemetry,
        )


_settings: Settings | None = None
_lock = threading.Lock()


def get_settings(config_path: str | Path | None = None) -> Settings:
    """Thread-safe singleton settings accessor."""
    global _settings
    if _settings is not None:
        return _settings
    with _lock:
        if _settings is not None:
            return _settings
        if config_path is None:
            config_path = Path("cortex/config/settings.yaml")
        path = Path(config_path)
        if path.exists() and yaml is not None:
            _settings = Settings.from_yaml(path)
        else:
            _settings = Settings()
        return _settings
