"""Tests for ArenaConfig YAML frontmatter parser."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ORGANISM_DIR = Path(__file__).parent.parent.parent / "skill-organism"
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"
sys.path.insert(0, str(ORGANISM_DIR))

from arena_config import ArenaConfig  # noqa: E402


class TestArenaConfig:
    def test_load_from_real_skill(self):
        """Load ArenaConfig from the first available skill directory."""
        skill_dirs = sorted(SKILLS_DIR.iterdir())
        found = None
        for d in skill_dirs:
            if (d / "ARENA.md").exists():
                found = d
                break
        assert found is not None, "No skill with ARENA.md found"

        config = ArenaConfig.load(found)
        assert config.skill_name != ""
        assert config.eval_budget_seconds > 0

    def test_skill_name_populated(self):
        first_skill = next(
            (d for d in sorted(SKILLS_DIR.iterdir()) if (d / "ARENA.md").exists()),
            None,
        )
        assert first_skill is not None
        config = ArenaConfig.load(first_skill)
        assert isinstance(config.skill_name, str)
        assert len(config.skill_name) > 0

    def test_to_browser_json(self):
        first_skill = next(
            (d for d in sorted(SKILLS_DIR.iterdir()) if (d / "ARENA.md").exists()),
            None,
        )
        assert first_skill is not None
        config = ArenaConfig.load(first_skill)
        js = config.to_browser_json()
        assert isinstance(js, str)
        parsed = json.loads(js)
        assert "skill_name" in parsed
