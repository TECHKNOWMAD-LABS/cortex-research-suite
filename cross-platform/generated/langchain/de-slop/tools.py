#!/usr/bin/env python3
"""
LangChain tool wrappers for de-slop.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Scan_contentToolInput(BaseModel):
    content: str = Field(description="Content to scan for AI patterns")
    fix: bool = Field(description="Auto-fix detected patterns")


class Scan_contentTool(BaseTool):
    name: str = "scan_content"
    description: str = "Scan content for AI-generated writing patterns and flag violations"
    args_schema: type[BaseModel] = Scan_contentToolInput

    def _run(self, **kwargs) -> str:
        from skills.de_slop import execute_sync
        return json.dumps(execute_sync("scan_content", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.de_slop import execute
        result = await execute("scan_content", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Scan_contentTool()]
