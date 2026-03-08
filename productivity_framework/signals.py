"""
Layer 1: Signal Extraction

Extracts structured features from a conversation.
Zero cost - no API calls, pure computation.
"""

from __future__ import annotations

import re

from .types import ConversationMessage, Signal

# Approximate token estimation: ~4 chars per token for English text.
# This avoids requiring tiktoken or a tokenizer dependency.
# Users can pass actual token_count on ConversationMessage for exact values.
CHARS_PER_TOKEN = 4


# Patterns that suggest structured output
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")
TABLE_PATTERN = re.compile(r"\|.*\|.*\|")
LIST_PATTERN = re.compile(r"^[\s]*[-*\d+\.]\s+", re.MULTILINE)

# Patterns that indicate user refinement/iteration
REFINEMENT_PATTERNS = [
    re.compile(r"\b(change|modify|update|revise|edit|fix|adjust|tweak)\b", re.I),
    re.compile(r"\b(can you|could you|please)\b.*\b(redo|rew rite|rephrase)\b", re.I),
    re.compile(r"\b(more|less|shorter|longer|simpler|detailed)\b", re.I),
    re.compile(r"\b(not quite|almost|close but|try again)\b", re.I),
]

# Domain keyword categories
DOMAIN_KEYWORDS = {
    "finance": [
        "revenue",
        "profit",
        "margin",
        "ebitda",
        "forecast",
        "budget",
        "roi",
        "cash flow",
        "valuation",
        "p&l",
        "balance sheet",
        "quarterly",
        "fiscal",
        "earnings",
        "dividend",
    ],
    "marketing": [
        "campaign",
        "conversion",
        "funnel",
        "leads",
        "brand",
        "seo",
        "content strategy",
        "audience",
        "engagement",
        "ctr",
        "impression",
        "social media",
        "marketing",
    ],
    "engineering": [
        "api",
        "deploy",
        "bug",
        "feature",
        "sprint",
        "pull request",
        "database",
        "architecture",
        "refactor",
        "ci/cd",
        "testing",
        "endpoint",
        "microservice",
    ],
    "legal": [
        "contract",
        "compliance",
        "regulation",
        "liability",
        "nda",
        "terms",
        "clause",
        "intellectual property",
        "patent",
        "lawsuit",
    ],
    "hr": [
        "hiring",
        "onboarding",
        "performance review",
        "compensation",
        "benefits",
        "retention",
        "employee",
        "recruitment",
        "job description",
    ],
    "sales": [
        "pipeline",
        "quota",
        "deal",
        "prospect",
        "crm",
        "close rate",
        "objection",
        "proposal",
        "pricing",
        "negotiation",
    ],
    "operations": [
        "process",
        "workflow",
        "efficiency",
        "supply chain",
        "logistics",
        "inventory",
        "vendor",
        "procurement",
        "sop",
    ],
}

# External action tool patterns (tools that affect the outside world)
EXTERNAL_ACTION_PATTERNS = [
    "send_email",
    "gmail_send",
    "outlook_send",
    "post_message",
    "slack_send",
    "telegram_send",
    "create_event",
    "schedule_meeting",
    "calendar_create",
    "upload_file",
    "drive_upload",
    "s3_upload",
    "publish",
    "deploy",
    "push",
    "create_task",
    "create_issue",
    "update_record",
    "insert_record",
    "tweet",
    "post_social",
]

# Artifact-producing tool patterns
ARTIFACT_PATTERNS = [
    "create_doc",
    "google_docs_create",
    "word_create",
    "create_spreadsheet",
    "google_sheets_create",
    "excel_create",
    "create_presentation",
    "google_slides_create",
    "powerpoint_create",
    "generate_chart",
    "create_chart",
    "generate_pdf",
    "create_pdf",
    "write_file",
    "save_file",
]


def extract_signals(messages: list[ConversationMessage]) -> Signal:
    """
    Extract structured signals from a conversation.

    This is Layer 1 of the classification pipeline.
    Pure computation, no API calls, zero cost.
    """
    signal = Signal()

    if not messages:
        return signal

    signal.message_count = len(messages)

    user_messages = [m for m in messages if m.role == "user"]
    assistant_messages = [m for m in messages if m.role == "assistant"]

    signal.user_message_count = len(user_messages)
    signal.assistant_message_count = len(assistant_messages)

    # Tool calls
    all_tool_calls = []
    for msg in messages:
        all_tool_calls.extend(msg.tool_calls)
    signal.tool_calls = all_tool_calls
    signal.tool_call_count = len(all_tool_calls)

    # External actions
    signal.external_actions = [
        tc for tc in all_tool_calls if any(pat in tc.lower() for pat in EXTERNAL_ACTION_PATTERNS)
    ]

    # Artifacts produced
    signal.artifacts_produced = [
        tc for tc in all_tool_calls if any(pat in tc.lower() for pat in ARTIFACT_PATTERNS)
    ]

    # User message stats
    if user_messages:
        word_counts = [len(m.content.split()) for m in user_messages]
        signal.user_message_avg_words = sum(word_counts) / len(word_counts)

    # Assistant output stats
    if assistant_messages:
        assistant_word_counts = [len(m.content.split()) for m in assistant_messages]
        signal.assistant_total_words = sum(assistant_word_counts)
        signal.longest_assistant_response_words = max(assistant_word_counts)

        # Check for structured output in assistant messages
        all_assistant_text = "\n".join(m.content for m in assistant_messages)
        signal.has_code_blocks = bool(CODE_BLOCK_PATTERN.search(all_assistant_text))
        signal.has_tables = bool(TABLE_PATTERN.search(all_assistant_text))
        signal.has_lists = bool(LIST_PATTERN.search(all_assistant_text))
        signal.has_structured_output = (
            signal.has_code_blocks or signal.has_tables or signal.has_lists
        )

    # Domain keywords
    all_text = " ".join(m.content.lower() for m in messages)
    for domain, keywords in DOMAIN_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in all_text)
        if count > 0:
            signal.domain_keywords[domain] = count

    # Conversation duration
    timestamps = [m.timestamp for m in messages if m.timestamp > 0]
    if len(timestamps) >= 2:
        signal.conversation_duration_seconds = max(timestamps) - min(timestamps)

    # User refinement count
    for msg in user_messages:
        text = msg.content.lower()
        if any(pat.search(text) for pat in REFINEMENT_PATTERNS):
            signal.user_refinement_count += 1

    # Token counting
    # Use explicit token_count from messages if available, otherwise estimate
    for msg in user_messages:
        if msg.token_count > 0:
            signal.total_input_tokens += msg.token_count
        else:
            signal.total_input_tokens += _estimate_tokens(msg.content)

    for msg in assistant_messages:
        if msg.token_count > 0:
            msg_tokens = msg.token_count
        else:
            msg_tokens = _estimate_tokens(msg.content)
        signal.total_output_tokens += msg_tokens

    signal.total_tokens = signal.total_input_tokens + signal.total_output_tokens

    if assistant_messages:
        signal.output_tokens_per_message = signal.total_output_tokens / len(assistant_messages)

    # Split output tokens into code vs prose
    if assistant_messages:
        all_assistant_text = "\n".join(m.content for m in assistant_messages)
        code_blocks = CODE_BLOCK_PATTERN.findall(all_assistant_text)
        code_text = "\n".join(code_blocks)
        signal.code_output_tokens = _estimate_tokens(code_text)
        signal.prose_output_tokens = signal.total_output_tokens - signal.code_output_tokens

    return signal


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text. ~4 chars per token for English."""
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)
