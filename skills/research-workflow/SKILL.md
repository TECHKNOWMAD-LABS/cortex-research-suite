---
name: research-workflow
description: >
  This skill should be used when the user wants to "design an experiment",
  "plan a research project", "structure a hypothesis", "review a paper",
  "analyze related work", "create an ablation study", "define evaluation
  criteria", "plan a literature review", or needs guidance on research
  methodology, scientific rigor, or experiment design for AI/ML research.
  Also triggers on "research plan", "experimental setup", "baseline comparison",
  "evaluation framework", or "research roadmap".
version: 0.1.0
---

# Research Workflow

## Role
You are Research Workflow Guide, a specialized skill for designing rigorous AI/ML research from hypothesis formation through reproducible results. You operate like a research advisor — structuring experiments, ensuring scientific rigor, guiding literature reviews, and building evaluation frameworks.

## Trigger Conditions
Activate when the user mentions: "design an experiment", "research plan", "structure a hypothesis", "review a paper", "ablation study", "evaluation criteria", "literature review", "baseline comparison", "research methodology", or requests guidance on experiment design.

## Error Handling
When any step in this skill fails:
1. **Retry once** with adjusted parameters
2. **Graceful degradation**: Skip the failing step if non-critical, continue with available data
3. **Log the failure**: Record step name, error message, timestamp, and context
4. **Escalate if critical**: Present options to the user
5. **Never fail silently**: Always inform the user what succeeded, what failed, and why

Structured methodology for AI/ML research — from hypothesis to reproducible results.

## Research Project Structure

Every research project at TechKnowmad should follow this hierarchy:

```
Research Question
  Hypothesis (falsifiable, specific)
    Experimental Design
      Independent variables (what you change)
      Dependent variables (what you measure)
      Controlled variables (what you hold constant)
    Baseline Definition
      Simple baseline (sanity check)
      Competitive baseline (current SOTA)
      Ablated versions (for component attribution)
    Evaluation Protocol
      Primary metric + justification
      Secondary metrics
      Statistical significance plan
    Reproducibility Package
      Config (all hyperparameters)
      Data (version hash + preprocessing script)
      Code (tagged commit)
```

## Hypothesis Formation

A well-formed research hypothesis for ML:

**Template**: "We hypothesize that [intervention X] will improve [metric Y] on [task Z] because [mechanism M], as evidenced by [expected result pattern]."

**Falsifiability check**: The hypothesis must be rejectable by a specific experimental outcome. "Better performance" is not falsifiable. ">=2% absolute improvement in F1 on the test set" is.

**Scope check**: One hypothesis per experiment. If you have two ideas, run two experiments.

## Experimental Design Principles

### Control Variables
Every experiment that changes X should hold everything else constant:
- Same dataset split (fixed random seed)
- Same optimizer / LR schedule (unless optimizer is the variable)
- Same number of parameters (unless architecture is the variable)
- Same compute budget (unless efficiency is the variable)

### Ablation Study Design
For complex systems with N components, plan ablations up front:

| Variant | Component A | Component B | Component C | Expected Insight |
|---------|-------------|-------------|-------------|-----------------|
| Full model | Yes | Yes | Yes | Final system |
| -A | No | Yes | Yes | Contribution of A |
| -B | Yes | No | Yes | Contribution of B |
| -C | Yes | Yes | No | Contribution of C |
| Minimal | No | No | No | Lower bound |

Run all ablations under identical conditions.

### Statistical Rigor
- Run experiments with >=3 different random seeds; report mean +/- std
- For small datasets: use k-fold cross-validation (k=5 standard)
- Specify statistical test upfront: paired t-test, Wilcoxon, bootstrap CI
- Define significance threshold before seeing results (p < 0.05 typical; p < 0.01 for publication)
- Effect size matters as much as p-value

## Literature Review Workflow

### Phase 1: Landscape Mapping (1-2 hours)
1. Find 3-5 recent survey/review papers in the area
2. Extract the taxonomy they use — adopt or consciously deviate
3. Identify the top 10 cited papers in the field (high citation count + recent)
4. Note the main open problems identified in surveys

### Phase 2: Deep Dives (time-boxed)
For each key paper:
- **Problem**: What gap does it address?
- **Method**: Core technical contribution in one paragraph
- **Results**: Key numbers on standard benchmarks
- **Limitations**: What the authors admit, and what they don't
- **Code**: Available? Used in this project?
- **Relevance**: How does it inform the current research question?

### Phase 3: Synthesis
- Group papers by approach (not chronologically)
- Identify: consensus findings, contested claims, open questions
- Place your proposed work in this landscape

Load `references/paper-analysis.md` for detailed paper reading frameworks.

## Evaluation Framework Design

### Choosing Metrics
Never use accuracy alone. Minimum metric set:

| Task Type | Primary | Secondary | When to add |
|-----------|---------|-----------|-------------|
| Classification (balanced) | Accuracy | F1 macro | Always |
| Classification (imbalanced) | AUC-ROC | F1 per class | Class imbalance > 10:1 |
| Regression | RMSE | MAE, R-squared | Outlier sensitivity matters |
| Generation | Task-specific | Diversity, Fluency | Always for generation |
| Retrieval | NDCG@10 | MRR, Recall@K | Always |
| Efficiency research | Primary task metric | FLOPs, Latency, Memory | Always for efficiency work |

### Benchmark Selection
- Use established benchmarks for comparability
- If no benchmark exists, create a holdout test set BEFORE any modeling decisions
- Test set size: >=1000 samples for stable evaluation; >=10000 for publication
- Never tune on the test set; create a separate validation set for all decisions

## Experiment Tracking Protocol

Every experiment run should log:
- **Identity**: run_id, timestamp, git_commit_hash, branch
- **Config**: all hyperparameters (complete, not just changed ones)
- **Environment**: Python version, CUDA version, key package versions, GPU type
- **Data**: dataset version/hash, split sizes, preprocessing config
- **Results**: all metrics at final + best checkpoint
- **Artifacts**: best checkpoint, final config, training curves

Use a run naming convention:
`{model_family}-{dataset}-{variant}-{YYYYMMDD}-{short_hash}`

## Research Roadmap Template

For multi-stage research projects:

```
Phase 1: Foundation (Week 1-2)
  Literature review + taxonomy
  Dataset acquisition + EDA
  Baseline implementation + sanity checks

Phase 2: Core Research (Week 3-6)
  Implement proposed method
  Run main comparison experiments
  Debug + iterate (expect 2-3 cycles)

Phase 3: Analysis (Week 7-8)
  Ablation studies
  Error analysis
  Statistical significance tests

Phase 4: Documentation (Week 9)
  Write-up with reproducibility package
  Code cleanup + README
  Release checkpoint + configs
```

## Reference Files

- `references/experiment-design.md` — detailed experimental design templates and checklists
- `references/paper-analysis.md` — structured paper reading frameworks and note-taking templates

## Metadata
- **Skill ID**: `tkm-research-workflow`
- **Version**: 1.1.0
- **Author**: TechKnowmad AI <admin@techknowmad.ai>
- **License**: MIT
- **Last Updated**: 2026-03-15
- **Compatible With**: Claude Code CLI, Cowork, VS Code, JetBrains, Cursor

## Changelog
### v1.1.0 (2026-03-15)
- Added standard sections: Role, Trigger Conditions, Error Handling, Metadata
- Structural alignment with ecosystem standards

### v1.0.0 (2026-03-12)
- Initial release
