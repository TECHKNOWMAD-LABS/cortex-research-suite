"""
Skill DNA Module
Represents and manipulates skill genetic material (SKILL.md content).
"""

import re
import logging
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SkillDNA:
    """Structured representation of skill genetic material."""
    
    skill_id: str
    role: str
    triggers: List[str]
    instructions: str
    tools: List[str]
    output_format: str
    error_handling: str
    metadata: Dict
    raw_content: str

    @classmethod
    def from_skill_file(cls, skill_path: Path) -> Optional["SkillDNA"]:
        """Parse a SKILL.md file into SkillDNA."""
        try:
            with open(skill_path, "r") as f:
                content = f.read()
            
            # Extract frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_str = parts[1]
                    body = parts[2].strip()
                else:
                    frontmatter_str = ""
                    body = content
            else:
                frontmatter_str = ""
                body = content

            # Parse YAML-like frontmatter
            metadata = cls._parse_frontmatter(frontmatter_str)
            skill_id = metadata.get("id", skill_path.stem)

            # Extract sections from body
            role = cls._extract_section(body, r"(?:^|\n)#+\s*Role\s*\n(.*?)(?=\n#+\s*\w|\Z)", 1)
            triggers_text = cls._extract_section(body, r"(?:^|\n)#+\s*Triggers?\s*\n(.*?)(?=\n#+\s*\w|\Z)", 1)
            instructions = cls._extract_section(body, r"(?:^|\n)#+\s*Instructions?\s*\n(.*?)(?=\n#+\s*\w|\Z)", 1)
            tools_text = cls._extract_section(body, r"(?:^|\n)#+\s*Tools?\s*\n(.*?)(?=\n#+\s*\w|\Z)", 1)
            output_format = cls._extract_section(body, r"(?:^|\n)#+\s*Output\s+Format\s*\n(.*?)(?=\n#+\s*\w|\Z)", 1)
            error_handling = cls._extract_section(body, r"(?:^|\n)#+\s*Error\s+Handling\s*\n(.*?)(?=\n#+\s*\w|\Z)", 1)

            # Parse tools list
            tools = cls._parse_list(tools_text) if tools_text else []
            triggers = cls._parse_list(triggers_text) if triggers_text else []

            return cls(
                skill_id=skill_id,
                role=role,
                triggers=triggers,
                instructions=instructions,
                tools=tools,
                output_format=output_format,
                error_handling=error_handling,
                metadata=metadata,
                raw_content=content,
            )
        except Exception as e:
            logger.error(f"Failed to parse skill file {skill_path}: {e}")
            return None

    @staticmethod
    def _parse_frontmatter(frontmatter_str: str) -> Dict:
        """Parse YAML-like frontmatter."""
        metadata = {}
        for line in frontmatter_str.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip().lower()] = value.strip()
        return metadata

    @staticmethod
    def _extract_section(content: str, pattern: str, group: int = 0) -> str:
        """Extract a section from content using regex."""
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(group).strip() if group else match.group(0).strip()
        return ""

    @staticmethod
    def _parse_list(text: str) -> List[str]:
        """Parse markdown list into list of strings."""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "* ", "+ ")):
                items.append(line[2:].strip())
            elif line and not line.startswith("#"):
                items.append(line)
        return [item for item in items if item]

    def to_skill_md(self) -> str:
        """Serialize SkillDNA back to SKILL.md format."""
        lines = ["---"]
        
        # Write metadata
        for key, value in self.metadata.items():
            lines.append(f"{key}: {value}")
        lines.append("---\n")

        # Write sections
        if self.role:
            lines.append("# Role")
            lines.append(self.role)
            lines.append("")

        if self.triggers:
            lines.append("# Triggers")
            for trigger in self.triggers:
                lines.append(f"- {trigger}")
            lines.append("")

        if self.instructions:
            lines.append("# Instructions")
            lines.append(self.instructions)
            lines.append("")

        if self.tools:
            lines.append("# Tools")
            for tool in self.tools:
                lines.append(f"- {tool}")
            lines.append("")

        if self.output_format:
            lines.append("# Output Format")
            lines.append(self.output_format)
            lines.append("")

        if self.error_handling:
            lines.append("# Error Handling")
            lines.append(self.error_handling)
            lines.append("")

        return "\n".join(lines)

    def get_genetic_signature(self) -> str:
        """Get hash signature of skill's genetic material."""
        combined = f"{self.role}|{self.instructions}|{','.join(self.tools)}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def similarity(self, other: "SkillDNA") -> float:
        """Compute similarity to another skill (0-1)."""
        if not self.instructions or not other.instructions:
            return 0.0

        # Use sequence matcher for text similarity
        matcher = SequenceMatcher(None, self.instructions, other.instructions)
        text_similarity = matcher.ratio()

        # Tools overlap
        self_tools = set(self.tools)
        other_tools = set(other.tools)
        if self_tools or other_tools:
            tools_overlap = len(self_tools & other_tools) / len(self_tools | other_tools)
        else:
            tools_overlap = 1.0

        return round((text_similarity * 0.7 + tools_overlap * 0.3), 3)


def crossover(skill_a: SkillDNA, skill_b: SkillDNA) -> SkillDNA:
    """Combine traits from two skills (genetic crossover)."""
    # Create hybrid skill
    combined_tools = list(set(skill_a.tools + skill_b.tools))
    combined_triggers = list(set(skill_a.triggers + skill_b.triggers))
    
    # Merge instructions intelligently
    combined_instructions = f"{skill_a.instructions}\n\n[From {skill_b.skill_id}]: {skill_b.instructions}"
    
    # Hybrid role
    hybrid_role = f"{skill_a.role} (with {skill_b.skill_id} traits)"

    # Hybrid metadata
    hybrid_metadata = {**skill_a.metadata, **skill_b.metadata}

    hybrid_skill_id = f"{skill_a.skill_id}_x_{skill_b.skill_id}"

    return SkillDNA(
        skill_id=hybrid_skill_id,
        role=hybrid_role,
        triggers=combined_triggers,
        instructions=combined_instructions,
        tools=combined_tools,
        output_format=skill_a.output_format or skill_b.output_format,
        error_handling=skill_a.error_handling or skill_b.error_handling,
        metadata=hybrid_metadata,
        raw_content="",
    )


def mutate(skill: SkillDNA, mutation_rate: float = 0.1) -> SkillDNA:
    """Create mutated version of skill (small random improvements)."""
    import random

    mutated = SkillDNA(
        skill_id=skill.skill_id,
        role=skill.role,
        triggers=skill.triggers.copy(),
        instructions=skill.instructions,
        tools=skill.tools.copy(),
        output_format=skill.output_format,
        error_handling=skill.error_handling,
        metadata=skill.metadata.copy(),
        raw_content=skill.raw_content,
    )

    # Mutation 1: Add improvement phrase to instructions
    if random.random() < mutation_rate:
        improvements = [
            "Prioritize clarity and conciseness.",
            "Include error handling for edge cases.",
            "Provide concrete examples where applicable.",
            "Focus on measurable outcomes.",
        ]
        mutated.instructions += f"\n\n[Mutation]: {random.choice(improvements)}"

    # Mutation 2: Add new trigger
    if random.random() < mutation_rate:
        mutated.triggers.append(f"Triggered by {skill.skill_id} evolution event")

    # Mutation 3: Optimize error handling
    if random.random() < mutation_rate and not mutated.error_handling:
        mutated.error_handling = "Log errors with full context. Retry with exponential backoff."

    return mutated
