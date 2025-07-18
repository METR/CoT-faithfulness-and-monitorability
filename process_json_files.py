#!/usr/bin/env python3
import glob
import json
import os
from typing import Optional


def get_latest_json_file(folder_path: str) -> Optional[str]:
    """Get the latest JSON file in a folder based on filename timestamp."""
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    if not json_files:
        return None
    # Sort by filename (which includes timestamp) and get the latest
    return max(json_files, key=lambda x: os.path.basename(x))


def count_state_correct_true(json_file_path: str) -> int:
    """Count how many state_correct values are true in detailed_data."""
    try:
        with open(json_file_path, "r") as f:
            data = json.load(f)

        detailed_data = data.get("detailed_data", [])
        count = sum(1 for item in detailed_data if item.get("state_correct") is True)
        return count
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Error processing {json_file_path}: {e}")
        return 0


def main():
    # Set base directory
    base_dir = "src/results/faithfulness/Claude 3.7 Sonnet"

    # List of folders to process
    folders = ["deepseek", "default", "grug", "pirate", "shy", "sydney", "tutor", "v0"]

    # Note: I noticed you mentioned "claude" but I see "ani" in the directory structure
    # Adding "ani" to the list as it might be what you meant
    folders.append("ani")

    total_count = 0
    folder_counts: dict[str, int] = {}

    for folder in folders:
        folder_path = os.path.join(base_dir, folder)

        if not os.path.exists(folder_path):
            print(f"Folder {folder} does not exist, skipping...")
            continue

        latest_json = get_latest_json_file(folder_path)

        if latest_json is None:
            print(f"No JSON files found in {folder}")
            folder_counts[folder] = 0
            continue

        count = count_state_correct_true(latest_json)
        folder_counts[folder] = count
        total_count += count

        print(f"{folder}: {count} true values (file: {os.path.basename(latest_json)})")

    print(f"\nTotal count across all folders: {total_count}")

    # Print summary
    print("\nSummary:")
    for folder, count in folder_counts.items():
        print(f"  {folder}: {count}")

    return total_count


if __name__ == "__main__":
    result = main()
