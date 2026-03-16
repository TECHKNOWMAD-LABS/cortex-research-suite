#!/usr/bin/env python3
"""
Validates Claude Code skill structure, frontmatter, scripts, and references against the canonical skill specification. Catches errors before packaging.

Auto-generated MCP server from TECHKNOWMAD Universal Skill Manifest.
Skill: skill-validator v1.0.0
"""

import os
from typing import Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="skill-validator", version="1.1.0")

@mcp.tool()
async def validate_skill(
    skill_path: str,
    strict: bool = "True"
) -> dict[str, Any]:
    """Validate a skill directory against the canonical specification"""
    # Implementation: delegate to skill logic
    from skills.skill_validator import execute
    return await execute("validate_skill", locals())


if __name__ == "__main__":
    mcp.run()