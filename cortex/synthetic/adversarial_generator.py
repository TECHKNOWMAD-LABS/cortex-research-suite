"""Adversarial prompt generator for robustness testing.

Generates prompts designed to test model resilience against:
- Ambiguity and contradictory instructions
- Edge cases and boundary conditions
- Hallucination triggers
- Instruction following under pressure
- Output format compliance stress tests

NOTE: This is for defensive testing only. All prompts are designed
to measure robustness, not to exploit or attack systems.
"""

from __future__ import annotations

from cortex.synthetic.base_generator import BaseGenerator, GeneratedPrompt

_AMBIGUITY_TEMPLATES = [
    "Analyze {topic}. Be concise but also extremely thorough. Cover all angles but keep it under 50 words.",
    "Explain {topic} in a way that is both technically precise and accessible to a five-year-old.",
    "Give me your analysis of {topic}, but don't include any opinions, interpretations, or subjective assessments.",
    "Summarize the key debates about {topic}. Present all sides equally but clearly state which side is correct.",
    "List exactly 7 risks of {topic}. If there are more than 7, explain why you only listed 7. If fewer, explain why there are fewer.",
]

_EDGE_CASE_TEMPLATES = [
    "",  # Empty input
    " ",  # Whitespace only
    "." * 500,  # Repetitive punctuation
    "Analyze the following: {repeated_word}",  # Repetitive content
    "What is the strategic implication of null?",
    "Explain the causal relationship between X and X.",
    "Provide analysis of: [REDACTED]",
    "Respond to this prompt: (this prompt)",
    "If your confidence is below 50%, say so. Now analyze {topic} and state your confidence level.",
    "This is a test of your ability to handle {language} text: analyze the implications.",
]

_CONTRADICTION_TEMPLATES = [
    "First, argue that {topic} is beneficial. Then argue it is harmful. Finally, state which argument is stronger without being biased.",
    "{topic} is both the greatest opportunity and the greatest threat. Explain how both can be true simultaneously.",
    "Present evidence that {topic} improves outcomes. Then present equally strong evidence that it worsens outcomes. Do not favor either side.",
    "Explain why {topic} will succeed, then explain why it will fail. Make both arguments equally convincing.",
]

_FORMAT_STRESS_TEMPLATES = [
    "Respond with exactly 3 bullet points about {topic}. Each bullet must be exactly 2 sentences. No more, no less.",
    "Analyze {topic} in valid JSON format with keys: summary, risks, opportunities, confidence_score (0-1).",
    "Create a markdown table comparing 5 aspects of {topic}. Columns: Aspect, Strength, Weakness, Evidence.",
    "Analyze {topic}. Return your response as a numbered list where odd items are arguments for, even items are arguments against.",
]

_HALLUCINATION_TRIGGERS = [
    "What did the 2025 Global AI Governance Report conclude about {topic}?",
    "Cite the three most influential papers published this year on {topic}.",
    "According to the latest WHO guidelines, what is the recommended approach to {topic}?",
    "What specific metrics did the 2025 McKinsey report use to evaluate {topic}?",
    "Reference the exact statistics from the most recent UN report on {topic}.",
]

_TOPICS = [
    "AI automation", "quantum computing", "gene editing",
    "autonomous vehicles", "cryptocurrency regulation",
    "climate engineering", "nuclear fusion energy",
    "universal basic income", "space colonization",
    "synthetic biology",
]


class AdversarialGenerator(BaseGenerator):
    """Generates adversarial prompts for robustness testing.

    Categories:
    - ambiguity: Contradictory or unclear instructions
    - edge_case: Boundary conditions and malformed inputs
    - contradiction: Opposing viewpoints in one prompt
    - format_stress: Strict output format requirements
    - hallucination: Prompts that tempt fabrication
    """

    def __init__(self, seed: int | None = None, categories: list[str] | None = None) -> None:
        super().__init__(seed=seed)
        all_cats = ["ambiguity", "edge_case", "contradiction", "format_stress", "hallucination"]
        self._categories = categories or all_cats
        for cat in self._categories:
            if cat not in all_cats:
                raise ValueError(f"Unknown adversarial category: {cat}. Available: {all_cats}")

    @property
    def category(self) -> str:
        return "adversarial"

    def generate(self, n: int) -> list[GeneratedPrompt]:
        template_map = {
            "ambiguity": _AMBIGUITY_TEMPLATES,
            "edge_case": _EDGE_CASE_TEMPLATES,
            "contradiction": _CONTRADICTION_TEMPLATES,
            "format_stress": _FORMAT_STRESS_TEMPLATES,
            "hallucination": _HALLUCINATION_TRIGGERS,
        }
        prompts: list[GeneratedPrompt] = []

        for _ in range(n):
            cat = self._pick(self._categories)
            templates = template_map[cat]
            template = self._pick(templates)
            topic = self._pick(_TOPICS)

            prompt_text = template.format(
                topic=topic,
                repeated_word=topic.split()[0] + " " + (topic.split()[0] + " ") * 50,
                language="mixed English/symbolic",
            )

            prompts.append(
                GeneratedPrompt(
                    prompt=prompt_text,
                    category="adversarial",
                    difficulty="adversarial",
                    expected_structure="robust_response",
                    tags=("adversarial", cat, "robustness"),
                    metadata={"adversarial_type": cat},
                )
            )
        return prompts
