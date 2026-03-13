---
name: context-engineer
description: >
  Token-optimized context management with auto-pruning, relevance scoring,
  priority injection, and budget tracking. Prevents context window bloat by
  scoring and filtering what enters the conversation. Use when context is
  getting large, when "optimize context", "context-engineer", "reduce tokens",
  "context budget", "prune context", or "what's in context" is mentioned.
---

# Context Engineer: Token-Optimized Context Management

A production-grade system for managing what stays in your context window, preventing bloat through intelligent pruning, relevance scoring, and budget allocation.

## Context Budget Management

### Budget Allocation Strategy

Define your total token budget and allocate by category:

| Category | Allocation | Purpose |
|----------|-----------|---------|
| System | 20% | System prompts, safety rules, core instructions |
| Task | 40% | Current task spec, active goals, requirements |
| Reference | 25% | Code files, documentation, examples |
| History | 15% | Conversation history, previous context |

**Example for 100K token budget:**
- System: 20,000 tokens
- Task: 40,000 tokens
- Reference: 25,000 tokens
- History: 15,000 tokens

### Real-Time Budget Tracking

Monitor usage across all categories:

```
Budget Report (100K total)
═══════════════════════════════════════════════════════════
System:      8,432 / 20,000  (42%)  ▓▓▓▓░░░░░░░░░░░░░░░░
Task:       32,891 / 40,000  (82%)  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░
Reference:  18,745 / 25,000  (75%)  ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░
History:    11,203 / 15,000  (75%)  ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░

Total Used: 71,271 / 100,000  (71%)

⚠️  Task category approaching limit (82%)
✓  System budget healthy
⚠️  Reference and History over 70%
```

### Alert Thresholds

- **70%+**: Yellow alert — monitor this category
- **85%+**: Orange alert — begin compression/pruning
- **95%+**: Red alert — auto-prune initiated

## Relevance Scoring Engine

### Four-Factor Scoring Formula

Each context item receives a relevance score (0-100) based on:

```
Score = (0.3 × Recency) + (0.2 × Frequency) + (0.4 × Task_Alignment) + (0.1 × Dependency)
```

### Factor Definitions

**Recency (30% weight)**
- Exponential decay based on time since last access/addition
- Formula: `recency_score = 100 × e^(-0.05 × hours_elapsed)`
- 1 hour old = 95 | 10 hours old = 61 | 50 hours old = 7

**Frequency (20% weight)**
- How often has this item been referenced in the conversation?
- 0 references = 0 | 1-3 references = 33 | 4-8 references = 67 | 9+ references = 100

**Task Alignment (40% weight - HIGHEST IMPACT)**
- Does this item relate to the current active task?
- No relation = 0 | Peripheral = 33 | Related = 67 | Critical = 100
- Checked via keyword matching against task description

**Dependency (10% weight)**
- Is other context dependent on this item?
- No dependencies = 0 | 1-2 items depend = 50 | 3+ items depend = 100

### Example Scoring

```
File: utils.py (1,245 tokens)
├─ Recency: 87 (added 2 hours ago)
├─ Frequency: 100 (referenced 12 times)
├─ Task Alignment: 92 (core to current feature)
└─ Dependency: 67 (3 other files import it)
─────────────────────────────
SCORE: (0.3×87) + (0.2×100) + (0.4×92) + (0.1×67) = 88.3 ★★★★★

File: old_notes.md (2,100 tokens)
├─ Recency: 12 (3 days old, never revisited)
├─ Frequency: 0 (never referenced)
├─ Task Alignment: 5 (mentions unrelated feature)
└─ Dependency: 0 (nothing depends on it)
─────────────────────────────
SCORE: (0.3×12) + (0.2×0) + (0.4×5) + (0.1×0) = 5.6 ★ (prune candidate)
```

## Auto-Pruning Strategy

### Pruning Rules

When budget is exceeded:

1. **Sort** all context items by relevance score (lowest first)
2. **Compress** large items before pruning (see Compression Techniques)
3. **Prune** from bottom of list until budget restored
4. **Never prune**: active task spec, current file being edited, error context
5. **Archive** pruned items for later recall via memory search

### Compression Fallback

Before removing an item, attempt compression:

- **Strip comments**: Remove // and # comments (saves ~15-30%)
- **Collapse whitespace**: Remove extra blank lines (saves ~10%)
- **Extract relevant sections**: Keep only parts matching task keywords (saves ~40-60%)
- **Summarize code blocks**: Replace implementation with 1-line description (saves ~70%)

### Compression Examples

```python
# BEFORE (145 tokens)
def calculate_user_metrics(user_id, date_range):
    """
    Calculate various metrics for a user over a date range.
    
    This function pulls data from the database, filters by date,
    applies various transformations, and returns aggregated metrics.
    Uses caching to improve performance.
    """
    # Get user from database
    user = db.get_user(user_id)
    
    # Filter events by date
    events = [e for e in user.events if date_in_range(e.date, date_range)]
    
    # Calculate metrics
    metrics = {
        'total': len(events),
        'avg': sum(e.value for e in events) / len(events),
        'max': max(e.value for e in events)
    }
    
    return metrics

# AFTER (32 tokens)
def calculate_user_metrics(user_id, date_range):
    """Calculate aggregated metrics (total, avg, max) for user events in date range."""
    user = db.get_user(user_id)
    events = [e for e in user.events if date_in_range(e.date, date_range)]
    return {'total': len(events), 'avg': sum(e.value for e in events)/len(events), 'max': max(e.value for e in events)}

# COMPRESSION GAIN: 78% reduction
```

## Context Injection Control

### Priority Levels

Assign each context item a priority level:

| Level | Behavior | Examples |
|-------|----------|----------|
| **CRITICAL** | Always inject, never prune | Current task, active file, error context |
| **HIGH** | Inject if budget allows | Core dependencies, recent files |
| **NORMAL** | Inject based on relevance score | Documentation, utilities, examples |
| **LOW** | Inject only on explicit request | Historical notes, archived code |

### Injection Timing

Context enters the window at:

1. **Session Start**: System prompts, task spec, high-priority items
2. **Task Switch**: New task spec, relevant files, dependencies
3. **Explicit Request**: User asks for specific context
4. **Auto-Recovery**: After pruning, if score improves

### Format Optimization

When injecting context:

- **Strip comments** from code files
- **Collapse whitespace** and excessive blank lines
- **Extract relevant sections** from large files (e.g., one function from a 500-line file)
- **Use summaries** for documentation (3-line summary instead of full docs)
- **Link references** instead of embedding entire files

## Context Inventory

### Inventory Report

View all items currently in context:

```
CONTEXT INVENTORY
═══════════════════════════════════════════════════════════════════════════════
Size   Score  Category    Priority  Source
───────────────────────────────────────────────────────────────────────────────
1,245  88.3   Reference   HIGH      utils.py
2,891  76.5   Task        CRITICAL  task_spec.md
3,127  71.2   Reference   NORMAL    models.py
  847  65.3   Reference   NORMAL    helpers.py
  234  62.1   History     NORMAL    conversation_snippet_001.txt
2,100   5.6   Reference   LOW       old_notes.md (PRUNE CANDIDATE)
 412   3.2   History     LOW       archived_draft.txt (PRUNE CANDIDATE)
───────────────────────────────────────────────────────────────────────────────
Total: 10,856 tokens | Items: 7 | Avg Score: 52.3
```

### Metrics to Track

For each item:
- **Source**: File path, URL, or conversation snippet ID
- **Size (tokens)**: Estimated token count
- **Relevance Score**: 0-100 calculation
- **Category**: System, Task, Reference, or History
- **Priority**: CRITICAL, HIGH, NORMAL, or LOW
- **Timestamp**: When added to context
- **Last Accessed**: When last referenced in conversation
- **Access Count**: How many times referenced

### Optimization Recommendations

The system provides actionable recommendations:

```
OPTIMIZATION OPPORTUNITIES
═════════════════════════════════════════════════════════════════════════════
✓ QUICK WINS (Immediate compression gains)
  • old_notes.md: Replace with 2-line summary (save 2,000 tokens)
  • archived_draft.txt: Safe to archive (score 3.2, save 412 tokens)
  • models.py: Extract only 2 functions used in task (save ~1,500 tokens)

! MONITOR THESE
  • Task category at 82% - will exceed budget in ~5 additions
  • Reference category at 75% - compress one large file to stay under 80%

✓ LONG-TERM STRATEGY
  • Split task context into subtasks (reduce active context)
  • Archive conversation history older than 20 messages
  • Create reference summary for documentation
```

## Usage with Claude Code

### When to Use Context Engineer

Use this skill when you notice:

- "Optimize context" or "context-engineer" explicitly mentioned
- "Reduce tokens" or "context budget" discussed
- "Prune context" or "what's in context" requested
- Context window getting large (75%+ capacity)
- Token count warnings appearing
- Need to manage multiple files/references simultaneously

### Integration with Your Workflow

1. **Start Session**: Initialize with `python3 context_engine.py add` for key files
2. **Monitor**: Check budget with `python3 context_engine.py budget` periodically
3. **Optimize**: Run `python3 context_engine.py optimize` when approaching limits
4. **Archive**: Review and archive low-score items before they're auto-pruned
5. **Recall**: Search archived context when needed via memory system

### Commands

```bash
# Add new context item
python3 context_engine.py add --source file.py --category reference --priority high

# Score all items and show recommendations
python3 context_engine.py score

# Prune lowest-scoring items until budget restored
python3 context_engine.py prune --budget 100000

# Show budget breakdown and alerts
python3 context_engine.py budget

# Full inventory report with metrics
python3 context_engine.py inventory

# One-command optimization (compress + prune)
python3 context_engine.py optimize --budget 100000 --target 85%

# Export context state as JSON
python3 context_engine.py export --output context_state.json
```

## Best Practices

1. **Set realistic budgets** based on task complexity (50-200K tokens)
2. **Prioritize ruthlessly** — CRITICAL and HIGH should be <20% of total context
3. **Compress early** — compress before pruning to minimize information loss
4. **Archive strategically** — keep pruned items searchable for 30 days
5. **Monitor trends** — review which categories consistently exceed budget
6. **Document dependencies** — note which files depend on which for better scoring
7. **Review recommendations** — check the optimization report weekly

## See Also

- `references/context-patterns.md` — Token budgeting strategies and compression techniques
- `scripts/context_engine.py` — Python implementation with CLI
