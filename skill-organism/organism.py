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
    status: str  # active, dormant, deprecated
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
            
            self.ecosystem_config = data.get("ecosystem", {})
            
            for skill_data in data.get("skills", []):
                skill = SkillEntry(**skill_data)
                self.skills[skill.id] = skill
            
            logger.info(f"Loaded {len(self.skills)} skills from registry")
        except FileNotFoundError:
            logger.warning(f"Registry not found at {self.registry_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse registry: {e}")

    def _save_registry(self) -> None:
        """Save skill registry to disk."""
        try:
            data = {
                "ecosystem": self.ecosystem_config,
                "skills": [asdict(skill) for skill in self.skills.values()],
            }
            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Registry saved")
        except IOError as e:
            logger.error(f"Failed to save registry: {e}")

    def observe(self) -> Dict:
        """Observe ecosystem state: scan skills, check health, detect patterns."""
        observation = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_skills": len(self.skills),
            "skill_details": [],
            "ecosystem_health": {},
            "anomalies": [],
        }

        skill_ids = list(self.skills.keys())
        
        # Get telemetry for each skill
        for skill_id in skill_ids:
            metrics = self.telemetry.get_skill_metrics(skill_id, period_days=7)
            
            skill_entry = self.skills[skill_id]
            
            detail = {
                "skill_id": skill_id,
                "name": skill_entry.name,
                "status": skill_entry.status,
                "health": skill_entry.health,
                "fitness_score": skill_entry.fitness_score,
            }
            
            if metrics:
                detail["metrics"] = asdict(metrics)
                # Update health status from metrics
                if metrics.health_status in ["excellent", "healthy"]:
                    skill_entry.health = "healthy"
                elif metrics.health_status == "degraded":
                    skill_entry.health = "degraded"
                else:
                    skill_entry.health = "critical"
            
            observation["skill_details"].append(detail)
            
            # Check for anomalies
            anomalies = self.telemetry.detect_anomalies(skill_id, sigma=2.0)
            if anomalies:
                observation["anomalies"].append({
                    "skill_id": skill_id,
                    "count": len(anomalies),
                    "recent": anomalies[:3],
                })

        # Ecosystem health
        observation["ecosystem_health"] = self.telemetry.get_ecosystem_health(skill_ids)
        
        return observation

    def mutate(self, mutation_rate: float = 0.15) -> List[str]:
        """Generate improved skill variants based on performance data."""
        mutated_skills = []
        
        # Get fitness rankings
        fitness_scores = self.telemetry.get_fitness_scores(
            list(self.skills.keys()), period_days=7
        )
        
        # Mutate top performers
        for skill_id, fitness in fitness_scores[:5]:  # Top 5 performers
            if random.random() < mutation_rate:
                try:
                    skill = self.skills[skill_id]
                    
                    # Create mutation
                    old_version = skill.version
                    version_parts = old_version.split(".")
                    version_parts[2] = str(int(version_parts[2]) + 1)
                    new_version = ".".join(version_parts)
                    
                    mutant_id = f"{skill_id}_v{new_version}"
                    mutant = SkillEntry(
                        id=mutant_id,
                        name=f"{skill.name} (mutant)",
                        version=new_version,
                        status="active",
                        fitness_score=min(skill.fitness_score + 0.05, 1.0),
                        usage_count=0,
                        last_used=None,
                        created=datetime.utcnow().isoformat(),
                        category=skill.category,
                        dependencies=skill.dependencies.copy(),
                        health="healthy",
                        generation=skill.generation + 1,
                        parent_skill=skill_id,
                        mutation_count=skill.mutation_count + 1,
                    )
                    
                    self.skills[mutant_id] = mutant
                    mutated_skills.append(mutant_id)
                    logger.info(f"Mutated {skill_id} → {mutant_id}")
                except Exception as e:
                    logger.error(f"Failed to mutate {skill_id}: {e}")
        
        return mutated_skills

    def select(self) -> Dict:
        """Fitness scoring and natural selection. Cull low performers."""
        selection_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "culled": [],
            "promoted": [],
            "fitness_threshold": self.ecosystem_config.get("fitness_threshold", 0.6),
        }

        fitness_scores = self.telemetry.get_fitness_scores(
            list(self.skills.keys()), period_days=7
        )

        # Find median fitness
        scores = [score for _, score in fitness_scores]
        median_fitness = sorted(scores)[len(scores) // 2] if scores else 0.5

        for skill_id, fitness in fitness_scores:
            skill = self.skills[skill_id]
            
            # Cull low performers
            if fitness < self.ecosystem_config.get("fitness_threshold", 0.6):
                if skill.usage_count < 5:  # Only cull if rarely used
                    skill.status = "deprecated"
                    selection_results["culled"].append({
                        "skill_id": skill_id,
                        "fitness": fitness,
                        "reason": "low_fitness"
                    })
                    logger.info(f"Deprecated {skill_id} due to low fitness ({fitness})")
            
            # Promote high performers
            if fitness > self.ecosystem_config.get("auto_deploy_threshold", 0.8):
                skill.status = "active"
                selection_results["promoted"].append({
                    "skill_id": skill_id,
                    "fitness": fitness,
                })
                logger.info(f"Promoted {skill_id} to auto-deploy (fitness: {fitness})")

        return selection_results

    def reproduce(self) -> List[str]:
        """Create new skills from high-performing combinations."""
        new_skills = []
        
        fitness_scores = self.telemetry.get_fitness_scores(
            list(self.skills.keys()), period_days=7
        )
        
        # Get top 10 performers
        top_skills = [skill_id for skill_id, _ in fitness_scores[:10]]
        
        # Breed pairs
        if len(top_skills) >= 2:
            for _ in range(random.randint(1, 3)):  # Create 1-3 offspring
                parent_a_id = random.choice(top_skills)
                parent_b_id = random.choice(top_skills)
                
                if parent_a_id != parent_b_id:
                    parent_a = self.skills[parent_a_id]
                    parent_b = self.skills[parent_b_id]
                    
                    # Create hybrid
                    offspring_id = f"hybrid_{parent_a_id}_{parent_b_id}_{self._get_short_hash()}"
                    offspring = SkillEntry(
                        id=offspring_id,
                        name=f"Hybrid ({parent_a.name} + {parent_b.name})",
                        version="1.0.0",
                        status="active",
                        fitness_score=(parent_a.fitness_score + parent_b.fitness_score) / 2,
                        usage_count=0,
                        last_used=None,
                        created=datetime.utcnow().isoformat(),
                        category=parent_a.category,
                        dependencies=list(set(parent_a.dependencies + parent_b.dependencies)),
                        health="healthy",
                        generation=max(parent_a.generation, parent_b.generation) + 1,
                        parent_skill=f"{parent_a_id}+{parent_b_id}",
                        mutation_count=0,
                    )
                    
                    self.skills[offspring_id] = offspring
                    new_skills.append(offspring_id)
                    logger.info(f"Bred {parent_a_id} x {parent_b_id} → {offspring_id}")
        
        return new_skills

    def heal(self) -> Dict:
        """Detect degraded skills and trigger recovery."""
        healing_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "recovered": [],
            "critical": [],
        }

        for skill_id, skill in self.skills.items():
            if skill.status == "deprecated":
                continue
            
            metrics = self.telemetry.get_skill_metrics(skill_id, period_days=7)
            
            if metrics and metrics.health_status == "critical":
                # Attempt recovery
                healing_results["critical"].append({
                    "skill_id": skill_id,
                    "error_count": metrics.error_count,
                    "success_rate": metrics.success_rate,
                })
                
                # Recovery action: reset version, increase priority
                skill.health = "degraded"
                skill.mutation_count += 1
                logger.warning(f"Flagged {skill_id} for recovery")

        return healing_results

    def evolve(self) -> Dict:
        """Run one full evolution cycle."""
        cycle_start = datetime.utcnow()
        
        evolution_report = {
            "cycle_timestamp": cycle_start.isoformat(),
            "stage_results": {},
        }

        try:
            # Stage 1: Observe
            logger.info("=== Evolution Cycle: OBSERVE ===")
            observation = self.observe()
            evolution_report["stage_results"]["observe"] = {
                "total_skills": observation["total_skills"],
                "anomalies_detected": len(observation["anomalies"]),
            }
            logger.info(f"Observed {observation['total_skills']} skills")

            # Stage 2: Mutate
            logger.info("=== Evolution Cycle: MUTATE ===")
            mutated = self.mutate(mutation_rate=0.15)
            evolution_report["stage_results"]["mutate"] = {
                "mutants_created": len(mutated),
                "mutant_ids": mutated,
            }
            logger.info(f"Created {len(mutated)} mutants")

            # Stage 3: Select
            logger.info("=== Evolution Cycle: SELECT ===")
            selection = self.select()
            evolution_report["stage_results"]["select"] = selection
            logger.info(f"Culled {len(selection['culled'])}, promoted {len(selection['promoted'])}")

            # Stage 4: Reproduce
            logger.info("=== Evolution Cycle: REPRODUCE ===")
            offspring = self.reproduce()
            evolution_report["stage_results"]["reproduce"] = {
                "offspring_created": len(offspring),
                "offspring_ids": offspring,
            }
            logger.info(f"Created {len(offspring)} offspring")

            # Stage 5: Heal
            logger.info("=== Evolution Cycle: HEAL ===")
            healing = self.heal()
            evolution_report["stage_results"]["heal"] = healing
            logger.info(f"Flagged {len(healing['critical'])} skills for recovery")

            # Save state
            self._save_registry()
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
            evolution_report["cycle_duration_seconds"] = cycle_duration

            # Log to JSONL
            self._log_evolution(evolution_report)

            logger.info(f"Evolution cycle completed in {cycle_duration:.1f}s")
            return evolution_report

        except Exception as e:
            logger.error(f"Evolution cycle failed: {e}", exc_info=True)
            return {"error": str(e)}

    def report(self) -> Dict:
        """Generate ecosystem health dashboard."""
        skill_ids = list(self.skills.keys())
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "ecosystem": {
                "total_skills": len(skill_ids),
                "active_skills": sum(1 for s in self.skills.values() if s.status == "active"),
                "deprecated_skills": sum(1 for s in self.skills.values() if s.status == "deprecated"),
                "avg_generation": sum(s.generation for s in self.skills.values()) / len(self.skills) if self.skills else 0,
            },
            "health": self.telemetry.get_ecosystem_health(skill_ids),
            "top_performers": [],
            "at_risk": [],
            "categories": self._get_category_stats(),
        }

        # Top performers
        fitness_scores = self.telemetry.get_fitness_scores(skill_ids, period_days=7)
        for skill_id, fitness in fitness_scores[:5]:
            skill = self.skills[skill_id]
            report["top_performers"].append({
                "skill_id": skill_id,
                "name": skill.name,
                "fitness": fitness,
                "generation": skill.generation,
            })

        # At risk
        for skill_id, fitness in fitness_scores[-5:]:
            skill = self.skills[skill_id]
            report["at_risk"].append({
                "skill_id": skill_id,
                "name": skill.name,
                "fitness": fitness,
                "health": skill.health,
            })

        return report

    def _get_category_stats(self) -> Dict:
        """Get statistics by category."""
        stats = {}
        for skill in self.skills.values():
            if skill.category not in stats:
                stats[skill.category] = {
                    "total": 0,
                    "active": 0,
                    "avg_fitness": 0,
                }
            stats[skill.category]["total"] += 1
            if skill.status == "active":
                stats[skill.category]["active"] += 1
            stats[skill.category]["avg_fitness"] += skill.fitness_score

        for cat in stats:
            if stats[cat]["total"] > 0:
                stats[cat]["avg_fitness"] = round(
                    stats[cat]["avg_fitness"] / stats[cat]["total"], 3
                )

        return stats

    def _get_short_hash(self) -> str:
        """Generate short hash for unique IDs."""
        return hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:8]

    def _log_evolution(self, report: Dict) -> None:
        """Log evolution cycle to JSONL."""
        log_file = self.log_dir / "evolution_log.jsonl"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(report) + "\n")
        except IOError as e:
            logger.error(f"Failed to write evolution log: {e}")


def setup_logging(log_level=logging.INFO) -> None:
    """Configure logging."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("organism.log"),
        ],
    )
