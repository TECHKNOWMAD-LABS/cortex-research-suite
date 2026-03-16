"""Knowledge indexer — watches reports/ and auto-indexes research outputs.

Monitors directories for new research reports, debate results, and
evidence files, then auto-indexes them into the knowledge store.

Usage:
    python -m knowledge.indexer --watch reports/
    python -m knowledge.indexer --index-all
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from knowledge.store import KnowledgeEntry, KnowledgeStore


class KnowledgeIndexer:
    """Auto-indexes research outputs into the knowledge store."""

    WATCH_PATTERNS = {
        "research_report.json": "research",
        "intelligence_report_*.json": "debate",
        "debate_*.json": "debate",
        "evidence.jsonl": "evidence",
    }

    def __init__(self, store: KnowledgeStore) -> None:
        self._store = store
        self._indexed_files: set[str] = set()

    def index_directory(self, directory: Path) -> list[str]:
        """Index all recognized files in a directory tree."""
        indexed: list[str] = []

        for json_file in directory.rglob("*.json"):
            if str(json_file) in self._indexed_files:
                continue

            file_name = json_file.name
            try:
                if file_name == "research_report.json":
                    ids = self._store.auto_index_research(json_file)
                    indexed.extend(ids)
                elif file_name.startswith("intelligence_report_") or file_name.startswith("debate_"):
                    ids = self._store.auto_index_debate(json_file)
                    indexed.extend(ids)
                else:
                    # Try generic JSON indexing
                    data = json.loads(json_file.read_text())
                    if isinstance(data, dict) and "topic" in data:
                        eid = self._store.add(
                            KnowledgeEntry(
                                title=f"Document: {json_file.stem}",
                                content=json.dumps(data)[:5000],
                                source="auto-indexed",
                                tags=["auto-indexed", json_file.parent.name],
                            )
                        )
                        indexed.append(eid)

                self._indexed_files.add(str(json_file))
            except (json.JSONDecodeError, KeyError, OSError):
                continue

        # Index JSONL evidence files
        for jsonl_file in directory.rglob("*.jsonl"):
            if str(jsonl_file) in self._indexed_files:
                continue
            try:
                for line in jsonl_file.read_text().splitlines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if isinstance(data, dict) and "finding" in data:
                        eid = self._store.add(
                            KnowledgeEntry(
                                title=f"Evidence: {data.get('source', jsonl_file.stem)}",
                                content=data.get("finding", ""),
                                source="evidence",
                                tags=["evidence", data.get("direction", ""), data.get("strength", "")],
                                metadata=data,
                            )
                        )
                        indexed.append(eid)
                self._indexed_files.add(str(jsonl_file))
            except (json.JSONDecodeError, OSError):
                continue

        return indexed

    def watch(self, directory: Path, interval: float = 10.0, max_cycles: int = 0) -> None:
        """Watch a directory for new files and auto-index them."""
        print(f"Watching {directory} for new files (interval: {interval}s)")
        cycles = 0
        while True:
            indexed = self.index_directory(directory)
            if indexed:
                print(f"  Indexed {len(indexed)} new entries")
            cycles += 1
            if max_cycles > 0 and cycles >= max_cycles:
                break
            time.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser(description="Knowledge store auto-indexer")
    parser.add_argument("--watch", type=Path, default=None, help="Directory to watch")
    parser.add_argument("--index-all", action="store_true", help="Index all recognized files")
    parser.add_argument("--db", default="knowledge/knowledge.db", help="Knowledge store DB path")
    parser.add_argument("--interval", type=float, default=10.0, help="Watch interval in seconds")
    args = parser.parse_args()

    store = KnowledgeStore(db_path=args.db)
    indexer = KnowledgeIndexer(store)

    if args.index_all:
        for search_dir in [Path("experiments"), Path("reports")]:
            if search_dir.exists():
                indexed = indexer.index_directory(search_dir)
                print(f"Indexed {len(indexed)} entries from {search_dir}")
        print(f"Store stats: {store.stats()}")
    elif args.watch:
        indexer.watch(args.watch, interval=args.interval)
    else:
        print("Specify --watch <dir> or --index-all")
        return 1

    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
