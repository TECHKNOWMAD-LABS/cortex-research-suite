"""Academic evidence scraper using Scrapling.

Scrapes Google Scholar, PubMed E-utilities API, and arXiv API to gather
academic evidence for a given research topic.

Usage:
    python -m skills.research-workflow.scripts.evidence_scraper --topic "AI in nephrology" --output evidence.json
"""

from __future__ import annotations

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

try:
    from scrapling import Fetcher  # type: ignore[import-untyped]

    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = "cortex-research-suite/1.3.0"
SCHOLAR_TIMEOUT = 15
API_TIMEOUT = 15
SCHOLAR_RATE_LIMIT = 3.0
API_RATE_LIMIT = 1.0
MAX_PER_SOURCE = 5
MAX_TOTAL = 15
MAX_SNIPPET_LEN = 500

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

_last_request_times: dict[str, float] = {}


def _rate_limit(source: str, delay: float) -> None:
    """Enforce per-source rate limiting."""
    last = _last_request_times.get(source, 0.0)
    elapsed = time.monotonic() - last
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_request_times[source] = time.monotonic()


# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------


def _compute_relevance(title: str, snippet: str, query: str) -> float:
    """Compute a simple relevance score in [0, 1] based on keyword overlap.

    Counts what fraction of the query terms appear in the title or snippet.
    """
    query_terms = set(query.lower().split())
    if not query_terms:
        return 0.0
    combined = f"{title} {snippet}".lower()
    matched = sum(1 for term in query_terms if term in combined)
    return round(matched / len(query_terms), 3)


def _extract_year(text: str) -> int:
    """Extract a 4-digit year from text, defaulting to current year."""
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if match:
        return int(match.group(0))
    return datetime.now(timezone.utc).year


# ---------------------------------------------------------------------------
# Source scrapers
# ---------------------------------------------------------------------------


def _scrape_google_scholar(
    fetcher: Any,
    topic: str,
    max_results: int = MAX_PER_SOURCE,
) -> list[dict[str, Any]]:
    """Scrape Google Scholar search results by parsing HTML.

    Args:
        fetcher: Scrapling Fetcher instance.
        topic: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of evidence dicts with keys: title, authors, year, source, url, snippet, relevance_score.
    """
    results: list[dict[str, Any]] = []
    encoded_query = quote_plus(topic)
    url = f"https://scholar.google.com/scholar?q={encoded_query}&hl=en&num={max_results}"

    _rate_limit("scholar", SCHOLAR_RATE_LIMIT)
    try:
        response = fetcher.get(url, timeout=SCHOLAR_TIMEOUT)
        page = response
    except Exception as exc:
        print(f"WARN: Google Scholar fetch failed: {exc}", file=sys.stderr)
        return results

    try:
        # Parse result blocks — Scholar uses .gs_r .gs_ri structure
        entries = page.find_all("div", class_="gs_ri")
        if not entries:
            # Fallback: try to find h3 tags with links
            entries = page.find_all("h3", class_="gs_rt")

        for entry in entries[:max_results]:
            # Extract title and URL
            link = entry.find("a")
            title = link.text.strip() if link else entry.text.strip()
            href = link.get("href", "") if link else ""

            # Extract author/year line
            author_div = entry.find("div", class_="gs_a")
            author_text = author_div.text.strip() if author_div else ""
            authors = [a.strip() for a in author_text.split("-")[0].split(",")] if author_text else []
            year = _extract_year(author_text)

            # Extract snippet
            snippet_div = entry.find("div", class_="gs_rs")
            snippet = snippet_div.text.strip()[:MAX_SNIPPET_LEN] if snippet_div else ""

            relevance = _compute_relevance(title, snippet, topic)

            results.append(
                {
                    "title": title[:500],
                    "authors": authors[:10],
                    "year": year,
                    "source": "google_scholar",
                    "url": href,
                    "snippet": snippet,
                    "relevance_score": relevance,
                }
            )
    except Exception as exc:
        print(f"WARN: Google Scholar parse failed: {exc}", file=sys.stderr)

    return results


def _scrape_pubmed(
    fetcher: Any,
    topic: str,
    max_results: int = MAX_PER_SOURCE,
) -> list[dict[str, Any]]:
    """Scrape PubMed via E-utilities API (esearch + esummary).

    Args:
        fetcher: Scrapling Fetcher instance.
        topic: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of evidence dicts.
    """
    results: list[dict[str, Any]] = []
    encoded_query = quote_plus(topic)

    # Step 1: Search for IDs
    _rate_limit("pubmed", API_RATE_LIMIT)
    search_url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&term={encoded_query}&retmax={max_results}&retmode=json"
    )
    try:
        response = fetcher.get(search_url, timeout=API_TIMEOUT)
        data = json.loads(response.text)
    except Exception as exc:
        print(f"WARN: PubMed search failed: {exc}", file=sys.stderr)
        return results

    id_list = data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return results

    # Step 2: Fetch summaries
    _rate_limit("pubmed", API_RATE_LIMIT)
    ids_str = ",".join(id_list[:max_results])
    summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_str}&retmode=json"
    try:
        response = fetcher.get(summary_url, timeout=API_TIMEOUT)
        summary_data = json.loads(response.text)
    except Exception as exc:
        print(f"WARN: PubMed summary fetch failed: {exc}", file=sys.stderr)
        return results

    result_map = summary_data.get("result", {})
    for pmid in id_list[:max_results]:
        article = result_map.get(pmid, {})
        if not isinstance(article, dict):
            continue

        title = article.get("title", "")
        author_list = article.get("authors", [])
        authors = [a.get("name", "") for a in author_list if isinstance(a, dict)]
        pub_date = article.get("pubdate", "")
        year = _extract_year(pub_date)
        snippet = article.get("sorttitle", title)[:MAX_SNIPPET_LEN]

        relevance = _compute_relevance(title, snippet, topic)
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        results.append(
            {
                "title": title[:500],
                "authors": authors[:10],
                "year": year,
                "source": "pubmed",
                "url": url,
                "snippet": snippet,
                "relevance_score": relevance,
            }
        )

    return results


def _scrape_arxiv(
    fetcher: Any,
    topic: str,
    max_results: int = MAX_PER_SOURCE,
) -> list[dict[str, Any]]:
    """Scrape arXiv API for academic papers.

    Args:
        fetcher: Scrapling Fetcher instance.
        topic: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of evidence dicts.
    """
    results: list[dict[str, Any]] = []
    encoded_query = quote_plus(topic)

    _rate_limit("arxiv", API_RATE_LIMIT)
    url = (
        f"http://export.arxiv.org/api/query"
        f"?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=relevance"
    )
    try:
        response = fetcher.get(url, timeout=API_TIMEOUT)
        xml_text = response.text
    except Exception as exc:
        print(f"WARN: arXiv fetch failed: {exc}", file=sys.stderr)
        return results

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        print(f"WARN: arXiv XML parse failed: {exc}", file=sys.stderr)
        return results

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)

    for entry in entries[:max_results]:
        title_el = entry.find("atom:title", ns)
        title = title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else ""

        summary_el = entry.find("atom:summary", ns)
        snippet = (
            summary_el.text.strip().replace("\n", " ")[:MAX_SNIPPET_LEN]
            if summary_el is not None and summary_el.text
            else ""
        )

        authors: list[str] = []
        for author_el in entry.findall("atom:author", ns):
            name_el = author_el.find("atom:name", ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        published_el = entry.find("atom:published", ns)
        pub_text = published_el.text if published_el is not None and published_el.text else ""
        year = _extract_year(pub_text)

        link_el = entry.find("atom:id", ns)
        url = link_el.text.strip() if link_el is not None and link_el.text else ""

        relevance = _compute_relevance(title, snippet, topic)

        results.append(
            {
                "title": title[:500],
                "authors": authors[:10],
                "year": year,
                "source": "arxiv",
                "url": url,
                "snippet": snippet,
                "relevance_score": relevance,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scrape_evidence(topic: str, max_per_source: int = MAX_PER_SOURCE) -> list[dict[str, Any]]:
    """Scrape academic evidence from Google Scholar, PubMed, and arXiv.

    Args:
        topic: Research topic to search for.
        max_per_source: Maximum results per source (default 5).

    Returns:
        List of evidence dicts with keys:
        - title (str), authors (list[str]), year (int), source (str),
          url (str), snippet (str), relevance_score (float 0-1).

        Returns at most 15 results total, sorted by relevance_score descending.
        Returns an empty list if Scrapling is not installed or all sources fail.
    """
    if not SCRAPLING_AVAILABLE:
        print("WARN: scrapling not installed, returning empty evidence list", file=sys.stderr)
        return []

    fetcher = Fetcher(auto_match=False)
    all_evidence: list[dict[str, Any]] = []

    scrapers = [
        (_scrape_google_scholar, "Google Scholar"),
        (_scrape_pubmed, "PubMed"),
        (_scrape_arxiv, "arXiv"),
    ]

    for scraper_fn, name in scrapers:
        try:
            items = scraper_fn(fetcher, topic, max_per_source)
            all_evidence.extend(items)
            print(f"  {name}: {len(items)} results", file=sys.stderr)
        except Exception as exc:
            print(f"WARN: {name} scraper failed: {exc}", file=sys.stderr)

    # Sort by relevance descending, cap at MAX_TOTAL
    all_evidence.sort(key=lambda e: e.get("relevance_score", 0.0), reverse=True)
    return all_evidence[:MAX_TOTAL]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for standalone evidence scraping."""
    import argparse

    parser = argparse.ArgumentParser(description="Academic evidence scraper")
    parser.add_argument("--topic", required=True, help="Research topic to search")
    parser.add_argument("--max-per-source", type=int, default=MAX_PER_SOURCE, help="Max results per source")
    parser.add_argument("--output", default=None, help="Output file path (JSON)")
    args = parser.parse_args()

    print(f"Scraping evidence for: {args.topic}", file=sys.stderr)
    evidence = scrape_evidence(topic=args.topic, max_per_source=args.max_per_source)
    output_text = json.dumps(evidence, indent=2) + "\n"

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_text)
        print(f"Written {len(evidence)} evidence items to {args.output}", file=sys.stderr)
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
