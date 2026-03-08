# Contributing

Thanks for your interest in contributing to the AI Productivity Tracker! Whether you use AI for coding, writing, research, or daily tasks — your experience can help make this framework better for everyone.

## Why Contribute?

Every person's workflow is different. The default time benchmarks might not reflect how *you* work. By contributing rules, benchmarks, and signal extractors, you help the framework give more accurate results for a wider range of AI users.

## Getting Started

```bash
git clone https://github.com/ehtan-smaltai/OpenTracking.git
cd OpenTracking
pip install -e ".[dev]"
pytest
```

## Ways to Contribute

### 1. Add or improve time benchmarks

Benchmarks answer: "How long would this take without AI?" They live in `productivity_framework/benchmarks/defaults.yaml`.

```yaml
tasks:
  your_new_task:
    low: 300       # seconds - fast worker / simple case
    mid: 600       # seconds - average
    high: 1200     # seconds - complex case
    description: "Human-readable description"
```

If you have real data (time-tracking logs, workplace studies) that suggests different estimates, open a PR with:
- The updated values
- Your data source or reasoning
- Whether this applies generally or to a specific domain

### 2. Add a new classification rule

Rules live in `productivity_framework/rules.py`. Each rule takes extracted signals and returns a classification.

```python
def _rule_your_pattern(signal: Signal) -> RuleResult:
    """Rule N: Description of what this catches."""
    if your_condition(signal):
        return RuleResult(
            matched=True,
            activity_type=ActivityType.WORK_CREATION,
            output_type=OutputType.DOCUMENT,
            confidence=0.85,
            rule_name="your_pattern",
        )
    return RuleResult()
```

**Guidelines:**
- Rules should have high precision (few false positives)
- Use 0.90+ confidence for tool-based signals, 0.70-0.85 for heuristics
- When in doubt, return `matched=False` and let the LLM handle it

### 3. Add signal extractors

Signals are features extracted from conversations (`productivity_framework/signals.py`). To add a new signal:

1. Add the field to the `Signal` dataclass in `types.py`
2. Add extraction logic in `extract_signals()` in `signals.py`
3. Add tests in `tests/test_signals.py`

### 4. Add output types

1. Add to `OutputType` enum in `types.py`
2. Add a benchmark entry in `benchmarks/defaults.yaml`
3. Add mapping in `benchmark_table.py`
4. Add tests

## Running Tests

```bash
pytest                                          # All tests
pytest productivity_framework/tests/test_rules.py  # Specific file
pytest -v                                       # Verbose
pytest --cov=productivity_framework             # With coverage
```

## Code Style

- Type hints on all public functions
- Docstrings on all public classes and functions
- No required external dependencies beyond `pyyaml`
- Keep the rule engine dependency-free (no API calls)

## Pull Request Checklist

- [ ] Tests pass (`pytest`)
- [ ] New features have tests
- [ ] Docstrings on new public API
- [ ] Updated README if adding user-facing features
- [ ] No new required dependencies
