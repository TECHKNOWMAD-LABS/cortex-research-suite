#!/usr/bin/env python3
"""
CrewAI tool wrappers for skill-validator.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Validate_skillToolSchema(BaseModel):
    skill_path: str = Field(description="Path to skill directory")
    strict: bool = Field(description="Enable strict validation")


class Validate_skillTool(BaseTool):
    name: str = "validate_skill"
    description: str = "Validate skill structure and manifest against specification"
    args_schema: type[BaseModel] = Validate_skillToolSchema

    def _run(self, **kwargs) -> str:
        from skills.skill_validator import execute_sync
        return json.dumps(execute_sync("validate_skill", kwargs))
