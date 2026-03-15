"""
SkillOrganism Telemetry Module
Tracks performance metrics for all skills using SQLite backend.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class SkillMetrics:
    """Aggregated metrics for a skill over a period."""
    skill_id: str
    invocation_count: int
    success_rate: float
    avg_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    total_tokens_used: int
    avg_tokens_per_call: float
    avg_satisfaction: float
    error_count: int
    last_invoked: Optional[str]
    health_status: str


class SkillTelemetry:
    """SQLite-backed telemetry tracking for skills."""

    def __init__(self, db_path: Path = Path("skill_telemetry.db")):
        """Initialize telemetry database."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_ms REAL,
                    success BOOLEAN,
                    tokens_used INTEGER,
                    error_message TEXT,
                    context TEXT,
                    user_satisfaction REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_skill_id 
                ON invocations(skill_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON invocations(timestamp)
            """)
            conn.commit()

    def record_invocation(
        self,
        skill_id: str,
        duration_ms: float,
        success: bool,
        tokens_used: int = 0,
        context: Optional[str] = None,
        error_message: Optional[str] = None,
        user_satisfaction: Optional[float] = None,
    ) -> None:
        """Record a skill invocation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO invocations 
                    (skill_id, timestamp, duration_ms, success, tokens_used, 
                     error_message, context, user_satisfaction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        skill_id,
                        datetime.utcnow().isoformat(),
                        duration_ms,
                        success,
                        tokens_used,
                        error_message,
                        context,
                        user_satisfaction,
                    ),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to record invocation for {skill_id}: {e}")

    def get_skill_metrics(
        self, skill_id: str, period_days: int = 7
    ) -> Optional[SkillMetrics]:
        """Get aggregated metrics for a skill over period."""
        try:
            cutoff_time = (datetime.utcnow() - timedelta(days=period_days)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT duration_ms, success, tokens_used, error_message,
                           user_satisfaction, timestamp
                    FROM invocations
                    WHERE skill_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    """,
                    (skill_id, cutoff_time),
                )
                rows = cursor.fetchall()

            if not rows:
                return None

            latencies = []
            success_count = 0
            error_count = 0
            token_total = 0
            satisfaction_scores = []
            last_invoked = None

            for row in rows:
                duration_ms, success, tokens_used, error_msg, satisfaction, timestamp = row
                if duration_ms is not None:
                    latencies.append(duration_ms)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                if tokens_used:
                    token_total += tokens_used
                if satisfaction is not None:
                    satisfaction_scores.append(satisfaction)
                if not last_invoked:
                    last_invoked = timestamp

            invocation_count = len(rows)
            success_rate = success_count / invocation_count if invocation_count > 0 else 0

            if latencies:
                avg_latency = statistics.mean(latencies)
                median_latency = statistics.median(latencies)
                # P95
                sorted_latencies = sorted(latencies)
                p95_idx = int(len(sorted_latencies) * 0.95)
                p95_latency = (
                    sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else sorted_latencies[-1]
                )
            else:
                avg_latency = median_latency = p95_latency = 0

            avg_tokens = token_total / invocation_count if invocation_count > 0 else 0
            avg_satisfaction = (
                statistics.mean(satisfaction_scores) if satisfaction_scores else 0.5
            )

            # Health status based on metrics
            if success_rate >= 0.95 and avg_satisfaction >= 0.8:
                health_status = "excellent"
            elif success_rate >= 0.85 and avg_satisfaction >= 0.7:
                health_status = "healthy"
            elif success_rate >= 0.7 and avg_satisfaction >= 0.5:
                health_status = "degraded"
            else:
                health_status = "critical"

            return SkillMetrics(
                skill_id=skill_id,
                invocation_count=invocation_count,
                success_rate=round(success_rate, 3),
                avg_latency_ms=round(avg_latency, 2),
                median_latency_ms=round(median_latency, 2),
                p95_latency_ms=round(p95_latency, 2),
                total_tokens_used=token_total,
                avg_tokens_per_call=round(avg_tokens, 2),
                avg_satisfaction=round(avg_satisfaction, 3),
                error_count=error_count,
                last_invoked=last_invoked,
                health_status=health_status,
            )
        except sqlite3.Error as e:
            logger.error(f"Failed to get metrics for {skill_id}: {e}")
            return None

    def get_ecosystem_health(self, skill_ids: List[str]) -> Dict:
        """Get overall ecosystem health metrics."""
        try:
            all_metrics = []
            healthy_count = 0
            degraded_count = 0
            critical_count = 0

            for skill_id in skill_ids:
                metrics = self.get_skill_metrics(skill_id)
                if metrics:
                    all_metrics.append(metrics)
                    if metrics.health_status == "excellent":
                        healthy_count += 1
                    elif metrics.health_status == "healthy":
                        healthy_count += 1
                    elif metrics.health_status == "degraded":
                        degraded_count += 1
                    elif metrics.health_status == "critical":
                        critical_count += 1

            total_skills = len(skill_ids)
            avg_success_rate = (
                statistics.mean([m.success_rate for m in all_metrics])
                if all_metrics
                else 0
            )
            total_invocations = sum(m.invocation_count for m in all_metrics)

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_skills": total_skills,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "critical": critical_count,
                "avg_success_rate": round(avg_success_rate, 3),
                "total_invocations": total_invocations,
                "ecosystem_health_score": round(healthy_count / total_skills, 3)
                if total_skills > 0
                else 0,
            }
        except Exception as e:
            logger.error(f"Failed to compute ecosystem health: {e}")
            return {}

    def detect_anomalies(
        self, skill_id: str, period_days: int = 7, sigma: float = 2.0
    ) -> List[Dict]:
        """Detect anomalies using statistical process control (2 sigma rule)."""
        anomalies = []
        try:
            cutoff_time = (datetime.utcnow() - timedelta(days=period_days)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT duration_ms, success, timestamp
                    FROM invocations
                    WHERE skill_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    """,
                    (skill_id, cutoff_time),
                )
                rows = cursor.fetchall()

            latencies = [row[0] for row in rows if row[0] is not None]
            if len(latencies) < 5:
                return anomalies

            mean_latency = statistics.mean(latencies)
            stdev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0

            for row in rows:
                duration_ms, success, timestamp = row
                if duration_ms and stdev_latency > 0:
                    z_score = (duration_ms - mean_latency) / stdev_latency
                    if abs(z_score) > sigma:
                        anomalies.append(
                            {
                                "timestamp": timestamp,
                                "duration_ms": duration_ms,
                                "z_score": round(z_score, 2),
                                "type": "latency_spike" if z_score > 0 else "latency_drop",
                            }
                        )

        except Exception as e:
            logger.error(f"Failed to detect anomalies for {skill_id}: {e}")

        return anomalies[:10]  # Return last 10 anomalies

    def get_fitness_scores(
        self, skill_ids: List[str], period_days: int = 7
    ) -> List[Tuple[str, float]]:
        """Get ranked list of all skills by composite fitness score."""
        fitness_scores = []

        for skill_id in skill_ids:
            metrics = self.get_skill_metrics(skill_id, period_days)
            if not metrics:
                # Unevaluated skills get baseline score
                fitness_scores.append((skill_id, 0.5))
                continue

            # Composite fitness: 40% success rate + 40% satisfaction + 20% invocation count
            invocation_factor = min(
                metrics.invocation_count / 100, 1.0
            )  # Normalize to 0-1

            fitness = (
                metrics.success_rate * 0.4
                + metrics.avg_satisfaction * 0.4
                + invocation_factor * 0.2
            )

            fitness_scores.append((skill_id, round(fitness, 3)))

        # Sort by fitness descending
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        return fitness_scores

    def clear_old_data(self, retention_days: int = 90) -> int:
        """Delete invocations older than retention period. Returns count deleted."""
        try:
            cutoff_time = (datetime.utcnow() - timedelta(days=retention_days)).isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM invocations WHERE timestamp < ?", (cutoff_time,)
                )
                deleted = cursor.rowcount
                conn.commit()
            logger.info(f"Cleared {deleted} old telemetry records")
            return deleted
        except sqlite3.Error as e:
            logger.error(f"Failed to clear old data: {e}")
            return 0
