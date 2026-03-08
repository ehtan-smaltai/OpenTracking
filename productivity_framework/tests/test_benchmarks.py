"""Tests for the benchmark table."""

import pytest
from productivity_framework.types import OutputType
from productivity_framework.benchmark_table import BenchmarkTable


class TestBenchmarkTable:
    def setup_method(self):
        self.table = BenchmarkTable(estimate_mode="low")

    def test_loads_defaults(self):
        bm = self.table.get_benchmark("email_draft")
        assert bm is not None
        assert bm.low > 0
        assert bm.mid > bm.low
        assert bm.high > bm.mid

    def test_get_time_for_output(self):
        low, mid, high = self.table.get_time_for_output(OutputType.EMAIL)
        assert low == 180   # 3 min
        assert mid == 420   # 7 min
        assert high == 900  # 15 min

    def test_get_default_time_low(self):
        table = BenchmarkTable(estimate_mode="low")
        t = table.get_default_time(OutputType.EMAIL)
        assert t == 180

    def test_get_default_time_mid(self):
        table = BenchmarkTable(estimate_mode="mid")
        t = table.get_default_time(OutputType.EMAIL)
        assert t == 420

    def test_get_default_time_high(self):
        table = BenchmarkTable(estimate_mode="high")
        t = table.get_default_time(OutputType.EMAIL)
        assert t == 900

    def test_none_output_returns_zero(self):
        low, mid, high = self.table.get_time_for_output(OutputType.NONE)
        assert low == 0
        assert mid == 0
        assert high == 0

    def test_tool_mapping(self):
        task = self.table.get_task_for_tool("gmail_send_message")
        assert task == "email_draft"

    def test_overrides(self):
        table = BenchmarkTable(
            overrides={
                "email_draft": {"low": 60, "mid": 120, "high": 240},
            }
        )
        bm = table.get_benchmark("email_draft")
        assert bm.low == 60
        assert bm.mid == 120

    def test_list_benchmarks(self):
        listing = self.table.list_benchmarks()
        assert "email_draft" in listing
        assert "mid_min" in listing["email_draft"]
