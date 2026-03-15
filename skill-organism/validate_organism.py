"""
Quick validation script to test the Skill Organism system.
Run this to verify the system is properly initialized.
"""

import json
import sys
from pathlib import Path

def validate():
    """Validate organism components."""
    print("=" * 60)
    print("Skill Organism System Validation")
    print("=" * 60)
    
    checks = []
    
    # Check 1: Registry file
    registry_path = Path("skill_registry.json")
    if registry_path.exists():
        try:
            with open(registry_path) as f:
                data = json.load(f)
            skill_count = len(data.get("skills", []))
            print(f"✓ skill_registry.json: {skill_count} skills loaded")
            checks.append(True)
        except Exception as e:
            print(f"✗ skill_registry.json: {e}")
            checks.append(False)
    else:
        print(f"✗ skill_registry.json: File not found")
        checks.append(False)
    
    # Check 2: Python imports
    try:
        from telemetry import SkillTelemetry
        from organism import SkillOrganism
        from skill_dna import SkillDNA
        print("✓ All Python modules import successfully")
        checks.append(True)
    except ImportError as e:
        print(f"✗ Import error: {e}")
        checks.append(False)
    
    # Check 3: Create telemetry instance
    try:
        telemetry = SkillTelemetry(Path(":memory:"))  # In-memory DB
        print("✓ SkillTelemetry: Can initialize")
        checks.append(True)
    except Exception as e:
        print(f"✗ SkillTelemetry: {e}")
        checks.append(False)
    
    # Check 4: Create organism instance
    try:
        organism = SkillOrganism(
            registry_path=registry_path,
            telemetry_db=Path(":memory:"),
            log_dir=Path("."),
        )
        print(f"✓ SkillOrganism: Initialized with {len(organism.skills)} skills")
        checks.append(True)
    except Exception as e:
        print(f"✗ SkillOrganism: {e}")
        checks.append(False)
    
    # Check 5: Validate registry integrity
    try:
        with open(registry_path) as f:
            data = json.load(f)
        
        ecosystem = data.get("ecosystem", {})
        skills = data.get("skills", [])
        
        # Validate ecosystem config
        required_config = [
            "name", "version", "carrying_capacity", 
            "evolution_interval_hours", "fitness_threshold"
        ]
        missing_config = [k for k in required_config if k not in ecosystem]
        
        if missing_config:
            print(f"✗ Registry: Missing config keys: {missing_config}")
            checks.append(False)
        else:
            print("✓ Registry: Ecosystem config complete")
            checks.append(True)
            
        # Validate skill structure
        required_fields = [
            "id", "name", "version", "status", "fitness_score",
            "category", "health", "generation"
        ]
        
        malformed = []
        for skill in skills:
            missing = [f for f in required_fields if f not in skill]
            if missing:
                malformed.append((skill.get("id"), missing))
        
        if malformed:
            print(f"✗ Registry: {len(malformed)} skills malformed")
            for skill_id, missing in malformed[:3]:
                print(f"  - {skill_id}: missing {missing}")
            checks.append(False)
        else:
            print(f"✓ Registry: All {len(skills)} skills well-formed")
            checks.append(True)
    
    except Exception as e:
        print(f"✗ Registry validation: {e}")
        checks.append(False)
    
    # Check 6: Category distribution
    try:
        with open(registry_path) as f:
            data = json.load(f)
        
        categories = {}
        for skill in data.get("skills", []):
            cat = skill.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"✓ Category Distribution: {dict(categories)}")
        checks.append(True)
    except Exception as e:
        print(f"✗ Category distribution: {e}")
        checks.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    print(f"Validation Result: {passed}/{total} checks passed")
    print("=" * 60)
    
    return all(checks)


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)