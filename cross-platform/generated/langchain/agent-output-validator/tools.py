#!/usr/bin/env python3
"""
LangChain tool wrappers for agent-output-validator.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Validate_outputToolInput(BaseModel):
    output: str = Field(description="Agent output to validate")
    schema: dict = Field(description="Expected output schema")
    quality_threshold: float = Field(description="Minimum quality score (0-1)")


class Validate_outputTool(BaseTool):
    name: str = "validate_output"
    description: str = "Validate agent output against quality gates and schema"
    args_schema: type[BaseModel] = Validate_outputToolInput

    def _run(self, **kwargs) -> str:
        from skills.agent_output_validator import execute_sync
        return json.dumps(execute_sync("validate_output", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.agent_output_validator import execute
        result = await execute("validate_output", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Validate_outputTool()]
