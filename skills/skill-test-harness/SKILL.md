---
name: skill-test-harness
description: >
  Automated test runner for skill scripts with fixtures, assertions, and
  regression detection. Use when testing skill scripts, validating scanner
  output, or checking for regressions after modifications. Triggers on
  "test skill", "run skill tests", "skill-test-harness", "regression check",
  or "validate skill output".
---

# Skill Test Harness

Automated testing framework for skill scripts with built-in fixture management, comprehensive assertions, and regression detection.

## Overview

The test harness executes skill scripts against a suite of test cases, each with fixtures (input data) and assertions (expected outcomes). Tests run in isolated environments, and a summary report indicates pass/fail status.

## Test Definition Format

Tests are defined in JSON with the following structure:

```json
{
  "skill": "skill-name",
  "tests": [
    {
      "name": "test_case_name",
      "command": "command to execute",
      "fixtures_dir": "path/to/fixtures",
      "assertions": [
        { "type": "assertion_type", ...assertion_params }
      ]
    }
  ]
}
```

### Required Fields

- **skill** — Name of the skill being tested
- **tests** — Array of test case objects
- **name** (per test) — Unique identifier for the test
- **command** — Shell command to execute; supports template variables
- **assertions** — Array of assertion objects to validate the outcome

### Optional Fields

- **fixtures_dir** — Directory containing test input files; defaults to `fixtures/` relative to test file directory
- **timeout** — Test timeout in seconds (default: 30)
- **env** — Object of environment variables to pass to the command

## Template Variables

Template variables are expanded in commands at runtime:

| Variable | Expansion |
|----------|-----------|
| `{scripts}` | Path to scripts directory (from `--scripts-dir`) |
| `{fixtures}` | Path to fixtures directory for this test |
| `{output}` | Isolated temp directory for test outputs |

Example command:
```bash
python3 {scripts}/security_scan.py --target {fixtures}/test_input --output {output}/results.json
```

## Test Fixture Format

Fixtures are organized per test case in the `fixtures_dir`:

```
fixtures/
├── eval_test/
│   ├── suspicious.py
│   ├── another_file.js
│   └── requirements.txt
├── clean_code/
│   ├── main.py
│   └── utils.py
└── malformed_json/
    └── input.json
```

Each subdirectory under `fixtures/` corresponds to a test's `fixtures_dir` parameter. Files in the fixture directory are available to the test command via the `{fixtures}` variable.

## Assertion Types

### exit_code
Validates the process exit code.

```json
{"type": "exit_code", "expected": 0}
```

Parameters:
- `expected` (int) — Expected exit code

### file_exists
Validates that a file was created.

```json
{"type": "file_exists", "path": "{output}/results.json"}
```

Parameters:
- `path` (string) — Path to file (supports `{output}` variable)

### file_not_exists
Validates that a file was not created.

```json
{"type": "file_not_exists", "path": "{output}/error.log"}
```

Parameters:
- `path` (string) — Path to file (supports `{output}` variable)

### output_contains
Validates that stdout or stderr contains a substring.

```json
{"type": "output_contains", "text": "scan completed"}
```

Parameters:
- `text` (string) — Substring to find in output

### output_not_contains
Validates that stdout or stderr does not contain a substring.

```json
{"type": "output_not_contains", "text": "error occurred"}
```

Parameters:
- `text` (string) — Substring that should not appear

### json_field
Validates a field in a JSON file using comparison operators.

```json
{"type": "json_field", "path": "{output}/report.json", "field": "summary.critical_count", "operator": "gte", "value": 1}
```

Parameters:
- `path` (string) — Path to JSON file (supports `{output}` variable)
- `field` (string) — Dotted path to field (e.g., `summary.critical_count`, `results[0].status`)
- `operator` (string) — Comparison operator: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `contains`
- `value` — Expected value for comparison

### line_count
Validates the number of lines in an output file.

```json
{"type": "line_count", "path": "{output}/lines.txt", "operator": "eq", "value": 42}
```

Parameters:
- `path` (string) — Path to file (supports `{output}` variable)
- `operator` (string) — Comparison operator: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`
- `value` (int) — Expected line count

### regex_match
Validates that output matches a regular expression.

```json
{"type": "regex_match", "pattern": "found \\d+ issues"}
```

Parameters:
- `pattern` (string) — Regular expression pattern to match in stdout/stderr

## Example Test Definition

```json
{
  "skill": "security-audit",
  "tests": [
    {
      "name": "detects_eval_in_python",
      "command": "python3 {scripts}/security_scan.py --target {fixtures}/eval_test --format json --output {output}/result.json",
      "fixtures_dir": "fixtures/eval_test",
      "timeout": 30,
      "assertions": [
        {"type": "exit_code", "expected": 1},
        {"type": "file_exists", "path": "{output}/result.json"},
        {"type": "json_field", "path": "{output}/result.json", "field": "summary.critical", "operator": "gte", "value": 1},
        {"type": "output_contains", "text": "eval detected"}
      ]
    },
    {
      "name": "clean_code_passes",
      "command": "python3 {scripts}/security_scan.py --target {fixtures}/clean_code --format json --output {output}/result.json",
      "fixtures_dir": "fixtures/clean_code",
      "assertions": [
        {"type": "exit_code", "expected": 0},
        {"type": "json_field", "path": "{output}/result.json", "field": "summary.critical", "operator": "eq", "value": 0}
      ]
    }
  ]
}
```

## Running Tests

### Basic Usage

```bash
python3 test_runner.py --test-file tests.json --scripts-dir ./scripts
```

### With Custom Fixtures and Output

```bash
python3 test_runner.py \
  --test-file tests.json \
  --scripts-dir ./scripts \
  --fixtures-dir /custom/fixtures \
  --output-dir /tmp/test-output
```

### Verbose Output

```bash
python3 test_runner.py --test-file tests.json --scripts-dir ./scripts --verbose
```

### JSON Report for CI Integration

```bash
python3 test_runner.py \
  --test-file tests.json \
  --scripts-dir ./scripts \
  --json-report /tmp/results.json
```

## Test Runner Behavior

- Each test runs in an isolated temporary directory
- Stdout, stderr, and exit code are captured
- Template variables are expanded before command execution
- Assertions are evaluated in order; first failure stops evaluation
- Test timeout is 30 seconds by default (configurable per test)
- Exit code: 0 if all tests pass, 1 if any test fails

## Regression Detection Workflow

1. Run baseline tests and capture JSON report:
   ```bash
   python3 test_runner.py --test-file tests.json --scripts-dir ./scripts --json-report baseline.json
   ```

2. Modify skill scripts and run tests again:
   ```bash
   python3 test_runner.py --test-file tests.json --scripts-dir ./scripts --json-report current.json
   ```

3. Compare reports:
   ```bash
   diff baseline.json current.json
   ```

Changes in the current.json report relative to baseline.json indicate regressions or improvements.

## Best Practices

- **Organize fixtures by test case** — Create separate subdirectories under `fixtures/` for each test's input
- **Use fixtures for realistic data** — Include actual files, code samples, and edge cases
- **Test both success and failure paths** — Include tests for valid and invalid inputs
- **Keep assertions focused** — Use multiple specific assertions rather than one broad check
- **Use JSON field assertions for structured output** — Preferred over output parsing
- **Version control test definitions** — Store tests.json in the skill repository
- **Run tests in CI/CD pipelines** — Use `--json-report` for integration with CI tools

## Command-Line Options

```
python3 test_runner.py [OPTIONS]

Options:
  --test-file PATH              Path to test definition JSON file (required)
  --scripts-dir PATH            Path to scripts directory (required)
  --fixtures-dir PATH           Path to fixtures directory (default: fixtures/ relative to test file)
  --output-dir PATH             Path for test output (default: temporary directory)
  --json-report PATH            Write JSON report to file
  --verbose                     Print detailed test output
  --help                        Show this help message
```

## Exit Codes

- `0` — All tests passed
- `1` — One or more tests failed
- `2` — Invalid arguments or configuration error
