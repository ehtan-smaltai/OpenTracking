"""
Main Classifier Pipeline

Orchestrates the 3-layer classification:
  Layer 1: Signal extraction (free)
  Layer 2: Rule engine (free)
  Layer 3: LLM classifier (user's API key, only when needed)
"""

from __future__ import annotations

from .types import (
    ActivityType,
    OutputType,
    ConversationMessage,
    Signal,
    Segment,
    ClassificationResult,
)
from .signals import extract_signals
from .rules import apply_rules
from .benchmark_table import BenchmarkTable
from .llm_classifier import (
    LLMResult,
    classify_with_llm_sync,
    classify_with_llm_anthropic,
    classify_with_llm_openai,
)


# Activity types that count as "productive" for time-saved calculation
PRODUCTIVE_ACTIVITIES = {
    ActivityType.WORK_CREATION,
    ActivityType.WORK_RESEARCH,
    ActivityType.WORK_SUPPORT,
    ActivityType.LEARNING,
    ActivityType.PERSONAL_PRODUCTIVE,
}


class ProductivityClassifier:
    """
    Classify AI conversations and estimate time saved.

    Usage:
        classifier = ProductivityClassifier()
        result = classifier.classify(messages)
        print(result.time_saved_display)  # "~7 min (3-15 min range)"

    With LLM fallback (for ambiguous cases):
        classifier = ProductivityClassifier(
            api_key="sk-...",
            provider="anthropic",
        )
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str = "anthropic",
        model: str | None = None,
        benchmark_table: BenchmarkTable | None = None,
        estimate_mode: str = "low",
        min_rule_confidence: float = 0.70,
        enable_llm_fallback: bool = True,
    ):
        """
        Args:
            api_key: API key for LLM fallback. None = rules-only mode.
            provider: "anthropic" or "openai".
            model: Model for LLM classifier. Defaults to cheapest per provider.
            benchmark_table: Custom benchmark table. Uses defaults if None.
            estimate_mode: "low", "mid", or "high" time estimates.
            min_rule_confidence: Minimum confidence for rule engine matches.
            enable_llm_fallback: Whether to use LLM for ambiguous cases.
        """
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.min_rule_confidence = min_rule_confidence
        self.enable_llm_fallback = enable_llm_fallback and api_key is not None

        self.benchmarks = benchmark_table or BenchmarkTable(
            estimate_mode=estimate_mode,
        )

    def classify(
        self,
        messages: list[ConversationMessage],
        conversation_id: str = "",
    ) -> ClassificationResult:
        """
        Classify a conversation and estimate time saved.

        This is the main entry point. Runs the full 3-layer pipeline.

        Args:
            messages: List of conversation messages.
            conversation_id: Optional ID for tracking.

        Returns:
            ClassificationResult with activity type, outputs, and time saved.
        """
        result = ClassificationResult(conversation_id=conversation_id)

        if not messages:
            return result

        # Layer 1: Extract signals
        signal = extract_signals(messages)

        # Layer 2: Apply rules
        rule_result = apply_rules(signal, self.min_rule_confidence)

        if rule_result.matched:
            # Rules handled it — no LLM needed
            result.overall_activity = rule_result.activity_type
            result.confidence = rule_result.confidence
            result.classifier_layer = 2

            segment = Segment(
                message_range=(0, len(messages) - 1),
                activity_type=rule_result.activity_type,
                output_type=rule_result.output_type,
                confidence=rule_result.confidence,
                classifier_layer=2,
            )

            # Calculate time saved
            if rule_result.activity_type in PRODUCTIVE_ACTIVITIES:
                low, mid, high = self.benchmarks.get_time_for_output(
                    rule_result.output_type
                )
                default_time = self.benchmarks.get_default_time(rule_result.output_type)
                segment.time_saved_seconds = default_time
                segment.time_saved_low = low
                segment.time_saved_high = high

            result.segments.append(segment)
            if rule_result.output_type != OutputType.NONE:
                result.outputs.append(rule_result.output_type.value)
            if signal.external_actions:
                result.actions_performed = signal.external_actions

        elif self.enable_llm_fallback:
            # Layer 3: LLM classification
            msg_dicts = [
                {"role": m.role, "content": m.content} for m in messages
            ]
            llm_result = classify_with_llm_sync(
                msg_dicts, signal, self.api_key, self.provider, self.model
            )

            result.overall_activity = llm_result.activity_type
            result.confidence = llm_result.confidence
            result.classifier_layer = 3
            result.classification_cost_tokens = llm_result.tokens_used

            segment = Segment(
                message_range=(0, len(messages) - 1),
                activity_type=llm_result.activity_type,
                output_type=llm_result.output_type,
                confidence=llm_result.confidence,
                classifier_layer=3,
            )

            # Calculate time saved
            if llm_result.activity_type in PRODUCTIVE_ACTIVITIES:
                low, mid, high = self.benchmarks.get_time_for_output(
                    llm_result.output_type
                )
                default_time = self.benchmarks.get_default_time(llm_result.output_type)
                segment.time_saved_seconds = default_time
                segment.time_saved_low = low
                segment.time_saved_high = high

            result.segments.append(segment)
            if llm_result.output_type != OutputType.NONE:
                result.outputs.append(llm_result.output_type.value)

        else:
            # No LLM fallback — default to ambiguous/casual
            result.overall_activity = ActivityType.CASUAL
            result.confidence = 0.3
            result.classifier_layer = 2
            result.segments.append(
                Segment(
                    message_range=(0, len(messages) - 1),
                    activity_type=ActivityType.CASUAL,
                    output_type=OutputType.NONE,
                    confidence=0.3,
                    classifier_layer=2,
                )
            )

        # Aggregate time saved from all segments
        result.time_saved_seconds = sum(s.time_saved_seconds for s in result.segments)
        result.time_saved_low = sum(s.time_saved_low for s in result.segments)
        result.time_saved_high = sum(s.time_saved_high for s in result.segments)

        # Propagate token metrics from signal
        result.total_output_tokens = signal.total_output_tokens
        result.total_input_tokens = signal.total_input_tokens
        result.code_output_tokens = signal.code_output_tokens
        result.prose_output_tokens = signal.prose_output_tokens

        return result

    def classify_batch(
        self,
        conversations: list[tuple[str, list[ConversationMessage]]],
    ) -> list[ClassificationResult]:
        """
        Classify multiple conversations.

        Args:
            conversations: List of (conversation_id, messages) tuples.

        Returns:
            List of ClassificationResult objects.
        """
        return [
            self.classify(messages, conv_id)
            for conv_id, messages in conversations
        ]

    def aggregate_time_saved(
        self,
        results: list[ClassificationResult],
    ) -> dict:
        """
        Aggregate time saved across multiple conversations.

        Returns a summary dict with total time, breakdown by activity, etc.
        """
        total_seconds = sum(r.time_saved_seconds for r in results)
        total_low = sum(r.time_saved_low for r in results)
        total_high = sum(r.time_saved_high for r in results)

        by_activity: dict[str, int] = {}
        by_output: dict[str, int] = {}
        productive_count = 0
        total_count = len(results)

        for r in results:
            if r.overall_activity in PRODUCTIVE_ACTIVITIES:
                productive_count += 1
            activity_key = r.overall_activity.value
            by_activity[activity_key] = (
                by_activity.get(activity_key, 0) + r.time_saved_seconds
            )
            for output in r.outputs:
                by_output[output] = by_output.get(output, 0) + r.time_saved_seconds

        return {
            "total_conversations": total_count,
            "productive_conversations": productive_count,
            "productivity_rate": (
                round(productive_count / total_count, 2) if total_count else 0
            ),
            "total_time_saved_seconds": total_seconds,
            "total_time_saved_minutes": round(total_seconds / 60, 1),
            "total_time_saved_hours": round(total_seconds / 3600, 1),
            "time_saved_range_minutes": [
                round(total_low / 60, 1),
                round(total_high / 60, 1),
            ],
            "by_activity": {
                k: round(v / 60, 1) for k, v in by_activity.items()
            },
            "by_output": {
                k: round(v / 60, 1) for k, v in by_output.items()
            },
            "llm_classifications": sum(
                1 for r in results if r.classifier_layer == 3
            ),
            "total_classification_tokens": sum(
                r.classification_cost_tokens for r in results
            ),
            # Token-based work output
            "total_output_tokens": sum(r.total_output_tokens for r in results),
            "total_input_tokens": sum(r.total_input_tokens for r in results),
            "total_tokens": sum(
                r.total_output_tokens + r.total_input_tokens for r in results
            ),
            "code_output_tokens": sum(r.code_output_tokens for r in results),
            "prose_output_tokens": sum(r.prose_output_tokens for r in results),
            "avg_output_tokens_per_conversation": (
                round(
                    sum(r.total_output_tokens for r in results) / total_count
                )
                if total_count
                else 0
            ),
        }
