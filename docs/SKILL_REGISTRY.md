# Skill Registry

Complete registry of all 26 skills in the Cortex Research Suite, including trilogy integration status.

## Skills

| Skill | Category | Trilogy | Description |
|-------|----------|---------|-------------|
| `agent-orchestrator` | Agents | — | Multi-agent orchestration with parallel dispatch, dependency resolution, and DAG task graphs |
| `agent-output-validator` | Validation | — | Verify outputs from parallel agent dispatches against expected contracts |
| `code-review-engine` | Engineering | — | Two-stage code review with spec compliance validation and code quality analysis |
| `context-engineer` | Engineering | — | Token-optimized context management with auto-pruning and relevance scoring |
| `de-slop` | Quality | — | Detect and flag AI-generated writing patterns in markdown and documentation |
| `design-system-forge` | Design | — | AI-powered design system generator with industry-specific rules and anti-pattern detection |
| `dev-lifecycle-engine` | DevOps | — | Autonomous development lifecycle orchestrator for the full pipeline |
| `diff-generator` | Engineering | — | Snapshot files, apply edits, and generate unified diffs for review |
| `forum-intelligence` | Intelligence | BettaFish | Forum thread analysis with coordination detection, sentiment distribution, and minority viewpoint extraction |
| `github-mcp` | Integration | — | Build and deploy a GitHub MCP server for repository management |
| `intelligence-query` | Intelligence | BettaFish | Multi-source intelligence analysis engine with query decomposition and parallel source collection |
| `meta-skill-evolver` | Meta | — | Autonomous skill lifecycle engine that generates, validates, tests, and packages skills |
| `mindspider-connector` | Data | MindSpider | Live social listening feed connector with demo/MySQL modes and parameterized SQL |
| `mlops-standards` | MLOps | — | MLOps best practices enforcement and standards validation |
| `multimodal-analyst` | Intelligence | BettaFish | Cross-modal content analysis for text, image URLs, and video URLs with hallucination warnings |
| `persistent-memory` | Infrastructure | — | Enterprise persistent memory with progressive disclosure retrieval |
| `pre-package-pipeline` | Packaging | — | Single-command pre-flight pipeline before .skill packaging |
| `prompt-architect` | Engineering | — | Prompt engineering and optimization for improved LLM outputs |
| `repo-publisher` | DevOps | — | Pre-publish pipeline for GitHub repositories with security scanning |
| `research-workflow` | Research | — | Experiment design and methodology planning |
| `scenario-simulator` | Simulation | MiroFish | Swarm scenario simulation with counterfactual injection and system-generated personas |
| `security-audit` | Security | — | Automated security scanning with bandit, semgrep, and secret detection |
| `session-memory` | Infrastructure | — | Automatic checkpointing of session state to survive context compaction |
| `skill-test-harness` | Testing | — | Automated test runner for skill scripts with fixtures and assertions |
| `skill-validator` | Validation | — | Pre-flight validation for Claude Code skills before packaging |
| `tdd-enforcer` | Testing | — | Enforces test-driven development with mandatory RED-GREEN-REFACTOR cycles |

## Trilogy Integration

The Cortex Research Suite integrates with the ARENA trilogy: **MindSpider**, **BettaFish**, and **MiroFish**. Each trilogy-integrated skill is aligned with one trilogy engine based on its primary function.

### Trilogy Engines

- **MindSpider** — Knowledge acquisition, web crawling, and information synthesis. Skills that discover, retrieve, and organize information.
- **BettaFish** — Code analysis, generation, and optimization. Skills that work directly with source code, prompts, and development workflows.
- **MiroFish** — Simulation, evaluation, and experimental pipelines. Skills that run experiments, track metrics, and validate results.

## Adding Trilogy Integration to a Skill

To integrate a skill with the ARENA trilogy, configure the following three settings in your skill's section of `ARENA.md`:

### `mindspider_feed_enabled`

Controls whether the skill feeds its output into the MindSpider knowledge graph.

```yaml
mindspider_feed_enabled: true   # Skill outputs are indexed by MindSpider
mindspider_feed_enabled: false  # Skill operates independently
```

Enable this when the skill produces knowledge artifacts (papers, summaries, extracted entities) that should be discoverable by other skills via MindSpider.

### `bettafish_engine_type`

Specifies which BettaFish engine mode the skill uses for code-related operations.

```yaml
bettafish_engine_type: "analysis"    # Read-only code inspection
bettafish_engine_type: "generation"  # Code generation and transformation
bettafish_engine_type: "hybrid"      # Both analysis and generation
bettafish_engine_type: null          # No BettaFish integration
```

Set this based on whether the skill reads code, writes code, or both.

### `mirofish_simulation_enabled`

Enables MiroFish simulation and evaluation pipelines for the skill.

```yaml
mirofish_simulation_enabled: true   # Skill can run simulations and evaluations
mirofish_simulation_enabled: false  # No simulation capabilities
```

Enable this for skills that run experiments, compare outputs, or need statistical evaluation support.

### Example Configuration in ARENA.md

```yaml
skills:
  security-audit:
    mindspider_feed_enabled: true
    bettafish_engine_type: "analysis"
    mirofish_simulation_enabled: false

  scenario-simulator:
    mindspider_feed_enabled: false
    bettafish_engine_type: null
    mirofish_simulation_enabled: true
```
