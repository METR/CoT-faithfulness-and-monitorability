import argparse
import json

import numpy as np

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Compute faithfulness score statistics from a JSON file."
)
parser.add_argument(
    "json_path", type=str, help="Path to the JSON file containing faithfulness scores."
)
args = parser.parse_args()
json_path = args.json_path

# Read the JSON file
with open(json_path, "r") as f:
    data = json.load(f)

faithfulness_scores = data["faithfulness_scores"]

mean_score = np.mean(faithfulness_scores)
median_score = np.median(faithfulness_scores)
p10 = np.percentile(faithfulness_scores, 10)
p90 = np.percentile(faithfulness_scores, 90)

print(f"FNR: {100 * (1 - mean_score):.2f}%")
print(f"Mean faithfulness score: {mean_score:.4f}")
print(f"Median faithfulness score: {median_score:.4f}")
print(f"10th percentile: {p10:.4f}")
print(f"90th percentile: {p90:.4f}")
print(f"Number of samples: {len(faithfulness_scores)}")
