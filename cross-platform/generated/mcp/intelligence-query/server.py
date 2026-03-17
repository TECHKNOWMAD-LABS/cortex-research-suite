#!/usr/bin/env python3
"""
Multi-source intelligence analysis engine. Queries knowledge base for evidence, cross-references sources, and flags contradictions.

Auto-generated MCP server from TECHKNOWMAD Universal Skill Manifest.
Skill: intelligence-query v1.2.0
"""

import os
from typing import Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="intelligence-query", version="1.2.0")


@mcp.tool()
async def query_intelligence(
    query: str,
    sources: Optional[list[str]] = None,
    depth: str = "deep",
) -> dict[str, Any]:
    """Query knowledge base for evidence, cross-reference sources, flag contradictions"""
    from skills.intelligence_query import execute

    return await execute("query_intelligence", locals())


if __name__ == "__main__":
    mcp.run()
