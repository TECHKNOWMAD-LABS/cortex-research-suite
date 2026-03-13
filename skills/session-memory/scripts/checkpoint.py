#!/usr/bin/env python3
"""
Session checkpoint manager for Claude Code sessions.

Manages structured checkpoint files to preserve session state across
context compaction and long-running operations.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


class CheckpointManager:
    """Manages session checkpoint creation, loading, and listing."""

    def __init__(self, time_window_seconds=3600):
        """
        Initialize checkpoint manager.

        Args:
            time_window_seconds: Time window for detecting recent file modifications
                                 (default: 1 hour)
        """
        self.time_window = timedelta(seconds=time_window_seconds)

    def save(
        self,
        session_dir,
        output_path,
        decisions=None,
        errors=None,
        tasks=None,
        include_files=True,
    ):
        """
        Create and save a checkpoint file.

        Args:
            session_dir: Path to session working directory
            output_path: Where to write checkpoint file
            decisions: List of decision descriptions
            errors: List of error descriptions
            tasks: Dict mapping task names to status
            include_files: Whether to scan and include modified files

        Returns:
            Path to created checkpoint file
        """
        session_dir = Path(session_dir).resolve()
        output_path = Path(output_path).resolve()

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate timestamp
        timestamp = datetime.now(timezone.utc).isoformat()
        timestamp_display = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        checkpoint = self._build_checkpoint(
            session_dir=session_dir,
            timestamp=timestamp_display,
            decisions=decisions or [],
            errors=errors or [],
            tasks=tasks or {},
            include_files=include_files,
        )

        # Write checkpoint
        output_path.write_text(checkpoint, encoding="utf-8")
        return str(output_path)

    def _build_checkpoint(self, session_dir, timestamp, decisions, errors, tasks, include_files):
        """Build checkpoint markdown content."""
        lines = []

        # Header
        lines.append(f"# Session Checkpoint — {timestamp}")
        lines.append("")

        # Files modified
        if include_files:
            files = self._get_recent_files(session_dir)
            lines.append("## Files Modified")
            if files:
                for filepath, size_kb, modified_time in sorted(files):
                    rel_path = _make_absolute(filepath)
                    lines.append(f"- {rel_path} ({size_kb}, {modified_time})")
            else:
                lines.append("(no recent files)")
            lines.append("")

        # Decisions
        lines.append("## Decisions Made")
        if decisions:
            for decision in decisions:
                lines.append(f"- {decision}")
        else:
            lines.append("(none yet)")
        lines.append("")

        # Errors
        lines.append("## Errors Resolved")
        if errors:
            for error in errors:
                lines.append(f"- {error}")
        else:
            lines.append("(none)")
        lines.append("")

        # Tasks
        lines.append("## Current Tasks")
        if tasks:
            for task_name, status in tasks.items():
                checkbox = "x" if status == "completed" else " "
                lines.append(f"- [{checkbox}] {task_name}")
        else:
            lines.append("(no tasks tracked)")
        lines.append("")

        # Environment
        lines.append("## Environment")
        lines.append(f"- Working directory: {session_dir}")
        lines.append(f"- Checkpoint created: {timestamp}")
        lines.append(f"- Python version: {sys.version.split()[0]}")
        lines.append("")

        return "\n".join(lines)

    def _get_recent_files(self, session_dir):
        """
        Scan session directory for recently modified files.

        Returns list of (filepath, size_kb, modified_time_str) tuples.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - self.time_window
        recent_files = []

        if not session_dir.exists():
            return recent_files

        for item in session_dir.rglob("*"):
            if not item.is_file():
                continue

            # Skip common non-essential directories
            if any(skip in item.parts for skip in [".git", "__pycache__", ".pytest_cache"]):
                continue

            # Check modification time
            mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
            if mtime >= cutoff:
                size_kb = round(item.stat().st_size / 1024, 1)
                mtime_str = mtime.strftime("%Y-%m-%dT%H:%M:%SZ")
                recent_files.append((str(item), size_kb, mtime_str))

        return recent_files

    def load(self, checkpoint_path):
        """
        Load and parse a checkpoint file.

        Returns dict with sections: files, decisions, errors, tasks, environment
        """
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        content = checkpoint_path.read_text(encoding="utf-8")
        return self._parse_checkpoint(content)

    def _parse_checkpoint(self, content):
        """Parse checkpoint markdown into structured data."""
        result = {
            "files": [],
            "decisions": [],
            "errors": [],
            "tasks": [],
            "environment": {},
        }

        current_section = None
        lines = content.split("\n")

        for line in lines:
            line = line.rstrip()

            # Section headers
            if line.startswith("## "):
                header = line[3:].strip()
                if header == "Files Modified":
                    current_section = "files"
                elif header == "Decisions Made":
                    current_section = "decisions"
                elif header == "Errors Resolved":
                    current_section = "errors"
                elif header == "Current Tasks":
                    current_section = "tasks"
                elif header == "Environment":
                    current_section = "environment"
                continue

            # Skip header line and empty lines
            if line.startswith("# ") or not line.strip():
                continue

            # Parse list items
            if line.startswith("- "):
                item = line[2:].strip()
                if current_section == "files":
                    result["files"].append(item)
                elif current_section == "decisions":
                    result["decisions"].append(item)
                elif current_section == "errors":
                    result["errors"].append(item)
                elif current_section == "tasks":
                    result["tasks"].append(item)

            # Parse environment key-value pairs
            elif current_section == "environment" and line.startswith("- "):
                item = line[2:].strip()
                if ":" in item:
                    key, value = item.split(":", 1)
                    result["environment"][key.strip()] = value.strip()

        return result

    def list_checkpoints(self, checkpoint_dir):
        """
        List all checkpoint files in a directory.

        Returns list of (filename, timestamp, path) tuples sorted by recency.
        """
        checkpoint_dir = Path(checkpoint_dir)
        if not checkpoint_dir.exists():
            return []

        checkpoints = []
        for cp_file in checkpoint_dir.glob("*.md"):
            try:
                content = cp_file.read_text(encoding="utf-8")
                # Extract timestamp from first line
                match = re.search(r"# Session Checkpoint — (.+)", content)
                if match:
                    timestamp_str = match.group(1)
                    checkpoints.append((cp_file.name, timestamp_str, str(cp_file)))
            except (IOError, OSError):
                continue

        # Sort by timestamp (reverse chronological)
        checkpoints.sort(key=lambda x: x[1], reverse=True)
        return checkpoints


def _make_absolute(path):
    """Ensure path is absolute string."""
    p = Path(path)
    if not p.is_absolute():
        p = p.resolve()
    return str(p)


def _parse_tasks_json(tasks_json_str):
    """Parse tasks from JSON string into dict."""
    if not tasks_json_str:
        return {}
    try:
        return json.loads(tasks_json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for tasks: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Session checkpoint manager for Claude Code"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Save command
    save_parser = subparsers.add_parser("save", help="Create a checkpoint")
    save_parser.add_argument(
        "--session-dir",
        required=True,
        help="Path to session working directory",
    )
    save_parser.add_argument(
        "--output",
        required=True,
        help="Output checkpoint file path",
    )
    save_parser.add_argument(
        "--decisions",
        action="append",
        default=[],
        help="Key decision (can be repeated)",
    )
    save_parser.add_argument(
        "--errors",
        action="append",
        default=[],
        help="Error description (can be repeated)",
    )
    save_parser.add_argument(
        "--tasks",
        help='JSON dict mapping task names to status, e.g. \'{"task1": "completed"}\'',
    )
    save_parser.add_argument(
        "--time-window",
        type=int,
        default=3600,
        help="Time window for recent files in seconds (default: 3600)",
    )

    # Load command
    load_parser = subparsers.add_parser("load", help="Load and display checkpoint")
    load_parser.add_argument(
        "--checkpoint",
        required=True,
        help="Path to checkpoint file",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List checkpoints")
    list_parser.add_argument(
        "--checkpoint-dir",
        required=True,
        help="Directory containing checkpoint files",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        manager = CheckpointManager(time_window_seconds=getattr(args, "time_window", 3600))

        if args.command == "save":
            tasks = _parse_tasks_json(args.tasks)
            output = manager.save(
                session_dir=args.session_dir,
                output_path=args.output,
                decisions=args.decisions,
                errors=args.errors,
                tasks=tasks,
            )
            print(f"Checkpoint saved: {output}")

        elif args.command == "load":
            data = manager.load(args.checkpoint)
            print(f"Checkpoint: {args.checkpoint}\n")
            print("Files Modified:")
            for f in data["files"] or ["(none)"]:
                print(f"  {f}")
            print("\nDecisions Made:")
            for d in data["decisions"] or ["(none)"]:
                print(f"  {d}")
            print("\nErrors Resolved:")
            for e in data["errors"] or ["(none)"]:
                print(f"  {e}")
            print("\nCurrent Tasks:")
            for t in data["tasks"] or ["(none)"]:
                print(f"  {t}")
            print("\nEnvironment:")
            for k, v in (data["environment"] or {}).items():
                print(f"  {k}: {v}")

        elif args.command == "list":
            checkpoints = manager.list_checkpoints(args.checkpoint_dir)
            if not checkpoints:
                print(f"No checkpoints found in {args.checkpoint_dir}")
            else:
                print(f"Checkpoints in {args.checkpoint_dir}:\n")
                for filename, timestamp, path in checkpoints:
                    print(f"  {filename}")
                    print(f"    Timestamp: {timestamp}")
                    print(f"    Path: {path}\n")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
