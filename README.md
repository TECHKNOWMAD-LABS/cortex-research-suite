# ⚠️ This repository has been deprecated

**cortex-research-suite has been decomposed into 20 focused repositories under the [TECHKNOWMAD-LABS](https://github.com/TECHKNOWMAD-LABS) organization.**

Each component now has its own repo with dedicated CI, tests, documentation, and release cycle. This architecture enables independent evolution and cleaner dependency management.

## Migration guide

| Old (cortex-research-suite) | New repository | Description |
|---|---|---|
| `skill-organism/` | [pep-spec](https://github.com/TECHKNOWMAD-LABS/pep-spec) | Phyloid Evolution Protocol — 7 formal specs |
| `skill-organism/engine` | [phyloid-engine](https://github.com/TECHKNOWMAD-LABS/phyloid-engine) | PEP-003 conforming evolution engine |
| `skills/de-slop` | [idea-killer](https://github.com/TECHKNOWMAD-LABS/idea-killer) | 7-lens adversarial startup analysis |
| `skills/security-audit` | [red-team-kit](https://github.com/TECHKNOWMAD-LABS/red-team-kit) | 52-hypothesis adversarial council |
| `skills/github-mcp` | [techknowmad-mcp](https://github.com/TECHKNOWMAD-LABS/techknowmad-mcp) | 8 MCP servers |
| `cortex/agents` | [agent-sim](https://github.com/TECHKNOWMAD-LABS/agent-sim) | Multi-agent simulation |
| `cortex/evaluation` | [ground-truth](https://github.com/TECHKNOWMAD-LABS/ground-truth) | Claim verification engine |
| `cortex/telemetry` | [trace-agent](https://github.com/TECHKNOWMAD-LABS/trace-agent) | OpenTelemetry agent observability |
| `knowledge/` | [graph-forge](https://github.com/TECHKNOWMAD-LABS/graph-forge) | Knowledge graph with Neo4j |
| `dashboards/petri-dish.html` | [phyloid](https://github.com/TECHKNOWMAD-LABS/phyloid) | 3D WebGL evolution simulator |
| Infrastructure | [infrastructure](https://github.com/TECHKNOWMAD-LABS/infrastructure) | Terraform, Docker, Helm |
| All skills | [founder-arsenal](https://github.com/TECHKNOWMAD-LABS/founder-arsenal) | 8 Claude skills for founders |
| Pitch analysis | [pitch-critic](https://github.com/TECHKNOWMAD-LABS/pitch-critic) | Pitch deck adversarial analysis |

## Full repository list

Visit [github.com/TECHKNOWMAD-LABS](https://github.com/TECHKNOWMAD-LABS) for the complete list of 20 repositories.

## Why the change?

The monorepo approach created coupling between unrelated components. The new architecture follows the Edgecraft Protocol principle: each repository is an independent intelligence unit that evolves on its own schedule while composing into the larger system.

Every new repo is autonomously developed and maintained by the Edgecraft Protocol. See `AGENTS.md` in any repo for the development protocol.

---

*This repository is archived and will receive no further updates.*

**Built by [TechKnowMad Labs](https://techknowmad.ai)**
