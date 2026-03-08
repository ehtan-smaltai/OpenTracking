# Getting Started

This guide walks you through installing and using the AI Productivity Tracker to measure how much time AI saves you.

## Installation

### From PyPI

```bash
pip install ai-productivity-framework
```

### With LLM support (optional, for better accuracy)

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
git clone https://github.com/ehtan-smaltai/OpenTracking.git
cd OpenTracking
pip install -e ".[dev]"
```

## Your First Classification

The simplest way to measure a conversation:

```python
from productivity_framework import classify

result = classify([
    {"role": "user", "content": "Write me a Python script to rename all files in a folder by date"},
    {"role": "assistant", "content": "Here's a script...\n```python\nimport os\nfrom pathlib import Path\n...```"},
])

print(result.overall_activity)     # ActivityType.WORK_CREATION
print(result.time_saved_display)   # "~15 min (15-30 min range)"
print(result.confidence)           # 0.85
```

That's it. No API key needed, no config, no cost. The rule engine handled it.

## Understanding the Result

Every classification tells you:

```python
result.overall_activity       # What did you do? (work_creation, learning, casual, etc.)
result.confidence             # How confident is the classification? (0.0 to 1.0)
result.time_saved_seconds     # Estimated seconds saved by using AI
result.time_saved_display     # Human-readable: "~15 min (15-30 min range)"
result.outputs                # What was produced: ["code"], ["email"], etc.
result.actions_performed      # External actions taken: ["send_email"], ["deploy"]
result.classifier_layer       # Which layer decided? (2 = rules, 3 = LLM)
result.to_dict()              # JSON-serializable for logging/dashboards
```

## Practical Scenarios

### Scenario 1: Track your daily AI usage

Save each conversation as a JSON file, then classify at the end of the day:

```bash
productivity-classify ~/ai-conversations/today/ --output daily-report.json
```

### Scenario 2: Weekly productivity summary

```python
from productivity_framework import ProductivityClassifier

classifier = ProductivityClassifier()

# Your week's conversations
conversations = [
    ("mon-email-draft", monday_email_messages),
    ("mon-code-review", monday_code_messages),
    ("tue-research", tuesday_research_messages),
    ("tue-casual", tuesday_casual_messages),
    ("wed-doc-writing", wednesday_doc_messages),
]

results = classifier.classify_batch(conversations)
summary = classifier.aggregate_time_saved(results)

print(f"This week:")
print(f"  {summary['total_conversations']} conversations")
print(f"  {summary['productive_conversations']} productive ({summary['productivity_rate']:.0%})")
print(f"  {summary['total_time_saved_minutes']} minutes saved")
print(f"  Breakdown: {summary['by_activity']}")
```

### Scenario 3: Compare AI tools

Classify conversations from different tools to see which saves you more time:

```python
claude_results = classifier.classify_batch(claude_conversations)
chatgpt_results = classifier.classify_batch(chatgpt_conversations)

claude_summary = classifier.aggregate_time_saved(claude_results)
chatgpt_summary = classifier.aggregate_time_saved(chatgpt_results)

print(f"Claude: {claude_summary['total_time_saved_minutes']} min saved")
print(f"ChatGPT: {chatgpt_summary['total_time_saved_minutes']} min saved")
```

## Rules-Only vs LLM Mode

### Rules-only (default, free, private)

```python
classifier = ProductivityClassifier()
```

Handles ~70% of conversations accurately:
- Code written → `work_creation` (85% confidence)
- Email sent → `work_support` (95% confidence)
- Document created → `work_creation` (90% confidence)
- Long unstructured chat → `casual` (80% confidence)

The other ~30% (ambiguous conversations) default to `casual` with low confidence.

### With LLM fallback (100% coverage)

```python
classifier = ProductivityClassifier(
    api_key="sk-ant-...",
    provider="anthropic",   # or "openai"
)
```

The LLM is **only called when rules can't decide** — most conversations still use the free, private rule engine.

## Next Steps

- [Architecture Guide](architecture.md) — understand the 3-layer pipeline
- [Custom Benchmarks](custom-benchmarks.md) — tune time estimates for your workflow
- [Integration Guide](integration-guide.md) — embed in your own tools
- [API Reference](api-reference.md) — complete API documentation
