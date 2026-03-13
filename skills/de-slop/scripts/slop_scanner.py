#!/usr/bin/env python3
"""
Production-grade slop detection scanner for de-slop skill.

Analyzes markdown/text files for marketing fluff, hyperbole, defensive language,
buzzwords, motivational filler, and other low-value content patterns.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Pattern:
    """Compiled regex pattern with metadata."""
    name: str
    category: str
    weight: int
    regex: re.Pattern
    suggestion_template: str


@dataclass
class Finding:
    """Individual pattern match in a file."""
    file: str
    line: int
    category: str
    pattern: str
    text: str
    weight: int
    suggestion: str


@dataclass
class FileSummary:
    """Summary statistics for a single file."""
    file: str
    score: float
    flags: int
    verdict: str


class SlopScanner:
    """Main scanner class for detecting slop patterns."""

    # Verdict thresholds
    VERDICT_THRESHOLDS = {
        "PASS": (0, 15),
        "WARN": (16, 40),
        "FAIL": (41, 100),
    }

    def __init__(self, threshold: int = 40):
        """Initialize scanner with pattern library and threshold.

        Args:
            threshold: Slop score threshold for FAIL verdict (default 40).
        """
        self.threshold = threshold
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> List[Pattern]:
        """Build comprehensive pattern library with compiled regexes.

        Returns:
            List of Pattern objects ready for matching.
        """
        patterns = []

        # STRUCTURAL (weight 3)
        patterns.append(
            Pattern(
                name="emoji_in_headers",
                category="STRUCTURAL",
                weight=3,
                regex=re.compile(
                    r"^#+\s+.*[\U0001F300-\U0001F9FF]",
                    re.MULTILINE,
                ),
                suggestion_template="Remove emoji from headers: '# Feature 🚀' → '# Feature'",
            )
        )

        patterns.append(
            Pattern(
                name="excessive_bold_lists",
                category="STRUCTURAL",
                weight=3,
                regex=re.compile(
                    r"^[-*+]\s+(?:\*\*.+?\*\*\s*)+",
                    re.MULTILINE,
                ),
                suggestion_template="Reduce bold formatting in list items; use bold only for key terms",
            )
        )

        patterns.append(
            Pattern(
                name="sentence_headers",
                category="STRUCTURAL",
                weight=3,
                regex=re.compile(
                    r"^#{2,3}\s+.{0,}?[\w\s]{50,}$",
                    re.MULTILINE,
                ),
                suggestion_template="Break long header into shorter, focused title: keep to 8 words max",
            )
        )

        # HYPERBOLIC (weight 2)
        power_words = (
            "revolutionary|game-changing|cutting-edge|world-class|domination|"
            "groundbreaking|transformative|unleash|supercharge|skyrocket|turbocharge"
        )
        patterns.append(
            Pattern(
                name="power_words",
                category="HYPERBOLIC",
                weight=2,
                regex=re.compile(
                    rf"\b({power_words})\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Replace hyperbolic term with concrete claim: 'revolutionary' → 'faster' or 'more reliable'",
            )
        )

        patterns.append(
            Pattern(
                name="unsupported_superlatives",
                category="HYPERBOLIC",
                weight=2,
                regex=re.compile(
                    r"\b(?:the\s+most|the\s+best|unparalleled|unmatched|second\s+to\s+none)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Replace superlative with specific metric: 'the best' → '30% faster than v1.0'",
            )
        )

        patterns.append(
            Pattern(
                name="marketing_in_tech",
                category="HYPERBOLIC",
                weight=2,
                regex=re.compile(
                    r"\b(?:take\s+it\s+to\s+the\s+next\s+level|"
                    r"unlock\s+the\s+power|harness\s+the\s+potential)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Replace marketing phrase with technical description of what it does",
            )
        )

        # DEFENSIVE (weight 2)
        patterns.append(
            Pattern(
                name="defensive_opening",
                category="DEFENSIVE",
                weight=2,
                regex=re.compile(
                    r"\b(?:This\s+is\s+not\s+a|This\s+isn't\s+just|"
                    r"Not\s+just\s+another|More\s+than\s+a)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Lead with what it IS, not what it ISN'T: 'Not just a logger' → 'Structured logger with tracing'",
            )
        )

        patterns.append(
            Pattern(
                name="unprompted_comparison",
                category="DEFENSIVE",
                weight=2,
                regex=re.compile(
                    r"\b(?:Unlike\s+other|What\s+sets\s+.+?\s+apart|While\s+others)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Remove unsolicited comparison; let features speak for themselves",
            )
        )

        patterns.append(
            Pattern(
                name="preemptive_objection",
                category="DEFENSIVE",
                weight=2,
                regex=re.compile(
                    r"\b(?:You\s+might\s+think|You\s+may\s+wonder|Some\s+might\s+say)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Remove preemptive objection; address only concerns directly mentioned by users",
            )
        )

        # BUZZWORDS (weight 2)
        buzzwords = (
            "enterprise-grade|production-ready|battle-tested|deployment-grade|"
            "mission-critical|industrial-strength|military-grade"
        )
        patterns.append(
            Pattern(
                name="buzzword_stacking",
                category="BUZZWORDS",
                weight=2,
                regex=re.compile(
                    rf"\b({buzzwords})\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Remove overused qualifier; 'production-ready' alone adds little value",
            )
        )

        empty_modifiers = (
            "robust|seamless|elegant|scalable|leveraging|leverage|leveraged|"
            "synergy|synergize|holistic|paradigm"
        )
        patterns.append(
            Pattern(
                name="empty_modifiers",
                category="BUZZWORDS",
                weight=2,
                regex=re.compile(
                    rf"\b({empty_modifiers})\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Replace vague modifier with measurable attribute: 'scalable' → 'supports 100k+ concurrent'",
            )
        )

        patterns.append(
            Pattern(
                name="redundant_autonomy",
                category="BUZZWORDS",
                weight=2,
                regex=re.compile(
                    r"\b(?:fully\s+autonomous\s+zero-human-intervention|"
                    r"complete\s+end-to-end\s+fully\s+automated)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Say it once: 'fully autonomous, zero human intervention' → 'fully autonomous'",
            )
        )

        # MOTIVATIONAL (weight 1)
        patterns.append(
            Pattern(
                name="aspirational",
                category="MOTIVATIONAL",
                weight=1,
                regex=re.compile(
                    r"\b(?:who\s+refuse\s+to\s+be\s+average|dare\s+to|"
                    r"for\s+those\s+who\s+demand\s+excellence|join\s+the\s+revolution)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Remove aspirational appeal; let technical merit speak to your audience",
            )
        )

        patterns.append(
            Pattern(
                name="urgency_filler",
                category="MOTIVATIONAL",
                weight=1,
                regex=re.compile(
                    r"\b(?:In\s+today's\s+rapidly|As\s+we\s+navigate|In\s+an\s+era\s+of)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Remove temporal filler; jump directly to the point",
            )
        )

        # FILLER (weight 1)
        patterns.append(
            Pattern(
                name="throat_clearing",
                category="FILLER",
                weight=1,
                regex=re.compile(
                    r"\b(?:It's\s+worth\s+noting|At\s+the\s+end\s+of\s+the\s+day|"
                    r"Let's\s+dive\s+in|Let's\s+explore|Without\s+further\s+ado)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Delete filler phrase and move to substantive content",
            )
        )

        patterns.append(
            Pattern(
                name="certainty_markers",
                category="FILLER",
                weight=1,
                regex=re.compile(
                    r"\b(?:certainly|absolutely|undeniably|without\s+a\s+doubt)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Remove empty certainty marker; let facts persuade",
            )
        )

        patterns.append(
            Pattern(
                name="filler_adverbs",
                category="FILLER",
                weight=1,
                regex=re.compile(
                    r"\b(?:basically|essentially|fundamentally|literally)\b",
                    re.IGNORECASE,
                ),
                suggestion_template="Delete filler adverb; say exactly what you mean instead",
            )
        )

        # REPETITIVE (weight 1)
        patterns.append(
            Pattern(
                name="never_repetition",
                category="REPETITIVE",
                weight=1,
                regex=re.compile(
                    r"^[-*+]\s+(?:Never|Always)\s+.+$",
                    re.MULTILINE,
                ),
                suggestion_template="Vary list structure; alternate with other patterns or organize differently",
            )
        )

        patterns.append(
            Pattern(
                name="parallel_starts",
                category="REPETITIVE",
                weight=1,
                regex=re.compile(
                    r"^[A-Z].+$",
                    re.MULTILINE,
                ),
                suggestion_template="Vary paragraph openings to improve readability",
            )
        )

        return patterns

    def scan_file(self, filepath: Path) -> Tuple[float, List[Finding]]:
        """Scan a single file for slop patterns.

        Args:
            filepath: Path to file to scan.

        Returns:
            Tuple of (score, findings list).
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, OSError) as e:
            print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
            return 0.0, []

        lines = content.split("\n")
        findings: List[Finding] = []
        total_weight = 0

        for pattern in self.patterns:
            for match in pattern.regex.finditer(content):
                # Find line number of match
                line_num = content[: match.start()].count("\n") + 1
                matched_text = match.group(0)[:100]  # Truncate for display

                finding = Finding(
                    file=str(filepath),
                    line=line_num,
                    category=pattern.category,
                    pattern=pattern.name,
                    text=matched_text,
                    weight=pattern.weight,
                    suggestion=pattern.suggestion_template,
                )
                findings.append(finding)
                total_weight += pattern.weight

        # Calculate score: (total_weight / max(lines, 1)) * 100, clamped to 0-100
        max_lines = max(len(lines), 1)
        score = min(100.0, (total_weight / max_lines) * 100)

        return score, findings

    def scan_directory(
        self, target_dir: Path
    ) -> Tuple[List[FileSummary], List[Finding]]:
        """Recursively scan directory for slop patterns.

        Args:
            target_dir: Directory to scan.

        Returns:
            Tuple of (file summaries, all findings).
        """
        if not target_dir.is_dir():
            raise ValueError(f"Target is not a directory: {target_dir}")

        summaries: List[FileSummary] = []
        all_findings: List[Finding] = []

        # Scan markdown and text files
        for filepath in sorted(target_dir.rglob("*")):
            if filepath.is_file() and filepath.suffix in {".md", ".txt", ".mdx"}:
                score, findings = self.scan_file(filepath)

                # Determine verdict
                verdict = "PASS"
                for v, (low, high) in self.VERDICT_THRESHOLDS.items():
                    if low <= score <= high:
                        verdict = v
                        break

                summary = FileSummary(
                    file=str(filepath.relative_to(target_dir)),
                    score=round(score, 2),
                    flags=len(findings),
                    verdict=verdict,
                )
                summaries.append(summary)
                all_findings.extend(findings)

        return summaries, all_findings

    def generate_json_report(
        self,
        summaries: List[FileSummary],
        findings: List[Finding],
        target_dir: Path,
    ) -> Dict:
        """Generate JSON report.

        Args:
            summaries: File summaries.
            findings: All findings.
            target_dir: Scanned directory.

        Returns:
            Report dictionary.
        """
        return {
            "target": str(target_dir),
            "date": datetime.now().isoformat(),
            "files_scanned": len(summaries),
            "summary": [asdict(s) for s in summaries],
            "findings": [asdict(f) for f in findings],
        }

    def generate_markdown_report(
        self,
        summaries: List[FileSummary],
        findings: List[Finding],
        target_dir: Path,
    ) -> str:
        """Generate markdown report.

        Args:
            summaries: File summaries.
            findings: All findings.
            target_dir: Scanned directory.

        Returns:
            Markdown report string.
        """
        lines = [
            "# De-Slop Scan Report",
            "",
            f"**Target:** {target_dir}",
            f"**Date:** {datetime.now().isoformat()}",
            f"**Files Scanned:** {len(summaries)}",
            "",
        ]

        # Summary table
        lines.extend(
            [
                "## Summary",
                "",
                "| File | Score | Flags | Verdict |",
                "|------|-------|-------|---------|",
            ]
        )

        for summary in summaries:
            lines.append(
                f"| {summary.file} | {summary.score} | {summary.flags} | {summary.verdict} |"
            )

        lines.extend(["", "## Findings", ""])

        if not findings:
            lines.append("No slop patterns detected.")
        else:
            # Group findings by file
            findings_by_file: Dict[str, List[Finding]] = {}
            for finding in findings:
                if finding.file not in findings_by_file:
                    findings_by_file[finding.file] = []
                findings_by_file[finding.file].append(finding)

            for filepath in sorted(findings_by_file.keys()):
                lines.append(f"### {filepath}")
                lines.append("")

                for finding in findings_by_file[filepath]:
                    lines.extend(
                        [
                            f"**Line {finding.line}** | {finding.category} | {finding.pattern}",
                            "",
                            f"Found: `{finding.text}`",
                            "",
                            f"**Suggestion:** {finding.suggestion}",
                            "",
                        ]
                    )

        return "\n".join(lines)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Detect marketing fluff and low-value patterns in documentation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--target",
        type=Path,
        required=True,
        help="Directory to scan (required)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./slop-report"),
        help="Base path for reports (default: ./slop-report)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "md", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=40,
        help="Slop score threshold for FAIL verdict (default: 40)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Output suggested fixes alongside flags (default: enabled for all formats)",
    )

    args = parser.parse_args()

    # Validate target
    if not args.target.exists():
        print(f"Error: Target directory does not exist: {args.target}", file=sys.stderr)
        return 1

    if not args.target.is_dir():
        print(f"Error: Target is not a directory: {args.target}", file=sys.stderr)
        return 1

    # Create scanner and scan
    try:
        scanner = SlopScanner(threshold=args.threshold)
        summaries, findings = scanner.scan_directory(args.target)
    except Exception as e:
        print(f"Error during scan: {e}", file=sys.stderr)
        return 1

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Generate reports
    if args.format in {"json", "both"}:
        json_report = scanner.generate_json_report(summaries, findings, args.target)
        json_path = args.output.parent / f"{args.output.name}.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_report, f, indent=2)
            print(f"JSON report written to {json_path}")
        except OSError as e:
            print(f"Error writing JSON report: {e}", file=sys.stderr)
            return 1

    if args.format in {"md", "both"}:
        md_report = scanner.generate_markdown_report(
            summaries, findings, args.target
        )
        md_path = args.output.parent / f"{args.output.name}.md"
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_report)
            print(f"Markdown report written to {md_path}")
        except OSError as e:
            print(f"Error writing markdown report: {e}", file=sys.stderr)
            return 1

    # Print summary to stdout
    print("\n=== SCAN SUMMARY ===")
    print(f"Files scanned: {len(summaries)}")
    print(f"Total findings: {len(findings)}")
    if summaries:
        passes = sum(1 for s in summaries if s.verdict == "PASS")
        warns = sum(1 for s in summaries if s.verdict == "WARN")
        fails = sum(1 for s in summaries if s.verdict == "FAIL")
        print(f"PASS: {passes} | WARN: {warns} | FAIL: {fails}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
