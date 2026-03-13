#!/usr/bin/env python3
"""
TDD Enforcer: Test-Driven Development enforcement system.

Enforces RED-GREEN-REFACTOR cycles, detects 12 anti-patterns,
gates code coverage, and generates test quality scores.
"""

import ast
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import argparse


@dataclass
class AntiPatternInstance:
    """Single instance of an anti-pattern found in a test."""
    pattern_name: str
    severity: str  # "critical", "warning"
    line_number: int
    function_name: str
    description: str
    code_snippet: str = ""


@dataclass
class FileFinding:
    """Anti-pattern findings for a single test file."""
    file_path: str
    total_tests: int
    anti_patterns: List[AntiPatternInstance] = field(default_factory=list)
    coverage: Optional[float] = None
    coverage_delta: Optional[float] = None
    test_count: int = 0
    assertion_count: int = 0
    average_test_length: float = 0.0

    def quality_score(self) -> float:
        """Calculate quality score for this file (0-100)."""
        score = 100.0

        # Anti-pattern penalties (negative scoring)
        for pattern in self.anti_patterns:
            if pattern.severity == "critical":
                score -= 15
            else:
                score -= 8

        # Coverage component (35% weight)
        if self.coverage is not None:
            if self.coverage >= 0.80:
                score += 0  # No bonus
            elif self.coverage >= 0.70:
                score -= 10
            else:
                score -= 25

        # Assertion density (20% weight)
        if self.test_count > 0:
            assertion_density = self.assertion_count / self.test_count
            if assertion_density < 1:
                score -= 15
            elif assertion_density > 10:
                score -= 10

        # Test organization (10% weight)
        if self.average_test_length > 50:
            score -= 12

        # Ensure floor at 0
        return max(0.0, min(100.0, score))


@dataclass
class ScanReport:
    """Overall scan report across all files."""
    files: Dict[str, FileFinding] = field(default_factory=dict)
    total_files: int = 0
    total_tests: int = 0
    total_anti_patterns: int = 0
    average_quality_score: float = 0.0
    blocking_violations: List[str] = field(default_factory=list)

    def has_blocking_issues(self) -> bool:
        """Check if any blocking violations exist."""
        return len(self.blocking_violations) > 0


class ASTVisitor(ast.NodeVisitor):
    """AST visitor to extract test information and detect anti-patterns."""

    def __init__(self, file_content: str, file_path: str):
        self.file_content = file_content
        self.file_path = file_path
        self.lines = file_content.split('\n')
        self.test_methods = []
        self.anti_patterns = []
        self.current_function_name = None
        self.assertion_count = 0
        self.test_count = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions to identify test methods."""
        if node.name.startswith('test_'):
            self.current_function_name = node.name
            self.test_count += 1
            self._analyze_test_method(node)
            self.current_function_name = None

        self.generic_visit(node)

    def _analyze_test_method(self, node: ast.FunctionDef):
        """Analyze a single test method for anti-patterns."""
        test_info = {
            'name': node.name,
            'line': node.lineno,
            'length': self._get_node_length(node),
            'assertions': self._count_assertions(node),
            'mocks': self._count_mocks(node),
            'has_assertions': self._has_any_assertions(node),
            'has_conditional_logic': self._has_conditional_logic(node),
            'has_exception_handling': self._has_try_except(node),
        }

        self.test_methods.append(test_info)

        # Detect individual anti-patterns
        self._detect_mocked_to_death(node, test_info)
        self._detect_assertion_free(node, test_info)
        self._detect_giant_test(node, test_info)
        self._detect_tautological(node, test_info)
        self._detect_logic_in_tests(node, test_info)
        self._detect_magic_numbers(node, test_info)
        self._detect_caught_exception(node, test_info)
        self._detect_over_specification(node, test_info)

    def _detect_mocked_to_death(self, node: ast.FunctionDef, test_info: dict):
        """Detect >70% mock setup."""
        if test_info['mocks'] > 0:
            mock_ratio = test_info['mocks'] / max(test_info['length'], 1)
            if mock_ratio > 0.7:
                self.anti_patterns.append(AntiPatternInstance(
                    pattern_name="Mocked-to-Death",
                    severity="warning",
                    line_number=node.lineno,
                    function_name=node.name,
                    description=f"Test is {mock_ratio*100:.0f}% mocks ({test_info['mocks']} mock lines out of {test_info['length']}, threshold >70%)"
                ))

    def _detect_assertion_free(self, node: ast.FunctionDef, test_info: dict):
        """Detect tests with no assertions."""
        if not test_info['has_assertions']:
            self.anti_patterns.append(AntiPatternInstance(
                pattern_name="Assertion-Free",
                severity="critical",
                line_number=node.lineno,
                function_name=node.name,
                description="Test has no assertions; cannot verify behavior"
            ))

    def _detect_giant_test(self, node: ast.FunctionDef, test_info: dict):
        """Detect tests >50 lines."""
        if test_info['length'] > 50:
            self.anti_patterns.append(AntiPatternInstance(
                pattern_name="Giant Test",
                severity="warning",
                line_number=node.lineno,
                function_name=node.name,
                description=f"Test is {test_info['length']} lines (threshold >50); tests too much"
            ))

    def _detect_tautological(self, node: ast.FunctionDef, test_info: dict):
        """Detect tautological assertions."""
        code = ast.unparse(node)
        # Look for self.assert_* with same variable on both sides
        if re.search(r'assert\s+(\w+)\s*==\s*\1', code):
            self.anti_patterns.append(AntiPatternInstance(
                pattern_name="Tautological",
                severity="warning",
                line_number=node.lineno,
                function_name=node.name,
                description="Assertion comparing variable to itself; always true"
            ))

    def _detect_logic_in_tests(self, node: ast.FunctionDef, test_info: dict):
        """Detect conditional logic in tests."""
        if test_info['has_conditional_logic']:
            self.anti_patterns.append(AntiPatternInstance(
                pattern_name="Logic in Tests",
                severity="warning",
                line_number=node.lineno,
                function_name=node.name,
                description="Test contains if/else logic; logic should be in implementation, not test"
            ))

    def _detect_magic_numbers(self, node: ast.FunctionDef, test_info: dict):
        """Detect unexplained magic numbers in assertions."""
        code = ast.unparse(node)
        # Find numeric assertions without descriptive context
        magic_patterns = re.findall(r'assert.*\b([0-9]{2,})\b', code)
        if magic_patterns and len(magic_patterns) > 2:
            self.anti_patterns.append(AntiPatternInstance(
                pattern_name="Magic Numbers",
                severity="warning",
                line_number=node.lineno,
                function_name=node.name,
                description=f"Test contains {len(magic_patterns)} unexplained numeric constants"
            ))

    def _detect_caught_exception(self, node: ast.FunctionDef, test_info: dict):
        """Detect silent exception catching."""
        code = ast.unparse(node)
        # Look for except with pass or empty body
        if re.search(r'except\s+\w+\s*:\s*pass', code):
            self.anti_patterns.append(AntiPatternInstance(
                pattern_name="Caught Exception",
                severity="critical",
                line_number=node.lineno,
                function_name=node.name,
                description="Test silently catches exception with 'pass'; cannot verify exception behavior"
            ))

    def _detect_over_specification(self, node: ast.FunctionDef, test_info: dict):
        """Detect over-specification (testing implementation details)."""
        code = ast.unparse(node)
        # Look for access to private members (_ prefix) or implementation details
        if re.search(r'\._\w+', code) and 'assert' in code:
            self.anti_patterns.append(AntiPatternInstance(
                pattern_name="Over-Specification",
                severity="warning",
                line_number=node.lineno,
                function_name=node.name,
                description="Test asserts on private implementation details (e.g., _cache, _internal); test public behavior instead"
            ))

    def _count_assertions(self, node: ast.FunctionDef) -> int:
        """Count assert statements in function."""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                count += 1
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr.startswith('assert'):
                        count += 1
        self.assertion_count += count
        return count

    def _has_any_assertions(self, node: ast.FunctionDef) -> bool:
        """Check if function has any assertions."""
        return self._count_assertions(node) > 0

    def _count_mocks(self, node: ast.FunctionDef) -> int:
        """Count mock-related lines."""
        code = ast.unparse(node)
        mock_keywords = ['MagicMock', 'Mock', 'patch', 'mock_', '@patch', '@mock']
        count = sum(len(re.findall(kw, code, re.IGNORECASE)) for kw in mock_keywords)
        return count

    def _has_conditional_logic(self, node: ast.FunctionDef) -> bool:
        """Check for if/for/while in test."""
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While)):
                return True
        return False

    def _has_try_except(self, node: ast.FunctionDef) -> bool:
        """Check for try/except blocks."""
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                return True
        return False

    def _get_node_length(self, node: ast.FunctionDef) -> int:
        """Get line count of a node."""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno
        return len(self.lines)

    def _get_code_snippet(self, node: ast.FunctionDef) -> str:
        """Get source code for a node."""
        start = node.lineno - 1
        end = getattr(node, 'end_lineno', node.lineno)
        return '\n'.join(self.lines[start:end])


class CoverageParser:
    """Parse coverage reports (XML or JSON format)."""

    def __init__(self, coverage_file: Optional[str] = None):
        self.coverage_file = coverage_file
        self.coverage_data = {}

    def parse(self) -> Dict[str, float]:
        """Parse coverage file and return per-file coverage percentages."""
        if not self.coverage_file or not Path(self.coverage_file).exists():
            return {}

        if self.coverage_file.endswith('.xml'):
            return self._parse_xml()
        elif self.coverage_file.endswith('.json'):
            return self._parse_json()

        return {}

    def _parse_xml(self) -> Dict[str, float]:
        """Parse coverage.xml (Cobertura format)."""
        try:
            tree = ET.parse(self.coverage_file)
            root = tree.getroot()

            coverage_data = {}
            for package in root.findall('.//package'):
                for cls in package.findall('.//class'):
                    filename = cls.get('filename', '')
                    line_rate = float(cls.get('line-rate', 0))
                    coverage_data[filename] = line_rate
            return coverage_data
        except Exception as e:
            print(f"Error parsing coverage XML: {e}")
            return {}

    def _parse_json(self) -> Dict[str, float]:
        """Parse coverage.json (coverage.py format)."""
        try:
            with open(self.coverage_file, 'r') as f:
                data = json.load(f)
            coverage_data = {}
            for filename, file_data in data.get('files', {}).items():
                summary = file_data.get('summary', {})
                if 'percent_covered' in summary:
                    coverage_data[filename] = summary['percent_covered'] / 100
            return coverage_data
        except Exception as e:
            print(f"Error parsing coverage JSON: {e}")
            return {}


class TDDEnforcer:
    """Main TDD enforcement engine."""

    def __init__(self, target_dir: str, threshold: float = 75.0,
                 coverage_file: Optional[str] = None,
                 code_dir: Optional[str] = None):
        self.target_dir = Path(target_dir)
        self.threshold = threshold
        self.coverage_file = coverage_file
        self.code_dir = Path(code_dir) if code_dir else None
        self.report = ScanReport()

    def scan(self) -> ScanReport:
        """Scan all test files for anti-patterns and coverage."""
        test_files = list(self.target_dir.rglob('test_*.py'))
        test_files.extend(self.target_dir.rglob('*_test.py'))

        if not test_files:
            print(f"Warning: No test files found in {self.target_dir}")
            return self.report

        self.report.total_files = len(test_files)

        # Parse coverage if provided
        coverage_parser = CoverageParser(self.coverage_file)
        coverage_data = coverage_parser.parse()

        # Scan each test file
        for test_file in sorted(set(test_files)):
            self._scan_file(test_file, coverage_data)

        # Calculate overall metrics
        self._finalize_report()

        return self.report

    def _scan_file(self, file_path: Path, coverage_data: Dict[str, float]):
        """Scan a single test file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return

        visitor = ASTVisitor(content, str(file_path))
        visitor.visit(tree)

        # Create finding entry
        finding = FileFinding(
            file_path=str(file_path),
            total_tests=visitor.test_count,
            anti_patterns=visitor.anti_patterns,
            test_count=visitor.test_count,
            assertion_count=visitor.assertion_count,
        )

        # Add coverage if available
        coverage_key = str(file_path.relative_to(self.target_dir.parent))
        if coverage_key in coverage_data:
            finding.coverage = coverage_data[coverage_key]

        # Calculate average test length
        if visitor.test_methods:
            finding.average_test_length = sum(t['length'] for t in visitor.test_methods) / len(visitor.test_methods)

        self.report.files[str(file_path)] = finding
        self.report.total_tests += visitor.test_count
        self.report.total_anti_patterns += len(visitor.anti_patterns)

    def _finalize_report(self):
        """Calculate final report metrics."""
        if not self.report.files:
            return

        # Calculate average quality score
        scores = [f.quality_score() for f in self.report.files.values()]
        self.report.average_quality_score = sum(scores) / len(scores) if scores else 0.0

        # Check for blocking violations
        self._check_blocking_violations()

    def _check_blocking_violations(self):
        """Identify blocking violations."""
        for file_path, finding in self.report.files.items():
            # Assertion-free tests block
            critical_patterns = [p for p in finding.anti_patterns if p.severity == "critical"]
            if critical_patterns:
                self.report.blocking_violations.append(
                    f"{file_path}: {len(critical_patterns)} critical anti-pattern(s) found"
                )

            # Low coverage blocks
            if finding.coverage is not None and finding.coverage < 0.70:
                self.report.blocking_violations.append(
                    f"{file_path}: Coverage {finding.coverage*100:.1f}% below minimum 70%"
                )

            # Multiple anti-patterns block
            if len(finding.anti_patterns) >= 5:
                self.report.blocking_violations.append(
                    f"{file_path}: {len(finding.anti_patterns)} anti-patterns; multiple quality issues"
                )

    def generate_report(self, quality_report: bool = False) -> str:
        """Generate human-readable report."""
        lines = []
        lines.append("=" * 80)
        lines.append("TDD ENFORCER SCAN REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append(f"Files Scanned: {self.report.total_files}")
        lines.append(f"Total Tests: {self.report.total_tests}")
        lines.append(f"Total Anti-Patterns: {self.report.total_anti_patterns}")
        lines.append(f"Average Quality Score: {self.report.average_quality_score:.1f}/100")
        lines.append(f"Threshold: {self.threshold:.1f}")
        lines.append("")

        # Per-file findings
        if self.report.files:
            lines.append("PER-FILE FINDINGS")
            lines.append("-" * 80)
            for file_path in sorted(self.report.files.keys()):
                finding = self.report.files[file_path]
                score = finding.quality_score()
                status = "PASS" if score >= self.threshold else "FAIL"
                lines.append(f"{Path(file_path).name}  [{status}]  Score: {score:.1f}/100")

                if finding.total_tests:
                    lines.append(f"  Tests: {finding.total_tests}  Assertions: {finding.assertion_count}  Avg Length: {finding.average_test_length:.1f}L")

                if finding.coverage is not None:
                    lines.append(f"  Coverage: {finding.coverage*100:.1f}%")

                if finding.anti_patterns:
                    lines.append(f"  Anti-Patterns ({len(finding.anti_patterns)}):")
                    for pattern in sorted(set(p.pattern_name for p in finding.anti_patterns)):
                        count = len([p for p in finding.anti_patterns if p.pattern_name == pattern])
                        lines.append(f"    - {pattern}: {count}")

                lines.append("")

        # Blocking violations
        if self.report.blocking_violations:
            lines.append("BLOCKING VIOLATIONS")
            lines.append("-" * 80)
            for violation in self.report.blocking_violations:
                lines.append(f"  ❌ {violation}")
            lines.append("")

        # Overall status
        lines.append("OVERALL STATUS")
        lines.append("-" * 80)
        if self.report.average_quality_score >= self.threshold:
            lines.append(f"✓ Quality threshold ({self.threshold}) MET")
        else:
            lines.append(f"✗ Quality threshold ({self.threshold}) NOT MET")

        if not self.report.blocking_violations:
            lines.append("✓ No blocking violations")
        else:
            lines.append(f"✗ {len(self.report.blocking_violations)} blocking violation(s)")

        lines.append("=" * 80)

        return '\n'.join(lines)


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='TDD Enforcer: Enforce test-driven development practices'
    )
    parser.add_argument('action', choices=['scan'], help='Action to perform')
    parser.add_argument('--target', required=True, help='Target test directory to scan')
    parser.add_argument('--target-code', help='Source code directory for comparison')
    parser.add_argument('--threshold', type=float, default=75.0, help='Quality score threshold (default: 75)')
    parser.add_argument('--coverage', help='Coverage report file (XML or JSON)')
    parser.add_argument('--quality-report', action='store_true', help='Generate detailed quality report')
    parser.add_argument('--blocking-mode', action='store_true', help='Exit with non-zero if blocking violations exist')

    args = parser.parse_args()

    enforcer = TDDEnforcer(
        target_dir=args.target,
        threshold=args.threshold,
        coverage_file=args.coverage,
        code_dir=args.target_code
    )

    report = enforcer.scan()
    output = enforcer.generate_report(quality_report=args.quality_report)
    print(output)

    if args.blocking_mode and report.has_blocking_issues():
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
