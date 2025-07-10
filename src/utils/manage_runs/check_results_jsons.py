#!/usr/bin/env python3
"""
Script to find the latest results JSON files from a directory structure.
Results structure: results/faithfulness|monitorability/<model>/<question_prompt>/<datetime>-<judge_prompt>.json
"""

import argparse
import os
import re
from datetime import datetime
from pathlib import Path


def parse_datetime_from_filename(filename):
    """Extract datetime from filename like '20250704-071728-faithfulness_narrow_0703.json'"""
    # Look for datetime pattern: YYYYMMDD-HHMMSS
    datetime_pattern = r"(\d{8}-\d{6})"
    match = re.search(datetime_pattern, filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S")
        except ValueError:
            return None
    return None


def find_latest_results(results_dir, min_datetime=None):
    """
    Find the latest results JSON files for each judge/model/question combination.
    Only processes the hardcoded judge names: monitorability_0624, faithfulness_narrow_0703, faithfulness_broad_0627
    Only considers files created on or after min_datetime if specified.

    Args:
        results_dir (str): Path to the results directory
        min_datetime (datetime): Only consider files created on or after this datetime (optional)
    """
    # Hardcoded judge names to process
    TARGET_JUDGES = [
        "monitorability_0624",
        "faithfulness_narrow_0703",
        "faithfulness_broad_0627",
    ]

    results_path = Path(results_dir)

    if not results_path.exists():
        print(f"Error: Results directory '{results_dir}' does not exist.")
        return

    # Track the latest datetime for each judge/model/question combination
    latest_combinations = {}

    # Walk through the results directory structure
    for judge_type_dir in results_path.iterdir():
        if not judge_type_dir.is_dir():
            continue

        judge_type = judge_type_dir.name

        for model_dir in judge_type_dir.iterdir():
            if not model_dir.is_dir():
                continue

            model_name = model_dir.name

            for question_dir in model_dir.iterdir():
                if not question_dir.is_dir():
                    continue

                question_name = question_dir.name

                # Skip folders that don't end with _positive_int (unless they're the base folders)
                # This ensures we only process the _positive_int variants
                if not question_name.endswith("_positive_int"):
                    continue

                # Look for JSON files in the question directory
                for json_file in question_dir.glob("*.json"):
                    # Extract datetime and judge prompt from filename
                    filename = json_file.name
                    dt = parse_datetime_from_filename(filename)

                    if dt is None:
                        print(
                            f"Warning: Could not parse datetime from '{filename}', skipping..."
                        )
                        continue

                    # Skip if the file date is before min_datetime
                    if min_datetime and dt < min_datetime:
                        continue

                        # Extract judge prompt (everything after the datetime part, before .json)
                    # The datetime format is YYYYMMDD-HHMMSS, so we need to find where it ends
                    datetime_str = dt.strftime("%Y%m%d-%H%M%S")
                    if filename.startswith(datetime_str + "-"):
                        judge_prompt = filename[
                            len(datetime_str) + 1 : -5
                        ]  # +1 for the dash, -5 for .json

                        # Handle the case where the filename ends with -positive-int
                        # The judge prompt is everything before the -positive-int part
                        if judge_prompt.endswith("-positive-int"):
                            judge_prompt = judge_prompt[:-13]  # Remove "-positive-int"
                    else:
                        judge_prompt = filename[:-5]  # Remove .json extension

                    # Only process if this is one of our target judges
                    if judge_prompt not in TARGET_JUDGES:
                        continue

                    # Create a key for this combination
                    combination_key = (
                        judge_type,
                        model_name,
                        question_name,
                        judge_prompt,
                    )

                    # Update if this is the latest datetime for this combination
                    if (
                        combination_key not in latest_combinations
                        or dt > latest_combinations[combination_key]["datetime"]
                    ):
                        latest_combinations[combination_key] = {
                            "datetime": dt,
                            "path": json_file,
                        }

    # Print the latest results for each combination
    found_count = 0
    for (judge, model, question, judge_prompt), info in latest_combinations.items():
        result_path = info["path"]

        print(f"{result_path}")
        found_count += 1

    if found_count == 0:
        print("No results found matching the criteria.")
    else:
        print(f"Found {found_count} latest result files.")

    # Group results by model
    models_data = {}
    all_questions = set()
    all_judges = set()

    for (
        judge_type,
        model,
        question,
        judge_prompt,
    ), info in latest_combinations.items():
        if model not in models_data:
            models_data[model] = {}

        if question not in models_data[model]:
            models_data[model][question] = {}

        models_data[model][question][judge_prompt] = info["datetime"]
        all_questions.add(question)
        all_judges.add(judge_prompt)

    # Sort for consistent output
    all_questions = sorted(all_questions)
    all_judges = sorted(all_judges)

    # Create table for each model
    for model in sorted(models_data.keys()):
        print(f"\nModel: {model}")
        print("-" * (len(model) + 7))

        # Prepare column widths
        question_col_width = 34
        judge_col_widths = [max(len(judge), 16) + 1 for judge in all_judges]

        # Print header
        header = f"{'Question':<{question_col_width}}"
        for judge, width in zip(all_judges, judge_col_widths):
            header += f"{judge:<{width}}"
        print(header)
        print("-" * len(header))

        # Print rows
        for question in all_questions:
            row = f"{question:<{question_col_width}}"
            for judge, width in zip(all_judges, judge_col_widths):
                if (
                    question in models_data[model]
                    and judge in models_data[model][question]
                ):
                    dt_str = models_data[model][question][judge].strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    row += f"{dt_str:<{width}}"
                else:
                    row += f"{'':<{width}}"
            print(row)


def main():
    parser = argparse.ArgumentParser(
        description="Find latest results JSON files based on datetime"
    )
    parser.add_argument("results_dir", help="Path to the results directory")
    parser.add_argument(
        "--min-datetime",
        type=str,
        help="Only consider files created on or after this datetime (YYYY-MM-DDTHH:MM)",
    )

    args = parser.parse_args()

    min_datetime = None
    if args.min_datetime:
        try:
            min_datetime = datetime.strptime(args.min_datetime, "%Y-%m-%dT%H:%M")
        except ValueError:
            print("Error: Invalid format for --min-datetime. Use 'YYYY-MM-DDTHH:MM'.")
            return

    find_latest_results(args.results_dir, min_datetime)


if __name__ == "__main__":
    main()
