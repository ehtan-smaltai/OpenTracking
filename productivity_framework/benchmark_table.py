"""
Benchmark Table

Maps output types to human time estimates.
Loads defaults from YAML, allows user overrides.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .types import OutputType


@dataclass
class TimeBenchmark:
    """Time estimate for a task type."""

    low: int = 0  # seconds
    mid: int = 0  # seconds
    high: int = 0  # seconds
    description: str = ""


# Default YAML path
_DEFAULTS_PATH = Path(__file__).parent / "benchmarks" / "defaults.yaml"


class BenchmarkTable:
    """
    Manages time-saved benchmarks for different task types.

    Loads defaults from YAML. Supports per-org and per-user overrides.
    """

    def __init__(
        self,
        defaults_path: str | Path | None = None,
        estimate_mode: str = "low",
        overrides: dict[str, dict[str, int]] | None = None,
    ):
        """
        Args:
            defaults_path: Path to defaults YAML. Uses built-in if None.
            estimate_mode: Which estimate to use as default: "low", "mid", "high".
            overrides: Dict of {task_name: {low, mid, high}} to override defaults.
        """
        self.estimate_mode = estimate_mode
        self._benchmarks: dict[str, TimeBenchmark] = {}
        self._tool_mappings: dict[str, str] = {}

        path = Path(defaults_path) if defaults_path else _DEFAULTS_PATH
        self._load_defaults(path)

        if overrides:
            self._apply_overrides(overrides)

    def _load_defaults(self, path: Path) -> None:
        """Load benchmarks from YAML file."""
        if not path.exists():
            return

        with open(path) as f:
            data = yaml.safe_load(f)

        if not data:
            return

        # Load tasks
        tasks = data.get("tasks", {})
        for task_name, task_data in tasks.items():
            self._benchmarks[task_name] = TimeBenchmark(
                low=task_data.get("low", 0),
                mid=task_data.get("mid", 0),
                high=task_data.get("high", 0),
                description=task_data.get("description", ""),
            )

        # Load tool mappings
        self._tool_mappings = data.get("tool_mappings", {})

        # Load default estimate mode from YAML if not overridden
        default_mode = data.get("default_estimate")
        if default_mode and self.estimate_mode == "low":
            self.estimate_mode = default_mode

    def _apply_overrides(self, overrides: dict[str, dict[str, int]]) -> None:
        """Apply user/org overrides to benchmarks."""
        for task_name, values in overrides.items():
            if task_name in self._benchmarks:
                bm = self._benchmarks[task_name]
                bm.low = values.get("low", bm.low)
                bm.mid = values.get("mid", bm.mid)
                bm.high = values.get("high", bm.high)
            else:
                self._benchmarks[task_name] = TimeBenchmark(
                    low=values.get("low", 0),
                    mid=values.get("mid", 0),
                    high=values.get("high", 0),
                )

    def get_benchmark(self, task_name: str) -> TimeBenchmark | None:
        """Get the benchmark for a specific task."""
        return self._benchmarks.get(task_name)

    def get_time_for_output(self, output_type: OutputType) -> tuple[int, int, int]:
        """
        Get (low, mid, high) seconds for an output type.

        Maps OutputType enum to the closest benchmark entry.
        """
        output_to_task = {
            OutputType.EMAIL: "email_draft",
            OutputType.DOCUMENT: "document_creation",
            OutputType.CODE: "code_snippet",
            OutputType.SPREADSHEET: "spreadsheet_creation",
            OutputType.ANALYSIS: "data_analysis",
            OutputType.PLAN: "task_planning",
            OutputType.SOCIAL_MEDIA_POST: "social_media_post",
            OutputType.PRESENTATION: "presentation_creation",
            OutputType.SUMMARY: "summarization",
            OutputType.ACTION_EXECUTED: "action_executed",
            OutputType.QUICK_ANSWER: "quick_answer",
            OutputType.NONE: None,
        }

        task_name = output_to_task.get(output_type)
        if not task_name:
            return (0, 0, 0)

        bm = self._benchmarks.get(task_name)
        if not bm:
            return (0, 0, 0)

        return (bm.low, bm.mid, bm.high)

    def get_default_time(self, output_type: OutputType) -> int:
        """Get the default time estimate (based on estimate_mode) for an output type."""
        low, mid, high = self.get_time_for_output(output_type)
        if self.estimate_mode == "high":
            return high
        elif self.estimate_mode == "mid":
            return mid
        return low

    def get_task_for_tool(self, tool_name: str) -> str | None:
        """Map a tool name to a task type using tool_mappings."""
        tool_lower = tool_name.lower()
        for pattern, task in self._tool_mappings.items():
            if pattern in tool_lower:
                return task
        return None

    def list_benchmarks(self) -> dict[str, dict[str, Any]]:
        """List all benchmarks as a dict (for debugging/display)."""
        return {
            name: {
                "low_min": bm.low // 60,
                "mid_min": bm.mid // 60,
                "high_min": bm.high // 60,
                "description": bm.description,
            }
            for name, bm in self._benchmarks.items()
        }
