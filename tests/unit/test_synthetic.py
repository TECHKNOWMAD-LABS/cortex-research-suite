"""Tests for synthetic data generators."""

from __future__ import annotations

import pytest

from cortex.synthetic.base_generator import GeneratedPrompt
from cortex.synthetic.reasoning_generator import ReasoningGenerator
from cortex.synthetic.research_generator import ResearchGenerator
from cortex.synthetic.strategy_generator import StrategyGenerator
from cortex.synthetic.domain_generator import DomainGenerator
from cortex.synthetic.adversarial_generator import AdversarialGenerator
from cortex.synthetic.validator import DatasetValidator


class TestGeneratedPrompt:
    def test_fingerprint_is_deterministic(self):
        p = GeneratedPrompt(prompt="test prompt", category="test")
        assert p.fingerprint == p.fingerprint

    def test_different_prompts_different_fingerprints(self):
        p1 = GeneratedPrompt(prompt="prompt one", category="test")
        p2 = GeneratedPrompt(prompt="prompt two", category="test")
        assert p1.fingerprint != p2.fingerprint

    def test_to_dict(self):
        p = GeneratedPrompt(prompt="test", category="reasoning", difficulty="hard")
        d = p.to_dict()
        assert d["prompt"] == "test"
        assert d["category"] == "reasoning"
        assert d["difficulty"] == "hard"
        assert "fingerprint" in d


class TestReasoningGenerator:
    def test_generates_correct_count(self):
        gen = ReasoningGenerator(seed=42)
        prompts = gen.generate(10)
        assert len(prompts) == 10

    def test_all_prompts_are_reasoning_category(self):
        gen = ReasoningGenerator(seed=42)
        for p in gen.generate(5):
            assert p.category == "reasoning"

    def test_reproducible_with_seed(self):
        gen1 = ReasoningGenerator(seed=42)
        gen2 = ReasoningGenerator(seed=42)
        assert gen1.generate(5)[0].prompt == gen2.generate(5)[0].prompt

    def test_different_seeds_different_output(self):
        gen1 = ReasoningGenerator(seed=1)
        gen2 = ReasoningGenerator(seed=2)
        # Very unlikely to be identical with different seeds
        p1 = [p.prompt for p in gen1.generate(10)]
        p2 = [p.prompt for p in gen2.generate(10)]
        assert p1 != p2

    def test_category_property(self):
        assert ReasoningGenerator(seed=1).category == "reasoning"


class TestResearchGenerator:
    def test_generates_correct_count(self):
        gen = ResearchGenerator(seed=42)
        assert len(gen.generate(20)) == 20

    def test_category(self):
        assert ResearchGenerator(seed=1).category == "research"


class TestStrategyGenerator:
    def test_generates_correct_count(self):
        gen = StrategyGenerator(seed=42)
        assert len(gen.generate(15)) == 15

    def test_category(self):
        assert StrategyGenerator(seed=1).category == "strategy"


class TestDomainGenerator:
    def test_healthcare_domain(self):
        gen = DomainGenerator(domain="healthcare", seed=42)
        prompts = gen.generate(5)
        assert len(prompts) == 5
        assert all(p.category == "domain_healthcare" for p in prompts)

    def test_finance_domain(self):
        gen = DomainGenerator(domain="finance", seed=42)
        prompts = gen.generate(5)
        assert all(p.category == "domain_finance" for p in prompts)

    def test_invalid_domain_raises(self):
        with pytest.raises(ValueError, match="Unknown domain"):
            DomainGenerator(domain="nonexistent")


class TestAdversarialGenerator:
    def test_generates_correct_count(self):
        gen = AdversarialGenerator(seed=42)
        assert len(gen.generate(10)) == 10

    def test_all_adversarial_category(self):
        gen = AdversarialGenerator(seed=42)
        for p in gen.generate(5):
            assert p.category == "adversarial"
            assert p.difficulty == "adversarial"

    def test_specific_categories(self):
        gen = AdversarialGenerator(seed=42, categories=["ambiguity"])
        prompts = gen.generate(5)
        assert all(p.metadata.get("adversarial_type") == "ambiguity" for p in prompts)

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError, match="Unknown adversarial category"):
            AdversarialGenerator(categories=["nonexistent"])


class TestDatasetValidator:
    def test_removes_duplicates(self):
        prompts = [
            GeneratedPrompt(prompt="duplicate prompt", category="test"),
            GeneratedPrompt(prompt="duplicate prompt", category="test"),
            GeneratedPrompt(prompt="unique prompt", category="test"),
        ]
        valid, report = DatasetValidator().validate(prompts)
        assert len(valid) == 2
        assert report.duplicates == 1

    def test_removes_empty_prompts(self):
        prompts = [
            GeneratedPrompt(prompt="", category="test"),
            GeneratedPrompt(prompt="  ", category="test"),
            GeneratedPrompt(prompt="valid prompt here", category="test"),
        ]
        valid, report = DatasetValidator().validate(prompts)
        assert len(valid) == 1
        assert report.empty == 2

    def test_enforces_min_length(self):
        prompts = [
            GeneratedPrompt(prompt="ab", category="test"),
            GeneratedPrompt(prompt="a valid prompt that meets minimum length", category="test"),
        ]
        valid, report = DatasetValidator(min_length=10).validate(prompts)
        assert len(valid) == 1
        assert report.too_short == 1

    def test_enforces_max_length(self):
        prompts = [
            GeneratedPrompt(prompt="x" * 20_000, category="test"),
            GeneratedPrompt(prompt="normal prompt", category="test"),
        ]
        valid, report = DatasetValidator(max_length=10_000).validate(prompts)
        assert len(valid) == 1
        assert report.too_long == 1

    def test_pass_rate(self):
        prompts = [
            GeneratedPrompt(prompt="valid prompt one", category="test"),
            GeneratedPrompt(prompt="valid prompt two", category="test"),
            GeneratedPrompt(prompt="", category="test"),
        ]
        _, report = DatasetValidator().validate(prompts)
        assert report.pass_rate == pytest.approx(2 / 3, rel=0.01)

    def test_category_distribution(self):
        prompts = [
            GeneratedPrompt(prompt="reasoning prompt", category="reasoning"),
            GeneratedPrompt(prompt="strategy prompt", category="strategy"),
            GeneratedPrompt(prompt="another reasoning", category="reasoning"),
        ]
        _, report = DatasetValidator().validate(prompts)
        assert report.category_distribution == {"reasoning": 2, "strategy": 1}
