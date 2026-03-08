"""Tests for the history tracker."""

import json

from productivity_framework.tracker import Tracker
from productivity_framework.types import ActivityType, ClassificationResult


def _make_result(
    conv_id: str = "test",
    activity: ActivityType = ActivityType.WORK_CREATION,
    time_saved: int = 900,
    outputs: list[str] | None = None,
) -> ClassificationResult:
    return ClassificationResult(
        conversation_id=conv_id,
        overall_activity=activity,
        confidence=0.85,
        classifier_layer=2,
        time_saved_seconds=time_saved,
        time_saved_low=time_saved // 2,
        time_saved_high=time_saved * 2,
        outputs=outputs or ["code"],
    )


class TestTracker:
    def test_log_creates_file(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        result = _make_result()
        tracker.log(result)

        assert tracker.history_path.exists()
        lines = tracker.history_path.read_text().strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["conversation_id"] == "test"
        assert entry["overall_activity"] == "work_creation"
        assert entry["time_saved_minutes"] == 15.0
        assert "timestamp" in entry
        assert "date" in entry

    def test_log_appends(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        tracker.log(_make_result(conv_id="a"))
        tracker.log(_make_result(conv_id="b"))
        tracker.log(_make_result(conv_id="c"))

        lines = tracker.history_path.read_text().strip().split("\n")
        assert len(lines) == 3

    def test_log_batch(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        results = [_make_result(conv_id=f"conv-{i}") for i in range(5)]
        count = tracker.log_batch(results)

        assert count == 5
        lines = tracker.history_path.read_text().strip().split("\n")
        assert len(lines) == 5

    def test_summary_empty(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        s = tracker.summary(period="all")

        assert s["total_conversations"] == 0
        assert s["productive_conversations"] == 0
        assert s["total_time_saved_minutes"] == 0

    def test_summary_all(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        tracker.log(_make_result(conv_id="a", time_saved=600))  # 10 min
        tracker.log(_make_result(conv_id="b", time_saved=900))  # 15 min
        tracker.log(
            _make_result(
                conv_id="c",
                activity=ActivityType.CASUAL,
                time_saved=0,
                outputs=[],
            )
        )

        s = tracker.summary(period="all")
        assert s["total_conversations"] == 3
        assert s["productive_conversations"] == 2
        assert s["total_time_saved_minutes"] == 25.0
        assert s["by_activity"]["work_creation"] == 25.0
        assert s["by_activity"]["casual"] == 0

    def test_summary_by_output(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        tracker.log(_make_result(outputs=["code"], time_saved=900))
        tracker.log(_make_result(outputs=["email"], time_saved=300))
        tracker.log(_make_result(outputs=["code"], time_saved=600))

        s = tracker.summary(period="all")
        assert s["by_output"]["code"] == 25.0  # 15 + 10
        assert s["by_output"]["email"] == 5.0

    def test_clear(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        tracker.log(_make_result())
        tracker.log(_make_result())

        count = tracker.clear()
        assert count == 2
        assert not tracker.history_path.exists()

        s = tracker.summary(period="all")
        assert s["total_conversations"] == 0

    def test_compare_empty(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        data = tracker.compare()

        assert data["this_week"]["total_conversations"] == 0
        assert data["last_week"]["total_conversations"] == 0

    def test_summary_today_filter(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))

        # Log a result (will have today's date)
        tracker.log(_make_result(conv_id="today"))

        # Manually add an old entry
        old_entry = {
            "timestamp": "2025-01-01T10:00:00",
            "date": "2025-01-01",
            "conversation_id": "old",
            "overall_activity": "work_creation",
            "time_saved_minutes": 10.0,
            "time_saved_seconds": 600,
            "outputs": ["code"],
        }
        with open(tracker.history_path, "a") as f:
            f.write(json.dumps(old_entry) + "\n")

        # "all" should see both
        s_all = tracker.summary(period="all")
        assert s_all["total_conversations"] == 2

        # "today" should only see today's entry
        s_today = tracker.summary(period="today")
        assert s_today["total_conversations"] == 1
        assert s_today["total_time_saved_minutes"] == 15.0

    def test_productivity_rate(self, tmp_path):
        tracker = Tracker(history_dir=str(tmp_path))
        tracker.log(_make_result(activity=ActivityType.WORK_CREATION))
        tracker.log(_make_result(activity=ActivityType.WORK_RESEARCH))
        tracker.log(_make_result(activity=ActivityType.CASUAL, time_saved=0))
        tracker.log(_make_result(activity=ActivityType.CASUAL, time_saved=0))

        s = tracker.summary(period="all")
        assert s["productivity_rate"] == 0.5

    def test_creates_directory(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        tracker = Tracker(history_dir=str(nested))
        tracker.log(_make_result())
        assert nested.exists()
        assert tracker.history_path.exists()
