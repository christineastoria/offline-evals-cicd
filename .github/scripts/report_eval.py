#!/usr/bin/env python3
"""
LangSmith evaluation report generator.
Processes evaluation results and creates PR comments with test results.
"""

import argparse
import glob
import json
import os
import sys
from typing import Any, Dict, List

from langsmith import Client


def format_score(value: float | None) -> str:
    """Format score for display."""
    return f"{value:.2f}" if value is not None else "N/A"


def process_config(config_path: str, client: Client) -> Dict[str, Any]:
    """Process a single evaluation config file using project stats API."""
    print(f"Processing evaluation config: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to read config {config_path}: {e}")
        return {}

    experiment_name = config.get("experiment_name")
    dataset_name = config.get("dataset_name")

    if not experiment_name:
        print(f"No experiment_name found in {config_path}")
        return {}
    
    if not dataset_name:
        print(f"WARNING: No dataset_name found in {config_path}")
        return {}

    try:
        print(f"Fetching project stats for: {experiment_name}")
        
        # Use read_project with include_stats for a single, efficient API call
        project = client.read_project(
            project_name=experiment_name, 
            include_stats=True
        )
        
        # Extract feedback stats from project metadata
        feedback_stats = project.feedback_stats or {}
        
        if not feedback_stats:
            print(f"No feedback stats found for: {experiment_name}")
            return {
                "experiment_name": experiment_name,
                "dataset_name": dataset_name,
                "error": "No feedback statistics available for this experiment"
            }
        
        print(f"Retrieved stats for {len(feedback_stats)} feedback keys")
        
        table_rows = []
        
        # Process feedback stats directly from project metadata
        for key, stats in feedback_stats.items():
            # stats typically has: avg, count, and possibly other aggregates
            avg_score = stats.get('avg')
            num_runs = stats.get('count', 0)
            
            table_rows.append({
                "key": key,
                "avg_score": avg_score,
                "num_runs": num_runs,
            })
        
        # Build explicit URLs with the dataset_name we know
        experiment_url = f"https://smith.langchain.com/o/default/datasets/{dataset_name}/compare?selectedSessions={experiment_name}"
        dataset_url = f"https://smith.langchain.com/o/default/datasets/{dataset_name}"

        return {
            "experiment_name": experiment_name,
            "dataset_name": dataset_name,
            "experiment_url": experiment_url,
            "dataset_url": dataset_url,
            "table_rows": table_rows,
            "num_examples": project.run_count or 0,
        }

    except Exception as e:
        error_msg = str(e)
        # Simplify common LangSmith API errors
        if "Connection error" in error_msg or "Max retries exceeded" in error_msg:
            error_msg = "LangSmith API connection failed. Please check network connectivity."
        elif "api.smith.langchain.com" in error_msg:
            error_msg = "LangSmith API request failed. Please try again later."
        
        print(f"Error processing experiment {experiment_name}: {error_msg}")
        return {"experiment_name": experiment_name, "dataset_name": dataset_name, "error": error_msg}


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
                # Truncate long error messages to keep report readable
                error_msg = result['error']
                if len(error_msg) > 200:
                    error_msg = error_msg[:200] + "... (truncated)"
                f.write(f"**Error:** {error_msg}\n\n")
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

