import json

import numpy as np

# Path to the JSON file
json_path = "results/monitorability/Claude 3.7 Sonnet/moe_v4_positive_int/20250714-092430-monitorability_0624-positive-int.json"

# Read the JSON file
with open(json_path, "r") as f:
    data = json.load(f)

faithfulness_scores = data["faithfulness_scores"]

mean_score = np.mean(faithfulness_scores)
median_score = np.median(faithfulness_scores)
p10 = np.percentile(faithfulness_scores, 10)
p90 = np.percentile(faithfulness_scores, 90)

print(f"Mean faithfulness score: {mean_score:.4f}")
print(f"Median faithfulness score: {median_score:.4f}")
print(f"10th percentile: {p10:.4f}")
print(f"90th percentile: {p90:.4f}")
