#!/usr/bin/env python3
"""
snap_diff.py - File snapshot and unified diff generation tool.

Provides snapshot, diff, rollback, and list commands for managing file versions
and generating git-style unified diffs before committing changes.

Usage:
    python3 snap_diff.py snapshot --target /path/to/dir --snapshot-dir /tmp/snapshots
    python3 snap_diff.py diff --snapshot /tmp/snapshots/2026-03-13T12-00-00 --target /path/to/dir
    python3 snap_diff.py rollback --snapshot /tmp/snapshots/2026-03-13T12-00-00 --target /path/to/dir
    python3 snap_diff.py list --snapshot-dir /tmp/snapshots
"""

import argparse
import difflib
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path


class SnapDiff:
    """Handle file snapshots and unified diff generation."""

    # ANSI color codes for terminal output
    COLOR_GREEN = '\033[32m'
    COLOR_RED = '\033[31m'
    COLOR_RESET = '\033[0m'
    COLOR_BOLD = '\033[1m'

    # Binary file signatures (common file extensions)
    BINARY_EXTENSIONS = {
        '.bin', '.exe', '.dll', '.so', '.a', '.o', '.pyc', '.pyo',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp',
        '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv',
        '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
        '.docx', '.xlsx', '.pptx', '.db', '.sqlite',
    }

    def __init__(self):
        """Initialize the SnapDiff instance."""
        self.snapshot_metadata = {}

    def is_binary_file(self, filepath):
        """Check if a file is likely binary based on extension and content."""
        # Check by extension first
        if Path(filepath).suffix.lower() in self.BINARY_EXTENSIONS:
            return True

        # Check file content for null bytes
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(8192)
                if b'\x00' in chunk:
                    return True
        except (OSError, IOError):
            return True

        return False

    def get_files_in_directory(self, dirpath):
        """Recursively get all files in a directory."""
        files = []
        for root, dirs, filenames in os.walk(dirpath):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                files.append(full_path)
        return sorted(files)

    def snapshot(self, target, snapshot_dir):
        """Create a timestamped snapshot of target files or directory."""
        target_path = Path(target).resolve()

        if not target_path.exists():
            print(f"Error: Target '{target}' does not exist", file=sys.stderr)
            return False

        # Create snapshot directory if needed
        snapshot_dir_path = Path(snapshot_dir).resolve()
        snapshot_dir_path.mkdir(parents=True, exist_ok=True)

        # Generate timestamped snapshot location
        timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        snapshot_path = snapshot_dir_path / timestamp
        snapshot_path.mkdir(parents=True, exist_ok=True)

        # Collect files to snapshot
        if target_path.is_file():
            files_to_snapshot = [target_path]
        else:
            files_to_snapshot = [Path(f) for f in self.get_files_in_directory(str(target_path))]

        metadata = {
            'timestamp': timestamp,
            'target': str(target_path),
            'file_count': len(files_to_snapshot),
            'files': [],
            'created_at': datetime.now().isoformat(),
        }

        total_size = 0

        # Copy files to snapshot
        for source_file in files_to_snapshot:
            try:
                # Calculate relative path
                if target_path.is_file():
                    rel_path = source_file.name
                else:
                    rel_path = source_file.relative_to(target_path)

                dest_file = snapshot_path / rel_path

                # Create parent directories
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(str(source_file), str(dest_file))

                file_size = source_file.stat().st_size
                total_size += file_size

                metadata['files'].append({
                    'path': str(rel_path),
                    'size': file_size,
                })
            except (OSError, IOError) as e:
                print(f"Warning: Could not snapshot '{source_file}': {e}", file=sys.stderr)

        metadata['total_size'] = total_size

        # Write metadata
        metadata_file = snapshot_path / 'snapshot.json'
        try:
            with open(str(metadata_file), 'w') as f:
                json.dump(metadata, f, indent=2)
        except (OSError, IOError) as e:
            print(f"Error: Could not write snapshot metadata: {e}", file=sys.stderr)
            return False

        print(f"Snapshot created: {snapshot_path}")
        print(f"Files: {len(files_to_snapshot)}")
        print(f"Size: {self._format_size(total_size)}")
        return True

    def diff(self, snapshot, target, output=None, format_type='unified'):
        """Generate unified diff between snapshot and current state."""
        snapshot_path = Path(snapshot).resolve()
        target_path = Path(target).resolve()

        if not snapshot_path.exists():
            print(f"Error: Snapshot '{snapshot}' does not exist", file=sys.stderr)
            return False

        if not target_path.exists():
            print(f"Error: Target '{target}' does not exist", file=sys.stderr)
            return False

        # Load snapshot metadata
        metadata_file = snapshot_path / 'snapshot.json'
        try:
            with open(str(metadata_file), 'r') as f:
                metadata = json.load(f)
        except (OSError, IOError, json.JSONDecodeError) as e:
            print(f"Error: Could not load snapshot metadata: {e}", file=sys.stderr)
            return False

        # Generate diff
        diff_lines = []

        for file_info in metadata['files']:
            rel_path = file_info['path']
            snapshot_file = snapshot_path / rel_path
            target_file = target_path / rel_path

            if format_type == 'json':
                diff_lines.append(self._diff_file_json(
                    snapshot_file, target_file, rel_path
                ))
            else:
                diff_lines.extend(self._diff_file_unified(
                    snapshot_file, target_file, rel_path
                ))

        # Handle files in target that don't exist in snapshot (new files)
        if target_path.is_dir():
            target_files = {str(Path(f).relative_to(target_path)): Path(f)
                          for f in self.get_files_in_directory(str(target_path))}
            snapshot_files = {f['path']: f for f in metadata['files']}

            for rel_path_str, target_file in target_files.items():
                if rel_path_str not in snapshot_files:
                    if format_type == 'json':
                        diff_lines.append(self._diff_file_json(None, target_file, rel_path_str))
                    else:
                        diff_lines.extend(self._diff_file_unified(None, target_file, rel_path_str))

        # Output diff
        diff_output = self._format_diff_output(diff_lines, format_type)

        if output:
            try:
                with open(output, 'w') as f:
                    f.write(diff_output)
                print(f"Diff written to: {output}")
            except (OSError, IOError) as e:
                print(f"Error: Could not write diff file: {e}", file=sys.stderr)
                return False
        else:
            print(diff_output)

        return True

    def _diff_file_unified(self, snapshot_file, target_file, rel_path):
        """Generate unified diff for a single file."""
        diff_lines = []

        snapshot_exists = snapshot_file and snapshot_file.exists()
        target_exists = target_file and target_file.exists()

        if not snapshot_exists and not target_exists:
            return diff_lines

        # Check if binary
        if snapshot_exists and self.is_binary_file(str(snapshot_file)):
            diff_lines.append(f"Binary file {rel_path} (snapshot) differs")
            return diff_lines

        if target_exists and self.is_binary_file(str(target_file)):
            diff_lines.append(f"Binary file {rel_path} (current) differs")
            return diff_lines

        # Read file contents
        snapshot_lines = []
        if snapshot_exists:
            try:
                with open(str(snapshot_file), 'r', errors='replace') as f:
                    snapshot_lines = f.readlines()
            except (OSError, IOError):
                pass

        target_lines = []
        if target_exists:
            try:
                with open(str(target_file), 'r', errors='replace') as f:
                    target_lines = f.readlines()
            except (OSError, IOError):
                pass

        # Skip if no difference
        if snapshot_lines == target_lines:
            return diff_lines

        # Generate unified diff
        unified = difflib.unified_diff(
            snapshot_lines,
            target_lines,
            fromfile=f'snapshot/{rel_path}',
            tofile=f'current/{rel_path}',
            lineterm=''
        )

        diff_lines.extend(unified)

        return diff_lines

    def _diff_file_json(self, snapshot_file, target_file, rel_path):
        """Generate JSON diff for a single file."""
        snapshot_exists = snapshot_file and Path(snapshot_file).exists()
        target_exists = target_file and Path(target_file).exists()

        status = 'modified'
        if not snapshot_exists:
            status = 'added'
        elif not target_exists:
            status = 'deleted'

        return {
            'path': rel_path,
            'status': status,
            'snapshot_exists': snapshot_exists,
            'target_exists': target_exists,
        }

    def _format_diff_output(self, diff_lines, format_type):
        """Format diff output with colors or JSON."""
        if format_type == 'json':
            return json.dumps(diff_lines, indent=2)

        output = []
        for line in diff_lines:
            if isinstance(line, str):
                if line.startswith('+') and not line.startswith('+++'):
                    output.append(f"{self.COLOR_GREEN}{line}{self.COLOR_RESET}")
                elif line.startswith('-') and not line.startswith('---'):
                    output.append(f"{self.COLOR_RED}{line}{self.COLOR_RESET}")
                else:
                    output.append(line)

        return '\n'.join(output)

    def rollback(self, snapshot, target):
        """Restore files from a snapshot with confirmation."""
        snapshot_path = Path(snapshot).resolve()
        target_path = Path(target).resolve()

        if not snapshot_path.exists():
            print(f"Error: Snapshot '{snapshot}' does not exist", file=sys.stderr)
            return False

        if not target_path.exists():
            print(f"Error: Target '{target}' does not exist", file=sys.stderr)
            return False

        # Load snapshot metadata
        metadata_file = snapshot_path / 'snapshot.json'
        try:
            with open(str(metadata_file), 'r') as f:
                metadata = json.load(f)
        except (OSError, IOError, json.JSONDecodeError) as e:
            print(f"Error: Could not load snapshot metadata: {e}", file=sys.stderr)
            return False

        # Identify files to restore
        changed_files = []
        for file_info in metadata['files']:
            rel_path = file_info['path']
            snapshot_file = snapshot_path / rel_path
            target_file = target_path / rel_path

            if not target_file.exists():
                changed_files.append((rel_path, 'missing'))
            else:
                try:
                    with open(str(snapshot_file), 'rb') as f1, open(str(target_file), 'rb') as f2:
                        if f1.read() != f2.read():
                            changed_files.append((rel_path, 'modified'))
                except (OSError, IOError):
                    changed_files.append((rel_path, 'error'))

        if not changed_files:
            print("No changes to rollback")
            return True

        # Display summary
        print(f"\nRollback will restore {len(changed_files)} file(s):")
        for rel_path, status in changed_files[:10]:
            print(f"  {rel_path} ({status})")
        if len(changed_files) > 10:
            print(f"  ... and {len(changed_files) - 10} more")

        # Confirm
        response = input("\nProceed with rollback? (yes/no): ").strip().lower()
        if response not in ('yes', 'y'):
            print("Rollback cancelled")
            return True

        # Restore files
        restored = 0
        for file_info in metadata['files']:
            rel_path = file_info['path']
            snapshot_file = snapshot_path / rel_path
            target_file = target_path / rel_path

            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(snapshot_file), str(target_file))
                restored += 1
            except (OSError, IOError) as e:
                print(f"Warning: Could not restore '{rel_path}': {e}", file=sys.stderr)

        print(f"\nRestored {restored}/{len(metadata['files'])} files")
        return True

    def list_snapshots(self, snapshot_dir):
        """List all available snapshots."""
        snapshot_dir_path = Path(snapshot_dir).resolve()

        if not snapshot_dir_path.exists():
            print(f"Snapshot directory '{snapshot_dir}' does not exist")
            return True

        snapshots = []
        for item in sorted(snapshot_dir_path.iterdir()):
            if item.is_dir():
                metadata_file = item / 'snapshot.json'
                if metadata_file.exists():
                    try:
                        with open(str(metadata_file), 'r') as f:
                            metadata = json.load(f)
                        snapshots.append({
                            'path': item.name,
                            'timestamp': metadata.get('timestamp', 'N/A'),
                            'files': metadata.get('file_count', 0),
                            'size': metadata.get('total_size', 0),
                            'created': metadata.get('created_at', 'N/A'),
                        })
                    except (OSError, IOError, json.JSONDecodeError):
                        pass

        if not snapshots:
            print("No snapshots found")
            return True

        print(f"{'Timestamp':<20} {'Files':<8} {'Size':<12} {'Created':<25}")
        print('-' * 65)

        for snap in snapshots:
            size_str = self._format_size(snap['size'])
            created_str = snap['created'][:19] if snap['created'] != 'N/A' else 'N/A'
            print(f"{snap['timestamp']:<20} {snap['files']:<8} {size_str:<12} {created_str:<25}")

        return True

    @staticmethod
    def _format_size(size_bytes):
        """Format bytes to human-readable size."""
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


def main():
    """Parse arguments and execute commands."""
    parser = argparse.ArgumentParser(
        description='File snapshot and unified diff generation tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 snap_diff.py snapshot --target /path/to/dir --snapshot-dir /tmp/snapshots
  python3 snap_diff.py diff --snapshot /tmp/snapshots/2026-03-13T12-00-00 --target /path/to/dir
  python3 snap_diff.py rollback --snapshot /tmp/snapshots/2026-03-13T12-00-00 --target /path/to/dir
  python3 snap_diff.py list --snapshot-dir /tmp/snapshots
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Snapshot command
    snapshot_parser = subparsers.add_parser('snapshot', help='Create a file snapshot')
    snapshot_parser.add_argument('--target', required=True, help='Target file or directory to snapshot')
    snapshot_parser.add_argument('--snapshot-dir', required=True, help='Directory to store snapshots')

    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Generate unified diff')
    diff_parser.add_argument('--snapshot', required=True, help='Path to snapshot directory')
    diff_parser.add_argument('--target', required=True, help='Target file or directory')
    diff_parser.add_argument('--output', help='Output file for diff (default: stdout)')
    diff_parser.add_argument('--format', choices=['unified', 'json'], default='unified',
                            help='Output format (default: unified)')

    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Restore files from snapshot')
    rollback_parser.add_argument('--snapshot', required=True, help='Path to snapshot directory')
    rollback_parser.add_argument('--target', required=True, help='Target file or directory')

    # List command
    list_parser = subparsers.add_parser('list', help='List available snapshots')
    list_parser.add_argument('--snapshot-dir', required=True, help='Snapshot directory to list')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    snap_diff = SnapDiff()

    try:
        if args.command == 'snapshot':
            success = snap_diff.snapshot(args.target, args.snapshot_dir)
        elif args.command == 'diff':
            success = snap_diff.diff(
                args.snapshot,
                args.target,
                output=args.output,
                format_type=args.format
            )
        elif args.command == 'rollback':
            success = snap_diff.rollback(args.snapshot, args.target)
        elif args.command == 'list':
            success = snap_diff.list_snapshots(args.snapshot_dir)
        else:
            parser.print_help()
            return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
