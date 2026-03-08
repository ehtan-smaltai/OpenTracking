"""Tests for the main classifier pipeline."""

import pytest
from productivity_framework.types import ConversationMessage, ActivityType, OutputType
from productivity_framework.classifier import ProductivityClassifier


def _msg(role, content, tool_calls=None):
    return ConversationMessage(
        role=role,
        content=content,
        tool_calls=tool_calls or [],
        timestamp=1000.0,
    )


class TestProductivityClassifier:
    def setup_method(self):
        # No API key = rules-only mode
        self.classifier = ProductivityClassifier(
            api_key=None,
            estimate_mode="low",
        )

    def test_email_sent_classified_productive(self):
        messages = [
            _msg("user", "Send an email to the team about the project update"),
            _msg("assistant", "I've sent the email.", tool_calls=["send_email"]),
        ]
        result = self.classifier.classify(messages, "test-1")
        assert result.overall_activity == ActivityType.WORK_SUPPORT
        assert result.time_saved_seconds > 0
        assert result.classifier_layer == 2

    def test_document_creation(self):
        messages = [
            _msg("user", "Create a project proposal document"),
            _msg("assistant", "Creating the document now...", tool_calls=["google_docs_create"]),
            _msg("user", "Make the introduction shorter"),
            _msg("assistant", "Updated!"),
        ]
        result = self.classifier.classify(messages, "test-2")
        assert result.overall_activity == ActivityType.WORK_CREATION
        assert result.time_saved_seconds > 0
        assert "document" in result.outputs or len(result.outputs) > 0

    def test_casual_conversation(self):
        messages = [
            _msg("user", "Hey"),
            _msg("assistant", "Hello! How are you?"),
            _msg("user", "I'm good, just bored"),
            _msg("assistant", "I see! Anything I can help with?"),
            _msg("user", "Nah just chatting"),
            _msg("assistant", "Sure, happy to chat!"),
            _msg("user", "Tell me a joke"),
            _msg("assistant", "Why did the chicken cross the road?"),
        ]
        result = self.classifier.classify(messages, "test-3")
        assert result.overall_activity == ActivityType.CASUAL
        assert result.time_saved_seconds == 0

    def test_ambiguous_without_llm_defaults_casual(self):
        messages = [
            _msg("user", "What's the capital of France?"),
            _msg("assistant", "Paris."),
        ]
        result = self.classifier.classify(messages, "test-4")
        # Without LLM fallback, ambiguous cases default to casual
        assert result.overall_activity == ActivityType.CASUAL
        assert result.confidence <= 0.5

    def test_time_saved_display(self):
        messages = [
            _msg("user", "Send the report to the client"),
            _msg("assistant", "Email sent!", tool_calls=["send_email"]),
        ]
        result = self.classifier.classify(messages, "test-5")
        display = result.time_saved_display
        assert "min" in display

    def test_to_dict(self):
        messages = [
            _msg("user", "Create a spreadsheet"),
            _msg("assistant", "Done!", tool_calls=["google_sheets_create"]),
        ]
        result = self.classifier.classify(messages, "test-6")
        d = result.to_dict()
        assert "conversation_id" in d
        assert "time_saved_seconds" in d
        assert "time_saved_range" in d
        assert "segments" in d
        assert isinstance(d["segments"], list)
        assert "total_output_tokens" in d
        assert "code_output_tokens" in d

    def test_token_metrics_propagated(self):
        messages = [
            _msg("user", "Send an email to the team about the project update"),
            _msg("assistant", "I've drafted and sent the email with the project status.", tool_calls=["send_email"]),
        ]
        result = self.classifier.classify(messages, "token-test")
        assert result.total_output_tokens > 0
        assert result.total_input_tokens > 0
        assert result.prose_output_tokens > 0

    def test_batch_classification(self):
        conv1 = ("c1", [
            _msg("user", "Send email"),
            _msg("assistant", "Sent!", tool_calls=["send_email"]),
        ])
        conv2 = ("c2", [
            _msg("user", "Hey"),
            _msg("assistant", "Hi!"),
            _msg("user", "Just testing"),
            _msg("assistant", "Ok!"),
            _msg("user", "Yep"),
            _msg("assistant", "Sure"),
            _msg("user", "Bye"),
            _msg("assistant", "Goodbye!"),
        ])
        results = self.classifier.classify_batch([conv1, conv2])
        assert len(results) == 2

    def test_aggregate_time_saved(self):
        conversations = [
            ("c1", [
                _msg("user", "Send email"),
                _msg("assistant", "Sent!", tool_calls=["send_email"]),
            ]),
            ("c2", [
                _msg("user", "Create doc"),
                _msg("assistant", "Created!", tool_calls=["create_doc"]),
            ]),
            ("c3", [
                _msg("user", "Hey"),
                _msg("assistant", "Hi!"),
                _msg("user", "Just chatting"),
                _msg("assistant", "Ok!"),
                _msg("user", "Yep"),
                _msg("assistant", "Sure"),
                _msg("user", "Bye"),
                _msg("assistant", "Goodbye!"),
            ]),
        ]
        results = self.classifier.classify_batch(conversations)
        summary = self.classifier.aggregate_time_saved(results)

        assert summary["total_conversations"] == 3
        assert summary["productive_conversations"] == 2
        assert summary["total_time_saved_seconds"] > 0
        assert "by_activity" in summary
        assert "by_output" in summary
        assert "total_output_tokens" in summary
        assert summary["total_output_tokens"] > 0
        assert summary["avg_output_tokens_per_conversation"] > 0

    def test_empty_conversation(self):
        result = self.classifier.classify([], "empty")
        assert result.time_saved_seconds == 0
        assert result.overall_activity == ActivityType.CASUAL
