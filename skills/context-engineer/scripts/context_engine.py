#!/usr/bin/env python3
"""
Context Engineer: Token-optimized context management system.

Manages context window allocation, auto-prunes irrelevant items,
scores relevance, and controls injection to prevent token bloat.
"""

import json
import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math

# Token estimation: words * 1.3 (word-based approximation)
TOKEN_MULTIPLIER = 1.3

# Default budget: 100K tokens
DEFAULT_BUDGET = 100_000

# Budget allocation by category (percentage)
BUDGET_ALLOCATION = {
    "system": 0.20,
    "task": 0.40,
    "reference": 0.25,
    "history": 0.15,
}

# Alert thresholds (percent of category budget)
ALERT_YELLOW = 70
ALERT_ORANGE = 85
ALERT_RED = 95

# State file for persistence
STATE_FILE = Path(__file__).parent.parent / "context_state.json"


def estimate_tokens(text: str) -> int:
    """Estimate token count using word-based approximation."""
    word_count = len(text.split())
    return max(1, int(word_count * TOKEN_MULTIPLIER))


def calculate_recency_score(hours_elapsed: float) -> float:
    """
    Calculate recency score with exponential decay.
    Formula: score = 100 * e^(-0.05 * hours)
    """
    if hours_elapsed < 0:
        hours_elapsed = 0
    score = 100 * math.exp(-0.05 * hours_elapsed)
    return min(100, max(0, score))


def calculate_frequency_score(reference_count: int) -> float:
    """Calculate frequency score based on reference count."""
    if reference_count == 0:
        return 0
    elif reference_count <= 3:
        return 33
    elif reference_count <= 8:
        return 67
    else:
        return 100


def calculate_task_alignment_score(is_critical: bool, is_related: bool) -> float:
    """Calculate task alignment score."""
    if is_critical:
        return 100
    elif is_related:
        return 67
    else:
        return 0


def calculate_dependency_score(dependency_count: int) -> float:
    """Calculate dependency score."""
    if dependency_count == 0:
        return 0
    elif dependency_count <= 2:
        return 50
    else:
        return 100


def calculate_relevance_score(
    recency: float, frequency: float, task_alignment: float, dependency: float
) -> float:
    """
    Calculate combined relevance score.
    Formula: 0.3*recency + 0.2*frequency + 0.4*task_alignment + 0.1*dependency
    """
    score = (0.3 * recency) + (0.2 * frequency) + (0.4 * task_alignment) + (0.1 * dependency)
    return min(100, max(0, score))


class ContextItem:
    """Represents a single context item in the window."""

    def __init__(
        self,
        source: str,
        size_tokens: int,
        category: str,
        priority: str,
        content: str = "",
    ):
        self.source = source
        self.size_tokens = size_tokens
        self.category = category
        self.priority = priority
        self.content = content
        self.timestamp = datetime.now().isoformat()
        self.last_accessed = datetime.now().isoformat()
        self.access_count = 0
        self.relevance_score = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "size_tokens": self.size_tokens,
            "category": self.category,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
            "content_preview": self.content[:100] if self.content else "",
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ContextItem":
        """Create from dictionary."""
        item = cls(
            data["source"],
            data["size_tokens"],
            data["category"],
            data["priority"],
        )
        item.timestamp = data.get("timestamp", item.timestamp)
        item.last_accessed = data.get("last_accessed", item.last_accessed)
        item.access_count = data.get("access_count", 0)
        item.relevance_score = data.get("relevance_score", 0)
        return item


class ContextEngine:
    """Main context management engine."""

    def __init__(self, budget: int = DEFAULT_BUDGET):
        self.budget = budget
        self.items: List[ContextItem] = []
        self.archived_items: List[ContextItem] = []
        self.load_state()

    def load_state(self):
        """Load context state from file if it exists."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                    self.items = [ContextItem.from_dict(item) for item in data.get("items", [])]
                    self.archived_items = [
                        ContextItem.from_dict(item) for item in data.get("archived", [])
                    ]
                    self.budget = data.get("budget", DEFAULT_BUDGET)
            except Exception as e:
                print(f"Warning: Could not load state: {e}")

    def save_state(self):
        """Save context state to file."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "budget": self.budget,
            "items": [item.to_dict() for item in self.items],
            "archived": [item.to_dict() for item in self.archived_items],
            "timestamp": datetime.now().isoformat(),
        }
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def add_item(
        self,
        source: str,
        content: str,
        category: str,
        priority: str,
    ):
        """Add a new item to context."""
        size_tokens = estimate_tokens(content)
        item = ContextItem(source, size_tokens, category, priority, content)
        self.items.append(item)
        self.save_state()
        print(f"✓ Added: {source} ({size_tokens} tokens, {priority} priority)")

    def score_items(self):
        """Score all items based on relevance formula."""
        now = datetime.now()

        for item in self.items:
            # Calculate hours elapsed since last access
            last_accessed = datetime.fromisoformat(item.last_accessed)
            hours_elapsed = (now - last_accessed).total_seconds() / 3600

            # Calculate factor scores
            recency = calculate_recency_score(hours_elapsed)
            frequency = calculate_frequency_score(item.access_count)
            task_alignment = calculate_task_alignment_score(
                item.priority in ["CRITICAL"], item.category in ["task"]
            )
            dependency = calculate_dependency_score(
                sum(1 for other in self.items if item.source in (other.content or ""))
            )

            # Calculate combined score
            item.relevance_score = calculate_relevance_score(
                recency, frequency, task_alignment, dependency
            )

        self.save_state()

    def get_category_usage(self) -> Dict[str, Tuple[int, int]]:
        """
        Get usage and budget for each category.
        Returns: {category: (used_tokens, budget_tokens)}
        """
        usage = {cat: 0 for cat in BUDGET_ALLOCATION}

        for item in self.items:
            usage[item.category] = usage.get(item.category, 0) + item.size_tokens

        budgets = {
            cat: int(self.budget * pct) for cat, pct in BUDGET_ALLOCATION.items()
        }

        return {cat: (usage.get(cat, 0), budgets[cat]) for cat in budgets}

    def get_total_usage(self) -> int:
        """Get total tokens used across all items."""
        return sum(item.size_tokens for item in self.items)

    def print_budget_report(self):
        """Print budget report with visual breakdown."""
        print("\n" + "=" * 70)
        print("CONTEXT BUDGET REPORT")
        print("=" * 70)

        category_usage = self.get_category_usage()
        total_used = self.get_total_usage()
        total_percent = (total_used / self.budget) * 100

        for category, (used, budget) in sorted(category_usage.items()):
            percent = (used / budget) * 100 if budget > 0 else 0
            bar_length = 20
            filled = int((percent / 100) * bar_length)
            bar = "▓" * filled + "░" * (bar_length - filled)

            # Determine alert level
            if percent >= ALERT_RED:
                alert = "🔴 RED"
            elif percent >= ALERT_ORANGE:
                alert = "🟠 ORANGE"
            elif percent >= ALERT_YELLOW:
                alert = "🟡 YELLOW"
            else:
                alert = "✓ OK"

            print(
                f"{category.upper():12} {used:6,} / {budget:6,}  ({percent:5.1f}%)  {bar}  {alert}"
            )

        print("-" * 70)
        print(f"{'TOTAL':12} {total_used:6,} / {self.budget:6,}  ({total_percent:5.1f}%)")
        print("=" * 70 + "\n")

        if total_percent >= ALERT_RED:
            print("🔴 CRITICAL: Context budget exceeded! Auto-prune recommended.\n")
        elif total_percent >= ALERT_ORANGE:
            print("🟠 WARNING: Context approaching budget limit.\n")

    def print_inventory(self):
        """Print detailed inventory report."""
        self.score_items()

        print("\n" + "=" * 90)
        print("CONTEXT INVENTORY")
        print("=" * 90)
        print(f"{'Tokens':>8} {'Score':>7} {'Category':>10} {'Priority':>10} {'Source':<45}")
        print("-" * 90)

        # Sort by score descending
        sorted_items = sorted(self.items, key=lambda x: x.relevance_score, reverse=True)

        for item in sorted_items:
            source_short = item.source[:42] + "..." if len(item.source) > 45 else item.source
            print(
                f"{item.size_tokens:8,} {item.relevance_score:7.1f} "
                f"{item.category:>10} {item.priority:>10} {source_short:<45}"
            )

        print("-" * 90)
        total_items = len(self.items)
        avg_score = (
            sum(item.relevance_score for item in self.items) / total_items
            if total_items > 0
            else 0
        )
        print(
            f"Total: {self.get_total_usage():,} tokens | Items: {total_items} | Avg Score: {avg_score:.1f}"
        )
        print("=" * 90 + "\n")

    def compress_item(self, item: ContextItem) -> int:
        """
        Attempt to compress an item, return tokens saved.
        Simple compression: strip comments, collapse whitespace.
        """
        original_size = item.size_tokens
        content = item.content

        # Strip comments (lines starting with # or //)
        lines = content.split("\n")
        filtered_lines = [
            line
            for line in lines
            if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("//")
        ]
        content = "\n".join(filtered_lines)

        # Remove extra blank lines
        while "\n\n\n" in content:
            content = content.replace("\n\n\n", "\n\n")

        item.content = content
        item.size_tokens = estimate_tokens(content)
        saved = original_size - item.size_tokens

        return max(0, saved)

    def auto_prune(self, target_percent: float = 85.0):
        """
        Auto-prune lowest-scoring items until usage is at target_percent.
        Never prunes CRITICAL priority items.
        """
        self.score_items()

        target_usage = int(self.budget * (target_percent / 100))
        current_usage = self.get_total_usage()

        if current_usage <= target_usage:
            print(f"✓ Context within budget ({current_usage:,} / {self.budget:,})")
            return

        print(f"\n🔄 Optimizing context: {current_usage:,} → {target_usage:,} tokens")
        print("-" * 70)

        # Sort by score, excluding CRITICAL items
        prunable_items = [item for item in self.items if item.priority != "CRITICAL"]
        prunable_items.sort(key=lambda x: x.relevance_score)

        pruned_count = 0
        compressed_count = 0

        for item in prunable_items:
            if self.get_total_usage() <= target_usage:
                break

            # Try compression first
            saved = self.compress_item(item)
            if saved > 0:
                print(f"  ✓ Compressed: {item.source} (saved {saved:,} tokens)")
                compressed_count += 1
            else:
                # If compression didn't help, archive the item
                self.archived_items.append(item)
                self.items.remove(item)
                print(f"  📦 Archived: {item.source} ({item.size_tokens:,} tokens)")
                pruned_count += 1

        print("-" * 70)
        print(f"Result: {pruned_count} pruned, {compressed_count} compressed")
        print(f"Final usage: {self.get_total_usage():,} / {self.budget:,} tokens")
        print()

        self.save_state()

    def export_json(self, output_file: str):
        """Export current context state as JSON."""
        self.score_items()

        data = {
            "timestamp": datetime.now().isoformat(),
            "budget": self.budget,
            "usage": {
                "total": self.get_total_usage(),
                "percent": (self.get_total_usage() / self.budget) * 100,
            },
            "categories": self.get_category_usage(),
            "items": [item.to_dict() for item in sorted(
                self.items, key=lambda x: x.relevance_score, reverse=True
            )],
            "archived": [item.to_dict() for item in self.archived_items],
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Exported to {output_file}")


def main():
    """CLI interface for context engine."""
    parser = argparse.ArgumentParser(
        description="Context Engineer: Token-optimized context management"
    )
    parser.add_argument(
        "command",
        choices=["add", "score", "prune", "budget", "inventory", "optimize", "export"],
        help="Command to execute",
    )
    parser.add_argument("--source", help="Source file or identifier for add command")
    parser.add_argument("--content", help="Content to add (or read from stdin if not provided)")
    parser.add_argument("--category", default="reference", help="Category for add command")
    parser.add_argument("--priority", default="NORMAL", help="Priority level for add command")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET, help="Token budget")
    parser.add_argument("--target", type=float, default=85.0, help="Target usage percent for optimize")
    parser.add_argument("--output", help="Output file for export command")

    args = parser.parse_args()
    engine = ContextEngine(args.budget)

    if args.command == "add":
        if not args.source:
            print("Error: --source required for add command")
            sys.exit(1)

        content = args.content
        if not content:
            print("Enter content (Ctrl+D to finish):")
            content = sys.stdin.read()

        if not content:
            print("Error: No content provided")
            sys.exit(1)

        engine.add_item(args.source, content, args.category, args.priority)

    elif args.command == "score":
        engine.score_items()
        engine.print_inventory()

    elif args.command == "prune":
        engine.auto_prune(args.target)

    elif args.command == "budget":
        engine.print_budget_report()

    elif args.command == "inventory":
        engine.print_inventory()

    elif args.command == "optimize":
        engine.print_budget_report()
        engine.auto_prune(args.target)
        engine.print_budget_report()

    elif args.command == "export":
        if not args.output:
            args.output = "context_state.json"
        engine.export_json(args.output)


if __name__ == "__main__":
    main()
