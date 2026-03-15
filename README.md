# Cortex Research Suite

21 autonomous skills for AI/ML research and development. Covers research workflows, MLOps enforcement, security auditing, agent orchestration, quality assurance, and developer tooling. Works natively with Claude Code and integrates with LangChain, CrewAI, and OpenAI via MCP adapters.

## Quick Start

```bash
git clone https://github.com/TECHKNOWMAD-LABS/cortex-research-suite.git
cd cortex-research-suite/skills/<skill-name>
```

Each skill directory contains a `SKILL.md` with setup instructions and a `scripts/` directory with Python implementations.

## Skills

| Skill | Category | Description |
|-------|----------|-------------|
| `agent-orchestrator` | Agents | Multi-agent coordination and task dispatch |
| `agent-output-validator` | Validation | Automated validation of agent outputs against quality gates |
| `code-review-engine` | Engineering | Automated code review with security checks |
| `context-engineer` | Engineering | Context window optimization and prompt context management |
| `de-slop` | Quality | AI-generated writing pattern detection and removal |
| `design-system-forge` | Design | Design system generation and component library scaffolding |
| `dev-lifecycle-engine` | DevOps | Development lifecycle management |
| `diff-generator` | Engineering | Structured diff generation for code and document changes |
| `github-mcp` | Integration | GitHub API via Model Context Protocol |
| `meta-skill-evolver` | Meta | Evolutionary skill improvement and mutation engine |
| `mlops-standards` | MLOps | ML operations best practices enforcement |
| `persistent-memory` | Infrastructure | SQLite-backed memory with FTS5 search |
| `pre-package-pipeline` | Packaging | Skill validation and packaging pipeline |
| `prompt-architect` | Engineering | Prompt engineering and optimization |
| `repo-publisher` | DevOps | Pre-publish pipeline with security scanning and quality gates |
| `research-workflow` | Research | Experiment design and methodology |
| `security-audit` | Security | Bandit + semgrep + secret scanning pipeline |
| `session-memory` | Infrastructure | Session-scoped memory persistence across conversations |
| `skill-test-harness` | Testing | Automated skill testing framework |
| `skill-validator` | Validation | Skill structure and manifest validation |
| `tdd-enforcer` | Testing | Test-driven development enforcement with coverage tracking |

## Skill Organism

The `skill-organism/` directory contains the evolution engine. Skills are automatically tested and scored. Underperformers get modified via mutation, top performers get replicated via crossbreeding, and the system recovers from population loss by restoring previously successful versions. Generation 0-1 skills are preserved indefinitely.

The enterprise runner (`enterprise_runner.py`) enforces SHA-256 integrity checks on the skill registry, supports atomic rollback on failure, and returns CI/CD-compatible exit codes.

## Cross-Platform Support

The `cross-platform/` directory contains generated adapters for each platform.

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
cortex-research-suite/
├── skills/                    # Native Claude Code skills (21 skills)
│   ├── <skill-name>/
│   │   ├── SKILL.md           # Skill definition and instructions
│   │   └── scripts/           # Python implementations
├── skill-organism/            # Skill evolution engine
│   ├── organism.py            # Core evolution: observe/mutate/select/reproduce/heal
│   ├── enterprise_runner.py   # Production runner with SHA-256 integrity
│   └── cortex_skill_organism/ # Installable package
├── packages/                  # Distributable skill packages
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

- Bandit Python SAST with zero HIGH findings
- CodeQL semantic code analysis
- Secret scanning with push protection enabled
- Dependabot automated dependency updates
- Safe XML parsing via defusedxml (no XXE)

Report vulnerabilities to admin@techknowmad.ai. See [SECURITY.md](SECURITY.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. All PRs require:

- Passing CI checks (bandit, lint, tests)
- One approving review
- No leaked secrets or credentials

## License

MIT — see [LICENSE](LICENSE).
