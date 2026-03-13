#!/usr/bin/env python3
"""
Pre-Package Pipeline: Quality assurance for skill packaging.

Orchestrates validation, security scanning, writing quality checks,
and packaging into a single pre-flight gate.
"""

import sys
import os
import json
import argparse
import zipfile
import re
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any, List, Optional


class PipelineStage:
    """Base class for pipeline stages."""

    def __init__(self, name: str):
        self.name = name
        self.status = None
        self.errors = []
        self.warnings = []
        self.data = {}

    def run(self, skill_dir: Path, tools_dir: Optional[Path] = None) -> bool:
        """Run stage. Return True if gate passes, False if blocked."""
        raise NotImplementedError

    def format_output(self) -> str:
        """Format stage result for console output."""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Serialize stage result to dict."""
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "data": self.data,
        }


class ValidationStage(PipelineStage):
    """Skill structure and metadata validation."""

    def __init__(self):
        super().__init__("Skill Validation")

    def run(self, skill_dir: Path, tools_dir: Optional[Path] = None) -> bool:
        """Validate skill structure and metadata."""
        self.errors = []
        self.warnings = []

        # Check SKILL.md exists
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            self.errors.append("SKILL.md not found in skill root")
            self.status = "FAIL"
            return False

        # Validate YAML frontmatter
        try:
            with open(skill_md, "r") as f:
                content = f.read()
                if not content.startswith("---"):
                    self.errors.append(
                        "SKILL.md missing YAML frontmatter (must start with ---)"
                    )
                    self.status = "FAIL"
                    return False

                # Extract frontmatter
                parts = content.split("---", 2)
                if len(parts) < 3:
                    self.errors.append("SKILL.md frontmatter not properly closed")
                    self.status = "FAIL"
                    return False

                fm = parts[1]
                if "name:" not in fm:
                    self.errors.append("SKILL.md frontmatter missing 'name' field")
                    self.status = "FAIL"
                    return False

                if "description:" not in fm:
                    self.errors.append(
                        "SKILL.md frontmatter missing 'description' field"
                    )
                    self.status = "FAIL"
                    return False

        except Exception as e:
            self.errors.append(f"Error reading SKILL.md: {str(e)}")
            self.status = "FAIL"
            return False

        # Check scripts directory exists
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.exists():
            self.warnings.append("scripts/ directory not found (optional)")

        # Validate Python scripts syntax
        if scripts_dir.exists():
            for py_file in scripts_dir.glob("*.py"):
                try:
                    with open(py_file, "r") as f:
                        compile(f.read(), str(py_file), "exec")
                except SyntaxError as e:
                    self.errors.append(
                        f"Syntax error in {py_file.name}: {e.msg} (line {e.lineno})"
                    )
                    self.status = "FAIL"
                    return False

        # Extract skill name for reporting
        try:
            with open(skill_md, "r") as f:
                for line in f:
                    if line.startswith("name:"):
                        self.data["skill_name"] = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

        self.status = "PASS"
        return True

    def format_output(self) -> str:
        status_str = f"{self.status}"
        if self.errors:
            status_str += f" ({len(self.errors)} error{'s' if len(self.errors) > 1 else ''})"
        elif self.warnings:
            status_str += f" ({len(self.warnings)} warning{'s' if len(self.warnings) > 1 else ''})"
        return status_str.ljust(20)


class SecurityStage(PipelineStage):
    """Security vulnerability scanning."""

    # Security patterns to detect
    SECURITY_PATTERNS = [
        (r"\beval\s*\(", "eval() usage", "CRITICAL"),
        (r"os\.system\s*\(", "os.system() usage", "CRITICAL"),
        (r"\$\{.*\}", "Unquoted shell variable expansion", "HIGH"),
        (r"exec\s*\(", "exec() usage", "HIGH"),
        (
            r"(password|passwd|pwd|secret|api_key|apikey|token|auth)\s*=\s*['\"]",
            "Hardcoded credential",
            "CRITICAL",
        ),
        (r"chmod.*666|chmod.*777", "Unsafe file permissions", "HIGH"),
        (r"rm\s+-rf\s+/", "Dangerous rm pattern", "CRITICAL"),
        (r"SELECT.*FROM.*WHERE", "SQL query in code", "MEDIUM"),
        (r"<\?xml|<!ENTITY", "XML/XXE risk pattern", "MEDIUM"),
        (r"pickle\.loads|yaml\.load\s*\(", "Unsafe deserialization", "HIGH"),
    ]

    def __init__(self):
        super().__init__("Security Scan")
        self.findings = []

    def run(self, skill_dir: Path, tools_dir: Optional[Path] = None) -> bool:
        """Scan for security issues."""
        self.errors = []
        self.warnings = []
        self.findings = []
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        # Try to load external security_scan.py
        if tools_dir and (tools_dir / "security_scan.py").exists():
            try:
                findings = self._load_external_scanner(tools_dir, skill_dir)
                if findings:
                    self.findings = findings
                    for finding in findings:
                        severity_counts[finding.get("severity", "LOW")] += 1
                    self.status = "PASS"
                    return severity_counts["CRITICAL"] == 0 and severity_counts["HIGH"] == 0
            except Exception as e:
                self.warnings.append(f"Failed to load external scanner: {str(e)}")

        # Built-in security scanning
        for file_path in skill_dir.rglob("*"):
            if file_path.is_file() and (
                file_path.suffix in [".py", ".sh", ".md"] or file_path.name == "Dockerfile"
            ):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for pattern, desc, severity in self.SECURITY_PATTERNS:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[: match.start()].count("\n") + 1
                                severity_counts[severity] += 1
                                self.findings.append(
                                    {
                                        "file": str(file_path.relative_to(skill_dir)),
                                        "line": line_num,
                                        "pattern": desc,
                                        "severity": severity,
                                        "snippet": content[
                                            match.start() : match.start() + 60
                                        ].replace("\n", " "),
                                    }
                                )
                except Exception:
                    pass

        self.data = severity_counts
        blocked = severity_counts["CRITICAL"] > 0 or severity_counts["HIGH"] > 0
        self.status = "PASS" if not blocked else "BLOCK"

        if blocked:
            self.errors.append(
                f"Security findings: {severity_counts['CRITICAL']} critical, "
                f"{severity_counts['HIGH']} high"
            )
        elif severity_counts["MEDIUM"] > 0 or severity_counts["LOW"] > 0:
            self.warnings.append(
                f"Security findings: {severity_counts['MEDIUM']} medium, "
                f"{severity_counts['LOW']} low"
            )

        return not blocked

    def _load_external_scanner(self, tools_dir: Path, skill_dir: Path) -> List[Dict]:
        """Load and run external security_scan.py if available."""
        scanner_path = tools_dir / "security_scan.py"
        spec = importlib.util.spec_from_file_location("security_scan", scanner_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "scan"):
            return module.scan(str(skill_dir))
        return []

    def format_output(self) -> str:
        counts = self.data
        detail = (
            f"({counts['CRITICAL']} critical, {counts['HIGH']} high, "
            f"{counts['MEDIUM']} medium)"
        )
        status = "PASS" if self.status == "PASS" else "BLOCK"
        return f"{status} {detail}".ljust(20)


class WritingQualityStage(PipelineStage):
    """AI writing quality analysis."""

    # AI writing indicators
    AI_PATTERNS = [
        r"\b(delve|traverse|harness|leverage|robust|synergy|paradigm)\b",
        r"\b(it\s+is\s+(important|crucial|vital|essential))\b",
        r"\b(in\s+conclusion|furthermore|in\s+summary)\b",
        r"\b(This\s+allows\s+for|enables\s+you\s+to)\b",
        r"\b(innovative|cutting-edge|state-of-the-art|game-changing)\b",
        r"\b(unlock|unleash|empower|transform|revolutionize)\b",
    ]

    def __init__(self):
        super().__init__("Writing Quality")
        self.issues = []

    def run(self, skill_dir: Path, tools_dir: Optional[Path] = None) -> bool:
        """Check writing quality in markdown files."""
        self.errors = []
        self.warnings = []
        self.issues = []

        total_score = 0
        file_count = 0

        # Try external slop_scanner.py
        if tools_dir and (tools_dir / "slop_scanner.py").exists():
            try:
                score = self._load_external_scanner(tools_dir, skill_dir)
                if score is not None:
                    self.data["score"] = score
                    self.data["max_score"] = 100
                    blocked = score > 70
                    warned = score > 40
                    self.status = "BLOCK" if blocked else ("WARN" if warned else "PASS")
                    if blocked:
                        self.errors.append(f"Writing quality score too high: {score}/100")
                    elif warned:
                        self.warnings.append(f"Writing quality score elevated: {score}/100")
                    return not blocked
            except Exception as e:
                self.warnings.append(f"Failed to load external scanner: {str(e)}")

        # Built-in quality check
        for md_file in skill_dir.rglob("*.md"):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    file_score = self._score_writing(content, md_file)
                    total_score += file_score
                    file_count += 1
                    if file_score > 40:
                        self.issues.append(
                            {
                                "file": str(md_file.relative_to(skill_dir)),
                                "score": file_score,
                            }
                        )
            except Exception:
                pass

        if file_count > 0:
            avg_score = total_score // file_count
        else:
            avg_score = 0

        self.data["score"] = avg_score
        self.data["max_score"] = 100
        self.data["files_checked"] = file_count

        blocked = avg_score > 70
        warned = avg_score > 40

        self.status = "BLOCK" if blocked else ("WARN" if warned else "PASS")

        if blocked:
            self.errors.append(f"Writing quality score too high: {avg_score}/100")
        elif warned:
            self.warnings.append(f"Writing quality score elevated: {avg_score}/100")

        return not blocked

    def _score_writing(self, content: str, file_path: Path) -> int:
        """Score writing quality (0-100, higher = worse)."""
        score = 0
        word_count = len(content.split())

        for pattern in self.AI_PATTERNS:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            score += min(matches * 3, 20)

        # Check for generic phrases
        generic_count = len(
            re.findall(
                r"\b(allows|enables|provides|offers|helps|supports)\b",
                content,
                re.IGNORECASE,
            )
        )
        score += min(generic_count, 15)

        # Penalize short content or unclear structure
        if word_count < 100:
            score += 10

        # Normalize to 0-100
        score = min(score, 100)
        return score

    def _load_external_scanner(self, tools_dir: Path, skill_dir: Path) -> Optional[int]:
        """Load and run external slop_scanner.py if available."""
        scanner_path = tools_dir / "slop_scanner.py"
        spec = importlib.util.spec_from_file_location("slop_scanner", scanner_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "scan"):
            return module.scan(str(skill_dir))
        return None

    def format_output(self) -> str:
        score = self.data.get("score", 0)
        status = "PASS" if self.status == "PASS" else (
            "WARN" if self.status == "WARN" else "BLOCK"
        )
        return f"{status} (score: {score}/100)".ljust(20)


class PackageStage(PipelineStage):
    """Create .skill archive."""

    def __init__(self):
        super().__init__("Package")
        self.filename = None
        self.size_kb = 0

    def run(self, skill_dir: Path, tools_dir: Optional[Path] = None) -> bool:
        """Create .skill zip archive."""
        # This stage is called with output_dir parameter in main pipeline
        # Placeholder for stage structure
        self.status = "PENDING"
        return True

    def package(self, skill_dir: Path, output_dir: Path) -> bool:
        """Create package. Called by pipeline after gates pass."""
        self.errors = []
        self.warnings = []

        # Get skill name from SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_name = "skill"
        try:
            with open(skill_md, "r") as f:
                for line in f:
                    if line.startswith("name:"):
                        skill_name = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

        output_dir.mkdir(parents=True, exist_ok=True)
        skill_file = output_dir / f"{skill_name}.skill"

        try:
            # Create zip file
            with zipfile.ZipFile(skill_file, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in skill_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(skill_dir)
                        zf.write(file_path, arcname)

            # Verify integrity
            try:
                with zipfile.ZipFile(skill_file, "r") as zf:
                    result = zf.testzip()
                    if result is not None:
                        self.errors.append(f"ZIP integrity check failed: {result}")
                        self.status = "FAIL"
                        return False
            except Exception as e:
                self.errors.append(f"ZIP integrity verification failed: {str(e)}")
                self.status = "FAIL"
                return False

            # Calculate size
            self.size_kb = skill_file.stat().st_size / 1024

            self.filename = skill_file.name
            self.data["filename"] = self.filename
            self.data["size_kb"] = round(self.size_kb, 1)
            self.data["integrity"] = "VERIFIED"
            self.status = "DONE"
            return True

        except Exception as e:
            self.errors.append(f"Packaging failed: {str(e)}")
            self.status = "FAIL"
            return False

    def format_output(self) -> str:
        if self.status == "DONE":
            return (
                f"{self.status} -> {self.filename} ({self.size_kb:.1f} KB)".ljust(20)
            )
        return f"{self.status}".ljust(20)


class Pipeline:
    """Orchestrates the pre-package pipeline."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stages: List[PipelineStage] = [
            ValidationStage(),
            SecurityStage(),
            WritingQualityStage(),
            PackageStage(),
        ]
        self.skip_security = False
        self.skip_slop = False
        self.force = False

    def run(
        self,
        skill_dir: Path,
        output_dir: Path,
        tools_dir: Optional[Path] = None,
    ) -> Tuple[int, str]:
        """Run full pipeline. Return (exit_code, result_string)."""
        skill_dir = Path(skill_dir).resolve()
        output_dir = Path(output_dir).resolve()

        if not skill_dir.exists():
            return 2, f"Skill directory not found: {skill_dir}"

        if self.verbose:
            print(f"Skill directory: {skill_dir}")
            if tools_dir:
                print(f"Tools directory: {tools_dir}")

        # Run stages 1-3 (gates)
        gates_passed = True
        blocked_gates = []

        for idx, stage in enumerate(self.stages[:3], 1):
            # Skip optional stages
            if isinstance(stage, SecurityStage) and self.skip_security:
                stage.status = "SKIP"
                continue
            if isinstance(stage, WritingQualityStage) and self.skip_slop:
                stage.status = "SKIP"
                continue

            if self.verbose:
                print(f"\nRunning {stage.name}...")

            passed = stage.run(skill_dir, tools_dir)

            if not passed:
                gates_passed = False
                if stage.status == "BLOCK" or (stage.errors and not self.force):
                    blocked_gates.append(stage.name)

            if self.verbose and stage.errors:
                for error in stage.errors:
                    print(f"  ERROR: {error}")
            if self.verbose and stage.warnings:
                for warning in stage.warnings:
                    print(f"  WARNING: {warning}")

        # Run stage 4 (package) only if gates pass
        package_stage = self.stages[3]
        if gates_passed or self.force:
            if self.verbose:
                print(f"\nRunning {package_stage.name}...")
            if package_stage.package(skill_dir, output_dir):
                result = "PASS"
                exit_code = 0
            else:
                result = "FAIL"
                exit_code = 1
        else:
            result = "BLOCKED"
            exit_code = 1
            package_stage.status = "SKIPPED"

        # Determine overall result string
        if exit_code == 0:
            has_warnings = any(
                s.status == "WARN" for s in self.stages if s.status is not None
            )
            if has_warnings:
                result_str = "PASS with warnings"
            else:
                result_str = "PASS"
        else:
            result_str = "BLOCKED" if blocked_gates else "FAIL"

        return exit_code, result_str

    def format_console_output(self) -> str:
        """Format stages for console output."""
        lines = []
        for idx, stage in enumerate(self.stages, 1):
            if stage.status == "SKIP":
                status = "SKIP"
            elif stage.status is None:
                status = "PENDING"
            else:
                status = stage.format_output()

            line = f"[STAGE {idx}/{len(self.stages)}] {stage.name:<25} {status}"
            lines.append(line)

        return "\n".join(lines)

    def report_json(self) -> Dict[str, Any]:
        """Generate JSON report."""
        skill_name = self.stages[0].data.get("skill_name", "unknown")

        return {
            "skill_name": skill_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "stages": {
                "validation": self.stages[0].to_dict(),
                "security": self.stages[1].to_dict(),
                "writing_quality": self.stages[2].to_dict(),
                "package": self.stages[3].to_dict(),
            },
            "overall_result": "UNKNOWN",
            "exit_code": -1,
        }


def discover_tools_dir(skill_dir: Path) -> Optional[Path]:
    """Auto-discover tools directory."""
    # Check common locations
    for candidate in [
        skill_dir.parent / "tools" / "scripts",
        skill_dir.parent / "scripts",
        skill_dir / "scripts",
        Path.cwd() / "scripts",
    ]:
        if candidate.exists():
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Pre-Package Pipeline: Quality assurance before skill packaging"
    )
    parser.add_argument(
        "--skill-dir", required=True, help="Path to skill directory to package"
    )
    parser.add_argument(
        "--output", required=True, help="Output directory for .skill file"
    )
    parser.add_argument(
        "--tools-dir",
        help="Directory containing validator/scanner scripts (auto-discovered if omitted)",
    )
    parser.add_argument(
        "--skip-security", action="store_true", help="Skip security scanning stage"
    )
    parser.add_argument(
        "--skip-slop", action="store_true", help="Skip writing quality check stage"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Package despite warnings (warnings become non-blocking)",
    )
    parser.add_argument("--report", help="Write detailed JSON report to specified path")
    parser.add_argument(
        "--verbose", action="store_true", help="Print detailed output for each stage"
    )

    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    output_dir = Path(args.output).resolve()

    tools_dir = None
    if args.tools_dir:
        tools_dir = Path(args.tools_dir).resolve()
    else:
        tools_dir = discover_tools_dir(skill_dir)

    pipeline = Pipeline(verbose=args.verbose)
    pipeline.skip_security = args.skip_security
    pipeline.skip_slop = args.skip_slop
    pipeline.force = args.force

    exit_code, result_str = pipeline.run(skill_dir, output_dir, tools_dir)

    # Output results
    print(pipeline.format_console_output())
    print()
    print(f"Result: {result_str}")

    # Write JSON report if requested
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report = pipeline.report_json()
        report["overall_result"] = result_str
        report["exit_code"] = exit_code

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        if args.verbose:
            print(f"Report written to: {report_path}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
