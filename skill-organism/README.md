# Skill Organism - Continuous Evolution Engine for Claude Code Skills

A Python-based evolutionary system that treats Claude Code skills as living organisms in a dynamic ecosystem. Skills evolve, reproduce, mutate, and compete for resources based on real performance telemetry.

## Overview

The Skill Organism is a production-ready framework that applies evolutionary biology principles to AI skill management:

- **Living Skills**: Each skill is a living entity with DNA (SKILL.md content), fitness scores, and a generational history
- **Continuous Evolution**: Automated cycles observe health, mutate successful variants, breed high-performers, and cull the weak
- **Fitness-Based Selection**: Natural selection driven by real telemetry (success rate, latency, user satisfaction)
- **Reproduction**: Top-performing skills can breed to create hybrid offspring combining their best traits
- **Self-Healing**: Degraded skills are flagged for recovery before they fail completely

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Skill Organism Ecosystem                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐  │
│  │ skill_registry  │  │ skill_telemetry  │  │ evolution  │  │
│  │    (JSON)       │  │     (SQLite)     │  │  (JSONL)   │  │
│  └────────┬────────┘  └────────┬─────────┘  └──────┬─────┘  │
│           │                    │                   │         │
│           └────────┬───────────┴───────┬───────────┘         │
│                    │                   │                     │
│                ┌───▼──────────────────▼──┐                   │
│                │   SkillOrganism Core    │                   │
│                │   (Evolution Engine)    │                   │
│                └──────────────────────────┘                   │
│                 │     │      │      │      │                 │
│            OBSERVE MUTATE SELECT BREED HEAL                  │
│                 │     │      │      │      │                 │
│                ┌┴─────┴──────┴──────┴──────┴┐                │
│                │  Cycle Runner               │                │
│                │  (evolution_cycle.py)      │                │
│                └────────────────────────────┘                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. `skill_registry.json`
Persistent skill catalog with metadata for all 24 unique TechKnowmad AI skills.

**Structure:**
```json
{
  "ecosystem": {
    "name": "TechKnowmad AI Skill Organism",
    "version": "1.0.0",
    "carrying_capacity": 200,
    "evolution_interval_hours": 24,
    "fitness_threshold": 0.6,
    "auto_deploy_threshold": 0.8
  },
  "skills": [
    {
      "id": "tkm-skill-name",
      "name": "Skill Name",
      "version": "1.0.0",
      "status": "active",
      "fitness_score": 0.85,
      "generation": 1,
      "parent_skill": null,
      "mutation_count": 0
    }
  ]
}
```

### 2. `telemetry.py` (~200 lines)
SQLite-backed telemetry tracking system.

**Key Classes:**
- `SkillTelemetry`: Main telemetry engine
- `SkillMetrics`: Aggregated performance metrics

**Key Methods:**
- `record_invocation()`: Log skill usage with performance data
- `get_skill_metrics(skill_id, period_days=7)`: Get aggregated metrics
- `get_ecosystem_health()`: Overall health dashboard
- `detect_anomalies()`: Statistical anomaly detection (2σ rule)
- `get_fitness_scores()`: Ranked list by composite fitness

### 3. `skill_dna.py` (~150 lines)
Skill genetic material representation and manipulation.

**Key Classes:**
- `SkillDNA`: Structured representation of SKILL.md content

**Key Functions:**
- `crossover(skill_a, skill_b)`: Genetic crossover producing hybrid
- `mutate(skill, mutation_rate=0.1)`: Generate improved variant
- `similarity(skill_a, skill_b)`: Compute genetic similarity (0-1)

### 4. `organism.py` (~460 lines)
Core evolution engine managing the full skill lifecycle.

**Key Class:** `SkillOrganism`

**Key Methods:**

#### `observe()` → Dict
Scan skill health, detect performance patterns, compute anomalies.
- Pulls telemetry for each skill
- Updates health status from metrics
- Flags anomalies (2σ deviations)

#### `mutate(mutation_rate=0.15)` → List[str]
Generate improved skill variants based on performance.
- Mutates top 5 performers
- Creates new version with incremented patch version
- Sets initial fitness slightly above parent

#### `select()` → Dict
Fitness scoring and natural selection. Cull low performers.
- Deprecated skills with fitness < threshold
- Promotes high-fitness skills (> auto_deploy_threshold)
- Protects recently-used skills from culling

#### `reproduce()` → List[str]
Create offspring from high-performing pairs.
- Breeds top 10 performers randomly
- Hybrid combines tools, triggers, and traits from parents
- Offspring inherits enhanced generation number

#### `heal()` → Dict
Detect degraded skills and trigger recovery.
- Flags critical health skills
- Increments mutation count (for retry with mutations)
- Logs for manual intervention

#### `evolve()` → Dict
Run one complete evolution cycle (observe → mutate → select → reproduce → heal).
- Executes all stages sequentially
- Saves updated registry
- Logs cycle to JSONL file
- Returns comprehensive report

#### `report()` → Dict
Generate ecosystem health dashboard.
- Ecosystem statistics (total, active, avg generation)
- Health metrics (healthy, degraded, critical counts)
- Top performers ranked by fitness
- At-risk skills requiring attention
- Category breakdowns

### 5. `evolution_cycle.py` (~200 lines)
Standalone CLI runner for manual or scheduled execution.

**CLI Arguments:**
```bash
python evolution_cycle.py \
  --registry path/to/skill_registry.json \
  --db path/to/skill_telemetry.db \
  --log-dir path/to/logs \
  --dry-run          # Don't save changes
  --verbose          # Debug logging
  --force            # Run regardless of conditions
  --output-report path/to/report.md
```

## How It Works

### Fitness Scoring

Composite fitness = 40% success_rate + 40% avg_satisfaction + 20% invocation_frequency

- **Success Rate**: Proportion of successful executions
- **Satisfaction**: User-provided rating (0-1)
- **Invocation Frequency**: Normalized usage count

### Natural Selection

1. **Culling**: Skills with fitness < 0.6 and usage_count < 5 are deprecated
2. **Promotion**: Skills with fitness > 0.8 are auto-deployed
3. **Protection**: Recent skills protected even if fitness is low

### Reproduction

- Top 10 performers randomly breed in pairs
- Offspring inherits:
  - Combined tool sets
  - Merged triggers
  - Hybrid role description
  - Both parents' dependencies
  - Next generation number

### Mutation

- Top 5 performers create mutant variants
- Mutations include:
  - Improved instructions with better practices
  - New triggers from evolution events
  - Enhanced error handling
  - Fitness bonus (+0.05)

### Health Detection

Health status by success rate + satisfaction:
- **Excellent**: Success ≥95%, Satisfaction ≥80%
- **Healthy**: Success ≥85%, Satisfaction ≥70%
- **Degraded**: Success ≥70%, Satisfaction ≥50%
- **Critical**: Below degraded thresholds

## Running the System

### Manual Execution

```bash
python evolution_cycle.py \
  --registry skill_registry.json \
  --db skill_telemetry.db \
  --verbose
```

### Scheduled Execution (Cron)

Add to crontab to run daily at 2 AM:

```bash
0 2 * * * cd /path/to/skill-organism && python evolution_cycle.py >> evolution.log 2>&1
```

### Scheduled Execution (Claude Scheduled Tasks)

Use Claude's scheduled task system to run at specified intervals:

```python
from scheduled_tasks import create_scheduled_task

create_scheduled_task(
    taskId="skill-organism-evolution",
    description="Run Skill Organism evolution cycle",
    cronExpression="0 2 * * *",  # Daily at 2 AM
    prompt="Run the skill organism evolution cycle at /path/to/skill-organism/evolution_cycle.py"
)
```

### Dry Run (Test)

```bash
python evolution_cycle.py --dry-run --verbose
```

## Telemetry Integration

Record skill invocations (called from your skill execution framework):

```python
from telemetry import SkillTelemetry

telemetry = SkillTelemetry()

# After executing a skill
telemetry.record_invocation(
    skill_id="tkm-research-commander",
    duration_ms=2150.5,
    success=True,
    tokens_used=4200,
    user_satisfaction=0.9,  # 0-1 scale
)
```

## Output Files

### `skill_registry.json`
Updated registry after each evolution cycle. Tracks:
- Fitness scores
- Health status
- Generation numbers
- Mutation counts
- Parent-child relationships

### `skill_telemetry.db`
SQLite database with invocation history:
- Timestamps
- Latency measurements
- Success/failure status
- Token usage
- Error logs
- User satisfaction ratings

### `evolution_log.jsonl`
One JSON object per line, one per evolution cycle:
```json
{
  "cycle_timestamp": "2026-03-15T14:30:00",
  "stage_results": {
    "observe": {"total_skills": 24, "anomalies_detected": 2},
    "mutate": {"mutants_created": 2, "mutant_ids": ["..."]},
    ...
  },
  "cycle_duration_seconds": 8.4
}
```

### `evolution_report.md`
Human-readable markdown report with:
- Ecosystem overview
- Health status
- Evolution cycle results by stage
- Top performers
- At-risk skills
- Category statistics

### `organism.log`
Structured logs from the evolution engine:
```
2026-03-15 14:30:12 - organism - INFO - === Evolution Cycle: OBSERVE ===
2026-03-15 14:30:12 - organism - INFO - Observed 24 skills
2026-03-15 14:30:13 - organism - INFO - Created 2 mutants
...
```

## Categories (24 Skills)

| Category | Skills | Purpose |
|----------|--------|---------|
| **Research** (6) | Research Commander, Research Workflow, Multi-Agent Research Swarm, Academic Output Pipeline, Patent Researcher, IP-Aware Competitive Intelligence | Information discovery and analysis |
| **MLOps** (4) | MLOps Standards, Zero-Touch ML Pipeline, Model Evaluator, Cost Optimizer | Machine learning operations |
| **Agents** (4) | Swarm Commander, Agent Debugger, Self-Healing Agent, Antifragile AI Ops | Multi-agent orchestration |
| **Meta** (5) | Skill Factory, Self-Evolving Skill Ecosystem, Knowledge Distiller, Prompt Evolution, Pareto Prompt Optimizer | Framework and evolution |
| **Security** (2) | Red Team AI Models, Compliance as Code | Safety and compliance |
| **Prompting** (1) | Prompt Architect | Prompt engineering |
| **Creative** (1) | Startup Creative Automation | Creative tasks |
| **Other** (1) | All remaining | Support functions |

## Design Principles

1. **Production-Ready**: Type hints, docstrings, error handling throughout
2. **Zero External Dependencies**: Uses only Python stdlib (sqlite3, json, logging, etc.)
3. **Minimal**: ~1000 lines total, clear separation of concerns
4. **Observable**: Comprehensive logging, telemetry, reports
5. **Evolutionary**: Real natural selection based on fitness metrics
6. **Autonomous**: Runs without manual intervention, self-healing capabilities

## Requirements

- Python 3.9+
- No external dependencies (stdlib only)
- Write access to registry and telemetry files
- Cron or scheduled task runner (optional, for automation)

## Future Enhancements

- **Skill Specialization**: Breed skills for specific use cases
- **Gene Pool Isolation**: Separate evolution tracks for different categories
- **Extinction Events**: Planned disruption to clear stagnant genes
- **Neural Architecture Search**: Optimize skill composition automatically
- **Competitive Tournaments**: Rank-based selection from structured competitions
- **Skill Migration**: Cross-ecosystem skill transfers
- **Niche Filling**: Auto-detect gaps in skill coverage

---

**Version**: 1.0.0  
**Created**: 2026-03-15  
**Author**: TechKnowmad AI Skill Organism