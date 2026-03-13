---
name: security-audit
description: >
  Automated security scanning for code repositories. Runs bandit (Python SAST),
  semgrep (multi-language static analysis), and secret detection to produce
  machine-readable reports. Use when the user mentions "security audit",
  "scan for vulnerabilities", "check for secrets", "SAST", "static analysis",
  "is this code safe", "security review", "pre-publish security check",
  "bandit", "semgrep", or any request to verify code security before deployment
  or publishing. Also triggers on "enterprise-grade security", "production-ready
  check", or "audit this repo". This skill runs actual tools — not just a
  checklist.
---

# Security Audit

Automated static analysis and secret detection for code repositories. Runs real
tools, produces machine-readable reports, and flags issues with severity scores
and file:line references.

## When to Use

This skill scans code. It does not review architecture or org-level compliance
(use `compliance-as-code` for that) and it does not red-team ML models (use
`red-team-ai-models` for that). It answers one question: "Does this codebase
have security vulnerabilities or leaked secrets?"

## Workflow

### 1. Discover the target

Identify what to scan:
- A directory path provided by the user
- The current working directory
- A repo cloned from a URL

Detect languages present:
```bash
find <target> -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.java" -o -name "*.rb" \) | head -50
```

### 2. Install tools (if missing)

Check availability and install what's needed:

```bash
# Python SAST
which bandit || pip install bandit --break-system-packages -q

# Multi-language SAST
which semgrep || pip install semgrep --break-system-packages -q

# Secret detection
which gitleaks || {
  # Fallback: use the Python script in scripts/secret_scanner.py
  echo "gitleaks not available, using built-in scanner"
}
```

If installs fail, fall back to `scripts/security_scan.py` which uses only
stdlib and regex patterns. Always have a working path — never skip scanning
because a tool isn't available.

### 3. Run scans

Run all applicable scanners. Use `scripts/security_scan.py` as the primary
orchestrator — it handles tool availability, runs what it can, and consolidates
output.

```bash
python <skill-path>/scripts/security_scan.py --target <directory> --output <report-path>
```

The script runs:
1. **Bandit** (if Python files exist) — checks for eval, exec, pickle, shell
   injection, hardcoded passwords, weak crypto, SQL injection
2. **Semgrep** (if installed) — runs `p/security-audit` and `p/secrets` rulesets
3. **Built-in secret scanner** — regex patterns for API keys, tokens, passwords,
   private keys (works without any external tools)
4. **Dependency check** — scans requirements.txt/package.json for known patterns

### 4. Produce report

Output two files:
- `security-report.json` — machine-readable, for CI/CD integration
- `security-report.md` — human-readable, for review

Report structure:
```markdown
# Security Audit Report

**Target:** /path/to/repo
**Date:** 2026-03-13
**Tools:** bandit 1.7.x, semgrep 1.x, built-in secret scanner

## Summary
- **Critical:** 0
- **High:** 2
- **Medium:** 3
- **Low:** 1
- **Secrets detected:** 0

## Findings

### [HIGH] Shell injection via subprocess (CWE-78)
- **File:** scripts/deploy.py:42
- **Code:** `subprocess.run(cmd, shell=True)`
- **Fix:** Use list form: `subprocess.run(["cmd", "arg1", "arg2"])`
- **Tool:** bandit B602

### [MEDIUM] Hardcoded password pattern
- **File:** config/settings.py:18
- **Code:** `DB_PASSWORD = "admin123"`
- **Fix:** Use environment variable: `os.environ["DB_PASSWORD"]`
- **Tool:** built-in secret scanner

## Pass/Fail
**PASS** — No critical or high findings with secrets exposure.
```

### 5. Interpret results

After producing the report, summarize findings for the user. Prioritize:
1. Any secrets or credentials found (always critical)
2. Injection vulnerabilities (shell, SQL, XSS)
3. Unsafe deserialization (pickle, yaml.load)
4. Weak cryptography
5. Information leakage patterns

If zero findings: state the scan passed with a clean bill of health, noting
which tools ran and what was checked.

## What This Skill Checks

### Python (via bandit + regex)
- `eval()`, `exec()`, `compile()` usage
- `pickle.loads()`, `yaml.load()` without SafeLoader
- `subprocess` with `shell=True`
- Hardcoded passwords and secrets
- SQL string formatting (not parameterized)
- Weak hash algorithms (MD5, SHA1 for security)
- `assert` statements in production code
- Wildcard imports

### JavaScript/TypeScript (via semgrep + regex)
- `eval()`, `Function()` constructor
- `innerHTML` assignment (XSS)
- `child_process.exec()` with string interpolation
- Hardcoded API keys and tokens
- `dangerouslySetInnerHTML`

### All Languages (via secret scanner)
- AWS access keys (`AKIA...`)
- GitHub tokens (`ghp_`, `gho_`, `ghs_`)
- Slack tokens (`xoxb-`, `xoxp-`)
- Generic API key patterns
- Private keys (RSA, EC, PGP)
- Database connection strings with credentials
- JWT tokens

## Reference Files

- **`scripts/security_scan.py`** — Main orchestrator script. Runs all scanners,
  consolidates output, produces JSON and markdown reports. Works with stdlib
  only as a fallback.
- **`references/severity-matrix.md`** — CWE-to-severity mapping and
  remediation priority guide.
