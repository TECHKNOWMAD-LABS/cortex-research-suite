#!/usr/bin/env python3
"""
CrewAI tool wrappers for code-review-engine.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class ReviewCodeToolSchema(BaseModel):
    target: str = Field(description="File or directory path to review")
    language: str = Field(description="Programming language (auto-detected if omitted)")
    dimensions: list = Field(description="Review dimensions to check")
    severity_threshold: str = Field(description="")


class ReviewCodeTool(BaseTool):
    name: str = "review_code"
    description: str = "Run automated code review on a file or directory with multi-dimensional analysis"
    args_schema: type[BaseModel] = ReviewCodeToolSchema

    def _run(self, **kwargs) -> str:
        from skills.code_review_engine import execute_sync
        return json.dumps(execute_sync("review_code", kwargs))