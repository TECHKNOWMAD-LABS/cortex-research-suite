#!/usr/bin/env python3
"""YAML-defined DAG executor with async parallel execution.

Loads workflow definitions from YAML files, builds a task graph,
and executes nodes in parallel where dependencies allow.

Usage:
    python task_graph.py --graph graphs/research_pipeline.yaml --input "AI safety"
    python task_graph.py --graph graphs/mlops_pipeline.yaml --input "model v2.1"
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class NodeSpec:
    """Specification for a single task node from YAML."""

    name: str
    agent_role: str
    dependencies: list[str] = field(default_factory=list)
    prompt_template: str = ""
    timeout_seconds: float = 120.0
    retry_count: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NodeSpec:
        return cls(
            name=data["name"],
            agent_role=data.get("agent_role", "generic"),
            dependencies=data.get("depends_on", []),
            prompt_template=data.get("prompt", "{input}"),
            timeout_seconds=data.get("timeout", 120.0),
            retry_count=data.get("retries", 0),
        )


@dataclass
class NodeResult:
    """Result of executing a single node."""

    name: str
    agent_role: str
    content: str
    latency_ms: float
    status: str = "completed"
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "agent_role": self.agent_role,
            "content_length": len(self.content),
            "content_preview": self.content[:300],
            "latency_ms": self.latency_ms,
            "status": self.status,
            "error": self.error,
        }


@dataclass
class GraphResult:
    """Result of executing a complete task graph."""

    graph_name: str
    input_text: str
    nodes: dict[str, NodeResult] = field(default_factory=dict)
    execution_order: list[list[str]] = field(default_factory=list)
    total_latency_ms: float = 0.0
    final_output: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph": self.graph_name,
            "input_preview": self.input_text[:200],
            "total_nodes": len(self.nodes),
            "execution_waves": self.execution_order,
            "total_latency_ms": self.total_latency_ms,
            "final_output_preview": self.final_output[:500],
            "node_results": {k: v.to_dict() for k, v in self.nodes.items()},
        }


# ---------------------------------------------------------------------------
# Graph definition loader
# ---------------------------------------------------------------------------


@dataclass
class GraphDefinition:
    """A complete graph definition loaded from YAML."""

    name: str
    description: str
    nodes: list[NodeSpec]
    output_node: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> GraphDefinition:
        if yaml is None:
            raise ImportError("PyYAML is required: pip install pyyaml")
        data = yaml.safe_load(path.read_text())
        graph = data["graph"]
        nodes = [NodeSpec.from_dict(n) for n in graph["nodes"]]
        return cls(
            name=graph.get("name", path.stem),
            description=graph.get("description", ""),
            nodes=nodes,
            output_node=graph.get("output_node", nodes[-1].name),
            metadata=graph.get("metadata", {}),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphDefinition:
        graph = data["graph"]
        nodes = [NodeSpec.from_dict(n) for n in graph["nodes"]]
        return cls(
            name=graph.get("name", "unnamed"),
            description=graph.get("description", ""),
            nodes=nodes,
            output_node=graph.get("output_node", nodes[-1].name),
            metadata=graph.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# Offline agent for testing
# ---------------------------------------------------------------------------


def _offline_execute(role: str, prompt: str, node_name: str) -> str:
    """Generate a mock response for a given agent role."""
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]
    templates = {
        "researcher": (
            f"Research output for '{node_name}' (ref:{prompt_hash}): "
            "Comprehensive literature review identifies 3 primary themes. "
            "Quantitative evidence suggests 25-40% improvement in target metrics "
            "across controlled studies. Gaps remain in long-term outcome data "
            "and cross-population generalizability."
        ),
        "critic": (
            f"Critique of '{node_name}' (ref:{prompt_hash}): "
            "Methodological review flags selection bias in cited studies. "
            "Claimed improvements lack standardized baselines. "
            "Recommend additional controlled trials before scaling."
        ),
        "strategist": (
            f"Strategy for '{node_name}' (ref:{prompt_hash}): "
            "Phased rollout recommended: pilot (3mo), validation (3mo), scale (6mo). "
            "Key gates: statistical significance at each phase, equity audit, "
            "stakeholder alignment check."
        ),
        "synthesizer": (
            f"Synthesis for '{node_name}' (ref:{prompt_hash}): "
            "Multi-perspective analysis yields moderate confidence assessment. "
            "Evidence supports cautious adoption with robust monitoring. "
            "Final recommendation: proceed with gated deployment."
        ),
        "data_engineer": (
            f"Data pipeline output for '{node_name}' (ref:{prompt_hash}): "
            "Schema validated. 15,000 records ingested, 23 duplicates removed, "
            "4 format corrections applied. Data quality score: 0.94."
        ),
        "validator": (
            f"Validation for '{node_name}' (ref:{prompt_hash}): "
            "All contract checks passed. Output conforms to expected schema. "
            "No hallucination markers detected. Confidence: HIGH."
        ),
        "deployer": (
            f"Deployment plan for '{node_name}' (ref:{prompt_hash}): "
            "Canary deployment to 5% traffic. Rollback trigger: p99 > 200ms or "
            "error rate > 0.5%. Full rollout after 24h stability."
        ),
    }
    return templates.get(role, f"Output for {node_name} ({role}): Analysis complete.")


# ---------------------------------------------------------------------------
# Async DAG executor
# ---------------------------------------------------------------------------


class AsyncDAGExecutor:
    """Executes a task graph with maximum parallelism.

    Nodes whose dependencies are satisfied run concurrently.
    Uses wave-based scheduling: each wave contains all nodes
    whose dependencies completed in prior waves.
    """

    def __init__(self, definition: GraphDefinition, provider: Any = None) -> None:
        self._definition = definition
        self._provider = provider
        self._node_map = {n.name: n for n in definition.nodes}
        self._validate_graph()

    def _validate_graph(self) -> None:
        names = set(self._node_map.keys())
        for node in self._definition.nodes:
            for dep in node.dependencies:
                if dep not in names:
                    raise ValueError(f"Node '{node.name}' depends on unknown node '{dep}'")
        # Cycle detection via topological sort
        self._compute_waves()

    def _compute_waves(self) -> list[list[str]]:
        """Compute execution waves (levels of parallelism)."""
        in_degree: dict[str, int] = {n.name: len(n.dependencies) for n in self._definition.nodes}
        dependents: dict[str, list[str]] = {n.name: [] for n in self._definition.nodes}
        for node in self._definition.nodes:
            for dep in node.dependencies:
                dependents[dep].append(node.name)

        waves: list[list[str]] = []
        ready = [name for name, deg in in_degree.items() if deg == 0]
        processed: set[str] = set()

        while ready:
            waves.append(sorted(ready))
            next_ready: list[str] = []
            for name in ready:
                processed.add(name)
                for dep_name in dependents[name]:
                    in_degree[dep_name] -= 1
                    if in_degree[dep_name] == 0:
                        next_ready.append(dep_name)
            ready = next_ready

        if len(processed) != len(self._node_map):
            unprocessed = set(self._node_map.keys()) - processed
            raise ValueError(f"Cycle detected involving nodes: {unprocessed}")

        return waves

    async def execute(self, input_text: str) -> GraphResult:
        """Execute the graph with async parallel scheduling."""
        waves = self._compute_waves()
        result = GraphResult(
            graph_name=self._definition.name,
            input_text=input_text,
            execution_order=waves,
        )
        start = time.time()
        outputs: dict[str, str] = {}

        for wave in waves:
            tasks = [self._execute_node(name, input_text, outputs) for name in wave]
            wave_results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, node_result in zip(wave, wave_results):
                if isinstance(node_result, Exception):
                    result.nodes[name] = NodeResult(
                        name=name,
                        agent_role=self._node_map[name].agent_role,
                        content="",
                        latency_ms=0,
                        status="failed",
                        error=str(node_result),
                    )
                else:
                    result.nodes[name] = node_result
                    outputs[name] = node_result.content

        result.total_latency_ms = round((time.time() - start) * 1000, 2)
        output_node = self._definition.output_node
        if output_node in outputs:
            result.final_output = outputs[output_node]

        return result

    async def _execute_node(
        self,
        name: str,
        input_text: str,
        dep_outputs: dict[str, str],
    ) -> NodeResult:
        """Execute a single node with its dependencies resolved."""
        node = self._node_map[name]
        start = time.time()

        # Build prompt from template and dependency outputs
        prompt = node.prompt_template.replace("{input}", input_text)
        for dep in node.dependencies:
            dep_content = dep_outputs.get(dep, "")
            prompt = prompt.replace(f"{{{dep}}}", dep_content[:3000])

        # Execute
        if self._provider is not None:
            response = self._provider.generate(prompt)
            content = response.content
        else:
            content = _offline_execute(node.agent_role, prompt, name)

        latency = (time.time() - start) * 1000
        return NodeResult(
            name=name,
            agent_role=node.agent_role,
            content=content,
            latency_ms=round(latency, 2),
        )

    def visualize(self) -> str:
        """ASCII visualization of the DAG with wave grouping."""
        waves = self._compute_waves()
        lines = [f"Graph: {self._definition.name}", f"Description: {self._definition.description}", ""]
        for i, wave in enumerate(waves):
            lines.append(f"Wave {i} (parallel):")
            for name in wave:
                node = self._node_map[name]
                deps = ", ".join(node.dependencies) if node.dependencies else "(start)"
                lines.append(f"  [{name}] ({node.agent_role}) <- {deps}")
            lines.append("")
        lines.append(f"Output: {self._definition.output_node}")
        return "\n".join(lines)


def run_graph(definition: GraphDefinition, input_text: str, provider: Any = None) -> GraphResult:
    """Synchronous wrapper for executing a graph."""
    executor = AsyncDAGExecutor(definition, provider=provider)
    return asyncio.run(executor.execute(input_text))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="YAML-defined DAG executor")
    parser.add_argument("--graph", type=Path, required=True, help="Path to graph YAML file")
    parser.add_argument("--input", required=True, help="Input text for the graph")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    parser.add_argument("--visualize", action="store_true", help="Print graph visualization and exit")
    args = parser.parse_args()

    definition = GraphDefinition.from_yaml(args.graph)

    if args.visualize:
        executor = AsyncDAGExecutor(definition)
        print(executor.visualize())
        return 0

    print(f"Executing graph: {definition.name}")
    print(f"Nodes: {len(definition.nodes)}")
    print("=" * 60)

    result = run_graph(definition, args.input)

    # Report
    print(f"\nExecution waves: {result.execution_order}")
    print(f"Total latency: {result.total_latency_ms:.0f}ms")
    print()
    for name, node_result in result.nodes.items():
        print(f"  [{node_result.status.upper()}] {name} ({node_result.agent_role}) — {node_result.latency_ms:.0f}ms")
    print(f"\nFinal output ({len(result.final_output)} chars):")
    print(result.final_output[:500])

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result.to_dict(), indent=2))
        print(f"\nSaved: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
