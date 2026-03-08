# Custom Benchmarks

Time benchmarks define how long a task would take a human without AI assistance. The framework ships with research-backed defaults, but every organization is different. This guide shows how to customize benchmarks for your team.

## Why Customize?

Default benchmarks assume a general knowledge worker. Your team might differ:

- **Legal teams** might spend 30 min drafting an email (not 7 min)
- **Engineers** might write code faster (5 min for a snippet, not 15)
- **Executives** might have assistants who already handle scheduling (2 min, not 5)

Customizing benchmarks gives you accurate time-saved estimates for your specific workflows.

## Override via Code

The quickest way to adjust specific benchmarks:

```python
from productivity_framework import ProductivityClassifier, BenchmarkTable

table = BenchmarkTable(overrides={
    "email_draft": {"low": 300, "mid": 600, "high": 1200},
    "document_creation": {"low": 1800, "mid": 3600, "high": 7200},
})

classifier = ProductivityClassifier(benchmark_table=table)
```

This keeps the defaults for everything else and only overrides what you specify.

## Override via YAML

For larger customizations, create your own YAML file:

```yaml
# my_company_benchmarks.yaml

tasks:
  # Override existing tasks
  email_draft:
    low: 300       # 5 min - your team writes longer emails
    mid: 600       # 10 min
    high: 1200     # 20 min
    description: "Drafting a client email"

  # Add new task types
  legal_review:
    low: 1800      # 30 min
    mid: 3600      # 60 min
    high: 7200     # 120 min
    description: "Reviewing a legal document"

  investor_update:
    low: 1200      # 20 min
    mid: 2400      # 40 min
    high: 4800     # 80 min
    description: "Writing an investor update"

# Map your custom tools to task types
tool_mappings:
  legal_doc_review: legal_review
  investor_report: investor_update

default_estimate: low
```

```python
table = BenchmarkTable(defaults_path="my_company_benchmarks.yaml")
classifier = ProductivityClassifier(benchmark_table=table)
```

## Estimate Modes

Each benchmark has three estimates:

| Mode | Use case | Description |
|------|----------|-------------|
| `low` | Conservative reporting | Minimum realistic time. Best for external reporting. |
| `mid` | Internal dashboards | Typical time for an average worker. |
| `high` | Maximum impact | Upper bound. Useful for showing potential. |

```python
# Conservative (default)
classifier = ProductivityClassifier(estimate_mode="low")

# Typical
classifier = ProductivityClassifier(estimate_mode="mid")

# Maximum
classifier = ProductivityClassifier(estimate_mode="high")
```

## Default Benchmark Values

The built-in defaults (`benchmarks/defaults.yaml`):

### Content Creation

| Task | Low | Mid | High |
|------|-----|-----|------|
| Email draft | 3 min | 7 min | 15 min |
| Document creation | 15 min | 30 min | 60 min |
| Presentation | 20 min | 45 min | 90 min |
| Social media post | 5 min | 10 min | 20 min |

### Analysis & Research

| Task | Low | Mid | High |
|------|-----|-----|------|
| Research summary | 10 min | 25 min | 45 min |
| Data analysis | 10 min | 20 min | 40 min |
| Competitive analysis | 20 min | 40 min | 90 min |

### Code & Technical

| Task | Low | Mid | High |
|------|-----|-----|------|
| Code snippet | 5 min | 15 min | 30 min |
| Code review | 5 min | 15 min | 30 min |
| Code debugging | 10 min | 30 min | 60 min |

### Spreadsheets

| Task | Low | Mid | High |
|------|-----|-----|------|
| Spreadsheet creation | 5 min | 15 min | 30 min |
| Spreadsheet analysis | 10 min | 20 min | 40 min |

### Work Support

| Task | Low | Mid | High |
|------|-----|-----|------|
| Meeting prep | 5 min | 10 min | 20 min |
| Scheduling | 2 min | 5 min | 10 min |
| Task planning | 5 min | 15 min | 30 min |

### Quick Tasks

| Task | Low | Mid | High |
|------|-----|-----|------|
| Quick answer | 1 min | 3 min | 5 min |
| Translation | 3 min | 10 min | 20 min |
| Summarization | 5 min | 10 min | 20 min |
| Action executed | 1 min | 3 min | 5 min |
| Message drafting | 1 min | 3 min | 5 min |

## YAML Format Reference

```yaml
tasks:
  task_name:              # Unique identifier
    low: 180              # Seconds - optimistic estimate
    mid: 420              # Seconds - typical estimate
    high: 900             # Seconds - pessimistic estimate
    description: "..."    # Human-readable description

tool_mappings:
  tool_pattern: task_name  # Maps tool names to task types

default_estimate: low     # Which estimate to use by default
```

## Inspecting Active Benchmarks

```python
table = BenchmarkTable()
for name, info in table.list_benchmarks().items():
    print(f"{name}: {info['low_min']}-{info['high_min']} min — {info['description']}")
```

Output:
```
email_draft: 3-15 min — Drafting an email from scratch
document_creation: 15-60 min — Creating a document (memo, report, proposal)
code_snippet: 5-30 min — Writing a code snippet or function
...
```
