"""
SkillOrganism: Core Evolution Engine
Manages the full lifecycle of skills as living entities in an evolving ecosystem.
"""

import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib

from telemetry import SkillTelemetry
from skill_dna import SkillDNA, crossover, mutate

logger = logging.getLogger(__name__)


@dataclass
class SkillEntry:
    """Represents a skill in the ecosystem."""
    id: str
    name: str
    version: str
    status: str  # active, dormant, deprecated, extinct
    fitness_score: float
    usage_count: int
    last_used: Optional[str]
    created: str
    category: str
    dependencies: List[str]
    health: str
    generation: int
    parent_skill: Optional[str]
    mutation_count: int
    deprecated_at: Optional[str] = None      # ISO timestamp when deprecated
    peak_fitness: Optional[float] = None     # highest fitness ever achieved
    resurrection_count: int = 0              # times resurrected from fossil archive


class SkillOrganism:
    """Evolution engine managing skill ecosystem."""

    def __init__(
        self,
        registry_path: Path = Path("skill_registry.json"),
        telemetry_db: Path = Path("skill_telemetry.db"),
        log_dir: Path = Path("."),
    ):
        """Initialize the organism."""
        self.registry_path = registry_path
        self.telemetry = SkillTelemetry(telemetry_db)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.ecosystem_config = {}
        self.skills: Dict[str, SkillEntry] = {}
        self.evolution_log = []
        
        self._load_registry()

    def _load_registry(self) -> None:
        """Load skill registry from disk."""
        try:
            with open(self.registry_path, "r") as f:
                data = json.load(f)
            
            self.ecosystem_config = data.get("ecosystem_config", {})
            self.skills = {
                skill_id: SkillEntry(**skill_data)
                for skill_id, skill_data in data.get("skills", {}).items()
            }
        except FileNotFoundError:
            logger.info(f"Registry not found at {self.registry_path}, initializing empty.")
            self.ecosystem_config = {"founding_generation": 1}
            self.skills = {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode registry: {e}")
            raise

    def _save_registry(self) -> None:
        """Save skill registry to disk."""
        data = {
            "ecosystem_config": self.ecosystem_config,
            "skills": {
                skill_id: asdict(skill)
                for skill_id, skill in self.skills.items()
            },
        }
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def _is_founding_skill(self, skill: SkillEntry) -> bool:
        """Check if a skill is a founding skill (gen 0-1)."""
        founding_gen = self.ecosystem_config.get("founding_generation", 1)
        return skill.generation <= founding_gen

    def select(self, fitness_threshold: float = 0.5) -> Dict[str, SkillEntry]:
        """
        Select skills based on fitness, protecting founding skills.
        
        Founding skills (generation <= founding_generation) are immune to 
        deprecation through selection pressure.
        """
        selected = {}
        for skill_id, skill in self.skills.items():
            # Protect founding skills from deprecation
            if self._is_founding_skill(skill):
                selected[skill_id] = skill
                logger.debug(f"Founding skill {skill_id} (gen {skill.generation}) protected from selection")
            elif skill.fitness_score >= fitness_threshold:
                selected[skill_id] = skill
        
        return selected

    def heal(self, phase: int = 0) -> None:
        """
        Heal the ecosystem.
        
        Phase 0: Restore incorrectly deprecated/extinct founding skills.
        """
        if phase == 0:
            for skill_id, skill in self.skills.items():
                # Check if this is a founding skill that was incorrectly deprecated
                if self._is_founding_skill(skill):
                    if skill.status in ["deprecated", "extinct"]:
                        # Restore founding skills
                        skill.status = "active"
                        skill.deprecated_at = None
                        logger.info(f"Restored founding skill {skill_id} from {skill.status}")

    def speciate(self) -> List[SkillEntry]:
        """Create new skill through speciation (crossover + mutation)."""
        if len(self.skills) < 2:
            logger.warning("Not enough skills for speciation.")
            return []
        
        parents = random.sample(list(self.skills.values()), 2)
        parent1_dna = SkillDNA.from_skill(parents[0])
        parent2_dna = SkillDNA.from_skill(parents[1])
        
        offspring_dna = crossover(parent1_dna, parent2_dna)
        offspring_dna = mutate(offspring_dna)
        
        offspring = SkillEntry(
            id=hashlib.md5(f"{parents[0].id}{parents[1].id}{datetime.now()}".encode()).hexdigest()[:8],
            name=f"{parents[0].name}_{parents[1].name}_hybrid",
            version="0.1",
            status="active",
            fitness_score=0.0,
            usage_count=0,
            last_used=None,
            created=datetime.now().isoformat(),
            category=parents[0].category,
            dependencies=list(set(parents[0].dependencies + parents[1].dependencies)),
            health="nascent",
            generation=max(parents[0].generation, parents[1].generation) + 1,
            parent_skill=parents[0].id,
            mutation_count=1,
        )
        
        self.skills[offspring.id] = offspring
        self._save_registry()
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "speciation",
            "parents": [parents[0].id, parents[1].id],
            "offspring_id": offspring.id,
            "offspring_generation": offspring.generation,
        }
        self.evolution_log.append(event)
        
        return [offspring]

    def deprecate(self, skill_id: str) -> None:
        """Mark a skill as deprecated."""
        if skill_id not in self.skills:
            logger.warning(f"Skill {skill_id} not found.")
            return
        
        skill = self.skills[skill_id]
        
        # Protect founding skills from deprecation
        if self._is_founding_skill(skill):
            logger.warning(f"Attempting to deprecate founding skill {skill_id} (gen {skill.generation}). Protected!")
            return
        
        skill.status = "deprecated"
        skill.deprecated_at = datetime.now().isoformat()
        self._save_registry()
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "deprecation",
            "skill_id": skill_id,
            "generation": skill.generation,
        }
        self.evolution_log.append(event)

    def extinct(self, skill_id: str) -> None:
        """Mark a skill as extinct."""
        if skill_id not in self.skills:
            logger.warning(f"Skill {skill_id} not found.")
            return
        
        skill = self.skills[skill_id]
        
        # Protect founding skills from extinction
        if self._is_founding_skill(skill):
            logger.warning(f"Attempting to mark founding skill {skill_id} (gen {skill.generation}) as extinct. Protected!")
            return
        
        skill.status = "extinct"
        skill.deprecated_at = datetime.now().isoformat()
        self._save_registry()
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "extinction",
            "skill_id": skill_id,
            "generation": skill.generation,
        }
        self.evolution_log.append(event)

    def resurrect(self, skill_id: str) -> None:
        """Resurrect an extinct skill."""
        if skill_id not in self.skills:
            logger.warning(f"Skill {skill_id} not found.")
            return
        
        skill = self.skills[skill_id]
        skill.status = "active"
        skill.deprecated_at = None
        skill.resurrection_count += 1
        self._save_registry()
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "resurrection",
            "skill_id": skill_id,
            "resurrection_count": skill.resurrection_count,
        }
        self.evolution_log.append(event)

    def get_ecosystem_stats(self) -> Dict:
        """Get ecosystem statistics."""
        total = len(self.skills)
        active = sum(1 for s in self.skills.values() if s.status == "active")
        deprecated = sum(1 for s in self.skills.values() if s.status == "deprecated")
        extinct = sum(1 for s in self.skills.values() if s.status == "extinct")
        dormant = sum(1 for s in self.skills.values() if s.status == "dormant")
        
        avg_fitness = (
            sum(s.fitness_score for s in self.skills.values()) / total
            if total > 0
            else 0.0
        )
        
        founding_count = sum(1 for s in self.skills.values() if self._is_founding_skill(s))
        
        return {
            "total_skills": total,
            "active": active,
            "deprecated": deprecated,
            "extinct": extinct,
            "dormant": dormant,
            "average_fitness": avg_fitness,
            "founding_skills": founding_count,
            "evolution_events": len(self.evolution_log),
        }

    def _configure_logging(self, log_level: str = "INFO") -> None:
        """Configure logging for the organism."""
        logger.setLevel(getattr(logging, log_level))
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        file_handler = logging.FileHandler(self.log_dir / "organism.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def log_state(self) -> None:
        """Log current ecosystem state."""
        stats = self.get_ecosystem_stats()
        logger.info(f"Ecosystem state: {stats}")

    def run_lifecycle_cycle(self) -> None:
        """Run one complete lifecycle cycle."""
        logger.info("Starting lifecycle cycle...")
        
        # Phase 1: Selection
        selected = self.select()
        logger.info(f"Selection phase: {len(selected)} skills selected")
        
        # Phase 2: Speciation
        offspring = self.speciate()
        logger.info(f"Speciation phase: {len(offspring)} new skills created")
        
        # Phase 3: Healing
        self.heal(phase=0)
        logger.info("Healing phase: restored founding skills")
        
        self.log_state()


# Setup logging
if __name__ == "__main__":
    organism = SkillOrganism()
    organism._configure_logging()
    organism.log_state()
