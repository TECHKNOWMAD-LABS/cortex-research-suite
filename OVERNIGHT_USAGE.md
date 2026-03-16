# Overnight Autonomous Evolution

Run the Skill Organism evolution engine overnight for continuous improvement.

## Quick start

```bash
# Run 10 generations across all 21 skills (default)
python skill-organism/enterprise_runner.py --overnight

# Custom generation count
python skill-organism/enterprise_runner.py --overnight --generations 20

# Single skill evolution
python skill-organism/enterprise_runner.py --skill security-audit --generations 5
```

## How it works

1. **ARENA.md** defines the fitness function, mutation strategies, and experiment budget for each skill
2. **enterprise_runner.py** orchestrates the evolution cycle with:
   - File integrity verification (SHA-256 checksums)
   - Atomic registry updates with backup/rollback
   - Health gate (aborts if >30% skills are critical)
   - EvalBudget context manager (30s per skill per generation)
3. **eval_judge.py** scores each mutation on 5 dimensions
4. **Git-per-experiment** branches isolate mutations; only improvements merge
5. **evolution_log.jsonl** captures every event for the dashboard

## Parallel execution

The overnight runner uses `asyncio.Semaphore(4)` for concurrent skill evolution.
Each generation processes up to 4 skills simultaneously.

## Monitoring

While the overnight run executes:

```bash
# Watch the evolution log
tail -f skill-organism/evolution_log.jsonl | python -m json.tool

# Open the dashboard
open dashboards/evolution_dashboard.html
```

## Budget controls

Each skill evaluation is capped at `eval_budget_seconds` (default: 30s) from its ARENA.md.
The total overnight budget is approximately: `generations × skills × budget_seconds`.

For 10 generations × 21 skills × 30s = ~105 minutes of evaluation time.

## Safety

- Lockfile prevents concurrent evolution cycles
- Pre-flight and post-flight integrity checks on the skill registry
- Automatic rollback if the registry becomes corrupted
- Signal handlers for graceful SIGTERM/SIGINT shutdown

## Trilogy integration

When ARENA.md has `mindspider_feed_enabled: true`, the evolution loop will:
1. Check `datasets/mindspider/today_topics.json` for live data
2. Fall back to synthetic data if unavailable
3. Log trilogy integration status in each evolution event
