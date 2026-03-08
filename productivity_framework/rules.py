"""
Layer 2: Rule Engine

Deterministic classification for clear-cut cases.
Handles ~70% of conversations with zero API cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from .types import ActivityType, OutputType, Signal


@dataclass
class RuleResult:
    """Output of the rule engine."""

    matched: bool = False
    activity_type: ActivityType = ActivityType.CASUAL
    output_type: OutputType = OutputType.NONE
    confidence: float = 0.0
    rule_name: str = ""


# Tool name → output type mapping
TOOL_OUTPUT_MAP: dict[str, OutputType] = {
    "email": OutputType.EMAIL,
    "gmail": OutputType.EMAIL,
    "outlook": OutputType.EMAIL,
    "send_email": OutputType.EMAIL,
    "google_sheets": OutputType.SPREADSHEET,
    "excel": OutputType.SPREADSHEET,
    "spreadsheet": OutputType.SPREADSHEET,
    "google_docs": OutputType.DOCUMENT,
    "create_doc": OutputType.DOCUMENT,
    "word": OutputType.DOCUMENT,
    "google_slides": OutputType.PRESENTATION,
    "powerpoint": OutputType.PRESENTATION,
    "presentation": OutputType.PRESENTATION,
    "code": OutputType.CODE,
    "github": OutputType.CODE,
    "git": OutputType.CODE,
}


def _infer_output_type(tool_calls: list[str]) -> OutputType:
    """Infer the output type from tool calls."""
    for tc in tool_calls:
        tc_lower = tc.lower()
        for pattern, output_type in TOOL_OUTPUT_MAP.items():
            if pattern in tc_lower:
                return output_type
    return OutputType.NONE


def _rule_external_action(signal: Signal) -> RuleResult:
    """Rule 1: External action was executed (email sent, event created, etc.)."""
    if signal.external_actions:
        output_type = _infer_output_type(signal.external_actions)
        if output_type == OutputType.NONE:
            output_type = OutputType.ACTION_EXECUTED
        return RuleResult(
            matched=True,
            activity_type=ActivityType.WORK_SUPPORT,
            output_type=output_type,
            confidence=0.95,
            rule_name="external_action",
        )
    return RuleResult()


def _rule_artifact_created(signal: Signal) -> RuleResult:
    """Rule 2: An artifact was created (document, spreadsheet, etc.)."""
    if signal.artifacts_produced:
        output_type = _infer_output_type(signal.artifacts_produced)
        if output_type == OutputType.NONE:
            output_type = OutputType.DOCUMENT
        return RuleResult(
            matched=True,
            activity_type=ActivityType.WORK_CREATION,
            output_type=output_type,
            confidence=0.90,
            rule_name="artifact_created",
        )
    return RuleResult()


def _rule_substantial_structured_output(signal: Signal) -> RuleResult:
    """Rule 3: Long structured output with user refinement."""
    if (
        signal.has_structured_output
        and signal.assistant_total_words > 500
        and signal.user_refinement_count >= 1
    ):
        output_type = OutputType.ANALYSIS
        if signal.has_code_blocks:
            output_type = OutputType.CODE
        return RuleResult(
            matched=True,
            activity_type=ActivityType.WORK_CREATION,
            output_type=output_type,
            confidence=0.82,
            rule_name="substantial_structured_output",
        )
    return RuleResult()


def _rule_code_generation(signal: Signal) -> RuleResult:
    """Rule 4: Code was generated."""
    if (
        signal.has_code_blocks
        and signal.longest_assistant_response_words > 100
        and signal.domain_keywords.get("engineering", 0) >= 1
    ):
        return RuleResult(
            matched=True,
            activity_type=ActivityType.WORK_CREATION,
            output_type=OutputType.CODE,
            confidence=0.85,
            rule_name="code_generation",
        )
    return RuleResult()


def _rule_research_heavy(signal: Signal) -> RuleResult:
    """Rule 5: Domain-heavy research conversation."""
    total_domain_hits = sum(signal.domain_keywords.values())
    if (
        total_domain_hits >= 3
        and signal.assistant_total_words > 800
    ):
        return RuleResult(
            matched=True,
            activity_type=ActivityType.WORK_RESEARCH,
            output_type=OutputType.ANALYSIS,
            confidence=0.75,
            rule_name="research_heavy",
        )
    return RuleResult()


def _rule_quick_qa(signal: Signal) -> RuleResult:
    """Rule 6: Quick Q&A (short conversation, no tools)."""
    if (
        signal.message_count <= 4
        and signal.tool_call_count == 0
        and signal.assistant_total_words < 300
    ):
        # Could be productive (quick answer) or casual - ambiguous
        return RuleResult(
            matched=False,  # Pass to Layer 3
            confidence=0.50,
            rule_name="quick_qa_ambiguous",
        )
    return RuleResult()


def _rule_extended_no_output(signal: Signal) -> RuleResult:
    """Rule 7: Long conversation with no tools and no structured output."""
    if (
        signal.message_count > 6
        and signal.tool_call_count == 0
        and not signal.artifacts_produced
        and not signal.has_structured_output
        and not signal.domain_keywords
    ):
        return RuleResult(
            matched=True,
            activity_type=ActivityType.CASUAL,
            output_type=OutputType.NONE,
            confidence=0.80,
            rule_name="extended_no_output",
        )
    return RuleResult()


def _rule_learning_pattern(signal: Signal) -> RuleResult:
    """Rule 8: Learning/educational pattern — long explanations, questions."""
    if (
        signal.assistant_total_words > 500
        and signal.has_structured_output
        and signal.user_refinement_count == 0
        and not signal.tool_calls
        and signal.domain_keywords
    ):
        return RuleResult(
            matched=True,
            activity_type=ActivityType.LEARNING,
            output_type=OutputType.SUMMARY,
            confidence=0.70,
            rule_name="learning_pattern",
        )
    return RuleResult()


# Rules in priority order — first high-confidence match wins
RULES = [
    _rule_external_action,       # Highest signal
    _rule_artifact_created,
    _rule_code_generation,
    _rule_substantial_structured_output,
    _rule_research_heavy,
    _rule_extended_no_output,
    _rule_learning_pattern,
    _rule_quick_qa,              # Fallback / ambiguous
]


def apply_rules(signal: Signal, min_confidence: float = 0.70) -> RuleResult:
    """
    Apply the rule engine to extracted signals.

    Returns the first rule match with confidence >= min_confidence.
    If no rule matches confidently, returns an unmatched result
    signaling that Layer 3 (LLM) should be called.
    """
    for rule_fn in RULES:
        result = rule_fn(signal)
        if result.matched and result.confidence >= min_confidence:
            return result

    return RuleResult(matched=False, confidence=0.0, rule_name="no_match")
