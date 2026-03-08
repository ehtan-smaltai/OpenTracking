# Architecture

## Why This Framework Exists

AI tools are everywhere. ChatGPT, Claude, Copilot, Gemini — millions of people use them daily for work. Companies pay $20-30/month per seat. Individuals pay out of pocket.

But nobody can answer the simple question: **"How much time does AI actually save me?"**

- You *feel* more productive, but feelings don't show up in performance reviews
- Your company invested $50K in AI licenses, but can't quantify the return
- You want to optimize your workflow, but don't know where AI helps most vs. where you're wasting time chatting

This framework exists to turn **"AI probably helps me"** into **"AI saved me 4.2 hours this week — 2.1h on code, 1.3h on emails, 0.8h on research."**

### Design Principles

1. **Free by default** — the rule engine handles most cases with zero cost
2. **Private by default** — nothing leaves your machine unless you opt into LLM fallback
3. **Conservative estimates** — we'd rather undercount than overcount time saved
4. **Customizable** — your workflow is unique, so benchmarks are overridable

## Pipeline Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Layer 1:       │     │  Layer 2:        │     │  Layer 3:       │
│  Signal         │────▶│  Rule Engine     │────▶│  LLM Classifier │
│  Extraction     │     │  (8 rules)       │     │  (optional)     │
│                 │     │                  │     │                 │
│  Cost: FREE     │     │  Cost: FREE      │     │  Cost: ~$0.001  │
│  Coverage: 100% │     │  Coverage: ~70%  │     │  Coverage: ~30% │
└─────────────────┘     └──────────────────┘     └─────────────────┘
       ▲                                                │
       │                                                │
  Your AI                                       ClassificationResult
  conversations                                 (what you did, time saved,
                                                 what was produced)
```

## Layer 1: Signal Extraction

**File:** `signals.py`

Scans your conversation and extracts structured features. Pure computation — no API calls, no cost, no data leaves your machine.

### What gets extracted

| Signal | What it tells us |
|--------|-----------------|
| `tool_calls` | Did the AI use tools? (send_email, create_doc, deploy, etc.) |
| `external_actions` | Did the AI affect the outside world? (sent something, posted, deployed) |
| `artifacts_produced` | Did the AI create files? (wrote a doc, saved code) |
| `message_count` | How long was the conversation? |
| `assistant_total_words` | How much did the AI output? |
| `has_code_blocks` | Did the AI write code? |
| `has_structured_output` | Did the AI produce structured content? (code, tables, lists) |
| `domain_keywords` | What domain is this about? (engineering, finance, marketing, etc.) |
| `user_refinement_count` | Did you iterate? ("make it shorter", "add error handling") |
| `code_output_tokens` | How much code was written? |
| `prose_output_tokens` | How much prose was written? |

### Domain detection

Keywords are scanned across 7 domains:
- **Engineering:** API, deploy, bug, sprint, CI/CD, refactor
- **Finance:** revenue, profit, EBITDA, forecast, ROI
- **Marketing:** campaign, conversion, funnel, CTR, SEO
- **Legal:** contract, compliance, NDA, patent, liability
- **HR:** hiring, onboarding, performance review, PIP
- **Sales:** pipeline, quota, CRM, proposal, close rate
- **Operations:** process, workflow, supply chain, SLA

## Layer 2: Rule Engine

**File:** `rules.py`

8 deterministic rules that classify obvious cases. Rules run in priority order — first confident match wins.

| # | Rule | What it catches | Classification | Confidence |
|---|------|----------------|----------------|------------|
| 1 | `external_action` | AI sent an email, posted, deployed | `work_support` | 95% |
| 2 | `artifact_created` | AI created a document, wrote a file | `work_creation` | 90% |
| 3 | `code_generation` | AI wrote substantial code | `work_creation` | 85% |
| 4 | `substantial_structured_output` | AI produced a long, structured document with iterations | `work_creation` | 82% |
| 5 | `research_heavy` | Deep domain research with long output | `work_research` | 75% |
| 6 | `extended_no_output` | Long chat, no tools, no structure | `casual` | 80% |
| 7 | `learning_pattern` | Long explanation, domain keywords, no iteration | `learning` | 70% |
| 8 | `quick_qa_ambiguous` | Short exchange, unclear purpose | *pass to LLM* | 50% |

Rules must hit a confidence threshold (default 70%) to be accepted. Below that → Layer 3.

## Layer 3: LLM Classifier

**File:** `llm_classifier.py`

For the ~30% of conversations that rules can't classify confidently. Uses the cheapest available model (Haiku for Anthropic, GPT-4o-mini for OpenAI).

**When does it run?**
1. No rule matched with enough confidence
2. You provided an API key
3. LLM fallback is enabled (default: yes)

**What does it send?** A summary of the conversation + extracted signals + instructions to classify. Typical cost: ~$0.001 per conversation.

**You can skip it entirely.** Without an API key, ambiguous conversations default to `casual` with low confidence. You still get accurate results for the ~70% that rules handle.

## Time Estimation

**File:** `benchmark_table.py`

After classifying *what* you did, the framework estimates *how long it would have taken without AI*.

### How it works

1. The output type (email, code, document, etc.) maps to a benchmark
2. Each benchmark has three estimates: `low`, `mid`, `high` (in seconds)
3. Your `estimate_mode` setting picks which to use (default: `low` = conservative)

### Default benchmarks (conservative)

| Output | Low | Mid | High |
|--------|-----|-----|------|
| Email draft | 3 min | 7 min | 15 min |
| Code function | 15 min | 30 min | 60 min |
| Document | 10 min | 20 min | 30 min |
| Research/analysis | 15 min | 30 min | 45 min |
| Quick answer | 2 min | 5 min | 10 min |

### Customizing

```yaml
# my_benchmarks.yaml - adjust for your speed
tasks:
  email_draft:
    low: 120    # I write fast — 2 min
    mid: 300    # 5 min
    high: 600   # 10 min
```

```python
table = BenchmarkTable(defaults_path="my_benchmarks.yaml")
classifier = ProductivityClassifier(benchmark_table=table)
```

## Data Flow

```
Your AI conversations
        │
        ▼
  extract_signals()  ──▶  What happened in this conversation?
        │
        ▼
    apply_rules()    ──▶  Can we classify this deterministically?
        │
        ├── YES (confident match)
        │       │
        │       ▼
        │   Look up time benchmark → ClassificationResult
        │
        └── NO (ambiguous)
                │
                ▼
          LLM classifies it → Look up benchmark → ClassificationResult
```

## Design Decisions

### Why not just use an LLM for everything?

| Concern | Rule engine | LLM-only |
|---------|------------|----------|
| **Cost** | Free | ~$0.001/conversation, adds up |
| **Speed** | Instant | 1-2 seconds per call |
| **Privacy** | Nothing leaves your machine | Conversations sent to API |
| **Reliability** | Deterministic, testable | May vary between calls |
| **Offline** | Works anywhere | Needs internet |

### Why YAML benchmarks?

- Easy to review and adjust without coding
- Version-controllable alongside the code
- Different people/teams can have different benchmarks without forking

### Why conservative estimates by default?

It's better to say "AI saved you 3 hours this week" and be right than "AI saved you 8 hours" and be wrong. Credibility matters — especially if you're reporting these numbers to someone else.
