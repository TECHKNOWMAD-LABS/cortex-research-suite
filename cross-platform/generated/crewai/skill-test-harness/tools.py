#!/usr/bin/env python3
"""
CrewAI tool wrappers for skill-test-harness.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Test_skillToolSchema(BaseModel):
    skill_path: str = Field(description="Path to skill directory")
    test_suite: str = Field(description="Test suite to run")
    coverage: bool = Field(description="Enable coverage reporting")


class Test_skillTool(BaseTool):
    name: str = "test_skill"
    description: str = "Run automated tests on a skill with fixtures and assertions"
    args_schema: type[BaseModel] = Test_skillToolSchema

    def _run(self, **kwargs) -> str:
        from skills.skill_test_harness import execute_sync
        return json.dumps(execute_sync("test_skill", kwargs))
