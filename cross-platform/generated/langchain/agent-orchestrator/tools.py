#!/usr/bin/env python3
"""
LangChain tool wrappers for agent-orchestrator.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class OrchestrateWorkflowToolInput(BaseModel):
    workflow: dict = Field(description="Workflow definition with tasks, dependencies, and agent assignments")
    config: dict = Field(description="Execution config (parallelism, timeout, retry policy)")
    dry_run: bool = Field(description="Validate without executing")


class OrchestrateWorkflowTool(BaseTool):
    name: str = "orchestrate_workflow"
    description: str = "Execute a multi-agent workflow with dependency resolution and parallel task routing"
    args_schema: type[BaseModel] = OrchestrateWorkflowToolInput

    def _run(self, **kwargs) -> str:
        from skills.agent_orchestrator import execute_sync
        return json.dumps(execute_sync("orchestrate_workflow", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.agent_orchestrator import execute
        result = await execute("orchestrate_workflow", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [OrchestrateWorkflowTool()]