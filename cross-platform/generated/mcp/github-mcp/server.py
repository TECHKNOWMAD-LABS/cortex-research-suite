#!/usr/bin/env python3
"""
GitHub API integration via MCP. Manages repositories, files, branches, pull requests, issues, and releases programmatically without browser automation.

Auto-generated MCP server from TECHKNOWMAD Universal Skill Manifest.
Skill: github-mcp v1.0.0
"""

import os
from typing import Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="github-mcp", version="1.0.0")

@mcp.tool()
async def github_manage_repo(
    owner: str,
    repo: str,
    action: str
) -> dict[str, Any]:
    """Create, update, and manage GitHub repositories and their settings"""
    # Implementation: delegate to skill logic
    from skills.github_mcp import execute
    return await execute("github_manage_repo", locals())

@mcp.tool()
async def github_manage_files(
    owner: str,
    repo: str,
    path: str,
    action: str,
    content: Optional[str] = None,
    message: Optional[str] = None,
    branch: str = "main"
) -> dict[str, Any]:
    """Create, read, update, and delete files in GitHub repositories via API"""
    # Implementation: delegate to skill logic
    from skills.github_mcp import execute
    return await execute("github_manage_files", locals())


if __name__ == "__main__":
    mcp.run()