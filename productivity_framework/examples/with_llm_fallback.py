"""
Example using LLM fallback for ambiguous conversations.

Requires an API key (Anthropic or OpenAI).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from productivity_framework import ConversationMessage, ProductivityClassifier


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY to enable LLM fallback.")
        print("Without it, ambiguous conversations default to 'casual'.")
        print()

    # With API key: ambiguous cases get classified by LLM
    # Without API key: rules-only mode
    classifier = ProductivityClassifier(
        api_key=api_key,
        provider="anthropic",  # or "openai"
        estimate_mode="low",  # conservative estimates
    )

    # This conversation is ambiguous — short Q&A, no tools
    # Rules can't classify it confidently, so LLM takes over
    messages = [
        ConversationMessage(
            role="user",
            content="What's the best way to structure a DCF model for a SaaS company?",
        ),
        ConversationMessage(
            role="assistant",
            content="For a SaaS DCF model, focus on these key drivers:\n"
            "1. Monthly Recurring Revenue (MRR) growth rate\n"
            "2. Churn rate and net revenue retention\n"
            "3. Customer acquisition cost (CAC) and payback period\n"
            "4. Gross margin trajectory\n"
            "5. Operating leverage assumptions\n\n"
            "Start with a 5-year projection period...",
        ),
    ]

    result = classifier.classify(messages, "ambiguous-example")
    print(f"Activity: {result.overall_activity.value}")
    print(f"Time saved: {result.time_saved_display}")
    print(f"Confidence: {result.confidence}")
    print(f"Classifier layer: {result.classifier_layer}")
    print(f"LLM tokens used: {result.classification_cost_tokens}")
    print()
    print("Full result:")
    import json

    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
