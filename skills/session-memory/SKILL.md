---
name: session-memory
description: >
  Automatic checkpointing of session state to survive context compaction.
  Tracks files created, decisions made, errors resolved, and current task
  state. Use when starting long sessions, before context gets large, or
  when resuming from a continuation summary. Triggers on "checkpoint",
  "save session state", "session-memory", "context is getting long", or
  "save progress".
---

## Overview

The session-memory skill provides automated state management for long-running Claude Code sessions. It captures the current context—files, decisions, errors, and task progress—into structured checkpoint files that survive context compaction and enable seamless resumption.

Use this skill when:
- Starting a multi-hour session with complex tasks
- Context size approaches limits (determined by token count)
- Completing major milestones that should be preserved
- Encountering errors that might need recovery context
- Resuming a session from a continuation summary

## Checkpoint Format

Checkpoints are structured markdown files with consistent sections:

```markdown
# Session Checkpoint — {ISO 8601 timestamp}

## Files Modified
- /absolute/path/file.py (created, 2.3KB, 2026-03-13T14:05:00Z)
- /absolute/path/file.md (modified, 1.1KB, 2026-03-13T13:58:00Z)

## Decisions Made
- Brief description of architectural choice or trade-off
- Explanation of why one approach was chosen over another

## Errors Resolved
- Error message or description — what was done to resolve it
- Root cause and fix applied

## Current Tasks
- [x] Completed task with clear description
- [x] Another completed task
- [ ] Task currently in progress
- [ ] Pending task

## Environment
- Working directory: /sessions/eloquent-wizardly-ride/
- Session start: 2026-03-13T10:00:00Z
- Last checkpoint: 2026-03-13T14:00:00Z
- Python version: 3.x.x
- Key paths: /mnt/VCEfiles/skills/, /sessions/*/
```

All file paths must be absolute. Timestamps follow ISO 8601 format with UTC timezone. Tasks are listed in order of completion or priority.

## When to Checkpoint

**Automatic triggers:**
- Explicitly request: "checkpoint", "save session state", "save progress"
- Periodic: after 1-2 hours of work or every 50-100 tool calls

**Manual triggers:**
- Before high-risk operations (deleting files, modifying core systems)
- After resolving significant errors
- When completing discrete project phases
- Before taking a major architectural decision

## Reading Checkpoints When Resuming

When resuming from a checkpoint:

1. **Load the checkpoint file** using `checkpoint.py load --checkpoint /path/to/checkpoint.md`
2. **Review the current tasks section** to understand what was in progress
3. **Check files modified** to know which files changed most recently
4. **Note resolved errors** to avoid repeating failed approaches
5. **Understand key decisions** to maintain architectural consistency

Use the Tasks section to restore TodoWrite state if needed. Reference specific file paths and decisions when continuing work.

## Integration with TodoWrite

When creating a checkpoint, include the current task state:

```bash
python3 checkpoint.py save \
  --session-dir /path/to/session \
  --output /path/to/checkpoint.md \
  --tasks '{"Build core feature": "in_progress", "Write tests": "pending"}'
```

When resuming from a checkpoint, extract task state and pass it to TodoWrite to restore the work context.

## Script Usage

### Save a checkpoint

```bash
python3 scripts/checkpoint.py save \
  --session-dir /sessions/eloquent-wizardly-ride/ \
  --output checkpoints/session_2026-03-13_1405.md \
  --decisions "Used async/await instead of callbacks" \
  --decisions "Chose SQLite over PostgreSQL for simplicity" \
  --errors "YAML parsing failed due to tabs" \
  --tasks '{"feature X": "completed", "feature Y": "in_progress"}'
```

### Load a checkpoint

```bash
python3 scripts/checkpoint.py load \
  --checkpoint checkpoints/session_2026-03-13_1405.md
```

### List all checkpoints

```bash
python3 scripts/checkpoint.py list \
  --checkpoint-dir checkpoints/
```

## Implementation Notes

- Files discovered via directory scan of session working directory
- Default time window: 1 hour (configurable via `--time-window 3600`)
- Incremental checkpoints only capture changes since last checkpoint (if tracking file)
- Script uses Python standard library only (no external dependencies)
- Output is human-readable markdown with machine-parseable sections
