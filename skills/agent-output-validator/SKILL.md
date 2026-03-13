---
name: agent-output-validator
description: >
  Verify outputs from parallel agent dispatches against expected contracts.
  Checks file paths, content requirements, and schema compliance after agents
  complete. Use when launching multiple agents in parallel, after agent
  completion, or when "agent wrote to wrong path" errors occur. Triggers on
  "validate agent output", "check agent results", "agent-output-validator",
  or "verify parallel agents".
---

## Overview

The agent-output-validator skill ensures that agents dispatched in parallel produce outputs that match your expected contract. This prevents silent failures where agents write to the wrong location, miss required files, or produce invalid content.

## Contract Definition Format

Define your agent outputs as a JSON contract file specifying what each agent should produce:

```json
{
  "agents": [
    {
      "name": "agent-name",
      "expected_files": [
        {
          "path": "/absolute/path/to/file",
          "min_size": 100,
          "max_size": 10000,
          "contains": ["required", "string", "patterns"],
          "not_contains": ["forbidden", "patterns"],
          "syntax_check": "python",
          "line_count_min": 10,
          "line_count_max": 500
        }
      ]
    }
  ]
}
```

### Contract Fields

**Agent level:**
- `name` (required) — Agent identifier, must be unique
- `expected_files` (required) — Array of file specifications

**File level:**
- `path` (required) — Absolute file path to validate
- `min_size` — File must be at least N bytes (optional)
- `max_size` — File must be at most N bytes (optional)
- `contains` — List of strings that must all appear in file (optional)
- `not_contains` — List of strings that must not appear in file (optional)
- `syntax_check` — One of: "python" (py_compile), "json" (json.loads), "yaml" (YAML parser) (optional)
- `line_count_min` — Minimum line count (optional)
- `line_count_max` — Maximum line count (optional)

All checks are AND-ed together. A file passes only if all specified checks pass.

## Validation Workflow

1. **Define Contract** — Create a JSON file describing expected outputs for each agent
2. **Dispatch Agents** — Launch multiple agents in parallel to produce outputs
3. **Validate** — Run the validator against the contract
4. **Inspect Results** — Review the detailed report to identify failures

Example workflow:

```bash
# 1. Create contract
cat > contract.json << 'EOF'
{
  "agents": [
    {
      "name": "security-audit-builder",
      "expected_files": [
        {
          "path": "/path/to/SKILL.md",
          "min_size": 100,
          "contains": ["---", "name:", "description:"]
        },
        {
          "path": "/path/to/scripts/scanner.py",
          "min_size": 500,
          "syntax_check": "python"
        }
      ]
    }
  ]
}
EOF

# 2. Dispatch agents (in parallel)
# Agent 1 writes to /path/to/
# Agent 2 writes to /path/to/

# 3. Validate outputs
python3 validate_outputs.py --contract contract.json --format text

# 4. Check exit code and review report
if [ $? -ne 0 ]; then
  echo "Agent outputs do not match contract"
  exit 1
fi
```

## Common Failure Modes

### Wrong Path
Agent writes to `/tmp/output/file.py` but contract expects `/home/user/output/file.py`.

**Diagnosis:** Validator reports "File not found at expected path"

**Resolution:** Verify agent's output directory configuration or update contract to match actual path.

### Missing Files
Agent produces only `SKILL.md` but contract requires both `SKILL.md` and `scripts/helper.py`.

**Diagnosis:** Validator reports file missing for `scripts/helper.py`

**Resolution:** Check agent logs to identify why file was not created. May indicate agent failure or incomplete execution.

### Schema Violations
Agent's Python file has syntax errors, JSON is malformed, or YAML is invalid.

**Diagnosis:** Validator reports syntax check failure with parsing error details

**Resolution:** Agent produced structurally invalid content. Review agent logic for encoding, indentation, or format errors.

### Content Mismatches
- `contains` check fails: Required string not found in file (typo, missing section)
- `not_contains` check fails: Forbidden string appears (debug output left in, wrong template used)

**Diagnosis:** Validator reports specific string not found or unexpected string found

**Resolution:** Review agent output and contract expectations. May indicate agent bug or template issue.

### Size Violations
File too small (incomplete output) or too large (runaway generation).

**Diagnosis:** Validator reports file size out of range: N bytes (expected M-K bytes)

**Resolution:** Check agent output completeness or investigate generator loops. May indicate agent timeout or truncation.

### Line Count Violations
File has too few or too many lines.

**Diagnosis:** Validator reports line count out of range: N lines (expected M-K lines)

**Resolution:** Verify agent output structure matches expectations. May indicate formatting issues or incomplete generation.

## Usage

Run the validator from command line:

```bash
python3 scripts/validate_outputs.py --contract /path/to/contract.json
```

### Options

- `--contract PATH` (required) — Path to JSON contract file
- `--format json|text` — Output format (default: text)
- `--strict` — Treat all validation warnings as errors (default: false)

### Output Formats

**Text format (default):**
```
VALIDATION REPORT
================

Agent: security-audit-builder
  Status: PASS
  Files: 2/2 passed

Agent: de-slop-builder
  Status: FAIL
  Files: 1/2 passed

  security-slop-scanner.py
    ERROR: File not found at /path/to/scripts/security-slop-scanner.py

SUMMARY
=======
Agents passed: 1/2
Files passed: 3/4
Exit code: 1
```

**JSON format:**
```json
{
  "summary": {
    "agents_passed": 1,
    "agents_total": 2,
    "files_passed": 3,
    "files_total": 4,
    "exit_code": 1
  },
  "agents": [
    {
      "name": "security-audit-builder",
      "passed": true,
      "files": [
        {
          "path": "/path/to/SKILL.md",
          "passed": true,
          "checks": []
        }
      ]
    }
  ]
}
```

## Exit Codes

- `0` — All agents and files passed validation
- `1` — One or more agents or files failed validation

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)
- Supports Linux, macOS, Windows

## Examples

### Example 1: Basic Validation

Contract expects two agents to each produce SKILL.md files:

```json
{
  "agents": [
    {
      "name": "agent-a",
      "expected_files": [
        {
          "path": "/output/agent-a/SKILL.md",
          "min_size": 200,
          "contains": ["---", "name:", "description:"]
        }
      ]
    },
    {
      "name": "agent-b",
      "expected_files": [
        {
          "path": "/output/agent-b/SKILL.md",
          "min_size": 200,
          "contains": ["---", "name:", "description:"]
        }
      ]
    }
  ]
}
```

### Example 2: Python Syntax Validation

Validate that generated Python files are syntactically correct:

```json
{
  "agents": [
    {
      "name": "code-generator",
      "expected_files": [
        {
          "path": "/output/main.py",
          "min_size": 500,
          "syntax_check": "python"
        },
        {
          "path": "/output/utils.py",
          "syntax_check": "python",
          "not_contains": ["TODO", "FIXME"]
        }
      ]
    }
  ]
}
```

### Example 3: Multi-File Agent Output

Validate all files from a complex agent:

```json
{
  "agents": [
    {
      "name": "full-skill-builder",
      "expected_files": [
        {
          "path": "/output/SKILL.md",
          "min_size": 100,
          "contains": ["---", "name:", "description:"]
        },
        {
          "path": "/output/scripts/validator.py",
          "syntax_check": "python",
          "line_count_min": 50
        },
        {
          "path": "/output/tests/test_validator.py",
          "syntax_check": "python",
          "contains": ["def test_"]
        },
        {
          "path": "/output/README.md",
          "min_size": 200
        }
      ]
    }
  ]
}
```

## Tips

- Use `min_size` and `max_size` to catch truncated or runaway outputs
- Use `syntax_check` for any generated code to catch encoding or formatting errors
- Use `contains` to verify critical sections are present (e.g., docstrings, license headers)
- Use `not_contains` to filter debug output, placeholder text, or incomplete markers
- Run validation immediately after agents complete to catch failures quickly
- Keep contracts in version control alongside agent definitions
