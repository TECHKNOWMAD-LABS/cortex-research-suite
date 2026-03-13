#!/usr/bin/env python3
"""
TECHKNOWMAD Universal Skill Adapter

Converts a single skill manifest into platform-specific tool definitions:
- MCP Server (FastMCP)
- LangChain Tool
- CrewAI Tool
- OpenAI GPT Action (OpenAPI spec)
- AGENTS.md discovery file
- GitHub Copilot MCP config

Usage:
    python universal_adapter.py --manifest skill-manifest.json --target mcp
    python universal_adapter.py --manifest skill-manifest.json --target all
    python universal_adapter.py --manifest skill-manifest.json --target langchain --output ./output/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_manifest(path: str) -> dict[str, Any]:
    """Load and validate a skill manifest."""
    with open(path) as f:
        manifest = json.load(f)

    required = ["name", "version", "description", "capabilities", "platforms"]
    missing = [k for k in required if k not in manifest]
    if missing:
        raise ValueError(f"Manifest missing required fields: {missing}")
    return manifest


# --- MCP Server Generator ---

def generate_mcp_server(manifest: dict, output_dir: Path) -> Path:
    """Generate a FastMCP server from manifest capabilities."""
    name = manifest["name"]
    caps = manifest["capabilities"]

    tools_code = []
    for cap in caps:
        params = []
        schema = cap.get("input_schema", {})
        props = schema.get("properties", {})
        required_fields = schema.get("required", [])

        for pname, pschema in props.items():
            ptype = _json_type_to_python(pschema.get("type", "string"))
            default = f' = "{pschema["default"]}"' if "default" in pschema else ""
            if pname not in required_fields and not default:
                default = " = None"
                ptype = f"Optional[{ptype}]"
            params.append(f"    {pname}: {ptype}{default}")

        params_str = ",\n".join(params)
        if params_str:
            params_str = "\n" + params_str + "\n"

        tools_code.append(f'''
@mcp.tool()
async def {cap["name"]}({params_str}) -> dict[str, Any]:
    """{cap["description"]}"""
    # Implementation: delegate to skill logic
    from skills.{name.replace("-", "_")} import execute
    return await execute("{cap["name"]}", locals())
''')

    server_code = f'''#!/usr/bin/env python3
"""
{manifest["description"]}

Auto-generated MCP server from TECHKNOWMAD Universal Skill Manifest.
Skill: {name} v{manifest["version"]}
"""

import os
from typing import Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name="{name}", version="{manifest["version"]}")
{"".join(tools_code)}

if __name__ == "__main__":
    mcp.run()
'''

    out = output_dir / "mcp" / name
    out.mkdir(parents=True, exist_ok=True)
    server_file = out / "server.py"
    server_file.write_text(server_code)

    # Generate pyproject.toml
    deps = manifest.get("dependencies", {}).get("packages", [])
    deps_str = ", ".join(f'"{d}"' for d in ["fastmcp>=3.1.0", "python-dotenv>=1.0.0"] + deps)
    pyproject = f'''[project]
name = "{name}-mcp"
version = "{manifest["version"]}"
description = "{manifest["description"]}"
requires-python = ">=3.12"
dependencies = [{deps_str}]
'''
    (out / "pyproject.toml").write_text(pyproject)

    # Generate .env.example
    (out / ".env.example").write_text("# Add required environment variables\n")
    (out / ".gitignore").write_text(".env\n__pycache__/\n*.pyc\n.venv/\n")

    return server_file


# --- LangChain Tool Generator ---

def generate_langchain_tools(manifest: dict, output_dir: Path) -> Path:
    """Generate LangChain BaseTool classes from manifest."""
    name = manifest["name"]
    caps = manifest["capabilities"]

    tool_classes = []
    for cap in caps:
        class_name = _snake_to_pascal(cap["name"]) + "Tool"
        schema = cap.get("input_schema", {})
        props = schema.get("properties", {})

        fields = []
        for pname, pschema in props.items():
            ptype = _json_type_to_python(pschema.get("type", "string"))
            desc = pschema.get("description", "")
            fields.append(f'    {pname}: {ptype} = Field(description="{desc}")')

        fields_str = "\n".join(fields) if fields else "    pass"

        tool_classes.append(f'''
class {class_name}Input(BaseModel):
{fields_str}


class {class_name}(BaseTool):
    name: str = "{cap["name"]}"
    description: str = "{cap["description"]}"
    args_schema: type[BaseModel] = {class_name}Input

    def _run(self, **kwargs) -> str:
        from skills.{name.replace("-", "_")} import execute_sync
        return json.dumps(execute_sync("{cap["name"]}", kwargs))

    async def _arun(self, **kwargs) -> str:
        from skills.{name.replace("-", "_")} import execute
        result = await execute("{cap["name"]}", kwargs)
        return json.dumps(result)
''')

    code = f'''#!/usr/bin/env python3
"""
LangChain tool wrappers for {name}.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
{"".join(tool_classes)}

def get_all_tools() -> list[BaseTool]:
    """Return all tools for this skill."""
    return [{", ".join(_snake_to_pascal(c["name"]) + "Tool()" for c in caps)}]
'''

    out = output_dir / "langchain" / name
    out.mkdir(parents=True, exist_ok=True)
    tools_file = out / "tools.py"
    tools_file.write_text(code)
    return tools_file


# --- CrewAI Tool Generator ---

def generate_crewai_tools(manifest: dict, output_dir: Path) -> Path:
    """Generate CrewAI tool classes from manifest."""
    name = manifest["name"]
    caps = manifest["capabilities"]

    tool_classes = []
    for cap in caps:
        class_name = _snake_to_pascal(cap["name"]) + "Tool"
        schema = cap.get("input_schema", {})
        props = schema.get("properties", {})

        fields = []
        for pname, pschema in props.items():
            ptype = _json_type_to_python(pschema.get("type", "string"))
            desc = pschema.get("description", "")
            fields.append(f'    {pname}: {ptype} = Field(description="{desc}")')

        fields_str = "\n".join(fields) if fields else "    pass"

        tool_classes.append(f'''
class {class_name}Schema(BaseModel):
{fields_str}


class {class_name}(BaseTool):
    name: str = "{cap["name"]}"
    description: str = "{cap["description"]}"
    args_schema: type[BaseModel] = {class_name}Schema

    def _run(self, **kwargs) -> str:
        from skills.{name.replace("-", "_")} import execute_sync
        return json.dumps(execute_sync("{cap["name"]}", kwargs))
''')

    code = f'''#!/usr/bin/env python3
"""
CrewAI tool wrappers for {name}.
Auto-generated from TECHKNOWMAD Universal Skill Manifest.
"""

import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
{"".join(tool_classes)}
'''

    out = output_dir / "crewai" / name
    out.mkdir(parents=True, exist_ok=True)
    tools_file = out / "tools.py"
    tools_file.write_text(code)
    return tools_file


# --- OpenAI GPT Action (OpenAPI spec) Generator ---

def generate_openapi_spec(manifest: dict, output_dir: Path) -> Path:
    """Generate OpenAPI 3.1 spec for OpenAI GPT Actions."""
    name = manifest["name"]
    caps = manifest["capabilities"]

    paths = {}
    for cap in caps:
        schema = cap.get("input_schema", {})
        paths[f"/{cap['name']}"] = {
            "post": {
                "operationId": cap["name"],
                "summary": cap["description"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": schema
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": cap.get("output_schema", {"type": "object"})
                            }
                        }
                    }
                }
            }
        }

    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": f"{name} API",
            "version": manifest["version"],
            "description": manifest["description"]
        },
        "servers": [{"url": f"https://api.techknowmad.ai/skills/{name}"}],
        "paths": paths
    }

    out = output_dir / "openai" / name
    out.mkdir(parents=True, exist_ok=True)
    spec_file = out / "openapi.json"
    spec_file.write_text(json.dumps(spec, indent=2))
    return spec_file


# --- AGENTS.md Generator ---

def generate_agents_md(manifest: dict, output_dir: Path) -> Path:
    """Generate AGENTS.md for cross-platform discovery."""
    name = manifest["name"]
    caps = manifest["capabilities"]

    tools_section = "\n".join(
        f"- **{c['name']}**: {c['description']}" for c in caps
    )

    content = f"""# {name}

{manifest["description"]}

## Tools

{tools_section}

## Integration

### MCP Server (Claude, Copilot, Cursor, Windsurf, VS Code, JetBrains)
```bash
cd mcp/{name} && uv run python server.py
```

### LangChain / LangGraph
```python
from langchain.{name.replace("-", "_")}.tools import get_all_tools
tools = get_all_tools()
```

### CrewAI
```python
from crewai.{name.replace("-", "_")}.tools import *
```

### OpenAI Custom GPT
Import `openai/{name}/openapi.json` as a GPT Action.

## License

MIT — TECHKNOWMAD LABS
"""

    out = output_dir / "agents" / name
    out.mkdir(parents=True, exist_ok=True)
    agents_file = out / "AGENTS.md"
    agents_file.write_text(content)
    return agents_file


# --- Generate All ---

def generate_all(manifest: dict, output_dir: Path) -> dict[str, Path]:
    """Generate all platform targets."""
    results = {}
    results["mcp"] = generate_mcp_server(manifest, output_dir)
    results["langchain"] = generate_langchain_tools(manifest, output_dir)
    results["crewai"] = generate_crewai_tools(manifest, output_dir)
    results["openai"] = generate_openapi_spec(manifest, output_dir)
    results["agents_md"] = generate_agents_md(manifest, output_dir)
    return results


# --- Helpers ---

def _json_type_to_python(json_type: str) -> str:
    mapping = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }
    return mapping.get(json_type, "Any")


def _snake_to_pascal(name: str) -> str:
    return "".join(word.capitalize() for word in name.split("_"))


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Generate platform-specific tool definitions from a Universal Skill Manifest"
    )
    parser.add_argument("--manifest", required=True, help="Path to skill-manifest.json")
    parser.add_argument(
        "--target",
        choices=["mcp", "langchain", "crewai", "openai", "agents_md", "all"],
        default="all",
        help="Target platform (default: all)"
    )
    parser.add_argument("--output", default="./generated", help="Output directory")

    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    output_dir = Path(args.output)

    generators = {
        "mcp": generate_mcp_server,
        "langchain": generate_langchain_tools,
        "crewai": generate_crewai_tools,
        "openai": generate_openapi_spec,
        "agents_md": generate_agents_md,
        "all": generate_all,
    }

    gen = generators[args.target]
    result = gen(manifest, output_dir)

    if isinstance(result, dict):
        for platform, path in result.items():
            print(f"  [{platform}] {path}")
    else:
        print(f"  [{args.target}] {result}")

    print(f"\nGenerated {args.target} target(s) for: {manifest['name']} v{manifest['version']}")


if __name__ == "__main__":
    main()