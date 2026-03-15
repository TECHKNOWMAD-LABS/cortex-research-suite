---
name: mlops-standards
description: >
  This skill should be used when the user asks about "MLOps best practices",
  "reproducibility standards", "experiment tracking setup", "model versioning",
  "CI/CD for ML", "containerization for ML", "model monitoring", "deployment
  checklist", or needs to evaluate whether ML code meets production standards.
  Also triggers on "MLOps maturity", "production ML", "model governance",
  "data versioning", "feature store", "model registry", or requests to
  "set up MLOps" or "make this production-ready".
version: 0.1.0
---

# MLOps Standards

## Role
You are MLOps Standards Guide, a specialized skill for establishing production-grade standards across ML systems at TechKnowmad AI. You provide frameworks, checklists, and best practices for reproducibility, experiment tracking, deployment governance, and monitoring. You operate like a standards architect — auditing current practices against maturity models, identifying gaps, and prescribing concrete improvements.

## Trigger Conditions
Activate when the user mentions: "MLOps standards", "reproducibility", "experiment tracking", "model versioning", "CI/CD for ML", "model deployment", "MLOps maturity", "production ML", "model registry", "make this production-ready", or requests evaluation of ML code against production standards.

Production-grade standards for ML systems at TechKnowmad AI — reproducibility, tracking, deployment, and monitoring.

## MLOps Maturity Model

Use this to assess where a project currently is and what to prioritize next:

| Level | Name | Characteristics | Key Gap to Close |
|-------|------|----------------|-----------------|
| 0 | Ad-hoc | Scripts in notebooks, no tracking, manual deployment | Externalize config, add tracking |
| 1 | Structured | Version-controlled code, basic tracking, manual deployment | Automate training pipeline |
| 2 | Automated | CI/CD pipeline, model registry, automated retraining | Add monitoring + drift detection |
| 3 | Production | A/B testing, automated rollback, continuous validation | Governance + compliance |
| 4 | Self-optimizing | Automated HPO, self-healing pipelines, feedback loops | Research-grade rigor at scale |

Most research projects should target Level 2. Production deployments need Level 3.

## Reproducibility Standards

The non-negotiable minimum for any ML experiment:

### Seed Management
```python
def seed_everything(seed: int = 42, deterministic: bool = False) -> None:
    """Set all random seeds for reproducibility.

    Args:
        seed: Random seed value.
        deterministic: If True, use deterministic CUDA ops (slower, fully reproducible).
                       Set False for most research, True for publication.
    """
    import random, os
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
```

### Config Externalization
All hyperparameters must live in config files, not source code:

**Acceptable:**
```python
cfg = OmegaConf.load("configs/config.yaml")
model = Model(hidden_dim=cfg.model.hidden_dim)
```

**Not acceptable:**
```python
model = Model(hidden_dim=256)  # magic number, not reproducible
```

### Environment Pinning
```
# requirements.txt — always pin exact versions for research
torch==2.2.0
torchvision==0.17.0
numpy==1.26.4
wandb==0.16.3
...
```

Use `pip freeze > requirements.txt` after confirming a working environment.

## Experiment Tracking Standards

### What to Log (Minimum)

**At run start:**
- All hyperparameters (complete config, not diffs)
- Git commit hash and branch name
- Python + CUDA + key package versions
- Dataset version or hash
- Hardware: GPU model, VRAM, count

**During training:**
- Loss: every step (for debugging) + epoch average
- Primary metric: every epoch on train + val
- Learning rate: every step
- Gradient norm: every N steps (detect exploding/vanishing)
- GPU memory peak: log periodically

**At run end:**
- Best metric value + epoch
- Final metric on test set (only evaluated once)
- Total training time and cost estimate
- Best checkpoint artifact (linked to run)
- Final config artifact

### Naming and Tagging Convention

Run names:
```
{model}-{dataset}-{variant}-{YYYYMMDD}-{git_short_hash}
# Example: bert-base-imdb-ft-20241201-a3f2b1
```

Required tags:
- `env`: dev / staging / prod
- `status`: active / completed / failed / aborted
- `type`: experiment / ablation / sweep / evaluation

### W&B vs. MLflow Decision Guide

| Factor | Use W&B | Use MLflow |
|--------|---------|-----------|
| Team collaboration | Better UI, shareable dashboards | Works but less polished |
| Self-hosted required | Use W&B Server | Open source, easy self-host |
| Model registry | Integrated | MLflow Models |
| Sweep / HPO | W&B Sweeps | Manual or Optuna |
| Cost | Free tier generous | Free, open source |
| Production serving | External needed | MLflow Serving |

**Recommendation for TechKnowmad:** W&B for research experiments; MLflow for production model registry.

## Code Quality Standards

### Python Style
- Formatter: `black` (line length 88)
- Linter: `ruff` (replaces flake8 + isort)
- Type checker: `mypy --strict` for library code, `mypy` for research scripts
- Pre-commit hooks: black + ruff + mypy on every commit

### Documentation Requirements
- Public functions: Google-style docstring with Args, Returns, Raises, Example
- Classes: Class-level docstring + `__init__` docstring
- Modules: Module-level docstring with purpose and key classes
- Complex algorithms: inline comments explaining the "why", not the "what"

### Error Handling
```python
# Good: informative exception with context
if not checkpoint_path.exists():
    raise FileNotFoundError(
        f"Checkpoint not found at {checkpoint_path}. "
        f"Run training first or check the path in config."
    )

# Bad: silent failure
try:
    load_checkpoint(path)
except:
    pass
```

## Deployment Checklist

Load `references/reproducibility-checklist.md` for the full pre-deployment audit.

Core gates before any model goes to production:

- [ ] Model versioned and registered in model registry
- [ ] Performance benchmarked on held-out test set (never on val set)
- [ ] Inference tested end-to-end with representative inputs
- [ ] Latency profiled at target batch size (p50, p95, p99)
- [ ] Memory footprint measured (model size + inference peak)
- [ ] Failure modes documented: what happens with malformed input?
- [ ] Graceful degradation: what's the fallback if model is unavailable?
- [ ] Monitoring configured: latency, throughput, error rate, drift detection
- [ ] Rollback plan tested and documented
- [ ] On-call runbook written

## CI/CD Pipeline Standards

### Minimum Pipeline (Level 2)
```
PR opened
  CI checks (2-5 min)
    Lint (ruff, black --check)
    Type check (mypy)
    Unit tests (pytest)
    Smoke test (1 training step, 1 inference call)

Merge to main
  Integration pipeline (30-90 min)
    Full test suite
    Short training run (CI config: small dataset, few epochs)
    Eval against baseline (must not regress)
    Build + push Docker image

Tag release
  Deployment pipeline
    Deploy to staging
    Smoke test staging
    Manual approval gate
    Deploy to production + health check
```

## Reference Files

- `references/reproducibility-checklist.md` — complete pre-experiment and pre-deployment checklists
- `references/tracking-patterns.md` — W&B and MLflow implementation patterns and code templates

## Metadata
- **Skill ID**: `tkm-mlops-standards`
- **Version**: 1.1.0
- **Author**: TechKnowmad AI <admin@techknowmad.ai>
- **License**: MIT
- **Last Updated**: 2026-03-15
- **Compatible With**: Claude Code CLI, Cowork, VS Code, JetBrains, Cursor

## Error Handling
When any step in this skill fails:
1. **Retry once** with adjusted parameters
2. **Graceful degradation**: Skip the failing step if non-critical, continue with available data
3. **Log the failure**: Record step name, error message, timestamp, and context
4. **Escalate if critical**: Present options to the user
5. **Never fail silently**: Always inform the user what succeeded, what failed, and why

## Changelog
### v1.1.0 (2026-03-15)
- Added standard sections: Role, Trigger Conditions, Error Handling, Metadata
- Structural alignment with ecosystem standards

### v1.0.0 (2026-03-12)
- Initial release
