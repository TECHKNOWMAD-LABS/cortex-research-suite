# Legal notes — trilogy integration

Cortex Research Suite (MIT License) includes skills inspired by the
architectural patterns of the following projects. No code has been
copied from any of these repositories. All Cortex skills are
independent implementations.

| Project | License | Integration type |
|---------|---------|-----------------|
| MindSpider (666ghj) | Non-Commercial Learning License 1.1 + MIT dual | Connector to external deployment |
| BettaFish (666ghj) | GPL-2.0 + Non-Commercial Learning License 1.1 | Architectural pattern inspiration |
| MiroFish (666ghj) | AGPL-3.0 | Architectural pattern inspiration |

All three projects use copyleft or non-commercial licenses.
Cortex skills contain zero derived code. The "inspired by"
relationship is limited to publicly documented architectural
patterns (engine separation, reflection loops, swarm simulation).
These are general software design patterns, not copyrightable
expression.

Specifically:
- **MindSpider connector**: Connects to a user's own MindSpider deployment
  via standard MySQL queries. No MindSpider code is bundled or redistributed.
  The connector produces Cortex-native data structures.
- **BettaFish-inspired skills**: The multi-source analysis pattern (query
  decomposition, parallel source collection, synthesis) is a standard
  intelligence analysis methodology. No BettaFish code was referenced.
- **MiroFish-inspired simulator**: Agent-based simulation with counterfactual
  injection is a well-established technique in computational social science.
  No MiroFish code was referenced.

Verified: 2026-03-16
Verified by: Claude Code automated license check
