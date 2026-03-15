#!/usr/bin/env python3
"""
LangChain tool wrappers for pre-package-pipeline.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Package_skillToolInput(BaseModel):
    skill_path: str = Field(description="Path to skill directory")
    output: str = Field(description="Output path for package")
    validate_only: bool = Field(description="Only validate without packaging")


class Package_skillTool(BaseTool):
    name: str = "package_skill"
    description: str = "Validate and package a skill for distribution"
    args_schema: type[BaseModel] = Package_skillToolInput

    def _run(self, **kwargs) -> str:
        from skills.pre_package_pipeline import execute_sync
        return json.dumps(execute_sync("package_skill", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.pre_package_pipeline import execute
        result = await execute("package_skill", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Package_skillTool()]
