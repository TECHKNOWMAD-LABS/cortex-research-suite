"""MiroFish-inspired swarm scenario simulator.

Generates agent personas from a seed report, runs simulated deliberation
rounds between them, injects counterfactual branches, and produces a
structured scenario report.

Security:
- Personas are system-generated from LLM analysis, NOT user-supplied.
- All outputs carry a simulation disclaimer.
- Seed report input capped at 3000 characters.
- No pickle, eval, or exec.

Usage:
    python -m skills.scenario-simulator.scripts.scenario_simulator \\
        --seed-report "Federated learning in hospitals..." \\
        --rounds 3 --counterfactuals 2 --output report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEED_REPORT_MAX_CHARS = 3000

DISCLAIMER = (
    "These are simulated outcomes for analytical purposes only. "
    "Not predictions or recommendations."
)

# Archetype pool for persona generation
_ROLE_ARCHETYPES = [
    ("Skeptical Analyst", "risk-averse", "Identifies failure modes and worst-case scenarios"),
    ("Optimistic Strategist", "opportunity-focused", "Highlights upside potential and growth vectors"),
    ("Systems Thinker", "second-order-effects", "Traces cascading consequences and feedback loops"),
    ("Empirical Realist", "data-driven", "Demands evidence and quantifiable metrics"),
    ("Regulatory Lens", "compliance-focused", "Evaluates legal, ethical, and policy constraints"),
    ("Innovation Champion", "disruption-focused", "Pushes boundaries and challenges status quo"),
    ("End-User Advocate", "user-centric", "Prioritises practical impact on affected populations"),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Persona:
    """An agent persona for the simulation."""

    name: str
    role: str
    lens: str
    expertise: str
    bias: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class RoundOutput:
    """A single persona's output for one deliberation round."""

    position: str
    evidence: str
    uncertainty: str
    challenge: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeliberationRound:
    """One round of deliberation across all personas."""

    round: int
    outputs: dict[str, RoundOutput] = field(default_factory=dict)
    agreement_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "outputs": {k: v.to_dict() for k, v in self.outputs.items()},
            "agreement_score": round(self.agreement_score, 2),
        }


@dataclass
class CounterfactualBranch:
    """A what-if branch in the scenario."""

    assumption_changed: str
    new_value: str
    outcome_delta: str
    impact_severity: str  # low, medium, high

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class ScenarioReport:
    """Final structured output of a scenario simulation."""

    disclaimer: str = DISCLAIMER
    seed_summary: str = ""
    personas: list[Persona] = field(default_factory=list)
    deliberation_rounds: list[DeliberationRound] = field(default_factory=list)
    counterfactual_branches: list[CounterfactualBranch] = field(default_factory=list)
    consensus_outcome: str = ""
    dissenting_views: list[str] = field(default_factory=list)
    confidence_level: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "disclaimer": self.disclaimer,
            "seed_summary": self.seed_summary,
            "personas": [p.to_dict() for p in self.personas],
            "deliberation_rounds": [r.to_dict() for r in self.deliberation_rounds],
            "counterfactual_branches": [c.to_dict() for c in self.counterfactual_branches],
            "consensus_outcome": self.consensus_outcome,
            "dissenting_views": self.dissenting_views,
            "confidence_level": round(self.confidence_level, 2),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Persona Generator
# ---------------------------------------------------------------------------


class PersonaGenerator:
    """Generates 3-5 agent personas from seed report analysis.

    Personas are system-generated based on topic analysis, NOT user-supplied.
    Ensures diversity: at least one skeptic, at least one second-order thinker.
    """

    def generate(self, seed_text: str, count: int = 4) -> list[Persona]:
        """Generate personas relevant to the seed report.

        Args:
            seed_text: The seed report text (already truncated to limit).
            count: Number of personas to generate (3-5, clamped).

        Returns:
            List of Persona objects.
        """
        count = max(3, min(5, count))
        keywords = self._extract_keywords(seed_text)
        domain = self._infer_domain(keywords)

        # Select archetypes ensuring diversity requirements
        selected = self._select_archetypes(count)

        personas: list[Persona] = []
        for i, (role, lens, bias_desc) in enumerate(selected):
            name = self._generate_name(role, i)
            personas.append(
                Persona(
                    name=name,
                    role=role,
                    lens=lens,
                    expertise=f"{domain} — {role.lower()} perspective",
                    bias=bias_desc,
                )
            )
        return personas

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract salient keywords from text using simple frequency analysis."""
        stop_words = frozenset(
            "a an the is are was were be been being have has had do does did will "
            "would shall should may might can could of in to for on with at by from "
            "as into through during before after above below between under and but or "
            "nor not so yet both either neither each every all any few more most other "
            "some such no only own same than too very that this these those it its he "
            "she they them his her their our your we you i me us".split()
        )
        words = re.findall(r"[a-z]{3,}", text.lower())
        filtered = [w for w in words if w not in stop_words]
        freq: dict[str, int] = {}
        for w in filtered:
            freq[w] = freq.get(w, 0) + 1
        ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in ranked[:15]]

    def _infer_domain(self, keywords: list[str]) -> str:
        """Infer a domain label from top keywords."""
        if not keywords:
            return "general analysis"
        return f"{keywords[0]}/{keywords[1]}" if len(keywords) > 1 else keywords[0]

    def _select_archetypes(self, count: int) -> list[tuple[str, str, str]]:
        """Select archetypes ensuring diversity.

        Guarantees at least one skeptic and one second-order thinker.
        """
        # Always include skeptic and systems thinker
        must_have = [_ROLE_ARCHETYPES[0], _ROLE_ARCHETYPES[2]]  # Skeptical, Systems
        remaining = [a for a in _ROLE_ARCHETYPES if a not in must_have]

        # Fill remaining slots deterministically but with variety
        selected = list(must_have)
        for archetype in remaining:
            if len(selected) >= count:
                break
            selected.append(archetype)

        return selected[:count]

    def _generate_name(self, role: str, index: int) -> str:
        """Generate a descriptive persona name."""
        prefixes = ["Agent", "Analyst", "Director", "Dr.", "Strategist"]
        prefix = prefixes[index % len(prefixes)]
        role_short = role.split()[0]
        return f"{prefix} {role_short}"


# ---------------------------------------------------------------------------
# Simulation Engine
# ---------------------------------------------------------------------------


class SimulationEngine:
    """Runs rounds of deliberation between personas.

    Each round produces structured outputs per persona. Agreement scores
    track convergence. Early convergence (>= 0.8) is flagged as a
    potential groupthink risk.
    """

    def run(
        self,
        seed_summary: str,
        personas: list[Persona],
        num_rounds: int = 3,
    ) -> list[DeliberationRound]:
        """Run deliberation rounds.

        Args:
            seed_summary: Summarised seed report.
            personas: List of generated personas.
            num_rounds: Number of rounds (default 3).

        Returns:
            List of DeliberationRound objects.
        """
        num_rounds = max(1, min(10, num_rounds))
        rounds: list[DeliberationRound] = []

        for rnd_num in range(1, num_rounds + 1):
            dr = DeliberationRound(round=rnd_num)
            previous_positions = self._collect_positions(rounds)

            for persona in personas:
                output = self._generate_output(
                    persona, seed_summary, rnd_num, previous_positions
                )
                dr.outputs[persona.name] = output

            dr.agreement_score = self._compute_agreement(dr)
            rounds.append(dr)

        return rounds

    def _generate_output(
        self,
        persona: Persona,
        seed_summary: str,
        round_num: int,
        previous_positions: dict[str, str],
    ) -> RoundOutput:
        """Generate a persona's output for the current round.

        This is the simulation stub. In production, this calls the LLM
        with the persona's system prompt. Here it produces structured
        placeholder output based on persona characteristics.
        """
        position = (
            f"[{persona.role}] Analysis of '{seed_summary[:80]}...' "
            f"through {persona.lens} lens."
        )
        evidence = (
            f"Based on {persona.expertise}, the key factors are "
            f"risk mitigation and feasibility assessment."
        )
        uncertainty = (
            f"Uncertain about long-term second-order effects and "
            f"external variable stability."
        )

        challenge = None
        if round_num > 1 and previous_positions:
            other_names = [n for n in previous_positions if n != persona.name]
            if other_names:
                target = other_names[0]
                challenge = (
                    f"[{persona.name}] challenges [{target}]: "
                    f"The {persona.lens} perspective suggests a different weighting."
                )

        return RoundOutput(
            position=position,
            evidence=evidence,
            uncertainty=uncertainty,
            challenge=challenge,
        )

    def _collect_positions(
        self, rounds: list[DeliberationRound]
    ) -> dict[str, str]:
        """Collect the latest position from each persona across rounds."""
        positions: dict[str, str] = {}
        for dr in rounds:
            for name, output in dr.outputs.items():
                positions[name] = output.position
        return positions

    def _compute_agreement(self, dr: DeliberationRound) -> float:
        """Compute agreement score for a round.

        Uses keyword overlap between persona positions as a proxy.
        Returns 0.0–1.0.
        """
        if len(dr.outputs) < 2:
            return 1.0

        all_keywords: list[set[str]] = []
        for output in dr.outputs.values():
            words = set(re.findall(r"[a-z]{3,}", output.position.lower()))
            all_keywords.append(words)

        # Pairwise Jaccard similarity
        pairs = 0
        total_sim = 0.0
        for i in range(len(all_keywords)):
            for j in range(i + 1, len(all_keywords)):
                intersection = all_keywords[i] & all_keywords[j]
                union = all_keywords[i] | all_keywords[j]
                if union:
                    total_sim += len(intersection) / len(union)
                pairs += 1

        return total_sim / pairs if pairs else 0.0


# ---------------------------------------------------------------------------
# Counterfactual Injector
# ---------------------------------------------------------------------------


class CounterfactualInjector:
    """Injects what-if variations at specified points.

    Extracts key assumptions from the seed text and flips them to
    create alternative scenario branches.
    """

    def inject(
        self,
        seed_text: str,
        num_branches: int = 2,
    ) -> list[CounterfactualBranch]:
        """Generate counterfactual branches.

        Args:
            seed_text: The seed report text.
            num_branches: Number of branches to generate (clamped 1-5).

        Returns:
            List of CounterfactualBranch objects.
        """
        num_branches = max(1, min(5, num_branches))
        assumptions = self._extract_assumptions(seed_text)
        branches: list[CounterfactualBranch] = []

        for i, assumption in enumerate(assumptions[:num_branches]):
            flipped = self._flip_assumption(assumption)
            severity = ["low", "medium", "high"][min(i, 2)]
            branches.append(
                CounterfactualBranch(
                    assumption_changed=assumption,
                    new_value=flipped,
                    outcome_delta=(
                        f"If '{assumption}' were instead '{flipped}', "
                        f"the scenario outcome would shift significantly "
                        f"in risk/benefit calculus."
                    ),
                    impact_severity=severity,
                )
            )

        return branches

    def _extract_assumptions(self, text: str) -> list[str]:
        """Extract key assumptions from text.

        Uses heuristic patterns to find assumption-like statements.
        """
        assumptions: list[str] = []

        # Look for assumption-indicator phrases
        patterns = [
            r"(?:assuming|assumes?|given that|provided that)\s+(.{10,80}?)(?:\.|,|;)",
            r"(?:if|when)\s+(.{10,80}?)(?:\s+then|\s+,|\.|;)",
            r"(?:based on|relies on|depends on)\s+(.{10,80}?)(?:\.|,|;)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            assumptions.extend(matches)

        # If no explicit assumptions found, extract key noun phrases as implicit assumptions
        if not assumptions:
            sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
            for s in sentences[:5]:
                assumptions.append(f"the situation described: '{s[:60]}' holds true")

        return assumptions[:5]

    def _flip_assumption(self, assumption: str) -> str:
        """Flip an assumption to create a counterfactual."""
        negations = {
            "increase": "decrease",
            "improve": "worsen",
            "success": "failure",
            "available": "unavailable",
            "high": "low",
            "large": "small",
            "positive": "negative",
            "growth": "decline",
            "stable": "volatile",
            "sufficient": "insufficient",
        }

        flipped = assumption
        for word, opposite in negations.items():
            if word in flipped.lower():
                flipped = re.sub(
                    re.escape(word), opposite, flipped, count=1, flags=re.IGNORECASE
                )
                return flipped

        return f"the opposite of: {assumption}"


# ---------------------------------------------------------------------------
# Scenario Reporter
# ---------------------------------------------------------------------------


class ScenarioReporter:
    """Produces the final structured scenario report."""

    def build_report(
        self,
        seed_text: str,
        personas: list[Persona],
        rounds: list[DeliberationRound],
        counterfactuals: list[CounterfactualBranch],
    ) -> ScenarioReport:
        """Build the final scenario report.

        Args:
            seed_text: Original seed report (truncated).
            personas: Generated personas.
            rounds: Completed deliberation rounds.
            counterfactuals: Counterfactual branches.

        Returns:
            ScenarioReport with all fields populated.
        """
        seed_summary = seed_text[:200] + ("..." if len(seed_text) > 200 else "")
        consensus = self._synthesize_consensus(rounds)
        dissenting = self._extract_dissent(rounds, personas)
        confidence = self._compute_confidence(rounds, counterfactuals)
        early_convergence = any(r.agreement_score >= 0.8 for r in rounds[:-1]) if len(rounds) > 1 else False

        return ScenarioReport(
            disclaimer=DISCLAIMER,
            seed_summary=seed_summary,
            personas=personas,
            deliberation_rounds=rounds,
            counterfactual_branches=counterfactuals,
            consensus_outcome=consensus,
            dissenting_views=dissenting,
            confidence_level=confidence,
            metadata={
                "rounds_completed": len(rounds),
                "counterfactuals_generated": len(counterfactuals),
                "early_convergence": early_convergence,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )

    def _synthesize_consensus(self, rounds: list[DeliberationRound]) -> str:
        """Synthesize consensus from the final round."""
        if not rounds:
            return "No deliberation rounds completed."

        final = rounds[-1]
        positions = [o.position for o in final.outputs.values()]
        return (
            f"After {len(rounds)} round(s) of deliberation, "
            f"the {len(positions)} personas reached the following synthesis: "
            f"The scenario warrants careful analysis with attention to "
            f"risk factors, second-order effects, and implementation feasibility. "
            f"Final agreement score: {final.agreement_score:.2f}."
        )

    def _extract_dissent(
        self,
        rounds: list[DeliberationRound],
        personas: list[Persona],
    ) -> list[str]:
        """Extract dissenting views from the deliberation."""
        dissent: list[str] = []
        if not rounds:
            return dissent

        final = rounds[-1]
        for persona in personas:
            if persona.name in final.outputs:
                output = final.outputs[persona.name]
                if output.uncertainty:
                    dissent.append(
                        f"[{persona.name} — {persona.role}] {output.uncertainty}"
                    )
        return dissent

    def _compute_confidence(
        self,
        rounds: list[DeliberationRound],
        counterfactuals: list[CounterfactualBranch],
    ) -> float:
        """Compute overall confidence level (0.0–1.0).

        Higher agreement and fewer high-severity counterfactuals
        increase confidence.
        """
        if not rounds:
            return 0.0

        avg_agreement = sum(r.agreement_score for r in rounds) / len(rounds)

        severity_penalty = 0.0
        for cf in counterfactuals:
            if cf.impact_severity == "high":
                severity_penalty += 0.15
            elif cf.impact_severity == "medium":
                severity_penalty += 0.08
            else:
                severity_penalty += 0.03

        confidence = max(0.0, min(1.0, avg_agreement - severity_penalty))
        return confidence


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_simulation(
    seed_report: str,
    num_rounds: int = 3,
    num_counterfactuals: int = 2,
    num_personas: int = 4,
) -> ScenarioReport:
    """Run the full scenario simulation pipeline.

    Args:
        seed_report: The seed report text or topic.
        num_rounds: Number of deliberation rounds (default 3).
        num_counterfactuals: Number of counterfactual branches (default 2).
        num_personas: Number of agent personas (3-5, default 4).

    Returns:
        A ScenarioReport with all simulation results.
    """
    # Security: cap seed report length
    seed_text = seed_report[:SEED_REPORT_MAX_CHARS]

    # Step 1: Generate personas
    generator = PersonaGenerator()
    personas = generator.generate(seed_text, count=num_personas)

    # Step 2: Run deliberation
    engine = SimulationEngine()
    rounds = engine.run(seed_text, personas, num_rounds=num_rounds)

    # Step 3: Inject counterfactuals
    injector = CounterfactualInjector()
    counterfactuals = injector.inject(seed_text, num_branches=num_counterfactuals)

    # Step 4: Build report
    reporter = ScenarioReporter()
    report = reporter.build_report(seed_text, personas, rounds, counterfactuals)

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MiroFish-inspired swarm scenario simulator"
    )
    parser.add_argument(
        "--seed-report",
        required=True,
        help="Seed report text or path to a text file",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="Number of deliberation rounds (default: 3)",
    )
    parser.add_argument(
        "--counterfactuals",
        type=int,
        default=2,
        help="Number of counterfactual branches (default: 2)",
    )
    parser.add_argument(
        "--personas",
        type=int,
        default=4,
        help="Number of agent personas, 3-5 (default: 4)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path (default: stdout)",
    )
    args = parser.parse_args()

    # Path validation helper
    def _safe_path(base_dir: Path, user_path: str) -> Path:
        resolved = Path(user_path).resolve()
        base = Path(base_dir).resolve()
        if not str(resolved).startswith(str(base) + os.sep) and resolved != base:
            raise ValueError(f"Path {user_path} escapes allowed directory {base_dir}")
        return resolved

    cwd = Path.cwd()

    # Resolve seed report: file path or direct text
    seed_path = Path(args.seed_report)
    if seed_path.is_file():
        safe_seed = _safe_path(cwd, args.seed_report)
        seed_text = safe_seed.read_text(encoding="utf-8")
    else:
        seed_text = args.seed_report

    report = run_simulation(
        seed_report=seed_text,
        num_rounds=args.rounds,
        num_counterfactuals=args.counterfactuals,
        num_personas=args.personas,
    )

    output_json = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)

    if args.output:
        out_path = _safe_path(cwd, args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json, encoding="utf-8")
        print(f"Report written to {out_path}", file=sys.stderr)
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
