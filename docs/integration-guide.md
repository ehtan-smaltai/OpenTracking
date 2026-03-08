# Integration Guide

How to embed the AI Productivity Framework in your application, API, or data pipeline.

## Flask / FastAPI

### FastAPI Example

```python
from fastapi import FastAPI
from pydantic import BaseModel
from productivity_framework import ProductivityClassifier, ConversationMessage

app = FastAPI()
classifier = ProductivityClassifier(estimate_mode="low")


class Message(BaseModel):
    role: str
    content: str
    tool_calls: list[str] = []


class ClassifyRequest(BaseModel):
    conversation_id: str = ""
    messages: list[Message]


@app.post("/classify")
def classify_conversation(req: ClassifyRequest):
    messages = [
        ConversationMessage(
            role=m.role,
            content=m.content,
            tool_calls=m.tool_calls,
        )
        for m in req.messages
    ]
    result = classifier.classify(messages, req.conversation_id)
    return result.to_dict()


@app.post("/classify/batch")
def classify_batch(conversations: list[ClassifyRequest]):
    conv_tuples = []
    for req in conversations:
        messages = [
            ConversationMessage(role=m.role, content=m.content, tool_calls=m.tool_calls)
            for m in req.messages
        ]
        conv_tuples.append((req.conversation_id, messages))

    results = classifier.classify_batch(conv_tuples)
    summary = classifier.aggregate_time_saved(results)
    return {
        "results": [r.to_dict() for r in results],
        "summary": summary,
    }
```

### Flask Example

```python
from flask import Flask, request, jsonify
from productivity_framework import ProductivityClassifier, ConversationMessage

app = Flask(__name__)
classifier = ProductivityClassifier()


@app.post("/classify")
def classify_conversation():
    data = request.json
    messages = [
        ConversationMessage(
            role=m["role"],
            content=m["content"],
            tool_calls=m.get("tool_calls", []),
        )
        for m in data["messages"]
    ]
    result = classifier.classify(messages, data.get("conversation_id", ""))
    return jsonify(result.to_dict())
```

## Webhook / Event-Driven

Process conversations as they complete:

```python
from productivity_framework import classify

def on_conversation_complete(conversation_data: dict):
    """Webhook handler called when a conversation ends."""
    result = classify(conversation_data["messages"])

    # Store result
    save_to_database({
        "conversation_id": conversation_data["id"],
        "activity": result.overall_activity.value,
        "time_saved_seconds": result.time_saved_seconds,
        "outputs": result.outputs,
        "tokens": result.total_output_tokens,
        "classified_at": datetime.utcnow().isoformat(),
    })

    # Alert on high-value conversations
    if result.time_saved_minutes > 30:
        send_notification(f"High-value conversation: saved {result.time_saved_display}")
```

## Batch Pipeline

Process historical conversations from a database or data warehouse:

```python
import json
from productivity_framework import ProductivityClassifier, ConversationMessage

classifier = ProductivityClassifier(estimate_mode="low")

def process_conversations(conversations: list[dict]) -> dict:
    """Process a batch of conversations and return aggregate stats."""
    conv_tuples = []
    for conv in conversations:
        messages = [
            ConversationMessage(
                role=m["role"],
                content=m["content"],
                tool_calls=m.get("tool_calls", []),
                token_count=m.get("token_count", 0),
            )
            for m in conv["messages"]
        ]
        conv_tuples.append((conv["id"], messages))

    results = classifier.classify_batch(conv_tuples)
    summary = classifier.aggregate_time_saved(results)

    # Enrich individual results
    enriched = []
    for conv, result in zip(conversations, results):
        enriched.append({
            "conversation_id": conv["id"],
            "user_id": conv.get("user_id"),
            "activity": result.overall_activity.value,
            "time_saved_seconds": result.time_saved_seconds,
            "time_saved_display": result.time_saved_display,
            "outputs": result.outputs,
            "confidence": result.confidence,
            "classifier_layer": result.classifier_layer,
        })

    return {
        "results": enriched,
        "summary": summary,
    }
```

## Dashboard Metrics

Common metrics you can derive from classification results:

```python
summary = classifier.aggregate_time_saved(results)

# Key metrics for dashboards
metrics = {
    # Productivity
    "hours_saved_this_week": summary["total_time_saved_hours"],
    "productivity_rate": f"{summary['productivity_rate']:.0%}",

    # Volume
    "total_conversations": summary["total_conversations"],
    "productive_conversations": summary["productive_conversations"],

    # Token efficiency
    "total_output_tokens": summary["total_output_tokens"],
    "code_ratio": (
        summary["code_output_tokens"] / summary["total_output_tokens"]
        if summary["total_output_tokens"] > 0 else 0
    ),

    # Top activities
    "top_activity": max(summary["by_activity"], key=summary["by_activity"].get)
        if summary["by_activity"] else "none",

    # Cost efficiency
    "llm_classification_rate": (
        summary["llm_classifications"] / summary["total_conversations"]
        if summary["total_conversations"] > 0 else 0
    ),
}
```

## Storing Results

### JSON

```python
import json

result = classifier.classify(messages)
with open("result.json", "w") as f:
    json.dump(result.to_dict(), f, indent=2)
```

### SQLite / PostgreSQL

```python
import sqlite3

conn = sqlite3.connect("productivity.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS classifications (
        conversation_id TEXT PRIMARY KEY,
        activity TEXT,
        confidence REAL,
        time_saved_seconds INTEGER,
        outputs TEXT,
        classifier_layer INTEGER,
        total_output_tokens INTEGER,
        classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

result = classifier.classify(messages, "conv-123")
conn.execute(
    "INSERT INTO classifications VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
    (
        result.conversation_id,
        result.overall_activity.value,
        result.confidence,
        result.time_saved_seconds,
        json.dumps(result.outputs),
        result.classifier_layer,
        result.total_output_tokens,
    ),
)
conn.commit()
```

## Per-Organization Benchmarks

For multi-tenant applications where each org has different time estimates:

```python
from productivity_framework import ProductivityClassifier, BenchmarkTable

# Cache classifiers per org
_classifiers: dict[str, ProductivityClassifier] = {}

def get_classifier(org_id: str) -> ProductivityClassifier:
    if org_id not in _classifiers:
        # Load org-specific benchmark overrides from your config/database
        overrides = load_org_overrides(org_id)
        table = BenchmarkTable(overrides=overrides)
        _classifiers[org_id] = ProductivityClassifier(benchmark_table=table)
    return _classifiers[org_id]

def classify_for_org(org_id: str, messages, conversation_id: str = ""):
    classifier = get_classifier(org_id)
    return classifier.classify(messages, conversation_id)
```
