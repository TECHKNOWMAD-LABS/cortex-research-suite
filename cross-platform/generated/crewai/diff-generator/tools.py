#!/usr/bin/env python3
"""
CrewAI tool wrappers for diff-generator.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Generate_diffToolSchema(BaseModel):
    original: str = Field(description="Original content")
    modified: str = Field(description="Modified content")
    format: str = Field(description="Output format")


class Generate_diffTool(BaseTool):
    name: str = "generate_diff"
    description: str = "Generate structured diff between two versions of content"
    args_schema: type[BaseModel] = Generate_diffToolSchema

    def _run(self, **kwargs) -> str:
        from skills.diff_generator import execute_sync
        return json.dumps(execute_sync("generate_diff", kwargs))
