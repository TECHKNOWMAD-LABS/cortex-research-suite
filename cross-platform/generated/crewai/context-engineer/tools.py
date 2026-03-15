#!/usr/bin/env python3
"""
CrewAI tool wrappers for context-engineer.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Optimize_contextToolSchema(BaseModel):
    content: str = Field(description="Raw content to optimize")
    max_tokens: int = Field(description="Target token budget")
    strategy: str = Field(description="Optimization strategy")


class Optimize_contextTool(BaseTool):
    name: str = "optimize_context"
    description: str = "Optimize context window by prioritizing and compressing relevant content"
    args_schema: type[BaseModel] = Optimize_contextToolSchema

    def _run(self, **kwargs) -> str:
        from skills.context_engineer import execute_sync
        return json.dumps(execute_sync("optimize_context", kwargs))
