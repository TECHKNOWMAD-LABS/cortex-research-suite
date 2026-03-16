"""Tests for MindSpider connector demo mode."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONNECTOR_DIR = Path(__file__).parent.parent.parent / "skills" / "mindspider-connector" / "scripts"
sys.path.insert(0, str(CONNECTOR_DIR))

from connector import generate_demo_data, run_connector

REQUIRED_KEYS = {"topic", "sentiment_score", "post_count", "trend_direction", "platforms"}


class TestGenerateDemoData:
    def test_returns_non_empty(self):
        data = generate_demo_data()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_item_has_required_keys(self):
        data = generate_demo_data()
        for item in data:
            missing = REQUIRED_KEYS - set(item.keys())
            assert not missing, f"Missing keys: {missing}"

    def test_sentiment_range(self):
        data = generate_demo_data()
        for item in data:
            assert -1.0 <= item["sentiment_score"] <= 1.0

    def test_platforms_is_list(self):
        data = generate_demo_data()
        for item in data:
            assert isinstance(item["platforms"], list)
            assert len(item["platforms"]) >= 1

    def test_domain_filter(self):
        data = generate_demo_data(domain="AI")
        assert len(data) > 0
        for item in data:
            assert "AI" in item["topic"] or "ai" in item["topic"].lower()


class TestRunConnector:
    def test_demo_source(self):
        result = run_connector(source="demo")
        assert isinstance(result, dict)
        assert "topics" in result
        assert len(result["topics"]) > 0

    def test_output_is_serializable(self):
        result = run_connector(source="demo")
        serialized = json.dumps(result)
        assert len(serialized) > 0
