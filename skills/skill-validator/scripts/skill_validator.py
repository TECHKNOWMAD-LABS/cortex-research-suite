#!/usr/bin/env python3
"""
Skill Validator - Pre-flight validation for Claude Code skills.

Validates YAML frontmatter schema, directory structure, script integrity,
and markdown quality before packaging skills as .skill files.
"""

import argparse
import json
import os
import sys
import py_compile
import re
from datetime import datetime
from pathlib import Path


class SkillValidator:
    """Validates skill directory structure and content."""

    ALLOWED_FRONTMATTER_FIELDS = {"name", "description"}
    ALLOWED_TOP_LEVEL = {"SKILL.md", "scripts", "references"}
    SKILL_FILE = "SKILL.md"
    MAX_FILE_SIZE = 50 * 1024  # 50KB

    def __init__(self, target_path):
        """Initialize validator with target skill directory."""
        self.target_path = Path(target_path)
        self.report = {
            "target": str(self.target_path),
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "warnings": [],
            "errors": [],
            "passed": True,
        }

    def validate(self):
        """Run all validation checks."""
        self._validate_frontmatter()
        self._validate_directory_structure()
        self._validate_scripts()
        self._validate_markdown()
        return self.report

    def _validate_frontmatter(self):
        """Validate SKILL.md YAML frontmatter."""
        checks = {}

        # Check if SKILL.md exists
        skill_file = self.target_path / self.SKILL_FILE
        if not skill_file.exists():
            checks["file_exists"] = False
            self.report["errors"].append("SKILL.md not found in skill directory")
            self.report["passed"] = False
            self.report["checks"]["frontmatter"] = checks
            return

        checks["file_exists"] = True

        # Read and parse frontmatter
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            checks["readable"] = False
            self.report["errors"].append(f"Cannot read SKILL.md: {e}")
            self.report["passed"] = False
            self.report["checks"]["frontmatter"] = checks
            return

        checks["readable"] = True

        # Check for frontmatter delimiters
        lines = content.split("\n")
        if not lines or lines[0] != "---":
            checks["yaml_structure"] = False
            self.report["errors"].append("SKILL.md must start with --- delimiter")
            self.report["passed"] = False
            self.report["checks"]["frontmatter"] = checks
            return

        # Find closing delimiter
        closing_index = None
        for i in range(1, len(lines)):
            if lines[i] == "---":
                closing_index = i
                break

        if closing_index is None:
            checks["yaml_structure"] = False
            self.report["errors"].append("SKILL.md missing closing --- delimiter")
            self.report["passed"] = False
            self.report["checks"]["frontmatter"] = checks
            return

        checks["yaml_structure"] = True

        # Parse YAML frontmatter
        frontmatter_lines = lines[1:closing_index]
        frontmatter = {}
        parse_errors = []

        for line in frontmatter_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                parse_errors.append(f"Invalid YAML line: {line}")
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Handle YAML block scalar indicator
            if value == ">":
                # Multi-line description - collect subsequent lines
                idx = frontmatter_lines.index(line)
                desc_lines = []
                for desc_line in frontmatter_lines[idx + 1 :]:
                    stripped = desc_line.strip()
                    if not stripped:
                        continue
                    desc_lines.append(stripped)
                value = " ".join(desc_lines)

            if key not in self.ALLOWED_FRONTMATTER_FIELDS:
                self.report["errors"].append(
                    f"Unknown frontmatter field: {key} (allowed: {', '.join(sorted(self.ALLOWED_FRONTMATTER_FIELDS))})"
                )
                self.report["passed"] = False
            else:
                frontmatter[key] = value

        checks["no_unknown_fields"] = len(self.report["errors"]) == 0

        # Validate required fields
        if "name" not in frontmatter or not frontmatter["name"]:
            checks["name_field"] = False
            self.report["errors"].append("name field is required and must not be empty")
            self.report["passed"] = False
        else:
            checks["name_field"] = True

        if "description" not in frontmatter or not frontmatter["description"]:
            checks["description_field"] = False
            self.report["errors"].append(
                "description field is required and must not be empty"
            )
            self.report["passed"] = False
        else:
            checks["description_field"] = True
            # Warn if description is a single long line
            if "\n" not in frontmatter["description"] and len(
                frontmatter["description"]
            ) > 100:
                self.report["warnings"].append(
                    "description is a single long line; consider using > block scalar"
                )

        self.report["checks"]["frontmatter"] = checks

    def _validate_directory_structure(self):
        """Validate skill directory structure."""
        checks = {}

        if not self.target_path.is_dir():
            checks["is_directory"] = False
            self.report["errors"].append(f"Target path is not a directory")
            self.report["passed"] = False
            self.report["checks"]["directory_structure"] = checks
            return

        checks["is_directory"] = True

        # Check top-level contents
        top_level = set(item.name for item in self.target_path.iterdir())
        unexpected = top_level - self.ALLOWED_TOP_LEVEL

        if unexpected:
            checks["no_unexpected_files"] = False
            self.report["errors"].append(
                f"Unexpected files/directories at root: {', '.join(sorted(unexpected))}"
            )
            self.report["passed"] = False
        else:
            checks["no_unexpected_files"] = True

        # Validate scripts/ directory
        scripts_dir = self.target_path / "scripts"
        if scripts_dir.exists():
            if not scripts_dir.is_dir():
                checks["scripts_is_directory"] = False
                self.report["errors"].append("scripts must be a directory")
                self.report["passed"] = False
            else:
                checks["scripts_is_directory"] = True
                script_files = list(scripts_dir.iterdir())
                valid_scripts = all(
                    f.suffix in {".py", ".sh"} for f in script_files if f.is_file()
                )
                if not valid_scripts:
                    checks["scripts_valid_extensions"] = False
                    self.report["errors"].append(
                        "scripts/ must contain only .py or .sh files"
                    )
                    self.report["passed"] = False
                else:
                    checks["scripts_valid_extensions"] = True
        else:
            checks["scripts_optional"] = True

        # Validate references/ directory
        references_dir = self.target_path / "references"
        if references_dir.exists():
            if not references_dir.is_dir():
                checks["references_is_directory"] = False
                self.report["errors"].append("references must be a directory")
                self.report["passed"] = False
            else:
                checks["references_is_directory"] = True
                ref_files = list(references_dir.iterdir())
                valid_refs = all(
                    f.suffix == ".md" for f in ref_files if f.is_file()
                )
                if not valid_refs:
                    checks["references_valid_extensions"] = False
                    self.report["errors"].append(
                        "references/ must contain only .md files"
                    )
                    self.report["passed"] = False
                else:
                    checks["references_valid_extensions"] = True
        else:
            checks["references_optional"] = True

        self.report["checks"]["directory_structure"] = checks

    def _validate_scripts(self):
        """Validate Python and shell scripts."""
        checks = {}

        scripts_dir = self.target_path / "scripts"
        if not scripts_dir.exists():
            checks["scripts_present"] = False
            self.report["checks"]["scripts"] = checks
            return

        checks["scripts_present"] = True
        python_files = list(scripts_dir.glob("*.py"))
        shell_files = list(scripts_dir.glob("*.sh"))

        # Validate Python files
        python_valid = True
        for py_file in python_files:
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                python_valid = False
                self.report["errors"].append(
                    f"Python syntax error in {py_file.name}: {e}"
                )
                self.report["passed"] = False

        checks["python_syntax"] = python_valid
        checks["python_file_count"] = len(python_files)

        # Validate shell scripts
        shell_valid = True
        for sh_file in shell_files:
            try:
                with open(sh_file, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                if not first_line.startswith("#!"):
                    shell_valid = False
                    self.report["errors"].append(
                        f"Shell script {sh_file.name} missing shebang"
                    )
                    self.report["passed"] = False
            except Exception as e:
                shell_valid = False
                self.report["errors"].append(f"Cannot read {sh_file.name}: {e}")
                self.report["passed"] = False

        checks["shell_syntax"] = shell_valid
        checks["shell_file_count"] = len(shell_files)

        # Check file sizes
        all_scripts = list(scripts_dir.glob("*"))
        size_valid = True
        for script_file in all_scripts:
            if script_file.is_file():
                size = script_file.stat().st_size
                if size > self.MAX_FILE_SIZE:
                    size_valid = False
                    self.report["errors"].append(
                        f"File {script_file.name} exceeds 50KB limit ({size} bytes)"
                    )
                    self.report["passed"] = False

        checks["file_sizes"] = size_valid

        self.report["checks"]["scripts"] = checks

    def _validate_markdown(self):
        """Validate markdown files."""
        checks = {}

        skill_file = self.target_path / self.SKILL_FILE
        if not skill_file.exists():
            checks["skill_md_exists"] = False
            self.report["checks"]["markdown"] = checks
            return

        checks["skill_md_exists"] = True

        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            checks["skill_md_readable"] = False
            self.report["errors"].append(f"Cannot read SKILL.md for markdown check: {e}")
            self.report["passed"] = False
            self.report["checks"]["markdown"] = checks
            return

        checks["skill_md_readable"] = True

        # Check heading structure
        lines = content.split("\n")
        markdown_lines = lines[lines.index("---", 1) + 1 :]
        headings = [
            (i, line.strip())
            for i, line in enumerate(markdown_lines)
            if line.strip().startswith("#")
        ]

        heading_valid = True
        if headings and not headings[0][1].startswith("# "):
            heading_valid = False
            self.report["warnings"].append(
                "First heading should be H1 (# ) for consistency"
            )

        checks["heading_structure"] = heading_valid

        # Check code blocks
        code_blocks = content.count("```")
        if code_blocks % 2 != 0:
            checks["code_blocks"] = False
            self.report["errors"].append("Unclosed code blocks detected (``` count is odd)")
            self.report["passed"] = False
        else:
            checks["code_blocks"] = True

        # Check links
        link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
        links = re.findall(link_pattern, content)
        link_valid = all(link[1] for link in links)
        checks["links"] = link_valid

        self.report["checks"]["markdown"] = checks

    def format_report(self):
        """Format report for human-readable output."""
        output = []
        output.append("SKILL VALIDATION REPORT")
        output.append("=" * 23)
        output.append(f"\nTarget: {self.report['target']}")
        output.append(f"Validation Time: {self.report['timestamp']}")

        # Print each section
        for section, checks in self.report["checks"].items():
            output.append(f"\n{section.upper().replace('_', ' ')}")
            for check, result in checks.items():
                if isinstance(result, bool):
                    status = "PASS" if result else "FAIL"
                    output.append(f"  {check}: {status}")
                else:
                    output.append(f"  {check}: {result}")

        # Print errors
        if self.report["errors"]:
            output.append("\nERRORS")
            for error in self.report["errors"]:
                output.append(f"  - {error}")

        # Print warnings
        if self.report["warnings"]:
            output.append("\nWARNINGS")
            for warning in self.report["warnings"]:
                output.append(f"  - {warning}")

        # Print result
        output.append("")
        if self.report["passed"]:
            output.append("RESULT: ALL CHECKS PASSED")
        else:
            output.append("RESULT: VALIDATION FAILED")

        return "\n".join(output)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Pre-flight validation for Claude Code skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        required=True,
        type=str,
        help="Path to skill directory to validate",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON report instead of human-readable format",
    )

    args = parser.parse_args()

    # Validate target exists
    if not os.path.exists(args.target):
        print(f"Error: target path does not exist: {args.target}", file=sys.stderr)
        sys.exit(1)

    # Run validation
    validator = SkillValidator(args.target)
    report = validator.validate()

    # Output results
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(validator.format_report())

    # Exit with appropriate code
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
