"""Tests for Layer 2: Rule Engine."""

from productivity_framework.rules import apply_rules
from productivity_framework.types import ActivityType, OutputType, Signal


class TestRuleEngine:
    def test_external_action_rule(self):
        signal = Signal(
            external_actions=["send_email"],
            tool_calls=["send_email"],
            tool_call_count=1,
            message_count=4,
        )
        result = apply_rules(signal)
        assert result.matched is True
        assert result.activity_type == ActivityType.WORK_SUPPORT
        assert result.output_type == OutputType.EMAIL
        assert result.confidence >= 0.90

    def test_artifact_created_rule(self):
        signal = Signal(
            artifacts_produced=["google_docs_create"],
            tool_calls=["google_docs_create"],
            tool_call_count=1,
            message_count=4,
        )
        result = apply_rules(signal)
        assert result.matched is True
        assert result.activity_type == ActivityType.WORK_CREATION
        assert result.confidence >= 0.85

    def test_code_generation_rule(self):
        signal = Signal(
            has_code_blocks=True,
            has_structured_output=True,
            longest_assistant_response_words=200,
            assistant_total_words=400,
            domain_keywords={"engineering": 2},
            message_count=4,
        )
        result = apply_rules(signal)
        assert result.matched is True
        assert result.output_type == OutputType.CODE

    def test_research_heavy_rule(self):
        signal = Signal(
            domain_keywords={"finance": 3, "sales": 1},
            assistant_total_words=1000,
            has_structured_output=True,
            message_count=6,
        )
        result = apply_rules(signal)
        assert result.matched is True
        assert result.activity_type == ActivityType.WORK_RESEARCH

    def test_extended_no_output_casual(self):
        signal = Signal(
            message_count=8,
            tool_call_count=0,
            artifacts_produced=[],
            has_structured_output=False,
            domain_keywords={},
            assistant_total_words=200,
        )
        result = apply_rules(signal)
        assert result.matched is True
        assert result.activity_type == ActivityType.CASUAL

    def test_ambiguous_goes_to_layer3(self):
        signal = Signal(
            message_count=3,
            tool_call_count=0,
            assistant_total_words=150,
        )
        result = apply_rules(signal)
        assert result.matched is False

    def test_substantial_structured_output(self):
        signal = Signal(
            has_structured_output=True,
            assistant_total_words=600,
            user_refinement_count=2,
            message_count=6,
        )
        result = apply_rules(signal)
        assert result.matched is True
        assert result.activity_type == ActivityType.WORK_CREATION
        assert result.confidence >= 0.80
