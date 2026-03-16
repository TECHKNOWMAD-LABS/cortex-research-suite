# Cortex Research Suite -- 5-Minute Demo Script

Total runtime: 5 minutes
Format: Screen recording with narration
Resolution: 1920x1080

---

## Shot 1: Terminal -- Single Skill Execution (0:00 - 0:50)

**Setup:** Terminal open, dark theme, font size 16.

**Narration:**

"Cortex Research Suite is a Python framework with 26 research skills that evolve autonomously. Let me show you what that means in practice."

**Action:**

```bash
# Install (skip in demo if pre-installed, just mention it)
pip install cortex-research-suite

# Run a single literature review skill
cortex run literature_review \
  --query "attention mechanism alternatives to transformers" \
  --domain "NLP" \
  --output results/demo_run.json
```

**Show:** The skill executing, pulling data, producing structured output. Briefly scroll through the JSON output showing the structured findings: sources, summaries, confidence scores.

**Key point to narrate:** "Every skill produces structured, scored output. This is not free-form text generation. Each finding has a source, a confidence score, and a relevance rating."

---

## Shot 2: Evaluation Lab (0:50 - 1:40)

**Action:**

```bash
# Evaluate the skill output
cortex eval results/demo_run.json

# Show the evaluation trace
cortex eval results/demo_run.json --verbose
```

**Show:** The evaluation scores appearing: accuracy, depth, relevance, composite. Then the verbose trace showing how each score was computed.

**Narration:**

"Every execution passes through the evaluation lab. Three axes: accuracy against known references, depth of topic coverage, and relevance to the original query. These scores are deterministic. Run the same evaluation twice, get the same result. The traces are JSON -- you can diff two skill versions the way you diff code."

**Key point:** Show the trace JSON briefly. Emphasize determinism and auditability.

---

## Shot 3: ARENA.md and Evolution Setup (1:40 - 2:30)

**Action:**

```bash
# Show the arena configuration
cat ARENA.md
```

**Show:** The ARENA.md file with competition parameters: rounds, population size, mutation rate, fitness weights, pruning threshold.

**Narration:**

"This is ARENA.md. It defines how skills compete. Population size of 8 means each generation has 8 variants of the skill. Mutation rate of 0.15 means each variant has a 15% chance of diverging on any given parameter. Tournament selection with a pruning threshold of 0.3 -- the bottom 30% get cut each round."

**Action:**

```bash
# Start an evolution run
cortex evolve literature_review \
  --generations 5 \
  --arena ARENA.md \
  --verbose
```

**Show:** The evolution running for 5 generations (use a short run for the demo). Show the generation-by-generation fitness scores improving. Highlight one mutation that improved performance and one that was pruned.

**Key point to narrate:** "In a real run, you would set this to 50 or 100 generations and let it run overnight. For the demo, 5 generations is enough to see the pattern: fitness improves, weak variants die, strong variants reproduce."

---

## Shot 4: Evolution Dashboard (2:30 - 3:30)

**Action:**

```bash
# Launch the dashboard
cortex dashboard --port 8080
```

**Switch to browser.** Navigate to localhost:8080.

**Show:** The evolution dashboard with:

- Fitness curve over generations (line chart showing improvement)
- Population diversity metric (should decrease slightly, then stabilize)
- Mutation log (which parameters changed in each variant)
- Head-to-head comparison between the original skill and the current champion

**Narration:**

"The dashboard gives you visibility into what the evolution is actually doing. This fitness curve shows composite score over generations -- steady improvement with some noise, which is expected. The diversity metric tells you whether the population is converging too fast. If it drops to near zero, you are losing exploration. The mutation log shows exactly what changed -- here you can see a variant that reordered its tool chain and gained 8% on depth."

**Key point:** Click on the head-to-head comparison. Show the original skill output and the evolved skill output side by side on the same query. Highlight the concrete improvement.

---

## Shot 5: Multi-Source Intelligence (3:30 - 4:10)

**Switch back to terminal.**

**Action:**

```bash
# Run multi-source analysis
cortex analyze \
  --query "quantum computing error correction progress" \
  --sources arxiv,patents,news \
  --output results/multi_source.json
```

**Show:** The multi-source analyzer pulling from three sources, cross-referencing findings, flagging one contradiction.

**Narration:**

"Layer 4 is multi-source intelligence. Here we are analyzing quantum computing error correction across three sources: arxiv papers, patent filings, and news. The analyzer cross-references findings automatically. See this flag -- it found a contradiction between a patent claim and a recent paper. The synthesis includes confidence weights so you know which findings are well-supported and which are single-source."

---

## Shot 6: Swarm Simulation (4:10 - 4:40)

**Action:**

```bash
# Run scenario simulation
cortex simulate \
  --hypothesis "Transformer alternatives will capture 30% of production deployments by 2027" \
  --swarm-size 3 \
  --rounds 5
```

**Show:** Three swarms (adversarial, optimistic, baseline) running in parallel. Show their conclusions diverging and the consensus probability.

**Narration:**

"Layer 5 is swarm simulation. Three agent swarms attack the hypothesis from different angles. The adversarial swarm is actively trying to disprove it. The optimistic swarm is seeking confirming evidence. The baseline swarm is neutral. The disagreement between them is the signal. Here the adversarial and baseline swarms agree the timeline is aggressive, while the optimistic swarm found supporting evidence in recent benchmarks. Consensus probability: 22%. That gap between the swarms tells you exactly where the uncertainty lives."

---

## Shot 7: Integration and Closing (4:40 - 5:00)

**Action:**

```bash
# Show MCP adapter usage (quick)
cortex mcp --list-adapters
```

**Show:** The available adapters: claude-code, langchain, crewai, openai.

**Narration:**

"Finally, integration. Cortex works with Claude Code natively, and MCP adapters let you plug individual skills into LangChain, CrewAI, or OpenAI pipelines. 26 skills, MIT license, Python. The link is in the description."

**End card:** GitHub URL on screen.

---

## Production Notes

- Pre-cache all API responses for the demo to avoid network latency on camera.
- Use a pre-seeded evolution run for Shot 3 so the 5-generation run completes in under 30 seconds.
- Terminal font: JetBrains Mono or similar monospace, size 16, dark background.
- Browser: clean profile, no extensions visible, dark mode.
- No background music. Clean narration only.
- Record at 1080p 60fps, export at 1080p 30fps for upload.

---
