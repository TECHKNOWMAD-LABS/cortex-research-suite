#!/usr/bin/env bash
# Run evaluation for all 27 skills using offline mode
# Usage: bash skills/skill-test-harness/scripts/run_all_evals.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO_ROOT"

EVAL_SCRIPT="skills/skill-test-harness/scripts/eval_judge.py"
GENERATOR="datasets/generators/skill_dataset_generator.py"
OUTPUT_DIR="benchmarks/results"

echo "=== Cortex Research Suite — Full Evaluation Run ==="
echo "Repo root: $REPO_ROOT"
echo ""

# Step 1: Generate datasets for all skills
echo "Step 1: Generating synthetic datasets..."
python3 "$GENERATOR" --all-skills --n 50 --output-dir datasets/synthetic
echo ""

# Step 2: Run evaluation for each skill
SKILLS=$(ls -1 skills/ | grep -v __pycache__)
TOTAL=0
PASSED=0
FAILED=0

for skill in $SKILLS; do
    DATASET="datasets/synthetic/$skill/shard_000.json"
    if [ ! -f "$DATASET" ]; then
        echo "  [SKIP] $skill — no dataset at $DATASET"
        continue
    fi

    TOTAL=$((TOTAL + 1))
    echo -n "  Evaluating $skill... "

    if python3 "$EVAL_SCRIPT" --skill "$skill" --dataset "$DATASET" --offline --compare-baseline > /dev/null 2>&1; then
        echo "[PASS]"
        PASSED=$((PASSED + 1))
    else
        echo "[FAIL]"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=== Results ==="
echo "Total: $TOTAL | Passed: $PASSED | Failed: $FAILED"

if [ "$FAILED" -gt 0 ]; then
    echo "WARNING: $FAILED skills failed evaluation"
    exit 1
fi

echo "All evaluations passed."
exit 0
