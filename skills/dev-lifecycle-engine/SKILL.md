---
name: dev-lifecycle-engine
description: >
  Autonomous development lifecycle orchestrator. Manages the full pipeline from
  brainstorming through design, planning, execution, testing, review, and merge.
  Enforces mandatory workflows — no skipping steps. Use when starting any
  development task, building features, or when "plan this", "build this",
  "design first", "dev lifecycle", or "full pipeline" is mentioned.
---

# Autonomous Development Lifecycle Engine

A comprehensive orchestrator for managing the complete software development workflow. This skill implements a 7-phase mandatory lifecycle that ensures quality, consistency, and traceability through every stage of development.

## When to Use This Skill

- Starting any new feature or development task
- Mentioning "plan this", "build this", "design first"
- Requesting "dev lifecycle", "full pipeline", or "complete workflow"
- When systematic development methodology is required
- When you need traceability from brainstorm to merge

## The 7 Mandatory Phases

### Phase 1: BRAINSTORM (Socratic Design Refinement)

**Purpose**: Lock in requirements and design before any code is written.

**Process**:
- Ask clarifying questions: "What are you really trying to do?", "Who uses this?", "What does success look like?"
- Generate a comprehensive Design Document with these sections:
  - **Problem Statement**: The core problem being solved
  - **User Stories**: Personas and their needs (format: "As a [role], I want [action] so that [benefit]")
  - **Technical Constraints**: Language, platform, dependencies, performance requirements
  - **Success Criteria**: Measurable outcomes (what "done" looks like)
  - **Edge Cases**: Boundary conditions, error scenarios, recovery paths
  - **Assumptions & Dependencies**: External factors affecting implementation

**Output**: Structured design document presented in human-reviewable sections

**Gate**: Design must receive explicit approval before advancing to Phase 2

**Key Principle**: Never jump to code. Every line written will be guided by this design.

---

### Phase 2: PLAN (Extreme Granular Decomposition)

**Purpose**: Break the approved design into executable tasks that require minimal context.

**Process**:
1. Convert design into 2-5 minute tasks (micro-tasks, not epics)
2. For each task, specify:
   - Exact file paths (absolute, no guessing)
   - Complete code snippets (not pseudo-code)
   - Pre-conditions (what must be true before this task)
   - Verification steps (how to know this task is complete)
   - Success criteria (what passes/fails)

3. Apply YAGNI (You Aren't Gonna Need It) principle
   - Only include code needed to pass verification
   - No speculative features
   - No over-engineering

4. Apply DRY (Don't Repeat Yourself) principle
   - Identify and extract common patterns
   - Reference shared utilities instead of duplicating

5. Generate task dependency graph
   - Show which tasks block which
   - Identify independent tasks (can run parallel)
   - Identify sequential chains (must run in order)

**Task Format Example**:
```
TASK: Add user authentication middleware
- File: /src/middleware/auth.js
- Duration: 3 minutes
- Blocked by: none
- Blocks: API route protection tests
- Pre-conditions:
  - Express app initialized
  - JWT library installed
- Code:
  [complete, runnable code snippet]
- Verify: Unit tests pass for token validation
```

**Output**: Task list with dependency graph, ready for execution by subagents

**Gate**: Plan must be reviewed for completeness, ordering, and realism before Phase 3

---

### Phase 3: SETUP (Workspace Isolation)

**Purpose**: Prepare a clean, isolated environment for development.

**Process**:
1. Create git worktree on a feature branch (isolates changes)
2. Verify test baseline passes (confirm tests work before development)
3. Set up project-specific environment:
   - Install dependencies
   - Load environment variables
   - Configure project-specific tooling
4. Create initial checkpoint (save workspace state at t=0)
5. Document setup steps for reproducibility

**Verification**:
- `git status` shows clean working tree
- `npm test` (or equivalent) passes with baseline coverage
- All dependencies installed and accessible
- Checkpoint saved and verified

**Output**: Ready-to-develop workspace with clean baseline

**Gate**: All verification steps must pass before Phase 4

---

### Phase 4: EXECUTE (Subagent-Driven Development)

**Purpose**: Implement tasks with fresh context per task, preventing degradation.

**Process**:
1. Dispatch a fresh subagent for each task
   - Each agent receives: task spec, file paths, code snippets, verification steps
   - Each agent has NO context from previous tasks (forces clarity)
   - Each agent independently validates their work

2. Two execution modes:
   - **Parallel**: Independent tasks execute concurrently
     - Reduces total time for non-blocking tasks
     - Requires conflict detection (file writes to same location)
   - **Sequential**: Dependent tasks chain with validation gates
     - Dependent task only starts after blocker completes
     - Each task validates before passing to next

3. Micro-checkpoint after each task
   - Save state after each task completion
   - Enables rollback if later phases find issues
   - Creates audit trail of incremental progress

4. Track execution metrics:
   - Time per task (vs. estimated 2-5 minutes)
   - Lines of code added/modified
   - Test coverage changes
   - Any blockers encountered

**Output**: Implemented code for all planned tasks, with execution audit trail

**Gate**: All tasks complete, all micro-checkpoints saved, no unresolved blockers

---

### Phase 5: TEST (TDD Enforcement)

**Purpose**: Verify implementation through comprehensive testing, using RED-GREEN-REFACTOR.

**Key Rule**: RED-GREEN-REFACTOR is **NON-NEGOTIABLE**
1. **RED**: Write test that fails (proves test is real)
2. **GREEN**: Write minimal code to pass test
3. **REFACTOR**: Improve code without breaking test

**Anti-Pattern Enforcement**:
- ❌ Code written before tests exist → DELETE IT
- ❌ Tests that only mock → Add integration tests
- ❌ Tests with no assertions → REWRITE
- ❌ 100% coverage target without value → Focus on critical paths

**Process**:
1. Run full test suite after each task batch
2. Measure code coverage (report all files)
3. Identify anti-patterns:
   - Over-mocked tests (low confidence in real behavior)
   - Assertion-free tests (tests that don't actually verify)
   - Tests with no branches (missing edge cases)
4. Generate coverage report with findings
5. Iterate until:
   - All tests pass
   - Coverage meets agreed threshold
   - No anti-patterns remain

**Output**: Full test suite with coverage report, clean green build

**Gate**: All tests pass + no anti-patterns + coverage acceptable

---

### Phase 6: REVIEW (Two-Stage Quality Gate)

**Purpose**: Ensure implementation matches spec AND meets quality standards.

**Stage 1: SPEC COMPLIANCE**
- Does implementation match the approved plan?
- Are all tasks from Phase 2 complete?
- Do all verification steps pass?
- Any unapproved deviations?

**Stage 2: CODE QUALITY**
- **Maintainability**: Clear naming, readable logic, documented complexity
- **Performance**: No N+1 queries, appropriate algorithms, resource-efficient
- **Security**: No injection vulnerabilities, proper auth/validation, secure defaults
- **Error Handling**: Graceful degradation, proper logging, user-friendly errors
- **Testing**: Adequate coverage, meaningful assertions, realistic scenarios
- **Architecture**: Follows project patterns, minimal coupling, good separation of concerns

**Issue Reporting Format**:
- **CRITICAL** (🔴): Blocks forward progress - must fix before merge
  - Security vulnerabilities
  - Test failures
  - Spec violations
  - Production data loss risks
  
- **MAJOR** (🟠): Should fix before merge - trade-off allowed with reason
  - Performance regressions
  - Missing error handling
  - Inadequate test coverage
  - Code duplication
  
- **MINOR** (🟡): Could fix before merge - low priority
  - Naming improvements
  - Comment clarity
  - Minor refactoring
  - Code style consistency

**Output**: Review report with findings, grouped by severity

**Gate**: Zero CRITICAL issues before advancing to Phase 7

---

### Phase 7: MERGE (Evidence-Based Completion)

**Purpose**: Integrate changes with full audit trail and verification.

**Process**:
1. Final verification:
   - Run full test suite one more time (catches race conditions)
   - Verify all checkpoints saved and loadable
   - Confirm no uncommitted changes

2. Generate diff summary:
   - Files changed (with line counts)
   - Functions added/modified/removed
   - Dependencies added/removed
   - Config changes
   - Migration notes (if applicable)

3. Present merge options:
   - **Merge**: Fast-forward or squash merge to main
   - **PR**: Create pull request for peer review
   - **Keep Branch**: Leave worktree active for continued work
   - **Discard**: Clean up and abandon branch

4. Clean up infrastructure:
   - Remove git worktree
   - Archive checkpoints
   - Update session memory with completion record

5. Completion record includes:
   - Total time (brainstorm → merge)
   - Tasks completed vs. planned
   - Tests added
   - Files modified
   - Commits (if applicable)
   - Lessons learned

**Output**: Changes merged/reviewed, infrastructure cleaned, audit trail complete

**Gate**: Explicit user confirmation before irreversible operations (merge/discard)

---

## Workflow Rules

1. **No Phase Skipping**: Each phase gates the next. Cannot skip from Plan to Execute.

2. **Mandatory Gates**: Each phase has explicit completion criteria that must be met.

3. **Fresh Context per Task**: Subagents in Phase 4 receive only their task spec (prevents accumulated context drift).

4. **TDD is Mandatory**: Phase 5 enforces RED-GREEN-REFACTOR. Code without tests is deleted.

5. **Two-Stage Review**: Phase 6 checks both spec compliance AND code quality.

6. **Checkpoint Recovery**: Micro-checkpoints allow rollback to any task if Phase 6 finds critical issues.

7. **Audit Trail**: Every decision, task, and checkpoint is documented for traceability.

## CLI Usage

```bash
# Initialize a new development project
python3 scripts/lifecycle.py init --name "project-name"

# Check current phase and status
python3 scripts/lifecycle.py status

# Advance to next phase
python3 scripts/lifecycle.py advance

# View all tasks and dependencies
python3 scripts/lifecycle.py tasks

# Save checkpoint
python3 scripts/lifecycle.py checkpoint --message "Task 3 complete"

# Load checkpoint (rollback)
python3 scripts/lifecycle.py load --checkpoint "Task 3 complete"

# Get phase-specific help
python3 scripts/lifecycle.py help --phase 2
```

## Integration Points

This skill integrates with:
- **Version Control**: Git worktrees, branching, commit history
- **Testing Frameworks**: Jest, pytest, unittest (framework-agnostic)
- **CI/CD**: Pluggable test runners, coverage reporters
- **Code Review**: PR generation, diff analysis
- **Documentation**: Design artifacts, task specs, completion records

## Success Metrics

A successful lifecycle run demonstrates:
- 100% of planned tasks completed
- All tests passing
- Zero CRITICAL review issues
- <2% ratio of estimated to actual task time (for calibration)
- Zero rollbacks needed in Phase 7
- Full audit trail from brainstorm to merge
