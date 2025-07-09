#!/usr/bin/env python3
"""
Script to find and copy the latest logs from a directory structure.
Log structure: logs/<model>/<question_prompt>/<datetime>-<judge_prompt>/*.eval
"""

import argparse
import os
import re
import shutil
from datetime import datetime
from pathlib import Path


def parse_datetime_from_path(path_str):
    """Extract datetime from path like '20250707-150237-faithfulness_narrow_0703'"""
    # Look for datetime pattern: YYYYMMDD-HHMMSS
    datetime_pattern = r"(\d{8}-\d{6})"
    match = re.search(datetime_pattern, path_str)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S")
        except ValueError:
            return None
    return None


def find_latest_logs(logs_dir, output_dir, min_date=None, dry_run=False):
    """
    Find the latest logs for each model/question/judge combination and copy them.
    Only processes the hardcoded judge names: monitorability_0624, faithfulness_narrow_0703, faithfulness_broad_0627
    Only copies files created on or after min_date if specified.

    Args:
        logs_dir (str): Path to the logs directory
        output_dir (str): Path to the output directory where logs will be copied
        min_date (datetime): Only copy files created on or after this date (optional)
        dry_run (bool): If True, only print what would be copied without actually copying
    """
    # Hardcoded judge names to process
    TARGET_JUDGES = ["monitorability_0624", "faithfulness_narrow_0703", "faithfulness_broad_0627"]
    
    logs_path = Path(logs_dir)
    output_path = Path(output_dir)

    if not logs_path.exists():
        print(f"Error: Logs directory '{logs_dir}' does not exist.")
        return

    # Create output directory if it doesn't exist (only if not dry run)
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)

    # Track the latest datetime for each model/question/judge combination
    latest_combinations = {}

    # Walk through the logs directory structure
    for model_dir in logs_path.iterdir():
        if not model_dir.is_dir():
            continue

        model_name = model_dir.name

        for question_dir in model_dir.iterdir():
            if not question_dir.is_dir():
                continue

            question_name = question_dir.name

            for datetime_judge_dir in question_dir.iterdir():
                if not datetime_judge_dir.is_dir():
                    continue

                # Extract datetime and judge prompt from directory name
                dir_name = datetime_judge_dir.name
                dt = parse_datetime_from_path(dir_name)

                if dt is None:
                    print(
                        f"Warning: Could not parse datetime from '{dir_name}', skipping..."
                    )
                    continue

                # Skip if the directory date is before min_date
                if min_date and dt < min_date:
                    continue

                # Extract judge prompt (everything after the datetime part)
                # The datetime format is YYYYMMDD-HHMMSS, so we need to find where it ends
                datetime_str = dt.strftime("%Y%m%d-%H%M%S")
                if dir_name.startswith(datetime_str + "-"):
                    judge_prompt = dir_name[len(datetime_str) + 1:]  # +1 for the dash
                else:
                    judge_prompt = dir_name

                # Only process if this is one of our target judges
                if judge_prompt not in TARGET_JUDGES:
                    continue

                # Create a key for this combination
                combination_key = (model_name, question_name, judge_prompt)

                # Update if this is the latest datetime for this combination
                if (
                    combination_key not in latest_combinations
                    or dt > latest_combinations[combination_key]["datetime"]
                ):
                    latest_combinations[combination_key] = {
                        "datetime": dt,
                        "path": datetime_judge_dir,
                    }

    # Copy the latest logs for each combination
    copied_count = 0
    for (model, question, judge), info in latest_combinations.items():
        source_path = info["path"]
        dt_str = info["datetime"].strftime("%Y-%m-%d_%H-%M-%S")

        # Create the destination directory structure
        dest_dir = output_path / model / question / f"{dt_str}-{judge}"

        # Copy all .eval files from the source directory
        eval_files = list(source_path.glob("*.eval"))
        if eval_files:
            if dry_run:
                print(f"Would copy {len(eval_files)} files from:")
                print(f"  Source: {source_path}")
                print(f"  Destination: {dest_dir}")
                for eval_file in eval_files:
                    print(f"    - {eval_file.name}")
                print()
            else:
                dest_dir.mkdir(parents=True, exist_ok=True)
                for eval_file in eval_files:
                    dest_file = dest_dir / eval_file.name
                    shutil.copy2(eval_file, dest_file)
                    print(f"Copied: {eval_file} -> {dest_file}")
            copied_count += 1
        else:
            print(f"Warning: No .eval files found in {source_path}")

    if dry_run:
        print(
            f"\nDry run summary: Would copy latest logs for {copied_count} model/question/judge combinations"
        )
        print(f"Output directory: {output_path.absolute()}")
    else:
        print(
            f"\nSummary: Copied latest logs for {copied_count} model/question/judge combinations"
        )
        print(f"Output directory: {output_path.absolute()}")


def main():
    parser = argparse.ArgumentParser(description="Copy latest logs based on datetime")
    parser.add_argument("logs_dir", help="Path to the logs directory")
    parser.add_argument("output_dir", help="Path to the output directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without actually copying files",
    )
    parser.add_argument(
        "--min-date",
        type=str,
        help="Only copy files created on or after this date (YYYY-MM-DD)",
    )

    args = parser.parse_args()

    min_date = None
    if args.min_date:
        try:
            min_date = datetime.strptime(args.min_date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format for --min-date. Expected YYYY-MM-DD.")
            return

    find_latest_logs(args.logs_dir, args.output_dir, min_date, args.dry_run)


if __name__ == "__main__":
    main()
