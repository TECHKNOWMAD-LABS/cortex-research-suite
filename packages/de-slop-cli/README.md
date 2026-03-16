# de-slop-cli

Standalone CLI for detecting AI-generated writing patterns in documentation and markdown files.

Part of [Cortex Research Suite](https://github.com/TECHKNOWMAD-LABS/cortex-research-suite).

## Install

```bash
pip install -e packages/de-slop-cli/
```

## Usage

```bash
de-slop --target docs/ --format both --threshold 40
```

## What it detects

- Emoji in headers
- Hyperbolic language and buzzword stacking
- Defensive framing and hedging
- Motivational fluff
- AI writing patterns (repetitive sentence starters, filler transitions)

## Output

JSON report + markdown report with per-file scores and suggested fixes.
