#!/usr/bin/env python3
"""
CrewAI tool wrappers for github-mcp.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Github_operationToolSchema(BaseModel):
    operation: str = Field(description="GitHub operation to perform")
    repo: str = Field(description="Repository in owner/repo format")
    params: dict = Field(description="Operation parameters")


class Github_operationTool(BaseTool):
    name: str = "github_operation"
    description: str = "Execute GitHub API operations via MCP"
    args_schema: type[BaseModel] = Github_operationToolSchema

    def _run(self, **kwargs) -> str:
        from skills.github_mcp import execute_sync
        return json.dumps(execute_sync("github_operation", kwargs))
