"""Task graph execution engine for complex multi-step workflows.

Defines workflows as directed acyclic graphs (DAGs) where each node
represents an agent task with defined inputs and outputs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from cortex.agents.base_agent import BaseAgent, AgentResponse


@dataclass
class TaskNode:
    """A node in the task execution graph."""

    name: str
    agent: BaseAgent
    dependencies: list[str] = field(default_factory=list)
    transform: Callable[[str, dict[str, str]], str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "agent": self.agent.name,
            "dependencies": self.dependencies,
        }


@dataclass
class TaskResult:
    """Result of executing a task graph."""

    outputs: dict[str, AgentResponse] = field(default_factory=dict)
    execution_order: list[str] = field(default_factory=list)
    total_latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_order": self.execution_order,
            "outputs": {k: v.to_dict() for k, v in self.outputs.items()},
            "total_latency_ms": self.total_latency_ms,
        }


class TaskGraph:
    """DAG-based task execution engine.

    Nodes are executed in topological order, with outputs from
    dependencies passed as context to downstream nodes.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, TaskNode] = {}

    def add_node(self, node: TaskNode) -> None:
        """Add a task node to the graph."""
        for dep in node.dependencies:
            if dep not in self._nodes:
                raise ValueError(f"Dependency '{dep}' not found. Add it before '{node.name}'.")
        if node.name in self._nodes:
            raise ValueError(f"Node '{node.name}' already exists.")
        self._nodes[node.name] = node

    def _topological_sort(self) -> list[str]:
        """Compute execution order via topological sort."""
        visited: set[str] = set()
        order: list[str] = []
        visiting: set[str] = set()

        def _visit(name: str) -> None:
            if name in visiting:
                raise ValueError(f"Cycle detected at node '{name}'")
            if name in visited:
                return
            visiting.add(name)
            for dep in self._nodes[name].dependencies:
                _visit(dep)
            visiting.discard(name)
            visited.add(name)
            order.append(name)

        for name in self._nodes:
            _visit(name)
        return order

    def execute(self, initial_input: str) -> TaskResult:
        """Execute the task graph with topological ordering."""
        execution_order = self._topological_sort()
        result = TaskResult(execution_order=execution_order)
        start = time.time()

        dep_outputs: dict[str, str] = {}

        for node_name in execution_order:
            node = self._nodes[node_name]

            # Build input from dependencies
            if node.transform:
                task_input = node.transform(initial_input, dep_outputs)
            elif node.dependencies:
                # Concatenate dependency outputs
                dep_texts = [f"## {dep}\n{dep_outputs[dep]}" for dep in node.dependencies if dep in dep_outputs]
                task_input = f"{initial_input}\n\n{''.join(dep_texts)}"
            else:
                task_input = initial_input

            # Execute agent
            context = {dep: dep_outputs.get(dep, "") for dep in node.dependencies}
            response = node.agent.execute(task_input, context=context)

            result.outputs[node_name] = response
            dep_outputs[node_name] = response.content

        result.total_latency_ms = round((time.time() - start) * 1000, 2)
        return result

    @property
    def nodes(self) -> list[str]:
        return list(self._nodes.keys())

    def visualize(self) -> str:
        """Return ASCII visualization of the task graph."""
        lines = ["Task Graph:", ""]
        order = self._topological_sort()
        for name in order:
            node = self._nodes[name]
            deps = ", ".join(node.dependencies) if node.dependencies else "(start)"
            lines.append(f"  [{name}] <- {deps}")
        return "\n".join(lines)
