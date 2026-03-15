"""Tests for metrics collector."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from cortex.telemetry.metrics import MetricsCollector, MetricRecord


class TestMetricsCollector:
    def test_record_and_query(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            collector.record("skill_a", "accuracy", 0.95)
            results = collector.query(skill="skill_a")
            assert len(results) == 1
            assert results[0]["value"] == 0.95

    def test_query_by_metric_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            collector.record("skill_a", "accuracy", 0.9)
            collector.record("skill_a", "latency", 100.0)
            results = collector.query(metric_name="accuracy")
            assert len(results) == 1

    def test_query_since(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            collector.record("skill_a", "accuracy", 0.9)
            future = time.time() + 1000
            results = collector.query(since=future)
            assert len(results) == 0

    def test_query_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            for i in range(5):
                collector.record("skill_a", "accuracy", float(i) / 10)
            results = collector.query(limit=2)
            assert len(results) == 2

    def test_query_invalid_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            collector.record("s", "m", 1.0)
            results = collector.query(limit=-1)
            assert len(results) == 1  # falls back to default

    def test_record_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            records = [
                MetricRecord(skill="s1", metric_name="acc", value=0.9),
                MetricRecord(skill="s2", metric_name="acc", value=0.8),
            ]
            collector.record_batch(records)
            results = collector.query()
            assert len(results) == 2

    def test_aggregate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            collector.record("skill_a", "accuracy", 0.8)
            collector.record("skill_a", "accuracy", 0.9)
            collector.record("skill_a", "accuracy", 1.0)
            agg = collector.aggregate("skill_a", "accuracy")
            assert agg["count"] == 3
            assert agg["min"] == 0.8
            assert agg["max"] == 1.0

    def test_aggregate_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            agg = collector.aggregate("nonexistent", "acc")
            assert agg["count"] == 0

    def test_purge_old(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            collector.record("skill_a", "accuracy", 0.9)
            # Purge with 0 retention should delete everything
            deleted = collector.purge_old(retention_days=0)
            assert deleted == 1

    def test_record_with_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "test.db"
            collector = MetricsCollector(db)
            collector.record("skill_a", "accuracy", 0.9, model="claude", version="v1")
            results = collector.query(skill="skill_a")
            assert results[0]["metadata"]["model"] == "claude"
