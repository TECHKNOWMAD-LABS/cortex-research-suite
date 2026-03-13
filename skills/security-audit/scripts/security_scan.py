#!/usr/bin/env python3
"""
Security Audit Scanner - Production-Ready Security Analysis Tool

Orchestrates multiple security scanning engines (Bandit, Semgrep, Built-in patterns)
to identify and report security vulnerabilities in source code.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityFinding:
    """Represents a security finding from any scanner."""

    def __init__(
        self,
        severity: str,
        title: str,
        file: str,
        line: int,
        code: str,
        cwe: Optional[str] = None,
        fix: Optional[str] = None,
        tool: str = "built-in"
    ) -> None:
        """
        Initialize a security finding.

        Args:
            severity: "critical", "high", "medium", "low"
            title: Short description of the vulnerability
            file: Path to the affected file
            line: Line number where issue occurs
            code: Code snippet showing the issue
            cwe: CWE identifier if available
            fix: Suggested fix or remediation
            tool: Which scanner found this ("bandit", "semgrep", "built-in")
        """
        self.severity = severity
        self.title = title
        self.file = file
        self.line = line
        self.code = code
        self.cwe = cwe
        self.fix = fix
        self.tool = tool

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary for JSON serialization."""
        return {
            "severity": self.severity,
            "title": self.title,
            "file": self.file,
            "line": self.line,
            "code": self.code,
            "cwe": self.cwe,
            "fix": self.fix,
            "tool": self.tool
        }


class SecurityScanner:
    """Main orchestrator for security scanning."""

    # Severity levels for ordering/filtering
    SEVERITY_LEVELS = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    # Regex patterns for built-in scanning
    PATTERNS = {
        # Python patterns
        "python_eval": {
            "pattern": r"\b(eval|exec)\s*\(",
            "title": "Use of eval() or exec()",
            "severity": "critical",
            "cwe": "CWE-95",
            "fix": "Use safer alternatives like ast.literal_eval() or other restricted execution methods"
        },
        "python_pickle": {
            "pattern": r"pickle\.load[s]?\s*\(",
            "title": "Unsafe pickle deserialization",
            "severity": "critical",
            "cwe": "CWE-502",
            "fix": "Use json.load() or other safe serialization formats instead"
        },
        "python_subprocess_shell": {
            "pattern": r"subprocess\.(call|run|popen)\s*\([^)]*shell\s*=\s*True",
            "title": "subprocess call with shell=True",
            "severity": "high",
            "cwe": "CWE-78",
            "fix": "Set shell=False and pass arguments as a list instead of string"
        },
        "python_yaml_unsafe": {
            "pattern": r"yaml\.load\s*\([^)]*\)",
            "title": "Unsafe YAML deserialization",
            "severity": "high",
            "cwe": "CWE-502",
            "fix": "Use yaml.safe_load() instead of yaml.load()"
        },
        "python_hardcoded_secret": {
            "pattern": r"(PASSWORD|SECRET|TOKEN|API_KEY|api_key|apiKey)\s*=\s*['\"]([^'\"]{8,})['\"]",
            "title": "Hardcoded secret or credentials",
            "severity": "critical",
            "cwe": "CWE-798",
            "fix": "Use environment variables or secure credential storage instead"
        },
        "python_assert": {
            "pattern": r"\bassert\s+\w+",
            "title": "Assert statement used for validation",
            "severity": "medium",
            "cwe": "CWE-390",
            "fix": "Replace assert with proper error handling and validation"
        },
        "python_wildcard_import": {
            "pattern": r"from\s+\S+\s+import\s+\*",
            "title": "Wildcard import used",
            "severity": "low",
            "cwe": None,
            "fix": "Import only necessary symbols explicitly"
        },
        # JavaScript/TypeScript patterns
        "js_eval": {
            "pattern": r"\b(eval|Function|setTimeout|setInterval)\s*\(\s*['\"]",
            "title": "Use of eval() or Function()",
            "severity": "critical",
            "cwe": "CWE-95",
            "fix": "Use safer alternatives or restrict dynamic code execution"
        },
        "js_innerhtml": {
            "pattern": r"\binnerHTML\s*=\s*",
            "title": "Assignment to innerHTML",
            "severity": "high",
            "cwe": "CWE-79",
            "fix": "Use textContent or safer DOM manipulation methods"
        },
        "js_dangerous_inner": {
            "pattern": r"dangerouslySetInnerHTML",
            "title": "Use of dangerouslySetInnerHTML",
            "severity": "high",
            "cwe": "CWE-79",
            "fix": "Use textContent or safe HTML escaping libraries"
        },
        "js_exec_interpolation": {
            "pattern": r"(child_process|exec)\s*\.\s*exec\s*\([`'\"].*\$\{",
            "title": "Command execution with string interpolation",
            "severity": "high",
            "cwe": "CWE-78",
            "fix": "Use execFile or execSync with array arguments instead"
        },
        # Secret patterns
        "secret_aws_key": {
            "pattern": r"AKIA[0-9A-Z]{16}",
            "title": "AWS access key exposed",
            "severity": "critical",
            "cwe": "CWE-798",
            "fix": "Rotate this key immediately and use IAM roles instead"
        },
        "secret_github_token": {
            "pattern": r"gh[pousr]{1,2}_[a-zA-Z0-9_]{36,255}",
            "title": "GitHub token exposed",
            "severity": "critical",
            "cwe": "CWE-798",
            "fix": "Revoke this token immediately and use GitHub App tokens instead"
        },
        "secret_slack_token": {
            "pattern": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9_]{24,32}",
            "title": "Slack token exposed",
            "severity": "critical",
            "cwe": "CWE-798",
            "fix": "Revoke this token immediately and rotate your secrets"
        },
        "secret_api_key": {
            "pattern": r"api[_-]?key\s*[=:]\s*['\"]([a-zA-Z0-9_\-]{32,})['\"]",
            "title": "API key exposed",
            "severity": "critical",
            "cwe": "CWE-798",
            "fix": "Rotate this key and use environment variables for storage"
        },
        "secret_private_key": {
            "pattern": r"-----BEGIN\s+(RSA|EC|PGP|OPENSSH|PRIVATE)\s+.*KEY",
            "title": "Private key exposed",
            "severity": "critical",
            "cwe": "CWE-798",
            "fix": "Revoke this key immediately and regenerate a new one"
        },
        "secret_db_connection": {
            "pattern": r"(mongodb|mysql|postgresql)://[a-zA-Z0-9]+:[a-zA-Z0-9]+@",
            "title": "Database connection string with credentials",
            "severity": "critical",
            "cwe": "CWE-798",
            "fix": "Use environment variables and remove credentials from code"
        },
        "secret_jwt": {
            "pattern": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.",
            "title": "JWT token exposed",
            "severity": "high",
            "cwe": "CWE-798",
            "fix": "Revoke this token and regenerate with proper security"
        }
    }

    def __init__(self, target: str, output_base: str, report_format: str, min_severity: str) -> None:
        """
        Initialize the security scanner.

        Args:
            target: Directory to scan
            output_base: Base path for report output
            report_format: Output format ("json", "md", or "both")
            min_severity: Minimum severity level to report
        """
        self.target = Path(target).resolve()
        self.output_base = Path(output_base)
        self.report_format = report_format
        self.min_severity = min_severity
        self.findings: List[SecurityFinding] = []
        self.tools_used: List[str] = []

        if not self.target.exists():
            raise ValueError(f"Target directory does not exist: {self.target}")

    def should_report(self, severity: str) -> bool:
        """Check if finding severity meets the minimum threshold."""
        min_level = self.SEVERITY_LEVELS.get(self.min_severity, 3)
        finding_level = self.SEVERITY_LEVELS.get(severity, 3)
        return finding_level <= min_level

    def scan_bandit(self) -> None:
        """Run Bandit scanner if available."""
        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.target), "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode not in [0, 1]:
                logger.warning(f"Bandit exited with code {result.returncode}")
                return

            data = json.loads(result.stdout)
            self.tools_used.append("bandit")

            for result_item in data.get("results", []):
                severity = result_item.get("severity", "medium").lower()
                if self.should_report(severity):
                    finding = SecurityFinding(
                        severity=severity,
                        title=result_item.get("issue_text", "Unknown issue"),
                        file=result_item.get("filename", "unknown"),
                        line=result_item.get("line_number", 0),
                        code=result_item.get("code", ""),
                        cwe=None,
                        fix=f"Review {result_item.get('test_id', 'issue')} in Bandit documentation",
                        tool="bandit"
                    )
                    self.findings.append(finding)
            logger.info(f"Bandit found {len([f for f in self.findings if f.tool == 'bandit'])} issues")
        except FileNotFoundError:
            logger.debug("Bandit not found, skipping")
        except Exception as e:
            logger.error(f"Error running Bandit: {e}")

    def scan_semgrep(self) -> None:
        """Run Semgrep scanner if available."""
        try:
            result = subprocess.run(
                ["semgrep", "--config", "p/security-audit", "--json", str(self.target)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode not in [0, 1]:
                logger.warning(f"Semgrep exited with code {result.returncode}")
                return

            data = json.loads(result.stdout)
            self.tools_used.append("semgrep")

            for result_item in data.get("results", []):
                severity = result_item.get("extra", {}).get("severity", "medium").lower()
                if self.should_report(severity):
                    finding = SecurityFinding(
                        severity=severity,
                        title=result_item.get("check_id", "Unknown") + ": " + result_item.get("extra", {}).get("message", ""),
                        file=result_item.get("path", "unknown"),
                        line=result_item.get("start", {}).get("line", 0),
                        code="",
                        cwe=None,
                        fix="Review the Semgrep documentation for this rule",
                        tool="semgrep"
                    )
                    self.findings.append(finding)
            logger.info(f"Semgrep found {len([f for f in self.findings if f.tool == 'semgrep'])} issues")
        except FileNotFoundError:
            logger.debug("Semgrep not found, skipping")
        except Exception as e:
            logger.error(f"Error running Semgrep: {e}")

    def scan_builtin(self) -> None:
        """Run built-in pattern scanning."""
        self.tools_used.append("built-in")
        file_count = 0
        issues_found = 0

        # Determine which file extensions to scan
        extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".env", ".txt", ".conf"}

        for file_path in self.target.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue

            file_count += 1
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                logger.debug(f"Could not read {file_path}: {e}")
                continue

            # Apply each pattern
            for pattern_name, pattern_config in self.PATTERNS.items():
                try:
                    regex = re.compile(pattern_config["pattern"], re.MULTILINE | re.IGNORECASE)
                    for match in regex.finditer(content):
                        severity = pattern_config["severity"]
                        if not self.should_report(severity):
                            continue

                        # Calculate line number
                        line_num = content[:match.start()].count("\n") + 1

                        # Extract code snippet (context around the match)
                        lines = content.split("\n")
                        start_line = max(0, line_num - 2)
                        end_line = min(len(lines), line_num + 2)
                        code_snippet = "\n".join(lines[start_line:end_line])

                        finding = SecurityFinding(
                            severity=severity,
                            title=pattern_config["title"],
                            file=str(file_path.relative_to(self.target)),
                            line=line_num,
                            code=code_snippet,
                            cwe=pattern_config.get("cwe"),
                            fix=pattern_config.get("fix"),
                            tool="built-in"
                        )
                        self.findings.append(finding)
                        issues_found += 1
                except Exception as e:
                    logger.debug(f"Error applying pattern {pattern_name} to {file_path}: {e}")

        logger.info(f"Built-in scanner scanned {file_count} files and found {issues_found} issues")

    def generate_json_report(self, output_path: Path) -> None:
        """Generate JSON format report."""
        report = {
            "target": str(self.target),
            "date": datetime.now().isoformat(),
            "tools_used": self.tools_used,
            "summary": self._get_summary(),
            "findings": [f.to_dict() for f in self.findings]
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"JSON report written to {output_path}")

    def generate_markdown_report(self, output_path: Path) -> None:
        """Generate Markdown format report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write("# Security Audit Report\n\n")
            f.write(f"**Target:** {self.target}\n\n")
            f.write(f"**Date:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Tools Used:** {', '.join(self.tools_used)}\n\n")

            summary = self._get_summary()
            f.write("## Summary\n\n")
            f.write(f"- **Critical:** {summary['critical']}\n")
            f.write(f"- **High:** {summary['high']}\n")
            f.write(f"- **Medium:** {summary['medium']}\n")
            f.write(f"- **Low:** {summary['low']}\n")
            f.write(f"- **Total:** {summary['total']}\n\n")

            if not self.findings:
                f.write("No security findings detected.\n")
            else:
                # Group by severity
                by_severity = {}
                for finding in self.findings:
                    if finding.severity not in by_severity:
                        by_severity[finding.severity] = []
                    by_severity[finding.severity].append(finding)

                for severity in ["critical", "high", "medium", "low"]:
                    if severity in by_severity:
                        f.write(f"## {severity.upper()} Severity Findings\n\n")
                        for finding in by_severity[severity]:
                            f.write(f"### {finding.title}\n\n")
                            f.write(f"- **File:** {finding.file}\n")
                            f.write(f"- **Line:** {finding.line}\n")
                            f.write(f"- **Tool:** {finding.tool}\n")
                            if finding.cwe:
                                f.write(f"- **CWE:** {finding.cwe}\n")
                            f.write(f"\n**Code:**\n```\n{finding.code}\n```\n\n")
                            if finding.fix:
                                f.write(f"**Fix:** {finding.fix}\n\n")
                            f.write("---\n\n")

        logger.info(f"Markdown report written to {output_path}")

    def _get_summary(self) -> Dict[str, int]:
        """Get summary counts by severity."""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": len(self.findings)}
        for finding in self.findings:
            if finding.severity in summary:
                summary[finding.severity] += 1
        return summary

    def run(self) -> int:
        """
        Execute the full security scan.

        Returns:
            Exit code: 0 = no critical/high findings, 1 = critical/high found, 2 = error
        """
        try:
            logger.info(f"Starting security scan of {self.target}")

            # Run all available scanners
            self.scan_bandit()
            self.scan_semgrep()
            self.scan_builtin()

            # Sort findings by severity and line number
            self.findings.sort(key=lambda f: (self.SEVERITY_LEVELS.get(f.severity, 3), f.file, f.line))

            # Generate reports
            if self.report_format in ["json", "both"]:
                json_path = Path(f"{self.output_base}.json")
                self.generate_json_report(json_path)

            if self.report_format in ["md", "both"]:
                md_path = Path(f"{self.output_base}.md")
                self.generate_markdown_report(md_path)

            # Determine exit code
            summary = self._get_summary()
            if summary["critical"] > 0 or summary["high"] > 0:
                logger.warning(f"Found {summary['critical']} critical and {summary['high']} high severity issues")
                return 1

            logger.info("Scan completed successfully with no critical/high findings")
            return 0

        except Exception as e:
            logger.error(f"Scan failed with error: {e}", exc_info=True)
            return 2


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Production security scanner with Bandit, Semgrep, and built-in patterns"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Directory to scan for security issues"
    )
    parser.add_argument(
        "--output",
        default="./security-report",
        help="Base path for report output (default: ./security-report)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "md", "both"],
        default="both",
        help="Output format (default: both)"
    )
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low", "all"],
        default="all",
        help="Minimum severity level to report (default: all)"
    )

    args = parser.parse_args()

    try:
        scanner = SecurityScanner(
            target=args.target,
            output_base=args.output,
            report_format=args.format,
            min_severity=args.severity if args.severity != "all" else "low"
        )
        return scanner.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 2
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
        return 2


if __name__ == "__main__":
    sys.exit(main())
