#!/usr/bin/env python3
"""
LangChain tool wrappers for tdd-enforcer.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class EnforceTddToolInput(BaseModel):
    target: str = Field(description="Path to codebase")
    coverage_threshold: float = Field(description="Minimum coverage percentage")
    check_anti_patterns: bool = Field(description="")
    block_commit: bool = Field(description="Return exit code for pre-commit hook")


class EnforceTddTool(BaseTool):
    name: str = "enforce_tdd"
    description: str = "Validate TDD compliance for a codebase — tests exist, coverage meets threshold, no anti-patterns"
    args_schema: type[BaseModel] = EnforceTddToolInput

    def _run(self, **kwargs) -> str:
        from skills.tdd_enforcer import execute_sync
        return json.dumps(execute_sync("enforce_tdd", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.tdd_enforcer import execute
        result = await execute("enforce_tdd", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [EnforceTddTool()]