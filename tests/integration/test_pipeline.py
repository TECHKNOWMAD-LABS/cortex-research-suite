"""Integration tests for dataset generation pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cortex.synthetic import (
    ReasoningGenerator,
    AdversarialGenerator,
    DatasetValidator,
    ShardManager,
)
from cortex.pipelines.dataset_pipeline import DatasetPipeline


class TestDatasetPipeline:
    def test_end_to_end(self):
        """Generate -> validate -> shard -> read back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DatasetPipeline(output_dir=tmpdir, shard_size=50)
            report = pipeline.run(
                [
                    (ReasoningGenerator(seed=42), 100),
                    (AdversarialGenerator(seed=42), 50),
                ]
            )

            assert report.total_generated == 150
            assert report.total_valid > 0
            assert report.shards_created > 0

            # Verify we can read shards back
            shard_manager = ShardManager(tmpdir)
            categories = shard_manager.list_categories()
            assert len(categories) >= 1

            stats = shard_manager.stats
            assert stats["total_prompts"] == report.total_valid


class TestShardManager:
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ShardManager(tmpdir, shard_size=10)
            gen = ReasoningGenerator(seed=42)
            prompts = gen.generate(25)

            paths = manager.write_shards("reasoning", prompts)
            assert len(paths) == 3  # 25 / 10 = 3 shards

            # Read back
            shard0 = manager.read_shard("reasoning", 0)
            assert len(shard0) == 10

            # Index
            index = manager.get_index("reasoning")
            assert index is not None
            assert index["total_prompts"] == 25

    def test_iter_shards(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ShardManager(tmpdir, shard_size=10)
            gen = ReasoningGenerator(seed=42)
            prompts = gen.generate(15)
            manager.write_shards("test", prompts)

            all_prompts = list(manager.iter_shards("test"))
            assert len(all_prompts) == 15
