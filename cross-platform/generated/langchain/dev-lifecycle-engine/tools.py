#!/usr/bin/env python3
"""
LangChain tool wrappers for dev-lifecycle-engine.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Manage_lifecycleToolInput(BaseModel):
    phase: str = Field(description="Lifecycle phase to execute")
    project: str = Field(description="Project identifier")
    config: dict = Field(description="Phase configuration")


class Manage_lifecycleTool(BaseTool):
    name: str = "manage_lifecycle"
    description: str = "Execute development lifecycle phase with automated tracking"
    args_schema: type[BaseModel] = Manage_lifecycleToolInput

    def _run(self, **kwargs) -> str:
        from skills.dev_lifecycle_engine import execute_sync
        return json.dumps(execute_sync("manage_lifecycle", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.dev_lifecycle_engine import execute
        result = await execute("manage_lifecycle", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Manage_lifecycleTool()]
