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

        # Get telemetry for each skill (skip extinct — no point observing fossils)
        for skill_id in skill_ids:
            skill_entry = self.skills[skill_id]
            if skill_entry.status == "extinct":
                continue

            metrics = self.telemetry.get_skill_metrics(skill_id, period_days=7)

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

    def _is_founding_skill(self, skill: SkillEntry) -> bool:
        """Check if a skill is part of the founding population.

        Founding skills (generation 0-1) are hand-crafted with specific purpose.
        They are immortal — they can evolve but never deprecate or go extinct.
        Only evolved offspring (hybrids, mutants, resurrected variants at gen 2+)
        face selection pressure.

        The founding_generation threshold is configurable via ecosystem config.
        """
        max_founding_gen = self.ecosystem_config.get("founding_generation", 1)
        return skill.generation <= max_founding_gen

    def select(self) -> Dict:
        """Fitness scoring and natural selection. Cull low performers.

        Founding skills (generation 0-1) are protected from deprecation.
        They represent the core genome — intentionally designed skills that
        should always remain available. Only evolved offspring face culling.
        """
        selection_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "culled": [],
            "promoted": [],
            "protected": [],
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

            # Track peak fitness for fossil value estimation
            if skill.peak_fitness is None or fitness > (skill.peak_fitness or 0):
                skill.peak_fitness = fitness

            # Cull low performers — but NEVER founding skills
            if fitness < self.ecosystem_config.get("fitness_threshold", 0.6):
                if self._is_founding_skill(skill):
                    # Founding skills are immortal — log but don't deprecate
                    selection_results["protected"].append({
                        "skill_id": skill_id,
                        "fitness": fitness,
                        "generation": skill.generation,
                        "reason": "founding_skill_protected"
                    })
                    logger.info(
                        f"Protected founding skill {skill_id} "
                        f"(fitness={fitness:.3f}, gen={skill.generation}) — immortal"
                    )
                elif skill.usage_count < 5:  # Only cull evolved offspring if rarely used
                    skill.status = "deprecated"
                    skill.deprecated_at = datetime.utcnow().isoformat()
                    selection_results["culled"].append({
                        "skill_id": skill_id,
                        "fitness": fitness,
                        "peak_fitness": skill.peak_fitness,
                        "reason": "low_fitness"
                    })
                    logger.info(
                        f"Deprecated {skill_id} (fitness={fitness:.3f}, "
                        f"peak={skill.peak_fitness:.3f}) → fossil archive"
                    )

            # Promote high performers
            if fitness > self.ecosystem_config.get("auto_deploy_threshold", 0.8):
                skill.status = "active"
                selection_results["promoted"].append({
                    "skill_id": skill_id,
                    "fitness": fitness,
                })
                logger.info(f"Promoted {skill_id} to auto-deploy (fitness: {fitness})")

        return selection_results

    def _get_fossil_archive(self) -> List[SkillEntry]:
        """Return deprecated skills ranked by peak fitness (best fossils first)."""
        fossils = [
            s for s in self.skills.values()
            if s.status == "deprecated" and s.peak_fitness is not None
        ]
        fossils.sort(key=lambda s: s.peak_fitness or 0, reverse=True)
        return fossils

    def _resurrect_fossil(self, fossil: SkillEntry, partner: SkillEntry) -> SkillEntry:
        """Resurrect a deprecated skill by crossbreeding with a living partner.

        The fossil contributes its category, dependencies, and stored peak genetics.
        The partner contributes its proven fitness and active traits.
        The offspring inherits the best of both lineages with a mutation bump.
        """
        offspring_id = f"resurrected_{fossil.id}_{self._get_short_hash()}"

        # Weighted fitness: favor the living partner but preserve fossil potential
        inherited_fitness = (
            0.4 * (fossil.peak_fitness or fossil.fitness_score)
            + 0.6 * partner.fitness_score
        )

        offspring = SkillEntry(
            id=offspring_id,
            name=f"{fossil.name} (resurrected gen-{fossil.generation + 1})",
            version="1.0.0",
            status="active",
            fitness_score=min(inherited_fitness, 1.0),
            usage_count=0,
            last_used=None,
            created=datetime.utcnow().isoformat(),
            category=fossil.category,
            dependencies=list(set(fossil.dependencies + partner.dependencies)),
            health="healthy",
            generation=max(fossil.generation, partner.generation) + 1,
            parent_skill=f"{fossil.id}+{partner.id}",
            mutation_count=fossil.mutation_count + 1,
            peak_fitness=inherited_fitness,
            resurrection_count=fossil.resurrection_count + 1,
        )

        # Mark the fossil as extinct — it gave its DNA, now it rests
        fossil.status = "extinct"

        return offspring

    def reproduce(self) -> List[str]:
        """Create new skills from high-performing combinations.

        Two reproduction strategies:
        1. Standard breeding: top performers crossover to create hybrids
        2. Fossil resurrection: when mean fitness drops or population thins,
           resurrect high-potential deprecated skills by crossing them with
           living top performers. Recessive traits re-emerge under pressure.
        """
        new_skills = []

        fitness_scores = self.telemetry.get_fitness_scores(
            list(self.skills.keys()), period_days=7
        )

        # Get top 10 active performers
        top_skills = [skill_id for skill_id, _ in fitness_scores[:10]]

        # --- Strategy 1: Standard breeding ---
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

        # --- Strategy 2: Fossil resurrection ---
        fossils = self._get_fossil_archive()
        if fossils and top_skills:
            # Calculate population pressure: resurrect when active population is thin
            active_count = sum(1 for s in self.skills.values() if s.status == "active")
            total_count = len(self.skills)
            active_ratio = active_count / total_count if total_count > 0 else 1.0

            # Calculate mean fitness of active population
            active_fitness = [f for sid, f in fitness_scores if self.skills.get(sid) and self.skills[sid].status == "active"]
            mean_fitness = sum(active_fitness) / len(active_fitness) if active_fitness else 0.5

            # Resurrection triggers:
            # 1. Active population dropped below 60% → genetic diversity crisis
            # 2. Mean fitness declining below 0.65 → population stagnation
            # 3. High-value fossils exist (peak_fitness > current mean)
            resurrection_pressure = 0.0
            if active_ratio < 0.6:
                resurrection_pressure += 0.4
                logger.info(f"Resurrection trigger: low active ratio ({active_ratio:.2f})")
            if mean_fitness < 0.65:
                resurrection_pressure += 0.3
                logger.info(f"Resurrection trigger: low mean fitness ({mean_fitness:.3f})")

            # Resurrect fossils whose peak exceeded current population mean
            valuable_fossils = [f for f in fossils if (f.peak_fitness or 0) > mean_fitness]
            if valuable_fossils:
                resurrection_pressure += 0.3
                logger.info(f"Resurrection trigger: {len(valuable_fossils)} fossils with peak > mean")

            if resurrection_pressure >= 0.3:
                # Number of resurrections scales with pressure (1-3)
                num_resurrections = min(
                    max(1, int(resurrection_pressure * 5)),
                    len(valuable_fossils or fossils),
                    3,  # cap at 3 per cycle
                )

                candidates = valuable_fossils if valuable_fossils else fossils
                for fossil in candidates[:num_resurrections]:
                    partner_id = random.choice(top_skills)
                    partner = self.skills[partner_id]

                    resurrected = self._resurrect_fossil(fossil, partner)
                    self.skills[resurrected.id] = resurrected
                    new_skills.append(resurrected.id)
                    logger.info(
                        f"RESURRECT {fossil.id} (peak={fossil.peak_fitness:.3f}) "
                        f"x {partner_id} → {resurrected.id} "
                        f"(fitness={resurrected.fitness_score:.3f}, "
                        f"resurrection #{resurrected.resurrection_count})"
                    )

        return new_skills

    def heal(self) -> Dict:
        """Detect degraded skills, enforce deprecation decay, and recover the population.

        Four healing mechanisms:
        0. Founding skill restoration: founding skills (gen 0-1) that were
           incorrectly deprecated or marked extinct are restored to active.
           Founding skills are intentionally designed — they never die.
        1. Critical recovery: flag degraded active skills for mutation/rescue
        2. Deprecation decay: deprecated *evolved* skills that exceed TTL become
           extinct (their DNA was either resurrected or proven unviable).
           Founding skills are exempt from decay.
        3. Population collapse recovery: if active count drops critically low,
           force-resurrect the best available fossils to maintain ecosystem viability
        """
        now = datetime.utcnow()
        decay_ttl_days = self.ecosystem_config.get("deprecation_ttl_days", 30)
        min_active_ratio = self.ecosystem_config.get("min_active_ratio", 0.4)

        healing_results = {
            "timestamp": now.isoformat(),
            "recovered": [],
            "critical": [],
            "founding_restored": [],
            "decayed_to_extinct": [],
            "emergency_resurrections": [],
        }

        # --- Phase 0: Founding skill restoration ---
        # Founding skills are the core genome. If any were incorrectly
        # deprecated or extinct (from before this protection existed),
        # restore them immediately.
        for skill_id, skill in list(self.skills.items()):
            if self._is_founding_skill(skill) and skill.status in ("deprecated", "extinct"):
                old_status = skill.status
                skill.status = "active"
                skill.deprecated_at = None
                skill.health = "healthy"
                healing_results["founding_restored"].append({
                    "skill_id": skill_id,
                    "from_status": old_status,
                    "fitness": skill.fitness_score,
                    "generation": skill.generation,
                })
                healing_results["recovered"].append(skill_id)
                logger.info(
                    f"RESTORED founding skill {skill_id} from {old_status} → active "
                    f"(gen={skill.generation}, fitness={skill.fitness_score:.3f})"
                )

        # --- Phase 1: Critical active skill recovery ---
        for skill_id, skill in list(self.skills.items()):
            if skill.status in ("deprecated", "extinct"):
                continue

            metrics = self.telemetry.get_skill_metrics(skill_id, period_days=7)

            if metrics and metrics.health_status == "critical":
                healing_results["critical"].append({
                    "skill_id": skill_id,
                    "error_count": metrics.error_count,
                    "success_rate": metrics.success_rate,
                })

                # Recovery action: flag for mutation priority
                skill.health = "degraded"
                skill.mutation_count += 1
                logger.warning(f"Flagged {skill_id} for recovery")

        # --- Phase 2: Deprecation decay (TTL enforcement) ---
        # Only evolved offspring (gen 2+) can decay to extinct.
        # Founding skills are exempt — they were restored in Phase 0.
        for skill_id, skill in list(self.skills.items()):
            if skill.status != "deprecated":
                continue

            # Double-check: founding skills should never be here after Phase 0
            if self._is_founding_skill(skill):
                continue

            if skill.deprecated_at:
                try:
                    deprecated_time = datetime.fromisoformat(skill.deprecated_at)
                    days_deprecated = (now - deprecated_time).total_seconds() / 86400

                    if days_deprecated >= decay_ttl_days:
                        skill.status = "extinct"
                        healing_results["decayed_to_extinct"].append({
                            "skill_id": skill_id,
                            "days_deprecated": round(days_deprecated, 1),
                            "peak_fitness": skill.peak_fitness,
                            "was_resurrected": skill.resurrection_count > 0,
                        })
                        logger.info(
                            f"EXTINCT {skill_id} after {days_deprecated:.0f} days deprecated "
                            f"(peak={skill.peak_fitness}, resurrections={skill.resurrection_count})"
                        )
                except (ValueError, TypeError):
                    # Malformed timestamp — set it now, decay starts fresh
                    skill.deprecated_at = now.isoformat()
            else:
                # Legacy deprecated skill without timestamp — backfill
                skill.deprecated_at = now.isoformat()
                logger.info(f"Backfilled deprecated_at for {skill_id}")

        # --- Phase 3: Population collapse recovery ---
        active_count = sum(1 for s in self.skills.values() if s.status == "active")
        total_count = len(self.skills)
        active_ratio = active_count / total_count if total_count > 0 else 1.0

        if active_ratio < min_active_ratio:
            logger.warning(
                f"POPULATION COLLAPSE: {active_count}/{total_count} active "
                f"({active_ratio:.1%} < {min_active_ratio:.0%} threshold)"
            )

            # Emergency resurrection: pull best fossils back to life
            fossils = self._get_fossil_archive()
            if fossils:
                # Resurrect enough to reach minimum viable population
                target_active = max(int(total_count * min_active_ratio), active_count + 1)
                needed = target_active - active_count

                for fossil in fossils[:needed]:
                    fossil.status = "active"
                    fossil.health = "degraded"  # comes back weakened
                    fossil.deprecated_at = None
                    fossil.resurrection_count += 1
                    fossil.fitness_score = fossil.peak_fitness or 0.5  # restore to peak

                    healing_results["emergency_resurrections"].append({
                        "skill_id": fossil.id,
                        "restored_fitness": fossil.fitness_score,
                        "resurrection_count": fossil.resurrection_count,
                    })
                    healing_results["recovered"].append(fossil.id)

                    logger.info(
                        f"EMERGENCY RESURRECT {fossil.id} → active "
                        f"(fitness={fossil.fitness_score:.3f}, "
                        f"resurrection #{fossil.resurrection_count})"
                    )
            else:
                logger.error(
                    "Population collapse with no fossils available — "
                    "ecosystem needs manual intervention"
                )

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
            logger.info(
                f"Heal: {len(healing.get('founding_restored', []))} founding restored, "
                f"{len(healing['critical'])} critical, "
                f"{len(healing.get('decayed_to_extinct', []))} decayed→extinct, "
                f"{len(healing.get('emergency_resurrections', []))} emergency resurrections"
            )

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
                "extinct_skills": sum(1 for s in self.skills.values() if s.status == "extinct"),
                "fossil_archive_size": len(self._get_fossil_archive()),
                "total_resurrections": sum(s.resurrection_count for s in self.skills.values()),
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
