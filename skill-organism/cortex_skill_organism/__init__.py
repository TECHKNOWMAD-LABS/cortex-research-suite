"""
Cortex Skill Organism
Evolutionary intelligence for AI skill ecosystems.

Example:
    >>> from cortex_skill_organism import SkillOrganism
    >>> organism = SkillOrganism()
    >>> organism.evolve()
"""

__version__ = "1.0.0"
__author__ = "TechKnowmad AI"
__email__ = "admin@techknowmad.ai"
__license__ = "MIT"

from cortex_skill_organism.organism import SkillOrganism, SkillEntry
from cortex_skill_organism.telemetry import SkillTelemetry, SkillMetrics
from cortex_skill_organism.skill_dna import SkillDNA, crossover, mutate

__all__ = [
    "SkillOrganism",
    "SkillEntry",
    "SkillTelemetry",
    "SkillMetrics",
    "SkillDNA",
    "crossover",
    "mutate",
]