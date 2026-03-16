# Cortex Research Suite

[![CI](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/ci.yml)
[![Evaluation Pipeline](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/eval.yml/badge.svg)](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/eval.yml)
[![Security Scan](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/security.yml/badge.svg)](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/security.yml)
[![Python 3.10-3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Skills: 26](https://img.shields.io/badge/skills-26-blueviolet.svg)](skills/)

**AI Research Operating System** — 26 autonomous skills, self-evolving Skill Organism, browser-based experiment arena, and a Python evaluation framework. Covers research workflows, MLOps enforcement, security auditing, agent orchestration, intelligence analysis, and developer tooling. Works natively with Claude Code and integrates with LangChain, CrewAI, and OpenAI via MCP adapters.

## Quickstart — 3 entry points

### 1. Browser (zero install)

Open `dashboards/skill_arena_demo.html` in any browser. Paste your Anthropic API key. Pick a skill. Click **Run Experiment**. Watch the organism evolve in real time.

### 2. Terminal

```bash
git clone https://github.com/TECHKNOWMAD-LABS/cortex-research-suite.git
cd cortex-research-suite
pip install -e ".[dev]"

# Run the test suite
pytest

# Generate evaluation datasets for all 26 skills
python datasets/generators/skill_dataset_generator.py --all-skills --n 50

# Run evaluation on any skill
python skills/skill-test-harness/scripts/eval_judge.py \
  --skill security-audit --dataset datasets/synthetic/security-audit/shard_000.json

# Run the multi-agent debate engine
python skills/agent-orchestrator/scripts/debate_engine.py \
  --topic "AI safety in healthcare" --rounds 3

# Start overnight evolution (runs in background)
python skill-organism/enterprise_runner.py --overnight --generations 10
```

### 3. Python API

```python
from cortex.synthetic.reasoning_generator import ReasoningGenerator
from cortex.evaluation.judge import LLMJudge
from cortex.agents.orchestrator import AgentOrchestrator

# Generate evaluation prompts
gen = ReasoningGenerator(seed=42)
prompts = gen.generate(100)

# Run multi-agent research pipeline
orchestrator = AgentOrchestrator(provider)
result = orchestrator.run("Analyze the impact of transformer architectures on NLP")

# Evaluate output quality
judge = LLMJudge(provider)
score = judge.score(prompt="...", response=result.final_output)
print(f"Quality: {score.normalized:.0%}")  # e.g., Quality: 87%
```

## Cortex in the intelligence ecosystem

| Layer | Component | What it does | Integration |
|-------|-----------|-------------|-------------|
| **5. Simulation** | MiroFish-inspired scenario simulator | Swarm-based what-if analysis with counterfactual injection | `skills/scenario-simulator/` |
| **4. Intelligence** | BettaFish-inspired analysis engine | Multi-source intelligence queries, forum analysis, multimodal | `skills/intelligence-query/`, `skills/forum-intelligence/`, `skills/multimodal-analyst/` |
| **3. Data** | MindSpider connector | Live topic feeds from social listening deployments | `skills/mindspider-connector/` |
| **2. Evolution** | Skill Organism + ARENA.md | Autonomous overnight evolution with fitness tracking | `skill-organism/`, `skills/*/ARENA.md` |
| **1. Foundation** | 21 core skills + evaluation lab | Research, security, MLOps, orchestration, quality | `skills/`, `cortex/` |

## Skills (26)

| Skill | Category | Description |
|-------|----------|-------------|
| `agent-orchestrator` | Agents | Multi-agent coordination with DAG task graphs |
| `agent-output-validator` | Validation | Automated validation of agent outputs against quality gates |
| `code-review-engine` | Engineering | Automated code review with security checks |
| `context-engineer` | Engineering | Context window optimization and prompt management |
| `de-slop` | Quality | AI-generated writing pattern detection and removal |
| `design-system-forge` | Design | Design system generation and component library scaffolding |
| `dev-lifecycle-engine` | DevOps | Development lifecycle management |
| `diff-generator` | Engineering | Structured diff generation for code and document changes |
| `forum-intelligence` | Intelligence | Forum thread analysis with coordination detection |
| `github-mcp` | Integration | GitHub API via Model Context Protocol |
| `intelligence-query` | Intelligence | Multi-source intelligence analysis engine |
| `meta-skill-evolver` | Meta | Evolutionary skill improvement and mutation engine |
| `mindspider-connector` | Data | Live social listening feed connector |
| `mlops-standards` | MLOps | ML operations best practices enforcement |
| `multimodal-analyst` | Intelligence | Cross-modal content analysis (text + image + video) |
| `persistent-memory` | Infrastructure | SQLite-backed memory with FTS5 search |
| `pre-package-pipeline` | Packaging | Skill validation and packaging pipeline |
| `prompt-architect` | Engineering | Prompt engineering and optimization |
| `repo-publisher` | DevOps | Pre-publish pipeline with security scanning |
| `research-workflow` | Research | Experiment design and methodology |
| `scenario-simulator` | Simulation | MiroFish-inspired swarm scenario simulation |
| `security-audit` | Security | Bandit + semgrep + secret scanning pipeline |
| `session-memory` | Infrastructure | Session-scoped memory persistence |
| `skill-test-harness` | Testing | Automated skill testing framework with LLM-as-Judge |
| `skill-validator` | Validation | Skill structure and manifest validation |
| `tdd-enforcer` | Testing | Test-driven development enforcement |

See [AGENTS.md](AGENTS.md) for the full agent manifest with platform-specific integration guides.

## Cortex Python Framework

| Module | Purpose |
|--------|---------|
| `cortex.synthetic` | Synthetic data generation (reasoning, research, strategy, domain, adversarial) |
| `cortex.evaluation` | LLM-as-Judge scoring, benchmark suites, regression detection |
| `cortex.agents` | Multi-agent orchestrator, debate arena, DAG task graphs |
| `cortex.models` | Model provider abstraction (Anthropic SDK + CLI fallback) |
| `cortex.telemetry` | Structured logging, SQLite metrics collector |
| `cortex.config` | YAML + env var configuration with thread-safe singleton |
| `cortex.utils` | Atomic I/O, input sanitization, prompt injection detection |
| `cortex.experiments` | Experiment tracking with comparison and best-run queries |

## Skill Organism

The `skill-organism/` directory contains the evolution engine. Skills are automatically tested and scored. Underperformers get modified via mutation, top performers get replicated via crossbreeding, and the system recovers from population loss by restoring previously successful versions.

Key features:
- **ARENA.md** per skill — the "program.md" from Karpathy's autoresearch pattern
- **ArenaConfig** parser with trilogy integration fields
- **EvalBudget** context manager for time-bounded evaluation
- **Git-per-experiment** branching (branch, mutate, evaluate, merge or discard)
- **Overnight runner** with `asyncio.Semaphore(4)` parallel generations
- **Crash-safe JSONL** evolution log for dashboard consumption

See [OVERNIGHT_USAGE.md](OVERNIGHT_USAGE.md) for autonomous evolution setup.

## Cross-Platform Support

| Platform | Adapter Type | Status |
|----------|-------------|--------|
| Claude Code | Native Skills | Primary |
| MCP (Model Context Protocol) | FastMCP Servers | Generated |
| LangChain | Tool Classes | Generated |
| CrewAI | Tool Wrappers | Generated |
| OpenAI GPT Actions | Action Schemas | Generated |
| VS Code / Copilot / Cursor / Windsurf / JetBrains | MCP via Extension | Compatible |

## Project Structure

```
cortex-research-suite/
├── cortex/                    # Python framework (pip install -e .)
├── skills/                    # 26 autonomous skills (SKILL.md + ARENA.md + scripts/)
├── skill-organism/            # Skill evolution engine
├── knowledge/                 # Knowledge store (FTS5 + GraphRAG)
├── experiments/               # Experiment tracker (SQLite)
├── datasets/                  # Synthetic datasets + MindSpider feed
├── benchmarks/                # Baselines for all skills
├── dashboards/                # Browser dashboards (evolution, benchmark, arena)
├── cross-platform/            # Generated adapters (MCP, LangChain, CrewAI, OpenAI)
├── packages/                  # Standalone packages (de-slop-cli)
├── docs/                      # Documentation site (GitHub Pages)
├── scripts/                   # CLI entry points and utilities
├── tests/                     # Test suite
└── .github/workflows/         # CI/CD (lint, test, security, eval, release)
```

## Security

All code passes automated security scanning on every push:

- Bandit Python SAST with zero HIGH/MEDIUM findings
- CodeQL semantic code analysis
- Secret scanning with push protection enabled
- Dependabot automated dependency updates
- Prompt injection detection (7 compiled regex patterns)
- Path traversal protection across all I/O operations
- Browser arena: CSP, sessionStorage key isolation, rate limiting, input sanitization

Report vulnerabilities to admin@techknowmad.ai. See [SECURITY.md](SECURITY.md).

## Legal

Cortex Research Suite is MIT licensed. Trilogy integration skills are inspired by the architectural patterns of MindSpider, BettaFish, and MiroFish. No code has been copied. See [LEGAL_NOTES.md](LEGAL_NOTES.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide including how to add new skills. All PRs require:

- Passing CI checks (bandit, lint, tests)
- One approving review
- No leaked secrets or credentials

## License

MIT — see [LICENSE](LICENSE).
