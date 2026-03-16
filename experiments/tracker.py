#!/usr/bin/env python3
"""SQLite experiment registry with auto-logging and CLI comparison.

Auto-logs every eval run into a persistent SQLite database.
Provides CLI for listing, comparing, and querying experiments.

Usage:
    python tracker.py log --name "security-audit-v2" --skill security-audit --dataset eval_50 --metrics '{"accuracy": 4.2, "overall": 0.78}'
    python tracker.py list --skill security-audit --limit 10
    python tracker.py compare --ids abc123 def456
    python tracker.py best --skill security-audit --metric overall
    python tracker.py summary
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ExperimentRecord:
    """A single experiment record."""

    name: str
    skill: str
    dataset: str
    model: str = "claude"
    prompt_version: str = "v1"
    config: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    status: str = "running"
    tags: list[str] = field(default_factory=list)

    @property
    def experiment_id(self) -> str:
        key = f"{self.name}:{self.skill}:{self.dataset}:{self.model}:{self.started_at}"
        return hashlib.sha256(key.encode()).hexdigest()[:12]

    @property
    def duration_seconds(self) -> float:
        if self.completed_at == 0:
            return 0.0
        return round(self.completed_at - self.started_at, 2)

    def complete(self, metrics: dict[str, float]) -> None:
        self.metrics = metrics
        self.completed_at = time.time()
        self.status = "completed"

    def fail(self, error: str) -> None:
        self.completed_at = time.time()
        self.status = "failed"
        self.config["error"] = error


# ---------------------------------------------------------------------------
# SQLite Registry
# ---------------------------------------------------------------------------


class ExperimentRegistry:
    """SQLite-backed experiment registry with auto-logging."""

    def __init__(self, db_path: str | Path = "experiments/experiments.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                skill TEXT NOT NULL,
                dataset TEXT NOT NULL,
                model TEXT DEFAULT 'claude',
                prompt_version TEXT DEFAULT 'v1',
                config TEXT DEFAULT '{}',
                metrics TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]',
                started_at REAL NOT NULL,
                completed_at REAL DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                status TEXT DEFAULT 'running'
            );

            CREATE INDEX IF NOT EXISTS idx_experiments_skill
                ON experiments(skill);
            CREATE INDEX IF NOT EXISTS idx_experiments_status
                ON experiments(status);
            CREATE INDEX IF NOT EXISTS idx_experiments_started
                ON experiments(started_at DESC);
        """)
        self._conn.commit()

    def log(self, record: ExperimentRecord) -> str:
        """Log an experiment record. Returns experiment_id."""
        eid = record.experiment_id
        self._conn.execute(
            """INSERT OR REPLACE INTO experiments
               (experiment_id, name, skill, dataset, model, prompt_version,
                config, metrics, tags, started_at, completed_at,
                duration_seconds, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                eid,
                record.name,
                record.skill,
                record.dataset,
                record.model,
                record.prompt_version,
                json.dumps(record.config),
                json.dumps(record.metrics),
                json.dumps(record.tags),
                record.started_at,
                record.completed_at,
                record.duration_seconds,
                record.status,
            ),
        )
        self._conn.commit()
        return eid

    def get(self, experiment_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM experiments WHERE experiment_id = ?",
            (experiment_id,),
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_experiments(
        self,
        skill: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM experiments WHERE 1=1"
        params: list[Any] = []
        if skill:
            query += " AND skill = ?"
            params.append(skill)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def compare(self, experiment_ids: list[str]) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in experiment_ids)
        rows = self._conn.execute(
            f"SELECT * FROM experiments WHERE experiment_id IN ({placeholders})",
            experiment_ids,
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def best(self, skill: str, metric: str = "overall") -> dict[str, Any] | None:
        """Find the best experiment for a skill by a specific metric."""
        rows = self._conn.execute(
            "SELECT * FROM experiments WHERE skill = ? AND status = 'completed'",
            (skill,),
        ).fetchall()
        if not rows:
            return None
        experiments = [self._row_to_dict(r) for r in rows]
        return max(experiments, key=lambda e: e.get("metrics", {}).get(metric, 0))

    def summary(self) -> dict[str, Any]:
        """Overall registry summary."""
        total = self._conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
        by_status = {}
        for row in self._conn.execute("SELECT status, COUNT(*) as cnt FROM experiments GROUP BY status").fetchall():
            by_status[row["status"]] = row["cnt"]

        by_skill = {}
        for row in self._conn.execute(
            "SELECT skill, COUNT(*) as cnt, AVG(duration_seconds) as avg_dur "
            "FROM experiments GROUP BY skill ORDER BY cnt DESC"
        ).fetchall():
            by_skill[row["skill"]] = {
                "count": row["cnt"],
                "avg_duration_s": round(row["avg_dur"] or 0, 2),
            }

        return {
            "total_experiments": total,
            "by_status": by_status,
            "by_skill": by_skill,
            "db_path": str(self._db_path),
        }

    def delete(self, experiment_id: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM experiments WHERE experiment_id = ?",
            (experiment_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        for json_field in ("config", "metrics", "tags"):
            if json_field in d and isinstance(d[json_field], str):
                d[json_field] = json.loads(d[json_field])
        return d

    def close(self) -> None:
        self._conn.close()


# ---------------------------------------------------------------------------
# Auto-logger — hook into eval runs
# ---------------------------------------------------------------------------


def auto_log_eval(
    registry: ExperimentRegistry,
    name: str,
    skill: str,
    dataset: str,
    metrics: dict[str, float],
    model: str = "claude",
    config: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> str:
    """Convenience function to log a completed eval run in one call."""
    record = ExperimentRecord(
        name=name,
        skill=skill,
        dataset=dataset,
        model=model,
        config=config or {},
        tags=tags or [],
    )
    record.complete(metrics)
    return registry.log(record)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "(no results)"
    widths = {c: len(c) for c in columns}
    str_rows = []
    for row in rows:
        str_row = {}
        for c in columns:
            val = row.get(c, "")
            if isinstance(val, dict):
                val = json.dumps(val)
            elif isinstance(val, float):
                val = f"{val:.4f}" if val < 100 else f"{val:.1f}"
            str_row[c] = str(val)[:40]
            widths[c] = max(widths[c], len(str_row[c]))
        str_rows.append(str_row)

    header = " | ".join(c.ljust(widths[c]) for c in columns)
    sep = "-+-".join("-" * widths[c] for c in columns)
    lines = [header, sep]
    for sr in str_rows:
        lines.append(" | ".join(sr[c].ljust(widths[c]) for c in columns))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="SQLite experiment registry")
    sub = parser.add_subparsers(dest="command", required=True)

    # log
    p_log = sub.add_parser("log", help="Log an experiment")
    p_log.add_argument("--name", required=True)
    p_log.add_argument("--skill", required=True)
    p_log.add_argument("--dataset", required=True)
    p_log.add_argument("--model", default="claude")
    p_log.add_argument("--metrics", required=True, help="JSON string of metrics")
    p_log.add_argument("--tags", default="", help="Comma-separated tags")
    p_log.add_argument("--db", default="experiments/experiments.db")

    # list
    p_list = sub.add_parser("list", help="List experiments")
    p_list.add_argument("--skill", default=None)
    p_list.add_argument("--status", default=None)
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--db", default="experiments/experiments.db")

    # compare
    p_cmp = sub.add_parser("compare", help="Compare experiments")
    p_cmp.add_argument("--ids", nargs="+", required=True)
    p_cmp.add_argument("--db", default="experiments/experiments.db")

    # best
    p_best = sub.add_parser("best", help="Find best experiment")
    p_best.add_argument("--skill", required=True)
    p_best.add_argument("--metric", default="overall")
    p_best.add_argument("--db", default="experiments/experiments.db")

    # summary
    p_sum = sub.add_parser("summary", help="Registry summary")
    p_sum.add_argument("--db", default="experiments/experiments.db")

    args = parser.parse_args()
    registry = ExperimentRegistry(args.db)

    try:
        if args.command == "log":
            metrics = json.loads(args.metrics)
            tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
            eid = auto_log_eval(
                registry,
                name=args.name,
                skill=args.skill,
                dataset=args.dataset,
                model=args.model,
                metrics=metrics,
                tags=tags,
            )
            print(f"Logged experiment: {eid}")

        elif args.command == "list":
            rows = registry.list_experiments(skill=args.skill, status=args.status, limit=args.limit)
            columns = ["experiment_id", "name", "skill", "status", "metrics", "duration_seconds"]
            print(_format_table(rows, columns))

        elif args.command == "compare":
            rows = registry.compare(args.ids)
            columns = ["experiment_id", "name", "skill", "model", "metrics", "duration_seconds"]
            print(_format_table(rows, columns))

        elif args.command == "best":
            result = registry.best(args.skill, args.metric)
            if result:
                print(json.dumps(result, indent=2))
            else:
                print(f"No completed experiments for skill '{args.skill}'")

        elif args.command == "summary":
            summary = registry.summary()
            print(json.dumps(summary, indent=2))

    finally:
        registry.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
