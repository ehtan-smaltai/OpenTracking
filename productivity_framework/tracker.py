"""
Lightweight JSON-file-based history tracker.

Appends classification results with timestamps to a local JSON Lines file.
Provides summary queries over the stored history (today, this week, this month, all time).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .types import ClassificationResult

DEFAULT_HISTORY_DIR = os.path.expanduser("~/.ai-productivity")
DEFAULT_HISTORY_FILE = "history.jsonl"


class Tracker:
    """Append-only JSON Lines history tracker for productivity results."""

    def __init__(self, history_dir: str | None = None):
        self._dir = Path(history_dir or DEFAULT_HISTORY_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / DEFAULT_HISTORY_FILE

    @property
    def history_path(self) -> Path:
        return self._file

    def log(self, result: ClassificationResult) -> dict[str, Any]:
        """Append a classification result to history. Returns the stored entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            **result.to_dict(),
            "time_saved_minutes": result.time_saved_minutes,
            "time_saved_display": result.time_saved_display,
        }
        with open(self._file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def log_batch(self, results: list[ClassificationResult]) -> int:
        """Append multiple results. Returns count logged."""
        for r in results:
            self.log(r)
        return len(results)

    def _load_entries(self) -> list[dict[str, Any]]:
        """Load all entries from history file."""
        if not self._file.exists():
            return []
        entries = []
        with open(self._file) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def _filter_by_date(
        self, entries: list[dict], start: datetime, end: datetime | None = None,
    ) -> list[dict]:
        """Filter entries by date range."""
        end = end or datetime.now()
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        return [
            e for e in entries
            if start_str <= e.get("date", "") <= end_str
        ]

    def summary(
        self, period: str = "week",
    ) -> dict[str, Any]:
        """
        Summarize productivity history for a given period.

        Args:
            period: "today", "week", "month", "all"

        Returns:
            Dict with total_conversations, productive_conversations,
            productivity_rate, total_time_saved_minutes, by_activity, by_output.
        """
        entries = self._load_entries()
        now = datetime.now()

        if period == "today":
            entries = self._filter_by_date(entries, now)
        elif period == "week":
            start = now - timedelta(days=now.weekday())  # Monday
            entries = self._filter_by_date(entries, start)
        elif period == "month":
            start = now.replace(day=1)
            entries = self._filter_by_date(entries, start)
        # "all" = no filter

        return self._aggregate(entries, period)

    def compare(self) -> dict[str, Any]:
        """Compare this week vs last week."""
        entries = self._load_entries()
        now = datetime.now()

        # This week (Monday to now)
        this_week_start = now - timedelta(days=now.weekday())
        this_week = self._filter_by_date(entries, this_week_start)

        # Last week (previous Monday to previous Sunday)
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start - timedelta(days=1)
        last_week = self._filter_by_date(entries, last_week_start, last_week_end)

        return {
            "this_week": self._aggregate(this_week, "this_week"),
            "last_week": self._aggregate(last_week, "last_week"),
        }

    def _aggregate(self, entries: list[dict], period: str) -> dict[str, Any]:
        """Aggregate a list of history entries into a summary."""
        casual_types = {"casual"}
        productive = [
            e for e in entries
            if e.get("overall_activity") not in casual_types
        ]

        total_saved = sum(e.get("time_saved_minutes", 0) for e in entries)

        by_activity: dict[str, float] = {}
        for e in entries:
            act = e.get("overall_activity", "unknown")
            by_activity[act] = by_activity.get(act, 0) + e.get("time_saved_minutes", 0)

        by_output: dict[str, float] = {}
        for e in entries:
            for out in e.get("outputs", []):
                by_output[out] = by_output.get(out, 0) + e.get("time_saved_minutes", 0)

        # Date range
        dates = sorted(set(e.get("date", "") for e in entries))

        return {
            "period": period,
            "date_range": [dates[0], dates[-1]] if dates else [],
            "total_conversations": len(entries),
            "productive_conversations": len(productive),
            "productivity_rate": len(productive) / len(entries) if entries else 0,
            "total_time_saved_minutes": round(total_saved, 1),
            "total_time_saved_hours": round(total_saved / 60, 1),
            "by_activity": by_activity,
            "by_output": by_output,
        }

    def clear(self) -> int:
        """Clear all history. Returns count of entries deleted."""
        entries = self._load_entries()
        count = len(entries)
        if self._file.exists():
            self._file.unlink()
        return count
