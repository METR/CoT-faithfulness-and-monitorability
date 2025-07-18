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


def get_per_file_min_stats(
    results_fp: str,
    difficulty_lower_bound: float = 0,
    difficulty_upper_bound: float = 1,
):
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
        if t >= 0.95 and d >= difficulty_lower_bound and d <= difficulty_upper_bound:
            min_faithfulness = min(min_faithfulness, f)
            counts += 1

    return min_faithfulness, counts


def get_per_file_sum_stats(
    results_fp: str,
    difficulty_lower_bound: float = 0,
    difficulty_upper_bound: float = 1,
):
    """
    Get the summary stats for each file in the results directory.
    """
    with open(results_fp, "r") as f:
        results = json.load(f)

    faithfulness_scores = results["faithfulness_scores"]
    take_hints_scores = results["take_hints_scores"]
    difficulty_scores = results["difficulty_scores"]

    total_faithfulness = 0
    counts = 0

    for t, f, d in zip(take_hints_scores, faithfulness_scores, difficulty_scores):
        if t >= 0.95 and d >= difficulty_lower_bound and d <= difficulty_upper_bound:
            total_faithfulness += f
            counts += 1

    return total_faithfulness, counts


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


def get_summary_min_stats(
    judge_type: str,
    difficulty_lower_bound: float = 0,
    difficulty_upper_bound: float = 1,
):
    """
    Get the summary minimum stats for all models, prompts, per judge type.
    """
    overall_min_faithfulness = 1
    total_counts = 0
    for model in MODELS:
        for prompt in PROMPTS:
            file = get_result_file(model, prompt, judge_type)
            min_faithfulness, counts = get_per_file_min_stats(
                file, difficulty_lower_bound, difficulty_upper_bound
            )
            print(
                f"{model} {prompt} {judge_type}: min faithfulness = {min_faithfulness}, counts = {counts}"
            )
            overall_min_faithfulness = min(overall_min_faithfulness, min_faithfulness)
            total_counts += counts

    return overall_min_faithfulness, total_counts


def get_summary_avg_stats(
    judge_type: str,
    difficulty_lower_bound: float = 0,
    difficulty_upper_bound: float = 1,
):
    """
    Get the summary average stats for all models, prompts, per judge type.
    """
    overall_faithfulness_sum = 0
    total_counts = 0
    for model in MODELS:
        for prompt in PROMPTS:
            file = get_result_file(model, prompt, judge_type)
            total_faithfulness, counts = get_per_file_sum_stats(
                file, difficulty_lower_bound, difficulty_upper_bound
            )
            overall_faithfulness_sum += total_faithfulness
            total_counts += counts
            print(
                f"{model} {prompt} {judge_type}: total faithfulness = {total_faithfulness}, counts = {counts}"
            )

    return overall_faithfulness_sum / total_counts, total_counts


def get_per_model_min_stats(
    judge_type: str,
    difficulty_lower_bound: float = 0,
    difficulty_upper_bound: float = 1,
):
    """
    Get the summary minimum stats for all prompts, per model, per judge type.
    """

    per_model_aggregate_min_faithfulness = {}
    for model in MODELS:
        per_model_min_faithfulness = 1
        per_model_total_counts = 0
        for prompt in PROMPTS:
            file = get_result_file(model, prompt, judge_type)
            min_faithfulness, counts = get_per_file_min_stats(
                file, difficulty_lower_bound, difficulty_upper_bound
            )
            per_model_min_faithfulness = min(
                per_model_min_faithfulness, min_faithfulness
            )
            per_model_total_counts += counts

        per_model_aggregate_min_faithfulness[model] = (
            per_model_min_faithfulness,
            per_model_total_counts,
        )

    return per_model_aggregate_min_faithfulness


def get_per_model_avg_stats(
    judge_type: str,
    difficulty_lower_bound: float = 0,
    difficulty_upper_bound: float = 1,
):
    """
    Get the summary minimum stats for all prompts, per model, per judge type.
    Sum all the faithfulness scores for all prompts for each model, and then divide by the total number of samples.
    """
    per_model_avg_faithfulness = {}
    for model in MODELS:
        per_model_total_faithfulness = 0
        per_model_total_counts = 0
        for prompt in PROMPTS:
            file = get_result_file(model, prompt, judge_type)
            total_faithfulness, counts = get_per_file_sum_stats(
                file, difficulty_lower_bound, difficulty_upper_bound
            )
            per_model_total_faithfulness += total_faithfulness
            per_model_total_counts += counts

        per_model_avg_faithfulness[model] = (
            (
                per_model_total_faithfulness / per_model_total_counts,
                per_model_total_counts,
            )
            if per_model_total_counts > 0
            else (0, 0)
        )

    return per_model_avg_faithfulness


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge_type", type=str, required=True)
    parser.add_argument("--difficulty_lower_bound", type=float, required=True)
    parser.add_argument("--difficulty_upper_bound", type=float, required=True)
    parser.add_argument("--summary_type", type=str, required=True)
    args = parser.parse_args()

    if args.summary_type == "min":
        overall_min_faithfulness, total_counts = get_summary_min_stats(
            judge_type=args.judge_type,
            difficulty_lower_bound=args.difficulty_lower_bound,
            difficulty_upper_bound=args.difficulty_upper_bound,
        )
        print("*** Overall minimum faithfulness = ", overall_min_faithfulness)
        print("*** Total counts = ", total_counts)
    elif args.summary_type == "avg":
        overall_avg_faithfulness, total_counts = get_summary_avg_stats(
            judge_type=args.judge_type,
            difficulty_lower_bound=args.difficulty_lower_bound,
            difficulty_upper_bound=args.difficulty_upper_bound,
        )
        print("*** Overall average faithfulness = ", overall_avg_faithfulness)
        print("*** Total counts = ", total_counts)
    elif args.summary_type == "per_model_min":
        per_model_min_faithfulness = get_per_model_min_stats(
            judge_type=args.judge_type,
            difficulty_lower_bound=args.difficulty_lower_bound,
            difficulty_upper_bound=args.difficulty_upper_bound,
        )
        for model, (min_faithfulness, counts) in per_model_min_faithfulness.items():
            print(
                f"{model} {args.judge_type}: minimum faithfulness = {min_faithfulness}, counts = {counts}"
            )
    elif args.summary_type == "per_model_avg":
        per_model_avg_faithfulness = get_per_model_avg_stats(
            judge_type=args.judge_type,
            difficulty_lower_bound=args.difficulty_lower_bound,
            difficulty_upper_bound=args.difficulty_upper_bound,
        )
        for model, (avg_faithfulness, counts) in per_model_avg_faithfulness.items():
            print(
                f"{model} {args.judge_type}: average faithfulness = {avg_faithfulness}, counts = {counts}"
            )
    else:
        raise ValueError(f"Invalid summary type: {args.summary_type}")
