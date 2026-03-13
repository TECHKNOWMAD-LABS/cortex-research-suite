---
name: skill-validator
description: >
  Pre-flight validation for Claude Code skills before packaging. Checks YAML
  frontmatter schema, directory structure, script integrity, and markdown
  quality. Use when packaging skills, before creating .skill files, or when
  "malformed YAML frontmatter" errors occur. Triggers on "validate skill",
  "check skill", "skill-validator", "pre-flight", or "package skill".
---

# Skill Validator

A comprehensive pre-flight validation tool for Claude Code skills. Use this to verify skill integrity before packaging or when encountering YAML frontmatter errors.

## What It Validates

### Frontmatter Schema
- SKILL.md file existence and structure
- YAML delimiters (`---`) present and correctly positioned
- Only allowed fields: `name` and `description`
- `name` is a simple kebab-case string
- `description` is present, non-empty, and properly formatted
- Detects and flags unknown fields (e.g., `tags`, `version`, `author`)
- Warns if description is a single long line instead of using block scalar (`>`)

### Directory Structure
- Required: `SKILL.md` at skill root
- Optional: `scripts/` directory containing `.py` or `.sh` files
- Optional: `references/` directory containing `.md` files
- Flags unexpected top-level files or directories
- Validates directory organization matches skill guidelines

### Script Integrity
- Python files syntax validation using `py_compile`
- Shell scripts must start with shebang (`#!/bin/bash` or `#!/usr/bin/env bash`)
- File size checks (flags files over 50KB as likely errors)
- Encoding and readability checks

### Markdown Quality
- Proper heading hierarchy
- Code block syntax validation
- Link integrity checks
- List formatting consistency

## How to Use

Run the validator against any skill directory:

```bash
python3 scripts/skill_validator.py --target /path/to/skill/directory
```

The validator produces:
1. **JSON report** with detailed pass/fail status for each check
2. **Human-readable summary** with clear pass/fail indicators
3. **Exit code** (0 for all pass, 1 if any validation fails)

## Validation Rules

### Frontmatter Checks
- **PASS**: SKILL.md exists and contains valid YAML frontmatter
- **FAIL**: SKILL.md missing, malformed YAML, or closing `---` delimiter absent
- **FAIL**: Unknown fields present (e.g., `tags`, `author`, `version`)
- **FAIL**: `name` field missing or empty
- **FAIL**: `description` field missing or empty
- **WARN**: Description is a single line (should use `>` block scalar for readability)

### Directory Structure Checks
- **PASS**: Only SKILL.md, optional scripts/, optional references/ at root level
- **FAIL**: Unexpected files or directories at skill root
- **FAIL**: scripts/ directory contains non-executable files
- **FAIL**: references/ directory contains non-markdown files

### Script Validation Checks
- **PASS**: All Python files have valid syntax
- **PASS**: All shell scripts have proper shebang
- **FAIL**: Python syntax errors detected
- **FAIL**: Shell scripts missing shebang
- **FAIL**: Any file exceeds 50KB (likely packaging error)

### Markdown Checks
- **PASS**: Proper heading structure (H1 at top, logical hierarchy)
- **PASS**: Code blocks properly closed
- **PASS**: Links use valid markdown syntax
- **WARN**: Inconsistent list formatting

## Example Output

```
SKILL VALIDATION REPORT
=======================

Target: /path/to/skill-validator
Validation Time: 2026-03-13 14:32:15

FRONTMATTER VALIDATION
  name field: PASS
  description field: PASS
  yaml structure: PASS
  no unknown fields: PASS

DIRECTORY STRUCTURE
  required files: PASS
  no unexpected files: PASS
  scripts/ validation: PASS
  references/ validation: PASS

SCRIPT VALIDATION
  python syntax: PASS (2 files)
  shell syntax: PASS (1 file)
  file sizes: PASS (all < 50KB)

MARKDOWN VALIDATION
  heading structure: PASS
  code blocks: PASS
  links: PASS

RESULT: ALL CHECKS PASSED
Exit Code: 0
```

## Typical Issues and Fixes

**"YAML structure: FAIL"** - Check that SKILL.md starts and ends with `---` on separate lines.

**"Unknown field detected: tags"** - Remove the `tags:` field from frontmatter. Only `name` and `description` are allowed.

**"description is a single line"** - Use YAML block scalar syntax:
```yaml
description: >
  This is a long description that spans
  multiple lines for readability.
```

**"Shell script missing shebang"** - Add `#!/bin/bash` as the first line of your shell scripts.

**"Unexpected file: .gitignore"** - Remove hidden files or place them in a subdirectory (e.g., .git/).
