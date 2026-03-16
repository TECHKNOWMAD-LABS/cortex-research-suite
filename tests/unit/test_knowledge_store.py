"""Tests for GraphStore knowledge graph."""

from __future__ import annotations

import sys
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent.parent.parent / "knowledge"
sys.path.insert(0, str(KNOWLEDGE_DIR))

from graph_store import GraphStore, Triple


class TestGraphStore:
    def test_instantiation(self):
        gs = GraphStore()
        assert gs is not None
        assert len(gs._triples) == 0

    def test_add_triple(self):
        gs = GraphStore()
        t = gs.add_triple("AKI", "caused_by", "nephrotoxic drugs")
        assert isinstance(t, Triple)
        assert t.subject == "AKI"
        assert t.predicate == "caused_by"
        assert t.object == "nephrotoxic drugs"

    def test_query_by_subject(self):
        gs = GraphStore()
        gs.add_triple("AKI", "caused_by", "nephrotoxic drugs")
        gs.add_triple("AKI", "diagnosed_with", "serum creatinine")
        gs.add_triple("CKD", "caused_by", "diabetes")
        results = gs.query(subject="AKI")
        assert len(results) == 2

    def test_query_by_predicate(self):
        gs = GraphStore()
        gs.add_triple("AKI", "caused_by", "nephrotoxic drugs")
        gs.add_triple("CKD", "caused_by", "diabetes")
        results = gs.query(predicate="caused_by")
        assert len(results) == 2

    def test_empty_query_returns_all(self):
        gs = GraphStore()
        gs.add_triple("A", "r", "B")
        gs.add_triple("C", "r", "D")
        assert len(gs.query()) == 2

    def test_add_triple_with_metadata(self):
        gs = GraphStore()
        t = gs.add_triple("AKI", "treated_with", "dialysis", metadata={"source": "pubmed"})
        assert t.metadata == {"source": "pubmed"}
