#!/usr/bin/env python3
"""
LangChain tool wrappers for agent-orchestrator.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Orchestrate_agentsToolInput(BaseModel):
    task: str = Field(description="Task description to orchestrate")
    agents: list = Field(description="List of agent identifiers to coordinate")


class Orchestrate_agentsTool(BaseTool):
    name: str = "orchestrate_agents"
    description: str = "Coordinate multiple agents to execute tasks with dynamic routing"
    args_schema: type[BaseModel] = Orchestrate_agentsToolInput

    def _run(self, **kwargs) -> str:
        from skills.agent_orchestrator import execute_sync
        return json.dumps(execute_sync("orchestrate_agents", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.agent_orchestrator import execute
        result = await execute("orchestrate_agents", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Orchestrate_agentsTool()]
