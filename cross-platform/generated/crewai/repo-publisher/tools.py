#!/usr/bin/env python3
"""
CrewAI tool wrappers for repo-publisher.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class Publish_repoToolSchema(BaseModel):
    repo_path: str = Field(description="Path to repository")
    target: str = Field(description="GitHub target (owner/repo)")
    dry_run: bool = Field(description="Run checks without publishing")


class Publish_repoTool(BaseTool):
    name: str = "publish_repo"
    description: str = "Run pre-publish checks and prepare repo for GitHub publication"
    args_schema: type[BaseModel] = Publish_repoToolSchema

    def _run(self, **kwargs) -> str:
        from skills.repo_publisher import execute_sync
        return json.dumps(execute_sync("publish_repo", kwargs))
