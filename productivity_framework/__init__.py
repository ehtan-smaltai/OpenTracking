"""
AI Productivity Measurement Framework

Open-source framework for measuring AI assistant productivity
by classifying conversations and estimating time saved.

3-Layer Pipeline:
  Layer 1 (Signals)  - Extract structured features from conversations (free)
  Layer 2 (Rules)    - Classify clear-cut cases via deterministic rules (free)
  Layer 3 (LLM)      - Classify ambiguous cases via LLM (user's API key)
"""

from .types import (
    ActivityType,
    OutputType,
    ConversationMessage,
    Signal,
    Segment,
    ClassificationResult,
)
from .classifier import ProductivityClassifier
from .benchmark_table import BenchmarkTable

__version__ = "0.1.0"

__all__ = [
    "ProductivityClassifier",
    "BenchmarkTable",
    "ActivityType",
    "OutputType",
    "ConversationMessage",
    "Signal",
    "Segment",
    "ClassificationResult",
    "classify",
]


def classify(
    messages: list[dict[str, str]],
    api_key: str | None = None,
    provider: str = "anthropic",
    estimate_mode: str = "low",
) -> ClassificationResult:
    """
    Convenience function — classify a conversation in one call.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."} dicts.
            Optionally include "tool_calls" (list of strings).
        api_key: API key for LLM fallback. None = rules-only mode.
        provider: "anthropic" or "openai".
        estimate_mode: "low", "mid", or "high".

    Returns:
        ClassificationResult

    Example:
        >>> from productivity_framework import classify
        >>> result = classify([
        ...     {"role": "user", "content": "Draft an email to the team"},
        ...     {"role": "assistant", "content": "Here's a draft...", "tool_calls": ["send_email"]},
        ... ])
        >>> print(result.time_saved_display)
    """
    conv_messages = [
        ConversationMessage(
            role=m["role"],
            content=m["content"],
            tool_calls=m.get("tool_calls", []),
        )
        for m in messages
    ]
    classifier = ProductivityClassifier(
        api_key=api_key,
        provider=provider,
        estimate_mode=estimate_mode,
    )
    return classifier.classify(conv_messages)
