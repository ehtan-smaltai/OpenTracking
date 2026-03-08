"""
Command-line interface for the AI Productivity Measurement Framework.

Usage:
    productivity-classify conversation.json
    productivity-classify conversations/ --output report.json
    productivity-classify conversation.json --api-key sk-... --provider anthropic
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .classifier import ProductivityClassifier
from .benchmark_table import BenchmarkTable
from .types import ConversationMessage


def _load_conversation(path: Path) -> tuple[str, list[ConversationMessage]]:
    """Load a conversation from a JSON file."""
    with open(path) as f:
        data = json.load(f)

    conv_id = data.get("conversation_id", path.stem)
    messages = []
    for msg in data.get("messages", []):
        messages.append(ConversationMessage(
            role=msg["role"],
            content=msg["content"],
            tool_calls=msg.get("tool_calls", []),
            tool_results=msg.get("tool_results", []),
            token_count=msg.get("token_count", 0),
        ))

    return conv_id, messages


def _format_result(result) -> dict:
    """Format a ClassificationResult for output."""
    return {
        **result.to_dict(),
        "time_saved_display": result.time_saved_display,
        "time_saved_minutes": result.time_saved_minutes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="productivity-classify",
        description="Classify AI conversations and estimate time saved.",
    )
    parser.add_argument(
        "input",
        help="JSON file or directory of JSON files to classify",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for results (default: stdout)",
    )
    parser.add_argument(
        "--api-key",
        help="API key for LLM fallback (Anthropic or OpenAI)",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider (default: anthropic)",
    )
    parser.add_argument(
        "--model",
        help="LLM model for classification",
    )
    parser.add_argument(
        "--benchmarks",
        help="Path to custom benchmarks YAML file",
    )
    parser.add_argument(
        "--estimate-mode",
        choices=["low", "mid", "high"],
        default="low",
        help="Time estimate mode (default: low)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output raw JSON (default for file output)",
    )

    args = parser.parse_args(argv)
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: {input_path} does not exist", file=sys.stderr)
        return 1

    # Build classifier
    benchmark_table = None
    if args.benchmarks:
        benchmark_table = BenchmarkTable(defaults_path=args.benchmarks)

    classifier = ProductivityClassifier(
        api_key=args.api_key,
        provider=args.provider,
        model=args.model,
        benchmark_table=benchmark_table,
        estimate_mode=args.estimate_mode,
    )

    # Load conversations
    if input_path.is_dir():
        json_files = sorted(input_path.glob("*.json"))
        if not json_files:
            print(f"Error: no JSON files in {input_path}", file=sys.stderr)
            return 1
        conversations = [_load_conversation(f) for f in json_files]
    else:
        conversations = [_load_conversation(input_path)]

    # Classify
    results = classifier.classify_batch(conversations)

    # Format output
    if len(results) == 1 and not args.output:
        # Single conversation, print human-readable
        r = results[0]
        if args.json_output:
            print(json.dumps(_format_result(r), indent=2))
        else:
            print(f"Activity:    {r.overall_activity.value}")
            print(f"Confidence:  {r.confidence:.0%}")
            print(f"Time saved:  {r.time_saved_display}")
            print(f"Layer:       {r.classifier_layer}")
            if r.outputs:
                print(f"Outputs:     {', '.join(r.outputs)}")
            if r.actions_performed:
                print(f"Actions:     {', '.join(r.actions_performed)}")
            print(f"Tokens:      {r.total_output_tokens} output ({r.code_output_tokens} code, {r.prose_output_tokens} prose)")
    else:
        # Multiple conversations or file output
        summary = classifier.aggregate_time_saved(results)
        output = {
            "results": [_format_result(r) for r in results],
            "summary": summary,
        }

        output_json = json.dumps(output, indent=2)

        if args.output:
            Path(args.output).write_text(output_json)
            print(f"Results written to {args.output}")
            print(f"  {summary['total_conversations']} conversations")
            print(f"  {summary['productive_conversations']} productive ({summary['productivity_rate']:.0%})")
            print(f"  {summary['total_time_saved_minutes']} min saved")
        else:
            if args.json_output:
                print(output_json)
            else:
                print(f"Conversations:  {summary['total_conversations']}")
                print(f"Productive:     {summary['productive_conversations']} ({summary['productivity_rate']:.0%})")
                print(f"Time saved:     {summary['total_time_saved_minutes']} min")
                print(f"Range:          {summary['time_saved_range_minutes'][0]}-{summary['time_saved_range_minutes'][1]} min")
                print(f"LLM calls:      {summary['llm_classifications']}")
                print(f"Total tokens:   {summary['total_tokens']}")
                print()
                if summary["by_activity"]:
                    print("By activity:")
                    for activity, minutes in summary["by_activity"].items():
                        print(f"  {activity}: {minutes} min")
                if summary["by_output"]:
                    print("By output:")
                    for output_type, minutes in summary["by_output"].items():
                        print(f"  {output_type}: {minutes} min")

    return 0


if __name__ == "__main__":
    sys.exit(main())
