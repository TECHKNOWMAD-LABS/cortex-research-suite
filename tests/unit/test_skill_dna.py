"""Tests for SkillDNA, crossover, and mutate."""

from __future__ import annotations

import sys
from pathlib import Path

ORGANISM_DIR = Path(__file__).parent.parent.parent / "skill-organism"
sys.path.insert(0, str(ORGANISM_DIR))


def _make_dna(skill_id: str = "test-skill", instructions: str = "Do the thing.") -> "SkillDNA":
    from skill_dna import SkillDNA

    return SkillDNA(
        skill_id=skill_id,
        role="tester",
        triggers=["on test"],
        instructions=instructions,
        tools=["tool-a"],
        output_format="JSON",
        error_handling="Log and retry.",
        metadata={"id": skill_id},
        raw_content="# Test\nDo the thing.",
    )


class TestSkillDNA:
    def test_creation(self):
        dna = _make_dna()
        assert dna.skill_id == "test-skill"
        assert dna.role == "tester"
        assert len(dna.tools) == 1

    def test_genetic_signature(self):
        dna = _make_dna()
        sig = dna.get_genetic_signature()
        assert isinstance(sig, str)
        assert len(sig) == 16

    def test_to_skill_md(self):
        dna = _make_dna()
        md = dna.to_skill_md()
        assert "# Role" in md
        assert "tester" in md

    def test_similarity_same(self):
        dna_a = _make_dna(instructions="Same instructions here.")
        dna_b = _make_dna(instructions="Same instructions here.")
        assert dna_a.similarity(dna_b) == 1.0

    def test_similarity_different(self):
        dna_a = _make_dna(instructions="Alpha instructions.")
        dna_b = _make_dna(instructions="Completely different text about something else.")
        assert dna_a.similarity(dna_b) < 1.0


class TestCrossover:
    def test_crossover_produces_hybrid(self):
        from skill_dna import crossover

        parent_a = _make_dna("skill-a", "Analyze data.")
        parent_b = _make_dna("skill-b", "Generate reports.")
        child = crossover(parent_a, parent_b)
        assert "skill-a" in child.skill_id
        assert "skill-b" in child.skill_id
        assert len(child.tools) >= 1


class TestMutate:
    def test_mutate_with_high_rate(self):
        from skill_dna import mutate

        original = _make_dna()
        mutated = mutate(original, mutation_rate=1.0)
        # At rate=1.0 all mutations fire — instructions should differ
        assert mutated.instructions != original.instructions or mutated.triggers != original.triggers

    def test_mutate_with_zero_rate(self):
        from skill_dna import mutate

        original = _make_dna()
        mutated = mutate(original, mutation_rate=0.0)
        assert mutated.instructions == original.instructions
        assert mutated.tools == original.tools
