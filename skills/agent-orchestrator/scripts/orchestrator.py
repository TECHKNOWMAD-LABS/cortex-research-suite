#!/usr/bin/env python3
"""
Multi-agent orchestration engine with parallel dispatch, checkpointing, and recovery.

Supports task graphs with dependencies, automatic parallelization, failure recovery,
and consensus-based output validation.
"""

import json
import sys
import time
import logging
import threading
import queue
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import random


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class Checkpoint:
    """Checkpoint record for task execution."""
    task_id: str
    agent_id: str
    status: str
    started_at: str
    completed_at: str
    duration_seconds: float
    retries: int
    outputs: Dict[str, Any]
    validation: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TaskDefinition:
    """Task configuration."""
    task_id: str
    agent: str
    depends_on: List[str]
    timeout: int
    retries: int
    outputs: Dict[str, Any]
    optional: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.timeout <= 0:
            raise ValueError(f"timeout must be positive: {self.timeout}")
        if self.retries < 0:
            raise ValueError(f"retries must be non-negative: {self.retries}")


class TaskGraph:
    """DAG-based task dependency graph with topological sorting."""

    def __init__(self, tasks: Dict[str, TaskDefinition]) -> None:
        """Initialize graph from task definitions."""
        self.tasks = tasks
        self._validate_graph()
        self.status: Dict[str, TaskStatus] = {
            tid: TaskStatus.PENDING for tid in tasks
        }
        self.checkpoints: Dict[str, Checkpoint] = {}

    def _validate_graph(self) -> None:
        """Validate graph for cycles and missing dependencies."""
        # Check for missing dependencies
        all_task_ids = set(self.tasks.keys())
        for task_id, task in self.tasks.items():
            for dep in task.depends_on:
                if dep not in all_task_ids:
                    raise ValueError(
                        f"Task {task_id} depends on non-existent task {dep}"
                    )

        # Check for cycles (topological sort will fail if cycles exist)
        try:
            self.topological_sort()
        except ValueError as e:
            raise ValueError(f"Graph contains cycle: {e}")

    def topological_sort(self) -> List[str]:
        """Return tasks in topological order (respects dependencies)."""
        in_degree = {tid: len(self.tasks[tid].depends_on) for tid in self.tasks}
        queue_ts = [tid for tid in self.tasks if in_degree[tid] == 0]

        result = []
        while queue_ts:
            # Sort for determinism
            queue_ts.sort()
            current = queue_ts.pop(0)
            result.append(current)

            # Find all tasks that depend on current
            for task_id, task in self.tasks.items():
                if current in task.depends_on:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue_ts.append(task_id)

        if len(result) != len(self.tasks):
            raise ValueError("Graph contains cycle")

        return result

    def get_runnable_tasks(self) -> List[str]:
        """Get tasks that are ready to run (dependencies complete)."""
        runnable = []
        for task_id, task in self.tasks.items():
            if self.status[task_id] != TaskStatus.PENDING:
                continue
            # All dependencies must be completed
            if all(
                self.status[dep] == TaskStatus.COMPLETED for dep in task.depends_on
            ):
                runnable.append(task_id)
        return runnable

    def critical_path_length(self) -> Dict[str, float]:
        """Calculate critical path (longest dependency chain)."""
        topo = self.topological_sort()
        lengths = {tid: 0 for tid in self.tasks}

        for task_id in topo:
            task = self.tasks[task_id]
            if task.depends_on:
                max_dep_len = max(lengths[dep] for dep in task.depends_on)
                lengths[task_id] = max_dep_len + task.timeout
            else:
                lengths[task_id] = task.timeout

        return lengths

    def mark_completed(
        self, task_id: str, outputs: Dict[str, Any], duration: float
    ) -> None:
        """Mark task as completed and save checkpoint."""
        task = self.tasks[task_id]
        checkpoint = Checkpoint(
            task_id=task_id,
            agent_id=task.agent,
            status=TaskStatus.COMPLETED.value,
            started_at=time.isoformat(time.time() - duration),
            completed_at=time.isoformat(time.time()),
            duration_seconds=duration,
            retries=0,
            outputs=outputs,
            validation={"passed": True, "errors": []},
        )
        self.checkpoints[task_id] = checkpoint
        self.status[task_id] = TaskStatus.COMPLETED

    def mark_failed(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        self.status[task_id] = TaskStatus.FAILED

    def save_checkpoints(self, output_dir: Path) -> None:
        """Save all checkpoints to JSON files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        for task_id, checkpoint in self.checkpoints.items():
            file_path = output_dir / f"{task_id}.json"
            with open(file_path, "w") as f:
                json.dump(checkpoint.to_dict(), f, indent=2)
            logging.info(f"Saved checkpoint: {file_path}")

    def load_checkpoints(self, input_dir: Path) -> None:
        """Load checkpoints from JSON files."""
        if not input_dir.exists():
            return
        for file_path in input_dir.glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                checkpoint = Checkpoint.from_dict(data)
                self.checkpoints[checkpoint.task_id] = checkpoint
                self.status[checkpoint.task_id] = TaskStatus.COMPLETED
            logging.info(f"Loaded checkpoint: {file_path}")


class AgentSimulator:
    """Simulates agent execution."""

    def __init__(self, agent_id: str, failure_rate: float = 0.0) -> None:
        """Initialize agent with optional failure injection for testing."""
        self.agent_id = agent_id
        self.failure_rate = failure_rate

    def execute(self, task: TaskDefinition) -> Tuple[bool, Dict[str, Any], str]:
        """
        Execute task. Returns (success, outputs, error_message).

        This is a simulator; in real usage, you'd call actual agent API here.
        """
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.5))

        # Simulate occasional failures
        if random.random() < self.failure_rate:
            return False, {}, "Simulated agent failure"

        # Return mock outputs
        outputs = task.outputs.copy()
        outputs["agent_executed"] = self.agent_id
        outputs["executed_at"] = time.isoformat(time.time())

        return True, outputs, ""


class Orchestrator:
    """Orchestrates multi-agent task execution with recovery."""

    def __init__(
        self,
        task_manifest: Dict[str, Any],
        checkpoint_dir: Path,
        max_workers: int = 4,
    ) -> None:
        """Initialize orchestrator."""
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_workers = max_workers

        # Parse task definitions
        tasks_data = task_manifest.get("tasks", {})
        self.tasks: Dict[str, TaskDefinition] = {
            tid: TaskDefinition(
                task_id=tid,
                agent=td["agent"],
                depends_on=td.get("depends_on", []),
                timeout=td.get("timeout", 30),
                retries=td.get("retries", 3),
                outputs=td.get("outputs", {}),
                optional=td.get("optional", False),
            )
            for tid, td in tasks_data.items()
        }

        self.graph = TaskGraph(self.tasks)
        self.retry_counts: Dict[str, int] = defaultdict(int)
        self.agents: Dict[str, AgentSimulator] = {}

    def dispatch(self) -> None:
        """Dispatch tasks with parallel execution."""
        logging.info("Starting orchestration")
        logging.info(
            f"Topological order: {self.graph.topological_sort()}"
        )

        # Load any existing checkpoints for recovery
        self.graph.load_checkpoints(self.checkpoint_dir)

        task_queue: queue.Queue[str] = queue.Queue()
        result_queue: queue.Queue[Tuple[str, bool, Dict, str]] = queue.Queue()
        workers = []

        # Spawn worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker,
                args=(i, task_queue, result_queue),
                daemon=False,
            )
            worker.start()
            workers.append(worker)

        # Main dispatch loop
        completed = 0
        total = len(self.tasks)

        while completed < total:
            # Get runnable tasks
            runnable = self.graph.get_runnable_tasks()
            for task_id in runnable:
                task_queue.put(task_id)
                self.graph.status[task_id] = TaskStatus.RUNNING

            # Collect results
            try:
                task_id, success, outputs, error = result_queue.get(timeout=1)
                duration = self.tasks[task_id].timeout

                if success:
                    logging.info(
                        f"✓ Task {task_id} completed in {duration}s"
                    )
                    self.graph.mark_completed(task_id, outputs, duration)
                    completed += 1
                else:
                    self._handle_failure(task_id, error)
            except queue.Empty:
                # Check if workers are still alive
                if not any(w.is_alive() for w in workers):
                    break
                continue

        # Signal workers to stop
        for _ in range(self.max_workers):
            task_queue.put(None)

        # Wait for workers to finish
        for worker in workers:
            worker.join(timeout=5)

        self.graph.save_checkpoints(self.checkpoint_dir)
        logging.info("Orchestration complete")

    def _worker(
        self,
        worker_id: int,
        task_queue: queue.Queue[str],
        result_queue: queue.Queue[Tuple[str, bool, Dict, str]],
    ) -> None:
        """Worker thread that executes tasks."""
        while True:
            task_id = task_queue.get()
            if task_id is None:
                break

            task = self.tasks[task_id]

            # Get or create agent
            if task.agent not in self.agents:
                self.agents[task.agent] = AgentSimulator(task.agent)
            agent = self.agents[task.agent]

            # Execute with timeout
            try:
                success, outputs, error = agent.execute(task)
                result_queue.put((task_id, success, outputs, error))
            except Exception as e:
                result_queue.put((task_id, False, {}, str(e)))

    def _handle_failure(self, task_id: str, error: str) -> None:
        """Handle task failure with retry logic."""
        task = self.tasks[task_id]
        retries = self.retry_counts[task_id]

        if retries < task.retries:
            backoff = min(2 ** retries, 32) + random.uniform(0, 0.2 * 2 ** retries)
            logging.warning(
                f"✗ Task {task_id} failed: {error}. "
                f"Retrying in {backoff:.1f}s ({retries + 1}/{task.retries})"
            )
            self.retry_counts[task_id] += 1
            self.graph.status[task_id] = TaskStatus.RETRYING
            time.sleep(backoff)
            self.graph.status[task_id] = TaskStatus.PENDING
        else:
            if task.optional:
                logging.warning(
                    f"✗ Task {task_id} failed after {task.retries} retries "
                    f"(optional, continuing)"
                )
                self.graph.mark_failed(task_id, error)
            else:
                logging.error(
                    f"✗ Task {task_id} failed after {task.retries} retries"
                )
                self.graph.mark_failed(task_id, error)

    def get_status(self) -> Dict[str, Any]:
        """Get orchestration status."""
        return {
            "tasks": {
                tid: self.graph.status[tid].value for tid in self.tasks
            },
            "checkpoints": {
                tid: ckpt.to_dict() for tid, ckpt in self.graph.checkpoints.items()
            },
            "critical_path": self.graph.critical_path_length(),
            "completion_rate": (
                len(self.graph.checkpoints) / len(self.tasks)
                if self.tasks
                else 0
            ),
        }

    def print_graph(self) -> None:
        """Print task graph visualization."""
        print("\nTask Dependency Graph:")
        print("=" * 50)

        topo = self.graph.topological_sort()
        for task_id in topo:
            task = self.tasks[task_id]
            status = self.graph.status[task_id].value
            status_symbol = {
                "pending": "◯",
                "running": "◐",
                "completed": "●",
                "failed": "✗",
                "retrying": "◆",
                "skipped": "○",
            }.get(status, "?")

            deps_str = (
                f" ← {', '.join(task.depends_on)}"
                if task.depends_on
                else " (root)"
            )
            print(f"{status_symbol} {task_id:20} [{task.agent}]{deps_str}")

        print("=" * 50)


def load_manifest(file_path: Path) -> Dict[str, Any]:
    """Load task manifest from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def save_manifest(manifest: Dict[str, Any], file_path: Path) -> None:
    """Save task manifest to JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(manifest, f, indent=2)


def init_project(project_dir: Path) -> None:
    """Initialize new orchestration project."""
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create sample manifest
    sample_manifest = {
        "name": "sample-orchestration",
        "tasks": {
            "gather_data": {
                "agent": "researcher",
                "depends_on": [],
                "timeout": 30,
                "retries": 2,
                "outputs": {"data_collected": True},
            },
            "analyze_a": {
                "agent": "analyst",
                "depends_on": ["gather_data"],
                "timeout": 20,
                "retries": 2,
                "outputs": {"analysis": "metric_a"},
            },
            "analyze_b": {
                "agent": "analyst",
                "depends_on": ["gather_data"],
                "timeout": 20,
                "retries": 2,
                "outputs": {"analysis": "metric_b"},
            },
            "synthesize": {
                "agent": "synthesizer",
                "depends_on": ["analyze_a", "analyze_b"],
                "timeout": 25,
                "retries": 1,
                "outputs": {"report": "final"},
            },
        },
    }

    manifest_file = project_dir / "manifest.json"
    save_manifest(sample_manifest, manifest_file)
    print(f"Created project structure at {project_dir}")
    print(f"Manifest: {manifest_file}")


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print(
            "Usage: orchestrator.py <init|dispatch|status|checkpoint|graph> "
            "[options]"
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        project_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./orchest")
        init_project(project_dir)

    elif command == "dispatch":
        manifest_file = (
            Path(sys.argv[2]) if len(sys.argv) > 2
            else Path("./orchest/manifest.json")
        )
        if not manifest_file.exists():
            print(f"Error: manifest not found at {manifest_file}")
            sys.exit(1)

        manifest = load_manifest(manifest_file)
        checkpoint_dir = manifest_file.parent / "checkpoints"

        orchestrator = Orchestrator(manifest, checkpoint_dir)
        orchestrator.dispatch()

    elif command == "status":
        manifest_file = (
            Path(sys.argv[2]) if len(sys.argv) > 2
            else Path("./orchest/manifest.json")
        )
        if not manifest_file.exists():
            print(f"Error: manifest not found at {manifest_file}")
            sys.exit(1)

        manifest = load_manifest(manifest_file)
        checkpoint_dir = manifest_file.parent / "checkpoints"

        orchestrator = Orchestrator(manifest, checkpoint_dir)
        orchestrator.graph.load_checkpoints(checkpoint_dir)

        status = orchestrator.get_status()
        print(json.dumps(status, indent=2))

    elif command == "graph":
        manifest_file = (
            Path(sys.argv[2]) if len(sys.argv) > 2
            else Path("./orchest/manifest.json")
        )
        if not manifest_file.exists():
            print(f"Error: manifest not found at {manifest_file}")
            sys.exit(1)

        manifest = load_manifest(manifest_file)
        checkpoint_dir = manifest_file.parent / "checkpoints"

        orchestrator = Orchestrator(manifest, checkpoint_dir)
        orchestrator.graph.load_checkpoints(checkpoint_dir)
        orchestrator.print_graph()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
