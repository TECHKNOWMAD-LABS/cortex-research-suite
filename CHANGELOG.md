# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-03-16

### Added

#### Trilogy Integration (5 new skills, 26 total)
- **mindspider-connector** (#22): Live social listening feed connector with demo/MySQL modes, parameterized SQL, 10s connect timeout, 30s query timeout
- **intelligence-query** (#23): Multi-source intelligence analysis with query decomposition, parallel source collection, and synthesis (BettaFish-inspired)
- **multimodal-analyst** (#24): Cross-modal content analysis for text, image URLs, and video URLs with hallucination warnings (BettaFish-inspired)
- **forum-intelligence** (#25): Forum thread analysis with coordination detection, sentiment distribution, and minority viewpoint extraction (BettaFish-inspired)
- **scenario-simulator** (#26): MiroFish-inspired swarm scenario simulation with counterfactual injection, system-generated personas, and mandatory disclaimers

#### GraphRAG Knowledge Store
- `knowledge/graph_store.py`: Triple-based knowledge graph with JSON persistence (no pickle), regex-based entity extraction, BFS neighbor traversal, optional NetworkX export
- `knowledge/retriever.py`: Updated with `retrieve_with_graph()` combining FTS5 search with graph traversal

#### Enterprise Security Hardening
- Browser Skill Arena: CSP meta tag, sessionStorage-only API key isolation, MAX_AUTO_RUNS=20 rate limit, 8s minimum interval, input sanitization (8000 char truncation, escHtml)
- All BettaFish skills: MAX_INPUT_CHARS=50000 truncation, HTML stripping via stdlib, JSON schema validation, no pickle/eval/exec
- Scenario simulator: 3000 char seed report cap, system-generated personas only, mandatory simulation disclaimers
- GraphRAG: JSON-only persistence, regex-only triple extraction, no eval/exec

#### Documentation & Compliance
- `LEGAL_NOTES.md`: License compatibility audit for MindSpider (Non-Commercial + MIT), BettaFish (GPL-2.0), MiroFish (AGPL-3.0) — all pattern-inspiration only
- `datasets/mindspider/DATA_NOTICE.md`: Data handling policy with GDPR/DPDP Act 2023 awareness
- `SECURITY.md`: 7 new subsections for trilogy skills and browser arena
- `CONTRIBUTING.md`: Skill creation guide with directory structure, ARENA.md setup, eval/evolution commands
- `docs/SKILL_REGISTRY.md`: Full registry of 26 skills with trilogy integration guide
- `docs/launch/`: 7 launch content files (Show HN, X thread, Discord, Dev.to, LinkedIn India, Reddit, demo script)
- `OVERNIGHT_USAGE.md`: Autonomous evolution setup documentation

#### Infrastructure
- `scripts/smoke_test.py`: 12-check end-to-end verification (runs without API key)
- `requirements-lock.txt`: Dependency pinning for reproducible builds
- `scripts/publish.sh`: Build verification and distribution pipeline
- 21 skill documentation pages generated at `docs/skills/`
- Arena snapshot regeneration pipeline

### Changed
- README.md: 7-badge panel, 5-layer ecosystem table, 26-skill catalog, trilogy section
- AGENTS.md: Added Intelligence & Data category with 5 trilogy skills
- `docs/index.html`: Updated with ecosystem table and 26-skill catalog
- `pyproject.toml`: Version bump to 1.1.0, package-data includes for ARENA.md/SKILL.md

## [1.0.0] - 2026-03-15

### Added

#### Core Framework
- Centralized configuration system with YAML loading, environment variable overrides (`CORTEX_` prefix), and thread-safe singleton pattern
- Abstract model provider with Anthropic SDK integration and CLI fallback
- Intelligent model router for task-type-based routing (reasoning, evaluation, extraction, generation)
- Structured JSON logging with rotation (50 MB, 5 backups)
- Thread-safe SQLite metrics collector with recording, querying, aggregation, and retention purge
- Experiment tracker with deterministic IDs, comparison, and best-experiment queries

#### Synthetic Data Engine (Dataset Forge)
- Multi-step reasoning prompt generator (10 templates, 20 topics, 8 premises, 4 hard templates)
- Academic research prompt generator (8 templates, 20 fields, 20 topics)
- Business strategy prompt generator (10 templates, 15 industries, 10 trends, 8 challenges)
- Domain-specific generator for healthcare, finance, technology, and policy verticals
- Adversarial prompt generator for robustness testing (ambiguity, edge cases, contradictions, hallucination triggers)
- Dataset validator with deduplication, length checks, and distribution analysis
- Shard manager for memory-efficient large-scale dataset storage

#### Evaluation Lab
- LLM-as-Judge with structured rubric (accuracy, reasoning, completeness, coherence) and weighted scoring
- Evaluation runner orchestrating skill execution and judging with aggregated reports
- Regression detector comparing scores against stored baselines with configurable tolerance
- Benchmark suites with factory methods for reasoning and strategy domains

#### Multi-Agent Runtime
- Four specialized agents: Researcher, Critic, Strategist, Synthesizer
- Agent orchestrator with sequential pipeline and result tracking
- Multi-round debate arena (capped at 5 rounds) with final synthesis
- DAG-based task graph with topological sort and cycle detection
- Research engine with iterative quality refinement and configurable quality gates

#### 21 Autonomous Skills
- **Code Quality & Security:** security-audit, code-review-engine, de-slop, tdd-enforcer
- **Agent Infrastructure:** agent-orchestrator, agent-output-validator, context-engineer, persistent-memory, session-memory
- **Development Lifecycle:** dev-lifecycle-engine, diff-generator, github-mcp, repo-publisher
- **Research & MLOps:** research-workflow, mlops-standards, prompt-architect
- **Skill Development:** meta-skill-evolver, skill-validator, skill-test-harness, pre-package-pipeline, design-system-forge

#### Cross-Platform Support
- Native Claude Code skill definitions (21 skills)
- MCP (Model Context Protocol) FastMCP server adapters
- LangChain tool class adapters
- CrewAI tool wrapper adapters
- OpenAI GPT Action schema adapters
- AGENTS.md discovery files for each skill
- Universal Skill Manifest format (JSON)

#### Skill Organism (Evolution Engine)
- Autonomous skill evolution: observe, mutate, select, reproduce, heal
- SHA-256 integrity checks on skill registry
- Atomic rollback on failure
- CI/CD-compatible exit codes via enterprise runner

#### Security
- Prompt injection detection (7 compiled regex patterns)
- Path traversal protection across all I/O operations
- Input sanitization at agent base class level
- Atomic file writes (temp file + `os.replace`)
- Subprocess hardening with model name validation
- Sanitized error messages to prevent information leakage
- SQL injection prevention with parameterized queries and type casting
- JSONL size limits to prevent resource exhaustion

#### CI/CD
- GitHub Actions: lint, test (Python 3.10-3.12), skill validation, security scan
- Bandit SAST with zero HIGH/MEDIUM findings
- CodeQL semantic analysis
- Secret scanning with push protection
- Automated release workflow on tag push

#### Testing
- 127 unit and integration tests
- 80%+ code coverage (threshold: 70%)
- Tests for all core modules: agents, config, evaluation, experiments, I/O, metrics, router, security, shard manager, synthetic generators

#### Documentation
- Enterprise setup runbook (13-step configuration guide)
- SECURITY.md with vulnerability reporting policy
- CONTRIBUTING.md with PR requirements
- CODE_OF_CONDUCT.md
- Publish report with full pipeline results

[1.1.0]: https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/releases/tag/v1.0.0
