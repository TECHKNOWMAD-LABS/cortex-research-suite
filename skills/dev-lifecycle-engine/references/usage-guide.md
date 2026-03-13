# Dev Lifecycle Engine Skill

A comprehensive Claude Code skill that orchestrates the complete software development lifecycle. This skill enforces a 7-phase mandatory workflow that ensures quality and consistency from brainstorm through merge.

## Key Features

- **7 Mandatory Phases** with explicit gates between each
- **Task Decomposition** to 2-5 minute micro-tasks
- **Subagent Architecture** for fresh context per task
- **TDD Enforcement** with RED-GREEN-REFACTOR cycle
- **Two-Stage Review** (spec compliance + code quality)
- **Checkpoint System** for state recovery and audit trail
- **Dependency Tracking** with parallel/sequential task scheduling
- **Production-Grade State Machine** with full audit logging

## Quick Start

### Using the Skill in Claude Code

```bash
# Start a development project
Use the dev-lifecycle-engine skill to design a new authentication system

# Follow the prompts through each phase:
# Phase 1: Brainstorm - Design questions and document
# Phase 2: Plan - Task decomposition
# Phase 3: Setup - Workspace preparation
# Phase 4: Execute - Task execution
# Phase 5: Test - TDD and coverage
# Phase 6: Review - Quality gates
# Phase 7: Merge - Integration
```

### Using the Python CLI

```bash
# Initialize a new project
python3 scripts/lifecycle.py init --name "auth-system"

# Check current status
python3 scripts/lifecycle.py status

# Advance to next phase
python3 scripts/lifecycle.py advance

# View task dependency graph
python3 scripts/lifecycle.py tasks

# Create a checkpoint
python3 scripts/lifecycle.py checkpoint --message "Login endpoint complete"

# Show help for a specific phase
python3 scripts/lifecycle.py help --phase 2
```

## The 7 Phases

### Phase 1: BRAINSTORM (Socratic Design Refinement)
Ask clarifying questions, generate a comprehensive design document covering:
- Problem Statement
- User Stories
- Technical Constraints
- Success Criteria
- Edge Cases
- Assumptions & Dependencies

**Gate**: Design document must receive explicit approval

### Phase 2: PLAN (Extreme Granular Decomposition)
Break design into 2-5 minute tasks, each with:
- Exact file paths
- Complete code snippets
- Pre-conditions
- Verification steps
- Success criteria

**Gate**: Task dependency graph reviewed and approved

### Phase 3: SETUP (Workspace Isolation)
- Create git worktree on feature branch
- Verify test baseline
- Set up project environment
- Create initial checkpoint

**Gate**: Clean baseline with all tests passing

### Phase 4: EXECUTE (Subagent-Driven Development)
- Dispatch fresh subagent per task
- Run parallel or sequential based on dependencies
- Create micro-checkpoint after each task
- Track execution metrics

**Gate**: All tasks complete, all micro-checkpoints saved

### Phase 5: TEST (TDD Enforcement)
- Enforce RED-GREEN-REFACTOR cycle
- Delete code written before tests
- Measure coverage
- Detect anti-patterns (mocked-to-death, assertion-free tests, etc.)

**Gate**: All tests pass, no anti-patterns, coverage acceptable

### Phase 6: REVIEW (Two-Stage Quality Gate)
**Stage 1**: SPEC COMPLIANCE - Does it match the plan?
**Stage 2**: CODE QUALITY - Is it maintainable, performant, secure?

Issues categorized by severity:
- 🔴 CRITICAL (blocks merge)
- 🟠 MAJOR (should fix)
- 🟡 MINOR (could fix)

**Gate**: Zero CRITICAL issues

### Phase 7: MERGE (Evidence-Based Completion)
- Final verification (all tests pass)
- Generate diff summary
- Present merge options
- Clean up infrastructure
- Create completion record

**Gate**: Explicit user confirmation before irreversible operations

## Architecture

### State Machine (lifecycle.py)

The Python script implements:
- **ProjectState**: Manages project lifecycle state
- **Task**: Represents individual development tasks
- **Checkpoint**: Saves recoverable project snapshots
- **LifecycleManager**: CLI interface

Key capabilities:
- Phase transition validation
- Task dependency tracking
- Checkpoint creation and loading
- Comprehensive status reporting
- JSON-based state persistence

### Integration Points

The skill integrates with:
- **Version Control**: Git worktrees and branching
- **Testing**: Any test framework (Jest, pytest, unittest)
- **CI/CD**: Pluggable test runners
- **Code Review**: PR generation, diff analysis
- **Documentation**: Design artifacts, task specs

## Example Workflow

```
USER: Use dev-lifecycle-engine to build a REST API for user management

SKILL PHASE 1 (BRAINSTORM):
? What are the core endpoints? (GET, POST, PUT, DELETE users)
? Authentication requirements? (JWT)
? Database? (PostgreSQL)
? Validation rules? (Email format, password strength)
[Generates design document]
OK to proceed? → User approves

SKILL PHASE 2 (PLAN):
[Decomposes into tasks]
- Task 1: Create user model (3 min)
- Task 2: Add database migration (2 min)
- Task 3: Implement GET /users (4 min)
- Task 4: Implement POST /users (4 min)
- Task 5: Add authentication middleware (3 min)
- Task 6: Add request validation (3 min)
[Shows dependency graph]
Ready to execute? → User approves

SKILL PHASE 3 (SETUP):
- Created git worktree: feature/user-api
- Baseline tests: ✓ PASS
- Created checkpoint: setup-complete
Ready to execute? → User approves

SKILL PHASE 4 (EXECUTE):
[Dispatch subagent for each task]
✓ Task 1: Create user model (actual: 2 min, planned: 3 min)
✓ Task 2: Add migration (actual: 3 min, planned: 2 min)
✓ Task 3: GET /users (actual: 4 min, planned: 4 min)
✓ Task 4: POST /users (actual: 5 min, planned: 4 min)
✓ Task 5: Auth middleware (actual: 4 min, planned: 3 min)
✓ Task 6: Validation (actual: 3 min, planned: 3 min)
Total: 21 min (estimated: 19 min)

SKILL PHASE 5 (TEST):
✓ All tests pass
✓ Coverage: 87% (target: 80%)
✓ No anti-patterns detected
Ready to review? → Yes

SKILL PHASE 6 (REVIEW):
SPEC COMPLIANCE: ✓ All planned tasks complete
CODE QUALITY:
  - Security: ✓ Proper JWT validation
  - Performance: ✓ N+1 queries prevented
  - Testing: ✓ Adequate coverage
  - Maintainability: ✓ Clear naming, good structure
CRITICAL ISSUES: 0
Ready to merge? → Yes

SKILL PHASE 7 (MERGE):
Summary:
- Files changed: 8
- Lines added: 342
- Tests added: 24
- Coverage increase: +12%
Merging to main...
✓ COMPLETE
```

## Task Format

Each task in Phase 2 follows this structure:

```json
{
  "task_id": "task-001",
  "name": "Create user model",
  "description": "Define User schema with fields for email, name, password",
  "file_paths": ["/src/models/User.js"],
  "code_snippet": "const userSchema = new Schema({ ... });",
  "preconditions": ["Database initialized", "Schema framework installed"],
  "verification_steps": [
    "Model file created",
    "Schema exports User",
    "Validation tests pass"
  ],
  "success_criteria": "User model created with all required fields",
  "estimated_duration_minutes": 3,
  "blocked_by": [],
  "blocks": ["Task 3: Implement GET /users"]
}
```

## State Persistence

Project state is stored in `.lifecycle/` directory:

```
.lifecycle/
  ├── project-name.json          # Current state
  └── checkpoints/
      ├── abc12345.json          # Checkpoint snapshots
      ├── def67890.json
      └── ...
```

State includes:
- Current phase
- All tasks and their status
- Checkpoint history
- Metadata (design doc, reviews, etc.)
- Start time and progress metrics

## CLI Commands

### Initialize Project
```bash
python3 scripts/lifecycle.py init --name "my-project"
```

### Check Status
```bash
python3 scripts/lifecycle.py status
```
Shows current phase, task counts, blockages, advance conditions.

### Advance Phase
```bash
python3 scripts/lifecycle.py advance
```
Validates all gate criteria before advancing.

### View Tasks
```bash
python3 scripts/lifecycle.py tasks
```
Shows full task dependency graph in JSON format.

### Create Checkpoint
```bash
python3 scripts/lifecycle.py checkpoint --message "Feature X complete"
```

### Load Checkpoint
```bash
python3 scripts/lifecycle.py load --checkpoint abc123
```
Shows checkpoint details (informational; actual loading is manual).

### Help
```bash
python3 scripts/lifecycle.py help --phase 2
```
Shows phase-specific guidance.

## Error Handling

The state machine validates:
- Phase transition prerequisites
- Task dependency satisfaction
- Gate completion criteria
- State persistence integrity

All errors are logged with context for debugging.

## Type Hints & Documentation

The Python implementation includes:
- Full type hints (Python 3.7+)
- Comprehensive docstrings
- Inline comments for complex logic
- Error handling with logging

## Production Use

This skill is suitable for:
- Individual feature development
- Team sprint planning
- Complex system refactoring
- New codebase initialization
- Multi-phase migrations

The mandatory phase structure prevents:
- Skipping design and planning
- Inadequate testing
- Bypassing code review
- Merging without verification

## Notes

- Requires Python 3.7+ for type hints and dataclasses
- Git recommended for Phase 3+ (worktree support)
- State is JSON-based for easy inspection and recovery
- All timestamps are ISO 8601 formatted for consistency
- Checkpoint IDs are 8-character hex hashes for uniqueness
