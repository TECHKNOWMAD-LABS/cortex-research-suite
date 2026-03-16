"""De-slop CLI — detect and remove AI-generated writing patterns.

Usage:
    de-slop check <file>
    de-slop scan <directory>
    de-slop check <file> --output json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import click
except ImportError:
    print("Error: click is required. Install with: pip install click", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Slop pattern definitions
# ---------------------------------------------------------------------------

SLOP_PATTERNS: list[dict[str, Any]] = [
    {
        "id": "emoji_headers",
        "name": "Emoji in headers",
        "pattern": r"^#+\s.*[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]",
        "severity": "medium",
        "description": "Emojis in markdown headers are a telltale sign of AI-generated content",
    },
    {
        "id": "hyperbolic_language",
        "name": "Hyperbolic language",
        "pattern": r"\b(groundbreaking|revolutionary|game-?changing|cutting-?edge|world-?class|best-in-class|next-?gen(?:eration)?|paradigm.?shift)\b",
        "severity": "high",
        "description": "Overuse of superlatives and buzzwords typical of AI slop",
    },
    {
        "id": "defensive_framing",
        "name": "Defensive framing",
        "pattern": r"\b(it(')?s (important|worth|crucial) to note|it should be noted|one might argue|to be fair)\b",
        "severity": "medium",
        "description": "Hedging and defensive language patterns common in AI output",
    },
    {
        "id": "buzzword_stacking",
        "name": "Buzzword stacking",
        "pattern": r"\b(leverage|synerg|holistic|robust|scalable|seamless|enterprise-grade|mission-critical)\b",
        "severity": "medium",
        "description": "Stacking corporate buzzwords without substance",
    },
    {
        "id": "motivational_fluff",
        "name": "Motivational fluff",
        "pattern": r"\b(unlock the (full )?potential|take .+ to the next level|empower|transform the way)\b",
        "severity": "high",
        "description": "Empty motivational language with no technical content",
    },
    {
        "id": "filler_transitions",
        "name": "Filler transitions",
        "pattern": r"\b(in today(')?s (rapidly )?(evolving|changing)|in (the|this) (modern|digital) (era|age|landscape)|at the end of the day)\b",
        "severity": "low",
        "description": "Generic filler transitions that add no information",
    },
    {
        "id": "exclamation_overuse",
        "name": "Exclamation overuse",
        "pattern": r"!\s*\n.*!\s*\n",
        "severity": "low",
        "description": "Multiple exclamation marks in close proximity",
    },
]


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


def scan_text(text: str, filename: str = "<stdin>") -> list[dict[str, Any]]:
    """Scan text for slop patterns. Returns list of findings."""
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()

    for pattern_def in SLOP_PATTERNS:
        regex = re.compile(pattern_def["pattern"], re.IGNORECASE | re.MULTILINE)
        for i, line in enumerate(lines, 1):
            for match in regex.finditer(line):
                findings.append(
                    {
                        "file": filename,
                        "line": i,
                        "column": match.start() + 1,
                        "pattern_id": pattern_def["id"],
                        "pattern_name": pattern_def["name"],
                        "severity": pattern_def["severity"],
                        "matched_text": match.group()[:80],
                        "description": pattern_def["description"],
                    }
                )

    return findings


def compute_slop_score(findings: list[dict[str, Any]], total_lines: int) -> int:
    """Compute a 0-100 slop score. 0 = clean, 100 = pure slop."""
    if total_lines == 0:
        return 0
    severity_weights = {"low": 1, "medium": 3, "high": 5}
    raw = sum(severity_weights.get(f["severity"], 1) for f in findings)
    normalized = min(100, int(raw / max(total_lines, 1) * 100))
    return normalized


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


@click.group()
def main():
    """De-slop: detect AI-generated writing patterns in text files."""
    pass


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", type=click.Choice(["text", "json"]), default="text", help="Output format")
def check(file: str, output: str):
    """Check a single file for AI slop patterns."""
    path = Path(file)
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = scan_text(text, filename=str(path))
    lines = text.splitlines()
    score = compute_slop_score(findings, len(lines))

    if output == "json":
        result = {
            "file": str(path),
            "slop_score": score,
            "findings_count": len(findings),
            "findings": findings,
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"File: {path}")
        click.echo(f"Slop score: {score}/100")
        click.echo(f"Findings: {len(findings)}")
        for f in findings:
            click.echo(
                f'  L{f["line"]}:{f["column"]} [{f["severity"].upper()}] {f["pattern_name"]}: "{f["matched_text"]}"'
            )
        if not findings:
            click.echo("  No slop patterns detected ✓")


@main.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--output", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--ext", multiple=True, default=(".md", ".txt", ".rst"), help="File extensions to scan")
def scan(directory: str, output: str, ext: tuple):
    """Scan a directory for AI slop patterns."""
    dir_path = Path(directory)
    all_findings: list[dict[str, Any]] = []
    file_scores: dict[str, int] = {}

    for ext_pattern in ext:
        for file_path in dir_path.rglob(f"*{ext_pattern}"):
            text = file_path.read_text(encoding="utf-8", errors="replace")
            findings = scan_text(text, filename=str(file_path))
            all_findings.extend(findings)
            file_scores[str(file_path)] = compute_slop_score(findings, len(text.splitlines()))

    if output == "json":
        result = {
            "directory": str(dir_path),
            "files_scanned": len(file_scores),
            "total_findings": len(all_findings),
            "file_scores": file_scores,
            "findings": all_findings,
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Scanned: {len(file_scores)} files in {dir_path}")
        click.echo(f"Total findings: {len(all_findings)}")
        for fp, score in sorted(file_scores.items(), key=lambda x: x[1], reverse=True):
            count = sum(1 for f in all_findings if f["file"] == fp)
            if count > 0:
                click.echo(f"  [{score:3d}] {fp} ({count} findings)")


if __name__ == "__main__":
    main()
