# TECHKNOWMAD LABS — Cortex Skill Library

Open-source AI agent tools for code quality, security, memory, orchestration, and development lifecycle automation. Every skill runs as a Claude Skill, MCP Server, LangChain Tool, CrewAI Tool, or OpenAI GPT Action from a single source definition.

## Skills

### Code Quality & Security
- **security-audit**: SAST scanning (bandit + semgrep) with secret detection and severity-graded reports
- **code-review-engine**: Multi-dimensional code review (correctness, security, performance, maintainability, style)
- **de-slop**: AI writing pattern detector — scores 0-100 for emoji abuse, hyperbolic language, buzzword stacking
- **tdd-enforcer**: TDD compliance enforcement with coverage thresholds, anti-pattern detection, and pre-commit hooks

### Agent Infrastructure
- **agent-orchestrator**: Multi-agent workflow orchestration with dependency resolution and parallel execution
- **agent-output-validator**: Schema/quality/safety validation for agent outputs — catches hallucinations and drift
- **context-engineer**: Optimal context window assembly with compression, prioritization, and token budgeting
- **persistent-memory**: Key-value memory with TTL, tagging, and semantic search across sessions
- **session-memory**: Lightweight session-scoped checkpoints for context window resets

### Development Lifecycle
- **dev-lifecycle-engine**: Full SDLC tracking from planning through production with gate checks
- **diff-generator**: Snapshot-based file system diffs with structured change reports
- **github-mcp**: GitHub API integration (repos, files, branches, PRs, issues, releases) via MCP
- **repo-publisher**: Pre-publish pipeline chaining security, slop detection, structure validation, and metadata updates

### Skill Development
- **meta-skill-evolver**: Automated skill analysis, metrics collection, and iterative self-improvement
- **skill-validator**: Structure and frontmatter validation against canonical skill spec
- **skill-test-harness**: Test framework for skills with coverage reporting
- **pre-package-pipeline**: Pre-packaging validation ensuring .skill file readiness
- **design-system-forge**: Design system generation from brand parameters with accessibility compliance

## Quick Start

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/<skill-name> && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.<skill_name>.tools import get_all_tools
tools = get_all_tools()
agent = create_react_agent(llm, tools)
```

### CrewAI
```python
from crewai.<skill_name>.tools import *
agent = Agent(role="...", tools=[SecurityScanTool()])
```

### OpenAI Custom GPT
Import `openai/<skill-name>/openapi.json` as a GPT Action in the GPT Builder.

## Architecture

```
cortex/
├── skills/                     # Source skills (SKILL.md + scripts/ + references/)
├── cross-platform/
│   ├── manifests/              # Universal Skill Manifests (JSON)
│   ├── adapters/               # Platform adapter generators
│   ├── tools/                  # Manifest generators and converters
│   └── generated/              # Platform-specific outputs
│       ├── mcp/                # FastMCP servers (18 skills)
│       ├── langchain/          # LangChain BaseTool classes
│       ├── crewai/             # CrewAI BaseTool classes
│       ├── openai/             # OpenAPI 3.1 specs for GPT Actions
│       └── agents/             # AGENTS.md discovery files
├── packages/                   # .skill files for Claude Desktop
└── AGENTS.md                   # This file
```

## Universal Skill Manifest

Each skill is defined by a single JSON manifest that maps to all platforms:

```json
{
  "name": "security-audit",
  "version": "1.0.0",
  "capabilities": [
    {
      "name": "security_scan",
      "input_schema": { "type": "object", "properties": {...} },
      "output_schema": { "type": "object", "properties": {...} }
    }
  ],
  "platforms": {
    "claude_skill": { "entry_point": "SKILL.md" },
    "mcp_server": { "command": "uv", "args": [...] },
    "langchain": { "tool_class": "SecurityScanTool" },
    "crewai": { "tool_class": "SecurityScanTool" },
    "openai_gpt": { "openapi_spec": "openai/security-audit/openapi.json" },
    "github_copilot": { "mcp_config": {...} }
  }
}
```

## Supported Platforms

| Platform | Transport | Status |
|----------|-----------|--------|
| Claude Desktop / Claude Code | Skill (.skill) | Production |
| Claude Desktop | MCP (stdio) | Production |
| GitHub Copilot | MCP (stdio) | Production |
| Cursor | MCP (stdio) | Production |
| Windsurf | MCP (stdio) | Production |
| VS Code (Copilot) | MCP (stdio) | Production |
| JetBrains IDEs | MCP (stdio) | Production |
| LangChain / LangGraph | Python SDK | Production |
| CrewAI | Python SDK | Production |
| OpenAI GPTs | OpenAPI Action | Production |
| Google A2A | Agent Card | Available |

## License

MIT — TECHKNOWMAD LABS
https://github.com/TECHKNOWMAD-LABS