"""
AI Productivity Measurement Framework

Open-source framework for measuring AI assistant productivity
by classifying conversations and estimating time saved.

3-Layer Pipeline:
  Layer 1 (Signals)  - Extract structured features from conversations (free)
  Layer 2 (Rules)    - Classify clear-cut cases via deterministic rules (free)
  Layer 3 (LLM)      - Classify ambiguous cases via LLM (user's API key)
"""

from .types import (
    ActivityType,
    OutputType,
    ConversationMessage,
    Signal,
    Segment,
    ClassificationResult,
)
from .classifier import ProductivityClassifier
from .benchmark_table import BenchmarkTable

__version__ = "0.1.0"

__all__ = [
    "ProductivityClassifier",
    "BenchmarkTable",
    "ActivityType",
    "OutputType",
    "ConversationMessage",
    "Signal",
    "Segment",
    "ClassificationResult",
]
