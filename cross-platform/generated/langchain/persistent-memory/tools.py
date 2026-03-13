#!/usr/bin/env python3
"""
LangChain tool wrappers for persistent-memory.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class MemoryOperationToolInput(BaseModel):
    action: str = Field(description="Memory operation")
    key: str = Field(description="Memory key")
    value: dict = Field(description="Value to store")
    query: str = Field(description="Search query")
    tags: list = Field(description="Tags for filtering")
    ttl: int = Field(description="Time-to-live in seconds")


class MemoryOperationTool(BaseTool):
    name: str = "memory_operation"
    description: str = "Store, retrieve, search, or manage persistent memory entries"
    args_schema: type[BaseModel] = MemoryOperationToolInput

    def _run(self, **kwargs) -> str:
        from skills.persistent_memory import execute_sync
        return json.dumps(execute_sync("memory_operation", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.persistent_memory import execute
        result = await execute("memory_operation", kwargs)
        return json.dumps(result)


def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [MemoryOperationTool()]