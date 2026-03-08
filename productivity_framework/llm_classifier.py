"""
Layer 3: LLM Classifier

Called only for ambiguous cases (~30% of conversations).
Uses the user's own API key. Model-agnostic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .types import ActivityType, OutputType, Signal


@dataclass
class LLMResult:
    """Output of the LLM classifier."""

    activity_type: ActivityType = ActivityType.CASUAL
    output_type: OutputType = OutputType.NONE
    confidence: float = 0.0
    tokens_used: int = 0


CLASSIFICATION_PROMPT = """Classify this AI assistant conversation.

CONVERSATION SUMMARY:
- First user message: {first_user_message}
- Last user message: {last_user_message}
- Message count: {message_count}
- Tools used: {tool_calls}
- Artifacts created: {artifacts}
- Assistant output length: {assistant_words} words
- Structured output: {structured}
- Domain keywords detected: {domain_keywords}

ACTIVITY_TYPE (pick one):
- work_creation: Produced a deliverable (document, email, code, plan, spreadsheet)
- work_research: Research or analysis for a work purpose
- work_support: Helped with a work process (scheduling, organizing, reviewing)
- learning: Educational, skill-building, understanding concepts
- personal_productive: Personal but useful (travel planning, budgeting, health)
- casual: Social, entertainment, idle chat, testing the AI

OUTPUT_TYPE (pick one):
- document, email, code, spreadsheet, analysis, plan, social_media_post, presentation, summary, action_executed, quick_answer, none

Respond with JSON only, no other text:
{{"activity_type": "...", "output_type": "...", "confidence": 0.0}}"""


def build_classification_input(
    messages: list[dict[str, str]],
    signal: Signal,
) -> str:
    """Build the LLM prompt from messages and signals."""
    first_user = ""
    last_user = ""
    for msg in messages:
        if msg.get("role") == "user":
            if not first_user:
                first_user = msg["content"][:200]
            last_user = msg["content"][:200]

    return CLASSIFICATION_PROMPT.format(
        first_user_message=first_user or "(none)",
        last_user_message=last_user or "(none)",
        message_count=signal.message_count,
        tool_calls=", ".join(signal.tool_calls[:10]) or "none",
        artifacts=", ".join(signal.artifacts_produced[:5]) or "none",
        assistant_words=signal.assistant_total_words,
        structured=signal.has_structured_output,
        domain_keywords=json.dumps(signal.domain_keywords) if signal.domain_keywords else "none",
    )


def parse_llm_response(response_text: str) -> LLMResult:
    """Parse the LLM's JSON response into an LLMResult."""
    try:
        # Try to extract JSON from the response
        text = response_text.strip()

        # Handle markdown code blocks
        if "```" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]

        data = json.loads(text)

        activity_str = data.get("activity_type", "casual")
        output_str = data.get("output_type", "none")
        confidence = float(data.get("confidence", 0.5))

        # Map strings to enums with fallback
        try:
            activity = ActivityType(activity_str)
        except ValueError:
            activity = ActivityType.CASUAL

        try:
            output = OutputType(output_str)
        except ValueError:
            output = OutputType.NONE

        return LLMResult(
            activity_type=activity,
            output_type=output,
            confidence=min(confidence, 1.0),
        )

    except (json.JSONDecodeError, KeyError, TypeError):
        # If parsing fails, default to casual
        return LLMResult(
            activity_type=ActivityType.CASUAL,
            output_type=OutputType.NONE,
            confidence=0.3,
        )


async def classify_with_llm_anthropic(
    messages: list[dict[str, str]],
    signal: Signal,
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
) -> LLMResult:
    """
    Classify using Anthropic's Claude API.

    Uses Haiku by default for cost efficiency (~$0.001 per classification).
    """
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)
        prompt = build_classification_input(messages, signal)

        response = await client.messages.create(
            model=model,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        result = parse_llm_response(response_text)
        result.tokens_used = response.usage.input_tokens + response.usage.output_tokens
        return result

    except Exception:
        return LLMResult(
            activity_type=ActivityType.CASUAL,
            output_type=OutputType.NONE,
            confidence=0.0,
        )


async def classify_with_llm_openai(
    messages: list[dict[str, str]],
    signal: Signal,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> LLMResult:
    """
    Classify using OpenAI's API.

    Uses gpt-4o-mini by default for cost efficiency.
    """
    try:
        import openai

        client = openai.AsyncOpenAI(api_key=api_key)
        prompt = build_classification_input(messages, signal)

        response = await client.chat.completions.create(
            model=model,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.choices[0].message.content or ""
        result = parse_llm_response(response_text)
        if response.usage:
            result.tokens_used = (
                response.usage.prompt_tokens + response.usage.completion_tokens
            )
        return result

    except Exception:
        return LLMResult(
            activity_type=ActivityType.CASUAL,
            output_type=OutputType.NONE,
            confidence=0.0,
        )


def classify_with_llm_sync(
    messages: list[dict[str, str]],
    signal: Signal,
    api_key: str,
    provider: str = "anthropic",
    model: str | None = None,
) -> LLMResult:
    """
    Synchronous wrapper for LLM classification.

    Args:
        messages: Conversation messages as dicts with 'role' and 'content'.
        signal: Extracted signals from Layer 1.
        api_key: The user's API key.
        provider: "anthropic" or "openai".
        model: Model to use. Defaults to cheapest option per provider.
    """
    import asyncio

    if provider == "anthropic":
        model = model or "claude-haiku-4-5-20251001"
        coro = classify_with_llm_anthropic(messages, signal, api_key, model)
    elif provider == "openai":
        model = model or "gpt-4o-mini"
        coro = classify_with_llm_openai(messages, signal, api_key, model)
    else:
        return LLMResult(confidence=0.0)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're already in an async context, create a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, coro).result()
        return result
    else:
        return asyncio.run(coro)
