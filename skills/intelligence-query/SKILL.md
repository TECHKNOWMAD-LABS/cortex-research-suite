# intelligence-query

## Purpose
Multi-source intelligence analysis engine. Takes a query topic, decomposes it into sub-queries, collects evidence from multiple sources (demo mode: synthetic), and synthesizes an intelligence report.

## BettaFish Engine Type
`multi_source_analysis`

## Phase
Phase 14 — BettaFish-inspired intelligence skills

## Architecture
- **QueryDecomposer**: Breaks a complex topic into targeted sub-queries for parallel investigation.
- **SourceCollector**: Gathers evidence from multiple sources. In demo mode, generates synthetic source data.
- **IntelligenceSynthesizer**: Merges findings across sub-queries and sources into a coherent intelligence report with confidence scoring.

## CLI Usage
```bash
python scripts/query_engine.py --topic "topic string" --sources demo --output results.json --format json
```

## Input
- `--topic`: The intelligence query topic (string, required).
- `--sources`: Source mode. Currently supports `demo` for synthetic data.
- `--output`: Output file path for the JSON report.
- `--format`: Output format (`json`).

## Output Schema (JSON)
```json
{
  "query": "original topic",
  "sub_queries": ["sub-query 1", "sub-query 2"],
  "sources": ["source_id_1", "source_id_2"],
  "findings": [{"sub_query": "...", "source": "...", "evidence": "...", "relevance": 0.0}],
  "synthesis": "synthesized intelligence narrative",
  "confidence_level": 0.0,
  "timestamp": "ISO-8601"
}
```

## Security
- All user input truncated to 50,000 characters before processing.
- HTML content stripped before analysis (stdlib only).
- JSON output validated against expected schema before returning.
- No `pickle`, `eval()`, or `exec()` anywhere.
