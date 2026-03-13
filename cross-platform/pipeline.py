#!/usr/bin/env python3
"""
TECHKNOWMAD Cross-Platform Pipeline

End-to-end pipeline that:
1. Generates Universal Skill Manifests for all cortex skills
2. Generates platform-specific outputs (MCP, LangChain, CrewAI, OpenAPI, AGENTS.md)
3. Validates generated outputs
4. Reports summary

Usage:
    python pipeline.py                    # Full pipeline
    python pipeline.py --manifests-only   # Just generate manifests
    python pipeline.py --generate-only    # Just generate platform outputs
    python pipeline.py --validate         # Validate existing outputs
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_step(name: str, cmd: list[str], cwd: str = ".") -> bool:
    """Run a pipeline step and report status."""
    print(f"\n{'='*60}")
    print(f"  STEP: {name}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"  [FAIL] {name}")
        if result.stderr:
            print(result.stderr)
        return False
    print(f"  [PASS] {name}")
    return True


def generate_manifests(base_dir: Path) -> bool:
    """Step 1: Generate all skill manifests."""
    return run_step(
        "Generate Universal Skill Manifests",
        [sys.executable, "tools/generate_all_manifests.py", "--output", "manifests/"],
        cwd=str(base_dir),
    )


def generate_platform_outputs(base_dir: Path) -> bool:
    """Step 2: Generate platform-specific outputs for all manifests."""
    manifests_dir = base_dir / "manifests"
    success = True
    count = 0

    for manifest_file in sorted(manifests_dir.glob("*.json")):
        if manifest_file.name.startswith("_") or manifest_file.name == "skill-manifest.schema.json":
            continue

        ok = run_step(
            f"Generate outputs: {manifest_file.stem}",
            [
                sys.executable, "adapters/universal_adapter.py",
                "--manifest", str(manifest_file),
                "--target", "all",
                "--output", "generated/",
            ],
            cwd=str(base_dir),
        )
        if ok:
            count += 1
        else:
            success = False

    print(f"\n  Generated platform outputs for {count} skills")
    return success


def validate_outputs(base_dir: Path) -> dict:
    """Step 3: Validate generated outputs exist and are well-formed."""
    generated = base_dir / "generated"
    results = {"mcp": 0, "langchain": 0, "crewai": 0, "openai": 0, "agents_md": 0, "errors": []}

    # Check MCP servers
    mcp_dir = generated / "mcp"
    if mcp_dir.exists():
        for skill_dir in mcp_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "server.py").exists():
                results["mcp"] += 1
                # Check pyproject.toml exists
                if not (skill_dir / "pyproject.toml").exists():
                    results["errors"].append(f"Missing pyproject.toml: {skill_dir.name}")

    # Check LangChain tools
    lc_dir = generated / "langchain"
    if lc_dir.exists():
        for skill_dir in lc_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "tools.py").exists():
                results["langchain"] += 1

    # Check CrewAI tools
    crew_dir = generated / "crewai"
    if crew_dir.exists():
        for skill_dir in crew_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "tools.py").exists():
                results["crewai"] += 1

    # Check OpenAPI specs
    oai_dir = generated / "openai"
    if oai_dir.exists():
        for skill_dir in oai_dir.iterdir():
            if skill_dir.is_dir():
                spec = skill_dir / "openapi.json"
                if spec.exists():
                    # Validate JSON
                    try:
                        data = json.loads(spec.read_text())
                        if "openapi" in data and "paths" in data:
                            results["openai"] += 1
                        else:
                            results["errors"].append(f"Invalid OpenAPI: {skill_dir.name}")
                    except json.JSONDecodeError:
                        results["errors"].append(f"Malformed JSON: {spec}")

    # Check AGENTS.md files
    agents_dir = generated / "agents"
    if agents_dir.exists():
        for skill_dir in agents_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "AGENTS.md").exists():
                results["agents_md"] += 1

    return results


def print_summary(validation: dict):
    """Print pipeline summary."""
    print(f"\n{'='*60}")
    print("  PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"  MCP Servers:      {validation['mcp']}")
    print(f"  LangChain Tools:  {validation['langchain']}")
    print(f"  CrewAI Tools:     {validation['crewai']}")
    print(f"  OpenAPI Specs:    {validation['openai']}")
    print(f"  AGENTS.md Files:  {validation['agents_md']}")

    total = sum(validation[k] for k in ["mcp", "langchain", "crewai", "openai", "agents_md"])
    print(f"  Total Outputs:    {total}")

    if validation["errors"]:
        print(f"\n  Errors ({len(validation['errors'])}):")
        for err in validation["errors"]:
            print(f"    - {err}")
    else:
        print(f"\n  Status: ALL CLEAR")


def main():
    parser = argparse.ArgumentParser(description="TECHKNOWMAD Cross-Platform Pipeline")
    parser.add_argument("--manifests-only", action="store_true", help="Only generate manifests")
    parser.add_argument("--generate-only", action="store_true", help="Only generate platform outputs")
    parser.add_argument("--validate", action="store_true", help="Only validate outputs")
    parser.add_argument("--base-dir", default=".", help="Base directory")

    args = parser.parse_args()
    base_dir = Path(args.base_dir).resolve()

    if args.validate:
        results = validate_outputs(base_dir)
        print_summary(results)
        return

    if not args.generate_only:
        if not generate_manifests(base_dir):
            print("Pipeline failed at manifest generation")
            sys.exit(1)

    if args.manifests_only:
        return

    if not generate_platform_outputs(base_dir):
        print("Pipeline completed with errors")

    results = validate_outputs(base_dir)
    print_summary(results)


if __name__ == "__main__":
    main()