"""
Skill Organism Evolution Cycle Runner
Standalone script to execute one evolution cycle and generate reports.
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

from organism import SkillOrganism, setup_logging


def main():
    """Main entry point for evolution cycle."""
    parser = argparse.ArgumentParser(
        description="Run a skill organism evolution cycle"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("skill_registry.json"),
        help="Path to skill registry",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("skill_telemetry.db"),
        help="Path to telemetry database",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("."),
        help="Directory for evolution logs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving changes",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force evolution even if conditions not met",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("evolution_report.md"),
        help="Path to write markdown report",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    logger.info("Skill Organism Evolution Cycle Starting")
    logger.info(f"Registry: {args.registry}")
    logger.info(f"Telemetry DB: {args.db}")
    logger.info(f"Dry run: {args.dry_run}")

    # Initialize organism
    try:
        organism = SkillOrganism(
            registry_path=args.registry,
            telemetry_db=args.db,
            log_dir=args.log_dir,
        )
    except Exception as e:
        logger.error(f"Failed to initialize organism: {e}")
        return 1

    # Run evolution cycle
    try:
        evolution_result = organism.evolve()
        
        if args.dry_run:
            logger.info("DRY RUN: Changes not saved")
        else:
            logger.info("Evolution cycle completed successfully")

        # Generate report
        report = organism.report()
        _write_report(report, args.output_report, evolution_result)

        # Output to console
        print("\n" + "=" * 60)
        print("EVOLUTION CYCLE REPORT")
        print("=" * 60)
        print(json.dumps(report, indent=2))

        return 0

    except Exception as e:
        logger.error(f"Evolution cycle failed: {e}", exc_info=True)
        return 1


def _write_report(report: dict, output_path: Path, evolution_result: dict) -> None:
    """Write human-readable markdown report."""
    timestamp = datetime.utcnow().isoformat()
    
    lines = [
        "# Skill Organism Evolution Report",
        f"\n**Generated:** {timestamp}\n",
        
        "## Ecosystem Overview",
        f"- **Total Skills:** {report['ecosystem']['total_skills']}",
        f"- **Active Skills:** {report['ecosystem']['active_skills']}",
        f"- **Deprecated Skills:** {report['ecosystem']['deprecated_skills']}",
        f"- **Average Generation:** {report['ecosystem']['avg_generation']:.1f}",
        "",
        
        "## Health Status",
        f"- **Ecosystem Health Score:** {report['health']['ecosystem_health_score']}",
        f"- **Healthy Skills:** {report['health']['healthy']}",
        f"- **Degraded Skills:** {report['health']['degraded']}",
        f"- **Critical Skills:** {report['health']['critical']}",
        f"- **Average Success Rate:** {report['health']['avg_success_rate']}",
        "",
        
        "## Evolution Cycle Results",
    ]
    
    if 'stage_results' in evolution_result:
        stages = evolution_result['stage_results']
        
        if 'observe' in stages:
            lines.extend([
                "### Observe",
                f"- Detected {stages['observe']['anomalies_detected']} anomalies",
            ])
        
        if 'mutate' in stages:
            lines.extend([
                "### Mutate",
                f"- Created {stages['mutate']['mutants_created']} mutants",
            ])
        
        if 'select' in stages:
            lines.extend([
                "### Select",
                f"- Culled {len(stages['select']['culled'])} low performers",
                f"- Promoted {len(stages['select']['promoted'])} high performers",
            ])
        
        if 'reproduce' in stages:
            lines.extend([
                "### Reproduce",
                f"- Created {stages['reproduce']['offspring_created']} offspring",
            ])
        
        if 'heal' in stages:
            lines.extend([
                "### Heal",
                f"- Flagged {len(stages['heal']['critical'])} for recovery",
            ])
    
    lines.extend(["", "## Top Performers"])
    for i, performer in enumerate(report['top_performers'], 1):
        lines.append(
            f"{i}. **{performer['name']}** (Gen {performer['generation']}) "
            f"- Fitness: {performer['fitness']}"
        )
    
    lines.extend(["", "## At Risk"])
    for i, at_risk in enumerate(report['at_risk'], 1):
        lines.append(
            f"{i}. **{at_risk['name']}** - Fitness: {at_risk['fitness']}, "
            f"Health: {at_risk['health']}"
        )
    
    lines.extend(["", "## Category Statistics"])
    for category, stats in report['categories'].items():
        lines.extend([
            f"### {category.upper()}",
            f"- Total: {stats['total']}",
            f"- Active: {stats['active']}",
            f"- Average Fitness: {stats['avg_fitness']}",
        ])
    
    lines.append("")
    
    try:
        with open(output_path, "w") as f:
            f.write("\n".join(lines))
        logging.getLogger(__name__).info(f"Report written to {output_path}")
    except IOError as e:
        logging.getLogger(__name__).error(f"Failed to write report: {e}")


if __name__ == "__main__":
    exit(main())