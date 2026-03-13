---
name: de-slop
description: >
  Detect and flag AI-generated writing patterns in markdown and documentation.
  Scans for emoji in headers, hyperbolic language, defensive framing, buzzword
  stacking, motivational fluff, and other telltale signs of LLM-generated
  content. Use when the user mentions "remove AI slop", "make this look
  professional", "doesn't look human-written", "de-slop", "clean up AI
  writing", "remove AI artifacts", "make this look like a human wrote it",
  "too much AI energy", "sounds like ChatGPT", or any request to improve
  writing quality by removing machine-generated patterns. Also use as a
  pre-publish quality gate for documentation, READMEs, and technical writing.
  This skill runs an actual scanner — not just a checklist.
---

# De-Slop — AI Writing Pattern Scanner

Automated detection of AI-generated writing patterns in markdown files. Runs
regex and heuristic analysis, produces per-file scores, and flags specific
lines with suggested fixes.

## When to Use

This skill detects AI writing anti-patterns. It does not enforce brand voice
(use `brand-voice-enforcement` for that) or compress content (use
`knowledge-distiller` for that). It answers: "Does this text look like an AI
wrote it, and where specifically?"

## Workflow

### 1. Identify target files

Scan all markdown files in the target directory:
```bash
find <target> -name "*.md" -type f
```

Also scan: `.txt`, `.rst`, any file the user points to.

### 2. Run the scanner

```bash
python <skill-path>/scripts/slop_scanner.py --target <directory> --output <report-path>
```

The scanner checks every line against a curated pattern library and produces a
per-file score (0–100, where 0 = clean, 100 = pure slop).

### 3. Produce report

Output:
- `slop-report.json` — machine-readable scores and line-level flags
- `slop-report.md` — human-readable summary with suggested fixes

Report structure:
```markdown
# AI Slop Audit Report

**Target:** /path/to/repo
**Files scanned:** 12
**Date:** 2026-03-13

## Summary
| File | Score | Flags | Verdict |
|------|-------|-------|---------|
| README.md | 72 | 14 | FAIL |
| SKILL.md | 31 | 5 | WARN |
| docs/guide.md | 8 | 1 | PASS |

## Findings

### README.md (score: 72)

**Line 1:** Emoji in header
> # 🚀 ViralForge — Social Media Domination Engine
Suggested: `# ViralForge — Video content pipeline for social media`

**Line 15:** Buzzword stacking
> Battle-tested, enterprise-grade, production-ready pipeline
Suggested: Remove redundant qualifiers. Pick one.

**Line 22:** Defensive framing
> This is not a template collection — it's a complete system
Suggested: Remove. Let the content speak for itself.
```

### 4. Optionally auto-fix

If the user asks for fixes (not just detection), apply them:
1. Generate a clean version of each flagged file
2. Show a diff to the user before applying
3. Apply only after confirmation

## Pattern Categories

The scanner checks for these categories, each weighted by severity:

### Category 1: Structural Tells (weight: 3)
- Emoji in headers (`# 🚀 Title`)
- Excessive bold in lists (`- **Always** do **this** with **every** item`)
- Headers that are full sentences (`## How This Revolutionary System Works`)
- Numbered lists where bullets would do

### Category 2: Hyperbolic Language (weight: 2)
- Power words: revolutionary, game-changing, cutting-edge, world-class,
  domination, groundbreaking, transformative, unleash, supercharge
- Superlatives without evidence: "the most", "the best", "unparalleled"
- Marketing language in technical docs: "take it to the next level"

### Category 3: Defensive/Compensatory Framing (weight: 2)
- "This is not a..." (defensive opening)
- "Unlike other..." (unprompted comparison)
- "What sets X apart..." (self-promotional)
- "Not just another..." (anticipating skepticism)

### Category 4: Buzzword Patterns (weight: 2)
- Stacking: "enterprise-grade, production-ready, battle-tested"
- Redundancy: "fully autonomous zero-human-intervention pipeline"
- Empty modifiers: "robust", "seamless", "elegant", "scalable" (without
  specifics)

### Category 5: Motivational/Inspirational Tone (weight: 1)
- "Who refuse to be average"
- "Dare to dream bigger"
- "For those who demand excellence"
- Aspirational statements in technical documentation

### Category 6: Filler Patterns (weight: 1)
- "In today's rapidly evolving landscape..."
- "As we navigate the complexities of..."
- "It's worth noting that..."
- "At the end of the day..."
- "Let's dive in" / "Let's explore"
- Starting paragraphs with "So," or "Now,"

### Category 7: Repetitive Structure (weight: 1)
- Every list item starts with "Never" or "Always"
- Identical sentence structures across paragraphs
- Parallel phrasing that feels templated

## Scoring

```
file_score = sum(pattern_weight * match_count for each pattern) / total_lines * 100
```

Thresholds:
- 0–15: PASS (clean, professional writing)
- 16–40: WARN (some patterns detected, review suggested)
- 41+: FAIL (significant AI writing patterns, rewrite recommended)

## Reference Files

- **`scripts/slop_scanner.py`** — Main scanner script. Regex + heuristic
  analysis, JSON and markdown output. Stdlib only.
- **`references/anti-patterns.md`** — Full pattern catalog with examples and
  suggested rewrites for each category.
