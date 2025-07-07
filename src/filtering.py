import os
from copy import deepcopy
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from inspect_ai import Task, eval, task
from inspect_ai.dataset import Dataset, FieldSpec, hf_dataset
from inspect_ai.model import CachePolicy, GenerateConfig
from inspect_ai.scorer import match
from inspect_ai.solver import generate
from inspect_ai.util import DisplayType

from utils.batch import get_batch_args
from utils.question_prompts.default_positive_int import DEFAULT_QUESTION_PREFIX


@task
def free_response(
    dataset: Dataset,
    epochs: int = 10,
    temperature: float = 0.6,
    limit: int = 100,
    batch_size: int = 0,
) -> Task:
    dataset = deepcopy(dataset)
    dataset = dataset[:limit]
    batch_args = get_batch_args(batch_size)

    return Task(
        dataset=dataset,
        solver=generate(cache=CachePolicy(expiry=None), **batch_args),
        scorer=match(),
        config=GenerateConfig(
            temperature=temperature,
            max_tokens=32_000,
            reasoning_tokens=30_000,
            **batch_args,
        ),
        epochs=epochs,
    )


def get_problem_difficulty(
    reasoning_model: str,
    display: DisplayType = "none",
    epochs: int = 10,
    log_dir: str | None = None,
    temperature: float = 0.6,
    max_connections: int = 50,
    limit: int = 100,
    filtered_csv: str | None = None,
    prompt_suffix: str = "",
    prompt_template: str = DEFAULT_QUESTION_PREFIX,
    use_nonzero_accuracy: bool = False,
    batch_size: int = 0,
) -> Tuple[Dataset, Dict[str, List[float]]]:
    dataset = hf_dataset(
        "metr-evals/hard-math-v0",
        split="train",
        sample_fields=FieldSpec(input="Updated Question", target="Updated Answer"),
        shuffle=False,
        auto_id=True,
    )

    dataset = dataset.filter(lambda sample: sample.target.isdigit())
    problem_accuracies: Dict[str, List[float]] = {}
    dataset = dataset[:limit]
    for sample in dataset:
        sample.target = str(int(sample.target))


    if filtered_csv:
        accuracy_df = pd.read_csv(filtered_csv)
        if use_nonzero_accuracy:
            accuracy_df = accuracy_df[accuracy_df["avg_accuracy"] > 0]
        else:
            accuracy_df = accuracy_df[accuracy_df["avg_accuracy"] == 0]

        filtered_problems = accuracy_df["problem_id"].tolist()
    else:
        for sample in dataset:
            sample.input = prompt_template + sample.input + prompt_suffix
        evalscore = eval(
            free_response(
                dataset=dataset,
                epochs=epochs,
                temperature=temperature,
                limit=limit,
                batch_size=batch_size,
            ),
            model=reasoning_model,
            display=display,
            max_connections=max_connections,
            log_dir=os.path.join(log_dir, "reasoning") if log_dir else None,
        )

        samples = evalscore[0].samples
        for sample in samples:
            problem_id = sample.id
            if sample.scores:
                first_scorer = next(iter(sample.scores))
                is_correct = sample.scores[first_scorer].value == "C"  # CORRECT
                if problem_id not in problem_accuracies:
                    problem_accuracies[problem_id] = []
                problem_accuracies[problem_id].append(float(is_correct))

        filtered_problems = []
        for problem_id, accuracies in problem_accuracies.items():
            avg_accuracy = np.mean(accuracies)
            if use_nonzero_accuracy and avg_accuracy > 0:
                filtered_problems.append(problem_id)
            elif not use_nonzero_accuracy and avg_accuracy == 0:
                filtered_problems.append(problem_id)

    accuracy_condition = "> 0" if use_nonzero_accuracy else "== 0"
    print(f"Using {len(filtered_problems)} problems with accuracy {accuracy_condition}")

    dataset = dataset.filter(lambda sample: sample.id in filtered_problems)

    return dataset, problem_accuracies


def calculate_difficulty_scores(
    problem_accuracies: Dict[str, List[float]],
) -> pd.DataFrame:
    difficulty_scores = []
    for problem_id, accuracies in problem_accuracies.items():
        avg_accuracy = np.mean(accuracies)
        std_accuracy = np.std(accuracies)
        difficulty_scores.append(
            {
                "problem_id": problem_id,
                "avg_accuracy": avg_accuracy,
                "difficulty_score": 1
                - avg_accuracy,  # Higher score means more difficult
                "std_accuracy": std_accuracy,
                "num_epochs": len(accuracies),
            }
        )

    return pd.DataFrame(difficulty_scores).sort_values(
        "difficulty_score", ascending=False
    )


def plot_difficulty_distribution(
    model_name: str,
    difficulty_df: pd.DataFrame,
    dataset_name: str,
) -> None:
    """
    Plot a histogram of the avg_accuracy distribution in the difficulty dataframe.

    Args:
        difficulty_df: DataFrame containing problem difficulty data
        output_file: Path where to save the histogram image
    """
    plt.figure(figsize=(10, 6))
    plt.hist(
        difficulty_df["avg_accuracy"],
        bins=100,
        alpha=0.75,
        color="skyblue",
        edgecolor="black",
    )
    plt.xlabel("Average Accuracy")
    plt.ylabel("Number of Problems")
    plt.title(f"Distribution of {model_name} Average Accuracy for {dataset_name}")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.show()


if __name__ == "__main__":
    # Example usage
    reasoning_model = "together/Qwen/Qwen3-235B-A22B-fp8-tput"
    temperature = 0.6
    epochs = 10
    limit = 200
    max_connections = 2000
    dataset_name = "hard-math-v0"
    batch_size = 2000

    print(f"Running problem difficulty analysis with {epochs} epochs...")
    _, problem_accuracies = get_problem_difficulty(
        reasoning_model=reasoning_model,
        epochs=epochs,
        limit=limit,
        max_connections=max_connections,
        display="full",
        temperature=temperature,
        batch_size=batch_size,
    )

    # Calculate and display difficulty scores
    difficulty_df = calculate_difficulty_scores(problem_accuracies)

    # Save results to CSV
    output_dir = "problem_difficulty"
    os.makedirs(output_dir, exist_ok=True)
    output_file = (
        f"{output_dir}/{reasoning_model.split('/')[-1]}_{dataset_name}_difficulty.csv"
    )
    difficulty_df.to_csv(output_file, index=False)
    print(f"\nFull results with length {len(difficulty_df)} saved to {output_file}")

    # Plot the distribution of problem difficulties
    plot_difficulty_distribution(reasoning_model, difficulty_df, dataset_name)
