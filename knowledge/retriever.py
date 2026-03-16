"""Knowledge retriever — FTS5 search interface for the knowledge store.

Provides semantic search retrieval with ranked results.
Will be upgraded to GraphRAG in Phase 15.

Usage:
    python -m knowledge.retriever --query "AKI prediction bias"
    python -m knowledge.retriever --query "nephrology triage" --source research --top-k 5
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from knowledge.store import KnowledgeStore, SearchResult


class KnowledgeRetriever:
    """Search interface for the knowledge store.

    Currently uses TF-IDF search. Will be upgraded to GraphRAG
    with entity extraction and relationship traversal in Phase 15.
    """

    def __init__(self, store: KnowledgeStore) -> None:
        self._store = store

    def search(
        self,
        query: str,
        top_k: int = 10,
        source: str | None = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """Search the knowledge store with optional filtering."""
        results = self._store.search(query, top_k=top_k, source=source)
        if min_score > 0:
            results = [r for r in results if r.score >= min_score]
        return results

    def retrieve_for_debate(self, topic: str, max_tokens: int = 2000) -> str:
        """Retrieve context formatted for debate engine injection."""
        return self._store.retrieve_context(topic, max_tokens=max_tokens)

    def retrieve_for_research(self, topic: str, max_items: int = 10) -> list[dict[str, Any]]:
        """Retrieve evidence items for the research pipeline."""
        results = self.search(topic, top_k=max_items, source="evidence")
        return [
            {
                "source": r.entry.title,
                "finding": r.entry.content,
                "relevance_score": r.score,
                "tags": r.entry.tags,
            }
            for r in results
        ]

    def stats(self) -> dict[str, Any]:
        return self._store.stats()


def main() -> int:
    parser = argparse.ArgumentParser(description="Knowledge store search")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--top-k", type=int, default=10, help="Max results")
    parser.add_argument("--source", default=None, help="Filter by source")
    parser.add_argument("--min-score", type=float, default=0.0, help="Minimum score threshold")
    parser.add_argument("--db", default="knowledge/knowledge.db", help="Knowledge store DB path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    store = KnowledgeStore(db_path=args.db)
    retriever = KnowledgeRetriever(store)

    results = retriever.search(args.query, top_k=args.top_k, source=args.source, min_score=args.min_score)

    if args.json:
        output = [r.to_dict() for r in results]
        print(json.dumps(output, indent=2))
    else:
        print(f"Query: {args.query}")
        print(f"Results: {len(results)}")
        print()
        for r in results:
            print(f"  [{r.score:.4f}] {r.entry.title}")
            print(f"           Source: {r.entry.source} | Tags: {', '.join(r.entry.tags)}")
            print(f"           {r.entry.content[:150]}...")
            print()

    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
