# Show HN: Cortex Research Suite -- 26 self-evolving research skills with an autoresearch pattern

**GitHub:** https://github.com/TECHKNOWMAD-LABS/cortex-research-suite

We built a Python framework where research skills don't just run -- they evolve. The core idea draws from Karpathy's autoresearch pattern: skills compete in an evaluation arena, mutate based on results, and the best variants survive. You leave it running overnight; by morning, your research pipeline is measurably better.

## The Architecture: A 5-Layer Stack

**Layer 1 -- Foundation.** 26 core skills (literature review, patent analysis, competitive intelligence, etc.) plus an evaluation lab that scores every skill output on accuracy, depth, and relevance.

**Layer 2 -- Evolution.** The Skill Organism. Skills are treated as living entities with an ARENA.md configuration that defines competition rules. Skills fork, mutate their prompts and parameters, compete head-to-head, and the losers get pruned. This is the autoresearch loop.

**Layer 3 -- Data.** MindSpider, a connector layer for live social listening. Pulls from APIs, RSS, and web sources so skills operate on fresh data rather than stale corpora.

**Layer 4 -- Intelligence.** Multi-source analysis inspired by the BettaFish pattern. Cross-references findings across sources, detects contradictions, and produces confidence-weighted synthesis.

**Layer 5 -- Simulation.** Swarm scenario simulation inspired by the MiroFish pattern. Spins up agent swarms that model adversarial, optimistic, and baseline scenarios against your research hypothesis.

## Integration

Works with Claude Code natively. Also supports LangChain, CrewAI, and OpenAI via MCP (Model Context Protocol) adapters. You can plug individual skills into any existing agent pipeline or run the full stack standalone.

## What makes this different from yet another agent framework

- **Skills are the unit of evolution, not prompts.** A skill includes its prompt, its tool chain, its evaluation criteria, and its mutation rules. Evolution operates on all of these simultaneously.
- **The evaluation lab is deterministic and auditable.** Every skill run produces a scored trace. You can diff two skill versions the way you diff code.
- **It is a research tool, not a chatbot wrapper.** The 26 base skills cover specific research workflows: systematic literature review, PESTEL analysis, technology readiness assessment, stakeholder mapping, and more.

## Technical Details

- Python 3.10+
- MIT license
- 26 skills total (26 core skills including 5 trilogy integration skills)
- MCP adapter layer for cross-framework compatibility
- No vendor lock-in -- works with any LLM backend that supports tool use

Built by TECHKNOWMAD LABS. We'd appreciate feedback on the evolution mechanics specifically -- the arena scoring function and the mutation strategy are the parts we're least certain about.
