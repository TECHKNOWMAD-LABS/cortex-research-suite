# Discord Community Post

---

**Title:** Cortex Research Suite -- 26 self-evolving research skills, open source, works with Claude Code + MCP adapters

---

Hey everyone,

We just open-sourced Cortex Research Suite and wanted to share it here since it touches a few things this community cares about: skill evolution, evaluation frameworks, and MCP integration.

**What it is:** A Python framework with 26 research skills (literature review, patent analysis, competitive intelligence, PESTEL, etc.) that can autonomously evolve and improve through a competition-based arena system.

**The interesting part:** Skills are not static. We implemented an autoresearch pattern (inspired by Karpathy's work) where skills fork, mutate their prompts and tool configurations, compete head-to-head in an evaluation arena, and the best variants survive. You can set this running overnight and come back to measurably improved skill performance.

**The 5-layer architecture:**

1. **Foundation** -- 21 core skills + evaluation lab with deterministic scoring
2. **Evolution** -- Skill Organism + ARENA.md competition rules
3. **Data** -- MindSpider connector for live social listening and data ingestion
4. **Intelligence** -- Multi-source cross-referencing with contradiction detection
5. **Simulation** -- Swarm-based scenario modeling (adversarial, optimistic, baseline)

**Integration story:**

This works natively with Claude Code -- skills are exposed as Claude Code commands. But we also built MCP (Model Context Protocol) adapters so you can use individual skills with:

- LangChain (as tools)
- CrewAI (as agent skills)
- OpenAI function calling

Each adapter translates the skill interface to the target framework's expected format. You can mix and match -- use our literature review skill in your existing CrewAI pipeline, or run the full stack standalone.

**Tech specs:**
- Python 3.10+
- MIT license
- No vendor lock-in on the LLM backend
- Evaluation traces are JSON, fully diffable

**What we are looking for:**

Feedback on two things specifically:

1. The arena scoring function -- how we weight accuracy vs. depth vs. relevance
2. The mutation strategy -- how aggressively skills should diverge from their parent

GitHub: https://github.com/TECHKNOWMAD-LABS/cortex-research-suite

Happy to answer questions about the architecture or the evolution mechanics.

---
