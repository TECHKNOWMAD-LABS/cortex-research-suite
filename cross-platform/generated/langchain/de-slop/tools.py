#!/usr/bin/env python3
"""
LangChain tool wrappers for de-slop.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class ScanSlopToolInput(BaseModel):
    target: str = Field(description="File path or directory to scan")
    format: str = Field(description="")
    fix: bool = Field(description="Auto-fix detected patterns")


class ScanSlopTool(BaseTool):
    name: str = "scan_slop"
    description: str = "Scan text for AI-generated writing patterns and return a slop score with findings"
    args_schema: type[BaseModel] = ScanSlopToolInput

    def _run(self, **kwargs) -> str:
        from skills.de_slop import execute_sync
        return json.dumps(execute_sync("scan_slop", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.de_slop import execute
        result = await execute("scan_slop", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [ScanSlopTool()]