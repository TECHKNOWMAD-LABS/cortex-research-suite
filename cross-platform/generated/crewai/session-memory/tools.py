#!/usr/bin/env python3
"""
CrewAI tool wrappers for session-memory.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Session_operationToolSchema(BaseModel):
    operation: str = Field(description="Operation: save, load, list, clear")
    session_id: str = Field(description="Session identifier")
    data: dict = Field(description="Data to persist")


class Session_operationTool(BaseTool):
    name: str = "session_operation"
    description: str = "Store or retrieve session-scoped memory"
    args_schema: type[BaseModel] = Session_operationToolSchema

    def _run(self, **kwargs) -> str:
        from skills.session_memory import execute_sync
        return json.dumps(execute_sync("session_operation", kwargs))
