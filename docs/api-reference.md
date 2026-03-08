# API Reference

Complete reference for all public classes, functions, and types.

## Module: `productivity_framework`

### `classify(messages, api_key=None, provider="anthropic", estimate_mode="low")`

Convenience function for one-shot classification.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | `list[dict]` | *(required)* | List of `{"role": str, "content": str}` dicts. Optionally include `"tool_calls"` (list of strings). |
| `api_key` | `str \| None` | `None` | API key for LLM fallback. `None` = rules-only. |
| `provider` | `str` | `"anthropic"` | `"anthropic"` or `"openai"` |
| `estimate_mode` | `str` | `"low"` | `"low"`, `"mid"`, or `"high"` |

**Returns:** `ClassificationResult`

**Example:**
```python
from productivity_framework import classify

result = classify([
    {"role": "user", "content": "Send the report"},
    {"role": "assistant", "content": "Sent!", "tool_calls": ["send_email"]},
])
print(result.time_saved_display)  # "~3 min (3-15 min range)"
```

---

## `ProductivityClassifier`

Main classifier class. Reusable across multiple conversations.

### Constructor

```python
ProductivityClassifier(
    api_key: str | None = None,
    provider: str = "anthropic",
    model: str | None = None,
    benchmark_table: BenchmarkTable | None = None,
    estimate_mode: str = "low",
    min_rule_confidence: float = 0.70,
    enable_llm_fallback: bool = True,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | API key for LLM fallback. `None` disables LLM. |
| `provider` | `str` | `"anthropic"` | LLM provider: `"anthropic"` or `"openai"`. |
| `model` | `str \| None` | `None` | Model for LLM classifier. Defaults to cheapest per provider. |
| `benchmark_table` | `BenchmarkTable \| None` | `None` | Custom benchmark table. Uses built-in defaults if `None`. |
| `estimate_mode` | `str` | `"low"` | Which time estimate to use: `"low"`, `"mid"`, or `"high"`. |
| `min_rule_confidence` | `float` | `0.70` | Minimum confidence for rule engine matches. Below this threshold, conversations are passed to the LLM. |
| `enable_llm_fallback` | `bool` | `True` | Whether to use the LLM for ambiguous cases. Set to `False` to force rules-only even with an API key. |

### `classify(messages, conversation_id="")`

Classify a single conversation through the 3-layer pipeline.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | `list[ConversationMessage]` | *(required)* | Conversation messages |
| `conversation_id` | `str` | `""` | Optional ID for tracking |

**Returns:** `ClassificationResult`

### `classify_batch(conversations)`

Classify multiple conversations.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `conversations` | `list[tuple[str, list[ConversationMessage]]]` | List of `(conversation_id, messages)` tuples |

**Returns:** `list[ClassificationResult]`

### `aggregate_time_saved(results)`

Compute aggregate statistics across multiple classification results.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `results` | `list[ClassificationResult]` | Classification results to aggregate |

**Returns:** `dict` with the following keys:

| Key | Type | Description |
|-----|------|-------------|
| `total_conversations` | `int` | Number of conversations |
| `productive_conversations` | `int` | Conversations with productive activity types |
| `productivity_rate` | `float` | Ratio of productive to total (0.0-1.0) |
| `total_time_saved_seconds` | `int` | Total estimated seconds saved |
| `total_time_saved_minutes` | `float` | Total minutes saved |
| `total_time_saved_hours` | `float` | Total hours saved |
| `time_saved_range_minutes` | `list[float]` | `[low_minutes, high_minutes]` |
| `by_activity` | `dict[str, float]` | Minutes saved per activity type |
| `by_output` | `dict[str, float]` | Minutes saved per output type |
| `llm_classifications` | `int` | How many used the LLM |
| `total_classification_tokens` | `int` | Total LLM tokens consumed |
| `total_output_tokens` | `int` | Total AI output tokens |
| `total_input_tokens` | `int` | Total user input tokens |
| `total_tokens` | `int` | Combined input + output |
| `code_output_tokens` | `int` | Tokens in code blocks |
| `prose_output_tokens` | `int` | Tokens outside code blocks |
| `avg_output_tokens_per_conversation` | `int` | Average output tokens |

---

## Data Types

### `ConversationMessage`

A single message in a conversation.

```python
@dataclass
class ConversationMessage:
    role: str                              # "user" or "assistant"
    content: str                           # Message text
    timestamp: float = 0.0                 # Unix timestamp (auto-set if 0)
    tool_calls: list[str] = []             # Tool names invoked
    tool_results: list[dict[str, Any]] = [] # Tool outputs
    token_count: int = 0                   # Exact token count (0 = estimate)
```

### `ClassificationResult`

Output of the classification pipeline.

```python
@dataclass
class ClassificationResult:
    conversation_id: str = ""
    overall_activity: ActivityType = ActivityType.CASUAL
    confidence: float = 0.0
    classifier_layer: int = 0              # 2 = rules, 3 = LLM
    segments: list[Segment] = []
    time_saved_seconds: int = 0
    time_saved_low: int = 0
    time_saved_high: int = 0
    outputs: list[str] = []                # Output type values
    actions_performed: list[str] = []      # External actions
    classification_cost_tokens: int = 0    # LLM tokens used
    total_output_tokens: int = 0
    total_input_tokens: int = 0
    code_output_tokens: int = 0
    prose_output_tokens: int = 0
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `time_saved_minutes` | `float` | `time_saved_seconds / 60` |
| `time_saved_display` | `str` | Human-readable: `"~7 min (3-15 min range)"` |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `dict` | JSON-serializable dictionary |

### `Signal`

Extracted features from Layer 1.

```python
@dataclass
class Signal:
    tool_calls: list[str] = []
    tool_call_count: int = 0
    artifacts_produced: list[str] = []
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    user_message_avg_words: float = 0.0
    assistant_total_words: int = 0
    has_structured_output: bool = False
    external_actions: list[str] = []
    domain_keywords: dict[str, int] = {}
    conversation_duration_seconds: float = 0.0
    user_refinement_count: int = 0
    longest_assistant_response_words: int = 0
    has_code_blocks: bool = False
    has_tables: bool = False
    has_lists: bool = False
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    output_tokens_per_message: float = 0.0
    code_output_tokens: int = 0
    prose_output_tokens: int = 0
```

### `Segment`

A classified portion of a conversation.

```python
@dataclass
class Segment:
    message_range: tuple[int, int] = (0, 0)
    activity_type: ActivityType = ActivityType.CASUAL
    output_type: OutputType = OutputType.NONE
    confidence: float = 0.0
    classifier_layer: int = 0
    time_saved_seconds: int = 0
    time_saved_low: int = 0
    time_saved_high: int = 0
```

---

## Enums

### `ActivityType`

```python
class ActivityType(str, Enum):
    WORK_CREATION = "work_creation"           # Produced a deliverable
    WORK_RESEARCH = "work_research"           # Research/analysis for work
    WORK_SUPPORT = "work_support"             # Helped with a work process
    LEARNING = "learning"                      # Educational, skill-building
    PERSONAL_PRODUCTIVE = "personal_productive" # Personal but useful
    CASUAL = "casual"                          # Social, entertainment, testing
```

**Productive types** (count toward time saved): `WORK_CREATION`, `WORK_RESEARCH`, `WORK_SUPPORT`, `LEARNING`, `PERSONAL_PRODUCTIVE`

### `OutputType`

```python
class OutputType(str, Enum):
    DOCUMENT = "document"
    EMAIL = "email"
    CODE = "code"
    SPREADSHEET = "spreadsheet"
    ANALYSIS = "analysis"
    PLAN = "plan"
    SOCIAL_MEDIA_POST = "social_media_post"
    PRESENTATION = "presentation"
    SUMMARY = "summary"
    ACTION_EXECUTED = "action_executed"
    QUICK_ANSWER = "quick_answer"
    NONE = "none"
```

---

## `BenchmarkTable`

### Constructor

```python
BenchmarkTable(
    defaults_path: str | Path | None = None,
    estimate_mode: str = "low",
    overrides: dict[str, dict[str, int]] | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `defaults_path` | `str \| Path \| None` | `None` | Path to YAML file. Uses built-in defaults if `None`. |
| `estimate_mode` | `str` | `"low"` | Default estimate: `"low"`, `"mid"`, `"high"` |
| `overrides` | `dict \| None` | `None` | Override specific benchmarks: `{"task_name": {"low": N, "mid": N, "high": N}}` |

### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_benchmark(task_name)` | `str` | `TimeBenchmark \| None` | Get benchmark for a task |
| `get_time_for_output(output_type)` | `OutputType` | `tuple[int,int,int]` | Get `(low, mid, high)` seconds |
| `get_default_time(output_type)` | `OutputType` | `int` | Get default seconds per `estimate_mode` |
| `get_task_for_tool(tool_name)` | `str` | `str \| None` | Map tool to task type |
| `list_benchmarks()` | — | `dict` | All benchmarks as dict |

### `TimeBenchmark`

```python
@dataclass
class TimeBenchmark:
    low: int = 0        # seconds
    mid: int = 0        # seconds
    high: int = 0       # seconds
    description: str = ""
```
