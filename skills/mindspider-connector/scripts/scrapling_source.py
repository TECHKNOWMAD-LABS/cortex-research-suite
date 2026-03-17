"""Live web scraping via Scrapling for MindSpider connector.

Scrapes trending topics from Reddit, HackerNews, and Bluesky public APIs.
Falls back gracefully when Scrapling is not installed or endpoints fail.

Usage:
    python -m skills.mindspider-connector.scripts.scrapling_source --domain "AI" --n-topics 10
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scrapling import Fetcher  # type: ignore[import-untyped]

    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = "cortex-research-suite/1.3.0"
REQUEST_TIMEOUT = 10
RATE_LIMIT_SECONDS = 1.0

POSITIVE_WORDS: set[str] = {
    "good",
    "great",
    "excellent",
    "amazing",
    "wonderful",
    "positive",
    "breakthrough",
    "success",
    "improve",
    "improvement",
    "benefit",
    "hope",
    "promising",
    "progress",
    "win",
    "innovative",
    "exciting",
    "impressive",
    "brilliant",
    "optimistic",
    "advance",
    "achieve",
    "celebrate",
    "remarkable",
    "effective",
}

NEGATIVE_WORDS: set[str] = {
    "bad",
    "terrible",
    "awful",
    "horrible",
    "negative",
    "failure",
    "fail",
    "crisis",
    "danger",
    "threat",
    "risk",
    "concern",
    "problem",
    "disaster",
    "conflict",
    "attack",
    "decline",
    "collapse",
    "scandal",
    "corrupt",
    "alarming",
    "devastating",
    "tragic",
    "controversial",
    "exploit",
}

MAX_SAMPLE_POST_LEN = 280

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_last_request_time: float = 0.0


def _rate_limit() -> None:
    """Enforce 1 request per second rate limit."""
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    _last_request_time = time.monotonic()


def _compute_sentiment(text: str) -> float:
    """Compute a simple keyword-based sentiment score in [-1, 1].

    Counts positive vs negative words and normalizes by total matched count.
    Returns 0.0 when no sentiment words are found.
    """
    words = set(text.lower().split())
    pos_count = len(words & POSITIVE_WORDS)
    neg_count = len(words & NEGATIVE_WORDS)
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return round((pos_count - neg_count) / total, 3)


def _infer_trend(score: float) -> str:
    """Infer trend direction from sentiment score magnitude."""
    if abs(score) > 0.3:
        return "rising"
    if abs(score) < 0.1:
        return "declining"
    return "stable"


def _make_topic(
    title: str,
    sentiment: float,
    post_count: int,
    trend: str,
    sample_posts: list[str],
    platforms: list[str],
    first_seen: str,
    peak_time: str,
) -> dict[str, Any]:
    """Build a topic dict matching the canonical MindSpider schema."""
    return {
        "topic": title[:500],
        "sentiment_score": sentiment,
        "post_count": post_count,
        "trend_direction": trend,
        "sample_posts": [p[:MAX_SAMPLE_POST_LEN] for p in sample_posts[:5]],
        "platforms": platforms,
        "first_seen": first_seen,
        "peak_time": peak_time,
    }


# ---------------------------------------------------------------------------
# Source scrapers
# ---------------------------------------------------------------------------


def _scrape_reddit(fetcher: Any, domain: str | None = None) -> list[dict[str, Any]]:
    """Scrape trending topics from Reddit JSON API.

    Fetches from r/worldnews, r/technology, and r/geopolitics.
    """
    subreddits = ["worldnews", "technology", "geopolitics"]
    topics: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for sub in subreddits:
        _rate_limit()
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
        try:
            response = fetcher.get(url, timeout=REQUEST_TIMEOUT)
            data = json.loads(response.text)
        except Exception as exc:
            print(f"WARN: Reddit r/{sub} fetch failed: {exc}", file=sys.stderr)
            continue

        children = data.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data", {})
            title = post.get("title", "")
            if domain and domain.lower() not in title.lower():
                continue

            selftext = post.get("selftext", "")
            combined = f"{title} {selftext}"
            sentiment = _compute_sentiment(combined)
            score = post.get("score", 0)
            num_comments = post.get("num_comments", 0)
            created_utc = post.get("created_utc", now.timestamp())

            first_seen_dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            sample = [title]
            if selftext:
                sample.append(selftext[:MAX_SAMPLE_POST_LEN])

            topics.append(
                _make_topic(
                    title=title,
                    sentiment=sentiment,
                    post_count=score + num_comments,
                    trend=_infer_trend(sentiment),
                    sample_posts=sample,
                    platforms=["reddit"],
                    first_seen=first_seen_dt.isoformat(),
                    peak_time=now.isoformat(),
                )
            )

    return topics


def _scrape_hackernews(fetcher: Any, domain: str | None = None) -> list[dict[str, Any]]:
    """Scrape trending topics from HackerNews Algolia API."""
    topics: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    _rate_limit()
    url = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=15"
    try:
        response = fetcher.get(url, timeout=REQUEST_TIMEOUT)
        data = json.loads(response.text)
    except Exception as exc:
        print(f"WARN: HackerNews fetch failed: {exc}", file=sys.stderr)
        return topics

    hits = data.get("hits", [])
    for hit in hits:
        title = hit.get("title", "")
        if domain and domain.lower() not in title.lower():
            continue

        sentiment = _compute_sentiment(title)
        points = hit.get("points", 0) or 0
        num_comments = hit.get("num_comments", 0) or 0
        created_at = hit.get("created_at", now.isoformat())

        topics.append(
            _make_topic(
                title=title,
                sentiment=sentiment,
                post_count=points + num_comments,
                trend=_infer_trend(sentiment),
                sample_posts=[title],
                platforms=["hackernews"],
                first_seen=created_at if isinstance(created_at, str) else now.isoformat(),
                peak_time=now.isoformat(),
            )
        )

    return topics


def _scrape_bluesky(fetcher: Any, domain: str | None = None) -> list[dict[str, Any]]:
    """Scrape trending topics from Bluesky public API."""
    topics: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    _rate_limit()
    url = "https://public.api.bsky.app/xrpc/app.bsky.unspecced.getPopularFeedGenerators?limit=15"
    try:
        response = fetcher.get(url, timeout=REQUEST_TIMEOUT)
        data = json.loads(response.text)
    except Exception as exc:
        print(f"WARN: Bluesky fetch failed: {exc}", file=sys.stderr)
        return topics

    feeds = data.get("feeds", [])
    for feed in feeds:
        display_name = feed.get("displayName", "")
        description = feed.get("description", "")
        combined = f"{display_name} {description}"

        if domain and domain.lower() not in combined.lower():
            continue

        sentiment = _compute_sentiment(combined)
        like_count = feed.get("likeCount", 0) or 0

        topics.append(
            _make_topic(
                title=display_name or description[:100],
                sentiment=sentiment,
                post_count=like_count,
                trend=_infer_trend(sentiment),
                sample_posts=[description[:MAX_SAMPLE_POST_LEN]] if description else [],
                platforms=["bluesky"],
                first_seen=now.isoformat(),
                peak_time=now.isoformat(),
            )
        )

    return topics


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fetch_live_topics(domain: str | None = None, n_topics: int = 15) -> list[dict[str, Any]]:
    """Scrape live trending topics from Reddit, HackerNews, and Bluesky.

    Args:
        domain: Optional keyword filter. Only topics containing this term are returned.
        n_topics: Maximum number of topics to return (default 15).

    Returns:
        List of topic dicts matching the MindSpider canonical schema:
        - topic (str), sentiment_score (float), post_count (int),
          trend_direction (str), sample_posts (list), platforms (list),
          first_seen (ISO str), peak_time (ISO str).

        Returns an empty list if Scrapling is not installed or all sources fail.
    """
    if not SCRAPLING_AVAILABLE:
        print("WARN: scrapling not installed, returning empty list", file=sys.stderr)
        return []

    fetcher = Fetcher(auto_match=False)

    all_topics: list[dict[str, Any]] = []

    for scraper_fn in (_scrape_reddit, _scrape_hackernews, _scrape_bluesky):
        try:
            results = scraper_fn(fetcher, domain)
            all_topics.extend(results)
        except Exception as exc:
            print(f"WARN: Scraper {scraper_fn.__name__} failed: {exc}", file=sys.stderr)

    if not all_topics:
        return []

    # Deduplicate by topic title (case-insensitive)
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for t in all_topics:
        key = t["topic"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(t)

    # Sort by post_count descending, return top n
    unique.sort(key=lambda t: t["post_count"], reverse=True)
    return unique[:n_topics]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def sentiment_score(text: str) -> float:
    """Public alias for _compute_sentiment.

    Args:
        text: Input text to score.

    Returns:
        Float between -1.0 and 1.0, or 0.0 for empty/neutral text.
    """
    return _compute_sentiment(text)


def validate_url(url: str) -> bool:
    """Validate that a URL uses http or https scheme.

    Args:
        url: The URL string to validate.

    Returns:
        True if the URL is valid and uses http/https.
    """
    if not url:
        return False
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except ValueError:
        return False


def main() -> int:
    """CLI entry point for standalone testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrapling live topic scraper")
    parser.add_argument("--domain", default=None, help="Filter by domain keyword")
    parser.add_argument("--n-topics", type=int, default=15, help="Max topics to return")
    parser.add_argument("--output", default=None, help="Output file path (JSON)")
    args = parser.parse_args()

    topics = fetch_live_topics(domain=args.domain, n_topics=args.n_topics)
    output_text = json.dumps(topics, indent=2) + "\n"

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_text)
        print(f"Written {len(topics)} topics to {args.output}", file=sys.stderr)
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
