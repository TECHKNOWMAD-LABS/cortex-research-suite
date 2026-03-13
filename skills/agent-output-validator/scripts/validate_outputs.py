#!/usr/bin/env python3
"""
Agent Output Validator

Validates outputs from parallel agent dispatches against expected contracts.
Checks file paths, content requirements, and schema compliance.
"""

import argparse
import json
import os
import sys
import py_compile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ValidationError:
    """Represents a single validation failure."""

    def __init__(self, check_type: str, message: str, severity: str = "error"):
        self.check_type = check_type
        self.message = message
        self.severity = severity

    def to_dict(self) -> Dict[str, str]:
        return {
            "check": self.check_type,
            "message": self.message,
            "severity": self.severity,
        }


class FileValidator:
    """Validates a single file against a specification."""

    def __init__(self, path: str, spec: Dict[str, Any]):
        self.path = path
        self.spec = spec
        self.errors: List[ValidationError] = []
        self.passed = True

    def validate(self) -> bool:
        """Run all specified checks on the file."""
        # Check if file exists
        if not os.path.exists(self.path):
            self.errors.append(
                ValidationError("path", f"File not found at {self.path}")
            )
            self.passed = False
            return False

        # Check file is a regular file
        if not os.path.isfile(self.path):
            self.errors.append(
                ValidationError("path", f"{self.path} is not a regular file")
            )
            self.passed = False
            return False

        # Get file size
        try:
            file_size = os.path.getsize(self.path)
        except OSError as e:
            self.errors.append(
                ValidationError("size", f"Cannot read file size: {e}")
            )
            self.passed = False
            return False

        # Check size constraints
        min_size = self.spec.get("min_size")
        if min_size is not None and file_size < min_size:
            self.errors.append(
                ValidationError(
                    "min_size",
                    f"File size {file_size} bytes (expected at least {min_size} bytes)",
                )
            )
            self.passed = False

        max_size = self.spec.get("max_size")
        if max_size is not None and file_size > max_size:
            self.errors.append(
                ValidationError(
                    "max_size",
                    f"File size {file_size} bytes (expected at most {max_size} bytes)",
                )
            )
            self.passed = False

        # Read file content for text checks
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            self.errors.append(
                ValidationError("read", f"Cannot read file: {e}")
            )
            self.passed = False
            return False

        # Check line count constraints
        line_count = len(lines)
        line_count_min = self.spec.get("line_count_min")
        if line_count_min is not None and line_count < line_count_min:
            self.errors.append(
                ValidationError(
                    "line_count_min",
                    f"File has {line_count} lines (expected at least {line_count_min} lines)",
                )
            )
            self.passed = False

        line_count_max = self.spec.get("line_count_max")
        if line_count_max is not None and line_count > line_count_max:
            self.errors.append(
                ValidationError(
                    "line_count_max",
                    f"File has {line_count} lines (expected at most {line_count_max} lines)",
                )
            )
            self.passed = False

        # Check required content
        contains = self.spec.get("contains", [])
        for required_str in contains:
            if required_str not in content:
                self.errors.append(
                    ValidationError(
                        "contains",
                        f"Required string not found: {repr(required_str)}",
                    )
                )
                self.passed = False

        # Check forbidden content
        not_contains = self.spec.get("not_contains", [])
        for forbidden_str in not_contains:
            if forbidden_str in content:
                self.errors.append(
                    ValidationError(
                        "not_contains",
                        f"Forbidden string found: {repr(forbidden_str)}",
                    )
                )
                self.passed = False

        # Check syntax
        syntax_check = self.spec.get("syntax_check")
        if syntax_check == "python":
            self._check_python_syntax()
        elif syntax_check == "json":
            self._check_json_syntax()
        elif syntax_check == "yaml":
            self._check_yaml_syntax()
        elif syntax_check is not None:
            self.errors.append(
                ValidationError(
                    "syntax_check",
                    f"Unknown syntax check type: {syntax_check}",
                )
            )
            self.passed = False

        return self.passed

    def _check_python_syntax(self) -> None:
        """Validate Python syntax using py_compile."""
        try:
            py_compile.compile(self.path, doraise=True)
        except py_compile.PyCompileError as e:
            self.errors.append(
                ValidationError("syntax_check", f"Python syntax error: {e}")
            )
            self.passed = False

    def _check_json_syntax(self) -> None:
        """Validate JSON syntax."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(
                ValidationError(
                    "syntax_check",
                    f"JSON syntax error at line {e.lineno}, col {e.colno}: {e.msg}",
                )
            )
            self.passed = False
        except Exception as e:
            self.errors.append(
                ValidationError("syntax_check", f"JSON validation error: {e}")
            )
            self.passed = False

    def _check_yaml_syntax(self) -> None:
        """Validate YAML syntax."""
        try:
            import yaml
            with open(self.path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
        except ImportError:
            self.errors.append(
                ValidationError(
                    "syntax_check",
                    "YAML validation requires PyYAML (not in stdlib, skipped)",
                    severity="warning",
                )
            )
        except Exception as e:
            self.errors.append(
                ValidationError("syntax_check", f"YAML syntax error: {e}")
            )
            self.passed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "passed": self.passed,
            "errors": [e.to_dict() for e in self.errors],
        }


class AgentValidator:
    """Validates outputs for a single agent."""

    def __init__(self, agent_spec: Dict[str, Any]):
        self.name = agent_spec["name"]
        self.expected_files = agent_spec.get("expected_files", [])
        self.file_validators: List[FileValidator] = []
        self.passed = True

    def validate(self) -> bool:
        """Validate all expected files."""
        for file_spec in self.expected_files:
            path = file_spec.get("path")
            if not path:
                raise ValueError("File spec missing required 'path' field")

            validator = FileValidator(path, file_spec)
            validator.validate()
            self.file_validators.append(validator)

            if not validator.passed:
                self.passed = False

        return self.passed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "files": [v.to_dict() for v in self.file_validators],
        }


class ContractValidator:
    """Validates all agents against a contract."""

    def __init__(self, contract: Dict[str, Any], strict: bool = False):
        self.contract = contract
        self.strict = strict
        self.agent_validators: List[AgentValidator] = []
        self.passed = True

    def validate(self) -> bool:
        """Validate all agents."""
        agents = self.contract.get("agents", [])
        if not agents:
            raise ValueError("Contract must contain 'agents' field")

        for agent_spec in agents:
            validator = AgentValidator(agent_spec)
            validator.validate()
            self.agent_validators.append(validator)

            if not validator.passed:
                self.passed = False

        if self.strict:
            # Check for warnings in strict mode
            for agent_validator in self.agent_validators:
                for file_validator in agent_validator.file_validators:
                    for error in file_validator.errors:
                        if error.severity == "warning":
                            self.passed = False

        return self.passed

    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary statistics."""
        agents_passed = sum(1 for a in self.agent_validators if a.passed)
        agents_total = len(self.agent_validators)

        files_passed = 0
        files_total = 0
        for agent in self.agent_validators:
            for file_validator in agent.file_validators:
                files_total += 1
                if file_validator.passed:
                    files_passed += 1

        return {
            "agents_passed": agents_passed,
            "agents_total": agents_total,
            "files_passed": files_passed,
            "files_total": files_total,
            "exit_code": 0 if self.passed else 1,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.get_summary(),
            "agents": [a.to_dict() for a in self.agent_validators],
        }

    def to_text(self) -> str:
        """Format validation results as human-readable text."""
        lines = []
        lines.append("VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")

        for agent in self.agent_validators:
            status = "PASS" if agent.passed else "FAIL"
            files_passed = sum(1 for f in agent.file_validators if f.passed)
            files_total = len(agent.file_validators)

            lines.append(f"Agent: {agent.name}")
            lines.append(f"  Status: {status}")
            lines.append(f"  Files: {files_passed}/{files_total} passed")

            # Show details for failed files
            for file_validator in agent.file_validators:
                if not file_validator.passed:
                    lines.append(f"")
                    lines.append(f"  {Path(file_validator.path).name}")
                    for error in file_validator.errors:
                        severity_label = error.severity.upper()
                        lines.append(f"    {severity_label}: {error.message}")

            lines.append("")

        # Summary section
        summary = self.get_summary()
        lines.append("SUMMARY")
        lines.append("=" * 80)
        lines.append(
            f"Agents passed: {summary['agents_passed']}/{summary['agents_total']}"
        )
        lines.append(
            f"Files passed: {summary['files_passed']}/{summary['files_total']}"
        )
        lines.append(f"Exit code: {summary['exit_code']}")

        return "\n".join(lines)


def load_contract(contract_path: str) -> Dict[str, Any]:
    """Load and validate contract JSON."""
    try:
        with open(contract_path, "r") as f:
            contract = json.load(f)
    except FileNotFoundError:
        print(f"Error: Contract file not found: {contract_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(
            f"Error: Invalid JSON in contract file: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    return contract


def main():
    parser = argparse.ArgumentParser(
        description="Validate agent outputs against contracts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 validate_outputs.py --contract contract.json
  python3 validate_outputs.py --contract contract.json --format json
  python3 validate_outputs.py --contract contract.json --strict
        """,
    )

    parser.add_argument(
        "--contract",
        required=True,
        help="Path to JSON contract file",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    # Load contract
    contract = load_contract(args.contract)

    # Validate
    validator = ContractValidator(contract, strict=args.strict)
    validator.validate()

    # Output results
    if args.format == "json":
        print(json.dumps(validator.to_dict(), indent=2))
    else:
        print(validator.to_text())

    # Exit with appropriate code
    sys.exit(validator.get_summary()["exit_code"])


if __name__ == "__main__":
    main()
