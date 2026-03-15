"""
Example Usage: Skill Organism
Demonstrates core API patterns for integrating with your skill system.
"""

from organism import SkillOrganism, setup_logging
from telemetry import SkillTelemetry
import logging

# Setup logging
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)


def example_1_record_telemetry():
    """Example 1: Record skill invocation telemetry."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Record Telemetry")
    print("="*60)
    
    telemetry = SkillTelemetry()
    
    # Simulate skill executions
    executions = [
        ("tkm-research-commander", 1500, True, 3200, 0.9),
        ("tkm-research-commander", 1600, True, 3100, 0.95),
        ("tkm-swarm-commander", 2100, True, 4500, 0.85),
        ("tkm-model-evaluator", 3200, False, 2800, 0.5),  # Failed
    ]
    
    for skill_id, duration, success, tokens, satisfaction in executions:
        telemetry.record_invocation(
            skill_id=skill_id,
            duration_ms=duration,
            success=success,
            tokens_used=tokens,
            user_satisfaction=satisfaction,
        )
        status = "✓" if success else "✗"
        print(f"{status} Recorded: {skill_id} ({duration}ms, {tokens} tokens)")


def example_2_get_metrics():
    """Example 2: Query skill metrics."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Query Metrics")
    print("="*60)
    
    telemetry = SkillTelemetry()
    
    # Get metrics for a skill
    metrics = telemetry.get_skill_metrics("tkm-research-commander", period_days=7)
    
    if metrics:
        print(f"Skill: {metrics.skill_id}")
        print(f"  Invocations: {metrics.invocation_count}")
        print(f"  Success Rate: {metrics.success_rate * 100:.1f}%")
        print(f"  Avg Latency: {metrics.avg_latency_ms}ms")
        print(f"  Median Latency: {metrics.median_latency_ms}ms")
        print(f"  P95 Latency: {metrics.p95_latency_ms}ms")
        print(f"  Tokens Used: {metrics.total_tokens_used}")
        print(f"  Avg Satisfaction: {metrics.avg_satisfaction}")
        print(f"  Health: {metrics.health_status}")


def example_3_ecosystem_health():
    """Example 3: Get ecosystem health dashboard."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Ecosystem Health")
    print("="*60)
    
    organism = SkillOrganism()
    report = organism.report()
    
    print(f"Total Skills: {report['ecosystem']['total_skills']}")
    print(f"Active Skills: {report['ecosystem']['active_skills']}")
    print(f"Deprecated Skills: {report['ecosystem']['deprecated_skills']}")
    print(f"Average Generation: {report['ecosystem']['avg_generation']:.1f}")
    
    print(f"\nHealth Status:")
    health = report['health']
    print(f"  Healthy: {health['healthy']}")
    print(f"  Degraded: {health['degraded']}")
    print(f"  Critical: {health['critical']}")
    print(f"  Ecosystem Score: {health['ecosystem_health_score']:.3f}")
    
    print(f"\nTop Performers:")
    for i, perf in enumerate(report['top_performers'][:3], 1):
        print(f"  {i}. {perf['name']} (Gen {perf['generation']}, "
              f"Fitness: {perf['fitness']})")
    
    print(f"\nAt Risk:")
    for i, risk in enumerate(report['at_risk'][:3], 1):
        print(f"  {i}. {risk['name']} (Fitness: {risk['fitness']}, "
              f"Health: {risk['health']})")


def example_4_fitness_ranking():
    """Example 4: Get fitness rankings."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Fitness Rankings")
    print("="*60)
    
    telemetry = SkillTelemetry()
    organism = SkillOrganism()
    
    skill_ids = list(organism.skills.keys())
    rankings = telemetry.get_fitness_scores(skill_ids, period_days=7)
    
    print("Top 5 Skills by Fitness:")
    for i, (skill_id, fitness) in enumerate(rankings[:5], 1):
        skill = organism.skills[skill_id]
        print(f"  {i}. {skill.name}")
        print(f"     ID: {skill_id}")
        print(f"     Fitness: {fitness}")
        print(f"     Generation: {skill.generation}")


def example_5_observe():
    """Example 5: Observe ecosystem state."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Observe Ecosystem")
    print("="*60)
    
    organism = SkillOrganism()
    observation = organism.observe()
    
    print(f"Timestamp: {observation['timestamp']}")
    print(f"Total Skills: {observation['total_skills']}")
    print(f"Anomalies Detected: {len(observation['anomalies'])}")
    
    if observation['anomalies']:
        print(f"\nAnomalies:")
        for anomaly in observation['anomalies'][:2]:
            print(f"  - {anomaly['skill_id']}: {anomaly['count']} spikes")
    
    print(f"\nEcosystem Health:")
    health = observation['ecosystem_health']
    print(f"  Health Score: {health['ecosystem_health_score']}")
    print(f"  Healthy: {health['healthy']}")
    print(f"  Critical: {health['critical']}")


def example_6_dry_run_evolution():
    """Example 6: Run evolution cycle (dry run)."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Evolution Cycle (Dry Run)")
    print("="*60)
    
    organism = SkillOrganism()
    
    # Run evolution (in-memory, no persistence)
    result = organism.evolve()
    
    print(f"Cycle Timestamp: {result.get('cycle_timestamp')}")
    print(f"Duration: {result.get('cycle_duration_seconds'):.2f}s")
    
    if 'stage_results' in result:
        stages = result['stage_results']
        
        if 'observe' in stages:
            print(f"\nObserve: {stages['observe']['anomalies_detected']} anomalies")
        
        if 'mutate' in stages:
            print(f"Mutate: {stages['mutate']['mutants_created']} mutants")
        
        if 'select' in stages:
            print(f"Select: Culled {len(stages['select']['culled'])}, "
                  f"Promoted {len(stages['select']['promoted'])}")
        
        if 'reproduce' in stages:
            print(f"Reproduce: {stages['reproduce']['offspring_created']} offspring")
        
        if 'heal' in stages:
            print(f"Heal: {len(stages['heal']['critical'])} flagged")


def example_7_anomaly_detection():
    """Example 7: Detect anomalies."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Anomaly Detection")
    print("="*60)
    
    telemetry = SkillTelemetry()
    
    # Create some test data with an outlier
    test_data = [
        ("test-skill", 100, True, 0),
        ("test-skill", 110, True, 0),
        ("test-skill", 105, True, 0),
        ("test-skill", 350, True, 0),  # Outlier
        ("test-skill", 95, True, 0),
    ]
    
    for skill_id, duration, success, tokens in test_data:
        telemetry.record_invocation(skill_id, duration, success, tokens)
    
    anomalies = telemetry.detect_anomalies("test-skill", sigma=1.5)
    
    if anomalies:
        print(f"Detected {len(anomalies)} anomaly(ies):")
        for anom in anomalies:
            print(f"  - {anom['type']}: {anom['duration_ms']}ms "
                  f"(z={anom['z_score']})")
    else:
        print("No anomalies detected")


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("Skill Organism - API Usage Examples")
    print("█"*60)
    
    # Run examples
    example_1_record_telemetry()
    example_2_get_metrics()
    example_3_ecosystem_health()
    example_4_fitness_ranking()
    example_5_observe()
    example_6_dry_run_evolution()
    example_7_anomaly_detection()
    
    print("\n" + "█"*60)
    print("Examples completed!")
    print("█"*60)
