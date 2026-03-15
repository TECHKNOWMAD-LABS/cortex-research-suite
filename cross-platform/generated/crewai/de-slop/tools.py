#!/usr/bin/env python3
"""
CrewAI tool wrappers for de-slop.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Scan_contentToolSchema(BaseModel):
    content: str = Field(description="Content to scan for AI patterns")
    fix: bool = Field(description="Auto-fix detected patterns")


class Scan_contentTool(BaseTool):
    name: str = "scan_content"
    description: str = "Scan content for AI-generated writing patterns and flag violations"
    args_schema: type[BaseModel] = Scan_contentToolSchema

    def _run(self, **kwargs) -> str:
        from skills.de_slop import execute_sync
        return json.dumps(execute_sync("scan_content", kwargs))
