---
name: repo-publisher
description: >
  Pre-publish pipeline for GitHub repositories. Chains security scanning,
  AI slop detection, structure validation, and repo metadata updates into a
  single workflow. Use when the user mentions "publish to GitHub", "ship this
  repo", "make this repo production-ready", "pre-publish check", "repo
  quality gate", "publish this skill", "push to GitHub with checks", or any
  request to prepare and publish a codebase to GitHub. Also triggers on
  "repo-publisher", "publish pipeline", or "release checklist".
---

# Repo Publisher — Pre-Publish Pipeline

Orchestrates security scanning, writing quality checks, structure validation,
and GitHub publishing into a single workflow. The goal: every published repo
meets a consistent quality bar.

## When to Use

Use this when publishing code to GitHub, releasing a skill, or preparing a
repository for public visibility. This skill chains other skills and tools
together — it doesn't duplicate their functionality.

## Pipeline Stages

### Stage 1: Structure Validation

Check that the repo has required files:
```
Required:
  ✓ README.md
  ✓ LICENSE (or LICENSE.md or LICENSE.txt)
  ✓ .gitignore

Recommended:
  ○ CHANGELOG.md
  ○ CONTRIBUTING.md
  ○ .github/workflows/ (CI/CD)

For skills:
  ✓ SKILL.md
  ○ scripts/ (if the skill references any)
  ○ references/ (if the skill references any)
```

If required files are missing, generate them:
- README.md — scaffold from directory contents and any SKILL.md present
- LICENSE — ask user which license (default: MIT)
- .gitignore — generate based on detected languages

### Stage 2: Security Scan

Run the `security-audit` skill:
```
Invoke: security-audit
Target: <repo directory>
Output: <workspace>/security-report.{json,md}
```

Gate criteria:
- Zero critical findings → proceed
- Zero secrets detected → proceed
- High findings → warn user, ask to proceed or fix
- Any secrets → BLOCK. Do not publish until resolved.

### Stage 3: Writing Quality Scan

Run the `de-slop` skill:
```
Invoke: de-slop
Target: <repo directory> (all .md files)
Output: <workspace>/slop-report.{json,md}
```

Gate criteria:
- All files score ≤ 15 → proceed
- Any file 16–40 → warn user, show flagged lines
- Any file > 40 → recommend rewrite before publishing

### Stage 4: README Quality Check

Verify the README has:
- Project title and one-line description
- Installation/setup instructions
- Usage examples (at least one code block)
- License reference
- No broken internal links

If using badges, verify badge URLs resolve.

### Stage 5: Git Operations

Prepare the repo for push:
```bash
# Ensure clean working tree
git status

# Check remote is configured
git remote -v

# If no remote, help user set one up
# If remote exists, push
git push origin main
```

If using GitHub MCP (when available):
- Create or update repo via API
- Push files via contents API
- Set description, topics, website

If no GitHub MCP:
- Use `gh` CLI if available
- Fall back to git commands
- Last resort: guide user through manual steps

### Stage 6: Repo Metadata

After pushing:
- Set repo description (concise, no buzzwords)
- Add relevant topics (language, domain, framework)
- Set website URL if applicable
- Verify README renders correctly on GitHub

### Stage 7: Publish Report

Produce a final summary:
```markdown
# Publish Report

**Repo:** github.com/owner/repo
**Date:** 2026-03-13

## Pre-Publish Checks
| Check | Status |
|-------|--------|
| Structure validation | PASS |
| Security scan | PASS (0 critical, 0 high) |
| Writing quality | PASS (avg score: 12) |
| README quality | PASS |
| Git push | PASS |
| Repo metadata | PASS |

## Files Published
- 15 files across 4 directories
- 3 markdown files, 7 Python scripts, 2 configs

## Actions Taken
- Generated .gitignore (Python template)
- Set repo description
- Added topics: python, youtube, content-creation
```

## Configuration

The pipeline can be configured per-repo via a `.publish.yml` file:
```yaml
# .publish.yml
security:
  block_on: [critical, high]  # or [critical] for less strict
  allow_secrets: false         # always false for public repos

writing:
  max_slop_score: 25           # default: 15
  skip_files: [CHANGELOG.md]

structure:
  require: [README.md, LICENSE]
  recommend: [CONTRIBUTING.md]

metadata:
  description: "Short repo description"
  topics: [python, tool]
  website: "https://example.com"
```

## Dependency Skills

This skill orchestrates:
- `security-audit` — Stage 2
- `de-slop` — Stage 3

It works best when both are installed. If either is missing, it runs a
lightweight inline check instead (less thorough, but functional).

## Reference Files

- **`references/publish-checklist.md`** — Detailed checklist for manual
  verification when automated checks aren't available.
