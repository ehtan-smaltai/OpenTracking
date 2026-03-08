# Architecture

The framework uses a 3-layer pipeline that prioritizes speed and cost. Most conversations are classified for free by the rule engine. Only ambiguous cases are escalated to an LLM.

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
  Conversation                                  ClassificationResult
  Messages                                      (activity, time saved,
                                                 outputs, tokens)
```

## Layer 1: Signal Extraction

**File:** `signals.py`

Extracts structured features from raw conversation messages. This is pure computation — no API calls, no cost.

### Signals extracted

| Signal | Description |
|--------|-------------|
| `tool_calls` | List of tools invoked (send_email, create_doc, etc.) |
| `tool_call_count` | Total number of tool calls |
| `external_actions` | Tools that affect the outside world (send, post, deploy) |
| `artifacts_produced` | Tools that create files (create_doc, write_file) |
| `message_count` | Total messages in conversation |
| `user_message_avg_words` | Average words per user message |
| `assistant_total_words` | Total words in all assistant messages |
| `has_code_blocks` | Whether assistant output contained ``` code blocks |
| `has_tables` | Whether assistant output contained markdown tables |
| `has_lists` | Whether assistant output contained bullet/numbered lists |
| `has_structured_output` | Any of: code blocks, tables, or lists |
| `domain_keywords` | Keyword hits by domain (finance, engineering, etc.) |
| `user_refinement_count` | How many times the user asked for changes |
| `total_input_tokens` | Total user tokens (estimated or explicit) |
| `total_output_tokens` | Total assistant tokens |
| `code_output_tokens` | Tokens inside code blocks |
| `prose_output_tokens` | Tokens outside code blocks |

### Token estimation

Tokens are estimated at ~4 characters per token when `token_count` isn't provided on `ConversationMessage`. For exact counts, set `token_count` on each message.

### Domain keyword detection

The signal extractor scans for keywords across 7 domains:
- **Finance:** revenue, profit, EBITDA, forecast, ROI, etc.
- **Marketing:** campaign, conversion, funnel, CTR, etc.
- **Engineering:** API, deploy, bug, sprint, CI/CD, etc.
- **Legal:** contract, compliance, NDA, patent, etc.
- **HR:** hiring, onboarding, performance review, etc.
- **Sales:** pipeline, quota, CRM, proposal, etc.
- **Operations:** process, workflow, supply chain, etc.

## Layer 2: Rule Engine

**File:** `rules.py`

8 deterministic rules that classify clear-cut cases. Rules are evaluated in priority order — the first confident match wins.

### Rules (in priority order)

| # | Rule | Condition | Activity | Confidence |
|---|------|-----------|----------|------------|
| 1 | `external_action` | Tool call matches send/post/deploy pattern | `work_support` | 0.95 |
| 2 | `artifact_created` | Tool call matches create/write pattern | `work_creation` | 0.90 |
| 3 | `code_generation` | Code blocks + long output + engineering keywords | `work_creation` | 0.85 |
| 4 | `substantial_structured_output` | Structured output + 500+ words + user refinement | `work_creation` | 0.82 |
| 5 | `research_heavy` | 3+ domain keyword hits + 800+ assistant words | `work_research` | 0.75 |
| 6 | `extended_no_output` | 6+ messages, no tools, no structure, no domain | `casual` | 0.80 |
| 7 | `learning_pattern` | Long structured output, no tools, domain keywords, no refinement | `learning` | 0.70 |
| 8 | `quick_qa_ambiguous` | 4 or fewer messages, no tools, short output | *(pass to LLM)* | 0.50 |

### Confidence threshold

Rules must meet the `min_rule_confidence` threshold (default 0.70) to be accepted. Below that, the conversation is passed to Layer 3.

## Layer 3: LLM Classifier

**File:** `llm_classifier.py`

Handles ambiguous cases that the rule engine can't classify confidently. Uses the cheapest model available (Haiku for Anthropic, GPT-4o-mini for OpenAI).

### When does the LLM get called?

Only when:
1. No rule matched with confidence >= `min_rule_confidence`
2. `api_key` was provided
3. `enable_llm_fallback` is `True`

### What does it send to the LLM?

A structured prompt with:
- The conversation messages (truncated to key portions)
- The extracted signals from Layer 1
- Instructions to classify into ActivityType and OutputType
- Instructions to assess confidence

### Cost

Typical cost per classification: ~$0.001 (using cheapest models). Token usage is tracked in `result.classification_cost_tokens`.

## Time Estimation

**File:** `benchmark_table.py`

After classification, the framework estimates how long the task would have taken a human without AI assistance.

### How it works

1. The `OutputType` (email, document, code, etc.) maps to a benchmark entry
2. The benchmark provides three estimates: `low`, `mid`, `high` (in seconds)
3. The `estimate_mode` setting determines which estimate to use as the default
4. All three estimates are always available on the result

### Default benchmarks

Loaded from `benchmarks/defaults.yaml`. Example:

```yaml
email_draft:
  low: 180       # 3 min - quick reply
  mid: 420       # 7 min - standard business email
  high: 900      # 15 min - detailed/sensitive email
```

### Overriding benchmarks

```python
# Via code
table = BenchmarkTable(overrides={
    "email_draft": {"low": 300, "mid": 600, "high": 1200},
})

# Via custom YAML
table = BenchmarkTable(defaults_path="my_company_benchmarks.yaml")
```

## Data Flow

```
ConversationMessage[]
        │
        ▼
  extract_signals()  ──▶  Signal
        │
        ▼
    apply_rules()    ──▶  RuleResult
        │
        ├── matched (confidence >= threshold)
        │       │
        │       ▼
        │   Build Segment with activity + output type
        │       │
        │       ▼
        │   Look up time benchmark
        │       │
        │       ▼
        │   ClassificationResult ✓
        │
        └── not matched
                │
                ▼
          classify_with_llm()  ──▶  LLMResult
                │
                ▼
            Build Segment
                │
                ▼
            Look up time benchmark
                │
                ▼
            ClassificationResult ✓
```

## Design Decisions

### Why 3 layers?

- **Layer 1** is always needed — signals are the foundation for both rules and LLM prompts.
- **Layer 2** handles the easy cases (tool call = work done) at zero cost.
- **Layer 3** handles nuanced cases where context matters. Separating it keeps the framework usable without any API key.

### Why YAML benchmarks?

- Easy for non-developers to review and suggest changes
- Version-controllable alongside the code
- Overridable per organization without forking

### Why not use the LLM for everything?

- Cost: even at $0.001/call, it adds up at scale
- Speed: rule engine is instant, LLM adds 1-2s latency
- Reliability: rules are deterministic and testable
- Privacy: some users don't want conversation data sent to an LLM
