"""MindSpider connector — pulls trending topics from a MindSpider deployment.

Supports two modes:
  --source demo   : Generate synthetic demo data (no external connections)
  --source mysql  : Connect to live MindSpider via MINDSPIDER_DB_URL env var

Usage:
    python -m skills.mindspider-connector.scripts.connector --source demo
    python -m skills.mindspider-connector.scripts.connector --source mysql --domain "AI"
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

MAX_INPUT_CHARS = 50000
MAX_SAMPLE_POST_LEN = 280
CONNECT_TIMEOUT = 10
QUERY_TIMEOUT = 30


def generate_demo_data(domain: str | None = None, n_topics: int = 15) -> list[dict[str, Any]]:
    """Generate synthetic demo topics — no external connections."""
    base_topics = [
        ("AI regulation framework debate", 0.35, 1842, "rising"),
        ("Open-source LLM benchmark results", 0.62, 3201, "rising"),
        ("Healthcare data privacy concerns", -0.28, 956, "stable"),
        ("Autonomous vehicle safety incidents", -0.45, 2103, "declining"),
        ("Quantum computing breakthrough claims", 0.71, 4502, "rising"),
        ("Social media algorithm transparency", -0.12, 1567, "stable"),
        ("Climate tech investment trends", 0.48, 2890, "rising"),
        ("Remote work productivity studies", 0.22, 1205, "stable"),
        ("Cybersecurity zero-day exploits", -0.55, 3412, "rising"),
        ("EdTech adaptive learning results", 0.38, 876, "stable"),
        ("Cryptocurrency market manipulation", -0.67, 5201, "declining"),
        ("Biotech CRISPR therapy approvals", 0.81, 2340, "rising"),
        ("Supply chain AI optimization", 0.44, 1123, "stable"),
        ("Misinformation detection tools", 0.15, 1890, "rising"),
        ("Digital identity verification", 0.29, 1456, "stable"),
    ]

    rng = random.Random(42)
    now = datetime.now(timezone.utc)
    topics = []

    for title, sentiment, count, trend in base_topics[:n_topics]:
        if domain and domain.lower() not in title.lower():
            continue
        hours_ago = rng.randint(2, 20)
        peak_offset = rng.randint(0, hours_ago)
        topics.append(
            {
                "topic": title,
                "sentiment_score": round(sentiment + rng.uniform(-0.05, 0.05), 3),
                "post_count": count + rng.randint(-100, 300),
                "trend_direction": trend,
                "sample_posts": [
                    f"Sample post about {title.lower()} — perspective {i + 1}"[:MAX_SAMPLE_POST_LEN]
                    for i in range(3)
                ],
                "platforms": rng.sample(
                    ["twitter", "reddit", "weibo", "telegram", "mastodon"], k=rng.randint(2, 4)
                ),
                "first_seen": (now - timedelta(hours=hours_ago)).isoformat(),
                "peak_time": (now - timedelta(hours=peak_offset)).isoformat(),
            }
        )

    return topics


def fetch_mysql_topics(db_url: str, domain: str | None = None) -> list[dict[str, Any]]:
    """Fetch topics from a live MindSpider MySQL deployment.

    Uses parameterized queries only — never string concatenation.
    """
    try:
        import pymysql  # type: ignore[import-untyped]
    except ImportError:
        print("ERROR: pymysql not installed. Install with: pip install pymysql", file=sys.stderr)
        print("Falling back to demo data.", file=sys.stderr)
        return generate_demo_data(domain)

    # Parse connection URL: mysql://user:pass@host:port/dbname
    from urllib.parse import urlparse

    parsed = urlparse(db_url)

    try:
        conn = pymysql.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 3306,
            user=parsed.username or "root",
            password=parsed.password or "",
            database=parsed.path.lstrip("/") if parsed.path else "mindspider",
            connect_timeout=CONNECT_TIMEOUT,
            read_timeout=QUERY_TIMEOUT,
            charset="utf8mb4",
        )
    except Exception as e:
        print(f"ERROR: Could not connect to MindSpider DB: {e}", file=sys.stderr)
        print("Falling back to demo data.", file=sys.stderr)
        return generate_demo_data(domain)

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            if domain:
                cursor.execute(
                    "SELECT topic, sentiment_score, post_count, trend_direction, "
                    "first_seen, peak_time FROM trending_topics "
                    "WHERE topic LIKE %s ORDER BY post_count DESC LIMIT 50",
                    (f"%{domain[:200]}%",),
                )
            else:
                cursor.execute(
                    "SELECT topic, sentiment_score, post_count, trend_direction, "
                    "first_seen, peak_time FROM trending_topics "
                    "ORDER BY post_count DESC LIMIT 50"
                )

            rows = cursor.fetchall()
            topics = []
            for row in rows:
                # Fetch sample posts for this topic
                cursor.execute(
                    "SELECT content FROM posts WHERE topic_id = %s LIMIT 3",
                    (row.get("id", 0),),
                )
                posts = [p["content"][:MAX_SAMPLE_POST_LEN] for p in cursor.fetchall()]

                topics.append(
                    {
                        "topic": str(row.get("topic", ""))[:500],
                        "sentiment_score": float(row.get("sentiment_score", 0)),
                        "post_count": int(row.get("post_count", 0)),
                        "trend_direction": str(row.get("trend_direction", "stable")),
                        "sample_posts": posts,
                        "platforms": [],
                        "first_seen": str(row.get("first_seen", "")),
                        "peak_time": str(row.get("peak_time", "")),
                    }
                )
            return topics
    finally:
        conn.close()


def run_connector(source: str = "demo", domain: str | None = None) -> dict[str, Any]:
    """Main connector logic."""
    if source == "mysql":
        db_url = os.environ.get("MINDSPIDER_DB_URL", "")
        if not db_url:
            print("WARN: MINDSPIDER_DB_URL not set, falling back to demo mode", file=sys.stderr)
            source = "demo"
            topics = generate_demo_data(domain)
        else:
            topics = fetch_mysql_topics(db_url, domain)
    else:
        topics = generate_demo_data(domain)

    return {
        "source": "mindspider",
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "topics": topics,
        "metadata": {
            "total_topics": len(topics),
            "time_range_hours": 24,
            "source_mode": source,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MindSpider connector")
    parser.add_argument("--source", choices=["demo", "mysql"], default="demo", help="Data source")
    parser.add_argument("--domain", default=None, help="Filter by domain keyword")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--format", choices=["json", "jsonl"], default="json", help="Output format")
    args = parser.parse_args()

    result = run_connector(source=args.source, domain=args.domain)

    if args.format == "jsonl":
        lines = [json.dumps(t) for t in result["topics"]]
        output_text = "\n".join(lines) + "\n"
    else:
        output_text = json.dumps(result, indent=2) + "\n"

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_text)
        print(f"Written {len(result['topics'])} topics to {args.output}", file=sys.stderr)
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
