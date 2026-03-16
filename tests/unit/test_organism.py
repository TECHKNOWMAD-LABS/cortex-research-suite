"""Tests for skill-organism core components."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Load SkillEntry directly from the canonical organism.py to avoid __init__.py telemetry import
ORGANISM_DIR = Path(__file__).parent.parent.parent / "skill-organism"
CANONICAL = ORGANISM_DIR / "cortex_skill_organism" / "organism.py"

sys.path.insert(0, str(ORGANISM_DIR))


def _load_skill_entry():
    """Load SkillEntry without triggering the package __init__.py."""
    spec = importlib.util.spec_from_file_location("_organism", CANONICAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SkillEntry


class TestSkillEntry:
    def test_create_skill_entry(self):
        SkillEntry = _load_skill_entry()
        entry = SkillEntry(
            id="test-skill-001",
            name="test-skill",
            version="1.0.0",
            status="active",
            fitness_score=0.75,
            usage_count=10,
            last_used="2026-03-16T00:00:00Z",
            created="2026-03-01T00:00:00Z",
            category="testing",
            dependencies=[],
            health="healthy",
            generation=1,
            parent_skill=None,
            mutation_count=0,
        )
        assert entry.name == "test-skill"
        assert entry.fitness_score == 0.75
        assert entry.status == "active"

    def test_skill_entry_defaults(self):
        SkillEntry = _load_skill_entry()
        entry = SkillEntry(
            id="test",
            name="test",
            version="1.0.0",
            status="active",
            fitness_score=0.5,
            usage_count=0,
            last_used=None,
            created="2026-03-16",
            category="test",
            dependencies=[],
            health="healthy",
            generation=0,
            parent_skill=None,
            mutation_count=0,
        )
        assert entry.deprecated_at is None
        assert entry.peak_fitness is None
        assert entry.resurrection_count == 0


class TestOrganismRedirect:
    def test_redirect_file_exists(self):
        """The thin redirect at skill-organism/organism.py should exist."""
        redirect_path = ORGANISM_DIR / "organism.py"
        assert redirect_path.exists()
        content = redirect_path.read_text()
        assert "cortex_skill_organism" in content
