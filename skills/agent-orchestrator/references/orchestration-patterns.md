# Orchestration Patterns

This guide covers the four primary patterns for coordinating multi-agent work.

## 1. Fan-Out Pattern

**Pattern**: Dispatch N agents simultaneously for independent, parallel work.

### Structure

```
Coordinator
├── Agent A (Task 1)
├── Agent B (Task 2)
├── Agent C (Task 3)
└── Agent D (Task 4)

All agents run in parallel.
Coordinator waits for all to complete, then aggregates results.
```

### When to Use

- **Multiple independent tasks**: No task depends on output from another
- **Latency-sensitive**: Need results quickly; parallelism reduces total time
- **Data gathering**: Collecting information from multiple sources
- **Horizontal scaling**: Each agent handles one piece of a larger problem

### Real-World Examples

#### Market Analysis
```
Coordinator dispatches:
- Agent A: Analyze competitor pricing
- Agent B: Analyze market trends
- Agent C: Analyze customer sentiment
- Agent D: Analyze regulatory changes

All four agents research simultaneously.
Result: Comprehensive market report combining all perspectives.
```

#### Parallel Code Review
```
Coordinator dispatches:
- Agent A: Reviews security aspects
- Agent B: Reviews performance aspects
- Agent C: Reviews code style
- Agent D: Reviews test coverage

All four review in parallel.
Result: Multi-dimensional code feedback combined.
```

#### Media Processing
```
Coordinator dispatches:
- Agent A: Generate thumbnail
- Agent B: Generate metadata
- Agent C: Generate transcript
- Agent D: Generate tags

All four process simultaneously.
Result: Complete media object with all derived content.
```

### Advantages

- **Maximum parallelism**: No waiting for dependencies
- **Natural fault isolation**: One agent failing doesn't directly block others
- **Easy horizontal scaling**: Add more agents/tasks without changing coordinator logic
- **Clean results aggregation**: Combine independent outputs

### Disadvantages

- **No dependency ordering**: Can't use one agent's output as another's input
- **Resource contention**: All agents compete for system resources
- **Aggregation complexity**: Merging N independent outputs requires logic
- **All-or-nothing**: If one required task fails, entire fan-out may fail

### Implementation Checklist

- [ ] Identify independent tasks with no data dependencies
- [ ] Dispatch all agents to task queue
- [ ] Spawn worker threads (typically one per core, up to N agents)
- [ ] Collect outputs as agents complete
- [ ] Aggregate/merge results in coordinator
- [ ] Handle partial failures gracefully

---

## 2. Pipeline Pattern

**Pattern**: Chain agents sequentially; output of one feeds directly to the next.

### Structure

```
Task 1 (Agent A) 
  → Task 2 (Agent B)  [uses output from Task 1]
  → Task 3 (Agent C)  [uses output from Task 2]
  → Task 4 (Agent D)  [uses output from Task 3]

Each task blocks until its predecessor completes.
Data flows linearly through the pipeline.
```

### When to Use

- **Sequential dependencies**: Each task must use prior task's output
- **Progressive refinement**: Generate, then review, then polish
- **Workflow with clear stages**: Each stage transforms data
- **Data transformation**: ETL (extract, transform, load) patterns

### Real-World Examples

#### Document Processing Pipeline
```
Task 1: Agent A uploads document (Extract)
  ↓
Task 2: Agent B parses content (Transform)
  ↓
Task 3: Agent C enriches with metadata (Enrich)
  ↓
Task 4: Agent D stores in knowledge base (Load)

Output of Task 1 (raw document) → input to Task 2
Output of Task 2 (structured data) → input to Task 3
Output of Task 3 (enriched data) → input to Task 4
```

#### Content Creation Pipeline
```
Task 1: Agent A generates outline
  ↓
Task 2: Agent B writes draft based on outline
  ↓
Task 3: Agent C edits for clarity
  ↓
Task 4: Agent D formats for publication

Output flows: outline → draft → edited → formatted
```

#### Data Analysis Pipeline
```
Task 1: Agent A fetches raw data
  ↓
Task 2: Agent B cleans and normalizes
  ↓
Task 3: Agent C computes statistics
  ↓
Task 4: Agent D generates visualizations

Output flows: raw → clean → analyzed → visualized
```

#### Software Build Pipeline
```
Task 1: Agent A compiles code
  ↓
Task 2: Agent B runs unit tests
  ↓
Task 3: Agent C runs integration tests
  ↓
Task 4: Agent D deploys to staging

Output flows: source → binary → test results → deployment
```

### Advantages

- **Natural data flow**: Clear input→process→output for each stage
- **Easy to debug**: Each stage's input and output is explicit
- **Resource efficient**: Only one agent active at a time
- **Progressive refinement**: Each stage builds on prior work
- **Clear error handling**: Know exactly where failures occur

### Disadvantages

- **No parallelism**: Total time = sum of all stages
- **Brittle dependencies**: One stage failure blocks everything downstream
- **Coupling between stages**: Changes to one stage may require upstream/downstream changes
- **Throughput limited**: Can only process one item at a time

### Implementation Checklist

- [ ] Define sequential task order respecting dependencies
- [ ] Implement output validation for each stage (output becomes next input)
- [ ] Add checkpoints after each stage for recovery
- [ ] Implement error handling with graceful degradation
- [ ] Log input and output of each stage for debugging
- [ ] Consider retry logic for transient failures at each stage

---

## 3. Map-Reduce Pattern

**Pattern**: Fan-out agents to process (map) data, then coordinator reduces (synthesizes) results.

### Structure

```
Map Phase:
Coordinator
├── Agent A (maps over dataset partition 1)
├── Agent B (maps over dataset partition 2)
├── Agent C (maps over dataset partition 3)
└── Agent D (maps over dataset partition 4)

Reduce Phase:
Coordinator aggregates/synthesizes all map outputs
```

### When to Use

- **Large dataset processing**: Partition data, process in parallel
- **Gather then synthesize**: Collect data from multiple sources, then combine
- **Distributed computation**: Problem naturally partitions into sub-problems
- **Scalable analytics**: Process-per-partition scales horizontally

### Real-World Examples

#### Quarterly Business Review
```
Map Phase:
- Agent A analyzes Q1 data
- Agent B analyzes Q2 data
- Agent C analyzes Q3 data
- Agent D analyzes Q4 data

Reduce Phase:
Coordinator synthesizes quarterly analyses into annual report:
- Trends across all quarters
- Year-over-year comparisons
- Recommendations for next year

Benefit: Each quarter analyzed in parallel; synthesis happens once.
```

#### Multi-Region Data Processing
```
Map Phase:
- Agent A processes North America region data
- Agent B processes Europe region data
- Agent C processes Asia region data
- Agent D processes South America region data

Reduce Phase:
Coordinator combines regional reports into global analysis:
- Global patterns
- Regional differences
- Cross-regional opportunities

Benefit: Regions processed in parallel; global insights synthesized once.
```

#### Web Content Aggregation
```
Map Phase:
- Agent A scrapes source 1 (news site)
- Agent B scrapes source 2 (blog)
- Agent C scrapes source 3 (social)
- Agent D scrapes source 4 (forums)

Reduce Phase:
Coordinator synthesizes into unified report:
- Sentiment analysis across sources
- Trend identification
- Conflict resolution
- Curated summary

Benefit: All sources gathered in parallel; synthesis happens once.
```

#### Search Index Generation
```
Map Phase:
- Agent A indexes documents 1-1000
- Agent B indexes documents 1001-2000
- Agent C indexes documents 2001-3000
- Agent D indexes documents 3001-4000

Reduce Phase:
Coordinator merges all indices:
- Deduplicates entries
- Resolves conflicts
- Builds final index

Benefit: Indexing parallelized; final merge is efficient.
```

### Advantages

- **Parallelism in map phase**: Multiple agents process independently
- **Scalability**: Add more map agents as dataset grows
- **Natural partitioning**: Divide data by region, time, category, etc.
- **Efficient reduce**: Reduce operates on summarized outputs, not raw data
- **Fault isolation**: One map agent failure doesn't stop others

### Disadvantages

- **Partitioning overhead**: Must split data appropriately
- **Reduce complexity**: Merging outputs requires careful logic
- **Imbalanced load**: If partitions are uneven, some agents idle
- **Data skew**: Some partitions may have much more data than others

### Implementation Checklist

- [ ] Identify natural data partition boundaries
- [ ] Split dataset into N roughly-equal partitions
- [ ] Dispatch map agents (one per partition)
- [ ] Collect map outputs as agents complete
- [ ] Merge outputs in reduce phase (merge algorithm depends on data type)
- [ ] Validate final reduced result
- [ ] Handle stragglers (slow map agents) gracefully

---

## 4. Hierarchical Pattern

**Pattern**: Coordinator dispatches specialist sub-agents, who may themselves coordinate further agents.

### Structure

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

Each coordinator manages its own team.
Top-level orchestrator manages coordinators.
Nested coordination at multiple levels.
```

### When to Use

- **Complex workflows requiring multiple domains**: Design, dev, QA, ops
- **Specialist teams**: Each domain has its own coordinator and specialists
- **Scalable org structure**: Can add specialists under coordinators
- **Decentralized control**: Each coordinator is autonomous within its domain
- **Flexible resource allocation**: Specialists allocated to coordinators as needed

### Real-World Examples

#### Product Launch Orchestration
```
Launch Orchestrator
├── Content Coordinator
│   ├── Technical Writer
│   ├── Marketing Writer
│   └── Social Media Writer
├── Engineering Coordinator
│   ├── Platform Engineer
│   ├── Infrastructure Engineer
│   └── Release Engineer
├── Marketing Coordinator
│   ├── Email Campaign Agent
│   ├── Ad Campaign Agent
│   └── PR Agent
└── Support Coordinator
    ├── Help Center Agent
    ├── FAQ Agent
    └── Knowledge Base Agent

Each coordinator:
- Receives launch timeline from orchestrator
- Manages its own team's deliverables
- Reports back with status

Benefits:
- Content team works independently on messaging
- Engineering works independently on deployment
- Marketing works independently on campaign
- Support prepares independently for launch
```

#### Research Project Orchestration
```
Project Orchestrator
├── Literature Review Coordinator
│   ├── Senior Researcher A
│   ├── Junior Researcher B
│   └── Data Librarian
├── Experiments Coordinator
│   ├── Lab Manager
│   ├── Equipment Specialist
│   └── Data Collector
├── Analysis Coordinator
│   ├── Statistician
│   ├── Visualization Specialist
│   └── Data Analyst
└── Writing Coordinator
    ├── Lead Author
    ├── Co-Author
    └── Editor

Each coordinator:
- Manages its phase of research
- Coordinates with other phases
- Reports progress to project orchestrator
```

#### Enterprise System Migration
```
Migration Orchestrator
├── Data Migration Coordinator
│   ├── ETL Developer
│   ├── Data Quality Specialist
│   └── Database Admin
├── Application Coordinator
│   ├── Backend Integration Dev
│   ├── Frontend Adapter Dev
│   └── API Migration Dev
├── Infrastructure Coordinator
│   ├── Network Engineer
│   ├── Security Engineer
│   └── Ops Engineer
└── Testing Coordinator
    ├── Test Automation Dev
    ├── Performance Tester
    └── User Acceptance Tester

Each coordinator:
- Manages its migration workstream
- Coordinates dependencies with other workstreams
- Runs its own mini-orchestrations
```

#### Customer Onboarding Workflow
```
Onboarding Orchestrator
├── Account Setup Coordinator
│   ├── Account Creation Agent
│   ├── Billing Setup Agent
│   └── Access Provisioning Agent
├── Training Coordinator
│   ├── Technical Training Agent
│   ├── Compliance Training Agent
│   └── Process Training Agent
├── Integration Coordinator
│   ├── API Integration Agent
│   ├── Data Sync Agent
│   └── Webhook Setup Agent
└── Success Coordinator
    ├── Kickoff Meeting Agent
    ├── Success Plan Agent
    └── First Check-in Agent

Each coordinator:
- Manages its onboarding phase
- Works in parallel with other coordinators
- Reports completion back to orchestrator
```

### Advantages

- **Natural org structure**: Mirrors actual team structure
- **Autonomy**: Each coordinator is independent within its domain
- **Scalability**: Add specialists under coordinators as needed
- **Parallel domains**: Design, dev, QA can work simultaneously
- **Composable**: Can reuse sub-orchestrations in other projects
- **Fault isolation**: Failure in one domain doesn't directly impact others

### Disadvantages

- **Coordination overhead**: Communicating between domains adds complexity
- **Dependency tracking**: Cross-domain dependencies must be explicit
- **Eventual consistency**: Results from different domains may need merging
- **More moving parts**: More entities to monitor and debug
- **Latency**: Hierarchical dispatch may add overhead

### Implementation Checklist

- [ ] Identify natural domain boundaries (design, dev, ops, etc.)
- [ ] Create coordinator for each domain
- [ ] Within each domain, create specialist agents
- [ ] Define coordination contracts (what each coordinator produces/requires)
- [ ] Implement inter-coordinator communication (status updates, dependency signals)
- [ ] Add cross-domain checkpoints for recovery
- [ ] Handle misalignment between domain timelines
- [ ] Test failure scenarios across domains

---

## Pattern Selection Guide

| Pattern | Best For | Parallelism | Complexity | When to Use |
|---------|----------|------------|-----------|-----------|
| **Fan-Out** | Independent tasks | High | Low | Multiple agents, no dependencies |
| **Pipeline** | Sequential work | None | Low | Progressive refinement, transformation |
| **Map-Reduce** | Large dataset processing | High | Medium | Partition data, gather results |
| **Hierarchical** | Multi-domain work | High | High | Complex projects, many teams |

### Decision Tree

```
Do tasks depend on each other?
  ├─ NO (all independent)
  │   └─ Use: FAN-OUT
  │
  └─ YES (some dependencies)
      ├─ Linear chain (A→B→C→D)?
      │   └─ Use: PIPELINE
      │
      └─ Partition data then merge?
          ├─ YES
          │   └─ Use: MAP-REDUCE
          │
          └─ Complex multi-domain?
              └─ Use: HIERARCHICAL
```

---

## Hybrid Patterns

Real-world orchestrations often combine patterns:

### Pipeline of Fan-Outs
```
Stage 1: Fan-out 4 agents to gather data
         ↓ (all complete)
Stage 2: Pipeline agent processes combined data
         ↓
Stage 3: Fan-out 3 agents to apply transformations
```

### Hierarchical with Map-Reduce
```
Top-level Coordinator
├── Data Coordinator (runs map-reduce internally)
├── Analysis Coordinator (runs map-reduce internally)
└── Reporting Coordinator
```

### Fan-Out with Pipeline Results
```
Stage 1: Fan-out 4 agents to gather data
         ↓ (all complete)
Stage 2: Pipeline transformation chain on combined data
```

## Conclusion

Choose patterns based on:

1. **Dependency structure**: Are tasks independent or chained?
2. **Scale**: How many agents? How much data?
3. **Org structure**: Are there natural domains/teams?
4. **Latency requirements**: Can we wait for sequential stages?
5. **Fault tolerance**: Can we recover from partial failures?

Start simple (fan-out or pipeline), then add complexity only as needed.
