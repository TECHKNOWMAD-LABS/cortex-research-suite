#!/usr/bin/env python3
"""
LangChain tool wrappers for prompt-architect.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Optimize_promptToolInput(BaseModel):
    prompt: str = Field(description="Prompt to optimize")
    task_type: str = Field(description="Type of task the prompt is for")
    model: str = Field(description="Target model")


class Optimize_promptTool(BaseTool):
    name: str = "optimize_prompt"
    description: str = "Analyze and optimize a prompt for improved performance"
    args_schema: type[BaseModel] = Optimize_promptToolInput

    def _run(self, **kwargs) -> str:
        from skills.prompt_architect import execute_sync
        return json.dumps(execute_sync("optimize_prompt", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.prompt_architect import execute
        result = await execute("optimize_prompt", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Optimize_promptTool()]
