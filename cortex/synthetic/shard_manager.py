"""Dataset shard manager for large-scale dataset storage.

Handles partitioning datasets into shards, writing/reading shards,
and managing the shard index for efficient access.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from cortex.synthetic.base_generator import GeneratedPrompt
from cortex.utils.io import read_json, write_json


class ShardManager:
    """Manages sharded dataset storage for large-scale evaluation.

    Splits datasets into fixed-size shards for memory-efficient
    processing and parallel evaluation.
    """

    def __init__(self, base_dir: str | Path, shard_size: int = 10_000) -> None:
        self._base_dir = Path(base_dir)
        self._shard_size = shard_size
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_category(name: str) -> None:
        """Validate category name to prevent path traversal."""
        if not name or "/" in name or "\\" in name or ".." in name or "\x00" in name:
            raise ValueError(f"Invalid category name: {name!r}")
        if not all(c.isalnum() or c in "-_" for c in name):
            raise ValueError(f"Category name must be alphanumeric with - or _: {name!r}")

    def write_shards(self, category: str, prompts: list[GeneratedPrompt]) -> list[Path]:
        """Write prompts to shards, returning paths of created shard files."""
        self._validate_category(category)
        cat_dir = self._base_dir / category
        cat_dir.mkdir(parents=True, exist_ok=True)

        num_shards = math.ceil(len(prompts) / self._shard_size)
        shard_paths: list[Path] = []

        for i in range(num_shards):
            start = i * self._shard_size
            end = min(start + self._shard_size, len(prompts))
            shard_data = [p.to_dict() for p in prompts[start:end]]
            shard_path = cat_dir / f"shard_{i:04d}.json"
            write_json(shard_path, shard_data)
            shard_paths.append(shard_path)

        # Write index
        index = {
            "category": category,
            "total_prompts": len(prompts),
            "shard_count": num_shards,
            "shard_size": self._shard_size,
            "shards": [str(p.name) for p in shard_paths],
        }
        write_json(cat_dir / "index.json", index)
        return shard_paths

    def read_shard(self, category: str, shard_index: int) -> list[dict[str, Any]]:
        """Read a specific shard by category and index."""
        self._validate_category(category)
        if not isinstance(shard_index, int) or shard_index < 0:
            raise ValueError(f"Invalid shard index: {shard_index}")
        shard_path = self._base_dir / category / f"shard_{shard_index:04d}.json"
        return read_json(shard_path)

    def iter_shards(self, category: str):
        """Iterate over all shards in a category, yielding prompt dicts."""
        self._validate_category(category)
        cat_dir = self._base_dir / category
        index_path = cat_dir / "index.json"
        if not index_path.exists():
            return

        index = read_json(index_path)
        for shard_name in index["shards"]:
            shard_data = read_json(cat_dir / shard_name)
            yield from shard_data

    def get_index(self, category: str) -> dict[str, Any] | None:
        """Get the shard index for a category."""
        self._validate_category(category)
        index_path = self._base_dir / category / "index.json"
        if not index_path.exists():
            return None
        return read_json(index_path)

    def list_categories(self) -> list[str]:
        """List all available dataset categories."""
        return [d.name for d in self._base_dir.iterdir() if d.is_dir() and (d / "index.json").exists()]

    @property
    def stats(self) -> dict[str, Any]:
        """Get overall dataset statistics."""
        categories = self.list_categories()
        total = 0
        details = {}
        for cat in categories:
            index = self.get_index(cat)
            if index:
                count = index["total_prompts"]
                total += count
                details[cat] = count
        return {
            "total_prompts": total,
            "categories": details,
            "shard_size": self._shard_size,
        }
