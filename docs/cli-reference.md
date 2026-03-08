# CLI Reference

The `productivity-classify` command lets you classify conversations from the terminal.

## Installation

The CLI is installed automatically with the package:

```bash
pip install ai-productivity-framework
```

## Usage

```
productivity-classify INPUT [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INPUT` | Path to a JSON file or directory of JSON files |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output, -o FILE` | stdout | Write results to a file |
| `--api-key KEY` | None | API key for LLM fallback |
| `--provider {anthropic,openai}` | `anthropic` | LLM provider |
| `--model MODEL` | auto | LLM model for classification |
| `--benchmarks FILE` | built-in | Path to custom benchmarks YAML |
| `--estimate-mode {low,mid,high}` | `low` | Time estimate mode |
| `--json` | false | Output raw JSON |

## Input Format

### Single Conversation

```json
{
  "conversation_id": "optional-id",
  "messages": [
    {
      "role": "user",
      "content": "Draft an email to the marketing team",
      "tool_calls": []
    },
    {
      "role": "assistant",
      "content": "Here's a draft email...",
      "tool_calls": ["send_email"]
    }
  ]
}
```

### Batch (Directory)

Place multiple JSON files in a directory:

```
conversations/
├── conv-001.json
├── conv-002.json
└── conv-003.json
```

Each file follows the single conversation format above.

## Examples

### Classify a single conversation

```bash
$ productivity-classify conversation.json
Activity:    work_support
Confidence:  95%
Time saved:  ~3 min (3-15 min range)
Layer:       2
Outputs:     email
Actions:     send_email
Tokens:      150 output (0 code, 150 prose)
```

### Get JSON output

```bash
$ productivity-classify conversation.json --json
{
  "conversation_id": "test",
  "overall_activity": "work_support",
  "confidence": 0.95,
  "classifier_layer": 2,
  "time_saved_seconds": 180,
  ...
}
```

### Batch classify a directory

```bash
$ productivity-classify conversations/
Conversations:  25
Productive:     18 (72%)
Time saved:     145.0 min
Range:          95.0-310.0 min
LLM calls:      3
Total tokens:   15420

By activity:
  work_creation: 85.0 min
  work_support: 40.0 min
  work_research: 20.0 min

By output:
  document: 45.0 min
  email: 25.0 min
  code: 35.0 min
```

### Save batch results to file

```bash
$ productivity-classify conversations/ --output report.json
Results written to report.json
  25 conversations
  18 productive (72%)
  145.0 min saved
```

### With LLM fallback

```bash
$ productivity-classify conversation.json --api-key sk-ant-api03-...
```

### Custom benchmarks

```bash
$ productivity-classify conversation.json --benchmarks my_benchmarks.yaml --estimate-mode mid
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (file not found, invalid JSON, etc.) |
