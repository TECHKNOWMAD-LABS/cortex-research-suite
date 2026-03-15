"""Tests for I/O utilities."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from cortex.utils.io import read_json, write_json, read_jsonl, write_jsonl


class TestJson:
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            data = {"key": "value", "count": 42}
            write_json(path, data)
            loaded = read_json(path)
            assert loaded == data

    def test_atomic_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            write_json(path, {"a": 1})
            # File should exist and be valid
            assert path.exists()
            assert read_json(path) == {"a": 1}

    def test_read_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            read_json("/nonexistent/file.json")

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dir" / "test.json"
            write_json(path, {"nested": True})
            assert read_json(path) == {"nested": True}


class TestJsonl:
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            data = [{"id": 1, "text": "hello"}, {"id": 2, "text": "world"}]
            write_jsonl(path, data)
            loaded = read_jsonl(path)
            assert loaded == data

    def test_read_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            read_jsonl("/nonexistent/file.jsonl")

    def test_invalid_jsonl_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.jsonl"
            path.write_text("not json\n")
            with pytest.raises(ValueError, match="Invalid JSON at line 1"):
                read_jsonl(path)
