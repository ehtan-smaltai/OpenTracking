"""
Basic usage example for the AI Productivity Measurement Framework.

No API key needed — runs entirely with the rule engine (Layer 1 + 2).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from productivity_framework import ProductivityClassifier, ConversationMessage


def main():
    # Initialize classifier (no API key = rules-only mode)
    classifier = ProductivityClassifier(estimate_mode="low")

    # --- Example 1: Email sent ---
    print("=" * 50)
    print("Example 1: Email Sent")
    print("=" * 50)

    messages = [
        ConversationMessage(
            role="user",
            content="Draft an email to the marketing team about the Q3 campaign results",
        ),
        ConversationMessage(
            role="assistant",
            content="Here's a draft email summarizing the Q3 campaign performance...",
            tool_calls=["send_email"],
        ),
    ]

    result = classifier.classify(messages, "email-example")
    print(f"Activity: {result.overall_activity.value}")
    print(f"Time saved: {result.time_saved_display}")
    print(f"Confidence: {result.confidence}")
    print(f"Classifier layer: {result.classifier_layer}")
    print(f"Outputs: {result.outputs}")
    print(f"Output tokens: {result.total_output_tokens}")
    print(f"  Code tokens: {result.code_output_tokens}")
    print(f"  Prose tokens: {result.prose_output_tokens}")
    print()

    # --- Example 2: Document creation ---
    print("=" * 50)
    print("Example 2: Document Creation")
    print("=" * 50)

    messages = [
        ConversationMessage(
            role="user",
            content="Create a project proposal for the new CRM integration",
        ),
        ConversationMessage(
            role="assistant",
            content="I'll create the project proposal now...",
            tool_calls=["google_docs_create"],
        ),
        ConversationMessage(
            role="user",
            content="Make the timeline section more detailed",
        ),
        ConversationMessage(
            role="assistant",
            content="Updated the timeline with specific milestones...",
        ),
    ]

    result = classifier.classify(messages, "doc-example")
    print(f"Activity: {result.overall_activity.value}")
    print(f"Time saved: {result.time_saved_display}")
    print(f"Confidence: {result.confidence}")
    print()

    # --- Example 3: Casual conversation ---
    print("=" * 50)
    print("Example 3: Casual Conversation")
    print("=" * 50)

    messages = [
        ConversationMessage(role="user", content="Hey what's up"),
        ConversationMessage(role="assistant", content="Not much! How can I help?"),
        ConversationMessage(role="user", content="Just bored at work"),
        ConversationMessage(role="assistant", content="I see! Want me to help with anything?"),
        ConversationMessage(role="user", content="Nah just chatting"),
        ConversationMessage(role="assistant", content="Sure, happy to chat!"),
        ConversationMessage(role="user", content="Tell me something interesting"),
        ConversationMessage(role="assistant", content="Did you know that octopuses have three hearts?"),
    ]

    result = classifier.classify(messages, "casual-example")
    print(f"Activity: {result.overall_activity.value}")
    print(f"Time saved: {result.time_saved_display}")
    print(f"Confidence: {result.confidence}")
    print()

    # --- Aggregate report ---
    print("=" * 50)
    print("Aggregate Report (all conversations)")
    print("=" * 50)

    all_conversations = [
        ("email-1", [
            ConversationMessage(role="user", content="Send the weekly report"),
            ConversationMessage(role="assistant", content="Sent!", tool_calls=["send_email"]),
        ]),
        ("doc-1", [
            ConversationMessage(role="user", content="Create meeting notes"),
            ConversationMessage(role="assistant", content="Created!", tool_calls=["create_doc"]),
        ]),
        ("sheet-1", [
            ConversationMessage(role="user", content="Update the budget spreadsheet"),
            ConversationMessage(role="assistant", content="Updated!", tool_calls=["google_sheets_create"]),
        ]),
        ("casual-1", [
            ConversationMessage(role="user", content="Hey"),
            ConversationMessage(role="assistant", content="Hi!"),
            ConversationMessage(role="user", content="Nothing"),
            ConversationMessage(role="assistant", content="Ok!"),
            ConversationMessage(role="user", content="Bye"),
            ConversationMessage(role="assistant", content="Bye!"),
            ConversationMessage(role="user", content="Wait"),
            ConversationMessage(role="assistant", content="Yes?"),
        ]),
    ]

    results = classifier.classify_batch(all_conversations)
    summary = classifier.aggregate_time_saved(results)

    print(f"Total conversations: {summary['total_conversations']}")
    print(f"Productive: {summary['productive_conversations']}")
    print(f"Productivity rate: {summary['productivity_rate']:.0%}")
    print(f"Total time saved: {summary['total_time_saved_minutes']} min")
    print(f"Time saved range: {summary['time_saved_range_minutes'][0]}-{summary['time_saved_range_minutes'][1]} min")
    print(f"LLM classifications used: {summary['llm_classifications']}")
    print(f"Total output tokens: {summary['total_output_tokens']}")
    print(f"Avg output tokens/conversation: {summary['avg_output_tokens_per_conversation']}")
    print()
    print("By activity type (minutes):")
    for activity, minutes in summary["by_activity"].items():
        print(f"  {activity}: {minutes} min")
    print()
    print("By output type (minutes):")
    for output, minutes in summary["by_output"].items():
        print(f"  {output}: {minutes} min")


if __name__ == "__main__":
    main()
