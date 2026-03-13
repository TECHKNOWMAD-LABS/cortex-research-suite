---
name: persistent-memory
description: >
  Enterprise persistent memory with progressive disclosure retrieval. Captures
  observations, decisions, errors, and context across sessions. Uses hybrid
  search (full-text + semantic scoring) for token-efficient recall. Use when
  "remember this", "what did we decide", "persistent-memory", "recall",
  "search memory", or "cross-session context" is mentioned.
---

# Persistent Memory System

An enterprise-grade memory management system for Claude that captures observations, decisions, and context across sessions. Built on progressive disclosure principles to minimize token overhead while maintaining semantic precision.

## Core Philosophy

Modern AI agents need persistent external memory that is:
- **Lossless**: Observations never degrade through retrieval cycles
- **Token-efficient**: Multi-layer retrieval prevents context bloat
- **Production-ready**: Queryable, auditable, structured storage
- **Privacy-aware**: Sensitive data can be marked for exclusion
- **Cross-session**: Observations persist across conversation boundaries

## Memory Capture System

### Automatic Observation Recording

The system captures structured observations during execution:

```json
{
  "observation_id": "obs_20260313_001a2b3c",
  "type": "tool_output|decision|error|file_change|context",
  "content": "Raw captured content from tool or decision point",
  "summary": "AI-powered 1-line semantic summary",
  "context": "Related project, task, or domain",
  "timestamp": "2026-03-13T14:22:45Z",
  "content_session_id": "user_conversation_id",
  "memory_session_id": "mem_20260313_ab12cd34",
  "project": "project_name",
  "tags": ["tag1", "tag2"],
  "token_estimate": 250,
  "private": false
}
```

### Observation Types

- **tool_output**: Results from function calls (API responses, command outputs)
- **decision**: Significant choices made during reasoning (architecture decisions, bug fixes)
- **error**: Failures, exceptions, and recovery strategies
- **file_change**: Notable modifications to files or structure
- **context**: Project state, environment setup, discovered patterns

### AI-Powered Compression

Large observations are semantically summarized:
- Full content stored with hash for integrity
- Retrieval always returns lossless original
- Compression is metadata-only (never destructive)
- Token estimates guide progressive disclosure

### Privacy Controls

Mark sensitive content with `<private>` tags:

```
Decision: Implemented OAuth flow. 
<private>Used credentials: aws_key_xxx, client_secret_yyy</private>
Implementation stored in /config/auth.py
```

Privacy-tagged portions are:
- Never included in search indexes
- Excluded from public exports
- Still stored for session-local recall
- Explicitly marked in retrieval results

## Progressive Disclosure Retrieval (3-Layer)

The system uses a 3-layer retrieval strategy to balance recall precision with token efficiency.

### Layer 1: SEARCH INDEX
**Purpose**: Fast, lightweight initial query results  
**Return Format**: Observation ID + 1-line summary + metadata  
**Token Cost**: ~50 tokens per result  
**Use Case**: "What do we know about X?" initial exploration

```
[obs_20260313_001] Auth system uses OAuth2 with PKCE
[obs_20260312_fff] Database migration: users table schema updated
[obs_20260311_aaa] Error: CORS policy blocking API calls from frontend
```

Each result includes:
- Observation ID (for direct retrieval)
- Summary (semantic 1-liner)
- Type badge (decision/error/tool_output)
- Match score (text + semantic combined)
- Timestamp

### Layer 2: TIMELINE
**Purpose**: Chronological context around matches  
**Return Format**: 5-observation window before/after match  
**Token Cost**: ~200 tokens per window  
**Use Case**: "What led to this decision?" understanding causality

Shows causality and sequence:

```
[obs_20260310_xxx] Setup PostgreSQL database
[obs_20260310_yyy] Created initial schema
[obs_20260311_zzz] ← ERROR: CORS policy blocking API calls ← You are here
[obs_20260311_aaa] Decision: Added CORS middleware to API
[obs_20260311_bbb] Testing completed, CORS now working
```

Explicitly displays:
- Temporal sequence (before/after)
- Type indicators (error → decision → validation pattern)
- How previous context led to the current observation
- What downstream effects followed

### Layer 3: FULL DETAIL
**Purpose**: Complete observation content for deep analysis  
**Return Format**: Full structured observation JSON  
**Token Cost**: Variable (typically 300-800 tokens)  
**Use Case**: "Give me everything about this decision" detailed review

Returns complete context:
- Full original content (uncompressed)
- All metadata and tags
- Related observations (linked by project/session)
- Integrity hash and storage path
- Full formatting and code blocks preserved

### Token Cost Transparency

Every retrieval explicitly shows token estimates:

```
Search results: 5 matches (estimated 250 tokens)
Layer 2 timeline: obs_20260311_zzz (estimated 220 tokens)
Total cost so far: 470 tokens. Layer 3 detailed retrieval will cost ~600 additional tokens.
```

Users can decide whether to pay the retrieval cost before fetching full details.

## Hybrid Search Engine

Combines full-text and semantic similarity for precision recall.

### Full-Text Search (TF-IDF)

Indexes observation summaries and content:
- Tokenizes on word boundaries and common separators
- Removes stopwords (the, a, an, is, etc.)
- Weights term frequency × inverse document frequency
- Boosts exact phrase matches

Example:
```
Query: "OAuth implementation"
- "OAuth" appears in 3 observations (higher IDF)
- "implementation" appears in 120 observations (lower IDF)
- Result: Observations mentioning both are scored highest
```

### Semantic Similarity (Keyword Overlap + Synonym Expansion)

Simulates embedding-based similarity using keyword networks:
- Extracts key noun phrases from query and observations
- Expands with synonym clusters (decided/chose, error/failure, API/endpoint)
- Measures semantic distance based on shared terms
- Weights key concepts higher than background terms

Example:
```
Query: "why did we choose React?"
Expands to: {decided, React, framework, choose, frontend, UI}
Matches observations with: React, frontend, framework, UI library, etc.
Semantic score: 0.72 (high overlap despite synonym differences)
```

### Combined Ranking

Final score combines both signals:

```
final_score = 0.6 * text_score + 0.4 * semantic_score
```

Weighting:
- Text score (60%): Exact term matches, phrase proximity
- Semantic score (40%): Concept similarity, synonym matches
- Combined approach: Avoids both false positives (semantic only) and missed concepts (text only)

### Search Filters

All queries support optional filters:

```python
search(
    query="authentication",
    project="api-backend",        # Limit to project
    session_id="mem_20260313",    # Specific session
    observation_type="decision",  # Only decisions, not errors
    start_date="2026-03-01",      # Date range
    end_date="2026-03-13",
    exclude_private=True          # Skip sensitive content
)
```

## Session Tracking

Maintains dual session context for proper observation lifecycle.

### Dual Session IDs

- **content_session_id**: User's conversation thread ID (from Claude context)
  - Preserves immediate conversation context
  - Groups related interactions from same chat
  
- **memory_session_id**: Internal memory system ID
  - Persists across user conversation boundaries
  - Enables cross-session continuity
  - Format: `mem_YYYYMMDD_8hexchars` (e.g., `mem_20260313_ab12cd34`)

### Cross-Session Continuity

Observations are independent of conversation lifecycle:
- First session ends → observations remain accessible
- New session begins → can query all prior observations
- Search spans all sessions by default
- Can filter to specific sessions if needed

### Session Management

```python
# Start new memory context
session_id = start_session(project="api-backend")

# Record observations during work
save_observation(
    type="decision",
    content="Chose async/await over callbacks",
    context="api-backend",
    session_id=session_id
)

# End session (marks as complete, doesn't delete observations)
end_session(session_id)

# Later: Resume work, observations are still there
resume_session(project="api-backend")
search(query="async", project="api-backend")  # Finds prior observations
```

### Project-Level Grouping

Observations organized by project context:
- Single project isolation: "Show me all decisions in payment-processor"
- Multi-project view: "Search across all my projects"
- Prevents noise from unrelated work
- Enables project-specific memory archives

## Implementation Details

The system is implemented in `scripts/memory_engine.py` with:

- **Database**: SQLite with FTS5 virtual table for full-text search
- **Storage**: Structured JSON observations with integrity hashes
- **CLI**: Command-line interface for save, search, retrieve operations
- **Export/Import**: JSON-based backup and restore functionality

See `references/memory-patterns.md` for detailed usage patterns and token budgeting strategies.

## Usage Examples

### Capturing a Decision

```python
from memory_engine import save_observation

save_observation(
    observation_type="decision",
    content="""Decision: Use PostgreSQL instead of MongoDB
    Reasoning: Strong consistency requirements for payments
    Trade-off: Lose flexible schema, gain ACID guarantees""",
    context="database-selection",
    project="payment-system"
)
```

### Searching for Context

```python
from memory_engine import search_index, get_timeline, get_full

# Quick search
results = search_index("payment validation", limit=5)
# Returns 5 lightweight results

# Get context around a result
timeline = get_timeline(results[0]['observation_id'])
# Shows before/after context

# Get full details if needed
full = get_full(results[0]['observation_id'])
# Returns complete observation
```

### Tracking Errors and Recovery

```python
save_observation(
    observation_type="error",
    content="""CORS error: XMLHttpRequest blocked by CORS policy
    Location: API call from frontend origin http://localhost:3000
    Resolution: Added CORS middleware to Express server""",
    context="api-integration",
    project="frontend-api"
)

# Later: query what we learned
search_index("CORS blocked")
```

## Best Practices

1. **Observation Size**: Keep individual observations focused (100-500 words typical)
2. **Tagging**: Use consistent project names for grouping
3. **Timestamps**: System auto-records; focus on accurate content
4. **Privacy**: Mark sensitive data with `<private>` tags
5. **Search Queries**: Be specific; "OAuth bug" better than just "bug"
6. **Layer Selection**: Start with Layer 1, escalate to Layer 2/3 as needed
7. **Session Naming**: Use descriptive project names for cross-session recall
