#!/usr/bin/env python3
"""
TECHKNOWMAD Skill-to-Manifest Converter

Parses SKILL.md files from the cortex repo and generates Universal Skill Manifests.
Handles YAML frontmatter extraction, script introspection, and capability inference.

Usage:
    python skill_to_manifest.py --skills-dir ./skills --output ./manifests
    python skill_to_manifest.py --skill ./skills/security-audit --output ./manifests
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Capability:
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)


@dataclass
class SkillManifest:
    name: str
    version: str
    description: str
    author: str = "TECHKNOWMAD LABS"
    license: str = "MIT"
    repository: str = ""
    capabilities: list = field(default_factory=list)
    platforms: dict = field(default_factory=dict)
    dependencies: dict = field(default_factory=dict)


def parse_frontmatter(skill_md_path: Path) -> dict[str, str]:
    """Extract YAML frontmatter from SKILL.md."""
    content = skill_md_path.read_text()
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        raise ValueError(f"No YAML frontmatter found in {skill_md_path}")

    frontmatter = {}
    raw = match.group(1)

    # Parse simple YAML (name, description with multi-line >)
    current_key = None
    current_value = []

    for line in raw.split('\n'):
        key_match = re.match(r'^(\w+):\s*(.*)', line)
        if key_match:
            if current_key:
                frontmatter[current_key] = ' '.join(current_value).strip()
            current_key = key_match.group(1)
            val = key_match.group(2).strip()
            if val == '>':
                current_value = []
            else:
                current_value = [val]
        elif current_key and line.startswith('  '):
            current_value.append(line.strip())

    if current_key:
        frontmatter[current_key] = ' '.join(current_value).strip()

    return frontmatter


def extract_triggers(skill_md_path: Path) -> list[str]:
    """Extract trigger phrases from the description field."""
    content = skill_md_path.read_text()
    triggers = []

    # Find quoted phrases in description that look like triggers
    matches = re.findall(r'"([^"]+)"', content[:2000])
    for m in matches:
        if len(m) < 60 and not m.startswith('http'):
            triggers.append(m)

    return triggers[:20]  # Cap at 20


def detect_scripts(skill_dir: Path) -> list[dict]:
    """Detect Python scripts and their CLI arguments."""
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return []

    scripts = []
    for py_file in scripts_dir.glob("*.py"):
        script_info = {
            "name": py_file.stem,
            "path": f"scripts/{py_file.name}",
            "args": extract_argparse_args(py_file),
        }
        scripts.append(script_info)

    return scripts


def extract_argparse_args(script_path: Path) -> list[dict]:
    """Extract argparse arguments from a Python script via regex."""
    content = script_path.read_text()
    args = []

    # Match add_argument calls
    pattern = r'add_argument\(\s*["\']--?([\w-]+)["\']'
    for match in re.finditer(pattern, content):
        arg_name = match.group(1)
        # Try to find help text
        help_match = re.search(
            rf'add_argument\([^)]*["\']--?{re.escape(arg_name)}["\'][^)]*help=["\']([^"\']+)',
            content
        )
        help_text = help_match.group(1) if help_match else ""

        # Try to find type
        type_match = re.search(
            rf'add_argument\([^)]*["\']--?{re.escape(arg_name)}["\'][^)]*type=(\w+)',
            content
        )
        arg_type = type_match.group(1) if type_match else "string"

        # Try to find required
        required = bool(re.search(
            rf'add_argument\([^)]*["\']--?{re.escape(arg_name)}["\'][^)]*required=True',
            content
        ))

        args.append({
            "name": arg_name,
            "type": arg_type,
            "description": help_text,
            "required": required,
        })

    return args


def detect_references(skill_dir: Path) -> list[str]:
    """Detect reference files."""
    refs_dir = skill_dir / "references"
    if not refs_dir.exists():
        return []
    return [f"references/{f.name}" for f in refs_dir.glob("*.md")]


def infer_capabilities(
    name: str,
    description: str,
    scripts: list[dict],
    skill_md_path: Path
) -> list[dict]:
    """Infer tool capabilities from scripts and SKILL.md content."""
    capabilities = []

    for script in scripts:
        # Build input schema from argparse args
        properties = {}
        required = []
        for arg in script["args"]:
            prop = {"type": _python_type_to_json(arg["type"])}
            if arg["description"]:
                prop["description"] = arg["description"]
            properties[arg["name"].replace("-", "_")] = prop
            if arg["required"]:
                required.append(arg["name"].replace("-", "_"))

        cap = {
            "name": f"{name.replace('-', '_')}_{script['name']}",
            "description": f"Run {script['name']} from {name} skill",
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pass", "warn", "fail"]},
                    "report": {"type": "string", "description": "Report content"},
                    "findings": {"type": "array", "items": {"type": "object"}},
                },
            },
        }
        capabilities.append(cap)

    # If no scripts found, create a single capability from the skill itself
    if not capabilities:
        capabilities.append({
            "name": name.replace("-", "_"),
            "description": description[:200],
            "input_schema": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target directory or file path",
                    }
                },
                "required": ["target"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "result": {"type": "object"},
                },
            },
        })

    return capabilities


def build_platforms(name: str) -> dict:
    """Build platform configuration block."""
    return {
        "claude_skill": {
            "entry_point": "SKILL.md",
            "triggers": [],  # Will be filled from description
        },
        "mcp_server": {
            "transport": "stdio",
            "entry_point": f"mcp/{name}/server.py",
            "command": "uv",
            "args": ["--directory", f"mcp/{name}", "run", "python", "server.py"],
        },
        "langchain": {
            "tool_class": f"{_snake_to_pascal(name)}Tool",
            "module_path": f"langchain.{name.replace('-', '_')}.tools",
        },
        "crewai": {
            "tool_class": f"{_snake_to_pascal(name)}Tool",
            "module_path": f"crewai.{name.replace('-', '_')}.tools",
        },
        "openai_gpt": {
            "action_schema_url": f"https://api.techknowmad.ai/skills/{name}/openapi.json",
            "openapi_spec": f"openai/{name}/openapi.json",
        },
        "github_copilot": {
            "mcp_config": {
                "command": "uv",
                "args": ["--directory", f"mcp/{name}", "run", "python", "server.py"],
            }
        },
    }


def build_dependencies(skill_dir: Path) -> dict:
    """Detect dependencies from scripts."""
    deps = {
        "python": ">=3.12",
        "packages": [],
        "system": [],
    }

    # Scan scripts for imports
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.glob("*.py"):
            content = py_file.read_text()
            # Detect common external imports
            if "import requests" in content or "from requests" in content:
                deps["packages"].append("requests>=2.31.0")
            if "import yaml" in content or "from yaml" in content:
                deps["packages"].append("pyyaml>=6.0")
            if "import bandit" in content:
                deps["packages"].append("bandit>=1.7.0")
                deps["system"].append("bandit")
            if "import semgrep" in content or "semgrep" in content:
                deps["system"].append("semgrep")

    deps["packages"] = list(set(deps["packages"]))
    deps["system"] = list(set(deps["system"]))
    return deps


def convert_skill(skill_dir: Path, version: str = "1.0.0") -> dict:
    """Convert a single skill directory to a Universal Manifest."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"No SKILL.md found in {skill_dir}")

    frontmatter = parse_frontmatter(skill_md)
    name = frontmatter.get("name", skill_dir.name)
    description = frontmatter.get("description", "")

    # Clean up description — collapse whitespace
    description = re.sub(r'\s+', ' ', description).strip()

    scripts = detect_scripts(skill_dir)
    triggers = extract_triggers(skill_md)
    capabilities = infer_capabilities(name, description, scripts, skill_md)
    platforms = build_platforms(name)
    platforms["claude_skill"]["triggers"] = triggers
    dependencies = build_dependencies(skill_dir)

    manifest = {
        "name": name,
        "version": version,
        "description": description[:300],
        "author": "TECHKNOWMAD LABS",
        "license": "MIT",
        "repository": f"https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/tree/main/skills/{name}",
        "capabilities": capabilities,
        "platforms": platforms,
        "dependencies": dependencies,
    }

    return manifest


def convert_all(skills_dir: Path, output_dir: Path, version: str = "1.0.0"):
    """Convert all skills in a directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").exists():
            continue

        try:
            manifest = convert_skill(skill_dir, version)
            out_file = output_dir / f"{manifest['name']}.json"
            out_file.write_text(json.dumps(manifest, indent=2))
            results[manifest["name"]] = {"status": "ok", "path": str(out_file)}
            print(f"  [OK] {manifest['name']} -> {out_file}")
        except Exception as e:
            results[skill_dir.name] = {"status": "error", "error": str(e)}
            print(f"  [ERR] {skill_dir.name}: {e}", file=sys.stderr)

    # Write index file
    index = {
        "generated": True,
        "skill_count": len([r for r in results.values() if r["status"] == "ok"]),
        "skills": results,
    }
    (output_dir / "_index.json").write_text(json.dumps(index, indent=2))
    return results


# --- Helpers ---

def _python_type_to_json(py_type: str) -> str:
    mapping = {
        "str": "string",
        "string": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "dict": "object",
    }
    return mapping.get(py_type, "string")


def _snake_to_pascal(name: str) -> str:
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Convert TECHKNOWMAD cortex skills to Universal Skill Manifests"
    )
    parser.add_argument("--skill", help="Path to a single skill directory")
    parser.add_argument("--skills-dir", help="Path to directory containing all skills")
    parser.add_argument("--output", default="./manifests", help="Output directory")
    parser.add_argument("--version", default="1.0.0", help="Version to assign")

    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.skill:
        skill_dir = Path(args.skill)
        manifest = convert_skill(skill_dir, args.version)
        out_file = output_dir / f"{manifest['name']}.json"
        out_file.write_text(json.dumps(manifest, indent=2))
        print(f"Generated: {out_file}")
    elif args.skills_dir:
        convert_all(Path(args.skills_dir), output_dir, args.version)
    else:
        parser.error("Provide either --skill or --skills-dir")


if __name__ == "__main__":
    main()