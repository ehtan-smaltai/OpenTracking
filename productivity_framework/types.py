"""Data models for the productivity measurement framework."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any


class ActivityType(str, enum.Enum):
    """What kind of activity was this conversation segment?"""

    WORK_CREATION = "work_creation"      # Produced a deliverable
    WORK_RESEARCH = "work_research"      # Research/analysis for work
    WORK_SUPPORT = "work_support"        # Helped with a work process
    LEARNING = "learning"                # Educational, skill-building
    PERSONAL_PRODUCTIVE = "personal_productive"  # Personal but useful
    CASUAL = "casual"                    # Social, entertainment, testing


class OutputType(str, enum.Enum):
    """What was produced?"""

    DOCUMENT = "document"
    EMAIL = "email"
    CODE = "code"
    SPREADSHEET = "spreadsheet"
    ANALYSIS = "analysis"
    PLAN = "plan"
    SOCIAL_MEDIA_POST = "social_media_post"
    PRESENTATION = "presentation"
    SUMMARY = "summary"
    ACTION_EXECUTED = "action_executed"
    QUICK_ANSWER = "quick_answer"
    NONE = "none"


@dataclass
class ConversationMessage:
    """A single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float = 0.0
    tool_calls: list[str] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    token_count: int = 0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class Signal:
    """Extracted features from a conversation. Layer 1 output."""

    tool_calls: list[str] = field(default_factory=list)
    tool_call_count: int = 0
    artifacts_produced: list[str] = field(default_factory=list)
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    user_message_avg_words: float = 0.0
    assistant_total_words: int = 0
    has_structured_output: bool = False
    external_actions: list[str] = field(default_factory=list)
    domain_keywords: dict[str, int] = field(default_factory=dict)
    conversation_duration_seconds: float = 0.0
    user_refinement_count: int = 0
    longest_assistant_response_words: int = 0
    has_code_blocks: bool = False
    has_tables: bool = False
    has_lists: bool = False
    # Token-based output metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    output_tokens_per_message: float = 0.0
    code_output_tokens: int = 0
    prose_output_tokens: int = 0


@dataclass
class Segment:
    """A classified segment of a conversation."""

    message_range: tuple[int, int] = (0, 0)
    activity_type: ActivityType = ActivityType.CASUAL
    output_type: OutputType = OutputType.NONE
    confidence: float = 0.0
    classifier_layer: int = 0  # 1, 2, or 3
    time_saved_seconds: int = 0
    time_saved_low: int = 0
    time_saved_high: int = 0


@dataclass
class ClassificationResult:
    """Final output of the classification pipeline."""

    conversation_id: str = ""
    overall_activity: ActivityType = ActivityType.CASUAL
    confidence: float = 0.0
    classifier_layer: int = 0
    segments: list[Segment] = field(default_factory=list)
    time_saved_seconds: int = 0
    time_saved_low: int = 0
    time_saved_high: int = 0
    outputs: list[str] = field(default_factory=list)
    actions_performed: list[str] = field(default_factory=list)
    classification_cost_tokens: int = 0
    # Token-based work output
    total_output_tokens: int = 0
    total_input_tokens: int = 0
    code_output_tokens: int = 0
    prose_output_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "conversation_id": self.conversation_id,
            "overall_activity": self.overall_activity.value,
            "confidence": round(self.confidence, 2),
            "classifier_layer": self.classifier_layer,
            "segments": [
                {
                    "message_range": list(seg.message_range),
                    "activity_type": seg.activity_type.value,
                    "output_type": seg.output_type.value,
                    "confidence": round(seg.confidence, 2),
                    "time_saved_seconds": seg.time_saved_seconds,
                    "time_saved_range": [seg.time_saved_low, seg.time_saved_high],
                }
                for seg in self.segments
            ],
            "time_saved_seconds": self.time_saved_seconds,
            "time_saved_range": [self.time_saved_low, self.time_saved_high],
            "outputs": self.outputs,
            "actions_performed": self.actions_performed,
            "classification_cost_tokens": self.classification_cost_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_input_tokens": self.total_input_tokens,
            "code_output_tokens": self.code_output_tokens,
            "prose_output_tokens": self.prose_output_tokens,
        }

    @property
    def time_saved_minutes(self) -> float:
        """Time saved as minutes (convenience)."""
        return round(self.time_saved_seconds / 60, 1)

    @property
    def time_saved_display(self) -> str:
        """Human-readable time saved string."""
        low_min = self.time_saved_low // 60
        high_min = self.time_saved_high // 60
        mid_min = self.time_saved_seconds // 60
        if mid_min == 0:
            return "< 1 min"
        if low_min == high_min:
            return f"~{mid_min} min"
        return f"~{mid_min} min ({low_min}-{high_min} min range)"
