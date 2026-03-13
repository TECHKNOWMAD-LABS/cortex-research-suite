---
name: agent-orchestrator
description: >
  Multi-agent orchestration with parallel dispatch, dependency resolution,
  micro-checkpoints, and consensus protocols. Coordinates concurrent agent
  work with automatic failure recovery and output validation. Use when
  dispatching parallel agents, coordinating multi-agent work, or when
  "orchestrate", "parallel agents", "agent-orchestrator", "dispatch",
  "fan-out", or "coordinate agents" is mentioned.
---

# Multi-Agent Orchestration Engine

A complete orchestration system for managing parallel agent workflows with sophisticated task dependency resolution, micro-checkpoint recovery, and consensus-based output validation.

## Core Concepts

### Dispatch Patterns

#### Fan-Out
Dispatch N agents simultaneously for independent tasks.

**When to use**: 
- Multiple agents need to work on separate, non-dependent tasks
- Maximizing parallelism and reducing total execution time
- Gathering data from multiple sources in parallel

**Example**:
```
Coordinator dispatches:
- Agent A: Analyze market trends
- Agent B: Analyze competitor activity
- Agent C: Analyze internal capacity
All three run in parallel, then results merge
```

**Benefits**: Maximum parallelism, reduced latency, natural failure isolation

#### Pipeline
Chain agents sequentially; output of one feeds directly to the next.

**When to use**:
- Task B depends on output from Task A
- Progressive refinement (generate → review → summarize)
- Workflow requires ordered processing

**Example**:
```
Agent A (Research) → Agent B (Analyze) → Agent C (Synthesize)
Output: Research findings
Input to B: Research findings
Output: Analysis
Input to C: Analysis  
Output: Synthesized report
```

**Benefits**: Clear dependency management, natural information flow, easy debugging

#### Map-Reduce
Fan-out agents to gather/process data (map phase), then coordinator reduces results.

**When to use**:
- Need to gather data from multiple sources then synthesize
- Processing that naturally splits (partition data) then combines (aggregate)
- Distributed analysis problems

**Example**:
```
Map Phase:
- Agent A: Analyze Q1 data
- Agent B: Analyze Q2 data
- Agent C: Analyze Q3 data
- Agent D: Analyze Q4 data

Reduce Phase:
- Coordinator merges quarterly analyses into annual report
```

**Benefits**: Scalable data processing, isolation of map tasks, efficient reduce phase

#### Hierarchical
Coordinator dispatches specialist sub-agents, who may themselves coordinate further agents.

**When to use**:
- Complex workflows requiring multiple levels of coordination
- Different domains need different specialist clusters
- Flexible resource allocation and scoping

**Example**:
```
Orchestrator (Top Level)
├── Design Coordinator
│   ├── UX Designer
│   ├── Visual Designer
│   └── Interaction Designer
├── Development Coordinator
│   ├── Backend Engineer
│   ├── Frontend Engineer
│   └── DevOps Engineer
└── QA Coordinator
    ├── Test Engineer
    └── Performance Engineer
```

**Benefits**: Natural organizational structure, independent specialist teams, composable sub-orchestrations

## Task Graph Engine

The orchestrator uses a **Directed Acyclic Graph (DAG)** to represent task dependencies.

### Features

**Topological Sort**: Determines valid execution order respecting all dependencies.

**Critical Path Identification**: Identifies the longest dependency chain; reducing critical path time reduces overall execution time.

**Automatic Parallelization**: Tasks with no dependencies or completed dependencies are automatically scheduled in parallel.

**Deadlock Detection**: Identifies circular dependencies that would block forever, fails fast rather than hanging.

### Task Graph Representation

```json
{
  "tasks": {
    "task_1": {
      "agent": "agent_name",
      "depends_on": [],
      "timeout": 30,
      "retries": 3
    },
    "task_2": {
      "agent": "agent_name",
      "depends_on": ["task_1"],
      "timeout": 45,
      "retries": 2
    },
    "task_3": {
      "agent": "agent_name",
      "depends_on": ["task_1"],
      "timeout": 60,
      "retries": 3
    },
    "task_4": {
      "agent": "agent_name",
      "depends_on": ["task_2", "task_3"],
      "timeout": 30,
      "retries": 1
    }
  }
}
```

Task 1 runs first, then tasks 2 and 3 run in parallel (both depend only on task 1), then task 4 runs after both complete.

## Micro-Checkpoint Protocol

### Design

After each task completes, the orchestrator:

1. **Validates** the task output against expected schema
2. **Saves** a checkpoint (JSON file with task state)
3. **Updates** the task graph (marks task complete, unlocks dependents)
4. **Signals** downstream tasks (ready to run if dependencies met)

### Checkpoint Format

```json
{
  "task_id": "task_2",
  "agent_id": "analysis_agent",
  "status": "completed",
  "started_at": "2025-03-13T14:22:05Z",
  "completed_at": "2025-03-13T14:22:35Z",
  "duration_seconds": 30,
  "retries": 0,
  "outputs": {
    "summary": "...",
    "metrics": {...}
  },
  "validation": {
    "passed": true,
    "errors": []
  }
}
```

### Failure Recovery

If a task fails:

1. **Transient Failure** (network timeout, temporary unavailability):
   - Retry from the same task, using cached inputs
   - Exponential backoff: 2s, 4s, 8s, ... between attempts
   - No replay of previous tasks

2. **Persistent Failure** (logic error, incompatible output):
   - Task reassigned to backup agent if available
   - Otherwise marked as failed, downstream tasks notified
   - Graceful degradation: continue with alternative paths

### Checkpoint Usage

- **Resume after crash**: Load last checkpoint, continue from there
- **Distributed execution**: Checkpoint makes each task independently restartable
- **Audit trail**: Complete history of what ran, when, and with what results
- **Incremental execution**: Re-run only failed tasks and their dependents

## Consensus Protocol

When multiple agents work on overlapping concerns, the orchestrator uses consensus to merge or select outputs.

### Scoring Algorithm

Each agent's output is scored on:

- **Completeness**: Did it address all required aspects? (0-100)
- **Correctness**: Validates against known facts or schema (0-100)
- **Consistency**: Does it align with other agents' outputs? (0-100)
- **Recency**: How fresh is the data/analysis? (timestamp-based)

### Consensus Strategies

**Plurality Vote**: For discrete choices, pick the most-selected option.

**Scoring Merge**: Weight outputs by score; for numeric/percentages, use weighted average.

**Conflict Flag**: If top two outputs differ significantly, flag for human review rather than auto-merging.

**Best-of-Breed**: For different dimensions, pick best output per dimension and merge.

### Example

Three agents analyze market opportunity:

```
Agent A: "Market size $50M, grow 15% YoY, high competition"
  Completeness: 95  Correctness: 90  Consistency: 85

Agent B: "Market size $48M, grow 12% YoY, fragmented"
  Completeness: 90  Correctness: 85  Consistency: 90

Agent C: "Market size $52M, grow 18% YoY, consolidating"
  Completeness: 85  Correctness: 75  Consistency: 70

Consensus Result:
- Market size: $50M (weighted average of top-scored)
- Growth: 15% YoY (plurality of 15% vs 12% vs 18%)
- Competition: HIGH (consensus across all three)
- Flag for review: Growth rate varies (12-18%), human should verify
```

## Self-Healing Recovery

### Automatic Retry

- **Exponential Backoff**: 2s, 4s, 8s, 16s, 32s (capped at 5 minutes)
- **Jitter**: Add ±20% randomness to avoid thundering herd
- **Max Retries**: Configurable per task (default 3)

### Task Reassignment

If agent fails persistently:
- Check for backup agents with same capability
- Reassign task to backup
- Log reason for failover
- Continue orchestration

### Graceful Degradation

If task cannot be completed:
- Skip if optional (soft dependency)
- Continue with alternative path if available
- Report blocked downstream tasks
- Return partial results to coordinator

### Dead Letter Queue

Unrecoverable tasks are:
- Moved to dead letter queue
- Logged with full error context
- Require manual intervention to resolve
- Don't block entire orchestration

## Implementation

Use the provided `scripts/orchestrator.py` for:

- Loading task manifests from JSON
- Managing task graph and dependency resolution
- Parallel dispatch via threading
- Checkpoint persistence to JSON
- CLI for initialization, dispatch, status, retry, graph visualization
- Automatic failure recovery with exponential backoff

All operations are logged for audit trail and debugging.
