"""Web intelligence: extract, crawl, and stealth-scrape web pages via Scrapling.

Provides three modes of operation:
  - extract: Single URL to structured JSON with text, metadata, links.
  - crawl:   Breadth-first crawl from a seed URL with depth/page limits.
  - stealth: JavaScript-rendered extraction using StealthyFetcher.

Usage:
    python web_intel.py --mode extract --url https://example.com
    python web_intel.py --mode crawl --url https://example.com --max-pages 10 --max-depth 2
    python web_intel.py --mode stealth --url https://example.com --output result.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

try:
    from scrapling import Fetcher  # type: ignore[import-untyped]

    SCRAPLING_FETCHER_AVAILABLE = True
except ImportError:
    SCRAPLING_FETCHER_AVAILABLE = False

try:
    from scrapling import StealthyFetcher  # type: ignore[import-untyped]

    SCRAPLING_STEALTH_AVAILABLE = True
except ImportError:
    SCRAPLING_STEALTH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = "cortex-research-suite/1.3.0"
DEFAULT_TIMEOUT = 15
MAX_PAGE_SIZE = 50 * 1024  # 50KB
MAX_PAGES_DEFAULT = 10
MAX_DEPTH_DEFAULT = 2
RATE_LIMIT_SECONDS = 1.0

# Language detection heuristics — common words per language
_LANG_HINTS: dict[str, list[str]] = {
    "en": ["the", "and", "is", "in", "to", "of", "a", "for", "that", "it"],
    "es": ["el", "de", "en", "y", "la", "los", "del", "que", "un", "por"],
    "fr": ["le", "de", "et", "la", "les", "des", "en", "un", "du", "est"],
    "de": ["der", "die", "und", "in", "den", "von", "zu", "das", "mit", "ist"],
    "pt": ["de", "que", "em", "um", "para", "com", "uma", "os", "no", "da"],
}

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


def _validate_url(url: str) -> bool:
    """Validate that a URL uses http or https scheme."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _strip_tags(html: str, tags: list[str]) -> str:
    """Remove specified HTML tags and their content."""
    for tag in tags:
        pattern = re.compile(rf"<{tag}[^>]*>.*?</{tag}>", re.DOTALL | re.IGNORECASE)
        html = pattern.sub("", html)
    return html


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text by stripping tags.

    Removes script and style blocks first, then strips all remaining tags.
    """
    # Remove script and style content
    text = _strip_tags(html, ["script", "style", "noscript"])
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _detect_language(text: str) -> str:
    """Detect language from text using simple word frequency heuristic.

    Returns ISO 639-1 code or 'unknown'.
    """
    words = text.lower().split()[:200]
    word_set = set(words)

    best_lang = "unknown"
    best_score = 0
    for lang, common_words in _LANG_HINTS.items():
        score = sum(1 for w in common_words if w in word_set)
        if score > best_score:
            best_score = score
            best_lang = lang

    return best_lang if best_score >= 3 else "unknown"


def _extract_metadata(page: Any) -> dict[str, str]:
    """Extract metadata from HTML meta tags."""
    metadata: dict[str, str] = {}
    try:
        meta_tags = page.find_all("meta")
        for meta in meta_tags:
            name = meta.get("name", "") or meta.get("property", "")
            content = meta.get("content", "")
            if name and content:
                metadata[name.lower()] = content[:500]
    except Exception:
        pass
    return metadata


def _extract_links(page: Any, base_url: str) -> list[str]:
    """Extract and resolve all href links from page."""
    links: list[str] = []
    try:
        for anchor in page.find_all("a"):
            href = anchor.get("href", "")
            if href and not href.startswith(("#", "javascript:", "mailto:")):
                resolved = urljoin(base_url, href)
                if _validate_url(resolved):
                    links.append(resolved)
    except Exception:
        pass
    return links


def _count_images(page: Any) -> int:
    """Count img tags in the page."""
    try:
        return len(page.find_all("img"))
    except Exception:
        return 0


def _check_robots(url: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Check if the URL is allowed by robots.txt.

    Returns True if allowed or if robots.txt cannot be fetched.
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        # If we can't fetch robots.txt, assume allowed
        return True


# ---------------------------------------------------------------------------
# Extract mode
# ---------------------------------------------------------------------------


def extract_page(url: str, fetcher: Any, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Extract structured data from a single URL.

    Args:
        url: Target URL (must be http/https).
        fetcher: Scrapling Fetcher or StealthyFetcher instance.
        timeout: Request timeout in seconds.

    Returns:
        Dict with keys: url, title, body_text, metadata, links, images_count,
        word_count, language_hint, extracted_at.
    """
    _rate_limit()
    try:
        response = fetcher.get(url, timeout=timeout)
    except Exception as exc:
        return {
            "url": url,
            "error": f"Fetch failed: {exc}",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

    html = response.text[:MAX_PAGE_SIZE] if hasattr(response, "text") else ""
    page = response

    # Title
    title = ""
    try:
        title_el = page.find("title")
        if title_el:
            title = title_el.text.strip()[:500]
    except Exception:
        pass

    # Body text
    body_text = _html_to_text(html)

    # Metadata
    metadata = _extract_metadata(page)

    # Links
    links = _extract_links(page, url)

    # Images
    images_count = _count_images(page)

    # Word count
    word_count = len(body_text.split())

    # Language hint
    language_hint = _detect_language(body_text)

    return {
        "url": url,
        "title": title,
        "body_text": body_text[:MAX_PAGE_SIZE],
        "metadata": metadata,
        "links": links,
        "images_count": images_count,
        "word_count": word_count,
        "language_hint": language_hint,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Crawl mode
# ---------------------------------------------------------------------------


def crawl_pages(
    seed_url: str,
    fetcher: Any,
    max_pages: int = MAX_PAGES_DEFAULT,
    max_depth: int = MAX_DEPTH_DEFAULT,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]]:
    """Breadth-first crawl from a seed URL.

    Respects robots.txt for each URL. Stays within the same domain.

    Args:
        seed_url: Starting URL.
        fetcher: Scrapling Fetcher instance.
        max_pages: Maximum pages to crawl.
        max_depth: Maximum link depth from seed.
        timeout: Request timeout per page.

    Returns:
        List of extracted page dicts.
    """
    parsed_seed = urlparse(seed_url)
    seed_domain = parsed_seed.netloc

    visited: set[str] = set()
    results: list[dict[str, Any]] = []

    # BFS queue: (url, depth)
    queue: list[tuple[str, int]] = [(seed_url, 0)]

    while queue and len(results) < max_pages:
        url, depth = queue.pop(0)

        # Normalize URL
        normalized = url.split("#")[0].rstrip("/")
        if normalized in visited:
            continue
        visited.add(normalized)

        # Domain check
        parsed = urlparse(url)
        if parsed.netloc != seed_domain:
            continue

        # Robots check
        if not _check_robots(url, timeout):
            print(f"  Blocked by robots.txt: {url}", file=sys.stderr)
            continue

        print(f"  Crawling (depth={depth}): {url}", file=sys.stderr)
        page_data = extract_page(url, fetcher, timeout)
        page_data["crawl_depth"] = depth
        results.append(page_data)

        # Enqueue child links if within depth
        if depth < max_depth and "links" in page_data:
            for link in page_data["links"]:
                link_normalized = link.split("#")[0].rstrip("/")
                if link_normalized not in visited:
                    link_parsed = urlparse(link)
                    if link_parsed.netloc == seed_domain:
                        queue.append((link, depth + 1))

    return results


# ---------------------------------------------------------------------------
# Stealth mode
# ---------------------------------------------------------------------------


def stealth_extract(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Extract page content using StealthyFetcher for JS-rendered pages.

    Args:
        url: Target URL.
        timeout: Request timeout in seconds.

    Returns:
        Extracted page dict, same schema as extract_page.
    """
    if not SCRAPLING_STEALTH_AVAILABLE:
        return {
            "url": url,
            "error": "StealthyFetcher not available. Install scrapling with browser support.",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

    fetcher = StealthyFetcher(auto_match=False)
    return extract_page(url, fetcher, timeout)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Public convenience API (used by tests and external callers)
# ---------------------------------------------------------------------------

SCRAPLING_AVAILABLE: bool = SCRAPLING_FETCHER_AVAILABLE


def validate_url(url: str) -> bool:
    """Public URL validation — delegates to _validate_url.

    Args:
        url: The URL string to validate.

    Returns:
        True if the URL is valid and uses http/https.
    """
    return _validate_url(url)


def sanitize_body(html: str) -> str:
    """Public HTML sanitization — delegates to _html_to_text.

    Strips script/style tags and their content, removes remaining HTML tags,
    and normalises whitespace.

    Args:
        html: Raw HTML string.

    Returns:
        Cleaned plain text.
    """
    return _html_to_text(html)


def analyse_url(url: str) -> dict[str, Any]:
    """Analyse a web page and return structured intelligence.

    Uses stdlib urllib when scrapling is unavailable.

    Args:
        url: The URL to analyse.

    Returns:
        Dictionary with url, title, body_text, links, sentiment, word_count.
    """
    if not _validate_url(url):
        return {
            "url": url,
            "title": "",
            "body_text": "",
            "links": [],
            "sentiment": 0.0,
            "word_count": 0,
            "error": "Invalid URL",
        }

    return _fetch_and_parse(url)


def _fetch_and_parse(url: str) -> dict[str, Any]:
    """Fetch a URL via stdlib and parse the page content.

    Args:
        url: The URL to fetch.

    Returns:
        Dictionary with url, title, body_text, links, sentiment, word_count.
    """
    import urllib.error
    import urllib.request

    result: dict[str, Any] = {
        "url": url,
        "title": "",
        "body_text": "",
        "links": [],
        "sentiment": 0.0,
        "word_count": 0,
    }

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return result

    # Title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    if title_match:
        result["title"] = title_match.group(1).strip()

    body_text = _html_to_text(html)
    result["body_text"] = body_text
    result["word_count"] = len(body_text.split()) if body_text else 0

    links = re.findall(r'href="(https?://[^"]+)"', html)
    result["links"] = list(set(links))

    return result


def main() -> int:
    """CLI entry point for web intelligence."""
    if not SCRAPLING_FETCHER_AVAILABLE:
        print(
            "ERROR: scrapling is not installed. Install with: pip install scrapling",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(description="Web intelligence: extract, crawl, or stealth-scrape web pages")
    parser.add_argument("--mode", choices=["extract", "crawl", "stealth"], required=True, help="Operation mode")
    parser.add_argument("--url", required=True, help="Target URL (http/https)")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES_DEFAULT, help="Max pages for crawl mode")
    parser.add_argument("--max-depth", type=int, default=MAX_DEPTH_DEFAULT, help="Max depth for crawl mode")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--format", choices=["json", "jsonl"], default="json", help="Output format")
    args = parser.parse_args()

    # Validate URL
    if not _validate_url(args.url):
        print(f"ERROR: Invalid URL (must be http/https): {args.url}", file=sys.stderr)
        return 1

    # Execute mode
    if args.mode == "extract":
        fetcher = Fetcher(auto_match=False)
        result = extract_page(args.url, fetcher, args.timeout)
        results = [result]
    elif args.mode == "crawl":
        fetcher = Fetcher(auto_match=False)
        results = crawl_pages(args.url, fetcher, args.max_pages, args.max_depth, args.timeout)
        result = {
            "seed_url": args.url,
            "pages_crawled": len(results),
            "max_pages": args.max_pages,
            "max_depth": args.max_depth,
            "pages": results,
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }
    elif args.mode == "stealth":
        result = stealth_extract(args.url, args.timeout)
        results = [result]
    else:
        print(f"ERROR: Unknown mode: {args.mode}", file=sys.stderr)
        return 1

    # Format output
    if args.mode == "crawl" and args.format == "jsonl":
        output_text = "\n".join(json.dumps(page) for page in results) + "\n"
    elif args.format == "jsonl":
        output_text = json.dumps(result) + "\n"
    else:
        output_text = json.dumps(result, indent=2) + "\n"

    # Write output
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_text)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
