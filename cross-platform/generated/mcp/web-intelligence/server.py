#!/usr/bin/env python3
"""
Live web scraping with Scrapling for social signals, academic evidence, and forum analysis.

Auto-generated MCP server from TECHKNOWMAD Universal Skill Manifest.
Skill: web-intelligence v1.2.0
"""

import os
from typing import Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="web-intelligence", version="1.2.0")


@mcp.tool()
async def web_sweep(
    topic: str,
    sources: Optional[list[str]] = None,
    live: bool = False,
) -> dict[str, Any]:
    """Run live web intelligence sweep combining social, academic, and forum signals"""
    from skills.web_intelligence import execute

    return await execute("web_sweep", locals())


if __name__ == "__main__":
    mcp.run()
