#!/usr/bin/env python3
"""
Automated test runner for skill scripts with fixtures, assertions, and regression detection.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class AssertionError(Exception):
    """Raised when an assertion fails."""
    pass


class TestRunner:
    """Executes test cases against skill scripts."""
    
    def __init__(
        self,
        test_file: Path,
        scripts_dir: Path,
        fixtures_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        verbose: bool = False,
    ):
        self.test_file = test_file
        self.scripts_dir = scripts_dir.resolve()
        self.test_file_dir = test_file.parent.resolve()
        self.fixtures_dir = (
            fixtures_dir.resolve() if fixtures_dir
            else self.test_file_dir / "fixtures"
        )
        self.output_dir = output_dir.resolve() if output_dir else None
        self.verbose = verbose
        self.results = []
        
    def load_tests(self) -> Dict[str, Any]:
        """Load test definition from JSON file."""
        try:
            with open(self.test_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Test file not found: {self.test_file}", file=sys.stderr)
            sys.exit(2)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in test file: {e}", file=sys.stderr)
            sys.exit(2)
    
    def expand_variables(self, text: str, fixtures_dir: Path, output_dir: Path) -> str:
        """Expand template variables in text."""
        return (
            text.replace("{scripts}", str(self.scripts_dir))
            .replace("{fixtures}", str(fixtures_dir))
            .replace("{output}", str(output_dir))
        )
    
    def run_command(
        self,
        command: str,
        fixtures_dir: Path,
        output_dir: Path,
        timeout: int = 30,
        env: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, str, str]:
        """Execute a command and return exit code, stdout, and stderr."""
        expanded_command = self.expand_variables(command, fixtures_dir, output_dir)
        
        if self.verbose:
            print(f"  Command: {expanded_command}")
        
        try:
            process = subprocess.Popen(
                expanded_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(output_dir),
                env={**os.environ, **(env or {})},
            )
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", f"Command execution failed: {e}"
    
    def get_json_field(self, data: Any, field_path: str) -> Any:
        """Extract a field from JSON data using dotted notation."""
        keys = re.split(r'[\.\[\]]', field_path)
        keys = [k for k in keys if k]
        
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        
        return current
    
    def compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare two values using the given operator."""
        if operator == "eq":
            return actual == expected
        elif operator == "neq":
            return actual != expected
        elif operator == "gt":
            return actual > expected
        elif operator == "gte":
            return actual >= expected
        elif operator == "lt":
            return actual < expected
        elif operator == "lte":
            return actual <= expected
        elif operator == "contains":
            return expected in actual if isinstance(actual, (str, list)) else False
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    def evaluate_assertion(
        self,
        assertion: Dict[str, Any],
        exit_code: int,
        stdout: str,
        stderr: str,
        output_dir: Path,
        fixtures_dir: Path,
    ) -> Tuple[bool, str]:
        """Evaluate a single assertion. Returns (passed, message)."""
        assertion_type = assertion.get("type")
        
        if assertion_type == "exit_code":
            expected = assertion.get("expected")
            passed = exit_code == expected
            message = f"Exit code: {exit_code} {'==' if passed else '!='} {expected}"
            return passed, message
        
        elif assertion_type == "file_exists":
            path = self.expand_variables(assertion.get("path", ""), fixtures_dir, output_dir)
            passed = Path(path).exists()
            message = f"File exists: {path}" if passed else f"File not found: {path}"
            return passed, message
        
        elif assertion_type == "file_not_exists":
            path = self.expand_variables(assertion.get("path", ""), fixtures_dir, output_dir)
            passed = not Path(path).exists()
            message = f"File does not exist: {path}" if passed else f"File should not exist: {path}"
            return passed, message
        
        elif assertion_type == "output_contains":
            text = assertion.get("text", "")
            combined_output = stdout + stderr
            passed = text in combined_output
            message = f"Output contains '{text}'" if passed else f"Output does not contain '{text}'"
            return passed, message
        
        elif assertion_type == "output_not_contains":
            text = assertion.get("text", "")
            combined_output = stdout + stderr
            passed = text not in combined_output
            message = f"Output does not contain '{text}'" if passed else f"Output should not contain '{text}'"
            return passed, message
        
        elif assertion_type == "json_field":
            path = self.expand_variables(assertion.get("path", ""), fixtures_dir, output_dir)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                actual = self.get_json_field(data, assertion.get("field", ""))
                expected = assertion.get("value")
                operator = assertion.get("operator", "eq")
                passed = self.compare_values(actual, operator, expected)
                message = (
                    f"JSON field '{assertion.get('field')}': {actual} {operator} {expected}"
                    if passed else
                    f"JSON field '{assertion.get('field')}': {actual} {operator} {expected} (FAILED)"
                )
                return passed, message
            except (FileNotFoundError, json.JSONDecodeError) as e:
                return False, f"Failed to read JSON file {path}: {e}"
        
        elif assertion_type == "line_count":
            path = self.expand_variables(assertion.get("path", ""), fixtures_dir, output_dir)
            try:
                with open(path, "r") as f:
                    line_count = sum(1 for _ in f)
                expected = assertion.get("value")
                operator = assertion.get("operator", "eq")
                passed = self.compare_values(line_count, operator, expected)
                message = (
                    f"Line count: {line_count} {operator} {expected}"
                    if passed else
                    f"Line count: {line_count} {operator} {expected} (FAILED)"
                )
                return passed, message
            except FileNotFoundError as e:
                return False, f"File not found: {path}"
        
        elif assertion_type == "regex_match":
            pattern = assertion.get("pattern", "")
            combined_output = stdout + stderr
            try:
                passed = bool(re.search(pattern, combined_output))
                message = (
                    f"Output matches pattern '{pattern}'" if passed
                    else f"Output does not match pattern '{pattern}'"
                )
                return passed, message
            except re.error as e:
                return False, f"Invalid regex pattern: {e}"
        
        else:
            return False, f"Unknown assertion type: {assertion_type}"
    
    def run_test(
        self,
        test: Dict[str, Any],
        test_output_dir: Optional[Path] = None,
    ) -> Tuple[bool, List[str]]:
        """Run a single test case. Returns (passed, messages)."""
        messages = []
        test_name = test.get("name", "unknown")
        
        if self.verbose:
            print(f"Running: {test_name}")
        
        fixtures_dir = self.test_file_dir / test.get("fixtures_dir", "fixtures")
        if not fixtures_dir.exists():
            fixtures_dir = self.fixtures_dir
        
        temp_dir = None
        try:
            if test_output_dir:
                output_dir = test_output_dir
            else:
                temp_dir = tempfile.TemporaryDirectory()
                output_dir = Path(temp_dir.name)
            
            command = test.get("command", "")
            timeout = test.get("timeout", 30)
            env = test.get("env", {})
            
            exit_code, stdout, stderr = self.run_command(
                command,
                fixtures_dir,
                output_dir,
                timeout=timeout,
                env=env,
            )
            
            if self.verbose:
                if stdout:
                    print(f"  stdout: {stdout[:200]}")
                if stderr:
                    print(f"  stderr: {stderr[:200]}")
            
            assertions = test.get("assertions", [])
            all_passed = True
            
            for assertion in assertions:
                passed, message = self.evaluate_assertion(
                    assertion,
                    exit_code,
                    stdout,
                    stderr,
                    output_dir,
                    fixtures_dir,
                )
                messages.append(message)
                if not passed:
                    all_passed = False
                    if self.verbose:
                        print(f"  FAILED: {message}")
            
            return all_passed, messages
        
        except Exception as e:
            messages.append(f"Test execution error: {e}")
            return False, messages
        
        finally:
            if temp_dir:
                temp_dir.cleanup()
    
    def run_all_tests(self) -> Tuple[int, int]:
        """Run all tests and return (passed_count, total_count)."""
        test_defs = self.load_tests()
        tests = test_defs.get("tests", [])
        
        if not tests:
            print("Warning: No tests found in test file")
            return 0, 0
        
        passed_count = 0
        
        for test in tests:
            test_name = test.get("name", "unknown")
            passed, messages = self.run_test(test)
            
            self.results.append({
                "name": test_name,
                "passed": passed,
                "messages": messages,
            })
            
            if passed:
                passed_count += 1
                if self.verbose:
                    print(f"PASSED: {test_name}")
            else:
                if self.verbose:
                    print(f"FAILED: {test_name}")
                    for msg in messages:
                        print(f"  {msg}")
        
        return passed_count, len(tests)
    
    def print_summary(self, passed_count: int, total_count: int) -> None:
        """Print test summary."""
        print(f"\nTest Results: {passed_count}/{total_count} passed")
        
        if passed_count < total_count:
            print("\nFailed tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  {result['name']}")
                    for msg in result["messages"]:
                        print(f"    {msg}")
    
    def write_json_report(self, output_path: Path, passed_count: int, total_count: int) -> None:
        """Write results as JSON report."""
        report = {
            "summary": {
                "passed": passed_count,
                "total": total_count,
                "success": passed_count == total_count,
            },
            "tests": self.results,
        }
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        if self.verbose:
            print(f"JSON report written to: {output_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated test runner for skill scripts",
    )
    parser.add_argument(
        "--test-file",
        type=Path,
        required=True,
        help="Path to test definition JSON file",
    )
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        required=True,
        help="Path to scripts directory",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        help="Path to fixtures directory (default: fixtures/ relative to test file)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Path for test output (default: temporary directory)",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        help="Write JSON report to file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed test output",
    )
    
    args = parser.parse_args()
    
    runner = TestRunner(
        test_file=args.test_file,
        scripts_dir=args.scripts_dir,
        fixtures_dir=args.fixtures_dir,
        output_dir=args.output_dir,
        verbose=args.verbose,
    )
    
    passed_count, total_count = runner.run_all_tests()
    runner.print_summary(passed_count, total_count)
    
    if args.json_report:
        runner.write_json_report(args.json_report, passed_count, total_count)
    
    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
