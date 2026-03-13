# Cortex

Enterprise-grade autonomous skill suite for Claude Code and Cowork.

Cortex is a modular collection of 18 production-ready skills that extend Claude's capabilities across the full software development lifecycle — from design intelligence and test-driven development to multi-agent orchestration and self-evolving skill generation.

Built by [TechKnowmad AI](https://techknowmad.ai).

---

## Quick Install

Download any `.skill` file from [`packages/`](./packages) and drag it into Claude Desktop or Cowork.

---

## Skill Catalog

### Development Lifecycle

| Skill | Description |
|---|---|
| [`dev-lifecycle-engine`](./skills/dev-lifecycle-engine) | 7-phase mandatory pipeline: brainstorm, plan, setup, implement, test, review, merge. |
| [`tdd-enforcer`](./skills/tdd-enforcer) | RED-GREEN-REFACTOR enforcement with 12 anti-pattern detectors and quality scoring. |
| [`code-review-engine`](./skills/code-review-engine) | Two-stage review separating spec compliance from code quality with severity-based blocking. |

### Memory and Context

| Skill | Description |
|---|---|
| [`persistent-memory`](./skills/persistent-memory) | SQLite + FTS5 hybrid search with progressive disclosure and cross-session persistence. |
| [`context-engineer`](./skills/context-engineer) | Token budget management with 4-factor relevance scoring and auto-pruning. |
| [`session-memory`](./skills/session-memory) | Lightweight session state checkpointing for context compaction recovery. |

### Multi-Agent Orchestration

| Skill | Description |
|---|---|
| [`agent-orchestrator`](./skills/agent-orchestrator) | DAG-based task graphs with fan-out, pipeline, and map-reduce patterns. Self-healing recovery. |
| [`agent-output-validator`](./skills/agent-output-validator) | Contract-based output verification for parallel agent dispatches. |

### Design Intelligence

| Skill | Description |
|---|---|
| [`design-system-forge`](./skills/design-system-forge) | 50+ industry design rules, WCAG validation, and framework-specific output. |

### Quality and Security

| Skill | Description |
|---|---|
| [`security-audit`](./skills/security-audit) | Bandit + semgrep SAST scanning with secret detection and severity scoring. |
| [`de-slop`](./skills/de-slop) | AI writing pattern scanner detecting emoji headers, hyperbolic language, and buzzword stacking. |
| [`skill-validator`](./skills/skill-validator) | Pre-flight validation for YAML frontmatter, directory structure, and script syntax. |
| [`pre-package-pipeline`](./skills/pre-package-pipeline) | 4-stage quality gate: validation, security, writing quality, packaging. |

### Meta and Evolution

| Skill | Description |
|---|---|
| [`meta-skill-evolver`](./skills/meta-skill-evolver) | Autonomous skill generation, validation, testing, and packaging pipeline. |
| [`skill-test-harness`](./skills/skill-test-harness) | JSON-defined test suites with 7 assertion types and regression detection. |
| [`diff-generator`](./skills/diff-generator) | File snapshots and unified diffs for safe multi-file editing with rollback. |

### Infrastructure

| Skill | Description |
|---|---|
| [`github-mcp`](./skills/github-mcp) | GitHub MCP server builder with 18 REST API tools via FastMCP. |
| [`repo-publisher`](./skills/repo-publisher) | Pre-publish pipeline: security scan, slop detection, structure validation, metadata updates. |

---

## Architecture

Each skill follows a standard structure:

```
skill-name/
├── SKILL.md              # Frontmatter + instructions (name + description only)
├── scripts/              # Executable tools (Python 3.10+, stdlib-only)
│   └── tool.py
└── references/           # Supporting documentation (optional)
    └── reference.md
```

Skills compose into production stacks:

```
dev-lifecycle-engine
  ├── tdd-enforcer          (test phase)
  ├── code-review-engine    (review phase)
  ├── security-audit        (pre-merge gate)
  └── de-slop               (documentation gate)

agent-orchestrator
  ├── agent-output-validator (post-dispatch verification)
  ├── persistent-memory      (cross-session state)
  └── context-engineer       (token budget management)

meta-skill-evolver
  ├── skill-validator       (validation stage)
  ├── skill-test-harness    (testing stage)
  └── pre-package-pipeline  (packaging stage)
```

## Requirements

Python 3.10+ with stdlib only. No external dependencies.

## License

MIT
