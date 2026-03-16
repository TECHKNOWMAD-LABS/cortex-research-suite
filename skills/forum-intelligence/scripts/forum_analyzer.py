#!/usr/bin/env python3
"""
forum-intelligence: Forum thread analysis with coordination detection.
Phase 14 — BettaFish-inspired intelligence skills.
BettaFish engine type: forum_analysis

Analyzes discussion threads for sentiment, key arguments, coordination
patterns, and minority viewpoints.
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Set, Tuple

MAX_INPUT_CHARS = 50000

# ---------- Security helpers ----------

class _HTMLStripper(HTMLParser):
    """Strip HTML tags using stdlib html.parser."""

    def __init__(self):
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def strip_html(text: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()


def sanitize_input(text: str) -> str:
    """Truncate and strip HTML from user input."""
    text = text[:MAX_INPUT_CHARS]
    return strip_html(text)


# ---------- Output schema validation ----------

EXPECTED_KEYS = {
    "thread_summaries": list,
    "sentiment_distribution": dict,
    "key_arguments": list,
    "coordination_detected": bool,
    "coordination_evidence": list,
    "minority_viewpoints": list,
    "metadata": dict,
}


def validate_output(data: Dict[str, Any]) -> bool:
    """Validate output JSON against expected schema."""
    for key, expected_type in EXPECTED_KEYS.items():
        if key not in data:
            return False
        if not isinstance(data[key], expected_type):
            return False
    # Validate metadata sub-keys
    meta_keys = {"total_threads", "total_posts", "unique_authors", "timestamp"}
    if not meta_keys.issubset(set(data.get("metadata", {}).keys())):
        return False
    return True


# ---------- Core classes ----------

POSITIVE_WORDS = frozenset({
    "good", "great", "excellent", "agree", "support", "like", "love",
    "helpful", "positive", "thanks", "awesome", "best", "wonderful",
    "fantastic", "perfect", "correct", "right", "yes", "benefit",
})

NEGATIVE_WORDS = frozenset({
    "bad", "terrible", "disagree", "hate", "wrong", "awful", "worst",
    "no", "never", "fail", "failure", "risk", "danger", "threat",
    "stupid", "useless", "horrible", "against", "problem", "broken",
})

STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
    "to", "for", "of", "and", "or", "but", "with", "this", "that",
    "it", "be", "as", "by", "from", "not", "no", "i", "you", "we",
    "they", "he", "she", "my", "your", "his", "her", "its", "do",
    "did", "has", "have", "had", "will", "would", "can", "could",
    "should", "just", "so", "if", "then", "than", "also", "very",
})


class ThreadParser:
    """Parses and normalizes forum thread data."""

    def parse(self, raw_threads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        parsed = []
        for thread in raw_threads:
            title = sanitize_input(str(thread.get("title", "Untitled")))
            posts = []
            for post in thread.get("posts", []):
                posts.append({
                    "author": sanitize_input(str(post.get("author", "anonymous"))),
                    "content": sanitize_input(str(post.get("content", ""))),
                    "timestamp": str(post.get("timestamp", "")),
                })
            parsed.append({"title": title, "posts": posts})
        return parsed


class CoordinationDetector:
    """Detects potential coordination patterns among posters."""

    def detect(self, threads: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        evidence: List[str] = []

        for thread in threads:
            posts = thread["posts"]
            if len(posts) < 2:
                continue

            # Check 1: Repeated near-identical content
            contents = [p["content"].lower().strip() for p in posts]
            content_counts = Counter(contents)
            for content, count in content_counts.items():
                if count >= 3 and len(content) > 20:
                    evidence.append(
                        f"Identical content posted {count} times in "
                        f"thread '{thread['title']}': "
                        f"'{content[:80]}...'"
                    )

            # Check 2: Same author posting disproportionately
            author_counts = Counter(p["author"] for p in posts)
            total = len(posts)
            for author, count in author_counts.items():
                ratio = count / total if total > 0 else 0
                if count >= 5 and ratio > 0.5:
                    evidence.append(
                        f"Author '{author}' posted {count}/{total} times "
                        f"({ratio:.0%}) in thread '{thread['title']}'."
                    )

            # Check 3: Rapid-fire posting (timestamps within same second)
            timestamps = [p["timestamp"] for p in posts if p["timestamp"]]
            ts_counts = Counter(timestamps)
            for ts, count in ts_counts.items():
                if count >= 3:
                    evidence.append(
                        f"{count} posts at identical timestamp '{ts}' "
                        f"in thread '{thread['title']}'."
                    )

        coordination_detected = len(evidence) > 0
        return coordination_detected, evidence


class ViewpointExtractor:
    """Extracts key arguments, sentiment, and minority viewpoints."""

    def _classify_sentiment(self, text: str) -> str:
        words = set(
            re.sub(r"[^\w\s]", "", text.lower()).split()
        )
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        if pos > neg:
            return "positive"
        elif neg > pos:
            return "negative"
        return "neutral"

    def _extract_phrases(self, text: str) -> List[str]:
        """Extract non-trivial words for argument detection."""
        words = re.sub(r"[^\w\s]", "", text.lower()).split()
        return [w for w in words if w not in STOP_WORDS and len(w) > 2]

    def extract(
        self, threads: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, float], List[str], List[str]]:
        sentiments: List[str] = []
        all_phrases: List[str] = []
        author_sentiments: Dict[str, List[str]] = {}

        for thread in threads:
            for post in thread["posts"]:
                content = post["content"]
                sentiment = self._classify_sentiment(content)
                sentiments.append(sentiment)
                phrases = self._extract_phrases(content)
                all_phrases.extend(phrases)

                author = post["author"]
                if author not in author_sentiments:
                    author_sentiments[author] = []
                author_sentiments[author].append(sentiment)

        # Sentiment distribution
        total = len(sentiments) if sentiments else 1
        dist = {
            "positive": round(sentiments.count("positive") / total, 3),
            "negative": round(sentiments.count("negative") / total, 3),
            "neutral": round(sentiments.count("neutral") / total, 3),
        }

        # Key arguments from most frequent phrases
        phrase_counts = Counter(all_phrases)
        key_arguments = [
            phrase for phrase, _ in phrase_counts.most_common(10)
        ]

        # Minority viewpoints: authors whose sentiment opposes majority
        majority_sentiment = max(dist, key=dist.get)
        minority_viewpoints: List[str] = []
        for author, sents in author_sentiments.items():
            author_majority = Counter(sents).most_common(1)[0][0]
            if author_majority != majority_sentiment:
                minority_viewpoints.append(
                    f"Author '{author}' leans {author_majority} "
                    f"(vs. overall majority: {majority_sentiment})."
                )

        return dist, key_arguments, minority_viewpoints


# ---------- Orchestrator ----------

def analyze_forum(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run full forum intelligence analysis pipeline."""
    raw_threads = input_data.get("threads", [])
    if not isinstance(raw_threads, list):
        raw_threads = []

    parser = ThreadParser()
    coord_detector = CoordinationDetector()
    viewpoint_extractor = ViewpointExtractor()

    threads = parser.parse(raw_threads)
    coordination_detected, coordination_evidence = coord_detector.detect(threads)
    sentiment_dist, key_arguments, minority_viewpoints = (
        viewpoint_extractor.extract(threads)
    )

    # Thread summaries
    thread_summaries = []
    for thread in threads:
        post_count = len(thread["posts"])
        authors = {p["author"] for p in thread["posts"]}
        thread_summaries.append({
            "title": thread["title"],
            "post_count": post_count,
            "summary": (
                f"Thread with {post_count} posts from "
                f"{len(authors)} unique author(s)."
            ),
        })

    total_posts = sum(len(t["posts"]) for t in threads)
    all_authors: Set[str] = set()
    for t in threads:
        for p in t["posts"]:
            all_authors.add(p["author"])

    result = {
        "thread_summaries": thread_summaries,
        "sentiment_distribution": sentiment_dist,
        "key_arguments": key_arguments,
        "coordination_detected": coordination_detected,
        "coordination_evidence": coordination_evidence,
        "minority_viewpoints": minority_viewpoints,
        "metadata": {
            "total_threads": len(threads),
            "total_posts": total_posts,
            "unique_authors": len(all_authors),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

    if not validate_output(result):
        raise RuntimeError("Output validation failed against expected schema.")

    return result


# ---------- CLI ----------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="forum-intelligence: Forum thread analysis with coordination detection"
    )
    parser.add_argument(
        "--input", required=True, type=str,
        help="Path to input JSON file with thread data"
    )
    parser.add_argument(
        "--output", required=True, type=str,
        help="Output file path for JSON report"
    )
    parser.add_argument(
        "--format", default="json", choices=["json"],
        help="Output format (default: json)"
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        raw = f.read()[:MAX_INPUT_CHARS]
        input_data = json.loads(raw)

    if not isinstance(input_data, dict):
        print("Error: Input JSON must be an object.", file=sys.stderr)
        sys.exit(1)

    report = analyze_forum(input_data)

    output_json = json.dumps(report, indent=2, ensure_ascii=False)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output_json)

    print(f"Forum intelligence report written to {args.output}")
    print(f"Threads analyzed: {report['metadata']['total_threads']}")
    print(f"Total posts: {report['metadata']['total_posts']}")
    print(f"Coordination detected: {report['coordination_detected']}")


if __name__ == "__main__":
    main()
