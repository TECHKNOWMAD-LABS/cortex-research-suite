#!/usr/bin/env python3
"""
Autonomous Development Lifecycle Engine - State Machine Implementation

Manages the complete software development workflow with 7 mandatory phases:
1. BRAINSTORM (design refinement)
2. PLAN (task decomposition)
3. SETUP (workspace isolation)
4. EXECUTE (subagent-driven development)
5. TEST (TDD enforcement)
6. REVIEW (quality gates)
7. MERGE (evidence-based completion)

Enforces phase transitions, manages task dependencies, and maintains audit trail.
"""

import json
import sys
import argparse
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase(Enum):
    """Development lifecycle phases."""
    BRAINSTORM = 1
    PLAN = 2
    SETUP = 3
    EXECUTE = 4
    TEST = 5
    REVIEW = 6
    MERGE = 7
    COMPLETE = 8  # Terminal state


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a single development task."""
    task_id: str
    name: str
    description: str
    file_paths: List[str] = field(default_factory=list)
    code_snippet: Optional[str] = None
    preconditions: List[str] = field(default_factory=list)
    verification_steps: List[str] = field(default_factory=list)
    success_criteria: str = ""
    estimated_duration_minutes: int = 3
    blocked_by: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_minutes: Optional[int] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        data_copy = data.copy()
        if isinstance(data_copy.get('status'), str):
            data_copy['status'] = TaskStatus(data_copy['status'])
        return Task(**data_copy)


@dataclass
class Checkpoint:
    """Represents a saved project state."""
    checkpoint_id: str
    timestamp: str
    phase: Phase
    message: str
    tasks_completed: int
    git_sha: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary."""
        data = asdict(self)
        data['phase'] = self.phase.value
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Checkpoint':
        """Create checkpoint from dictionary."""
        data_copy = data.copy()
        if isinstance(data_copy.get('phase'), int):
            data_copy['phase'] = Phase(data_copy['phase'])
        return Checkpoint(**data_copy)


class ProjectState:
    """Manages the state of a development project."""

    def __init__(self, project_name: str, state_dir: Path = Path.cwd()):
        """Initialize project state manager."""
        self.project_name = project_name
        self.state_dir = state_dir / ".lifecycle"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / f"{project_name}.json"
        self.checkpoint_dir = self.state_dir / "checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)

        self.current_phase: Phase = Phase.BRAINSTORM
        self.tasks: Dict[str, Task] = {}
        self.checkpoints: List[Checkpoint] = []
        self.start_time: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {
            "design_document": None,
            "task_graph": None,
            "review_report": None,
            "merge_summary": None,
        }

        self._load_state()

    def _load_state(self) -> None:
        """Load project state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                self.current_phase = Phase(data.get('current_phase', 1))
                self.tasks = {
                    tid: Task.from_dict(t)
                    for tid, t in data.get('tasks', {}).items()
                }
                self.checkpoints = [
                    Checkpoint.from_dict(c)
                    for c in data.get('checkpoints', [])
                ]
                self.metadata = data.get('metadata', {})
                self.start_time = data.get('start_time')
                logger.info(f"Loaded project state: {self.project_name}")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self._initialize_new()
        else:
            self._initialize_new()

    def _initialize_new(self) -> None:
        """Initialize new project state."""
        self.current_phase = Phase.BRAINSTORM
        self.tasks = {}
        self.checkpoints = []
        self.start_time = datetime.now().isoformat()
        self.metadata = {
            "design_document": None,
            "task_graph": None,
            "review_report": None,
            "merge_summary": None,
        }
        self.save_state()
        logger.info(f"Initialized new project: {self.project_name}")

    def save_state(self) -> None:
        """Persist project state to disk."""
        state_data = {
            'project_name': self.project_name,
            'current_phase': self.current_phase.value,
            'start_time': self.start_time,
            'tasks': {tid: t.to_dict() for tid, t in self.tasks.items()},
            'checkpoints': [c.to_dict() for c in self.checkpoints],
            'metadata': self.metadata,
            'last_updated': datetime.now().isoformat(),
        }
        with open(self.state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
        logger.info(f"Saved project state: {self.project_name}")

    def can_advance(self) -> Tuple[bool, List[str]]:
        """Check if project can advance to next phase."""
        errors: List[str] = []

        # Phase-specific advancement criteria
        if self.current_phase == Phase.BRAINSTORM:
            if not self.metadata.get('design_document'):
                errors.append("Design document required before advancing to PLAN")
        
        elif self.current_phase == Phase.PLAN:
            if not self.tasks:
                errors.append("Tasks required before advancing to SETUP")
            incomplete_tasks = [t for t in self.tasks.values() 
                               if t.status != TaskStatus.COMPLETE]
            if incomplete_tasks:
                errors.append(f"All plan tasks must be complete ({len(incomplete_tasks)} incomplete)")
        
        elif self.current_phase == Phase.SETUP:
            if not self.checkpoints:
                errors.append("Initial checkpoint required before advancing to EXECUTE")
        
        elif self.current_phase == Phase.EXECUTE:
            incomplete = [t for t in self.tasks.values() 
                         if t.status != TaskStatus.COMPLETE]
            if incomplete:
                errors.append(f"{len(incomplete)} tasks incomplete")
        
        elif self.current_phase == Phase.TEST:
            if not self.metadata.get('test_report'):
                errors.append("Test report required before advancing to REVIEW")
        
        elif self.current_phase == Phase.REVIEW:
            if not self.metadata.get('review_report'):
                errors.append("Review report required before advancing to MERGE")
            review = self.metadata.get('review_report', {})
            critical_issues = review.get('critical_issues', [])
            if critical_issues:
                errors.append(
                    f"Critical issues must be resolved ({len(critical_issues)} found)"
                )
        
        elif self.current_phase == Phase.MERGE:
            errors.append("Already at final phase")

        return len(errors) == 0, errors

    def advance_phase(self) -> Tuple[bool, str]:
        """Advance to next phase."""
        can_advance, errors = self.can_advance()
        
        if not can_advance:
            msg = "Cannot advance: " + "; ".join(errors)
            return False, msg

        if self.current_phase == Phase.MERGE:
            return False, "Already at final phase"

        old_phase = self.current_phase
        self.current_phase = Phase(self.current_phase.value + 1)
        self.save_state()
        
        msg = f"Advanced from {old_phase.name} to {self.current_phase.name}"
        logger.info(msg)
        return True, msg

    def add_task(self, task: Task) -> None:
        """Add a task to the project."""
        self.tasks[task.task_id] = task
        self.save_state()

    def update_task_status(self, task_id: str, status: TaskStatus,
                          execution_time: Optional[int] = None) -> bool:
        """Update task status."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = status
        task.completed_at = datetime.now().isoformat()
        if execution_time:
            task.execution_time_minutes = execution_time
        self.save_state()
        return True

    def create_checkpoint(self, message: str) -> str:
        """Create a checkpoint of the current state."""
        checkpoint_id = hashlib.md5(
            f"{datetime.now().isoformat()}:{message}".encode()
        ).hexdigest()[:8]

        tasks_completed = sum(
            1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETE
        )

        git_sha = self._get_git_sha()

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now().isoformat(),
            phase=self.current_phase,
            message=message,
            tasks_completed=tasks_completed,
            git_sha=git_sha,
        )

        self.checkpoints.append(checkpoint)
        self.save_state()
        logger.info(f"Created checkpoint: {checkpoint_id} - {message}")
        return checkpoint_id

    def _get_git_sha(self) -> Optional[str]:
        """Get current git SHA if in a git repo."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.state_dir.parent.parent,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive project status."""
        elapsed = None
        if self.start_time:
            start = datetime.fromisoformat(self.start_time)
            elapsed = (datetime.now() - start).total_seconds() / 60

        task_stats = {
            'total': len(self.tasks),
            'complete': sum(1 for t in self.tasks.values() 
                          if t.status == TaskStatus.COMPLETE),
            'pending': sum(1 for t in self.tasks.values() 
                         if t.status == TaskStatus.PENDING),
            'blocked': sum(1 for t in self.tasks.values() 
                         if t.status == TaskStatus.BLOCKED),
            'in_progress': sum(1 for t in self.tasks.values() 
                             if t.status == TaskStatus.IN_PROGRESS),
            'failed': sum(1 for t in self.tasks.values() 
                        if t.status == TaskStatus.FAILED),
        }

        can_advance, errors = self.can_advance()

        return {
            'project': self.project_name,
            'current_phase': self.current_phase.name,
            'phase_number': self.current_phase.value,
            'can_advance': can_advance,
            'advance_blockers': errors,
            'elapsed_minutes': round(elapsed, 2) if elapsed else None,
            'start_time': self.start_time,
            'tasks': task_stats,
            'checkpoints': len(self.checkpoints),
            'metadata': self.metadata,
        }

    def get_task_graph(self) -> Dict[str, Any]:
        """Generate task dependency graph."""
        graph = {
            'tasks': {},
            'dependencies': [],
            'parallel_groups': [],
        }

        for task_id, task in self.tasks.items():
            graph['tasks'][task_id] = {
                'name': task.name,
                'status': task.status.value,
                'duration_minutes': task.estimated_duration_minutes,
                'blocked_by': task.blocked_by,
                'blocks': task.blocks,
            }

        # Find dependency chains
        for task_id, task in self.tasks.items():
            for blocker in task.blocked_by:
                graph['dependencies'].append({
                    'from': blocker,
                    'to': task_id,
                })

        return graph

    def export_summary(self) -> str:
        """Export human-readable project summary."""
        status = self.get_status()
        task_graph = self.get_task_graph()

        lines = [
            f"\n{'='*60}",
            f"Project: {self.project_name}",
            f"Phase: {status['current_phase']} ({status['phase_number']}/8)",
            f"Elapsed: {status['elapsed_minutes']} minutes",
            f"{'='*60}",
            f"\nTasks ({status['tasks']['total']} total):",
            f"  ✓ Complete:    {status['tasks']['complete']}",
            f"  ○ Pending:     {status['tasks']['pending']}",
            f"  ⧖ In Progress: {status['tasks']['in_progress']}",
            f"  ◐ Blocked:     {status['tasks']['blocked']}",
            f"  ✗ Failed:      {status['tasks']['failed']}",
            f"\nCheckpoints: {status['checkpoints']}",
        ]

        if not status['can_advance'] and status['advance_blockers']:
            lines.append(f"\nCannot advance to next phase:")
            for error in status['advance_blockers']:
                lines.append(f"  • {error}")

        if self.tasks:
            lines.append(f"\nTask Dependency Graph:")
            for task_id, task in self.tasks.items():
                lines.append(f"  [{task['status'][:3].upper()}] {task_id}: {task['name']}")
                if task['blocked_by']:
                    lines.append(f"         blocked by: {', '.join(task['blocked_by'])}")

        lines.append(f"\n{'='*60}\n")
        return "\n".join(lines)


class LifecycleManager:
    """Main CLI interface for the lifecycle engine."""

    def __init__(self, project_name: str = "default"):
        """Initialize lifecycle manager."""
        self.state = ProjectState(project_name)

    def handle_init(self, args: argparse.Namespace) -> int:
        """Initialize a new project."""
        name = args.name or "default"
        state = ProjectState(name)
        state.save_state()
        print(f"Initialized project: {name}")
        return 0

    def handle_status(self, args: argparse.Namespace) -> int:
        """Show project status."""
        print(self.state.export_summary())
        return 0

    def handle_advance(self, args: argparse.Namespace) -> int:
        """Advance to next phase."""
        success, message = self.state.advance_phase()
        status_code = 0 if success else 1
        print(message)
        if success:
            print(self.state.export_summary())
        return status_code

    def handle_tasks(self, args: argparse.Namespace) -> int:
        """Show task list and dependencies."""
        graph = self.state.get_task_graph()
        print("\nTask Dependency Graph:")
        print(json.dumps(graph, indent=2))
        return 0

    def handle_checkpoint(self, args: argparse.Namespace) -> int:
        """Create a checkpoint."""
        message = args.message or f"Checkpoint at {Phase(self.state.current_phase.value).name}"
        checkpoint_id = self.state.create_checkpoint(message)
        print(f"Created checkpoint: {checkpoint_id}")
        print(f"Message: {message}")
        return 0

    def handle_load(self, args: argparse.Namespace) -> int:
        """Load a checkpoint (informational only)."""
        if not args.checkpoint:
            print("Error: --checkpoint ID required")
            return 1
        
        matching = [c for c in self.state.checkpoints 
                   if c.checkpoint_id.startswith(args.checkpoint)]
        
        if not matching:
            print(f"Checkpoint not found: {args.checkpoint}")
            return 1
        
        checkpoint = matching[0]
        print(f"Checkpoint: {checkpoint.checkpoint_id}")
        print(f"Phase: {checkpoint.phase.name}")
        print(f"Timestamp: {checkpoint.timestamp}")
        print(f"Message: {checkpoint.message}")
        print(f"Tasks Completed: {checkpoint.tasks_completed}")
        if checkpoint.git_sha:
            print(f"Git SHA: {checkpoint.git_sha}")
        return 0

    def handle_help(self, args: argparse.Namespace) -> int:
        """Show help for a specific phase."""
        phase_helps = {
            1: "BRAINSTORM: Ask clarifying questions, generate design document",
            2: "PLAN: Decompose design into 2-5 minute tasks with full specs",
            3: "SETUP: Create worktree, verify baseline, create checkpoint",
            4: "EXECUTE: Dispatch subagents, execute tasks, create micro-checkpoints",
            5: "TEST: Enforce RED-GREEN-REFACTOR, measure coverage",
            6: "REVIEW: Spec compliance + code quality gates",
            7: "MERGE: Final verification, generate diff, integrate changes",
        }
        
        if args.phase:
            phase_num = int(args.phase)
            if phase_num in phase_helps:
                print(f"\nPhase {phase_num}: {phase_helps[phase_num]}\n")
            else:
                print(f"Unknown phase: {phase_num}")
                return 1
        else:
            print("\nDevelopment Lifecycle Phases:")
            for num, help_text in phase_helps.items():
                print(f"  {num}. {help_text}")
            print()
        return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Development Lifecycle Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 lifecycle.py init --name "my-project"
  python3 lifecycle.py status
  python3 lifecycle.py advance
  python3 lifecycle.py tasks
  python3 lifecycle.py checkpoint --message "Task 3 complete"
  python3 lifecycle.py load --checkpoint abc123
  python3 lifecycle.py help --phase 2
        """
    )

    parser.add_argument(
        'command',
        choices=['init', 'status', 'advance', 'tasks', 'checkpoint', 'load', 'help'],
        help='Command to execute'
    )
    parser.add_argument('--name', help='Project name (for init)')
    parser.add_argument('--message', help='Checkpoint message')
    parser.add_argument('--checkpoint', help='Checkpoint ID to load')
    parser.add_argument('--phase', help='Phase number (for help)')

    args = parser.parse_args()

    try:
        manager = LifecycleManager(args.name or "default")
        
        handler_map = {
            'init': manager.handle_init,
            'status': manager.handle_status,
            'advance': manager.handle_advance,
            'tasks': manager.handle_tasks,
            'checkpoint': manager.handle_checkpoint,
            'load': manager.handle_load,
            'help': manager.handle_help,
        }

        handler = handler_map.get(args.command)
        if handler:
            return handler(args)
        return 1
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
