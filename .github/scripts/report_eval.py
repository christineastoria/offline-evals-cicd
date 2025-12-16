#!/usr/bin/env python3
"""
LangSmith evaluation report generator.
Processes evaluation results and creates PR comments with test results.
"""

import argparse
import glob
import json
import operator
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

from langsmith import Client

# Operator map for threshold comparisons
OP_MAP = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


def parse_threshold(threshold_str: str) -> tuple:
    """Parse threshold expression and return operator and value."""
    for symbol in sorted(OP_MAP.keys(), key=len, reverse=True):
        if threshold_str.startswith(symbol):
            return OP_MAP[symbol], float(threshold_str[len(symbol) :])
    raise ValueError(f"Invalid threshold format: {threshold_str}")


def format_score(value: Optional[float]) -> str:
    """Format score for display."""
    return f"{value:.2f}" if value is not None else "N/A"


def process_config(config_path: str, client: Client) -> Dict[str, Any]:
    """Process a single evaluation config file."""
    print(f"Processing evaluation config: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to read config {config_path}: {e}")
        return {}

    experiment_name = config.get("experiment_name")
    criteria = config.get("criteria", {})
    dataset_name = config.get("dataset_name")

    if not experiment_name:
        print(f"No experiment_name found in {config_path}")
        return {}

    try:
        runs = list(client.list_runs(project_name=experiment_name))
        if not runs:
            print(f"No runs found for experiment: {experiment_name}")
            return {"experiment_name": experiment_name, "results": []}

        run_ids = [r.id for r in runs]
        feedbacks = client.list_feedback(run_ids=run_ids)

        feedback_by_key = defaultdict(list)
        for fb in feedbacks:
            if fb.score is not None:
                feedback_by_key[fb.key].append(fb.score)

        table_rows = []
        num_passed = 0
        num_failed = 0

        for key, scores in feedback_by_key.items():
            avg_score = sum(scores) / len(scores) if scores else None
            min_score = min(scores) if scores else None
            max_score = max(scores) if scores else None
            num_runs = len(scores)
            threshold_expr = criteria.get(key)
            passed = "N/A"
            check = "–"

            if threshold_expr:
                try:
                    op, value = parse_threshold(threshold_expr)
                    result = op(avg_score, value)
                    passed = "Pass" if result else "Fail"
                    check = threshold_expr
                    if result:
                        num_passed += 1
                    else:
                        num_failed += 1
                except ValueError as e:
                    print(
                        f"Invalid threshold '{threshold_expr}' for key '{key}': {e}"
                    )
                    passed = "Fail"
                    num_failed += 1

            table_rows.append({
                "key": key,
                "avg_score": avg_score,
                "min_score": min_score,
                "max_score": max_score,
                "num_runs": num_runs,
                "threshold": check,
                "passed": passed
            })

        # Get experiment URL
        experiment_url = f"https://smith.langchain.com/o/default/datasets/{dataset_name or 'unknown'}/compare?selectedSessions={experiment_name}"
        
        # Get dataset URL if available
        dataset_url = None
        if dataset_name:
            dataset_url = f"https://smith.langchain.com/o/default/datasets/{dataset_name}"

        return {
            "experiment_name": experiment_name,
            "dataset_name": dataset_name,
            "experiment_url": experiment_url,
            "dataset_url": dataset_url,
            "table_rows": table_rows,
            "num_passed": num_passed,
            "num_failed": num_failed,
            "total": num_passed + num_failed,
            "num_examples": len(runs),
        }

    except Exception as e:
        print(f"Error processing experiment {experiment_name}: {e}")
        return {"experiment_name": experiment_name, "error": str(e)}


# Metric descriptions for common evaluation types
METRIC_DESCRIPTIONS = {
    "trajectory_unordered_match": "Measures if the agent called the correct tools regardless of order",
    "trajectory_exact_match": "Measures if the agent called the exact sequence of tools",
    "response_correctness": "LLM judge evaluation of response accuracy compared to reference",
    "response_relevance": "LLM judge evaluation of response relevance to the question",
    "tool_args_match_score": "Measures accuracy of tool names and arguments used",
    "argument_correctness": "Evaluates if tool arguments match expected values",
}

def get_metric_description(key: str) -> str:
    """Get description for a metric key."""
    # Try exact match first
    if key in METRIC_DESCRIPTIONS:
        return METRIC_DESCRIPTIONS[key]
    
    # Try partial matches for custom metrics
    key_lower = key.lower()
    if "trajectory" in key_lower:
        return "Evaluates the sequence of tools called by the agent"
    elif "correctness" in key_lower or "accuracy" in key_lower:
        return "Evaluates response accuracy"
    elif "relevance" in key_lower:
        return "Evaluates response relevance"
    elif "tool" in key_lower and "arg" in key_lower:
        return "Evaluates tool usage and arguments"
    else:
        return "Custom evaluation metric"


def write_markdown_report(
    results: List[Dict[str, Any]], output_file: str = "eval_comment.md"
):
    """Write evaluation results to markdown file."""
    print(f"Writing report to {output_file}")

    with open(output_file, "w") as f:
        f.write("# Financial Agents Evaluation Results\n\n")

        for result in results:
            experiment_name = result.get("experiment_name", "Unknown")

            if "error" in result:
                f.write(f"## {experiment_name}\n\n")
                f.write(f"**Error:** {result['error']}\n\n")
                continue

            if not result.get("table_rows"):
                f.write(f"## {experiment_name}\n\n")
                f.write("No evaluation results found.\n\n")
                continue

            # Header with link
            f.write(f"## {experiment_name}\n\n")
            
            # Links section
            if result.get("experiment_url"):
                f.write(f"[View Experiment in LangSmith]({result['experiment_url']})\n\n")
            
            if result.get("dataset_name"):
                f.write(f"**Dataset:** {result['dataset_name']}")
                if result.get("dataset_url"):
                    f.write(f" ([view]({result['dataset_url']}))")
                f.write("\n\n")
            
            num_examples = result.get("num_examples", 0)
            f.write(f"**Examples:** {num_examples}\n\n")

            # List metrics with descriptions
            f.write("**Metrics:**\n\n")
            for row in result["table_rows"]:
                avg = format_score(row.get("avg_score"))
                key = row['key']
                description = get_metric_description(key)
                
                f.write(f"- **{key}**: {avg} — {description}\n")

            f.write("\n---\n\n")

    print(f"Report written to {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate LangSmith evaluation reports for PR comments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all evaluation config files
  python report_eval.py

  # Process specific config files
  python report_eval.py evaluation_config__*.json

  # Process single config file
  python report_eval.py evaluation_config__my_experiment.json
        """,
    )

    parser.add_argument(
        "config_files",
        nargs="*",
        help="Evaluation config files to process (default: evaluation_config__*.json)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="eval_comment.md",
        help="Output markdown file (default: eval_comment.md)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Set up LangSmith client
    try:
        client = Client()
    except Exception as e:
        print(f"Failed to initialize LangSmith client: {e}")
        print("Make sure LANGSMITH_API_KEY environment variable is set.")
        sys.exit(1)

    # Determine config files to process
    if args.config_files:
        config_files = args.config_files
    else:
        config_files = glob.glob("evaluation_config__*.json")

    if not config_files:
        print("No evaluation config files found.")
        print("Expected files matching pattern: evaluation_config__*.json")
        sys.exit(1)

    if args.verbose:
        print(f"Found {len(config_files)} config files: {config_files}")

    # Process all config files
    results = []
    for config_path in config_files:
        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            continue

        result = process_config(config_path, client)
        if result:
            results.append(result)

    if not results:
        print("No valid evaluation results to process.")
        sys.exit(1)

    # Write report
    write_markdown_report(results, args.output)

    # Summary
    total_experiments = len(results)
    successful_experiments = sum(1 for r in results if "error" not in r)
    print(
        f"Processed {successful_experiments}/{total_experiments} experiments successfully"
    )


if __name__ == "__main__":
    main()

