"""Dataset generation pipeline.

Orchestrates generators, validation, and sharding into a single
pipeline for producing large-scale evaluation datasets.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cortex.synthetic.base_generator import BaseGenerator, GeneratedPrompt
from cortex.synthetic.validator import DatasetValidator, ValidationReport
from cortex.synthetic.shard_manager import ShardManager
from cortex.telemetry.logger import get_logger


@dataclass
class PipelineReport:
    """Report from a dataset generation pipeline run."""

    generators_used: list[str] = field(default_factory=list)
    total_generated: int = 0
    total_valid: int = 0
    validation_report: ValidationReport | None = None
    shards_created: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "generators_used": self.generators_used,
            "total_generated": self.total_generated,
            "total_valid": self.total_valid,
            "validation": self.validation_report.to_dict() if self.validation_report else None,
            "shards_created": self.shards_created,
            "duration_seconds": round(self.duration_seconds, 2),
        }


class DatasetPipeline:
    """End-to-end dataset generation pipeline.

    Pipeline stages:
    1. Generate prompts from multiple generators
    2. Validate and deduplicate
    3. Shard into files for efficient processing
    """

    def __init__(
        self,
        output_dir: str | Path = "datasets",
        shard_size: int = 10_000,
        min_length: int = 10,
        max_length: int = 10_000,
    ) -> None:
        self._output_dir = Path(output_dir)
        self._validator = DatasetValidator(
            min_length=min_length,
            max_length=max_length,
        )
        self._shard_manager = ShardManager(self._output_dir, shard_size=shard_size)
        self._logger = get_logger()

    def run(
        self,
        generators: list[tuple[BaseGenerator, int]],
    ) -> PipelineReport:
        """Run the full dataset generation pipeline.

        Args:
            generators: List of (generator, count) tuples specifying
                        how many prompts to generate from each.
        """
        start = time.time()
        report = PipelineReport()
        all_prompts: list[GeneratedPrompt] = []

        # Stage 1: Generate
        for gen, count in generators:
            self._logger.info(
                "Generating prompts",
                generator=gen.category,
                count=count,
            )
            prompts = gen.generate(count)
            all_prompts.extend(prompts)
            report.generators_used.append(gen.category)

        report.total_generated = len(all_prompts)

        # Stage 2: Validate
        self._logger.info("Validating dataset", total=len(all_prompts))
        valid_prompts, validation = self._validator.validate(all_prompts)
        report.total_valid = len(valid_prompts)
        report.validation_report = validation

        # Stage 3: Shard by category
        by_category: dict[str, list[GeneratedPrompt]] = {}
        for p in valid_prompts:
            by_category.setdefault(p.category, []).append(p)

        total_shards = 0
        for category, prompts in by_category.items():
            self._logger.info(
                "Writing shards",
                category=category,
                count=len(prompts),
            )
            shard_paths = self._shard_manager.write_shards(category, prompts)
            total_shards += len(shard_paths)

        report.shards_created = total_shards
        report.duration_seconds = time.time() - start

        self._logger.info(
            "Pipeline complete",
            generated=report.total_generated,
            valid=report.total_valid,
            shards=report.shards_created,
        )
        return report
