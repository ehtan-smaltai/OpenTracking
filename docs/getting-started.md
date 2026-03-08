# Getting Started

This guide walks you through installing, configuring, and using the AI Productivity Measurement Framework in your application.

## Installation

### From PyPI

```bash
pip install ai-productivity-framework
```

### With LLM support

```bash
# Anthropic (Claude)
pip install "ai-productivity-framework[anthropic]"

# OpenAI (GPT)
pip install "ai-productivity-framework[openai]"

# Both
pip install "ai-productivity-framework[all]"
```

### From source

```bash
git clone https://github.com/ehtan-smaltai/ai-productivity-framework.git
cd ai-productivity-framework
pip install -e ".[dev]"
```

## Your First Classification

The simplest way to classify a conversation:

```python
from productivity_framework import classify

result = classify([
    {"role": "user", "content": "Draft an email to the marketing team about Q3 results"},
    {"role": "assistant", "content": "Subject: Q3 Campaign Performance Summary\n\nHi team,\n\nI wanted to share..."},
])

print(result.overall_activity)     # ActivityType.WORK_CREATION
print(result.time_saved_display)   # "~5 min (5-10 min range)"
print(result.confidence)           # 0.82
```

That's it. No API key, no config, no cost. The rule engine handled it.

## Understanding the Result

Every classification returns a `ClassificationResult` with these key fields:

```python
result.overall_activity       # What kind of work was this? (ActivityType enum)
result.confidence             # How sure are we? (0.0 to 1.0)
result.classifier_layer       # Which layer classified it? (2 = rules, 3 = LLM)
result.time_saved_seconds     # Estimated seconds saved
result.time_saved_display     # Human-readable: "~7 min (3-15 min range)"
result.outputs                # What was produced: ["email", "document"]
result.actions_performed      # External actions: ["send_email"]
result.total_output_tokens    # AI output volume
result.to_dict()              # JSON-serializable for storage/APIs
```

## Rules-Only vs LLM Mode

### Rules-only (default, free)

```python
from productivity_framework import ProductivityClassifier

classifier = ProductivityClassifier()
```

The rule engine handles ~70% of conversations with zero cost:
- Email sent → `work_support` (95% confidence)
- Document created → `work_creation` (90% confidence)
- Code with engineering keywords → `work_creation` (85% confidence)
- Long chat, no tools, no structure → `casual` (80% confidence)

For the other ~30% (ambiguous conversations), it defaults to `casual` with low confidence.

### With LLM fallback (handles 100%)

```python
classifier = ProductivityClassifier(
    api_key="sk-ant-...",   # Your Anthropic API key
    provider="anthropic",
)
```

Now ambiguous conversations get classified by Claude (cheapest model by default). The LLM is **only called when rules can't decide** — most conversations still use the free rule engine.

## Batch Processing

Classify many conversations at once and get aggregate stats:

```python
conversations = [
    ("conv-1", messages_1),
    ("conv-2", messages_2),
    ("conv-3", messages_3),
]

results = classifier.classify_batch(conversations)
summary = classifier.aggregate_time_saved(results)

print(summary["total_time_saved_minutes"])   # 45.0
print(summary["productivity_rate"])           # 0.67 (67% productive)
print(summary["by_activity"])                 # {"work_creation": 30.0, "casual": 0.0}
print(summary["total_output_tokens"])         # 12500
```

## Using the CLI

For quick one-off classification:

```bash
# Single conversation
productivity-classify conversation.json

# Batch a directory
productivity-classify conversations/ --output report.json

# With LLM fallback
productivity-classify conversation.json --api-key sk-ant-...
```

See [CLI Reference](cli-reference.md) for full details.

## Next Steps

- [Architecture Guide](architecture.md) — understand the 3-layer pipeline
- [Custom Benchmarks](custom-benchmarks.md) — tune time estimates for your org
- [Integration Guide](integration-guide.md) — embed in your application
- [API Reference](api-reference.md) — complete API documentation
