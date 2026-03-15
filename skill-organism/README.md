# Cortex Skill Organism

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/TECHKNOWMAD-LABS/cortex?style=social)](https://github.com/TECHKNOWMAD-LABS/cortex)

**Evolutionary intelligence for AI skill ecosystems.** Cortex implements a biological evolution engine that treats AI skills as living organisms. Skills compete, adapt, breed, and evolve through natural selection, genetic mutation, and fitness-driven reproduction.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SKILL ORGANISM ENGINE                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  1. OBSERVE     │  Collect telemetry: success_rate, latency,
│   (telemetry)   │  satisfaction from SQLite
└────────┬────────┘
         ▼
┌─────────────────┐
│  2. MUTATE      │  Generate variants from top 5 performers
│ (param tweak)   │  Version bumps, ±5% fitness boost
└────────┬────────┘
         ▼
┌─────────────────┐
│  3. SELECT      │  Cull <0.6 fitness (if <5 uses)
│(natural select) │  Promote >0.8 to auto-deploy
└────────┬────────┘
         ▼
┌─────────────────┐
│  4. REPRODUCE   │  Crossover: combine top 10
│  (breed hybrids)│  Create 1-3 offspring/cycle
└────────┬────────┘
         ▼
┌─────────────────┐
│  5. HEAL        │  Flag critical skills
│  (recovery)     │  Plan remediation
└─────────────────┘
```

### Fitness Scoring

```
FITNESS = 0.40 × success_rate + 0.40 × satisfaction + 0.20 × normalized_invocations
```

Cull below 0.6 (if usage < 5). Promote above 0.8.

---

## Enterprise Features

`enterprise_runner.py` provides production-grade safety:

- **SHA-256 integrity** — Registry verified before/after mutations
- **Atomic backup/rollback** — Full snapshots; instant rollback on failure
- **fcntl lockfile** — Prevents concurrent execution
- **Health gate** — Aborts if >30% critical or >80% deprecated
- **JSON logging** — Structured logs with rotation (50 MB max)
- **Telemetry retention** — Auto-purges data older than 90 days
- **Signal handling** — Graceful shutdown on SIGTERM/SIGINT
- **CI/CD exit codes** — 0=success, 1=failure, 2=lock, 3=integrity, 4=health, 5=rollback

---

## Installation

```bash
pip install cortex-skill-organism
```

Or from source:

```bash
git clone https://github.com/TECHKNOWMAD-LABS/cortex.git
cd cortex && pip install -e .
```

**Requirements:** Python 3.10+, zero external dependencies.

---

## Quick Start

```python
from pathlib import Path
from cortex_skill_organism import SkillOrganism

organism = SkillOrganism(
    registry_path=Path("skill_registry.json"),
    telemetry_db=Path("skill_telemetry.db"),
    log_dir=Path("logs"),
)

result = organism.evolve()
report = organism.report()
```

CLI:

```bash
cortex-evolve --registry skill_registry.json --verbose
python enterprise_runner.py  # Production mode
```

---

## Live Results

From actual evolution run on 23-skill ecosystem:

```
EVOLUTION CYCLE COMPLETE — 0.03s
  Skills observed: 27
  Culled: 7
  Promoted: 1
  Offspring: 2
  Critical (healing): 3
```

1,040 invocations processed. 7 categories: research, MLOps, agents, meta, security, prompting, creative.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Good first issues: custom fitness functions, telemetry exporters, health check strategies.

## License

MIT. See [LICENSE](LICENSE).

## Citation

```bibtex
@software{cortex_2026,
  title={Cortex: Evolutionary Intelligence for AI Skill Ecosystems},
  author={TechKnowmad Labs},
  year={2026},
  url={https://github.com/TECHKNOWMAD-LABS/cortex}
}
```

Built by [TechKnowmad AI](https://techknowmad.ai)