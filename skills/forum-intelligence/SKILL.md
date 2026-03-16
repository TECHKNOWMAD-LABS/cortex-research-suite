# forum-intelligence

## Purpose
Forum thread analysis with coordination detection. Analyzes discussion threads for sentiment, key arguments, coordination patterns, and minority viewpoints.

## BettaFish Engine Type
`forum_analysis`

## Phase
Phase 14 — BettaFish-inspired intelligence skills

## Architecture
- **ThreadParser**: Parses and normalizes forum thread data, strips HTML, and validates structure.
- **CoordinationDetector**: Detects potential coordination patterns among posters (timing, language similarity, posting frequency).
- **ViewpointExtractor**: Identifies key arguments, majority/minority viewpoints, and sentiment distribution.

## CLI Usage
```bash
python scripts/forum_analyzer.py --input threads.json --output results.json --format json
```

## Input
- `--input`: Path to JSON file with structure:
```json
{
  "threads": [
    {
      "title": "Thread title",
      "posts": [
        {"author": "user1", "content": "Post content", "timestamp": "ISO-8601"}
      ]
    }
  ]
}
```

## Output Schema (JSON)
```json
{
  "thread_summaries": [{"title": "...", "post_count": 0, "summary": "..."}],
  "sentiment_distribution": {"positive": 0.0, "negative": 0.0, "neutral": 0.0},
  "key_arguments": ["..."],
  "coordination_detected": false,
  "coordination_evidence": [],
  "minority_viewpoints": ["..."],
  "metadata": {"total_threads": 0, "total_posts": 0, "unique_authors": 0, "timestamp": "ISO-8601"}
}
```

## Security
- All user input truncated to 50,000 characters before processing.
- HTML content stripped before analysis (stdlib only).
- JSON output validated against expected schema before returning.
- No `pickle`, `eval()`, or `exec()` anywhere.
