"""KnowledgeEntry store with TF-IDF semantic search and auto-indexing.

Provides persistent storage of knowledge entries (research outputs, debate
results, evidence items) with full-text search and TF-IDF similarity scoring.
Integrates with the debate engine for retrieval-augmented generation.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class KnowledgeEntry:
    """A single knowledge entry in the store."""

    title: str
    content: str
    source: str  # debate, research, evidence, manual
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    @property
    def entry_id(self) -> str:
        key = f"{self.title}:{self.source}:{self.created_at}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class SearchResult:
    """A search result with relevance score."""

    entry: KnowledgeEntry
    score: float
    matched_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry.entry_id,
            "title": self.entry.title,
            "score": round(self.score, 4),
            "source": self.entry.source,
            "matched_terms": self.matched_terms,
            "content_preview": self.entry.content[:300],
        }


# ---------------------------------------------------------------------------
# TF-IDF engine
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from as into "
    "through during before after above below between under and but or nor not "
    "so yet both either neither each every all any few more most other some such "
    "no only own same than too very that this these those it its he she they them "
    "his her their our your we you i me us".split()
)


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text for search."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOP_WORDS and len(w) > 1]


class TFIDFIndex:
    """Lightweight TF-IDF index for semantic search."""

    def __init__(self) -> None:
        self._documents: dict[str, list[str]] = {}  # entry_id -> tokens
        self._df: Counter = Counter()  # document frequency per term

    def add(self, entry_id: str, text: str) -> None:
        tokens = _tokenize(text)
        self._documents[entry_id] = tokens
        unique_tokens = set(tokens)
        for token in unique_tokens:
            self._df[token] += 1

    def remove(self, entry_id: str) -> None:
        if entry_id not in self._documents:
            return
        unique_tokens = set(self._documents[entry_id])
        for token in unique_tokens:
            self._df[token] -= 1
            if self._df[token] <= 0:
                del self._df[token]
        del self._documents[entry_id]

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float, list[str]]]:
        """Search for relevant documents. Returns [(entry_id, score, matched_terms)]."""
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        n_docs = len(self._documents)
        if n_docs == 0:
            return []

        results: list[tuple[str, float, list[str]]] = []
        query_tf = Counter(query_tokens)

        for entry_id, doc_tokens in self._documents.items():
            doc_tf = Counter(doc_tokens)
            score = 0.0
            matched: list[str] = []

            for term, qtf in query_tf.items():
                if term in doc_tf:
                    # TF-IDF: tf(doc) * idf * tf(query)
                    tf_doc = doc_tf[term] / max(len(doc_tokens), 1)
                    idf = math.log(n_docs / (1 + self._df.get(term, 0)))
                    tf_query = qtf / len(query_tokens)
                    score += tf_doc * idf * tf_query
                    matched.append(term)

            if score > 0:
                results.append((entry_id, score, matched))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    @property
    def size(self) -> int:
        return len(self._documents)


# ---------------------------------------------------------------------------
# Knowledge Store
# ---------------------------------------------------------------------------


class KnowledgeStore:
    """Persistent knowledge store with SQLite + TF-IDF search.

    Auto-indexes all entries for semantic search.
    Integrates with debate engine via retrieve_context().
    """

    def __init__(self, db_path: str | Path = "knowledge/knowledge.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._index = TFIDFIndex()
        self._init_schema()
        self._rebuild_index()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS knowledge (
                entry_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge(source);
            CREATE INDEX IF NOT EXISTS idx_knowledge_created ON knowledge(created_at DESC);
        """)
        self._conn.commit()

    def _rebuild_index(self) -> None:
        """Rebuild TF-IDF index from all stored entries."""
        rows = self._conn.execute("SELECT entry_id, title, content, tags FROM knowledge").fetchall()
        for row in rows:
            tags_text = " ".join(json.loads(row["tags"]))
            full_text = f"{row['title']} {row['content']} {tags_text}"
            self._index.add(row["entry_id"], full_text)

    def add(self, entry: KnowledgeEntry) -> str:
        """Add a knowledge entry. Returns entry_id."""
        eid = entry.entry_id
        self._conn.execute(
            """INSERT OR REPLACE INTO knowledge
               (entry_id, title, content, source, tags, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                eid,
                entry.title,
                entry.content,
                entry.source,
                json.dumps(entry.tags),
                json.dumps(entry.metadata),
                entry.created_at,
            ),
        )
        self._conn.commit()

        # Index for search
        tags_text = " ".join(entry.tags)
        self._index.add(eid, f"{entry.title} {entry.content} {tags_text}")

        return eid

    def get(self, entry_id: str) -> KnowledgeEntry | None:
        row = self._conn.execute("SELECT * FROM knowledge WHERE entry_id = ?", (entry_id,)).fetchone()
        return self._row_to_entry(row) if row else None

    def search(self, query: str, top_k: int = 10, source: str | None = None) -> list[SearchResult]:
        """Semantic search over the knowledge store."""
        raw_results = self._index.search(query, top_k=top_k * 2 if source else top_k)
        results: list[SearchResult] = []

        for entry_id, score, matched in raw_results:
            entry = self.get(entry_id)
            if entry is None:
                continue
            if source and entry.source != source:
                continue
            results.append(SearchResult(entry=entry, score=score, matched_terms=matched))
            if len(results) >= top_k:
                break

        return results

    def retrieve_context(self, query: str, max_tokens: int = 2000, top_k: int = 5) -> str:
        """Retrieve relevant context for debate engine integration.

        Returns a formatted string of relevant knowledge entries
        suitable for injection into agent prompts.
        """
        results = self.search(query, top_k=top_k)
        if not results:
            return ""

        parts = ["## Retrieved Knowledge\n"]
        total_len = 0
        for r in results:
            snippet = f"### {r.entry.title} (score: {r.score:.3f})\n{r.entry.content}\n"
            if total_len + len(snippet) > max_tokens * 4:  # rough char estimate
                break
            parts.append(snippet)
            total_len += len(snippet)

        return "\n".join(parts)

    def auto_index_research(self, report_path: Path) -> list[str]:
        """Auto-index a research report JSON into the knowledge store."""
        data = json.loads(report_path.read_text())
        indexed: list[str] = []

        # Index the main report
        eid = self.add(
            KnowledgeEntry(
                title=f"Research: {data.get('topic', 'unknown')}",
                content=data.get("report", "")[:10000],
                source="research",
                tags=["research", "report"],
                metadata={"topic": data.get("topic"), "confidence": data.get("analysis", {}).get("confidence")},
            )
        )
        indexed.append(eid)

        # Index individual evidence items
        for ev in data.get("evidence", []):
            eid = self.add(
                KnowledgeEntry(
                    title=f"Evidence: {ev.get('source', 'unknown')}",
                    content=ev.get("finding", ""),
                    source="evidence",
                    tags=["evidence", ev.get("direction", ""), ev.get("strength", "")],
                    metadata=ev,
                )
            )
            indexed.append(eid)

        # Index key findings
        analysis = data.get("analysis", {})
        for finding in analysis.get("key_findings", []):
            eid = self.add(
                KnowledgeEntry(
                    title=f"Finding: {finding[:60]}",
                    content=finding,
                    source="research",
                    tags=["finding", "key"],
                )
            )
            indexed.append(eid)

        return indexed

    def auto_index_debate(self, debate_path: Path) -> list[str]:
        """Auto-index a debate result JSON into the knowledge store."""
        data = json.loads(debate_path.read_text())
        indexed: list[str] = []

        topic = data.get("topic", "unknown")

        # Index the final synthesis
        synthesis = data.get("final_synthesis_preview", "")
        if synthesis:
            eid = self.add(
                KnowledgeEntry(
                    title=f"Debate Synthesis: {topic}",
                    content=synthesis,
                    source="debate",
                    tags=["debate", "synthesis", "consensus"],
                    metadata={"topic": topic, "rounds": data.get("num_rounds", 0)},
                )
            )
            indexed.append(eid)

        # Index per-round key outputs
        for rnd in data.get("rounds", []):
            for agent_name, output in rnd.get("outputs", {}).items():
                content = output.get("content_preview", "")
                if content:
                    eid = self.add(
                        KnowledgeEntry(
                            title=f"Debate R{rnd['round']} {agent_name}: {topic}",
                            content=content,
                            source="debate",
                            tags=["debate", agent_name, f"round-{rnd['round']}"],
                            metadata={"topic": topic, "round": rnd["round"], "agent": agent_name},
                        )
                    )
                    indexed.append(eid)

        return indexed

    def list_entries(self, source: str | None = None, limit: int = 50) -> list[KnowledgeEntry]:
        query = "SELECT * FROM knowledge"
        params: list[Any] = []
        if source:
            query += " WHERE source = ?"
            params.append(source)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        total = self._conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        by_source: dict[str, int] = {}
        for row in self._conn.execute("SELECT source, COUNT(*) as cnt FROM knowledge GROUP BY source").fetchall():
            by_source[row["source"]] = row["cnt"]
        return {
            "total_entries": total,
            "by_source": by_source,
            "index_size": self._index.size,
            "db_path": str(self._db_path),
        }

    def delete(self, entry_id: str) -> bool:
        self._index.remove(entry_id)
        cursor = self._conn.execute("DELETE FROM knowledge WHERE entry_id = ?", (entry_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        self._conn.close()

    def _row_to_entry(self, row: sqlite3.Row) -> KnowledgeEntry:
        return KnowledgeEntry(
            title=row["title"],
            content=row["content"],
            source=row["source"],
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
        )
