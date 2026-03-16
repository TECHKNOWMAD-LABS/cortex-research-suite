# mindspider-connector

## Overview

Connects Cortex Research Suite to a MindSpider social listening deployment. Pulls trending topics, sentiment scores, and sample posts from the MindSpider database and transforms them into Cortex-native evidence structures for the research pipeline.

## Core instruction

You are a data connector agent. Your job is to:

1. Connect to a MindSpider MySQL database (or use demo mode for synthetic data)
2. Extract today's trending topics with sentiment scores and post counts
3. Transform raw social data into structured evidence items
4. Output Cortex-native JSON suitable for research_pipeline.py consumption

## Input

- `--source demo` — Generate synthetic demo data (no database required)
- `--source mysql` — Connect to live MindSpider deployment via MINDSPIDER_DB_URL env var
- `--domain <keyword>` — Filter topics by domain keyword
- `--output <path>` — Write results to file (default: stdout)
- `--format json|jsonl` — Output format

## Output schema

```json
{
  "source": "mindspider",
  "extraction_timestamp": "2026-03-16T10:00:00Z",
  "topics": [
    {
      "topic": "string — topic title",
      "sentiment_score": "float — -1.0 to 1.0",
      "post_count": "int — number of posts",
      "trend_direction": "string — rising|stable|declining",
      "sample_posts": ["string — up to 3 excerpt strings"],
      "platforms": ["string — platform names"],
      "first_seen": "string — ISO datetime",
      "peak_time": "string — ISO datetime"
    }
  ],
  "metadata": {
    "total_topics": "int",
    "time_range_hours": 24,
    "source_mode": "demo|mysql"
  }
}
```

## Data handling

- Demo mode generates synthetic data with no external connections
- Live mode connects only to the user's own MindSpider deployment
- No PII is retained beyond the sample_posts field (limited to 3 excerpts per topic)
- today_topics.json is overwritten on each run — no historical accumulation
- See datasets/mindspider/DATA_NOTICE.md for full data handling policy

## Common gotchas

- MINDSPIDER_DB_URL must be set for live mode; without it, the connector falls back to demo
- MySQL connection timeout is 10 seconds; query timeout is 30 seconds
- SQL queries use parameterized placeholders — never string concatenation
- sample_posts are truncated to 280 characters each
