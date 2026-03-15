#!/usr/bin/env python3
"""
SQLite-backed persistent memory with FTS5 full-text search for cross-session knowledge retention.

Auto-generated MCP server from TECHKNOWMAD Universal Skill Manifest.
Skill: persistent-memory v1.0.0
"""

import os
from typing import Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="persistent-memory", version="1.0.0")

@mcp.tool()
async def memory_operation(
    operation: str,
    key: Optional[str] = None,
    value: Optional[str] = None,
    query: Optional[str] = None,
) -> dict[str, Any]:
    """Store, retrieve, or search persistent memory entries"""
    # Implementation: delegate to skill logic
    from skills.persistent_memory import execute
    return await execute("memory_operation", locals())


if __name__ == "__main__":
    mcp.run()