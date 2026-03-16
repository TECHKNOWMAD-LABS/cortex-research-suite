#!/usr/bin/env python3
"""
TECHKNOWMAD Batch Manifest Generator

Generates Universal Skill Manifests for all cortex skills using repo tree metadata.
Each manifest maps to MCP Server, LangChain Tool, CrewAI Tool, OpenAI GPT Action,
AGENTS.md, and GitHub Copilot MCP config.

Usage:
    python generate_all_manifests.py --output ./manifests
"""

import json
import sys
from pathlib import Path
from typing import Any

# --- Skill Registry ---
# Extracted from TECHKNOWMAD-LABS/cortex-research-suite repo tree + SKILL.md frontmatter

SKILLS = [
    {
        "name": "agent-orchestrator",
        "description": "Multi-agent workflow orchestration with dependency resolution, parallel execution, and fault-tolerant task routing. Coordinates complex pipelines where multiple agents collaborate on compound tasks.",
        "scripts": ["orchestrator.py"],
        "references": ["orchestration-patterns.md"],
        "capabilities": [
            {
                "name": "orchestrate_workflow",
                "description": "Execute a multi-agent workflow with dependency resolution and parallel task routing",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "workflow": {"type": "object", "description": "Workflow definition with tasks, dependencies, and agent assignments"},
                        "config": {"type": "object", "description": "Execution config (parallelism, timeout, retry policy)"},
                        "dry_run": {"type": "boolean", "default": False, "description": "Validate without executing"}
                    },
                    "required": ["workflow"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["completed", "partial", "failed"]},
                        "results": {"type": "array", "items": {"type": "object"}},
                        "execution_graph": {"type": "object"},
                        "duration_ms": {"type": "integer"}
                    }
                }
            }
        ]
    },
    {
        "name": "agent-output-validator",
        "description": "Validates AI agent outputs against schema contracts, quality thresholds, and safety constraints. Catches hallucinations, schema violations, and drift before outputs reach production.",
        "scripts": ["validate_outputs.py"],
        "references": [],
        "capabilities": [
            {
                "name": "validate_output",
                "description": "Validate an agent's output against schema, quality, and safety constraints",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "output": {"type": "object", "description": "Agent output to validate"},
                        "schema": {"type": "object", "description": "Expected output schema"},
                        "quality_threshold": {"type": "number", "default": 0.8, "description": "Minimum quality score (0-1)"},
                        "safety_checks": {"type": "boolean", "default": True, "description": "Run safety constraint checks"}
                    },
                    "required": ["output"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "valid": {"type": "boolean"},
                        "score": {"type": "number"},
                        "violations": {"type": "array", "items": {"type": "object"}},
                        "suggestions": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        ]
    },
    {
        "name": "code-review-engine",
        "description": "Automated code review with multi-dimensional analysis: correctness, security, performance, maintainability, and style. Produces structured findings with severity, location, and suggested fixes.",
        "scripts": ["review_engine.py"],
        "references": ["review-checklist.md"],
        "capabilities": [
            {
                "name": "review_code",
                "description": "Run automated code review on a file or directory with multi-dimensional analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "File or directory path to review"},
                        "language": {"type": "string", "description": "Programming language (auto-detected if omitted)"},
                        "dimensions": {"type": "array", "items": {"type": "string", "enum": ["correctness", "security", "performance", "maintainability", "style"]}, "description": "Review dimensions to check"},
                        "severity_threshold": {"type": "string", "enum": ["critical", "high", "medium", "low"], "default": "low"}
                    },
                    "required": ["target"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["pass", "warn", "fail"]},
                        "findings": {"type": "array", "items": {"type": "object"}},
                        "summary": {"type": "object"},
                        "score": {"type": "number"}
                    }
                }
            }
        ]
    },
    {
        "name": "context-engineer",
        "description": "Builds optimal context windows for LLM interactions. Compresses, prioritizes, and structures information to maximize relevance within token limits. Implements retrieval-augmented context assembly.",
        "scripts": ["context_engine.py"],
        "references": ["context-patterns.md"],
        "capabilities": [
            {
                "name": "build_context",
                "description": "Assemble an optimal context window from multiple sources within token limits",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sources": {"type": "array", "items": {"type": "string"}, "description": "Paths or URIs to context sources"},
                        "query": {"type": "string", "description": "Query to optimize context for"},
                        "max_tokens": {"type": "integer", "default": 8000, "description": "Maximum token budget"},
                        "strategy": {"type": "string", "enum": ["relevance", "recency", "hybrid"], "default": "hybrid"}
                    },
                    "required": ["sources", "query"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "context": {"type": "string"},
                        "token_count": {"type": "integer"},
                        "sources_used": {"type": "array", "items": {"type": "string"}},
                        "compression_ratio": {"type": "number"}
                    }
                }
            }
        ]
    },
    {
        "name": "de-slop",
        "description": "Detects and scores AI-generated writing patterns in markdown and documentation. Scans for emoji abuse, hyperbolic language, defensive framing, buzzword stacking, and motivational fluff. Produces a 0-100 slop score.",
        "scripts": ["slop_scanner.py"],
        "references": ["anti-patterns.md"],
        "capabilities": [
            {
                "name": "scan_slop",
                "description": "Scan text for AI-generated writing patterns and return a slop score with findings",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "File path or directory to scan"},
                        "format": {"type": "string", "enum": ["json", "markdown", "both"], "default": "both"},
                        "fix": {"type": "boolean", "default": False, "description": "Auto-fix detected patterns"}
                    },
                    "required": ["target"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "description": "Slop score 0-100 (lower is better)"},
                        "categories": {"type": "object"},
                        "findings": {"type": "array", "items": {"type": "object"}},
                        "report_path": {"type": "string"}
                    }
                }
            }
        ]
    },
    {
        "name": "design-system-forge",
        "description": "Generates complete design systems from brand parameters. Creates tokens, component specs, documentation, and theme configurations with accessibility compliance built in.",
        "scripts": ["design_forge.py"],
        "references": ["design-rules.md"],
        "capabilities": [
            {
                "name": "generate_design_system",
                "description": "Generate a complete design system from brand parameters",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "brand": {"type": "object", "description": "Brand parameters (colors, typography, spacing)"},
                        "components": {"type": "array", "items": {"type": "string"}, "description": "Components to generate"},
                        "output_dir": {"type": "string", "description": "Output directory for generated system"},
                        "format": {"type": "string", "enum": ["css", "tailwind", "styled-components", "all"], "default": "all"}
                    },
                    "required": ["brand"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "tokens": {"type": "object"},
                        "components": {"type": "array", "items": {"type": "object"}},
                        "output_path": {"type": "string"},
                        "accessibility_score": {"type": "number"}
                    }
                }
            }
        ]
    },
    {
        "name": "dev-lifecycle-engine",
        "description": "Manages the full software development lifecycle from planning through deployment. Tracks phases, gates, artifacts, and provides automated status reporting across the entire pipeline.",
        "scripts": ["lifecycle.py"],
        "references": ["usage-guide.md"],
        "capabilities": [
            {
                "name": "manage_lifecycle",
                "description": "Track and manage software development lifecycle phases and gates",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project": {"type": "string", "description": "Project identifier"},
                        "action": {"type": "string", "enum": ["status", "advance", "gate-check", "report"], "description": "Lifecycle action"},
                        "phase": {"type": "string", "description": "Target phase (planning, development, testing, staging, production)"}
                    },
                    "required": ["project", "action"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "current_phase": {"type": "string"},
                        "gates_passed": {"type": "array", "items": {"type": "string"}},
                        "blockers": {"type": "array", "items": {"type": "object"}},
                        "report": {"type": "object"}
                    }
                }
            }
        ]
    },
    {
        "name": "diff-generator",
        "description": "Creates snapshot-based diffs of file system state. Captures before/after snapshots and generates structured change reports showing additions, deletions, and modifications.",
        "scripts": ["snap_diff.py"],
        "references": [],
        "capabilities": [
            {
                "name": "generate_diff",
                "description": "Generate a structured diff between two file system snapshots",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Directory to snapshot/diff"},
                        "action": {"type": "string", "enum": ["snapshot", "diff", "report"], "default": "diff"},
                        "baseline": {"type": "string", "description": "Path to baseline snapshot"},
                        "format": {"type": "string", "enum": ["json", "markdown", "unified"], "default": "json"}
                    },
                    "required": ["target"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "added": {"type": "array", "items": {"type": "string"}},
                        "deleted": {"type": "array", "items": {"type": "string"}},
                        "modified": {"type": "array", "items": {"type": "object"}},
                        "summary": {"type": "object"}
                    }
                }
            }
        ]
    },
    {
        "name": "github-mcp",
        "description": "GitHub API integration via MCP. Manages repositories, files, branches, pull requests, issues, and releases programmatically without browser automation.",
        "scripts": ["bootstrap.py", "test_connection.py"],
        "references": ["github-api-patterns.md"],
        "capabilities": [
            {
                "name": "github_manage_repo",
                "description": "Create, update, and manage GitHub repositories and their settings",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"},
                        "action": {"type": "string", "enum": ["get", "create", "update", "list"], "description": "Repository action"}
                    },
                    "required": ["owner", "repo", "action"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {"type": "object"}
                    }
                }
            },
            {
                "name": "github_manage_files",
                "description": "Create, read, update, and delete files in GitHub repositories via API",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "path": {"type": "string", "description": "File path in repository"},
                        "action": {"type": "string", "enum": ["get", "create", "update", "delete"]},
                        "content": {"type": "string", "description": "File content (for create/update)"},
                        "message": {"type": "string", "description": "Commit message"},
                        "branch": {"type": "string", "default": "main"}
                    },
                    "required": ["owner", "repo", "path", "action"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "sha": {"type": "string"},
                        "url": {"type": "string"}
                    }
                }
            }
        ]
    },
    {
        "name": "meta-skill-evolver",
        "description": "Analyzes, improves, and evolves Claude Code skills through automated metrics collection, A/B testing, and iterative refinement. Skills that improve themselves.",
        "scripts": ["skill_evolver.py"],
        "references": ["skill-anatomy.md"],
        "capabilities": [
            {
                "name": "evolve_skill",
                "description": "Analyze a skill and generate improved versions based on performance metrics",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "skill_path": {"type": "string", "description": "Path to skill directory"},
                        "metrics": {"type": "object", "description": "Performance metrics from skill usage"},
                        "strategy": {"type": "string", "enum": ["optimize", "extend", "simplify", "auto"], "default": "auto"}
                    },
                    "required": ["skill_path"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "original_score": {"type": "number"},
                        "improved_score": {"type": "number"},
                        "changes": {"type": "array", "items": {"type": "object"}},
                        "output_path": {"type": "string"}
                    }
                }
            }
        ]
    },
    {
        "name": "persistent-memory",
        "description": "Persistent key-value memory system for AI agents. Stores, retrieves, and manages structured knowledge across sessions with TTL, tagging, and semantic search support.",
        "scripts": ["memory_engine.py"],
        "references": ["memory-patterns.md"],
        "capabilities": [
            {
                "name": "memory_operation",
                "description": "Store, retrieve, search, or manage persistent memory entries",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["store", "retrieve", "search", "delete", "list"], "description": "Memory operation"},
                        "key": {"type": "string", "description": "Memory key"},
                        "value": {"type": "object", "description": "Value to store"},
                        "query": {"type": "string", "description": "Search query"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for filtering"},
                        "ttl": {"type": "integer", "description": "Time-to-live in seconds"}
                    },
                    "required": ["action"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {"type": "object"},
                        "results": {"type": "array", "items": {"type": "object"}}
                    }
                }
            }
        ]
    },
    {
        "name": "pre-package-pipeline",
        "description": "Pre-packaging validation pipeline for Claude Code skills. Validates structure, checks references, verifies scripts, and ensures packaging readiness before .skill file creation.",
        "scripts": ["package_pipeline.py"],
        "references": [],
        "capabilities": [
            {
                "name": "validate_package",
                "description": "Run pre-packaging validation on a skill directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "skill_path": {"type": "string", "description": "Path to skill directory"},
                        "strict": {"type": "boolean", "default": True, "description": "Fail on warnings"},
                        "fix": {"type": "boolean", "default": False, "description": "Auto-fix issues"}
                    },
                    "required": ["skill_path"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["pass", "warn", "fail"]},
                        "checks": {"type": "array", "items": {"type": "object"}},
                        "fixable": {"type": "integer"},
                        "report_path": {"type": "string"}
                    }
                }
            }
        ]
    },
    {
        "name": "repo-publisher",
        "description": "Pre-publish pipeline for GitHub repositories. Chains security scanning, AI slop detection, structure validation, and repo metadata updates into a single workflow.",
        "scripts": [],
        "references": ["publish-checklist.md"],
        "capabilities": [
            {
                "name": "publish_repo",
                "description": "Run the full pre-publish pipeline on a repository",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Path to repository"},
                        "owner": {"type": "string", "description": "GitHub owner/org"},
                        "repo": {"type": "string", "description": "Repository name"},
                        "dry_run": {"type": "boolean", "default": False}
                    },
                    "required": ["repo_path"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["pass", "warn", "fail"]},
                        "stages": {"type": "array", "items": {"type": "object"}},
                        "publish_url": {"type": "string"}
                    }
                }
            }
        ]
    },
    {
        "name": "security-audit",
        "description": "Automated security scanning for code repositories. Runs bandit (Python SAST), semgrep (multi-language static analysis), and secret detection to produce machine-readable reports.",
        "scripts": ["security_scan.py"],
        "references": ["severity-matrix.md"],
        "capabilities": [
            {
                "name": "security_scan",
                "description": "Run a full security scan on a target directory with bandit, semgrep, and secret detection",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Directory path to scan"},
                        "output": {"type": "string", "description": "Output path for the report"},
                        "format": {"type": "string", "enum": ["json", "markdown", "both"], "default": "both"},
                        "severity_threshold": {"type": "string", "enum": ["critical", "high", "medium", "low"], "default": "low"}
                    },
                    "required": ["target"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["pass", "warn", "fail"]},
                        "summary": {"type": "object", "properties": {"critical": {"type": "integer"}, "high": {"type": "integer"}, "medium": {"type": "integer"}, "low": {"type": "integer"}, "secrets_detected": {"type": "integer"}}},
                        "findings": {"type": "array", "items": {"type": "object"}},
                        "report_path": {"type": "string"}
                    }
                }
            }
        ]
    },
    {
        "name": "session-memory",
        "description": "Lightweight session-scoped memory with checkpoint and restore. Captures working state snapshots that persist across context window resets within a single session.",
        "scripts": ["checkpoint.py"],
        "references": [],
        "capabilities": [
            {
                "name": "session_checkpoint",
                "description": "Create, restore, or list session memory checkpoints",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["save", "restore", "list", "delete"]},
                        "checkpoint_id": {"type": "string", "description": "Checkpoint identifier"},
                        "data": {"type": "object", "description": "State data to checkpoint"}
                    },
                    "required": ["action"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "checkpoint_id": {"type": "string"},
                        "data": {"type": "object"},
                        "checkpoints": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        ]
    },
    {
        "name": "skill-test-harness",
        "description": "Test framework for Claude Code skills. Runs structured test suites against skills, validates outputs, measures performance, and generates coverage reports.",
        "scripts": ["test_runner.py"],
        "references": [],
        "capabilities": [
            {
                "name": "run_skill_tests",
                "description": "Execute test suites against a Claude Code skill",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "skill_path": {"type": "string", "description": "Path to skill directory"},
                        "test_suite": {"type": "string", "description": "Path to test suite file"},
                        "verbose": {"type": "boolean", "default": False},
                        "coverage": {"type": "boolean", "default": True}
                    },
                    "required": ["skill_path"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "passed": {"type": "integer"},
                        "failed": {"type": "integer"},
                        "skipped": {"type": "integer"},
                        "coverage": {"type": "number"},
                        "results": {"type": "array", "items": {"type": "object"}}
                    }
                }
            }
        ]
    },
    {
        "name": "skill-validator",
        "description": "Validates Claude Code skill structure, frontmatter, scripts, and references against the canonical skill specification. Catches errors before packaging.",
        "scripts": ["skill_validator.py"],
        "references": [],
        "capabilities": [
            {
                "name": "validate_skill",
                "description": "Validate a skill directory against the canonical specification",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "skill_path": {"type": "string", "description": "Path to skill directory"},
                        "strict": {"type": "boolean", "default": True}
                    },
                    "required": ["skill_path"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "valid": {"type": "boolean"},
                        "errors": {"type": "array", "items": {"type": "object"}},
                        "warnings": {"type": "array", "items": {"type": "object"}},
                        "score": {"type": "number"}
                    }
                }
            }
        ]
    },
    {
        "name": "tdd-enforcer",
        "description": "Enforces test-driven development workflow. Validates that tests exist before implementation, checks coverage thresholds, detects test anti-patterns, and blocks commits without adequate test coverage.",
        "scripts": ["tdd_enforcer.py"],
        "references": ["testing-anti-patterns.md"],
        "capabilities": [
            {
                "name": "enforce_tdd",
                "description": "Validate TDD compliance for a codebase — tests exist, coverage meets threshold, no anti-patterns",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Path to codebase"},
                        "coverage_threshold": {"type": "number", "default": 80, "description": "Minimum coverage percentage"},
                        "check_anti_patterns": {"type": "boolean", "default": True},
                        "block_commit": {"type": "boolean", "default": False, "description": "Return exit code for pre-commit hook"}
                    },
                    "required": ["target"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "compliant": {"type": "boolean"},
                        "coverage": {"type": "number"},
                        "anti_patterns": {"type": "array", "items": {"type": "object"}},
                        "missing_tests": {"type": "array", "items": {"type": "string"}},
                        "report": {"type": "object"}
                    }
                }
            }
        ]
    }
]


def build_platforms(name: str, triggers: list[str] | None = None) -> dict:
    """Build platform configuration block for all targets."""
    return {
        "claude_skill": {
            "entry_point": "SKILL.md",
            "triggers": triggers or [],
        },
        "mcp_server": {
            "transport": "stdio",
            "entry_point": f"mcp/{name}/server.py",
            "command": "uv",
            "args": ["--directory", f"mcp/{name}", "run", "python", "server.py"],
        },
        "langchain": {
            "tool_class": f"{''.join(w.capitalize() for w in name.split('-'))}Tool",
            "module_path": f"langchain.{name.replace('-', '_')}.tools",
        },
        "crewai": {
            "tool_class": f"{''.join(w.capitalize() for w in name.split('-'))}Tool",
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


def build_manifest(skill: dict) -> dict:
    """Build a complete Universal Skill Manifest from skill metadata."""
    name = skill["name"]

    # Infer dependencies from skill type
    deps = {"python": ">=3.12", "packages": [], "system": []}
    if name == "security-audit":
        deps["packages"].append("bandit>=1.7.0")
        deps["system"].extend(["bandit", "semgrep"])
    if name == "github-mcp":
        deps["packages"].extend(["fastmcp>=3.1.0", "requests>=2.31.0", "python-dotenv>=1.0.0"])

    # Build triggers from description keywords
    triggers = _extract_triggers(skill["description"])

    return {
        "name": name,
        "version": "1.0.0",
        "description": skill["description"],
        "author": "TECHKNOWMAD LABS",
        "license": "MIT",
        "repository": f"https://github.com/TECHKNOWMAD-LABS/cortex-research-suite/tree/main/skills/{name}",
        "capabilities": skill["capabilities"],
        "platforms": build_platforms(name, triggers),
        "dependencies": deps,
    }


def _extract_triggers(description: str) -> list[str]:
    """Extract likely trigger phrases from description."""
    import re
    # Pull key terms from description
    words = re.findall(r'\b[a-z][\w-]+\b', description.lower())
    # Filter to meaningful triggers (3+ chars, not stopwords)
    stopwords = {"the", "and", "for", "with", "from", "that", "this", "into", "across",
                 "their", "against", "before", "without", "single", "multiple", "complex",
                 "based", "structured", "automated", "produces", "machine", "readable"}
    triggers = [w for w in words if len(w) > 3 and w not in stopwords]
    return list(dict.fromkeys(triggers))[:15]  # Dedupe, cap at 15


def generate_all(output_dir: str = "./manifests"):
    """Generate manifests for all skills."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    results = {}
    for skill in SKILLS:
        manifest = build_manifest(skill)
        out_file = out / f"{skill['name']}.json"
        out_file.write_text(json.dumps(manifest, indent=2))
        results[skill["name"]] = {"status": "ok", "path": str(out_file)}
        print(f"  [OK] {skill['name']} -> {out_file}")

    # Write index
    index = {
        "schema": "techknowmad-universal-skill-manifest",
        "version": "1.0.0",
        "generated": True,
        "skill_count": len(results),
        "skills": {name: {"manifest": f"{name}.json", **info} for name, info in results.items()},
    }
    (out / "_index.json").write_text(json.dumps(index, indent=2))
    print(f"\nGenerated {len(results)} manifests in {out}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Universal Skill Manifests for all cortex skills")
    parser.add_argument("--output", default="./manifests", help="Output directory")
    args = parser.parse_args()
    generate_all(args.output)
