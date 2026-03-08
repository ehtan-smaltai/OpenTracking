# AI Productivity Measurement Framework

Open-source framework for measuring AI assistant productivity by classifying conversations and estimating time saved.

**Zero cost by default.** The rule engine handles ~70% of conversations without any API calls. Optional LLM fallback (your API key) handles the rest.

## Quick Start

```bash
pip install ai-productivity-framework
```

### Classify a conversation in 4 lines

```python
from productivity_framework import ProductivityClassifier, ConversationMessage

classifier = ProductivityClassifier()

result = classifier.classify([
    ConversationMessage(role="user", content="Draft an email to the team about Q3 results"),
    ConversationMessage(role="assistant", content="Here's a draft...", tool_calls=["send_email"]),
])

print(result.time_saved_display)    # "~3 min (3-15 min range)"
print(result.overall_activity)      # ActivityType.WORK_SUPPORT
print(result.outputs)               # ["email"]
```

### Batch classify and get aggregate stats

```python
conversations = [
    ("conv-1", [ConversationMessage(role="user", content="Send the weekly report"),
                ConversationMessage(role="assistant", content="Sent!", tool_calls=["send_email"])]),
    ("conv-2", [ConversationMessage(role="user", content="Create project proposal"),
                ConversationMessage(role="assistant", content="Done!", tool_calls=["create_doc"])]),
]

results = classifier.classify_batch(conversations)
summary = classifier.aggregate_time_saved(results)

print(summary["total_time_saved_minutes"])   # 18.0
print(summary["productivity_rate"])           # 1.0
print(summary["by_activity"])                 # {"work_support": 3.0, "work_creation": 15.0}
```

## How It Works

The framework uses a **3-layer pipeline** that prioritizes speed and cost:

```
Conversation → [Layer 1: Signals] → [Layer 2: Rules] → [Layer 3: LLM*]
                   (free)              (free)           (optional)
```

| Layer | What it does | Cost | Coverage |
|-------|-------------|------|----------|
| **Layer 1: Signals** | Extracts structured features (tool calls, word counts, code blocks, domain keywords, token metrics) | Free | 100% |
| **Layer 2: Rules** | 8 deterministic rules that classify clear-cut cases (email sent → work_support, artifact created → work_creation, etc.) | Free | ~70% |
| **Layer 3: LLM** | Classifies ambiguous cases using Anthropic or OpenAI | Your API key | ~30% |

### Activity Types

| Type | Description | Example |
|------|-------------|---------|
| `work_creation` | Produced a deliverable | Wrote a document, generated code |
| `work_research` | Research/analysis for work | Market analysis, data deep-dive |
| `work_support` | Helped with a work process | Sent email, scheduled meeting |
| `learning` | Educational, skill-building | Explained a concept in depth |
| `personal_productive` | Personal but useful | Trip planning, personal finance |
| `casual` | Social, entertainment, testing | Chitchat, jokes, testing the AI |

### Output Types

`document`, `email`, `code`, `spreadsheet`, `analysis`, `plan`, `social_media_post`, `presentation`, `summary`, `action_executed`, `quick_answer`, `none`

## API Reference

### `ProductivityClassifier`

The main entry point. Handles the full 3-layer pipeline.

```python
classifier = ProductivityClassifier(
    api_key=None,              # API key for LLM fallback (None = rules-only)
    provider="anthropic",      # "anthropic" or "openai"
    model=None,                # LLM model (defaults to cheapest per provider)
    estimate_mode="low",       # "low", "mid", or "high" time estimates
    min_rule_confidence=0.70,  # Minimum confidence for rule matches
    enable_llm_fallback=True,  # Use LLM for ambiguous cases
)
```

#### Methods

**`classify(messages, conversation_id="")`** → `ClassificationResult`

Classify a single conversation.

```python
result = classifier.classify(messages)
```

**`classify_batch(conversations)`** → `list[ClassificationResult]`

Classify multiple conversations.

```python
results = classifier.classify_batch([
    ("id-1", messages_1),
    ("id-2", messages_2),
])
```

**`aggregate_time_saved(results)`** → `dict`

Aggregate stats across multiple results.

```python
summary = classifier.aggregate_time_saved(results)
# Returns: total_time_saved_minutes, productivity_rate, by_activity, by_output, etc.
```

### `ConversationMessage`

```python
msg = ConversationMessage(
    role="user",              # "user" or "assistant"
    content="...",            # Message text
    tool_calls=["send_email"],  # Tools invoked (optional)
    tool_results=[],          # Tool outputs (optional)
    token_count=0,            # Exact token count (optional, estimated if 0)
)
```

### `ClassificationResult`

```python
result.overall_activity       # ActivityType enum
result.confidence             # 0.0 - 1.0
result.classifier_layer       # 1, 2, or 3
result.time_saved_seconds     # Estimated seconds saved
result.time_saved_minutes     # Convenience: seconds / 60
result.time_saved_display     # "~7 min (3-15 min range)"
result.outputs                # ["email", "document"]
result.actions_performed      # ["send_email"]
result.total_output_tokens    # Token count
result.code_output_tokens     # Code token count
result.prose_output_tokens    # Prose token count
result.to_dict()              # JSON-serializable dict
```

### `BenchmarkTable`

Time benchmarks are loaded from YAML and can be overridden per-org or per-user.

```python
from productivity_framework import BenchmarkTable

# Use defaults
table = BenchmarkTable()

# Override specific benchmarks
table = BenchmarkTable(overrides={
    "email_draft": {"low": 300, "mid": 600, "high": 1200},
})

# Load from custom YAML
table = BenchmarkTable(defaults_path="my_benchmarks.yaml")

# Pass to classifier
classifier = ProductivityClassifier(benchmark_table=table)
```

## LLM Fallback

For the ~30% of conversations that rules can't classify confidently, you can enable LLM fallback:

```python
# Anthropic
classifier = ProductivityClassifier(
    api_key="sk-ant-...",
    provider="anthropic",
)

# OpenAI
classifier = ProductivityClassifier(
    api_key="sk-...",
    provider="openai",
)
```

The LLM is only called when the rule engine's confidence is below `min_rule_confidence` (default 0.70). Token usage is tracked in `result.classification_cost_tokens`.

## Custom Benchmarks

Create a YAML file with your own time estimates:

```yaml
tasks:
  email_draft:
    low: 300       # 5 min (your org writes longer emails)
    mid: 600       # 10 min
    high: 1200     # 20 min
    description: "Drafting an email"

  custom_task:
    low: 600
    mid: 1200
    high: 2400
    description: "Your custom task type"

tool_mappings:
  your_tool: custom_task

default_estimate: low
```

```python
table = BenchmarkTable(defaults_path="your_benchmarks.yaml")
classifier = ProductivityClassifier(benchmark_table=table)
```

## CLI Usage

Classify conversations from JSON files:

```bash
# Classify a single conversation
productivity-classify conversation.json

# Classify with LLM fallback
productivity-classify conversation.json --api-key sk-ant-... --provider anthropic

# Batch classify a directory
productivity-classify conversations/ --output report.json

# Use custom benchmarks
productivity-classify conversation.json --benchmarks my_benchmarks.yaml

# Adjust estimate mode
productivity-classify conversation.json --estimate-mode mid
```

### Input Format

The CLI expects JSON files with this structure:

```json
{
  "conversation_id": "optional-id",
  "messages": [
    {"role": "user", "content": "Draft an email...", "tool_calls": []},
    {"role": "assistant", "content": "Here's a draft...", "tool_calls": ["send_email"]}
  ]
}
```

Or a directory of such files for batch processing.

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/ehtan-smaltai/ai-productivity-framework.git
cd ai-productivity-framework
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=productivity_framework
```

## Architecture

```
productivity_framework/
├── __init__.py            # Public API
├── types.py               # Data models (ActivityType, OutputType, etc.)
├── signals.py             # Layer 1: Signal extraction
├── rules.py               # Layer 2: Rule engine (8 rules)
├── llm_classifier.py      # Layer 3: LLM fallback
├── benchmark_table.py     # Time benchmarks (YAML-driven)
├── cli.py                 # Command-line interface
├── benchmarks/
│   └── defaults.yaml      # Default time benchmarks
├── examples/
│   ├── basic_usage.py     # No API key needed
│   └── with_llm_fallback.py
└── tests/
    ├── test_signals.py
    ├── test_rules.py
    ├── test_classifier.py
    └── test_benchmarks.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new rules to the rule engine
- Contributing time benchmarks
- Adding output types
- Writing tests

## License

MIT License - see [LICENSE](LICENSE) for details.
