"""Tests for shard manager."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cortex.synthetic.shard_manager import ShardManager
from cortex.synthetic.base_generator import GeneratedPrompt


class TestShardManager:
    def _make_prompts(self, n: int) -> list[GeneratedPrompt]:
        return [
            GeneratedPrompt(
                prompt=f"prompt_{i}",
                category="test",
                difficulty="easy",
                metadata={"idx": i},
            )
            for i in range(n)
        ]

    def test_write_and_read_shard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir, shard_size=5)
            prompts = self._make_prompts(3)
            paths = mgr.write_shards("testcat", prompts)
            assert len(paths) == 1
            data = mgr.read_shard("testcat", 0)
            assert len(data) == 3

    def test_multiple_shards(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir, shard_size=2)
            prompts = self._make_prompts(5)
            paths = mgr.write_shards("testcat", prompts)
            assert len(paths) == 3  # ceil(5/2)

    def test_iter_shards(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir, shard_size=2)
            prompts = self._make_prompts(5)
            mgr.write_shards("testcat", prompts)
            items = list(mgr.iter_shards("testcat"))
            assert len(items) == 5

    def test_iter_shards_no_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir, shard_size=5)
            items = list(mgr.iter_shards("nonexistent"))
            assert items == []

    def test_get_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir, shard_size=5)
            prompts = self._make_prompts(3)
            mgr.write_shards("testcat", prompts)
            index = mgr.get_index("testcat")
            assert index is not None
            assert index["total_prompts"] == 3
            assert index["shard_count"] == 1

    def test_get_index_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir, shard_size=5)
            assert mgr.get_index("nonexistent") is None

    def test_list_categories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir, shard_size=5)
            prompts = self._make_prompts(2)
            mgr.write_shards("cat_a", prompts)
            mgr.write_shards("cat_b", prompts)
            cats = mgr.list_categories()
            assert sorted(cats) == ["cat_a", "cat_b"]

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir, shard_size=5)
            prompts = self._make_prompts(3)
            mgr.write_shards("testcat", prompts)
            stats = mgr.stats
            assert stats["total_prompts"] == 3
            assert stats["categories"]["testcat"] == 3

    def test_validate_category_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir)
            with pytest.raises(ValueError):
                mgr.write_shards("../evil", [])

    def test_validate_category_rejects_slashes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir)
            with pytest.raises(ValueError):
                mgr.read_shard("foo/bar", 0)

    def test_invalid_shard_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = ShardManager(tmpdir)
            with pytest.raises(ValueError):
                mgr.read_shard("testcat", -1)
