"""Tests for Layer 1: Signal Extraction."""

import pytest
from productivity_framework.types import ConversationMessage
from productivity_framework.signals import extract_signals


def _msg(role, content, tool_calls=None):
    return ConversationMessage(
        role=role,
        content=content,
        tool_calls=tool_calls or [],
        timestamp=1000.0,
    )


class TestSignalExtraction:
    def test_empty_messages(self):
        signal = extract_signals([])
        assert signal.message_count == 0
        assert signal.tool_call_count == 0

    def test_basic_counts(self):
        messages = [
            _msg("user", "Hello"),
            _msg("assistant", "Hi there! How can I help?"),
            _msg("user", "Write me an email"),
            _msg("assistant", "Sure, here's a draft..."),
        ]
        signal = extract_signals(messages)
        assert signal.message_count == 4
        assert signal.user_message_count == 2
        assert signal.assistant_message_count == 2

    def test_tool_calls_detected(self):
        messages = [
            _msg("user", "Send an email to john"),
            _msg("assistant", "Done!", tool_calls=["send_email", "gmail_send"]),
        ]
        signal = extract_signals(messages)
        assert signal.tool_call_count == 2
        assert "send_email" in signal.tool_calls

    def test_external_actions_detected(self):
        messages = [
            _msg("user", "Post this on slack"),
            _msg("assistant", "Posted!", tool_calls=["slack_send"]),
        ]
        signal = extract_signals(messages)
        assert len(signal.external_actions) == 1
        assert "slack_send" in signal.external_actions

    def test_artifacts_detected(self):
        messages = [
            _msg("user", "Create a spreadsheet"),
            _msg("assistant", "Created!", tool_calls=["google_sheets_create"]),
        ]
        signal = extract_signals(messages)
        assert len(signal.artifacts_produced) == 1

    def test_structured_output_code_blocks(self):
        messages = [
            _msg("user", "Write a function"),
            _msg("assistant", "Here:\n```python\ndef foo():\n    pass\n```"),
        ]
        signal = extract_signals(messages)
        assert signal.has_code_blocks is True
        assert signal.has_structured_output is True

    def test_structured_output_tables(self):
        messages = [
            _msg("user", "Show me the data"),
            _msg("assistant", "| Name | Value |\n| A | 1 |\n| B | 2 |"),
        ]
        signal = extract_signals(messages)
        assert signal.has_tables is True
        assert signal.has_structured_output is True

    def test_domain_keywords(self):
        messages = [
            _msg("user", "What's our revenue forecast for Q3?"),
            _msg("assistant", "Based on the EBITDA margin and cash flow analysis..."),
        ]
        signal = extract_signals(messages)
        assert "finance" in signal.domain_keywords
        assert signal.domain_keywords["finance"] >= 2

    def test_refinement_detection(self):
        messages = [
            _msg("user", "Write an email"),
            _msg("assistant", "Here's a draft..."),
            _msg("user", "Make it shorter and more detailed"),
            _msg("assistant", "Here's the revised version..."),
        ]
        signal = extract_signals(messages)
        assert signal.user_refinement_count >= 1

    def test_no_false_positive_refinement(self):
        messages = [
            _msg("user", "Hello"),
            _msg("assistant", "Hi!"),
            _msg("user", "What time is it?"),
            _msg("assistant", "I can't tell time."),
        ]
        signal = extract_signals(messages)
        assert signal.user_refinement_count == 0

    def test_token_estimation(self):
        messages = [
            _msg("user", "Write a function"),  # ~4 words = ~16 chars
            _msg("assistant", "Here is a longer response with some content to count tokens for"),
        ]
        signal = extract_signals(messages)
        assert signal.total_input_tokens > 0
        assert signal.total_output_tokens > 0
        assert signal.total_tokens == signal.total_input_tokens + signal.total_output_tokens

    def test_explicit_token_counts(self):
        messages = [
            ConversationMessage(role="user", content="Hello", token_count=50),
            ConversationMessage(role="assistant", content="Hi there", token_count=200, timestamp=1000.0),
        ]
        signal = extract_signals(messages)
        assert signal.total_input_tokens == 50
        assert signal.total_output_tokens == 200

    def test_code_vs_prose_tokens(self):
        messages = [
            _msg("user", "Write code"),
            _msg("assistant", "Here is some explanation text.\n```python\ndef hello():\n    print('hello world')\n    return True\n```\nThat should work."),
        ]
        signal = extract_signals(messages)
        assert signal.code_output_tokens > 0
        assert signal.prose_output_tokens > 0
        assert signal.code_output_tokens + signal.prose_output_tokens == signal.total_output_tokens

    def test_output_tokens_per_message(self):
        messages = [
            _msg("user", "Q1"),
            _msg("assistant", "Answer one with some content"),
            _msg("user", "Q2"),
            _msg("assistant", "Answer two with more content"),
        ]
        signal = extract_signals(messages)
        assert signal.output_tokens_per_message > 0
        assert signal.output_tokens_per_message == signal.total_output_tokens / 2
