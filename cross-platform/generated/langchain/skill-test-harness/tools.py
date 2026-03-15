#!/usr/bin/env python3
"""
LangChain tool wrappers for skill-test-harness.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Test_skillToolInput(BaseModel):
    skill_path: str = Field(description="Path to skill directory")
    test_suite: str = Field(description="Test suite to run")
    coverage: bool = Field(description="Enable coverage reporting")


class Test_skillTool(BaseTool):
    name: str = "test_skill"
    description: str = "Run automated tests on a skill with fixtures and assertions"
    args_schema: type[BaseModel] = Test_skillToolInput

    def _run(self, **kwargs) -> str:
        from skills.skill_test_harness import execute_sync
        return json.dumps(execute_sync("test_skill", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.skill_test_harness import execute
        result = await execute("test_skill", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Test_skillTool()]
