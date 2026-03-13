# Context Engineering Patterns & Techniques

Advanced strategies for token budgeting, relevance scoring, and context compression.

## Part 1: Token Budgeting Strategies

### Strategy 1: The Three-Ring Circus (Beginner)

Divide context into three tiers based on importance:

```
RING 1: CRITICAL (Never prune, always available)
├─ Current task specification
├─ Active file being edited
└─ Error context

RING 2: HOT (Keep for this session)
├─ Task-related files
├─ Recent changes
└─ Dependencies

RING 3: COOL (Reference, archive when needed)
├─ Documentation
├─ Historical context
└─ Low-relevance items
```

**Budget allocation**: 10% critical, 50% hot, 40% cool

**When to use**: Simple projects, short sessions (<30 messages)

### Strategy 2: The Category Fortress (Intermediate)

Strict budget allocation by context type (default in Context Engineer):

| Category | Budget | Contents |
|----------|--------|----------|
| System | 20% | Prompts, rules, instructions |
| Task | 40% | Current work, requirements |
| Reference | 25% | Code, docs, examples |
| History | 15% | Conversation, previous context |

**Enforcement**: Hard limits per category, spillover from one blocks additions to another

**When to use**: Multi-file projects, complex specifications, long sessions

### Strategy 3: The Time Decay (Advanced)

Allocate budget dynamically based on temporal distance:

```
AGE-BASED BUDGET WINDOWS:
├─ 0-1 hours:    85% available (hot context)
├─ 1-4 hours:    60% available (warm)
├─ 4-12 hours:   40% available (cool)
├─ 12-24 hours:  20% available (cold)
└─ 24+ hours:     5% available (archive)
```

Formula: `available_budget = base_budget × e^(-0.1 × hours_elapsed)`

**Advantage**: Automatically makes room for recent work without manual pruning

**When to use**: Long-running projects spanning multiple days

### Strategy 4: The Dependency Web (Expert)

Score context based on what depends on it:

```
DEPENDENCY SCORING:
├─ No dependencies: 0 points
├─ 1-2 other files depend on this: +50 points
├─ 3-5 files depend on this: +75 points
├─ 6+ files depend on this: +100 points

Example:
utils.py (7 files depend on it, 800 tokens) → Score 100 (keep!)
old_notes.md (0 dependencies, 2000 tokens) → Score 0 (prune!)
```

**When to use**: Large codebases, refactoring work, architectural review

## Part 2: Relevance Scoring Deep Dive

### Recency Scoring: Understanding Exponential Decay

The recency formula gives old context low scores:

```
score = 100 × e^(-0.05 × hours_elapsed)

Hours Elapsed    Score
─────────────────────────
0 minutes        100
30 minutes        98
1 hour            95
2 hours           91
6 hours           74
12 hours          54
24 hours          30
48 hours           9
72 hours           2
```

**Implication**: Context older than 3 days almost always gets pruned

**Adjust sensitivity** with decay constant:
- `-0.05` (default): Gentle decay, context stays relevant ~3 days
- `-0.10`: Faster decay, context ages out in ~1.5 days
- `-0.02`: Slower decay, context stays relevant ~7 days

### Frequency Scoring: Measuring Engagement

Track how many times context has been referenced:

```
Reference Count    Score    Interpretation
─────────────────────────────────────────────
0                  0        Never used yet
1-3                33       Lightly used
4-8                67       Moderately used
9+                 100      Heavily referenced
```

**Why it matters**: Items you keep returning to are more valuable than one-time reads

**Custom thresholds** for your project:
```python
# For short sessions (< 20 messages)
if references == 0: score = 0
elif references <= 2: score = 50
elif references >= 3: score = 100

# For long sessions (> 50 messages)
if references == 0: score = 0
elif references <= 5: score = 25
elif references <= 15: score = 75
elif references >= 16: score = 100
```

### Task Alignment: The Heavyweight Factor (40% weight)

Task alignment has the highest weight in scoring. Calculate by:

1. **Extract keywords** from task description
2. **Score each item** against keywords:
   - No matches → 0
   - 1-2 matches → 33
   - 3+ matches → 67
   - Explicitly marked critical → 100

**Example**: Building a payment system

```
Task: "Implement credit card payment processing with Stripe integration"
Keywords: [payment, stripe, card, process, integration, charge]

scoring_file.ts (keywords: payment, stripe, integration, charge)
  → 4 matches → Score 100 (critical)

utils.py (keywords: none)
  → 0 matches → Score 0 (irrelevant)

old_auth.py (keywords: none)
  → 0 matches → Score 0 (irrelevant)
```

### Dependency Scoring: Building the Knowledge Graph

Some context items are foundations others depend on:

```
models.ts (imported by 8 files)
├─ payment_processor.ts depends on it
├─ order_handler.ts depends on it
├─ receipt_generator.ts depends on it
├─ ... 5 more files
└─ Dependency score: 100 (KEEP!)

legacy_notes.md (no dependencies)
└─ Dependency score: 0 (PRUNE!)
```

Track this by:
1. After adding each item, scan for imports/references
2. Count how many other items reference this one
3. Score: 50 points per dependent item (capped at 100)

## Part 3: Advanced Compression Techniques

### Compression Technique 1: Strip Comments

**Remove** all comments (// and #)

```python
# BEFORE: 234 tokens
def calculate_metrics(data):
    """Calculate various metrics from data."""
    # Get base values
    total = sum(data)  # Sum all values
    
    # Calculate average
    # This is the mean value
    average = total / len(data)
    
    # Find max
    maximum = max(data)  # Get largest value
    
    return {"total": total, "avg": average, "max": maximum}

# AFTER: 156 tokens (33% reduction)
def calculate_metrics(data):
    """Calculate various metrics from data."""
    total = sum(data)
    average = total / len(data)
    maximum = max(data)
    return {"total": total, "avg": average, "max": maximum}
```

**Token savings**: 15-35% depending on comment density

**Safety**: Safe if comments aren't critical to understanding logic

### Compression Technique 2: Collapse Whitespace

**Remove** extra blank lines, leading spaces

```python
# BEFORE: 189 tokens
def process_order(order_id):

    order = fetch_order(order_id)
    
    
    if order.status == "pending":
        
        order.status = "processing"
        
        save_order(order)
        
        return {"success": True}
    
    
    return {"success": False}

# AFTER: 112 tokens (41% reduction)
def process_order(order_id):
    order = fetch_order(order_id)
    if order.status == "pending":
        order.status = "processing"
        save_order(order)
        return {"success": True}
    return {"success": False}
```

**Token savings**: 30-45% depending on whitespace

**Safety**: Very safe, preserves all logic

### Compression Technique 3: Extract Relevant Sections

**Keep** only functions/sections matching task keywords

```javascript
// BEFORE: 1,245 tokens (entire file)
class PaymentProcessor {
  constructor() { ... }
  
  // Unrelated: User authentication (300 tokens)
  authenticate(user) { ... }
  validateToken(token) { ... }
  refreshToken() { ... }
  
  // Relevant: Payment processing (400 tokens)
  processPayment(amount, card) { ... }
  validateCard(card) { ... }
  calculateFee(amount) { ... }
  
  // Unrelated: Reporting (300 tokens)
  generateReport(dateRange) { ... }
  exportToCSV() { ... }
  sendEmail(report) { ... }
  
  // Unrelated: Caching (245 tokens)
  cacheResult(key, value) { ... }
  getCached(key) { ... }
  invalidateCache() { ... }
}

// AFTER: 420 tokens (extract only payment methods)
class PaymentProcessor {
  processPayment(amount, card) { ... }
  validateCard(card) { ... }
  calculateFee(amount) { ... }
}

// Result: 66% reduction
```

**Token savings**: 50-70% when extracting from large files

**Safety**: Requires careful selection to avoid breaking dependencies

### Compression Technique 4: Summarize Large Blocks

**Replace** implementation with 1-line summary

```python
# BEFORE: 487 tokens
def build_user_profile(user_id):
    """Build comprehensive user profile with all metrics."""
    user = db.query_user(user_id)
    
    # Fetch user events from the past 6 months
    events = db.query_events(
        user_id=user_id,
        date_after=datetime.now() - timedelta(days=180)
    )
    
    # Group events by type
    events_by_type = {}
    for event in events:
        if event.type not in events_by_type:
            events_by_type[event.type] = []
        events_by_type[event.type].append(event)
    
    # Calculate statistics for each type
    stats = {}
    for event_type, type_events in events_by_type.items():
        values = [e.value for e in type_events]
        stats[event_type] = {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values) if values else 0,
            "max": max(values) if values else 0,
            "min": min(values) if values else 0,
        }
    
    # Build final profile
    profile = {
        "user": user,
        "event_stats": stats,
        "total_events": len(events),
        "last_event": max([e.timestamp for e in events]),
    }
    
    return profile

# AFTER: 34 tokens (93% reduction!)
def build_user_profile(user_id):
    """Build user profile: queries events, groups by type, calculates stats."""
    user = db.query_user(user_id)
    events = db.query_events(user_id, date_after=datetime.now()-timedelta(days=180))
    return {"user": user, "event_stats": summarize_events(events), "total_events": len(events)}
```

**Token savings**: 90%+ for verbose implementations

**Safety**: Use only for reference code, not actively being edited

### Compression Technique 5: Convert to Pseudocode

**Replace** code with human-readable algorithm description

```python
# BEFORE: 312 tokens (actual implementation)
def find_optimal_route(origin, destination, graph):
    visited = set()
    queue = [(origin, [origin], 0)]
    min_distance = float('inf')
    best_route = None
    
    while queue:
        current, path, distance = queue.pop(0)
        
        if current in visited:
            continue
        visited.add(current)
        
        if current == destination:
            if distance < min_distance:
                min_distance = distance
                best_route = path
            continue
        
        for neighbor, weight in graph[current].items():
            if neighbor not in visited:
                new_distance = distance + weight
                if new_distance < min_distance:
                    queue.append((neighbor, path + [neighbor], new_distance))
    
    return best_route, min_distance

# AFTER: 28 tokens (pseudocode)
def find_optimal_route(origin, destination, graph):
    """BFS to find shortest path from origin to destination in weighted graph."""
    # Queue stores: (current_node, path_so_far, distance)
    # Returns: (best_path, min_distance)
```

**Token savings**: 85-95% when code is reference-only

**Safety**: Only for understanding algorithm, not for running code

## Part 4: Real-World Optimization Examples

### Example 1: Refactoring a Large Module

**Scenario**: 3,000-token module, only 2 functions are relevant

```
Current Budget: 100K tokens (71% used)
Target: 85K (free up 6K tokens)

ANALYSIS:
├─ module.py (3,000 tokens, score 25)
│  ├─ function_a() - RELEVANT (400 tokens)
│  ├─ function_b() - RELEVANT (350 tokens)
│  ├─ function_c() - Unrelated (800 tokens)
│  ├─ function_d() - Unrelated (900 tokens)
│  └─ helper functions - Unrelated (550 tokens)
└─ Impact: Keep function_a/b only = 750 tokens (75% reduction)

ACTION: Extract function_a and function_b to new_module.py (750 tokens)
RESULT: -2,250 tokens freed = 68.7% utilization ✓
```

### Example 2: Aging Out Session History

**Scenario**: Session running for 8 hours, accumulating history

```
TIMELINE:
├─ Hour 0-2: Adding task context (highly relevant, max score)
├─ Hour 2-4: Building first feature (score 85+)
├─ Hour 4-6: Feature complete, moving to next (score 60)
└─ Hour 6-8: Only historical reference (score 15)

ACTION:
├─ Hour 0-2: Allocate 5,000 tokens (critical)
├─ Hour 2-4: Allocate 12,000 tokens (active work)
├─ Hour 4-6: Allocate 8,000 tokens (cooling down)
└─ Hour 6-8: Archive or compress to 2,000 tokens

RESULT: Progressive memory of first 6 hours without bloat
```

### Example 3: Multi-File Dependency Management

**Scenario**: Building payment system with 5 interdependent files

```
DEPENDENCY MAP:
payment_processor.ts (1,200 tokens)
├─ Depends on: stripe_api.ts, database.ts
├─ Depended on by: order_handler, receipt_generator, admin_dashboard
└─ Priority: HIGH (dependency count: 3)

stripe_api.ts (800 tokens)
├─ Depends on: config.ts
├─ Depended on by: payment_processor
└─ Priority: HIGH (dependency count: 1)

utils.ts (600 tokens)
├─ Depends on: nothing
├─ Depended on by: all other files
└─ Priority: CRITICAL (dependency count: 4)

database.ts (1,100 tokens)
├─ Depends on: config.ts
├─ Depended on by: payment_processor, audit_logger
└─ Priority: HIGH (dependency count: 2)

config.ts (400 tokens)
├─ Depends on: nothing
├─ Depended on by: stripe_api, database
└─ Priority: CRITICAL (dependency count: 2)

BUDGET ALLOCATION:
✓ Keep: utils.ts (600), config.ts (400) = 1,000 tokens
✓ Keep: payment_processor.ts (1,200) = 1,200 tokens
✓ Keep: database.ts (1,100) = 1,100 tokens
⚠️  Compress: stripe_api.ts (800 → 200 tokens) = 200 tokens
──────────────────────────
Total: 3,500 tokens (vs 4,100 if keeping all)
Savings: 14% + preserves all critical dependencies
```

## Part 5: Troubleshooting Common Issues

### Issue: Score keeps pruning files I need

**Solution**: Adjust factor weights in scoring formula

```python
# Current (maybe too aggressive on recency)
score = (0.3 * recency) + (0.2 * frequency) + (0.4 * task_alignment) + (0.1 * dependency)

# Try: Reduce recency impact, increase dependency
score = (0.1 * recency) + (0.2 * frequency) + (0.4 * task_alignment) + (0.3 * dependency)
```

### Issue: Can't fit all critical files

**Solution**: Increase budget or split into subtasks

```
Current: 100K budget, 110K needed
Option 1: Increase budget to 120K if possible
Option 2: Split into subtasks:
  ├─ Task 1: "Implement payment" (40K budget)
  ├─ Task 2: "Build receipts" (40K budget)
  └─ Task 3: "Add reporting" (40K budget)
```

### Issue: Compression isn't saving enough

**Solution**: Use more aggressive techniques

```python
# Start gentle
1. Strip comments (15-35% savings)
2. Collapse whitespace (30-45% savings)

# If still over budget, get aggressive
3. Extract relevant sections (50-70% savings)
4. Summarize to pseudocode (85-95% savings)
5. Create external summary document + archive file
```

## Summary: Quick Reference

| Technique | Savings | Effort | Safety |
|-----------|---------|--------|--------|
| Strip comments | 15-35% | Low | Very safe |
| Collapse whitespace | 30-45% | Low | Very safe |
| Extract sections | 50-70% | Medium | Safe with review |
| Summarize code | 85-95% | Medium | Reference-only |
| Convert to pseudocode | 90%+ | Medium | Reference-only |

**Choose your strategy** based on project size and session length, then apply compression techniques to stay within budget.
