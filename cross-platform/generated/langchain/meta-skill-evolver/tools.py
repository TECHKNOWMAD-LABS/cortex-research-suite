#!/usr/bin/env python3
"""
LangChain tool wrappers for meta-skill-evolver.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Evolve_skillToolInput(BaseModel):
    skill_path: str = Field(description="Path to skill directory")
    metrics: dict = Field(description="Performance metrics")
    strategy: str = Field(description="Evolution strategy")


class Evolve_skillTool(BaseTool):
    name: str = "evolve_skill"
    description: str = "Analyze skill performance and generate improved variants through mutation"
    args_schema: type[BaseModel] = Evolve_skillToolInput

    def _run(self, **kwargs) -> str:
        from skills.meta_skill_evolver import execute_sync
        return json.dumps(execute_sync("evolve_skill", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.meta_skill_evolver import execute
        result = await execute("evolve_skill", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Evolve_skillTool()]
