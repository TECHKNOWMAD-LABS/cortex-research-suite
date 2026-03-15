#!/usr/bin/env python3
"""
CrewAI tool wrappers for dev-lifecycle-engine.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Manage_lifecycleToolSchema(BaseModel):
    phase: str = Field(description="Lifecycle phase to execute")
    project: str = Field(description="Project identifier")
    config: dict = Field(description="Phase configuration")


class Manage_lifecycleTool(BaseTool):
    name: str = "manage_lifecycle"
    description: str = "Execute development lifecycle phase with automated tracking"
    args_schema: type[BaseModel] = Manage_lifecycleToolSchema

    def _run(self, **kwargs) -> str:
        from skills.dev_lifecycle_engine import execute_sync
        return json.dumps(execute_sync("manage_lifecycle", kwargs))
