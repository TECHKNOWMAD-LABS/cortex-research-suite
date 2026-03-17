#!/usr/bin/env python3
"""
Live social listening feed connector. Pulls trending topics from social platforms with sentiment analysis.

Auto-generated MCP server from TECHKNOWMAD Universal Skill Manifest.
Skill: mindspider-connector v1.2.0
"""

import os
from typing import Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="mindspider-connector", version="1.2.0")


@mcp.tool()
async def fetch_topics(
    source: str = "demo",
    platforms: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Pull trending topics from social platforms with sentiment analysis"""
    from skills.mindspider_connector import execute

    return await execute("fetch_topics", locals())


if __name__ == "__main__":
    mcp.run()
