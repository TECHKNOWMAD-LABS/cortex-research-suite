# Cortex

Autonomous skill suite for AI/ML research and development. 18 skills covering research workflows, MLOps, security auditing, agent orchestration, and developer tooling.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/TECHKNOWMAD-LABS/cortex.git

# Install a skill in Claude Code
cd cortex/skills/<skill-name>
# Follow the SKILL.md in each skill directory
```

## Skills

| Skill | Category | Description |
|-------|----------|-------------|
| `research-commander` | Research | Full research lifecycle orchestrator |
| `prompt-architect` | Engineering | Prompt engineering and optimization |
| `tdd-enforcer` | Testing | Test-driven development enforcement with coverage tracking |
| `agent-orchestrator` | Agents | Multi-agent coordination and task dispatch |
| `code-review-engine` | Engineering | Automated code review with security checks |
| `security-audit` | Security | Bandit + semgrep + secret scanning pipeline |
| `persistent-memory` | Infrastructure | SQLite-backed memory with FTS5 search |
| `dev-lifecycle-engine` | DevOps | Development lifecycle management |
| `github-mcp` | Integration | GitHub API via Model Context Protocol |
| `pre-package-pipeline` | Packaging | Skill validation and packaging pipeline |
| `skill-test-harness` | Testing | Automated skill testing framework |
| `mlops-standards` | MLOps | ML operations best practices enforcement |
| `research-workflow` | Research | Experiment design and methodology |
| `model-evaluator` | MLOps | Automated benchmark suite with leaderboards |
| `cost-optimizer` | Operations | Cross-cloud spend analysis |
| `self-healing-agent` | Agents | Autonomous failure detection and recovery |
| `swarm-commander` | Agents | Multi-agent swarm coordination |
| `knowledge-distiller` | Engineering | Document compression into skill prompts |

## Multi-Platform Support

Cortex skills are designed for portability. The `cross-platform/` directory contains generated adapters for each platform.

### Supported Platforms

| Platform | Adapter Type | Directory | Status |
|----------|-------------|-----------|--------|
| Claude Code | Native Skills | `skills/` | Primary |
| MCP (Model Context Protocol) | FastMCP Servers | `cross-platform/generated/mcp/` | Generated |
| LangChain | Tool Classes | `cross-platform/generated/langchain/` | Generated |
| CrewAI | Tool Wrappers | `cross-platform/generated/crewai/` | Generated |
| OpenAI GPT Actions | Action Schemas | `cross-platform/generated/openai/` | Generated |
| AGENTS.md | Agent Definitions | `cross-platform/generated/agents-md/` | Generated |
| VS Code | MCP via Extension | `cross-platform/generated/mcp/` | Compatible |
| JetBrains IDEs | MCP via Plugin | `cross-platform/generated/mcp/` | Compatible |
| GitHub Copilot | MCP via Extension | `cross-platform/generated/mcp/` | Compatible |
| Cursor | MCP via Settings | `cross-platform/generated/mcp/` | Compatible |
| Windsurf | MCP via Config | `cross-platform/generated/mcp/` | Compatible |

### Using with MCP

Each MCP adapter is a standalone FastMCP server:

```bash
cd cross-platform/generated/mcp/<skill-name>/
pip install -e .
python -m <skill_module>
```

### Using with LangChain

```python
from langchain_cortex import SecurityAuditTool

tool = SecurityAuditTool()
result = tool.run({"target": "./my-project"})
```

### Using with CrewAI

```python
from crewai_cortex import SecurityAuditTool

agent = Agent(
    role="Security Analyst",
    tools=[SecurityAuditTool()]
)
```

### Universal Skill Manifest

Each skill has a platform-agnostic manifest at `cross-platform/manifests/<skill>.json` describing inputs, outputs, dependencies, and platform-specific configuration.

## Project Structure

```
cortex/
├── skills/                    # Native Claude Code skills (18 skills)
│   ├── <skill-name>/
│   │   ├── SKILL.md           # Skill definition and instructions
│   │   └── scripts/           # Python implementations
├── cross-platform/
│   ├── manifests/             # Universal Skill Manifests (JSON)
│   ├── generated/             # Platform-specific adapters
│   │   ├── mcp/               # FastMCP servers
│   │   ├── langchain/         # LangChain tools
│   │   ├── crewai/            # CrewAI tools
│   │   ├── openai/            # GPT Action schemas
│   │   └── agents-md/         # AGENTS.md definitions
│   └── adapters/              # Cross-platform adapter framework
├── docs/                      # Documentation site (GitHub Pages)
├── .github/
│   ├── workflows/             # CI/CD (security, lint, CodeQL)
│   ├── CODEOWNERS             # Review requirements
│   └── scripts/               # Setup automation
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── LICENSE                    # MIT
```

## Security

All code passes automated security scanning on every push:

- **Bandit** — Python SAST, zero HIGH findings
- **CodeQL** — GitHub's semantic code analysis
- **Secret scanning** — Push protection enabled
- **Dependabot** — Automated dependency updates
- **defusedxml** — Safe XML parsing (no XXE)

Report vulnerabilities to admin@techknowmad.ai. See [SECURITY.md](SECURITY.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. All PRs require:
- Passing CI checks (bandit, lint, tests)
- One approving review
- No leaked secrets or credentials

## License

MIT — see [LICENSE](LICENSE).
