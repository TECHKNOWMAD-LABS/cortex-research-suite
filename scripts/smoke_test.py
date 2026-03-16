#!/usr/bin/env python3
"""Cortex Research Suite v1.1.0 — end-to-end smoke test.
Verifies all components work without requiring an API key.
Exit code 0 = all checks passed. Exit code 1 = fix before tagging.
"""
from pathlib import Path
import json
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKS_PASSED = 0
CHECKS_FAILED = 0


def check(name: str, condition: bool, detail: str = ""):
    global CHECKS_PASSED, CHECKS_FAILED
    if condition:
        CHECKS_PASSED += 1
        print(f"  [PASS] {name}")
    else:
        CHECKS_FAILED += 1
        print(f"  [FAIL] {name} -- {detail}")


def main():
    print("Cortex Research Suite v1.1.0 — Smoke Test")
    print("=" * 50)

    # 1. Skill count
    skills = [p for p in (REPO_ROOT / "skills").iterdir() if (p / "SKILL.md").exists()]
    check("26 skills with SKILL.md", len(skills) == 26, f"found {len(skills)}")

    # 2. ARENA.md count
    arenas = [p for p in (REPO_ROOT / "skills").iterdir() if (p / "ARENA.md").exists()]
    check("26 skills with ARENA.md", len(arenas) == 26, f"found {len(arenas)}")

    # 3. Import all skill script modules (no ImportErrors)
    import_ok = True
    for skill_dir in skills:
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            for py in scripts_dir.glob("*.py"):
                if py.name == "__init__.py":
                    continue
                try:
                    file_size = py.stat().st_size
                    if file_size > 1_000_000:  # 1 MB cap
                        print(f"    WARNING: Skipping {py} — file too large ({file_size} bytes)")
                        continue
                    compile(py.read_text(), str(py), "exec")
                except SyntaxError as e:
                    import_ok = False
                    print(f"    SyntaxError in {py}: {e}")
    check("All skill scripts compile without SyntaxError", import_ok)

    # 4. MindSpider demo data
    sys.path.insert(0, str(REPO_ROOT / "skills" / "mindspider-connector" / "scripts"))
    try:
        from connector import generate_demo_data
        data = generate_demo_data()
        check("MindSpider demo data generates", len(data) > 0, f"got {len(data)} topics")
    except Exception as e:
        check("MindSpider demo data generates", False, str(e))

    # 5. GraphStore initialisation
    sys.path.insert(0, str(REPO_ROOT / "knowledge"))
    try:
        from graph_store import GraphStore
        gs = GraphStore()
        check("GraphStore initialises", True)
    except Exception as e:
        check("GraphStore initialises", False, str(e))

    # 6. ArenaConfig loading
    sys.path.insert(0, str(REPO_ROOT / "skill-organism"))
    try:
        from arena_config import ArenaConfig
        cfg = ArenaConfig.load(skills[0])
        check("ArenaConfig loads from ARENA.md", cfg.skill_name != "")
    except Exception as e:
        check("ArenaConfig loads from ARENA.md", False, str(e))

    # 7. evolution_log.jsonl valid JSONL
    log_path = REPO_ROOT / "skill-organism" / "evolution_log.jsonl"
    if log_path.exists():
        lines = log_path.read_text().strip().splitlines()
        try:
            valid_jsonl = all(json.loads(line) for line in lines if line.strip())
            check(f"evolution_log.jsonl valid ({len(lines)} lines)", valid_jsonl)
        except json.JSONDecodeError as e:
            check("evolution_log.jsonl valid JSONL", False, str(e))
    else:
        check("evolution_log.jsonl exists", False, "file not found")

    # 8. skill_arena_demo.html security checks
    arena_path = REPO_ROOT / "dashboards" / "skill_arena_demo.html"
    if arena_path.exists():
        html = arena_path.read_text()
        check("Arena HTML has CSP meta tag", "Content-Security-Policy" in html)
        check("Arena HTML uses sessionStorage for API key", "sessionStorage" in html)
    else:
        check("skill_arena_demo.html exists", False)

    # 9. All baselines exist
    baselines = list((REPO_ROOT / "benchmarks" / "baselines").glob("*.json"))
    check(f"Baselines exist ({len(baselines)})", len(baselines) >= 21)

    # 10. All rubrics exist
    rubrics = list((REPO_ROOT / "skills" / "skill-test-harness" / "rubrics").glob("*.yaml"))
    check(f"Rubrics exist ({len(rubrics)})", len(rubrics) >= 21)

    # 11. LEGAL_NOTES.md exists
    check("LEGAL_NOTES.md exists", (REPO_ROOT / "LEGAL_NOTES.md").exists())

    # 12. DATA_NOTICE.md exists
    check("DATA_NOTICE.md exists", (REPO_ROOT / "datasets" / "mindspider" / "DATA_NOTICE.md").exists())

    # Summary
    total = CHECKS_PASSED + CHECKS_FAILED
    print(f"\nSmoke test: {CHECKS_PASSED}/{total} checks passed")
    if CHECKS_FAILED > 0:
        print("FIX FAILURES BEFORE TAGGING v1.1.0")
        sys.exit(1)
    else:
        print("All checks passed. Safe to tag v1.1.0.")
        sys.exit(0)


if __name__ == "__main__":
    main()
