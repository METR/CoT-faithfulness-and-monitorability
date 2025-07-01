#!/usr/bin/env python3
"""
Script to organize graph files into a single folder with ordered naming.
"""

import glob
import os
import re
import shutil
from datetime import datetime
from pathlib import Path


def organize_graphs():
    """Copy graph files to results_grid/ with ordered naming."""

    # Define the ordering
    model_order = ["Claude 3.7 Sonnet", "Claude 4 Opus", "Qwen3-235B"]

    question_prompt_order = [
        "default",
        "moe_v4",
        "grug",
        "jailbreak_0614",
        "cheater_ai",
        "general_instructive",
        "tcgs_non_instructive",
    ]

    judge_prompt_order = [
        "faithfulness_broad_0627",
        "faithfulness_narrow_0627",
        "monitorability_0624",
    ]

    # Create output directory with datetime stamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"results_grid_{timestamp}")
    output_dir.mkdir(exist_ok=True)

    counter = 1
    copied_files = []

    for model in model_order:
        for question_prompt in question_prompt_order:
            for judge_prompt in judge_prompt_order:
                faithfulness_or_monitorability = (
                    "faithfulness"
                    if "faithfulness" in judge_prompt
                    else "monitorability"
                )

                # Look for directories matching the pattern with datetime
                # Pattern: */model/config/*datetime*-judge_prompt*
                base_pattern = f"results/graphs/{faithfulness_or_monitorability}/{model}/{question_prompt}/*{judge_prompt}"

                # Find all matching directories
                matching_dirs = glob.glob(base_pattern, recursive=True)

                if matching_dirs:
                    # Extract datetime from directory names and find the latest
                    latest_dir = None
                    latest_datetime = None

                    for dir_path in matching_dirs:
                        dir_name = Path(dir_path).name
                        # Extract datetime from directory name (format: YYYYMMDD-HHMMSS-judge_prompt)
                        datetime_match = re.match(r"(\d{8}-\d{6})-", dir_name)
                        if datetime_match:
                            dir_datetime = datetime.strptime(
                                datetime_match.group(1), "%Y%m%d-%H%M%S"
                            )
                            if (
                                latest_datetime is None
                                or dir_datetime > latest_datetime
                            ):
                                latest_datetime = dir_datetime
                                latest_dir = dir_path

                    if latest_dir and latest_datetime:
                        # Look for the propensity_thresh0.95.png file in the latest directory
                        propensity_file = Path(latest_dir) / "propensity_thresh0.95.png"

                        if propensity_file.exists():
                            source = propensity_file
                            # Create ordered filename with datetime
                            file_ext = source.suffix
                            # Use the already parsed datetime to create the string
                            datetime_str = latest_datetime.strftime("%Y%m%d-%H%M%S")
                            ordered_name = f"{counter:02d}_{faithfulness_or_monitorability}_{model.replace(' ', '_')}_{question_prompt}_{judge_prompt}_{datetime_str}{file_ext}"
                            dest = output_dir / ordered_name

                            # Copy file
                            shutil.copy2(source, dest)
                            copied_files.append((str(source), str(dest)))
                            counter += 1
                            print(f"Copied: {source} -> {dest}")
                        else:
                            print(
                                f"Warning: propensity_thresh0.95.png not found in {latest_dir}"
                            )
                    else:
                        print(
                            f"Warning: No valid datetime found for {model}/{question_prompt}/{judge_prompt}"
                        )
                else:
                    print(
                        f"Warning: No directories found for {model}/{question_prompt}/{judge_prompt}"
                    )

    print(f"\nSummary:")
    print(f"Total files copied: {len(copied_files)}")
    print(f"Output directory: {output_dir.absolute()}")


if __name__ == "__main__":
    organize_graphs()
