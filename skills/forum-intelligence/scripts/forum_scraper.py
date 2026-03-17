"""Forum scraper: live Reddit and HackerNews comment scraping via Scrapling.

Scrapes forum posts and comments from Reddit JSON API and HackerNews API.
Returns structured post data with author, text, timestamp, URL, score, and platform.

Usage:
    python forum_scraper.py --subreddit worldnews --output posts.json
    python forum_scraper.py --url https://www.reddit.com/r/technology/comments/abc123/title/ --output thread.json
    python forum_scraper.py --url https://news.ycombinator.com/item?id=12345 --output comments.json
"""

from __future__ import annotations

import argparse
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
MAX_POSTS = 100

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

_last_request_time: float = 0.0


def _rate_limit() -> None:
    """Enforce 1 request per second rate limit."""
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    _last_request_time = time.monotonic()


# ---------------------------------------------------------------------------
# Reddit scraper
# ---------------------------------------------------------------------------


def scrape_reddit_subreddit(
    fetcher: Any,
    subreddit: str,
    query: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Scrape posts from a Reddit subreddit via JSON API.

    Args:
        fetcher: Scrapling Fetcher instance.
        subreddit: Subreddit name (without r/ prefix).
        query: Optional search query to filter posts.
        limit: Maximum number of posts to fetch.

    Returns:
        List of post dicts with keys: author, text, timestamp, url, score, platform.
    """
    posts: list[dict[str, Any]] = []

    if query:
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&restrict_sr=1&limit={limit}"
    else:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"

    _rate_limit()
    try:
        response = fetcher.get(url, timeout=REQUEST_TIMEOUT)
        data = json.loads(response.text)
    except Exception as exc:
        print(f"WARN: Reddit r/{subreddit} fetch failed: {exc}", file=sys.stderr)
        return posts

    children = data.get("data", {}).get("children", [])
    for child in children[:limit]:
        post_data = child.get("data", {})
        created_utc = post_data.get("created_utc", 0)
        timestamp = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat() if created_utc else ""

        text = post_data.get("selftext", "") or post_data.get("title", "")
        permalink = post_data.get("permalink", "")

        posts.append(
            {
                "author": str(post_data.get("author", "[deleted]"))[:100],
                "text": text[:5000],
                "timestamp": timestamp,
                "url": f"https://www.reddit.com{permalink}" if permalink else "",
                "score": int(post_data.get("score", 0)),
                "platform": "reddit",
            }
        )

    return posts


def scrape_reddit_thread(fetcher: Any, thread_url: str) -> list[dict[str, Any]]:
    """Scrape comments from a specific Reddit thread.

    Args:
        fetcher: Scrapling Fetcher instance.
        thread_url: Full URL to a Reddit thread.

    Returns:
        List of comment dicts.
    """
    posts: list[dict[str, Any]] = []

    # Ensure .json suffix
    json_url = thread_url.rstrip("/") + ".json"

    _rate_limit()
    try:
        response = fetcher.get(json_url, timeout=REQUEST_TIMEOUT)
        data = json.loads(response.text)
    except Exception as exc:
        print(f"WARN: Reddit thread fetch failed: {exc}", file=sys.stderr)
        return posts

    if not isinstance(data, list) or len(data) < 2:
        return posts

    def _extract_comments(children: list[dict], depth: int = 0) -> None:
        """Recursively extract comments from Reddit JSON tree."""
        for child in children:
            if depth > 5 or len(posts) >= MAX_POSTS:
                return
            comment = child.get("data", {})
            body = comment.get("body", "")
            if not body or body == "[deleted]":
                continue

            created_utc = comment.get("created_utc", 0)
            timestamp = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat() if created_utc else ""

            posts.append(
                {
                    "author": str(comment.get("author", "[deleted]"))[:100],
                    "text": body[:5000],
                    "timestamp": timestamp,
                    "url": thread_url,
                    "score": int(comment.get("score", 0)),
                    "platform": "reddit",
                }
            )

            # Recurse into replies
            replies = comment.get("replies", "")
            if isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                _extract_comments(reply_children, depth + 1)

    comments_listing = data[1].get("data", {}).get("children", [])
    _extract_comments(comments_listing)

    return posts


# ---------------------------------------------------------------------------
# HackerNews scraper
# ---------------------------------------------------------------------------


def scrape_hackernews_comments(fetcher: Any, story_id: int) -> list[dict[str, Any]]:
    """Scrape comments from a HackerNews story.

    Args:
        fetcher: Scrapling Fetcher instance.
        story_id: HackerNews story ID.

    Returns:
        List of comment dicts.
    """
    posts: list[dict[str, Any]] = []

    # Fetch story to get comment IDs
    _rate_limit()
    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    try:
        response = fetcher.get(story_url, timeout=REQUEST_TIMEOUT)
        story = json.loads(response.text)
    except Exception as exc:
        print(f"WARN: HN story {story_id} fetch failed: {exc}", file=sys.stderr)
        return posts

    kids = story.get("kids", [])

    for comment_id in kids[:MAX_POSTS]:
        _rate_limit()
        comment_url = f"https://hacker-news.firebaseio.com/v0/item/{comment_id}.json"
        try:
            response = fetcher.get(comment_url, timeout=REQUEST_TIMEOUT)
            comment = json.loads(response.text)
        except Exception as exc:
            print(f"WARN: HN comment {comment_id} fetch failed: {exc}", file=sys.stderr)
            continue

        if not comment or comment.get("deleted") or comment.get("dead"):
            continue

        text = comment.get("text", "")
        timestamp = comment.get("time", 0)
        ts_iso = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat() if timestamp else ""

        posts.append(
            {
                "author": str(comment.get("by", "anonymous"))[:100],
                "text": text[:5000],
                "timestamp": ts_iso,
                "url": f"https://news.ycombinator.com/item?id={comment_id}",
                "score": 0,  # HN comments don't expose scores publicly
                "platform": "hackernews",
            }
        )

    return posts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for forum scraper."""
    if not SCRAPLING_AVAILABLE:
        print("ERROR: scrapling not installed. Install with: pip install scrapling", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="Forum scraper: Reddit and HackerNews")
    parser.add_argument("--url", default=None, help="Thread URL (Reddit or HN)")
    parser.add_argument("--subreddit", default=None, help="Subreddit name (without r/)")
    parser.add_argument("--query", default=None, help="Search query (for subreddit mode)")
    parser.add_argument("--output", default=None, help="Output file path (JSON)")
    args = parser.parse_args()

    if not args.url and not args.subreddit:
        print("ERROR: Provide either --url or --subreddit", file=sys.stderr)
        return 1

    fetcher = Fetcher(auto_match=False)
    posts: list[dict[str, Any]] = []

    if args.url:
        if "reddit.com" in args.url:
            posts = scrape_reddit_thread(fetcher, args.url)
        elif "ycombinator.com" in args.url or "news.ycombinator" in args.url:
            # Extract story ID from URL
            import re

            match = re.search(r"id=(\d+)", args.url)
            if match:
                story_id = int(match.group(1))
                posts = scrape_hackernews_comments(fetcher, story_id)
            else:
                print(f"ERROR: Could not extract story ID from URL: {args.url}", file=sys.stderr)
                return 1
        else:
            print(f"ERROR: Unsupported URL platform: {args.url}", file=sys.stderr)
            return 1
    elif args.subreddit:
        posts = scrape_reddit_subreddit(fetcher, args.subreddit, query=args.query)

    output_text = json.dumps(posts, indent=2) + "\n"

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_text)
        print(f"Written {len(posts)} posts to {args.output}", file=sys.stderr)
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
