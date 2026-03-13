# Memory Patterns and Best Practices

Enterprise persistent memory requires disciplined patterns to maximize recall precision while maintaining token efficiency.

## Progressive Disclosure Pattern

The 3-layer retrieval system is designed to be used sequentially, with each layer providing deeper detail only when needed.

### When to Use Each Layer

**Layer 1: SEARCH INDEX** — Use first
- Quick scanning of what you know about a topic
- Cost: ~50 tokens per result
- Goal: Find relevant observations IDs and summaries
- Next step: Decide if you need context

Example workflow:
```python
# Initial search
results = engine.search("authentication bug", project="api")
# Returns: 5 observation IDs with 1-line summaries

# Examine summaries, pick the most relevant
picked_id = results['results'][0]['observation_id']
```

**Layer 2: TIMELINE** — Use when you need context
- Understand causality and sequence
- Cost: ~200 tokens per window
- Goal: See what led to and followed the observation
- When to use: "Why did we make this decision?"

Example workflow:
```python
# Get context around specific observation
timeline = engine.get_timeline(picked_id)
# Shows 5 observations before/after

# Understand the decision chain
for ctx in timeline['context_window']:
    print(f"{ctx['timestamp']}: {ctx['type']} - {ctx['summary']}")
```

**Layer 3: FULL DETAIL** — Use only when necessary
- Complete uncompressed content
- Cost: Variable, typically 300-800 tokens
- Goal: Review full original content
- When to use: "I need to re-read the exact implementation"

Example workflow:
```python
# After examining Layer 1 and 2, if you need full content:
full = engine.get_full(picked_id)
print(full['observation']['content'])
# Read entire original content
```

### Token Budgeting Strategy

Track cumulative token cost across layers:

```
Available context: 2000 tokens
- Layer 1 search (5 results): 250 tokens → 1750 remaining
- Layer 2 timeline: 220 tokens → 1530 remaining
- Layer 3 full detail: 400 tokens → 1130 remaining

Total cost for complete recall: 870 tokens
Remaining budget: 1130 tokens for rest of session
```

Always check token estimates before escalating to next layer.

## Observation Design Patterns

### Pattern 1: Decision with Rationale

Capture decisions with reasoning for future understanding.

```python
engine.save_observation(
    observation_type="decision",
    project="payment-system",
    context="database-selection",
    summary="Selected PostgreSQL over MongoDB for consistency",
    content="""
    Decision: Use PostgreSQL instead of MongoDB
    
    Requirements:
    - Financial transactions require ACID guarantees
    - Strong consistency non-negotiable for payments
    - Schema stability over flexibility
    
    Trade-offs Considered:
    - MongoDB: Flexible schema, horizontal scaling ease
    - PostgreSQL: Rigid schema, excellent transaction support, mature ecosystem
    
    Rationale:
    We cannot afford data inconsistency in payment processing. ACID guarantees
    are fundamental to our architecture. PostgreSQL with proper indexing will
    handle our transaction volume. The schema flexibility of MongoDB is not worth
    the consistency risk.
    
    Related: See error obs_20260310_xxx (previous consistency issues)
    """
)
```

Key points:
- Summary is actionable and specific
- Full content explains the "why" not just "what"
- References related observations for traceability
- Rationale survives across sessions

### Pattern 2: Error with Recovery

Document errors and how you resolved them for pattern recognition.

```python
engine.save_observation(
    observation_type="error",
    project="frontend-api",
    context="api-integration",
    summary="CORS policy blocked XMLHttpRequest from frontend origin",
    content="""
    Error: CORS Policy Violation
    Location: frontend/src/services/api.js
    Browser: Chrome 89, Firefox 88 (verified)
    
    Symptom:
    XMLHttpRequest blocked by CORS policy:
    No 'Access-Control-Allow-Origin' header present on requested resource
    
    Root Cause:
    API server not configured to accept requests from http://localhost:3000
    
    Investigation:
    1. Verified frontend is running at http://localhost:3000
    2. API is at http://localhost:5000
    3. Difference in origin (different ports) triggers CORS check
    4. API missing CORS middleware
    
    Solution:
    Added Express CORS middleware to API:
    ```javascript
    const cors = require('cors');
    app.use(cors({
        origin: 'http://localhost:3000',
        credentials: true
    }));
    ```
    
    Testing:
    ✓ Frontend can now call API
    ✓ Credentials (cookies) pass correctly
    ✓ Tested in Chrome, Firefox, Safari
    
    Lessons Learned:
    - CORS is per-origin (scheme + host + port)
    - Localhost:3000 ≠ localhost:5000
    - Whitelist only specific origins in production
    """
)
```

Key points:
- Describes symptom, root cause, solution sequentially
- Includes investigation steps (helpful if error recurs)
- Documents verification/testing
- Captures lessons for future reference

### Pattern 3: File Change with Context

Track significant file modifications and their rationale.

```python
engine.save_observation(
    observation_type="file_change",
    project="api-backend",
    context="authentication",
    summary="Refactored auth middleware into separate module",
    content="""
    File Change: Extracted auth.js middleware
    
    Files Modified:
    - server.js: Removed inline auth logic (~50 lines)
    - middleware/auth.js: NEW - centralized auth logic
    - middleware/index.js: NEW - exports all middleware
    
    Before:
    server.js had inline authentication logic mixed with route setup.
    Difficult to test, hard to reuse across projects.
    
    After:
    middleware/auth.js exports validateJWT, checkPermissions functions.
    server.js now just calls app.use(validateJWT).
    
    Benefits:
    - Testable in isolation (unit tests possible)
    - Reusable in other Express servers
    - Cleaner separation of concerns
    - Easier onboarding for new developers
    
    Testing:
    ✓ All existing tests still pass
    ✓ Auth behavior unchanged
    ✓ Verified CORS + auth work together
    """
)
```

Key points:
- Clear before/after comparison
- Lists specific files and nature of change
- Explains rationale (testability, reusability, etc)
- Verifies no regression

### Pattern 4: Context - Project State Snapshot

Periodically capture high-level project understanding.

```python
engine.save_observation(
    observation_type="context",
    project="myapp",
    context="project-state",
    summary="Architecture: PostgreSQL backend, React frontend, Express API",
    content="""
    Project Architecture Snapshot - 2026-03-13
    
    Technology Stack:
    - Frontend: React 18, Redux Toolkit, axios
    - Backend: Node.js/Express 4, PostgreSQL 13
    - Authentication: JWT via httpOnly cookies
    - Deployment: Docker containers, Kubernetes
    
    Key Decisions:
    1. PostgreSQL for data consistency (see decision obs_xxx)
    2. Express for lightweight API (see timeline obs_yyy)
    3. React for reactive UI (component state in Redux)
    
    Current Status:
    - Frontend: Mostly complete, auth flows working
    - API: Basic routes done, pagination pending
    - Database: Schema stable, migrations under version control
    
    Known Issues:
    - CORS configuration in development (documented obs_zzz)
    - Need API rate limiting before production
    
    Next Steps:
    - Implement rate limiting middleware
    - Add API documentation (Swagger)
    - Security audit before launch
    """
)
```

Key points:
- High-level overview useful for onboarding
- References other observations for details
- Lists known issues for future reference
- Clear next steps

## Hybrid Search Strategies

### Strategy 1: Narrow Query for Specificity

Specific queries return more relevant results.

```python
# Good: Specific
engine.search("JWT authentication error", project="api")

# Bad: Too broad
engine.search("error", project="api")  # Returns all errors

# Good: Specific terms
engine.search("CORS middleware Express", project="api")

# Bad: Too vague
engine.search("web", project="api")  # Matches everything
```

### Strategy 2: Technical Terms + Decision Keywords

Combine what happened with decision context.

```python
# Find a specific problem and solution
engine.search("OAuth PKCE implementation decision", project="auth")

# Find error patterns
engine.search("database connection timeout error recovery", project="backend")

# Find architectural choices
engine.search("microservices vs monolith decision rationale", project="architecture")
```

### Strategy 3: Date Range Filtering

Filter by time period when you remember roughly when something happened.

```python
# "What did we do last week?"
results = engine.search(
    "authentication",
    project="auth",
    start_date="2026-03-06",
    end_date="2026-03-13"
)

# "Recent decisions"
results = engine.search(
    "decision",
    observation_type="decision",
    start_date="2026-03-01"
)
```

### Strategy 4: Type-Specific Searches

Focus on specific observation types.

```python
# Only show decisions, not errors
decisions = engine.search(
    "API authentication",
    project="api",
    observation_type="decision"
)

# Only show errors in this context
errors = engine.search(
    "CORS",
    project="frontend-api",
    observation_type="error"
)

# Show file changes in specific area
changes = engine.search(
    "authentication",
    observation_type="file_change"
)
```

## Privacy Patterns

### Pattern 1: Sensitive Data Exclusion

Use `<private>` tags for credentials and secrets.

```python
engine.save_observation(
    observation_type="decision",
    project="backend",
    context="deployment",
    content="""
    Decision: Set up AWS S3 bucket for file uploads
    
    Configuration:
    - Bucket name: company-uploads
    - Region: us-east-1
    
    <private>
    Credentials used:
    - AWS_ACCESS_KEY_ID: AKIA...
    - AWS_SECRET_ACCESS_KEY: wJa...
    - S3_BUCKET_ARN: arn:aws:s3:::company-uploads
    </private>
    
    Policy: Only authenticated users can upload
    """,
    private=False  # Body is private, but observation is public
)
```

### Pattern 2: Mixed Public/Private Content

Structure observations to isolate sensitive data.

```python
# Good: Isolates secrets
content = """
Setup: Database backup to S3
- Schedule: Daily at 2 AM UTC
- Retention: 30 days
<private>AWS_ACCESS_KEY_ID: AKIA...</private>
- Tested with backup test on 2026-03-12
"""

# Bad: Secrets mixed throughout
content = """
AWS_ACCESS_KEY_ID: AKIA... (in file /config/.env)
Using bucket company-backups
AWS_SECRET_ACCESS_KEY: wJa...
Runs daily at 2 AM
"""
```

### Pattern 3: Exclude Sensitive Observations

Mark entire observations as private if they're sensitive.

```python
engine.save_observation(
    observation_type="context",
    project="infra",
    context="production-secrets",
    content="Production database connection strings and API keys",
    private=True  # Entire observation is excluded from searches
)
```

## Export/Import Patterns

### Pattern 1: Project Backups

Export entire project memory before major changes.

```bash
# Backup before refactoring
python3 memory_engine.py export api-backend --output api-backup-2026-03-13.json

# Review what was backed up
cat api-backup-2026-03-13.json | head -50

# If something goes wrong, restore
python3 memory_engine.py import api-backup-2026-03-13.json
```

### Pattern 2: Cross-Project Knowledge Transfer

Export learnings from one project, import to another.

```bash
# Learn from authentication patterns in project-a
python3 memory_engine.py export project-a-auth --output auth-learnings.json

# Adapt and import to project-b
python3 memory_engine.py import auth-learnings.json  # Creates obs in project-b
```

### Pattern 3: Knowledge Base Curation

Archive valuable observations for reference.

```bash
# Export decisions only
python3 memory_engine.py search "decision" --project api | \
  grep observation_id > important-decisions.txt

# Later: Batch export those specific obs for documentation
# (Requires custom script, but pattern is established)
```

## Session Management Patterns

### Pattern 1: Per-Project Sessions

Use sessions to isolate work context.

```python
# Start work on feature
session = engine.start_session(project="payment-feature")

# Capture observations during development
engine.save_observation(..., session_id=session)
engine.save_observation(..., session_id=session)

# End feature work
engine.end_session(session)

# Later: Resume work, access same session's history
new_session = engine.resume_session(project="payment-feature")
```

### Pattern 2: Context Switching

Quick context switch between projects.

```python
# Working on auth
auth_session = engine.start_session(project="authentication")

# Context switch: Working on payments
pay_session = engine.start_session(project="payments")

# Can search both project separately
auth_results = engine.search("JWT", project="authentication")
pay_results = engine.search("validation", project="payments")

# Different observations organized by project and session
```

### Pattern 3: Session-Scoped Recall

Get all observations from a specific work session.

```python
# List everything from a session
observations = engine.list_observations(session_id=session_id)

# Find all decisions made in a specific session
session_decisions = [
    obs for obs in observations
    if obs.observation_type == "decision"
]

# Useful for: reviewing what you decided in a focused work block
```

## Performance Tuning

### Observation Size Guidelines

- **Too small** (<50 words): No useful detail, excessive overhead
- **Ideal** (100-500 words): Captures full context, fast to retrieve
- **Too large** (>2000 words): Should be split into multiple observations
- **Very large** (>5000 words): Definitely split; one observation per concern

### Batch Operations

For bulk operations, create a helper script:

```python
# Process multiple observations
observations = [
    {
        "type": "decision",
        "content": "...",
        "project": "api",
        "context": "rate-limiting"
    },
    # ... more observations
]

session = engine.start_session(project="api")
for obs in observations:
    engine.save_observation(
        observation_type=obs["type"],
        content=obs["content"],
        project=obs["project"],
        context=obs["context"],
        session_id=session
    )
```

### Search Optimization

- **Pre-filter by project**: Reduces search space by 90%
- **Use type filter**: Narrows results when you know what type you want
- **Be specific in query**: Exact terms > broad keywords
- **Limit results**: Start with limit=5, expand if needed

## Common Pitfalls to Avoid

1. **Too Vague Summaries**: "Fixed bug" vs "Fixed race condition in auth token refresh"
2. **Missing Context**: Observation records what happened, not why
3. **Privacy Slip**: Accidentally including credentials in public observations
4. **Orphaned Observations**: Observations not linked to any project
5. **Inconsistent Tagging**: Same concept called 3 different ways
6. **Oversized Observations**: 3000-word observation better as 3 focused ones
7. **Time Lag**: Recording observations days later loses detail
8. **No Summary Discipline**: Storing raw logs without semantic summary

## Recommended Workflow

1. **During work**: Capture observations in real-time, brief notes
2. **After decision**: Expand summary with rationale while fresh
3. **End of session**: Review observations captured, add missing context
4. **Weekly**: Search recent work, identify patterns
5. **Before similar work**: Search for related prior observations
6. **Before deployment**: Export project, backup current state

This discipline ensures your persistent memory remains valuable across projects and time.
