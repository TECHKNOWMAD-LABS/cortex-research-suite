# Cortex Research Suite

[![CI](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/ci.yml)
[![Evaluation Pipeline](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/eval.yml/badge.svg)](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/eval.yml)
[![Security Scan](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/security.yml/badge.svg)](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/actions/workflows/security.yml)
[![Python 3.10-3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Skills: 27](https://img.shields.io/badge/skills-27-blueviolet.svg)](skills/)
[![NVIDIA Inception](https://img.shields.io/badge/NVIDIA-Inception%20Program-76b900.svg)](https://www.nvidia.com/en-us/startups/)
[![Zoho for Startups](https://img.shields.io/badge/Zoho-Startup%20Partner-e42527.svg)](https://www.zoho.com/startups/)
[![DPIIT Registered](https://img.shields.io/badge/DPIIT-Registered%20Startup-ff9933.svg)](https://www.startupindia.gov.in/)

**AI Research Operating System** — 27 self-evolving research skills built on [Karpathy's autoresearch pattern](https://github.com/karpathy/autoresearchgpt). Each skill has an ARENA.md (the "program.md" equivalent) that drives autonomous evolution through LLM-as-Judge evaluation. The Skill Organism engine runs genetic selection — skills compete, mutate, and reproduce. Includes trilogy integration (MindSpider social listening, intelligence analysis, scenario simulation), browser-based experiment arena, and cross-platform adapters for Claude Code, MCP, LangChain, CrewAI, and OpenAI.

## Installation

### Full suite (recommended)

```bash
git clone https://github.com/TECHKNOWMAD-LABS/cortex-research-suite.git
cd cortex-research-suite
pip install -e ".[dev]"
```

This gives you all 27 skills, Skill Organism evolution engine, dashboards, knowledge store (GraphRAG), datasets, and CLI scripts.

### Core framework only

```bash
pip install cortex-research-suite
```

> **Note:** `pip install` delivers only the `cortex/` Python package (synthetic data, evaluation, agents, models). For all 27 skills, Skill Organism, dashboards, and knowledge store, use `git clone`.

## Quickstart — 3 entry points

### 1. Petri Dish (zero install)

Open `dashboards/petri-dish.html` in any browser. Press **EVOLVE**. Watch 27 AI skills compete, mutate, and evolve as living organisms across 10,000 generations — with generative audio, god mode, and Claude Judge integration.

### 2. Browser Arena

Open `dashboards/skill_arena_demo.html` in any browser. Paste your Anthropic API key. Pick a skill. Click **Run Experiment**. Watch the organism evolve in real time.

### 3. Terminal

```bash

# Run the test suite
pytest

# Generate evaluation datasets for all 27 skills
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
| **1. Foundation** | 27 core skills + evaluation lab | Research, security, MLOps, orchestration, quality | `skills/`, `cortex/` |

## Live Mode (optional)

Install with live web intelligence support:

```bash
pip install -e ".[live]"
```

This enables Scrapling-powered web scraping for real-time social signals, academic evidence, and forum analysis. Skills that support live mode:

- `mindspider-connector` — `--source scrapling` for live Reddit/HN/Bluesky topic feeds
- `research-workflow` — `--live-evidence` for real-time Scholar/PubMed/arXiv citations
- `web-intelligence` — full live web intelligence sweeps
- `forum-intelligence` — live forum thread scraping

All skills work fully offline without Scrapling installed — live mode is additive.

## Dashboard Server (optional)

```bash
pip install uvicorn
python scripts/serve_dashboard.py --port 3117
```

SSE-powered live dashboard showing evolution progress, skill fitness, and generation deltas. Connects to `skill-organism/evolution_log.jsonl` and streams updates in real time.

## Skills (27)

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
| `web-intelligence` | Intelligence | Live web scraping with Scrapling — social signals, academic evidence, forum analysis |

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
├── skills/                    # 27 autonomous skills (SKILL.md + ARENA.md + scripts/)
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

## Architecture Notes

### Instruction-only skills

3 skills have no `scripts/` directory — they are Claude Code instruction files read directly from SKILL.md:
- `repo-publisher` — pre-publish pipeline checklist
- `prompt-architect` — prompt engineering patterns and guidelines
- `mlops-standards` — ML operations best practices reference

### Two dataset generators

| Generator | Path | Purpose |
|-----------|------|---------|
| Category-based | `scripts/generate_dataset.py` | Generates prompts by category (reasoning, strategy, healthcare, adversarial) for the cortex evaluation framework |
| Per-skill | `datasets/generators/skill_dataset_generator.py` | Generates 50 prompts per skill (27 skills, 10% adversarial) for skill evolution and arena testing |

### Two research pipelines

| Pipeline | Path | Usage |
|----------|------|-------|
| Cortex package | `scripts/run_research.py` | Positional topic arg, `--mock` for offline mode |
| Standalone skill | `skills/research-workflow/scripts/research_pipeline.py` | `--topic` flag, works offline automatically with hardcoded evidence |

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
