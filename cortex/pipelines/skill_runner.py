"""Universal skill execution runner.

Loads skill definitions, executes them against inputs,
and validates outputs against schemas.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cortex.models.provider import ModelProvider, ModelResponse
from cortex.utils.io import read_json
from cortex.utils.security import sanitize_input, validate_json_schema


@dataclass
class SkillDefinition:
    """Parsed skill definition."""

    name: str
    prompt: str
    schema: dict[str, Any] | None = None
    temperature: float = 0.2
    max_tokens: int = 4096


@dataclass
class SkillResult:
    """Result of executing a skill."""

    skill_name: str
    input_text: str
    output: str
    latency_ms: float = 0.0
    tokens_used: int = 0
    schema_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill": self.skill_name,
            "input": self.input_text[:200],
            "output": self.output[:1000],
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "schema_valid": self.schema_valid,
        }


class SkillRunner:
    """Executes skills with input sanitization and output validation."""

    def __init__(self, provider: ModelProvider, skills_dir: str | Path = "cortex/skills") -> None:
        self._provider = provider
        self._skills_dir = Path(skills_dir)

    def load_skill(self, skill_name: str) -> SkillDefinition:
        """Load a skill definition from the skills directory."""
        skill_dir = self._skills_dir / skill_name

        # Load prompt
        prompt_path = skill_dir / "prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Skill prompt not found: {prompt_path}")
        prompt = prompt_path.read_text()

        # Load schema (optional)
        schema = None
        schema_path = skill_dir / "schema.json"
        if schema_path.exists():
            schema = read_json(schema_path)

        return SkillDefinition(name=skill_name, prompt=prompt, schema=schema)

    def run(self, skill: SkillDefinition, input_text: str) -> SkillResult:
        """Execute a skill against input text.

        Sanitizes input, calls the model, and validates output.
        """
        # Sanitize input
        clean_input = sanitize_input(input_text)

        # Build full prompt
        full_prompt = f"{skill.prompt}\n\n{clean_input}"

        # Execute
        start = time.time()
        response = self._provider.generate(
            full_prompt,
            temperature=skill.temperature,
            max_tokens=skill.max_tokens,
        )
        latency = (time.time() - start) * 1000

        # Validate output against schema
        validation_errors: list[str] = []
        schema_valid = True
        if skill.schema:
            try:
                output_data = json.loads(response.content)
                validation_errors = validate_json_schema(output_data, skill.schema)
                schema_valid = len(validation_errors) == 0
            except json.JSONDecodeError:
                validation_errors = ["Output is not valid JSON"]
                schema_valid = False

        return SkillResult(
            skill_name=skill.name,
            input_text=clean_input,
            output=response.content,
            latency_ms=round(latency, 2),
            tokens_used=response.tokens_used,
            schema_valid=schema_valid,
            validation_errors=validation_errors,
        )

    def run_by_name(self, skill_name: str, input_text: str) -> SkillResult:
        """Load and run a skill by name."""
        skill = self.load_skill(skill_name)
        return self.run(skill, input_text)
