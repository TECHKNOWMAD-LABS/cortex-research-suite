#!/usr/bin/env python3
"""
LangChain tool wrappers for code-review-engine.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class Review_codeToolInput(BaseModel):
    target: str = Field(description="File or directory path to review")
    language: str = Field(description="Programming language")
    strict: bool = Field(description="Enable strict mode")


class Review_codeTool(BaseTool):
    name: str = "review_code"
    description: str = "Run automated code review on a target file or directory"
    args_schema: type[BaseModel] = Review_codeToolInput

    def _run(self, **kwargs) -> str:
        from skills.code_review_engine import execute_sync
        return json.dumps(execute_sync("review_code", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.code_review_engine import execute
        result = await execute("review_code", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [Review_codeTool()]
