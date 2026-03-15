"""Research prompt generator for academic and analytical evaluation.

Generates prompts that test research methodology, evidence synthesis,
literature review, and structured analytical output.
"""

from __future__ import annotations

from cortex.synthetic.base_generator import BaseGenerator, GeneratedPrompt

_RESEARCH_TEMPLATES = [
    "Conduct a structured analysis of recent developments in {field}. Identify key findings, methodological approaches, and open questions.",
    "Synthesize evidence from multiple perspectives on {topic} within {field}. Highlight areas of consensus and disagreement.",
    "Design a research methodology to investigate {topic} in the context of {field}. Specify data sources, analytical framework, and expected outcomes.",
    "Evaluate the current state of knowledge about {topic}. Identify gaps in the literature and propose future research directions.",
    "Compare methodological approaches used to study {topic} across different sub-fields of {field}. Assess strengths and limitations of each.",
    "Analyze how {topic} has evolved over the past decade within {field}. Identify inflection points and driving factors.",
    "Propose a multi-disciplinary research agenda combining {field} with adjacent domains to advance understanding of {topic}.",
    "Critically evaluate three competing theoretical frameworks for explaining {topic} in {field}.",
]

_FIELDS = [
    "artificial intelligence",
    "computational biology",
    "materials science",
    "behavioral economics",
    "systems engineering",
    "public health",
    "climate science",
    "cognitive neuroscience",
    "cybersecurity",
    "distributed systems",
    "epidemiology",
    "financial engineering",
    "genomics",
    "human-computer interaction",
    "information theory",
    "network science",
    "operations research",
    "quantum information",
    "robotics",
    "sustainable energy",
]

_TOPICS = [
    "model interpretability",
    "drug discovery pipelines",
    "carbon capture mechanisms",
    "decision-making under uncertainty",
    "fault-tolerant architectures",
    "pandemic preparedness",
    "neural architecture search",
    "market microstructure",
    "gene therapy delivery",
    "adversarial robustness",
    "supply chain resilience",
    "federated learning",
    "protein structure prediction",
    "renewable grid integration",
    "autonomous navigation",
    "privacy-preserving computation",
    "reinforcement learning from human feedback",
    "climate tipping points",
    "social network dynamics",
    "ethical AI governance",
]


class ResearchGenerator(BaseGenerator):
    """Generates research-oriented evaluation prompts."""

    @property
    def category(self) -> str:
        return "research"

    def generate(self, n: int) -> list[GeneratedPrompt]:
        prompts: list[GeneratedPrompt] = []
        for _ in range(n):
            difficulty = self._weighted_difficulty()
            field = self._pick(_FIELDS)
            topic = self._pick(_TOPICS)
            template = self._pick(_RESEARCH_TEMPLATES)

            prompt_text = template.format(field=field, topic=topic)
            prompts.append(
                GeneratedPrompt(
                    prompt=prompt_text,
                    category="research",
                    difficulty=difficulty,
                    expected_structure="research_report",
                    tags=("research", "analysis", field.split()[0].lower()),
                )
            )
        return prompts
