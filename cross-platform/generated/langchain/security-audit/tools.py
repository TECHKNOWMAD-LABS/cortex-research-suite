#!/usr/bin/env python3
"""
LangChain tool wrappers for security-audit.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class SecurityScanToolInput(BaseModel):
    target: str = Field(description="Directory path to scan")
    output: str = Field(description="Output path for the report")
    format: str = Field(description="")
    severity_threshold: str = Field(description="")


class SecurityScanTool(BaseTool):
    name: str = "security_scan"
    description: str = "Run a full security scan on a target directory with bandit, semgrep, and secret detection"
    args_schema: type[BaseModel] = SecurityScanToolInput

    def _run(self, **kwargs) -> str:
        from skills.security_audit import execute_sync
        return json.dumps(execute_sync("security_scan", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.security_audit import execute
        result = await execute("security_scan", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [SecurityScanTool()]