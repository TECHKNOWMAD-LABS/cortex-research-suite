#!/usr/bin/env python3
"""
intelligence-query: Multi-source intelligence analysis engine.
Phase 14 — BettaFish-inspired intelligence skills.
BettaFish engine type: multi_source_analysis

Takes a query topic, decomposes it into sub-queries, collects evidence
from multiple sources (demo mode: synthetic), and synthesizes an
intelligence report.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List

MAX_INPUT_CHARS = 50000

# ---------- Security helpers ----------

class _HTMLStripper(HTMLParser):
    """Strip HTML tags using stdlib html.parser."""

    def __init__(self):
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def strip_html(text: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()


def sanitize_input(text: str) -> str:
    """Truncate and strip HTML from user input."""
    text = text[:MAX_INPUT_CHARS]
    return strip_html(text)


# ---------- Output schema validation ----------

EXPECTED_KEYS = {
    "query": str,
    "sub_queries": list,
    "sources": list,
    "findings": list,
    "synthesis": str,
    "confidence_level": (int, float),
    "timestamp": str,
}


def validate_output(data: Dict[str, Any]) -> bool:
    """Validate output JSON against expected schema."""
    for key, expected_type in EXPECTED_KEYS.items():
        if key not in data:
            return False
        if not isinstance(data[key], expected_type):
            return False
    return True


# ---------- Core classes ----------

class QueryDecomposer:
    """Breaks a complex topic into targeted sub-queries."""

    def decompose(self, topic: str) -> List[str]:
        sanitized = sanitize_input(topic)
        words = sanitized.split()
        # Generate sub-queries by focusing on different aspects
        sub_queries = []
        if len(words) >= 1:
            sub_queries.append(f"Background and context of {sanitized}")
        if len(words) >= 1:
            sub_queries.append(f"Key actors and stakeholders related to {sanitized}")
        if len(words) >= 1:
            sub_queries.append(f"Recent developments regarding {sanitized}")
        if len(words) >= 2:
            sub_queries.append(f"Risks and implications of {sanitized}")
        if len(words) >= 2:
            sub_queries.append(f"Future outlook for {sanitized}")
        return sub_queries if sub_queries else [sanitized]


class SourceCollector:
    """Gathers evidence from multiple sources (demo: synthetic)."""

    def __init__(self, source_mode: str = "demo"):
        self.source_mode = source_mode

    def collect(self, sub_queries: List[str]) -> tuple:
        """Returns (source_ids, findings)."""
        sources: List[str] = []
        findings: List[Dict[str, Any]] = []

        if self.source_mode == "demo":
            source_pool = [
                "open_source_feed_alpha",
                "academic_db_beta",
                "news_aggregator_gamma",
                "social_signals_delta",
                "government_records_epsilon",
            ]
            for i, sq in enumerate(sub_queries):
                src = source_pool[i % len(source_pool)]
                if src not in sources:
                    sources.append(src)
                # Deterministic synthetic evidence
                seed = hashlib.sha256(sq.encode("utf-8")).hexdigest()[:8]
                relevance = round(0.5 + (int(seed, 16) % 50) / 100.0, 2)
                findings.append({
                    "sub_query": sq,
                    "source": src,
                    "evidence": f"[DEMO] Synthetic evidence for sub-query: '{sq}' "
                                f"(seed={seed}). In production this would contain "
                                f"real intelligence data from {src}.",
                    "relevance": min(relevance, 1.0),
                })
        else:
            raise ValueError(
                f"Unsupported source mode: {self.source_mode}. Use 'demo'."
            )

        return sources, findings


class IntelligenceSynthesizer:
    """Merges findings into a coherent intelligence report."""

    def synthesize(
        self,
        query: str,
        sub_queries: List[str],
        sources: List[str],
        findings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        # Compute average relevance as confidence proxy
        relevances = [f["relevance"] for f in findings if "relevance" in f]
        confidence = round(sum(relevances) / len(relevances), 2) if relevances else 0.0

        synthesis_parts = []
        for f in findings:
            synthesis_parts.append(
                f"From {f['source']}: {f['evidence']}"
            )
        synthesis = (
            f"Intelligence synthesis for '{sanitize_input(query)}': "
            f"Analyzed {len(findings)} findings across {len(sources)} sources. "
            + " | ".join(synthesis_parts[:3])
            + (f" ... and {len(synthesis_parts) - 3} more findings."
               if len(synthesis_parts) > 3 else "")
        )

        result = {
            "query": sanitize_input(query),
            "sub_queries": sub_queries,
            "sources": sources,
            "findings": findings,
            "synthesis": synthesis,
            "confidence_level": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not validate_output(result):
            raise RuntimeError("Output validation failed against expected schema.")

        return result


# ---------- CLI ----------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="intelligence-query: Multi-source intelligence analysis engine"
    )
    parser.add_argument(
        "--topic", required=True, type=str,
        help="The intelligence query topic"
    )
    parser.add_argument(
        "--sources", default="demo", choices=["demo"],
        help="Source mode (default: demo)"
    )
    parser.add_argument(
        "--output", required=True, type=str,
        help="Output file path for JSON report"
    )
    parser.add_argument(
        "--format", default="json", choices=["json"],
        help="Output format (default: json)"
    )
    args = parser.parse_args()

    # Validate CLI-provided output path
    def _safe_path(base_dir: Path, user_path: str) -> Path:
        resolved = Path(user_path).resolve()
        base = Path(base_dir).resolve()
        if not str(resolved).startswith(str(base) + os.sep) and resolved != base:
            raise ValueError(f"Path {user_path} escapes allowed directory {base_dir}")
        return resolved

    cwd = Path.cwd()
    output_path = _safe_path(cwd, args.output)

    decomposer = QueryDecomposer()
    collector = SourceCollector(source_mode=args.sources)
    synthesizer = IntelligenceSynthesizer()

    sub_queries = decomposer.decompose(args.topic)
    sources, findings = collector.collect(sub_queries)
    report = synthesizer.synthesize(args.topic, sub_queries, sources, findings)

    output_json = json.dumps(report, indent=2, ensure_ascii=False)

    with open(str(output_path), "w", encoding="utf-8") as f:
        f.write(output_json)

    print(f"Intelligence report written to {output_path}")
    print(f"Confidence level: {report['confidence_level']}")
    print(f"Sub-queries analyzed: {len(sub_queries)}")
    print(f"Sources consulted: {len(sources)}")


if __name__ == "__main__":
    main()
