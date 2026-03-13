#!/usr/bin/env python3
"""
Automated security scanning for code repositories. Runs bandit (Python SAST), semgrep (multi-language static analysis), and secret detection to produce machine-readable reports.

Auto-generated MCP server from TECHKNOWMAD Universal Skill Manifest.
Skill: security-audit v1.0.0
"""

import os
from typing import Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="security-audit", version="1.0.0")

@mcp.tool()
async def security_scan(
    target: str,
    output: Optional[str] = None,
    format: str = "both",
    severity_threshold: str = "low"
) -> dict[str, Any]:
    """Run a full security scan on a target directory with bandit, semgrep, and secret detection"""
    # Implementation: delegate to skill logic
    from skills.security_audit import execute
    return await execute("security_scan", locals())


if __name__ == "__main__":
    mcp.run()