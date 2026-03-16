# Reddit Post

**Subreddit:** r/MachineLearning or r/LocalLLaMA

---

**Title:** Cortex Research Suite: An open-source framework for self-evolving research skills with a deterministic evaluation arena

---

**Body:**

Sharing a project we have been working on. Cortex Research Suite is a Python framework with 26 research skills (literature review, patent analysis, competitive intelligence, PESTEL, stakeholder mapping, etc.) that can autonomously evolve through a competition-based arena system.

**The core idea:**

Skills are treated as organisms with a genome (prompt template + tool chain + eval criteria + mutation rules). An arena system forks skills into variants, applies mutations, evaluates each variant against the same dataset, and prunes the underperformers. This is an implementation of the autoresearch pattern -- set it running, come back to improved skills.

**What I actually want feedback on:**

The evaluation framework. The arena is only useful if the fitness function is sound. Currently we score on three axes:

- **Accuracy** -- factual correctness against known-good references
- **Depth** -- coverage of the topic space, measured by concept density
- **Relevance** -- alignment with the original query intent

Weights are configurable in ARENA.md. Default is 0.4 / 0.35 / 0.25. We arrived at these empirically but I suspect they are domain-dependent and our calibration is biased toward the domains we tested on (NLP research, patent landscapes, competitive tech analysis).

**Architecture overview (5 layers):**

1. **Foundation** -- 21 core skills + evaluation lab. Every execution produces a scored JSON trace.
2. **Evolution** -- Skill Organism + ARENA.md. Tournament selection, configurable mutation rate, crossover support.
3. **Data** -- MindSpider connector for live data (APIs, RSS, web). Normalized schema.
4. **Intelligence** -- Multi-source analysis with contradiction detection and confidence weighting.
5. **Simulation** -- Swarm scenario modeling. Adversarial, optimistic, and baseline agent swarms test hypotheses from multiple angles.

**What surprised us:**

- Tool chain mutation (changing which tools a skill uses and in what order) yields bigger improvements than prompt mutation alone.
- Tournament selection with occasional weak-variant survival outperforms strict truncation. Diversity maintenance matters.
- The hardest part is not the evolution mechanics. It is designing evaluation functions that do not reward verbose, confident-sounding but shallow outputs.

**Integration:**

Works with Claude Code natively. MCP adapters for LangChain, CrewAI, and OpenAI function calling. Python 3.10+. MIT license.

**Not claiming:**

This is not AGI. This is not a general-purpose agent framework. This is a focused research tool with a specific thesis: that research skills can be treated as evolvable artifacts, and that a well-designed fitness function plus selection pressure produces meaningful improvement over time.

GitHub: https://github.com/TECHKNOWMAD-LABS/cortex-research-suite

Interested in feedback on the evaluation methodology and whether the mutation strategy makes sense to people who have worked on evolutionary optimization.

---
