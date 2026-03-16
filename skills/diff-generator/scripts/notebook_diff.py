#!/usr/bin/env python3
"""Jupyter notebook (.ipynb) diff tool for the Diff Generator skill.

Compares two Jupyter notebooks cell-by-cell, producing a structured diff
of code and markdown changes.

Usage:
    python notebook_diff.py --old <path> --new <path> --output json|text
"""

import argparse
import difflib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CellDiff:
    """Represents the diff of a single notebook cell."""
    cell_index: int
    cell_type: str  # code, markdown, raw
    status: str  # added, removed, modified, unchanged
    old_source: Optional[str] = None
    new_source: Optional[str] = None
    diff_lines: list = field(default_factory=list)
    old_outputs_summary: Optional[str] = None
    new_outputs_summary: Optional[str] = None


@dataclass
class NotebookDiffResult:
    """Complete diff result between two notebooks."""
    old_path: str
    new_path: str
    old_cell_count: int = 0
    new_cell_count: int = 0
    cells_added: int = 0
    cells_removed: int = 0
    cells_modified: int = 0
    cells_unchanged: int = 0
    kernel_changed: bool = False
    old_kernel: str = ""
    new_kernel: str = ""
    cell_diffs: list = field(default_factory=list)


class NotebookDiffer:
    """Compares two Jupyter notebooks and produces a structured diff."""

    def __init__(self, old_path: str, new_path: str):
        self.old_path = old_path
        self.new_path = new_path
        self.old_nb = None
        self.new_nb = None

    def _load_notebook(self, path: str) -> dict:
        """Load and parse a .ipynb file."""
        nb_path = Path(path)
        if not nb_path.exists():
            print(f"Error: Notebook not found: {path}", file=sys.stderr)
            sys.exit(1)
        if not nb_path.suffix == ".ipynb":
            print(f"Warning: File does not have .ipynb extension: {path}", file=sys.stderr)

        try:
            with open(nb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
            sys.exit(1)

    def _get_cells(self, notebook: dict) -> list:
        """Extract cells from a notebook."""
        return notebook.get("cells", [])

    def _get_kernel_name(self, notebook: dict) -> str:
        """Extract the kernel display name from notebook metadata."""
        metadata = notebook.get("metadata", {})
        kernelspec = metadata.get("kernelspec", {})
        return kernelspec.get("display_name", kernelspec.get("name", "unknown"))

    def _get_cell_source(self, cell: dict) -> str:
        """Get cell source as a single string."""
        source = cell.get("source", [])
        if isinstance(source, list):
            return "".join(source)
        return str(source)

    def _get_cell_type(self, cell: dict) -> str:
        """Get cell type."""
        return cell.get("cell_type", "unknown")

    def _summarize_outputs(self, cell: dict) -> Optional[str]:
        """Summarize cell outputs for display."""
        outputs = cell.get("outputs", [])
        if not outputs:
            return None

        summaries = []
        for output in outputs:
            output_type = output.get("output_type", "unknown")
            if output_type == "stream":
                text = output.get("text", [])
                content = "".join(text) if isinstance(text, list) else str(text)
                lines = content.strip().split("\n")
                if len(lines) > 3:
                    summaries.append(f"stream ({len(lines)} lines)")
                else:
                    summaries.append(f"stream: {content.strip()[:80]}")
            elif output_type == "execute_result":
                summaries.append("execute_result")
            elif output_type == "display_data":
                data = output.get("data", {})
                types = list(data.keys())
                summaries.append(f"display_data [{', '.join(types)}]")
            elif output_type == "error":
                ename = output.get("ename", "Error")
                summaries.append(f"error: {ename}")
            else:
                summaries.append(output_type)

        return "; ".join(summaries)

    def _compute_cell_diff(self, old_source: str, new_source: str) -> list:
        """Compute a unified diff between two cell sources."""
        old_lines = old_source.splitlines(keepends=True)
        new_lines = new_source.splitlines(keepends=True)
        return list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile="old", tofile="new",
            lineterm="",
        ))

    def diff(self) -> NotebookDiffResult:
        """Perform the notebook diff and return structured results."""
        self.old_nb = self._load_notebook(self.old_path)
        self.new_nb = self._load_notebook(self.new_path)

        old_cells = self._get_cells(self.old_nb)
        new_cells = self._get_cells(self.new_nb)

        result = NotebookDiffResult(
            old_path=self.old_path,
            new_path=self.new_path,
            old_cell_count=len(old_cells),
            new_cell_count=len(new_cells),
            old_kernel=self._get_kernel_name(self.old_nb),
            new_kernel=self._get_kernel_name(self.new_nb),
        )
        result.kernel_changed = result.old_kernel != result.new_kernel

        # Use SequenceMatcher to align cells by source content
        old_sources = [self._get_cell_source(c) for c in old_cells]
        new_sources = [self._get_cell_source(c) for c in new_cells]

        matcher = difflib.SequenceMatcher(None, old_sources, new_sources)
        cell_index = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    cell = CellDiff(
                        cell_index=cell_index,
                        cell_type=self._get_cell_type(old_cells[i1 + k]),
                        status="unchanged",
                        old_source=old_sources[i1 + k],
                        new_source=new_sources[j1 + k],
                    )
                    result.cell_diffs.append(cell)
                    result.cells_unchanged += 1
                    cell_index += 1

            elif tag == "replace":
                max_len = max(i2 - i1, j2 - j1)
                for k in range(max_len):
                    old_idx = i1 + k if (i1 + k) < i2 else None
                    new_idx = j1 + k if (j1 + k) < j2 else None

                    if old_idx is not None and new_idx is not None:
                        diff_lines = self._compute_cell_diff(
                            old_sources[old_idx], new_sources[new_idx]
                        )
                        cell = CellDiff(
                            cell_index=cell_index,
                            cell_type=self._get_cell_type(new_cells[new_idx]),
                            status="modified",
                            old_source=old_sources[old_idx],
                            new_source=new_sources[new_idx],
                            diff_lines=diff_lines,
                            old_outputs_summary=self._summarize_outputs(old_cells[old_idx]),
                            new_outputs_summary=self._summarize_outputs(new_cells[new_idx]),
                        )
                        result.cells_modified += 1
                    elif old_idx is not None:
                        cell = CellDiff(
                            cell_index=cell_index,
                            cell_type=self._get_cell_type(old_cells[old_idx]),
                            status="removed",
                            old_source=old_sources[old_idx],
                            old_outputs_summary=self._summarize_outputs(old_cells[old_idx]),
                        )
                        result.cells_removed += 1
                    else:
                        cell = CellDiff(
                            cell_index=cell_index,
                            cell_type=self._get_cell_type(new_cells[new_idx]),
                            status="added",
                            new_source=new_sources[new_idx],
                            new_outputs_summary=self._summarize_outputs(new_cells[new_idx]),
                        )
                        result.cells_added += 1

                    result.cell_diffs.append(cell)
                    cell_index += 1

            elif tag == "delete":
                for k in range(i1, i2):
                    cell = CellDiff(
                        cell_index=cell_index,
                        cell_type=self._get_cell_type(old_cells[k]),
                        status="removed",
                        old_source=old_sources[k],
                        old_outputs_summary=self._summarize_outputs(old_cells[k]),
                    )
                    result.cell_diffs.append(cell)
                    result.cells_removed += 1
                    cell_index += 1

            elif tag == "insert":
                for k in range(j1, j2):
                    cell = CellDiff(
                        cell_index=cell_index,
                        cell_type=self._get_cell_type(new_cells[k]),
                        status="added",
                        new_source=new_sources[k],
                        new_outputs_summary=self._summarize_outputs(new_cells[k]),
                    )
                    result.cell_diffs.append(cell)
                    result.cells_added += 1
                    cell_index += 1

        return result

    def format_text(self, result: NotebookDiffResult) -> str:
        """Format the diff result as human-readable text."""
        lines = [
            "=" * 60,
            "NOTEBOOK DIFF",
            "=" * 60,
            f"Old: {result.old_path} ({result.old_cell_count} cells)",
            f"New: {result.new_path} ({result.new_cell_count} cells)",
            "",
        ]

        if result.kernel_changed:
            lines.append(f"Kernel changed: {result.old_kernel} -> {result.new_kernel}")
            lines.append("")

        lines.extend([
            f"Added:     {result.cells_added}",
            f"Removed:   {result.cells_removed}",
            f"Modified:  {result.cells_modified}",
            f"Unchanged: {result.cells_unchanged}",
            "",
        ])

        for cd in result.cell_diffs:
            if cd.status == "unchanged":
                continue

            lines.append("-" * 40)
            lines.append(f"Cell {cd.cell_index} [{cd.cell_type}] — {cd.status.upper()}")

            if cd.status == "added":
                for line in (cd.new_source or "").splitlines():
                    lines.append(f"  + {line}")
            elif cd.status == "removed":
                for line in (cd.old_source or "").splitlines():
                    lines.append(f"  - {line}")
            elif cd.status == "modified":
                for line in cd.diff_lines:
                    lines.append(f"  {line.rstrip()}")

            if cd.old_outputs_summary or cd.new_outputs_summary:
                if cd.old_outputs_summary:
                    lines.append(f"  Old outputs: {cd.old_outputs_summary}")
                if cd.new_outputs_summary:
                    lines.append(f"  New outputs: {cd.new_outputs_summary}")

            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def format_json(self, result: NotebookDiffResult) -> str:
        """Format the diff result as JSON."""
        data = {
            "old_path": result.old_path,
            "new_path": result.new_path,
            "old_cell_count": result.old_cell_count,
            "new_cell_count": result.new_cell_count,
            "kernel_changed": result.kernel_changed,
            "old_kernel": result.old_kernel,
            "new_kernel": result.new_kernel,
            "summary": {
                "added": result.cells_added,
                "removed": result.cells_removed,
                "modified": result.cells_modified,
                "unchanged": result.cells_unchanged,
            },
            "cell_diffs": [
                {
                    "cell_index": cd.cell_index,
                    "cell_type": cd.cell_type,
                    "status": cd.status,
                    "old_source": cd.old_source,
                    "new_source": cd.new_source,
                    "diff_lines": cd.diff_lines,
                    "old_outputs_summary": cd.old_outputs_summary,
                    "new_outputs_summary": cd.new_outputs_summary,
                }
                for cd in result.cell_diffs
                if cd.status != "unchanged"
            ],
        }
        return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Diff two Jupyter notebooks cell-by-cell"
    )
    parser.add_argument(
        "--old",
        required=True,
        help="Path to the old (base) notebook",
    )
    parser.add_argument(
        "--new",
        required=True,
        help="Path to the new (changed) notebook",
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    differ = NotebookDiffer(old_path=args.old, new_path=args.new)
    result = differ.diff()

    if args.output == "json":
        print(differ.format_json(result))
    else:
        print(differ.format_text(result))


if __name__ == "__main__":
    main()
