# Contributing

Thanks for your interest in contributing to the AI Productivity Measurement Framework! This guide covers the most common ways to contribute.

## Getting Started

```bash
git clone https://github.com/ehtan-smaltai/ai-productivity-framework.git
cd ai-productivity-framework
pip install -e ".[dev]"
pytest
```

## Adding a New Rule

Rules live in `productivity_framework/rules.py`. Each rule is a function that takes a `Signal` and returns a `RuleResult`.

1. Write your rule function:

```python
def _rule_your_pattern(signal: Signal) -> RuleResult:
    """Rule N: Description of what this catches."""
    if your_condition(signal):
        return RuleResult(
            matched=True,
            activity_type=ActivityType.WORK_CREATION,
            output_type=OutputType.DOCUMENT,
            confidence=0.85,  # 0.0 - 1.0
            rule_name="your_pattern",
        )
    return RuleResult()
```

2. Add it to the `RULES` list (order matters - higher priority first):

```python
RULES = [
    _rule_external_action,
    _rule_artifact_created,
    _rule_your_pattern,      # <-- insert based on priority
    ...
]
```

3. Add tests in `productivity_framework/tests/test_rules.py`.

### Rule guidelines

- Rules should have **high precision** (few false positives). Low confidence → let the LLM handle it.
- Confidence should reflect how certain the rule is. Use 0.90+ for tool-based signals, 0.70-0.85 for heuristic matches.
- Return `matched=False` for ambiguous cases to pass to Layer 3.

## Contributing Time Benchmarks

Benchmarks live in `productivity_framework/benchmarks/defaults.yaml`.

### Adding a new benchmark

```yaml
tasks:
  your_new_task:
    low: 300       # seconds - optimistic estimate
    mid: 600       # seconds - typical estimate
    high: 1200     # seconds - pessimistic estimate
    description: "Human-readable description of the task"
```

### Updating existing benchmarks

If you have data (time-tracking studies, workplace surveys, etc.) that suggests different estimates, open a PR with:
- The updated values
- A brief explanation of your data source
- Whether this is industry-specific or general

### Adding tool mappings

```yaml
tool_mappings:
  your_tool_name: your_task_name
```

## Adding a New Output Type

1. Add to `OutputType` enum in `productivity_framework/types.py`
2. Add a benchmark entry in `benchmarks/defaults.yaml`
3. Add mapping in `benchmark_table.py` → `get_time_for_output()`
4. Update relevant rules in `rules.py` if needed
5. Add tests

## Adding Signal Extractors

Signals are extracted in `productivity_framework/signals.py`. To add a new signal:

1. Add the field to the `Signal` dataclass in `types.py`
2. Add extraction logic in `extract_signals()` in `signals.py`
3. Add tests in `tests/test_signals.py`
4. Optionally, use the new signal in rules

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest productivity_framework/tests/test_rules.py

# Verbose output
pytest -v

# With coverage
pytest --cov=productivity_framework
```

## Code Style

- Type hints on all public functions
- Docstrings on all public classes and functions
- No external dependencies beyond `pyyaml` (LLM providers are optional)
- Keep the rule engine dependency-free (no API calls)

## Pull Request Checklist

- [ ] Tests pass (`pytest`)
- [ ] New features have tests
- [ ] Docstrings on new public API
- [ ] Updated README if adding user-facing features
- [ ] No new required dependencies (optional deps are fine)
