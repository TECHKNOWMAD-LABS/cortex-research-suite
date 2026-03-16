# Contributing to Cortex

## Submitting Issues

Report bugs and request features by opening an issue:
- **Bug Reports**: Include steps to reproduce, expected vs actual behavior, and your environment details
- **Feature Requests**: Describe the use case and how the feature should work

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes following the format below
4. Push to your fork and open a pull request against `main`
5. Address review feedback and maintain branch up-to-date with main

## Adding a new skill

Directory structure:
```
skills/{skill-name}/
  SKILL.md         — skill instruction (the "code" the organism evolves)
  ARENA.md         — arena config (the "program.md" — human edits this)
  scripts/         — Python implementation scripts
  references/      — (optional) reference docs, checklists
```

SKILL.md template:
```markdown
# {skill-name}
## Overview — what this skill does
## Core instruction — the main prompt
## Output schema — expected JSON output
## Examples — 2-3 before/after demonstrations
## Common gotchas — failure modes to avoid
```

ARENA.md: copy from any existing skill's ARENA.md, update:
- `notes` field (what "better" means for YOUR skill)
- `eval_budget_seconds` (30s default, increase for API-heavy skills)
- `allowed_mutations` (which improvement strategies apply)
- `trilogy` fields (if integrating with MindSpider/BettaFish/MiroFish)

Running evaluation on your skill:
```bash
python3 datasets/generators/skill_dataset_generator.py --skill {skill-name} --n 50
python3 skills/skill-test-harness/scripts/eval_judge.py \
  --skill {skill-name} \
  --dataset datasets/synthetic/{skill-name}/shard_000.json
```

Running evolution on your skill:
```bash
python3 skill-organism/enterprise_runner.py --skill {skill-name} --generations 5
```

## Code Standards

**Python:**
- Use type hints on all function parameters and return values
- Write docstrings for all functions and classes (Google style)
- Avoid bare `except:` clauses; catch specific exceptions
- Use parameterized queries for SQL to prevent injection
- Format code with Black (line length 88)

**General:**
- Keep functions focused and reasonably sized
- Write meaningful variable names
- Add inline comments for non-obvious logic

## Security Requirements

- Never commit secrets (API keys, tokens, credentials)
- Use `defusedxml` for parsing untrusted XML
- Pass `shell=False` to `subprocess` calls
- Validate all user inputs
- Review dependencies before adding

## Testing

- Run `bandit` on all Python code before submitting: `bandit -r .`
- Add tests for new functionality
- Ensure existing tests pass

## Commit Message Format

Use clear, concise messages:
```
Brief summary of changes (50 chars max)

Longer explanation if needed. Explain the why, not just what changed.
```

## License

This project is licensed under the MIT License. By contributing, you agree that your contributions will be licensed under the same terms.
