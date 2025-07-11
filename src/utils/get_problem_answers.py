import pandas as pd
from inspect_ai.dataset import Dataset, FieldSpec, hf_dataset
import random

if __name__ == "__main__":
    # generate CLUE_TARGETS

    random.seed(42)

    dataset = hf_dataset(
        "metr-evals/hard-math-v0",
        split="train",
        sample_fields=FieldSpec(input="Updated Question", target="Updated Answer"),
        shuffle=False,
        auto_id=True,
    )

    dataset = dataset.filter(lambda sample: sample.target.isdigit())

    accuracy_df = pd.read_csv("problem_difficulty/claude-3-7-sonnet-latest_hard-math-v0_difficulty-10-epochs.csv")
    accuracy_df = accuracy_df[accuracy_df["avg_accuracy"] == 0]
    filtered_problems = accuracy_df["problem_id"].tolist()

    dataset = dataset.filter(lambda sample: sample.id in filtered_problems)

    targets = [int(sample.target) for sample in dataset]
    unique_targets = list(set(targets))
    random_100_targets = random.sample(unique_targets, 100)
    print(sorted(random_100_targets))
    print(sorted(unique_targets))
