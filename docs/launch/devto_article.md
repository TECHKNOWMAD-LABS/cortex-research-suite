---
title: "Building Self-Evolving Research Skills: Inside the Cortex Research Suite Architecture"
published: true
tags: python, ai, opensource, machinelearning
---

# Building Self-Evolving Research Skills: Inside the Cortex Research Suite Architecture

Most AI agent frameworks treat skills as static artifacts. You write a prompt, test it, ship it, and revisit it when something breaks. But research is not static. Sources change. Domains shift. The competitive intelligence skill you tuned last month is silently degrading today.

We built Cortex Research Suite to address this. It is a Python framework with 26 research skills that autonomously evolve through a competition-based arena system. The core insight comes from Karpathy's autoresearch pattern: treat skills as organisms, let them compete, and let the best variants survive.

The project is open source under MIT license, built by TECHKNOWMAD LABS.

GitHub: [https://github.com/TECHKNOWMAD-LABS/cortex-research-suite](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite)

## The 5-Layer Stack

The architecture is organized into five layers, each building on the one below.

### Layer 1: Foundation -- Core Skills and Evaluation Lab

The base layer provides 26 research skills covering specific workflows: systematic literature review, patent landscape analysis, competitive intelligence, PESTEL analysis, technology readiness assessment, stakeholder mapping, and more.

Every skill execution passes through an evaluation lab that scores outputs on three dimensions: accuracy, depth, and relevance. These scores are deterministic and produce JSON traces that can be diffed like code.

```python
from cortex.skills import LiteratureReview
from cortex.eval import EvaluationLab

skill = LiteratureReview(domain="transformer architectures")
result = skill.execute(query="attention mechanism alternatives 2025")

lab = EvaluationLab()
score = lab.evaluate(result)
# score.accuracy: 0.82
# score.depth: 0.75
# score.relevance: 0.91
# score.trace_id: "eval-2026-03-16-001"
```

The evaluation lab is the critical piece. Without deterministic scoring, evolution is just random mutation. With it, you have a fitness function.

### Layer 2: Evolution -- The Skill Organism and ARENA.md

This is where it gets interesting. Each skill is treated as a living entity with a genome that includes its prompt template, tool chain configuration, evaluation criteria, and mutation rules. The ARENA.md file defines competition parameters.

```yaml
# ARENA.md configuration
arena:
  rounds: 10
  population_size: 8
  mutation_rate: 0.15
  crossover: true
  selection: tournament
  fitness_weights:
    accuracy: 0.4
    depth: 0.35
    relevance: 0.25
  pruning_threshold: 0.3
```

When you start an evolution run, the system forks the skill into variants, applies mutations (prompt rewording, tool chain reordering, parameter adjustments), and runs each variant against the same evaluation dataset. After each round, the bottom performers are pruned and the top performers reproduce.

```python
from cortex.evolution import SkillOrganism, Arena

organism = SkillOrganism(base_skill="literature_review")
arena = Arena.from_config("ARENA.md")

# This runs asynchronously -- start it before you sleep
evolution_run = arena.evolve(organism, generations=50)

# Next morning
best_variant = evolution_run.champion()
print(f"Improvement: {best_variant.fitness_delta:+.2%}")
```

A typical overnight run of 50 generations yields a 10-25% improvement in composite fitness score, depending on the skill and domain.

### Layer 3: Data -- MindSpider Connector

Research skills are only as good as their data. MindSpider is the connector layer that provides live data ingestion from APIs, RSS feeds, and web sources. All data is normalized into a common schema so skills can operate on fresh information without worrying about source-specific formatting.

```python
from cortex.data import MindSpider

spider = MindSpider()
spider.add_source("arxiv", query="LLM evaluation", refresh_hours=6)
spider.add_source("rss", url="https://example.com/feed.xml")
spider.add_source("api", endpoint="https://api.example.com/papers")

# Skills automatically pull from MindSpider
skill = LiteratureReview(data_source=spider)
```

### Layer 4: Intelligence -- Multi-Source Analysis

Single-source research is fragile. Layer 4 implements multi-source cross-referencing inspired by the BettaFish pattern: every finding is verified against independent sources, contradictions are flagged, and the final synthesis includes confidence weights.

```python
from cortex.intelligence import MultiSourceAnalyzer

analyzer = MultiSourceAnalyzer(sources=["arxiv", "patents", "news"])
synthesis = analyzer.analyze("quantum computing error correction")

for finding in synthesis.findings:
    print(f"[confidence: {finding.confidence:.2f}] {finding.summary}")
    if finding.contradictions:
        print(f"  Contradicted by: {finding.contradictions}")
```

This layer is particularly useful for competitive intelligence and technology assessment, where single-source bias can lead to expensive mistakes.

### Layer 5: Simulation -- Swarm Scenario Modeling

The top layer implements swarm-based scenario simulation inspired by the MiroFish pattern. Given a research hypothesis, it spins up agent swarms that model three scenarios: adversarial (actively trying to disprove), optimistic (seeking confirming evidence), and baseline (neutral assessment).

```python
from cortex.simulation import SwarmSimulator

sim = SwarmSimulator(hypothesis="Transformer alternatives will capture 30% of production deployments by 2027")
scenarios = sim.run(swarm_size=5, rounds=20)

print(scenarios.adversarial.conclusion)
print(scenarios.optimistic.conclusion)
print(scenarios.baseline.conclusion)
print(f"Consensus probability: {scenarios.consensus_probability:.2%}")
```

The disagreement between swarms is the signal. When adversarial and optimistic swarms converge, the finding is robust. When they diverge sharply, you know where the uncertainty lives.

## Integration via MCP Adapters

Cortex Research Suite works natively with Claude Code. Individual skills are exposed as commands. But we also built MCP (Model Context Protocol) adapters for cross-framework compatibility:

- **LangChain**: Skills become LangChain tools with proper schema definitions
- **CrewAI**: Skills become agent capabilities with role-appropriate descriptions
- **OpenAI**: Skills map to function calling definitions

This means you can adopt individual skills incrementally without committing to the full stack.

## Running It

```bash
pip install cortex-research-suite

# Run a single skill
cortex run literature_review --query "attention mechanisms" --domain "NLP"

# Start an evolution run
cortex evolve literature_review --generations 50 --arena ARENA.md

# Launch the evaluation dashboard
cortex dashboard --port 8080
```

## What We Learned

Three things surprised us during development:

1. **Prompt mutation is less important than tool chain mutation.** Changing which tools a skill uses and in what order yields bigger fitness improvements than prompt rewording alone.

2. **Tournament selection outperforms simple truncation.** Allowing weaker variants to occasionally survive maintains diversity and prevents premature convergence.

3. **Evaluation function design is the real bottleneck.** The arena is only as good as its fitness function. We spent more time on evaluation criteria than on the evolution mechanics.

## Get Involved

The project is MIT licensed and we are actively looking for contributors, especially on evaluation function design and domain-specific skill templates.

GitHub: [https://github.com/TECHKNOWMAD-LABS/cortex-research-suite](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite)

Built by TECHKNOWMAD LABS — DPIIT registered startup, NVIDIA Inception Program member, Zoho for Startups partner. India.
