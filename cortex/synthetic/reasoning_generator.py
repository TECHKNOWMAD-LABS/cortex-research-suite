"""Reasoning prompt generator for logic, causal analysis, and counterfactual evaluation.

Generates multi-step reasoning, causal inference, and counterfactual analysis prompts
across diverse domains.
"""

from __future__ import annotations

from cortex.synthetic.base_generator import BaseGenerator, GeneratedPrompt

_TEMPLATES = [
    "Explain the causal relationships between {topic_a} and {topic_b}.",
    "Analyze the second-order effects of {topic_a} on {topic_b}.",
    "Given that {premise}, what are the logical implications for {topic_b}?",
    "Compare and contrast the mechanisms by which {topic_a} influences {topic_b}.",
    "Construct a multi-step argument for why {topic_a} leads to changes in {topic_b}.",
    "Identify potential confounding factors in the relationship between {topic_a} and {topic_b}.",
    "If {premise}, what would be the counterfactual outcome for {topic_b}?",
    "Evaluate the strength of evidence linking {topic_a} to {topic_b}.",
    "Propose a falsifiable hypothesis about the relationship between {topic_a} and {topic_b}.",
    "Trace the chain of causation from {topic_a} through intermediate factors to {topic_b}.",
]

_TOPICS = [
    "AI automation", "labor market dynamics", "global supply chains",
    "energy transition", "monetary policy", "healthcare access",
    "education technology", "urbanization", "climate adaptation",
    "demographic shifts", "digital infrastructure", "food security",
    "geopolitical realignment", "quantum computing adoption",
    "regulatory frameworks", "social mobility", "innovation ecosystems",
    "data governance", "biotechnology advances", "space commercialization",
]

_PREMISES = [
    "automation replaces 30% of routine jobs within a decade",
    "interest rates remain elevated for five years",
    "a major supply chain disruption occurs in semiconductor manufacturing",
    "renewable energy becomes cheaper than fossil fuels globally",
    "universal basic income is adopted by three major economies",
    "AI achieves human-level performance on most cognitive tasks",
    "global population growth reverses in developed nations",
    "quantum computers break current encryption standards",
]

_HARD_TEMPLATES = [
    "Construct a formal argument with at least 5 logical steps showing how {topic_a} impacts {topic_b}, explicitly identifying each inference rule used.",
    "Analyze the feedback loops between {topic_a} and {topic_b}. Identify at least two positive and two negative feedback mechanisms.",
    "Given competing hypotheses about {topic_a}'s effect on {topic_b}, design a decision framework to evaluate which hypothesis is most likely correct.",
    "Model the interaction between {topic_a} and {topic_b} as a system with inputs, outputs, and state variables. Identify potential tipping points.",
]


class ReasoningGenerator(BaseGenerator):
    """Generates multi-step reasoning evaluation prompts."""

    @property
    def category(self) -> str:
        return "reasoning"

    def generate(self, n: int) -> list[GeneratedPrompt]:
        prompts: list[GeneratedPrompt] = []
        for _ in range(n):
            difficulty = self._weighted_difficulty()
            topic_a = self._pick(_TOPICS)
            topic_b = self._pick([t for t in _TOPICS if t != topic_a])
            premise = self._pick(_PREMISES)

            if difficulty == "hard":
                template = self._pick(_HARD_TEMPLATES)
            else:
                template = self._pick(_TEMPLATES)

            prompt_text = template.format(
                topic_a=topic_a,
                topic_b=topic_b,
                premise=premise,
            )
            prompts.append(
                GeneratedPrompt(
                    prompt=prompt_text,
                    category="reasoning",
                    difficulty=difficulty,
                    expected_structure="analysis",
                    tags=("logic", "causal", difficulty),
                )
            )
        return prompts
