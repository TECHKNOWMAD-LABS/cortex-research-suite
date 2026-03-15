# Contributing to Cortex

Thanks for considering a contribution. This guide covers the workflow and standards.

## Development Setup

```bash
git clone https://github.com/TECHKNOWMAD-LABS/cortex.git
cd cortex/skill-organism
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

No external dependencies required — the entire project runs on Python stdlib.

## Code Standards

- **Python 3.10+** required
- **PEP 8** formatting (use `ruff` or `black`)
- **Type hints** on all function signatures
- **Docstrings** on all public classes and methods
- No new external dependencies without strong justification

## Architecture Overview

The system follows a biological evolution cycle:

```
OBSERVE -> MUTATE -> SELECT -> REPRODUCE -> HEAL
```

Each stage is a method on `SkillOrganism` in `organism.py`. The telemetry backend lives in `telemetry.py`, genetic operations in `skill_dna.py`, and the production wrapper in `enterprise_runner.py`.

### Key Files

| File | Purpose |
|------|---------|
| `organism.py` | Core evolution engine |
| `telemetry.py` | SQLite metrics collection |
| `skill_dna.py` | Genetic crossover and mutation |
| `evolution_cycle.py` | CLI entry point |
| `enterprise_runner.py` | Production wrapper with integrity checks |
| `skill_registry.json` | Skill population state |

## Testing

```bash
python -m pytest tests/
python validate_organism.py  # Integration smoke test
python enterprise_runner.py  # Full cycle with enterprise checks
```

Ensure the evolution cycle completes with exit code 0 before submitting a PR.

## Pull Request Process

1. Fork the repo and create a feature branch from `main`
2. Make your changes with tests
3. Run the full evolution cycle locally
4. Submit a PR with the template filled out
5. One maintainer review required

## Good First Issues

These areas are well-scoped for new contributors:

- **Custom fitness functions**: Add alternative scoring strategies beyond the default 40/40/20 split
- **Telemetry exporters**: Export metrics to Prometheus, StatsD, or OpenTelemetry
- **Health check strategies**: Implement new healing strategies beyond the current critical-flag approach
- **Visualization**: Improve the dashboard with new chart types or real-time updates
- **Documentation**: Add examples, tutorials, or architecture decision records

## Commit Messages

Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

## Questions?

Open a discussion on GitHub or reach out at admin@techknowmad.ai.