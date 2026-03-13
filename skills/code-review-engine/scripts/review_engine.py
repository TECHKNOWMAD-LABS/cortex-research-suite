#!/usr/bin/env python3
"""
Code Review Engine: Two-stage review system for spec compliance and code quality.

Stages:
1. Spec Compliance: Validates implementation against specification
2. Code Quality: Analyzes code for correctness, performance, security, maintainability

Usage:
    python3 review_engine.py review --spec spec.md --target src/ --output review.md
"""

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class Issue:
    """Represents a single code review issue."""

    SEVERITY_LEVELS = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3}

    def __init__(
        self,
        severity: str,
        category: str,
        file: str,
        line: int,
        title: str,
        description: str,
        suggestion: Optional[str] = None,
    ):
        self.severity = severity
        self.category = category
        self.file = file
        self.line = line
        self.title = title
        self.description = description
        self.suggestion = suggestion

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.title} ({self.file}:{self.line})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion,
        }


class ComplianceGap:
    """Represents a spec compliance gap."""

    def __init__(
        self,
        gap_type: str,  # MISSING, INCORRECT, EXTRA
        requirement: str,
        spec_section: str,
        details: str,
    ):
        self.gap_type = gap_type
        self.requirement = requirement
        self.spec_section = spec_section
        self.details = details

    def __repr__(self) -> str:
        return f"[{self.gap_type}] {self.requirement} ({self.spec_section})"


class SpecComplianceChecker:
    """Stage 1: Validates implementation against specification."""

    def __init__(self, spec_path: Path):
        self.spec_path = spec_path
        self.requirements: Dict[str, Dict[str, str]] = {}
        self.parse_spec()

    def parse_spec(self) -> None:
        """Parse markdown specification to extract requirements."""
        if not self.spec_path.exists():
            return

        content = self.spec_path.read_text()
        lines = content.split("\n")

        current_req_id = None
        current_section = None
        current_details = []

        for line in lines:
            # Match REQ-N pattern
            req_match = re.match(r"^#+\s+(REQ-\d+):\s+(.*)", line)
            if req_match:
                if current_req_id:
                    self.requirements[current_req_id] = {
                        "title": current_details[0] if current_details else "",
                        "details": "\n".join(current_details[1:]),
                        "section": current_section,
                    }
                current_req_id = req_match.group(1)
                current_details = [req_match.group(2)]
                continue

            # Match section headers
            section_match = re.match(r"^#+\s+([^#]+)$", line)
            if section_match and not re.match(r"^#+\s+REQ-", line):
                current_section = section_match.group(1)
                continue

            # Accumulate details
            if current_req_id and line.strip():
                current_details.append(line)

        # Store last requirement
        if current_req_id:
            self.requirements[current_req_id] = {
                "title": current_details[0] if current_details else "",
                "details": "\n".join(current_details[1:]),
                "section": current_section,
            }

    def check_compliance(
        self, target_path: Path, implementation_files: List[Path]
    ) -> Tuple[float, List[ComplianceGap]]:
        """
        Check implementation against spec requirements.

        Returns:
            Tuple of (compliance_score: 0-100, gaps: list of ComplianceGap)
        """
        gaps: List[ComplianceGap] = []

        if not self.requirements:
            return 100.0, gaps

        # Read all implementation files
        impl_content = self._read_files(implementation_files)

        for req_id, req_data in self.requirements.items():
            title = req_data["title"]
            details = req_data["details"]
            section = req_data["section"] or "Requirements"

            # Look for requirement markers in code
            if not self._find_requirement_in_code(req_id, title, impl_content):
                gaps.append(
                    ComplianceGap(
                        gap_type="MISSING",
                        requirement=title,
                        spec_section=section,
                        details=f"No implementation found for {req_id}",
                    )
                )

        # Calculate compliance score
        if self.requirements:
            compliance_score = (
                (len(self.requirements) - len(gaps)) / len(self.requirements)
            ) * 100
        else:
            compliance_score = 100.0

        return compliance_score, gaps

    def _read_files(self, file_paths: List[Path]) -> str:
        """Read and concatenate all file contents."""
        content = []
        for fpath in file_paths:
            if fpath.is_file():
                try:
                    content.append(fpath.read_text())
                except (UnicodeDecodeError, IOError):
                    pass
        return "\n".join(content)

    def _find_requirement_in_code(
        self, req_id: str, title: str, code: str
    ) -> bool:
        """Check if requirement appears to be implemented in code."""
        # Extract function/class name from requirement title
        # Example: "Login Function" -> look for "login" function
        name_parts = title.lower().split()
        name_match = name_parts[0] if name_parts else ""

        # Look for function definitions, class definitions, or comments mentioning requirement
        patterns = [
            f"def {name_match}",
            f"class {name_match.capitalize()}",
            f"{req_id}",
            f"# {req_id}",
            f"# {title}",
        ]

        for pattern in patterns:
            if pattern.lower() in code.lower():
                return True

        return False


class CodeQualityScanner(ast.NodeVisitor):
    """Stage 2: Analyzes code quality using AST analysis."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.issues: List[Issue] = []
        self.functions: List[Tuple[str, int, int]] = []  # name, line, length
        self.imports: List[str] = []
        self.security_patterns = {
            "sql_injection": [
                r"execute\s*\(\s*['\"].*%",
                r"query\s*=\s*['\"].*%",
                r"\.format\s*\(\s*.*user",
            ],
            "hardcoded_secrets": [
                r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
                r"(password|secret|api_key|token):\s*['\"][^'\"]+['\"]",
            ],
            "unsafe_eval": [r"\beval\s*\(", r"\bexec\s*\("],
            "hardcoded_paths": [r"(password|key|secret):\s*['\"].*[/\\]"],
        }

    def scan(self) -> List[Issue]:
        """Scan file for quality issues."""
        if not self.file_path.exists():
            return self.issues

        try:
            content = self.file_path.read_text()
            tree = ast.parse(content)
            self.visit(tree)
            self._check_security_patterns(content)
            self._check_style(content)
        except SyntaxError as e:
            self.issues.append(
                Issue(
                    severity="MAJOR",
                    category="Correctness",
                    file=str(self.file_path),
                    line=e.lineno or 0,
                    title="Syntax Error",
                    description=f"File has syntax errors: {e.msg}",
                )
            )

        return self.issues

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definitions."""
        # Check function length
        func_length = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
        self.functions.append((node.name, node.lineno, func_length))

        if func_length > 50:
            self.issues.append(
                Issue(
                    severity="MINOR",
                    category="Maintainability",
                    file=str(self.file_path),
                    line=node.lineno,
                    title=f"Function too long ({func_length} lines)",
                    description=f"Function '{node.name}' exceeds 50-line guideline",
                    suggestion="Extract smaller helper functions or break into logical sections",
                )
            )

        # Check cyclomatic complexity
        complexity = self._calculate_complexity(node)
        if complexity > 10:
            self.issues.append(
                Issue(
                    severity="MINOR",
                    category="Maintainability",
                    file=str(self.file_path),
                    line=node.lineno,
                    title=f"High cyclomatic complexity ({complexity})",
                    description=f"Function '{node.name}' has complexity of {complexity}",
                    suggestion="Reduce branches by extracting methods or using polymorphism",
                )
            )

        # Check for missing docstring
        docstring = ast.get_docstring(node)
        if node.name.startswith("_") is False and not docstring:
            self.issues.append(
                Issue(
                    severity="MINOR",
                    category="Maintainability",
                    file=str(self.file_path),
                    line=node.lineno,
                    title="Missing docstring",
                    description=f"Public function '{node.name}' lacks documentation",
                    suggestion='Add docstring explaining function purpose, parameters, and return value',
                )
            )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Track imports."""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from imports."""
        if node.module:
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _check_security_patterns(self, content: str) -> None:
        """Check for common security vulnerabilities."""
        lines = content.split("\n")

        # Check for SQL injection
        for i, line in enumerate(lines, 1):
            for pattern in self.security_patterns["sql_injection"]:
                if re.search(pattern, line):
                    self.issues.append(
                        Issue(
                            severity="CRITICAL",
                            category="Security",
                            file=str(self.file_path),
                            line=i,
                            title="Potential SQL injection",
                            description=f"SQL query with user input: {line.strip()[:50]}",
                            suggestion="Use parameterized queries with placeholders (?)",
                        )
                    )

            # Check for hardcoded secrets
            for pattern in self.security_patterns["hardcoded_secrets"]:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append(
                        Issue(
                            severity="CRITICAL",
                            category="Security",
                            file=str(self.file_path),
                            line=i,
                            title="Hardcoded secret",
                            description="Credentials or secrets hardcoded in source",
                            suggestion="Use environment variables or secrets management system",
                        )
                    )

            # Check for unsafe eval/exec
            for pattern in self.security_patterns["unsafe_eval"]:
                if re.search(pattern, line):
                    self.issues.append(
                        Issue(
                            severity="CRITICAL",
                            category="Security",
                            file=str(self.file_path),
                            line=i,
                            title="Unsafe eval/exec usage",
                            description=f"Dangerous dynamic code execution: {line.strip()}",
                            suggestion="Avoid eval/exec; use safe alternatives like ast.literal_eval",
                        )
                    )

    def _check_style(self, content: str) -> None:
        """Check code style conventions."""
        lines = content.split("\n")

        # Check for unused imports
        import_lines = set()
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                import_lines.add(i)

        # Simple check: look for imports that don't appear later
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("import "):
                module = line.split()[1].split(",")[0]
                if not any(module in other for j, other in enumerate(lines) if j != i - 1):
                    # This is a simplified check - in production would use more sophisticated analysis
                    pass

        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line and line != line.rstrip():
                self.issues.append(
                    Issue(
                        severity="INFO",
                        category="Style",
                        file=str(self.file_path),
                        line=i,
                        title="Trailing whitespace",
                        description="Line contains trailing whitespace",
                        suggestion="Remove trailing whitespace",
                    )
                )


class ReviewReportGenerator:
    """Generates markdown review reports."""

    def __init__(self):
        self.spec_score = 0.0
        self.spec_gaps: List[ComplianceGap] = []
        self.quality_issues: List[Issue] = []

    def generate(self, output_path: Path) -> str:
        """Generate markdown review report."""
        report_lines = [
            "# Code Review Report",
            "",
            f"**Generated**: {datetime.now().isoformat()}",
            "",
            "## Review Summary",
            "",
        ]

        # Summary statistics
        report_lines.append(f"- **Spec Compliance**: {self.spec_score:.0f}%")
        if self.spec_gaps:
            report_lines.append(f"  - {len(self.spec_gaps)} gaps found")

        # Count issues by severity
        severity_counts = defaultdict(int)
        for issue in self.quality_issues:
            severity_counts[issue.severity] += 1

        if self.quality_issues:
            total_issues = len(self.quality_issues)
            report_lines.append(f"- **Code Quality**: {total_issues} issues")
            report_lines.append(
                f"  - CRITICAL: {severity_counts['CRITICAL']}, "
                f"MAJOR: {severity_counts['MAJOR']}, "
                f"MINOR: {severity_counts['MINOR']}, "
                f"INFO: {severity_counts['INFO']}"
            )

        # Determine verdict
        verdict = self._determine_verdict()
        report_lines.append(f"- **VERDICT**: {verdict}")
        report_lines.append("")

        # Spec compliance section
        if self.spec_gaps:
            report_lines.append("## Spec Compliance Gaps")
            report_lines.append("")
            for i, gap in enumerate(self.spec_gaps, 1):
                report_lines.append(f"{i}. [{gap.gap_type}] {gap.requirement}")
                report_lines.append(f"   - Section: {gap.spec_section}")
                report_lines.append(f"   - Details: {gap.details}")
                report_lines.append("")

        # Code quality section
        if self.quality_issues:
            report_lines.append("## Code Quality Issues")
            report_lines.append("")

            # Group by severity
            for severity in ["CRITICAL", "MAJOR", "MINOR", "INFO"]:
                issues_by_severity = [
                    i for i in self.quality_issues if i.severity == severity
                ]
                if issues_by_severity:
                    report_lines.append(f"### {severity} Issues")
                    report_lines.append("")
                    for i, issue in enumerate(issues_by_severity, 1):
                        report_lines.append(f"**{i}. {issue.title}**")
                        report_lines.append(f"- File: `{issue.file}:{issue.line}`")
                        report_lines.append(f"- Category: {issue.category}")
                        report_lines.append(f"- Description: {issue.description}")
                        if issue.suggestion:
                            report_lines.append(f"- Suggestion: {issue.suggestion}")
                        report_lines.append("")

        report_content = "\n".join(report_lines)

        if output_path:
            output_path.write_text(report_content)

        return report_content

    def _determine_verdict(self) -> str:
        """Determine review verdict based on issues."""
        critical_issues = [i for i in self.quality_issues if i.severity == "CRITICAL"]
        spec_failing = self.spec_score < 100.0

        if critical_issues or spec_failing:
            return "❌ CHANGES REQUESTED"
        elif any(i.severity == "MAJOR" for i in self.quality_issues):
            return "⚠️  CHANGES REQUESTED"
        elif self.quality_issues:
            return "✓ APPROVED WITH SUGGESTIONS"
        else:
            return "✓ APPROVED"


def find_python_files(target_path: Path) -> List[Path]:
    """Recursively find all Python files."""
    if target_path.is_file() and target_path.suffix == ".py":
        return [target_path]
    elif target_path.is_dir():
        return list(target_path.rglob("*.py"))
    return []


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Two-stage code review engine: spec compliance + code quality"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Review command
    review_parser = subparsers.add_parser("review", help="Run code review")
    review_parser.add_argument(
        "--spec", type=Path, help="Path to specification file (markdown)"
    )
    review_parser.add_argument(
        "--target", type=Path, required=True, help="Path to code directory or file"
    )
    review_parser.add_argument(
        "--output", type=Path, help="Path to save review report (markdown)"
    )
    review_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on MAJOR issues (default: fail only on CRITICAL)",
    )

    args = parser.parse_args()

    if args.command != "review":
        parser.print_help()
        return 1

    # Find Python files to review
    python_files = find_python_files(args.target)
    if not python_files:
        print(f"No Python files found in {args.target}")
        return 1

    # Stage 1: Spec Compliance Check
    generator = ReviewReportGenerator()

    if args.spec:
        checker = SpecComplianceChecker(args.spec)
        score, gaps = checker.check_compliance(args.target, python_files)
        generator.spec_score = score
        generator.spec_gaps = gaps

    # Stage 2: Code Quality Scan
    for py_file in python_files:
        scanner = CodeQualityScanner(py_file)
        generator.quality_issues.extend(scanner.scan())

    # Generate report
    report = generator.generate(args.output)
    print(report)

    # Determine exit code
    critical_issues = [i for i in generator.quality_issues if i.severity == "CRITICAL"]
    major_issues = [i for i in generator.quality_issues if i.severity == "MAJOR"]
    spec_failing = generator.spec_score < 100.0

    if critical_issues or spec_failing:
        return 1
    elif args.strict and major_issues:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
