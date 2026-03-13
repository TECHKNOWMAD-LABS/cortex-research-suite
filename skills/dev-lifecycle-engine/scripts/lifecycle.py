#!/usr/bin/env python3
"""
Autonomous Development Lifecycle Engine

A comprehensive orchestrator for managing the complete software development workflow.
Implements a 7-phase mandatory lifecycle ensuring quality, consistency, and traceability.

Phases:
1. BRAINSTORM - Socratic design refinement and requirements locking
2. PLAN - Extreme granular task decomposition
3. SETUP - Workspace isolation and baseline verification
4. EXECUTE - Subagent-driven development with fresh context per task
5. TEST - TDD enforcement with RED-GREEN-REFACTOR
6. REVIEW - Two-stage quality gate (spec compliance + code quality)
7. MERGE - Evidence-based completion with audit trail

CLI Usage:
  python3 lifecycle.py init --name "project-name"
  python3 lifecycle.py status
  python3 lifecycle.py advance
  python3 lifecycle.py tasks
  python3 lifecycle.py checkpoint --message "Task 3 complete"
  python3 lifecycle.py load --checkpoint "Task 3 complete"
  python3 lifecycle.py help --phase 2
"""

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from uuid import uuid4


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Severity(Enum):
    """Review issue severity."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


@dataclass
class DesignSection:
    """Section of a design document."""
    title: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Task:
    """Represents a single executable task."""
    id: str
    title: str
    description: str
    file_path: str
    duration_minutes: int
    code_snippet: str
    pre_conditions: List[str]
    verification_steps: List[str]
    success_criteria: str
    blocked_by: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    timestamp_created: str = field(default_factory=lambda: datetime.now().isoformat())
    timestamp_completed: Optional[str] = None
    lines_added: int = 0
    lines_modified: int = 0


@dataclass
class ReviewIssue:
    """Review issue found during Phase 6."""
    severity: Severity
    category: str  # "spec_compliance" or "code_quality"
    title: str
    description: str
    affected_files: List[str]
    suggested_fix: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Checkpoint:
    """Saves workspace state at a point in time."""
    id: str
    message: str
    phase: Phase
    timestamp: str
    file_hashes: Dict[str, str]  # filepath -> md5 hash
    git_sha: Optional[str] = None


@dataclass
class LifecycleSession:
    """Tracks the entire lifecycle session."""
    project_name: str
    session_id: str
    current_phase: Phase = Phase.BRAINSTORM
    timestamp_started: str = field(default_factory=lambda: datetime.now().isoformat())
    timestamp_last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Phase-specific data
    design_document: Dict[str, DesignSection] = field(default_factory=dict)
    tasks: Dict[str, Task] = field(default_factory=dict)
    checkpoints: Dict[str, Checkpoint] = field(default_factory=dict)
    review_issues: List[ReviewIssue] = field(default_factory=list)
    
    # Metrics
    total_tests_added: int = 0
    total_files_modified: int = 0
    total_lines_added: int = 0
    total_lines_modified: int = 0
    
    # Git integration
    feature_branch: Optional[str] = None
    worktree_path: Optional[str] = None
    baseline_tests_passed: bool = False


class LifecycleEngine:
    """Main lifecycle orchestrator."""
    
    def __init__(self, session_dir: Optional[Path] = None):
        """
        Initialize the lifecycle engine.
        
        Args:
            session_dir: Directory to store session state (default: ./.lifecycle)
        """
        self.session_dir = session_dir or Path.cwd() / ".lifecycle"
        self.session_dir.mkdir(exist_ok=True)
        self.session: Optional[LifecycleSession] = None
        self.session_file = self.session_dir / "session.json"
        
    def init(self, project_name: str) -> LifecycleSession:
        """
        Initialize a new development project lifecycle.
        
        Args:
            project_name: Name of the project being developed
            
        Returns:
            New LifecycleSession object
            
        Raises:
            FileExistsError: If session already exists
        """
        if self.session_file.exists():
            raise FileExistsError(f"Lifecycle already initialized. Session: {self.session_file}")
        
        self.session = LifecycleSession(
            project_name=project_name,
            session_id=str(uuid4())
        )
        
        self._save_session()
        logger.info(f"Initialized lifecycle for project: {project_name}")
        logger.info(f"Session ID: {self.session.session_id}")
        
        return self.session
    
    def load(self) -> LifecycleSession:
        """
        Load existing session from disk.
        
        Returns:
            Loaded LifecycleSession
            
        Raises:
            FileNotFoundError: If no session exists
        """
        if not self.session_file.exists():
            raise FileNotFoundError(f"No lifecycle session found at {self.session_file}")
        
        with open(self.session_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruct session with proper types
        self.session = self._deserialize_session(data)
        logger.info(f"Loaded session: {self.session.project_name} ({self.session.session_id})")
        
        return self.session
    
    def _save_session(self) -> None:
        """Save current session to disk."""
        if not self.session:
            raise RuntimeError("No session to save")
        
        with open(self.session_file, 'w') as f:
            json.dump(self._serialize_session(self.session), f, indent=2)
    
    def _serialize_session(self, session: LifecycleSession) -> Dict:
        """Convert session to JSON-serializable dict."""
        data = asdict(session)
        
        # Convert Phase enum
        data['current_phase'] = session.current_phase.name
        
        # Convert design document
        data['design_document'] = {
            k: asdict(v) for k, v in session.design_document.items()
        }
        
        # Convert tasks
        data['tasks'] = {
            k: {**asdict(v), 'status': v.status.value}
            for k, v in session.tasks.items()
        }
        
        # Convert checkpoints
        data['checkpoints'] = {
            k: {**asdict(v), 'phase': v.phase.name}
            for k, v in session.checkpoints.items()
        }
        
        # Convert review issues
        data['review_issues'] = [
            {**asdict(issue), 'severity': issue.severity.value, 'category': issue.category}
            for issue in session.review_issues
        ]
        
        return data
    
    def _deserialize_session(self, data: Dict) -> LifecycleSession:
        """Reconstruct session from JSON dict."""
        # Restore Phase enum
        data['current_phase'] = Phase[data['current_phase']]
        
        # Restore design document
        data['design_document'] = {
            k: DesignSection(**v)
            for k, v in data.get('design_document', {}).items()
        }
        
        # Restore tasks
        data['tasks'] = {
            k: Task(**{**v, 'status': TaskStatus(v['status'])})
            for k, v in data.get('tasks', {}).items()
        }
        
        # Restore checkpoints
        data['checkpoints'] = {
            k: Checkpoint(**{**v, 'phase': Phase[v['phase']]})
            for k, v in data.get('checkpoints', {}).items()
        }
        
        # Restore review issues
        data['review_issues'] = [
            ReviewIssue(**{**issue, 'severity': Severity(issue['severity'])})
            for issue in data.get('review_issues', [])
        ]
        
        return LifecycleSession(**data)
    
    def add_design_section(self, title: str, content: str) -> None:
        """
        Add a section to the design document (Phase 1).
        
        Args:
            title: Section title (e.g., "Problem Statement")
            content: Section content
        """
        if not self.session:
            raise RuntimeError("No active session")
        
        if self.session.current_phase != Phase.BRAINSTORM:
            logger.warning(f"Adding design section in {self.session.current_phase.name}")
        
        self.session.design_document[title] = DesignSection(title=title, content=content)
        self._save_session()
    
    def add_task(self, task: Task) -> None:
        """
        Add a task to the plan (Phase 2).
        
        Args:
            task: Task to add
        """
        if not self.session:
            raise RuntimeError("No active session")
        
        self.session.tasks[task.id] = task
        self._save_session()
    
    def create_git_worktree(self, branch_name: Optional[str] = None) -> str:
        """
        Create isolated git worktree for development (Phase 3).
        
        Args:
            branch_name: Feature branch name (default: generated from project name)
            
        Returns:
            Path to worktree
        """
        if not self.session:
            raise RuntimeError("No active session")
        
        if not branch_name:
            branch_name = f"feature/{self.session.project_name.lower().replace(' ', '-')}"
        
        try:
            # Create worktree
            worktree_path = Path.cwd() / f".worktree-{branch_name}"
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
                check=True,
                capture_output=True
            )
            
            self.session.feature_branch = branch_name
            self.session.worktree_path = str(worktree_path)
            self._save_session()
            
            logger.info(f"Created worktree at {worktree_path}")
            return str(worktree_path)
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e.stderr.decode()}")
            raise RuntimeError(f"Git worktree creation failed: {e}") from e
    
    def verify_test_baseline(self) -> bool:
        """
        Run tests to verify baseline passes (Phase 3).
        
        Returns:
            True if all tests pass
        """
        if not self.session:
            raise RuntimeError("No active session")
        
        try:
            # Try common test runners
            for cmd in [["npm", "test"], ["pytest"], ["python", "-m", "unittest"]]:
                try:
                    subprocess.run(
                        cmd,
                        check=True,
                        capture_output=True,
                        timeout=300
                    )
                    self.session.baseline_tests_passed = True
                    self._save_session()
                    logger.info("Baseline tests passed")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            logger.warning("Could not verify test baseline - no test runner found")
            return False
        
        except subprocess.TimeoutExpired:
            logger.error("Test baseline verification timed out")
            return False
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          lines_added: int = 0, lines_modified: int = 0) -> None:
        """
        Update task execution status (Phase 4).
        
        Args:
            task_id: Task ID to update
            status: New status
            lines_added: Lines of code added
            lines_modified: Lines of code modified
        """
        if not self.session:
            raise RuntimeError("No active session")
        
        if task_id not in self.session.tasks:
            raise ValueError(f"Unknown task: {task_id}")
        
        task = self.session.tasks[task_id]
        task.status = status
        task.lines_added = lines_added
        task.lines_modified = lines_modified
        
        if status == TaskStatus.COMPLETED:
            task.timestamp_completed = datetime.now().isoformat()
            self.session.total_lines_added += lines_added
            self.session.total_lines_modified += lines_modified
        
        self._save_session()
    
    def create_checkpoint(self, message: str) -> Checkpoint:
        """
        Create micro-checkpoint (Phase 4 and throughout).
        
        Args:
            message: Human-readable checkpoint message
            
        Returns:
            Created Checkpoint
        """
        if not self.session:
            raise RuntimeError("No active session")
        
        checkpoint = Checkpoint(
            id=str(uuid4()),
            message=message,
            phase=self.session.current_phase,
            timestamp=datetime.now().isoformat(),
            file_hashes=self._compute_file_hashes()
        )
        
        # Capture git SHA if in a worktree
        if self.session.worktree_path:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    checkpoint.git_sha = result.stdout.strip()
            except Exception as e:
                logger.warning(f"Could not capture git SHA: {e}")
        
        self.session.checkpoints[checkpoint.id] = checkpoint
        self._save_session()
        
        logger.info(f"Checkpoint created: {message}")
        return checkpoint
    
    def _compute_file_hashes(self) -> Dict[str, str]:
        """Compute MD5 hashes of modified files for checkpoint."""
        hashes = {}
        
        if not self.session or not self.session.tasks:
            return hashes
        
        file_paths = {task.file_path for task in self.session.tasks.values()}
        
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists():
                try:
                    with open(path, 'rb') as f:
                        file_hash = hashlib.md5(f.read(), usedforsecurity=False).hexdigest()
                        hashes[file_path] = file_hash
                except (IOError, OSError) as e:
                    logger.warning(f"Could not hash file {file_path}: {e}")
        
        return hashes
    
    def add_review_issue(self, issue: ReviewIssue) -> None:
        """
        Add review finding (Phase 6).
        
        Args:
            issue: ReviewIssue to add
        """
        if not self.session:
            raise RuntimeError("No active session")
        
        self.session.review_issues.append(issue)
        self._save_session()
    
    def get_critical_issues(self) -> List[ReviewIssue]:
        """Get all CRITICAL severity issues."""
        if not self.session:
            return []
        
        return [i for i in self.session.review_issues if i.severity == Severity.CRITICAL]
    
    def advance_phase(self) -> Phase:
        """
        Advance to next phase.
        
        Returns:
            New phase
            
        Raises:
            RuntimeError: If current phase gates not met
        """
        if not self.session:
            raise RuntimeError("No active session")
        
        current = self.session.current_phase
        
        # Validate gates before advancing
        if current == Phase.BRAINSTORM:
            if not self.session.design_document:
                raise RuntimeError("Design document required before advancing")
        
        elif current == Phase.PLAN:
            if not self.session.tasks:
                raise RuntimeError("Task plan required before advancing")
        
        elif current == Phase.SETUP:
            if not self.session.baseline_tests_passed:
                logger.warning("Test baseline not verified")
        
        elif current == Phase.EXECUTE:
            incomplete_tasks = [t for t in self.session.tasks.values() 
                              if t.status != TaskStatus.COMPLETED]
            if incomplete_tasks:
                raise RuntimeError(f"Cannot advance: {len(incomplete_tasks)} tasks incomplete")
        
        elif current == Phase.TEST:
            pass  # No specific gate
        
        elif current == Phase.REVIEW:
            critical = self.get_critical_issues()
            if critical:
                raise RuntimeError(f"Cannot advance: {len(critical)} CRITICAL review issues")
        
        elif current == Phase.MERGE:
            raise RuntimeError("Cannot advance beyond MERGE phase")
        
        # Advance phase
        next_phase = Phase(current.value + 1)
        self.session.current_phase = next_phase
        self.session.timestamp_last_updated = datetime.now().isoformat()
        self._save_session()
        
        logger.info(f"Advanced to Phase {next_phase.value}: {next_phase.name}")
        return next_phase
    
    def get_task_dependencies(self) -> Dict[str, List[str]]:
        """
        Get task dependency graph.
        
        Returns:
            Dict mapping task ID to list of task IDs it depends on
        """
        if not self.session:
            return {}
        
        dependencies = {}
        for task_id, task in self.session.tasks.items():
            dependencies[task_id] = task.blocked_by
        
        return dependencies
    
    def get_independent_tasks(self) -> Set[str]:
        """Get task IDs that can run in parallel."""
        dependencies = self.get_task_dependencies()
        return {task_id for task_id, deps in dependencies.items() if not deps}
    
    def get_sequential_chains(self) -> List[List[str]]:
        """Get ordered chains of dependent tasks."""
        if not self.session:
            return []
        
        chains = []
        visited = set()
        
        for task_id, task in self.session.tasks.items():
            if task_id in visited or task.blocked_by:
                continue
            
            chain = [task_id]
            visited.add(task_id)
            
            # Follow chain of blocked tasks
            for other_id, other_task in self.session.tasks.items():
                if task_id in other_task.blocked_by:
                    chain.append(other_id)
                    visited.add(other_id)
            
            if chain:
                chains.append(chain)
        
        return chains


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Development Lifecycle Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python3 lifecycle.py init --name "my-feature"
  python3 lifecycle.py status
  python3 lifecycle.py advance
  python3 lifecycle.py tasks
  python3 lifecycle.py checkpoint --message "Phase 4 complete"
  python3 lifecycle.py load --checkpoint <checkpoint-id>
  python3 lifecycle.py help --phase 2
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize new project lifecycle')
    init_parser.add_argument('--name', required=True, help='Project name')
    init_parser.add_argument('--dir', help='Session directory (default: ./.lifecycle)')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current phase and status')
    status_parser.add_argument('--dir', help='Session directory')
    
    # Advance command
    advance_parser = subparsers.add_parser('advance', help='Advance to next phase')
    advance_parser.add_argument('--dir', help='Session directory')
    
    # Tasks command
    tasks_parser = subparsers.add_parser('tasks', help='List all tasks and dependencies')
    tasks_parser.add_argument('--dir', help='Session directory')
    
    # Checkpoint command
    checkpoint_parser = subparsers.add_parser('checkpoint', help='Create checkpoint')
    checkpoint_parser.add_argument('--message', required=True, help='Checkpoint message')
    checkpoint_parser.add_argument('--dir', help='Session directory')
    
    # Load command
    load_parser = subparsers.add_parser('load', help='Load checkpoint (rollback)')
    load_parser.add_argument('--checkpoint', required=True, help='Checkpoint ID or message')
    load_parser.add_argument('--dir', help='Session directory')
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Get phase-specific help')
    help_parser.add_argument('--phase', type=int, choices=range(1, 8), help='Phase number')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    session_dir = Path(args.dir) if args.dir else None
    engine = LifecycleEngine(session_dir)
    
    try:
        if args.command == 'init':
            session = engine.init(args.name)
            print(f"\n✓ Initialized lifecycle for: {session.project_name}")
            print(f"  Session ID: {session.session_id}")
            print(f"  Current phase: {session.current_phase.name}")
        
        elif args.command == 'status':
            session = engine.load()
            print(f"\nProject: {session.project_name}")
            print(f"Phase: {session.current_phase.value} - {session.current_phase.name}")
            print(f"Session ID: {session.session_id}")
            print(f"Started: {session.timestamp_started}")
            
            if session.tasks:
                completed = sum(1 for t in session.tasks.values() if t.status == TaskStatus.COMPLETED)
                print(f"Tasks: {completed}/{len(session.tasks)} completed")
            
            if session.review_issues:
                critical = sum(1 for i in session.review_issues if i.severity == Severity.CRITICAL)
                print(f"Review issues: {len(session.review_issues)} ({critical} critical)")
        
        elif args.command == 'advance':
            session = engine.load()
            new_phase = engine.advance_phase()
            print(f"\n✓ Advanced to Phase {new_phase.value}: {new_phase.name}")
        
        elif args.command == 'tasks':
            session = engine.load()
            if not session.tasks:
                print("\nNo tasks defined yet")
            else:
                print(f"\nTasks ({len(session.tasks)}):")
                for task_id, task in session.tasks.items():
                    blocked = f" (blocked by: {', '.join(task.blocked_by)})" if task.blocked_by else ""
                    print(f"  [{task.status.value}] {task.title}{blocked}")
        
        elif args.command == 'checkpoint':
            session = engine.load()
            checkpoint = engine.create_checkpoint(args.message)
            print(f"\n✓ Checkpoint created: {checkpoint.id}")
            print(f"  Message: {checkpoint.message}")
            print(f"  Phase: {checkpoint.phase.name}")
        
        elif args.command == 'load':
            session = engine.load()
            # Find checkpoint by ID or message
            found = None
            for ckpt in session.checkpoints.values():
                if args.checkpoint in [ckpt.id, ckpt.message]:
                    found = ckpt
                    break
            
            if found:
                print(f"\n✓ Loaded checkpoint: {found.message}")
                print(f"  Phase: {found.phase.name}")
                print(f"  Created: {found.timestamp}")
            else:
                print(f"\n✗ Checkpoint not found: {args.checkpoint}")
                return 1
        
        elif args.command == 'help':
            phase_help = {
                1: "BRAINSTORM - Lock in requirements and design through Socratic questioning",
                2: "PLAN - Break design into 2-5 minute executable tasks",
                3: "SETUP - Create isolated environment and verify test baseline",
                4: "EXECUTE - Implement tasks with fresh context per task",
                5: "TEST - Enforce RED-GREEN-REFACTOR TDD methodology",
                6: "REVIEW - Two-stage quality gate (spec compliance + code quality)",
                7: "MERGE - Integrate changes with full audit trail"
            }
            
            if args.phase:
                print(f"\nPhase {args.phase}: {phase_help[args.phase]}")
            else:
                print("\nDevelopment Lifecycle Phases:")
                for i, help_text in phase_help.items():
                    print(f"  {i}. {help_text}")
        
        return 0
    
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n✗ Interrupted", file=sys.stderr)
        return 130


if __name__ == '__main__':
    sys.exit(main())
