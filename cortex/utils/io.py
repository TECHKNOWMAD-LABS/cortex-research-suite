"""Safe I/O utilities with atomic writes and validation.

All file operations use atomic writes to prevent corruption.
JSON loading uses size limits to prevent memory exhaustion.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB hard limit


def read_json(path: str | Path) -> Any:
    """Read and parse a JSON file with size validation."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large ({size} bytes > {MAX_FILE_SIZE} limit): {path}")
    with open(path) as f:
        return json.load(f)


def write_json(path: str | Path, data: Any, *, indent: int = 2) -> None:
    """Atomically write JSON to a file (write to temp, then rename)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
            f.write("\n")
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSONL file (one JSON object per line)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    results: list[dict[str, Any]] = []
    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num} in {path}: {e}") from e
    return results


def write_jsonl(path: str | Path, data: list[dict[str, Any]]) -> None:
    """Atomically write JSONL to a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            for record in data:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
