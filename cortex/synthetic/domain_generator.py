"""Domain-specific prompt generator for specialized verticals.

Generates evaluation prompts for healthcare, finance, technology,
and policy domains with appropriate technical depth.
"""

from __future__ import annotations

from cortex.synthetic.base_generator import BaseGenerator, GeneratedPrompt

_DOMAIN_TEMPLATES: dict[str, list[str]] = {
    "healthcare": [
        "Explain the mechanism of action and clinical implications of {topic} in treating {condition}.",
        "Evaluate the evidence base for {topic} as a diagnostic approach for {condition}.",
        "Compare treatment protocols for {condition}: analyze efficacy, side effects, and cost-effectiveness.",
        "Assess the role of {topic} in improving patient outcomes for {condition}.",
        "Design a clinical decision support framework for managing {condition} using {topic}.",
    ],
    "finance": [
        "Analyze the risk-return profile of {topic} in the context of {market_condition}.",
        "Evaluate the systemic risk implications of {topic} for financial stability.",
        "Model the impact of {market_condition} on {topic} using quantitative frameworks.",
        "Compare regulatory approaches to {topic} across major financial jurisdictions.",
        "Assess the portfolio diversification benefits of incorporating {topic} given {market_condition}.",
    ],
    "technology": [
        "Evaluate the technical architecture trade-offs of {topic} for {use_case}.",
        "Analyze the scalability challenges of {topic} when applied to {use_case}.",
        "Compare {topic} with alternative approaches for solving {use_case}.",
        "Assess the security implications of deploying {topic} in production for {use_case}.",
        "Design a migration strategy from legacy systems to {topic} for {use_case}.",
    ],
    "policy": [
        "Analyze the economic impact of {policy} on {sector}.",
        "Evaluate the unintended consequences of implementing {policy} in {sector}.",
        "Compare international approaches to {policy} and assess applicability to {sector}.",
        "Design a stakeholder engagement strategy for implementing {policy} in {sector}.",
        "Assess the equity implications of {policy} across different segments of {sector}.",
    ],
}

_DOMAIN_TERMS: dict[str, dict[str, list[str]]] = {
    "healthcare": {
        "topic": [
            "CRISPR gene editing",
            "mRNA therapeutics",
            "AI-assisted radiology",
            "telemedicine platforms",
            "personalized medicine",
            "immunotherapy",
            "wearable biomarkers",
            "digital pathology",
            "robotic surgery",
        ],
        "condition": [
            "chronic kidney disease",
            "Type 2 diabetes",
            "non-small cell lung cancer",
            "Alzheimer's disease",
            "cardiovascular disease",
            "autoimmune disorders",
            "rare genetic conditions",
            "treatment-resistant depression",
        ],
    },
    "finance": {
        "topic": [
            "algorithmic trading strategies",
            "decentralized lending protocols",
            "central bank digital currencies",
            "credit risk modeling",
            "ESG-integrated portfolios",
            "options volatility surfaces",
            "stablecoin mechanisms",
            "tokenized real-world assets",
        ],
        "market_condition": [
            "rising interest rates",
            "a liquidity crisis",
            "post-pandemic recovery",
            "high inflation environment",
            "emerging market volatility",
            "regulatory tightening",
            "technology sector correction",
        ],
    },
    "technology": {
        "topic": [
            "microservices architecture",
            "WebAssembly runtimes",
            "vector databases",
            "confidential computing",
            "edge ML inference",
            "service mesh",
            "event-driven architecture",
            "zero-trust networking",
        ],
        "use_case": [
            "real-time fraud detection",
            "autonomous vehicle coordination",
            "large-scale recommendation systems",
            "IoT fleet management",
            "multi-tenant SaaS platforms",
            "high-frequency trading systems",
            "healthcare data interoperability",
        ],
    },
    "policy": {
        "policy": [
            "AI regulation framework",
            "carbon pricing mechanisms",
            "universal basic income",
            "data localization requirements",
            "open banking mandates",
            "gig economy worker protections",
            "antitrust reform for tech platforms",
        ],
        "sector": [
            "technology industry",
            "healthcare delivery",
            "financial services",
            "education systems",
            "transportation infrastructure",
            "energy markets",
            "housing and real estate",
        ],
    },
}


class DomainGenerator(BaseGenerator):
    """Generates domain-specific evaluation prompts."""

    def __init__(self, domain: str = "healthcare", seed: int | None = None) -> None:
        super().__init__(seed=seed)
        if domain not in _DOMAIN_TEMPLATES:
            raise ValueError(f"Unknown domain: {domain}. Available: {list(_DOMAIN_TEMPLATES)}")
        self._domain = domain

    @property
    def category(self) -> str:
        return f"domain_{self._domain}"

    def generate(self, n: int) -> list[GeneratedPrompt]:
        templates = _DOMAIN_TEMPLATES[self._domain]
        terms = _DOMAIN_TERMS[self._domain]
        prompts: list[GeneratedPrompt] = []

        for _ in range(n):
            difficulty = self._weighted_difficulty()
            template = self._pick(templates)
            # Fill all placeholders from domain terms
            filled = template
            for key, values in terms.items():
                placeholder = "{" + key + "}"
                if placeholder in filled:
                    filled = filled.replace(placeholder, self._pick(values), 1)

            prompts.append(
                GeneratedPrompt(
                    prompt=filled,
                    category=f"domain_{self._domain}",
                    difficulty=difficulty,
                    expected_structure="domain_analysis",
                    tags=(self._domain, "domain", "specialist"),
                )
            )
        return prompts
