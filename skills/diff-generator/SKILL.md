---
name: diff-generator
description: >
  Snapshot files, apply edits, and generate unified diffs for review before
  committing changes. Use when making multi-file edits, reviewing changes
  holistically, or when you need rollback capability. Triggers on "show me
  the diff", "diff-generator", "what changed", "review changes", or
  "snapshot before editing".
---

# Diff Generator Skill

The diff-generator skill provides a workflow for safely editing multiple files with full visibility into changes before committing them. It uses file snapshots and unified diff generation for confident, reviewable modifications.

## Workflow

The typical workflow follows these stages:

1. **Snapshot** — Create a timestamped snapshot of target files/directories before making changes
2. **Edit** — Apply modifications to your files using normal tools or scripts
3. **Diff** — Generate a unified diff comparing the snapshot to the current state
4. **Review** — Examine the diff output to validate all changes are correct
5. **Apply/Rollback** — Commit the changes or restore from the snapshot if needed

This approach ensures you have complete visibility into what changed and the ability to undo if necessary.

## Snapshot Script Usage

The `snap_diff.py` script provides four main commands for managing file snapshots and diffs.

### Snapshot Command

Create a timestamped snapshot of target files or a directory:

```
python3 snap_diff.py snapshot --target /path/to/dir --snapshot-dir /tmp/snapshots
```

The snapshot operation:
- Recursively copies all files from the target location
- Creates a timestamped directory (format: `YYYY-MM-DDTHH-MM-SS`)
- Stores metadata in `snapshot.json` containing file list, sizes, and timestamps
- Preserves directory structure for easy comparison

Example:
```
python3 snap_diff.py snapshot --target ./src --snapshot-dir ./snapshots
# Creates: ./snapshots/2026-03-13T10-30-45/
```

### Diff Command

Generate a unified diff between a snapshot and the current state:

```
python3 snap_diff.py diff --snapshot /tmp/snapshots/2026-03-13T12-00-00 --target /path/to/dir
```

Options:
- `--output /path/to/diff.patch` — Save diff to file instead of printing
- `--format unified|json` — Output format (default: unified)

The unified diff format matches Git output, showing:
- File paths with `---` and `+++` headers
- Line numbers in `@@ ... @@` chunks
- Context lines, added lines (prefixed with `+`), removed lines (prefixed with `-`)

Terminal output uses ANSI colors:
- Green for added lines
- Red for removed lines
- Default color for context lines

Example:
```
python3 snap_diff.py diff --snapshot ./snapshots/2026-03-13T10-30-45 --target ./src --output changes.patch
```

### Rollback Command

Restore files from a snapshot (with confirmation):

```
python3 snap_diff.py rollback --snapshot /tmp/snapshots/2026-03-13T12-00-00 --target /path/to/dir
```

The rollback operation:
- Compares snapshot and current state to identify changed files
- Displays a summary of files that will be overwritten
- Prompts for confirmation before proceeding
- Restores all files from the snapshot

Example:
```
python3 snap_diff.py rollback --snapshot ./snapshots/2026-03-13T10-30-45 --target ./src
# Prompts for confirmation, then restores files
```

### List Command

View all available snapshots:

```
python3 snap_diff.py list --snapshot-dir /tmp/snapshots
```

Output includes:
- Snapshot timestamp
- Number of files in each snapshot
- Total size
- Creation date and time

## Features and Behavior

**Unified Diff Format**

The diff output uses the standard unified diff format compatible with `git diff` and `patch` command. This allows diffs to be:
- Reviewed in any text editor
- Piped to version control tools
- Applied with standard patch utilities

**Binary File Handling**

The script automatically detects binary files and:
- Skips detailed diff generation (binary files cannot be diffed as text)
- Reports whether the binary file changed or remained unchanged
- Includes the filename in the summary

**Recursive Directory Support**

Snapshots preserve the full directory structure, making it easy to:
- Track changes across nested subdirectories
- Understand the overall impact of modifications
- Apply changes consistently across a project

**Metadata Tracking**

Each snapshot stores a `snapshot.json` file containing:
- List of all files in the snapshot
- File sizes (for change detection)
- Snapshot creation timestamp
- Directory structure information

This enables accurate diff generation even if files are deleted or moved.

**Terminal Color Output**

When printing diffs to the terminal, the script uses ANSI color codes:
- Added lines: green
- Removed lines: red
- Context lines: default color

This makes changes visually distinct and easier to review quickly.

**JSON Output Format**

For machine-readable diffs, use `--format json` to receive:
- Structured representation of changes
- File paths, change types, and line-by-line differences
- Machine parsing for automated workflows

## Integration with Git

While diff-generator is standalone, it complements Git workflows:

- Generate snapshots before starting a feature branch
- Make edits across multiple files
- Review changes with diff-generator before staging
- Use `git apply` or `patch` to apply the diff.patch file
- Commit with confidence knowing exactly what changed

The unified diff output is fully compatible with Git tools.

## Example Workflow

1. Start with a project directory containing multiple source files:
   ```
   python3 snap_diff.py snapshot --target ./myproject --snapshot-dir ./snapshots
   # Creates snapshot at: ./snapshots/2026-03-13T14-30-00
   ```

2. Edit multiple files in `./myproject` (using your preferred editor or tools)

3. Generate a diff to review all changes:
   ```
   python3 snap_diff.py diff --snapshot ./snapshots/2026-03-13T14-30-00 --target ./myproject
   # Displays unified diff in terminal
   ```

4. Save the diff for later reference or application:
   ```
   python3 snap_diff.py diff --snapshot ./snapshots/2026-03-13T14-30-00 --target ./myproject --output changes.patch
   ```

5. If changes look good, commit them. If not, rollback:
   ```
   python3 snap_diff.py rollback --snapshot ./snapshots/2026-03-13T14-30-00 --target ./myproject
   # Restores all files to snapshot state after confirmation
   ```

6. List all snapshots for future reference:
   ```
   python3 snap_diff.py list --snapshot-dir ./snapshots
   ```
