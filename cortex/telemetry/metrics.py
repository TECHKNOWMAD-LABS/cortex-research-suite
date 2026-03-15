"""Metrics collection and aggregation for evaluation telemetry.

Tracks per-skill performance, token usage, latency, and error rates.
Thread-safe for concurrent evaluation workloads.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MetricRecord:
    """Single metric measurement."""

    skill: str
    metric_name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Thread-safe metrics collector backed by SQLite.

    Stores all evaluation metrics in a local SQLite database for
    querying, aggregation, and dashboard visualization.
    """

    def __init__(self, db_path: str | Path = "metrics.db") -> None:
        self._db_path = str(db_path)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        skill TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp REAL NOT NULL,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_metrics_skill
                    ON metrics(skill, metric_name)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
                    ON metrics(timestamp)
                """)
                conn.commit()
            finally:
                conn.close()

    def record(self, skill: str, metric_name: str, value: float, **metadata: Any) -> None:
        """Record a single metric value."""
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                conn.execute(
                    "INSERT INTO metrics (skill, metric_name, value, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                    (skill, metric_name, value, time.time(), json.dumps(metadata, default=str)),
                )
                conn.commit()
            finally:
                conn.close()

    def record_batch(self, records: list[MetricRecord]) -> None:
        """Record multiple metrics atomically."""
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                conn.executemany(
                    "INSERT INTO metrics (skill, metric_name, value, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                    [
                        (r.skill, r.metric_name, r.value, r.timestamp, json.dumps(r.metadata, default=str))
                        for r in records
                    ],
                )
                conn.commit()
            finally:
                conn.close()

    def query(
        self,
        skill: str | None = None,
        metric_name: str | None = None,
        since: float | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Query metrics with optional filters."""
        conditions: list[str] = []
        params: list[Any] = []
        if skill:
            conditions.append("skill = ?")
            params.append(skill)
        if metric_name:
            conditions.append("metric_name = ?")
            params.append(metric_name)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT skill, metric_name, value, timestamp, metadata FROM metrics {where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                rows = conn.execute(query, params).fetchall()
                return [
                    {
                        "skill": r[0],
                        "metric_name": r[1],
                        "value": r[2],
                        "timestamp": r[3],
                        "metadata": json.loads(r[4]) if r[4] else {},
                    }
                    for r in rows
                ]
            finally:
                conn.close()

    def aggregate(self, skill: str, metric_name: str) -> dict[str, float]:
        """Compute aggregate stats for a skill's metric."""
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) as count,
                        AVG(value) as mean,
                        MIN(value) as min,
                        MAX(value) as max
                    FROM metrics
                    WHERE skill = ? AND metric_name = ?
                    """,
                    (skill, metric_name),
                ).fetchone()
                if not row or row[0] == 0:
                    return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
                return {
                    "count": row[0],
                    "mean": round(row[1], 4),
                    "min": round(row[2], 4),
                    "max": round(row[3], 4),
                }
            finally:
                conn.close()

    def purge_old(self, retention_days: int = 90) -> int:
        """Delete metrics older than retention period. Returns rows deleted."""
        cutoff = time.time() - (retention_days * 86400)
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            try:
                cursor = conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
                conn.commit()
                return cursor.rowcount
            finally:
                conn.close()
