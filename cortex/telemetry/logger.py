"""Structured JSON logging with rotation and context tracking.

Production-grade logging for all Cortex operations.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    """Outputs structured JSON log lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "context"):
            log_entry["context"] = record.context
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }
        return json.dumps(log_entry, default=str)


class CortexLogger:
    """Structured logger with JSON output and file rotation."""

    def __init__(
        self,
        name: str = "cortex",
        log_dir: str = "logs",
        level: str = "INFO",
        max_bytes: int = 50 * 1024 * 1024,
        backup_count: int = 5,
    ) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._logger.handlers.clear()

        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(JsonFormatter())
        self._logger.addHandler(console)

        # File handler with rotation
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path / f"{name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(JsonFormatter())
        self._logger.addHandler(file_handler)

    def info(self, message: str, **context: Any) -> None:
        self._log(logging.INFO, message, context)

    def warning(self, message: str, **context: Any) -> None:
        self._log(logging.WARNING, message, context)

    def error(self, message: str, **context: Any) -> None:
        self._log(logging.ERROR, message, context)

    def debug(self, message: str, **context: Any) -> None:
        self._log(logging.DEBUG, message, context)

    def _log(self, level: int, message: str, context: dict[str, Any]) -> None:
        record = self._logger.makeRecord(self._logger.name, level, "(cortex)", 0, message, (), None)
        if context:
            record.context = context  # type: ignore[attr-defined]
        self._logger.handle(record)


_global_logger: CortexLogger | None = None


def get_logger(name: str = "cortex") -> CortexLogger:
    """Get or create the global Cortex logger."""
    global _global_logger
    if _global_logger is None:
        _global_logger = CortexLogger(name=name)
    return _global_logger
