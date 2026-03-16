# Skill Registry

Complete registry of all 26 skills in the Cortex Research Suite, including trilogy integration status.

## Skills

| Skill | Category | Trilogy | Description |
|-------|----------|---------|-------------|
| `arxiv-researcher` | Research | MindSpider | Searches and summarizes arXiv papers with semantic relevance ranking |
| `code-reviewer` | Development | BettaFish | Automated code review with style, correctness, and security checks |
| `data-pipeline` | Data | MiroFish | Builds and validates ETL pipelines for research datasets |
| `deep-search` | Research | MindSpider | Multi-source deep web search with result synthesis |
| `diff-generator` | Development | BettaFish | Generates structured diffs across files, notebooks, and repos |
| `doc-writer` | Documentation | MindSpider | Auto-generates documentation from code and annotations |
| `eval-harness` | Evaluation | MiroFish | LLM evaluation harness with configurable benchmarks |
| `experiment-tracker` | Research | MiroFish | Tracks ML experiments, hyperparameters, and results |
| `few-shot-builder` | Prompting | BettaFish | Constructs optimized few-shot prompt templates |
| `git-historian` | Development | MindSpider | Analyzes git history for patterns, contributors, and trends |
| `hypothesis-gen` | Research | MindSpider | Generates testable hypotheses from literature and data |
| `jupyter-runner` | Development | BettaFish | Executes and validates Jupyter notebooks programmatically |
| `knowledge-graph` | Research | MindSpider | Builds knowledge graphs from unstructured text sources |
| `lit-review` | Research | MindSpider | Conducts systematic literature reviews with citation mapping |
| `metric-dashboard` | Evaluation | MiroFish | Real-time metrics dashboard for model performance |
| `model-compare` | Evaluation | BettaFish | Side-by-side LLM comparison with statistical significance tests |
| `paper-replicator` | Research | MiroFish | Replicates methodology from published papers |
| `prompt-optimizer` | Prompting | BettaFish | Iteratively optimizes prompts using evaluation feedback |
| `rag-builder` | Development | BettaFish | Builds retrieval-augmented generation pipelines |
| `report-gen` | Documentation | MindSpider | Generates formatted research reports from structured data |
| `security-audit` | Security | BettaFish | Scans code for security vulnerabilities and LLM-specific risks |
| `stat-analyzer` | Data | MiroFish | Statistical analysis toolkit for research data |
| `survey-builder` | Research | MindSpider | Builds research surveys from topic ontologies |
| `tdd-enforcer` | Development | BettaFish | Enforces test-driven development with mutation testing |
| `toolkit-scanner` | DevOps | MiroFish | Scans and audits project dependencies and toolchains |
| `viz-generator` | Data | MiroFish | Generates publication-quality visualizations from data |

## Trilogy Integration

The Cortex Research Suite integrates with the ARENA trilogy: **MindSpider**, **BettaFish**, and **MiroFish**. Each skill is aligned with one trilogy engine based on its primary function.

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

  eval-harness:
    mindspider_feed_enabled: false
    bettafish_engine_type: null
    mirofish_simulation_enabled: true
```
