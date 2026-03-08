# AI Productivity Tracker

**Know exactly how much time AI saves you.**

You use ChatGPT, Claude, Copilot, or other AI assistants every day. But how much time are you *actually* saving? Can you prove it? This framework gives you the answer.

## The Problem

AI tools promise massive productivity gains, but nobody tracks them:

- **You feel faster** — but you can't put a number on it
- **Your manager asks** — "What's the ROI on that AI subscription?" and you shrug
- **Performance reviews** — you want to show you've become more productive, but it's all anecdotal
- **Companies spend thousands** on AI licenses — with zero data on whether it's working

Time saved by AI is invisible unless you measure it. This framework makes it visible.

## What This Does

Feed it your AI conversation history. It tells you:

1. **What you did** — wrote code, drafted emails, researched a topic, or just chatted
2. **How much time you saved** — in real minutes, with conservative estimates
3. **Your productivity breakdown** — creation vs research vs support vs casual

```
This week:
  23 conversations with AI
  18 were productive (78%)
  ~4.2 hours saved
  Breakdown: 2.1h code, 1.3h emails/docs, 0.8h research
```

## Quick Start

```bash
pip install ai-productivity-framework
```

### Track a conversation in 4 lines

```python
from productivity_framework import classify

result = classify([
    {"role": "user", "content": "Write a Python script to parse CSV and generate a summary report"},
    {"role": "assistant", "content": "Here's a script that reads your CSV...\n```python\nimport pandas as pd\n...```"},
])

print(result.time_saved_display)    # "~15 min (15-30 min range)"
print(result.overall_activity)      # ActivityType.WORK_CREATION
print(result.outputs)               # ["code"]
```

### Track your week

```python
from productivity_framework import ProductivityClassifier

classifier = ProductivityClassifier()

# Load your exported conversations
conversations = [
    ("monday-email", monday_messages),
    ("tuesday-code", tuesday_messages),
    ("wednesday-research", wednesday_messages),
]

results = classifier.classify_batch(conversations)
summary = classifier.aggregate_time_saved(results)

print(f"Productive conversations: {summary['productivity_rate']:.0%}")
print(f"Total time saved: {summary['total_time_saved_minutes']} min")
print(f"By type: {summary['by_activity']}")
```

### Use the CLI

```bash
# Classify a single conversation
productivity-classify conversation.json

# Output:
# Activity:    work_creation
# Confidence:  85%
# Time saved:  ~15 min (15-30 min range)
# Outputs:     code

# Classify a whole week's conversations
productivity-classify my_conversations/ --output weekly_report.json
```

## How It Works

The framework uses a **3-layer pipeline** — fast, cheap, and private by default:

```
Your conversations → [Signal Extraction] → [Rule Engine] → [LLM Fallback*]
                         (instant)           (instant)      (optional)
```

| Layer | What it does | Cost |
|-------|-------------|------|
| **Signals** | Extracts features: tool usage, word counts, code blocks, domain keywords | Free |
| **Rules** | 8 deterministic rules classify obvious cases (code written, email sent, casual chat) | Free |
| **LLM** | Handles ambiguous conversations using Claude or GPT | ~$0.001/conversation |

**~70% of conversations are classified by rules alone** — no API key, no cost, no data leaving your machine.

### What gets classified

| Activity | What it means | Example |
|----------|--------------|---------|
| `work_creation` | You produced something | Wrote code, drafted a document, created a plan |
| `work_research` | You researched something for work | Market analysis, technical deep-dive |
| `work_support` | AI handled a process for you | Sent email, scheduled meeting, ran a tool |
| `learning` | You learned something | Explained a concept, tutorial walkthrough |
| `personal_productive` | Useful but not work | Trip planning, personal finance |
| `casual` | Not productive | Chitchat, jokes, testing the AI |

### How time estimates work

Each output type has a benchmark: "How long would this take a human without AI?"

- Writing an email: **3-15 min** saved
- Writing a code function: **15-60 min** saved
- Research and analysis: **15-45 min** saved
- Creating a document: **10-30 min** saved

These benchmarks are conservative (`low` mode by default). You can customize them for your own workflow.

## Real Examples

### "I used Claude to draft 5 client emails this week"

```python
# Each email conversation gets classified
# Result: 5 × ~7 min = 35 min saved on emails alone
```

### "I had Copilot help me refactor a module"

```python
# Long conversation with code blocks + engineering keywords
# Result: work_creation, ~30 min saved (15-60 min range)
```

### "I asked ChatGPT to explain Kubernetes networking"

```python
# Long structured output, no tools, domain keywords, no refinement
# Result: learning, ~10 min saved (10-20 min range)
```

### "I spent 20 minutes chatting about movies with Claude"

```python
# Extended conversation, no tools, no structure, no domain keywords
# Result: casual, 0 min saved
```

## Customizing for Your Workflow

### Adjust time benchmarks

If you're a faster or slower writer, adjust the estimates:

```yaml
# my_benchmarks.yaml
tasks:
  email_draft:
    low: 120       # You write quick emails — 2 min
    mid: 300       # Average — 5 min
    high: 600      # Complex emails — 10 min

  code_function:
    low: 1800      # You're thorough — 30 min
    mid: 2700      # 45 min
    high: 3600     # 60 min
```

```python
from productivity_framework import BenchmarkTable, ProductivityClassifier

table = BenchmarkTable(defaults_path="my_benchmarks.yaml")
classifier = ProductivityClassifier(benchmark_table=table)
```

### Enable LLM for better accuracy

For the ~30% of conversations that rules can't classify:

```python
classifier = ProductivityClassifier(
    api_key="sk-ant-...",   # Your Anthropic key
    provider="anthropic",   # or "openai"
)
```

### Change estimate mode

```python
# Conservative (default)
classifier = ProductivityClassifier(estimate_mode="low")

# Middle ground
classifier = ProductivityClassifier(estimate_mode="mid")

# Generous
classifier = ProductivityClassifier(estimate_mode="high")
```

## Input Format

Export your conversations as JSON:

```json
{
  "conversation_id": "2024-03-08-email-draft",
  "messages": [
    {"role": "user", "content": "Draft an email to the team about the project delay"},
    {"role": "assistant", "content": "Subject: Project Timeline Update\n\nHi team,..."}
  ]
}
```

If your AI platform records tool usage, include it for better accuracy:

```json
{
  "role": "assistant",
  "content": "Email sent!",
  "tool_calls": ["send_email"]
}
```

## API Reference

### `classify()` — One-liner convenience function

```python
from productivity_framework import classify

result = classify(
    messages,                    # List of {"role": ..., "content": ...} dicts
    api_key=None,                # Optional: API key for LLM fallback
    provider="anthropic",        # "anthropic" or "openai"
    estimate_mode="low",         # "low", "mid", or "high"
)
```

### `ProductivityClassifier` — Full control

```python
from productivity_framework import ProductivityClassifier

classifier = ProductivityClassifier(
    api_key=None,
    provider="anthropic",
    model=None,                  # Defaults to cheapest model
    estimate_mode="low",
    min_rule_confidence=0.70,
    enable_llm_fallback=True,
)

result = classifier.classify(messages)
results = classifier.classify_batch(conversations)
summary = classifier.aggregate_time_saved(results)
```

### `ClassificationResult`

```python
result.overall_activity       # ActivityType enum
result.confidence             # 0.0 - 1.0
result.classifier_layer       # 2 = rules, 3 = LLM
result.time_saved_seconds     # Estimated seconds saved
result.time_saved_minutes     # Convenience: seconds / 60
result.time_saved_display     # "~7 min (3-15 min range)"
result.outputs                # ["email", "code"]
result.actions_performed      # ["send_email"]
result.to_dict()              # JSON-serializable dict
```

### `BenchmarkTable` — Custom time estimates

```python
from productivity_framework import BenchmarkTable

table = BenchmarkTable()                                    # Defaults
table = BenchmarkTable(defaults_path="my_benchmarks.yaml")  # Custom YAML
table = BenchmarkTable(overrides={"email_draft": {"low": 120, "mid": 300, "high": 600}})

classifier = ProductivityClassifier(benchmark_table=table)
```

## Architecture

```
productivity_framework/
├── __init__.py            # Public API + classify() convenience function
├── types.py               # Data models (ActivityType, OutputType, etc.)
├── signals.py             # Layer 1: Signal extraction
├── rules.py               # Layer 2: Rule engine (8 deterministic rules)
├── llm_classifier.py      # Layer 3: LLM fallback (optional)
├── benchmark_table.py     # Time benchmarks (YAML-driven)
├── classifier.py          # ProductivityClassifier orchestrator
├── cli.py                 # Command-line interface
└── benchmarks/
    └── defaults.yaml      # Default time benchmarks
```

## Why This Exists

AI tools are becoming essential for knowledge work. But "I feel more productive" isn't enough — you need data:

- **For yourself** — understand your AI usage patterns, optimize your workflow, see where AI helps most
- **For your career** — show concrete productivity improvements in reviews and promotions
- **For your team** — make informed decisions about which AI tools to keep paying for
- **For the industry** — contribute anonymized benchmarks so everyone can improve

The goal is simple: **turn "AI probably helps me" into "AI saved me 4.2 hours this week, mostly on code and emails."**

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding rules, benchmarks, and output types.

## License

MIT License — see [LICENSE](LICENSE) for details.
