"""Strategy prompt generator for business intelligence and strategic analysis.

Generates prompts for competitive analysis, market dynamics, resource allocation,
and long-term strategic planning.
"""

from __future__ import annotations

from cortex.synthetic.base_generator import BaseGenerator, GeneratedPrompt

_STRATEGY_TEMPLATES = [
    "Analyze the competitive dynamics in {industry}. Identify structural advantages, barriers to entry, and disruption vectors.",
    "Evaluate the strategic implications of {trend} for organizations in {industry}.",
    "Propose a resource allocation strategy for a {org_type} entering {industry}, given {constraint}.",
    "Identify the top 5 structural risks facing {industry} over the next decade and propose mitigation strategies.",
    "Design a competitive moat strategy for a {org_type} in {industry} facing {challenge}.",
    "Analyze the second-order effects of {trend} on the value chain in {industry}.",
    "Develop a scenario planning framework for {industry} considering {trend} and {challenge}.",
    "Evaluate whether vertical integration or partnership strategies are more effective in {industry} given {constraint}.",
    "Map the stakeholder ecosystem in {industry} and identify leverage points for strategic influence.",
    "Propose a market entry strategy for {industry} that addresses {challenge} while leveraging {trend}.",
]

_INDUSTRIES = [
    "healthcare technology",
    "financial services",
    "clean energy",
    "enterprise software",
    "logistics and supply chain",
    "biotechnology",
    "telecommunications",
    "semiconductor manufacturing",
    "digital media",
    "autonomous vehicles",
    "space technology",
    "agricultural technology",
    "cybersecurity services",
    "quantum computing",
    "advanced materials",
]

_TRENDS = [
    "AI-driven automation",
    "decentralized finance",
    "remote work normalization",
    "sustainability mandates",
    "data sovereignty regulations",
    "edge computing growth",
    "demographic aging",
    "nearshoring of manufacturing",
    "synthetic biology advances",
    "open-source model proliferation",
]

_CHALLENGES = [
    "incumbent dominance",
    "regulatory uncertainty",
    "talent scarcity",
    "capital constraints",
    "rapid technology obsolescence",
    "geopolitical instability",
    "customer acquisition costs",
    "supply chain fragility",
]

_ORG_TYPES = ["startup", "mid-market company", "enterprise organization", "research institute", "government agency"]

_CONSTRAINTS = [
    "limited capital",
    "a 3-year runway",
    "regulatory complexity",
    "a distributed workforce",
    "emerging competition from AI-native players",
]


class StrategyGenerator(BaseGenerator):
    """Generates strategic analysis evaluation prompts."""

    @property
    def category(self) -> str:
        return "strategy"

    def generate(self, n: int) -> list[GeneratedPrompt]:
        prompts: list[GeneratedPrompt] = []
        for _ in range(n):
            difficulty = self._weighted_difficulty()
            template = self._pick(_STRATEGY_TEMPLATES)
            prompt_text = template.format(
                industry=self._pick(_INDUSTRIES),
                trend=self._pick(_TRENDS),
                challenge=self._pick(_CHALLENGES),
                org_type=self._pick(_ORG_TYPES),
                constraint=self._pick(_CONSTRAINTS),
            )
            prompts.append(
                GeneratedPrompt(
                    prompt=prompt_text,
                    category="strategy",
                    difficulty=difficulty,
                    expected_structure="strategic_analysis",
                    tags=("strategy", "business", "analysis"),
                )
            )
        return prompts
