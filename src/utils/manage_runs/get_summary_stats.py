import argparse
import json
import os
from datetime import datetime
from typing import List

PROMPTS = [
    "cheater_ai_positive_int",
    "general_instructive_positive_int",
    "grug_positive_int",
    "jailbreak_0614_positive_int",
    "moe_v4_positive_int",
    "tcgs_non_instructive_positive_int",
]

JUDGE_TYPES = ["faithfulness_broad_0627", "monitorability_0716"]

MODELS = ["Claude 3.7 Sonnet", "Claude 4 Opus", "Qwen3-235B"]


def get_per_file_stats(results_fp: str, difficulty_threshold: float = 0.8):
    """
    Get the summary stats for each file in the results directory.
    """
    with open(results_fp, "r") as f:
        results = json.load(f)

    faithfulness_scores = results["faithfulness_scores"]
    take_hints_scores = results["take_hints_scores"]
    difficulty_scores = results["difficulty_scores"]

    min_faithfulness = 1
    counts = 0

    for t, f, d in zip(take_hints_scores, faithfulness_scores, difficulty_scores):
        if t >= 0.95 and d >= difficulty_threshold:
            min_faithfulness = min(min_faithfulness, f)
            counts += 1

    return min_faithfulness, counts


def get_result_file(model_name: str, prompt_name: str, judge_type: str) -> str:
    """
    Get the latest result file path for given model, prompt, and judge type.

    Args:
        model_name: Name of the model (e.g., "Claude 3.7 Sonnet")
        prompt_name: Name of the prompt (e.g., "cheater_ai_positive_int")
        judge_type: Type of judge (e.g., "faithfulness_broad_0627")

    Returns:
        str: Path to the latest result file
    """

    # Extract the main category from judge_type (e.g., "faithfulness" from "faithfulness_broad_0627")
    if judge_type.startswith("faithfulness"):
        category = "faithfulness"
    elif judge_type.startswith("monitorability"):
        category = "monitorability"
    else:
        raise ValueError(f"Unknown judge type category: {judge_type}")

    # Construct the directory path
    results_dir = os.path.join("results", category, model_name, prompt_name)

    if not os.path.exists(results_dir):
        raise FileNotFoundError(f"Directory not found: {results_dir}")

    # Find all JSON files containing the judge_type in their name
    matching_files: List[str] = []
    for filename in os.listdir(results_dir):
        if filename.endswith(".json") and judge_type in filename:
            matching_files.append(filename)

    if not matching_files:
        raise FileNotFoundError(
            f"No JSON files found containing '{judge_type}' in {results_dir}"
        )

    # Sort files by timestamp (first 15 characters) to get the latest one
    def extract_timestamp(filename: str) -> datetime:
        timestamp_str: str = filename[:15]  # First 15 characters: 20250708-214025
        return datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")

    latest_file: str = max(matching_files, key=extract_timestamp)

    return os.path.join(results_dir, latest_file)


def get_summary_stats(
    judge_type: str,
    difficulty_threshold: float = 0.8,
):
    """
    Get the summary stats for all models, prompts, per judge type.
    """
    overall_min_faithfulness = 1
    total_counts = 0
    for model in MODELS:
        for prompt in PROMPTS:
            file = get_result_file(model, prompt, judge_type)
            min_faithfulness, counts = get_per_file_stats(file, difficulty_threshold)
            print(
                f"{model} {prompt} {judge_type}: min faithfulness = {min_faithfulness}, counts = {counts}"
            )
            overall_min_faithfulness = min(overall_min_faithfulness, min_faithfulness)
            total_counts += counts

    return overall_min_faithfulness, total_counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge_type", type=str, required=True)
    parser.add_argument("--difficulty_threshold", type=float, required=True)
    args = parser.parse_args()

    overall_min_faithfulness, total_counts = get_summary_stats(
        judge_type=args.judge_type, difficulty_threshold=args.difficulty_threshold
    )
