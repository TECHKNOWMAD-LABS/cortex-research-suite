#!/usr/bin/env python3
"""Mutation testing integration for the TDD Enforcer skill.

Runs mutmut if available, otherwise provides manual mutation examples
to help assess test suite quality.

Usage:
    python mutation_testing.py --target <module> --test-dir <dir> --report-format json|text
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class MutationResult:
    """Result of a single mutation test."""
    mutant_id: str
    status: str  # killed, survived, timeout, error
    source_file: str
    line_number: int
    mutation_type: str
    description: str


@dataclass
class MutationReport:
    """Aggregate mutation testing report."""
    target: str
    test_dir: str
    total_mutants: int = 0
    killed: int = 0
    survived: int = 0
    timeout: int = 0
    errors: int = 0
    score: float = 0.0
    duration_seconds: float = 0.0
    results: list = field(default_factory=list)
    engine: str = "manual"

    def calculate_score(self):
        if self.total_mutants > 0:
            self.score = round((self.killed / self.total_mutants) * 100, 2)


MANUAL_MUTATIONS = [
    {
        "type": "arithmetic_operator",
        "original": "+",
        "mutated": "-",
        "description": "Replace addition with subtraction",
    },
    {
        "type": "comparison_operator",
        "original": "==",
        "mutated": "!=",
        "description": "Replace equality check with inequality",
    },
    {
        "type": "boolean_literal",
        "original": "True",
        "mutated": "False",
        "description": "Replace True with False",
    },
    {
        "type": "boundary_value",
        "original": ">",
        "mutated": ">=",
        "description": "Replace strict greater-than with greater-or-equal",
    },
    {
        "type": "return_value",
        "original": "return x",
        "mutated": "return None",
        "description": "Replace return value with None",
    },
    {
        "type": "remove_call",
        "original": "validate(input)",
        "mutated": "# validate(input)",
        "description": "Remove function call (comment out)",
    },
    {
        "type": "negate_condition",
        "original": "if condition:",
        "mutated": "if not condition:",
        "description": "Negate conditional expression",
    },
    {
        "type": "constant_replacement",
        "original": "0",
        "mutated": "1",
        "description": "Replace zero constant with one",
    },
]


class MutationRunner:
    """Runs mutation testing against a target module."""

    def __init__(self, target: str, test_dir: str):
        self.target = target
        self.test_dir = test_dir
        self.report = MutationReport(target=target, test_dir=test_dir)
        self._mutmut_available = shutil.which("mutmut") is not None

    def run(self) -> MutationReport:
        """Execute mutation testing.

        Uses mutmut if installed, otherwise falls back to manual mutation
        analysis with example mutations.
        """
        start_time = time.time()

        if self._mutmut_available:
            self._run_mutmut()
        else:
            self._run_manual()

        self.report.duration_seconds = round(time.time() - start_time, 2)
        self.report.calculate_score()
        return self.report

    def _run_mutmut(self):
        """Run mutation testing using mutmut."""
        self.report.engine = "mutmut"

        target_path = Path(self.target)
        if not target_path.exists():
            print(f"Error: Target module '{self.target}' not found.", file=sys.stderr)
            sys.exit(1)

        cmd = [
            "mutmut",
            "run",
            "--paths-to-mutate", str(target_path),
            "--tests-dir", self.test_dir,
            "--no-progress",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            print("Warning: mutmut timed out after 600 seconds.", file=sys.stderr)
            return
        except FileNotFoundError:
            print("Error: mutmut not found in PATH.", file=sys.stderr)
            return

        self._parse_mutmut_results()

    def _parse_mutmut_results(self):
        """Parse mutmut results from its JSON cache."""
        try:
            result = subprocess.run(
                ["mutmut", "results"],
                capture_output=True,
                text=True,
            )
            output = result.stdout

            for line in output.strip().split("\n"):
                line = line.strip()
                if line.startswith("Killed:"):
                    self.report.killed = int(line.split(":")[1].strip())
                elif line.startswith("Survived:"):
                    self.report.survived = int(line.split(":")[1].strip())
                elif line.startswith("Timeout:"):
                    self.report.timeout = int(line.split(":")[1].strip())

            self.report.total_mutants = (
                self.report.killed + self.report.survived + self.report.timeout
            )
        except Exception as e:
            print(f"Warning: Could not parse mutmut results: {e}", file=sys.stderr)

    def _run_manual(self):
        """Run manual mutation analysis when mutmut is not available."""
        self.report.engine = "manual"

        target_path = Path(self.target)
        if not target_path.exists():
            print(f"Warning: Target '{self.target}' not found. Using example mutations.", file=sys.stderr)
            self._generate_example_results()
            return

        if target_path.is_file():
            self._analyze_file(target_path)
        elif target_path.is_dir():
            for py_file in sorted(target_path.rglob("*.py")):
                if "__pycache__" not in str(py_file):
                    self._analyze_file(py_file)
        else:
            self._generate_example_results()

    def _analyze_file(self, file_path: Path):
        """Analyze a single file for potential mutations."""
        try:
            source = file_path.read_text()
        except (IOError, UnicodeDecodeError):
            return

        lines = source.split("\n")
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for mutation in MANUAL_MUTATIONS:
                if mutation["original"] in stripped:
                    mutant_id = f"{file_path.name}:{i}:{mutation['type']}"
                    result = MutationResult(
                        mutant_id=mutant_id,
                        status="survived",
                        source_file=str(file_path),
                        line_number=i,
                        mutation_type=mutation["type"],
                        description=mutation["description"],
                    )
                    self.report.results.append(result)
                    self.report.total_mutants += 1
                    self.report.survived += 1

    def _generate_example_results(self):
        """Generate example mutation results for demonstration."""
        examples = [
            MutationResult("example:1:arithmetic", "survived", "example.py", 10, "arithmetic_operator", "Replace + with -"),
            MutationResult("example:2:comparison", "killed", "example.py", 25, "comparison_operator", "Replace == with !="),
            MutationResult("example:3:boolean", "killed", "example.py", 30, "boolean_literal", "Replace True with False"),
            MutationResult("example:4:boundary", "survived", "example.py", 42, "boundary_value", "Replace > with >="),
            MutationResult("example:5:return", "killed", "example.py", 55, "return_value", "Replace return value with None"),
        ]
        self.report.results = examples
        self.report.total_mutants = len(examples)
        self.report.killed = sum(1 for r in examples if r.status == "killed")
        self.report.survived = sum(1 for r in examples if r.status == "survived")

    def report_text(self) -> str:
        """Format the report as human-readable text."""
        lines = [
            "=" * 60,
            "MUTATION TESTING REPORT",
            "=" * 60,
            f"Engine:          {self.report.engine}",
            f"Target:          {self.report.target}",
            f"Test directory:  {self.report.test_dir}",
            f"Duration:        {self.report.duration_seconds}s",
            "",
            f"Total mutants:   {self.report.total_mutants}",
            f"Killed:          {self.report.killed}",
            f"Survived:        {self.report.survived}",
            f"Timeout:         {self.report.timeout}",
            f"Errors:          {self.report.errors}",
            f"Mutation score:  {self.report.score}%",
            "",
        ]

        if self.report.survived > 0:
            lines.append("SURVIVING MUTANTS (test gaps detected):")
            lines.append("-" * 40)
            for r in self.report.results:
                if r.status == "survived":
                    lines.append(f"  [{r.mutant_id}] {r.source_file}:{r.line_number}")
                    lines.append(f"    Type: {r.mutation_type}")
                    lines.append(f"    {r.description}")
                    lines.append("")

        if self.report.engine == "manual":
            lines.append("NOTE: Using manual mutation analysis.")
            lines.append("Install mutmut for full mutation testing: pip install mutmut")

        lines.append("=" * 60)
        return "\n".join(lines)

    def report_json(self) -> str:
        """Format the report as JSON."""
        data = {
            "engine": self.report.engine,
            "target": self.report.target,
            "test_dir": self.report.test_dir,
            "duration_seconds": self.report.duration_seconds,
            "summary": {
                "total_mutants": self.report.total_mutants,
                "killed": self.report.killed,
                "survived": self.report.survived,
                "timeout": self.report.timeout,
                "errors": self.report.errors,
                "mutation_score": self.report.score,
            },
            "results": [
                {
                    "mutant_id": r.mutant_id,
                    "status": r.status,
                    "source_file": r.source_file,
                    "line_number": r.line_number,
                    "mutation_type": r.mutation_type,
                    "description": r.description,
                }
                for r in self.report.results
            ],
        }
        return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Mutation testing integration for TDD Enforcer"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target module or directory to mutate",
    )
    parser.add_argument(
        "--test-dir",
        required=True,
        help="Directory containing test files",
    )
    parser.add_argument(
        "--report-format",
        choices=["json", "text"],
        default="text",
        help="Output format for the mutation report (default: text)",
    )

    args = parser.parse_args()

    runner = MutationRunner(target=args.target, test_dir=args.test_dir)
    runner.run()

    if args.report_format == "json":
        print(runner.report_json())
    else:
        print(runner.report_text())


if __name__ == "__main__":
    main()
