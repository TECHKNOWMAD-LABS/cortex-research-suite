---
name: code-review-engine
description: >
  Two-stage code review with spec compliance validation and code quality
  analysis. Severity-based issue reporting with blocking gates. Use when
  reviewing code changes, validating implementations against specs, or when
  "code review", "review this", "code-review-engine", "spec compliance",
  "quality check", or "review PR" is mentioned.
---

# Code Review Engine

A two-stage code review system that validates spec compliance and analyzes code quality with severity-based blocking gates.

## Overview

This skill implements a professional code review engine with two separate review gates:

1. **Stage 1: Spec Compliance Review** — Validates that implementation matches approved specification
2. **Stage 2: Code Quality Review** — Analyzes code for correctness, performance, security, and maintainability

Issues are classified by severity (CRITICAL, MAJOR, MINOR, INFO) to determine merge eligibility.

## Stage 1: SPEC COMPLIANCE REVIEW

Compare the implementation against an approved specification or requirement document. This gate ensures the code does what it was supposed to do.

### Compliance Checks

- **Requirements Coverage**: Are all requirements from the spec implemented?
- **Scope Creep**: Are there unauthorized additions beyond the spec?
- **Function Signatures**: Do function/method signatures match the specification?
- **Edge Cases**: Are all edge cases mentioned in the spec handled?
- **Error Paths**: Are all error scenarios from the spec covered with appropriate handling?
- **Configuration**: Does the code handle configuration as specified?
- **Dependencies**: Are external dependencies and integrations as specified?

### Output

- **Compliance Score**: 0-100% indicating requirement coverage
- **Gap List**: Specific missing or incorrectly implemented requirements with spec section references
- **Verdict**: PASS or FAIL (must pass to proceed to Stage 2)

## Stage 2: CODE QUALITY REVIEW

Analyze code for defects, inefficiencies, and maintainability issues across five dimensions.

### Correctness

- Logic errors and off-by-one bugs
- Null/None safety and error handling
- Resource management and cleanup
- Boundary condition handling
- Type mismatches or unsafe operations

### Performance

- Algorithmic complexity (O(n²) where O(n) possible)
- Unnecessary object allocations or copies
- N+1 query patterns
- Inefficient data structure usage
- Unoptimized loops or iterations

### Security

- SQL injection vulnerabilities
- Command injection risks
- Path traversal vulnerabilities
- Hardcoded secrets or credentials
- Unsafe deserialization
- Missing input validation

### Maintainability

- Function length (>50 lines = refactor candidate)
- Cyclomatic complexity (>10 = too complex)
- Unclear variable/function naming
- Missing or unclear documentation
- Poor module organization

### Style

- Language convention adherence (PEP 8 for Python, etc.)
- Consistent formatting and indentation
- Import organization and naming
- Comment quality and clarity
- Dead code or unused imports

### Output

- **Issue Count** by severity (CRITICAL, MAJOR, MINOR, INFO)
- **Detailed Issues**: Each issue with:
  - Severity level
  - Location (file, line number)
  - Problem description
  - Suggested fix
  - Category (Correctness, Performance, Security, Maintainability, Style)

## Severity Classification

### CRITICAL (Blocks Merge)

Blocks code from being merged. Must be fixed before proceeding.

- Security vulnerabilities (injection, secrets, unsafe patterns)
- Data loss risks or corruption potential
- Spec violations (missing critical requirements)
- Runtime crashes or unhandled exceptions

### MAJOR (Must Fix Before Merge)

Should be fixed before merge. May allow exceptions in specific cases.

- Logic errors affecting core functionality
- Performance regressions (e.g., 10x slower)
- Missing required tests or test coverage gaps
- Resource leaks or memory issues
- Missing error handling for specified error cases

### MINOR (Should Fix)

Should be addressed but may be deferred to future PR.

- Code style or formatting issues
- Unclear naming or documentation
- Functions exceeding length guidelines
- Unused imports or variables
- Suboptimal but functional implementations

### INFO (Optional)

Suggestions and improvements for consideration.

- Alternative approaches or better patterns
- Code organization suggestions
- Documentation improvements
- Future optimization opportunities
- Library or framework suggestions

## Review Report Format

The review generates a markdown report with this structure:

```markdown
## Review Summary

- **Spec Compliance**: 87% (2 gaps found)
- **Code Quality**: 4 issues (0 critical, 1 major, 2 minor, 1 info)
- **VERDICT**: CHANGES REQUESTED

## Spec Compliance Gaps

1. [MISSING] Error handler for timeout case (spec section 3.2)
2. [MISSING] Retry logic not implemented (spec section 4.1)

## Code Quality Issues

1. [CRITICAL] SQL injection in user_query() — line 45
2. [MAJOR] Function exceeds 50 lines — extract helper
3. [MINOR] Missing docstring on public method
4. [INFO] Consider using dataclass instead of dict

## Detailed Analysis

[Comprehensive breakdown of each issue with context and suggestions]
```

## Usage

### Basic Review

Review code against a specification:

```bash
python3 scripts/review_engine.py review \
  --spec spec.md \
  --target src/ \
  --output review.md
```

### Parameters

- `--spec`: Path to specification file (markdown format)
- `--target`: Path to code directory or file to review
- `--output`: Path to save review report (markdown)
- `--strict`: Fail on MAJOR issues (default: fail only on CRITICAL)

### Specification Format

Create a markdown specification with requirements clearly marked:

```markdown
# User Authentication Module

## Requirements

### REQ-1: Login Function
- Function name: `authenticate_user(email, password)`
- Must handle invalid email format with ValueError
- Must handle missing password with ValueError
- Must check credentials against database
- Must rate-limit failed attempts (max 5 per minute)
- Must log all login attempts
- Should timeout after 5 seconds

### REQ-2: Token Generation
- Generate JWT tokens valid for 24 hours
- Must include user ID in token
- Must include issue timestamp
- Must not include password or secrets
```

## Workflow

1. **Prepare Specification**: Define requirements in markdown with clear section markers
2. **Run Review**: Execute the review engine against your code
3. **Read Report**: Review the compliance gaps and quality issues
4. **Stage 1 Decision**: Fix compliance gaps or dispute spec requirements
5. **Stage 2 Decision**: Address quality issues based on severity
6. **Merge Decision**: PASS all gates before merging

## Integration

Use this skill when:

- Reviewing pull requests before merge
- Validating implementations against specifications
- Ensuring code quality standards across a project
- Mentoring junior developers with detailed feedback
- Running automated quality gates in CI/CD pipelines

## See Also

- `references/review-checklist.md` — Detailed checklist for manual review
- `scripts/review_engine.py` — Implementation details and AST analysis logic
