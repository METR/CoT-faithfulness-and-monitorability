#!/usr/bin/env python3
"""
Summarize running main.py jobs in a table, extracting key arguments from the command lines.
"""

import re
import subprocess
from collections import defaultdict

# Arguments to extract from the command line
KEY_ARGS = [
    "--model",
    "--base_model",
    "--question_prompt",
    "--judge_prompt",
    "--filtered_csv",
    "--test-monitor-false-positives",
    "--temperature",
    "--batch_size",
    "--max_connections",
    "--epochs",
]

# Run the ps command and get output
ps_cmd = "ps xf | grep main.py | grep -v bash | grep -v grep"
proc = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
lines = [l.strip() for l in proc.stdout.strip().split("\n") if l.strip()]


# Parse each line for arguments
def parse_args_from_cmd(cmd):
    args = {}
    for key in KEY_ARGS:
        # Handle boolean flags (e.g., --test-monitor-false-positives)
        if re.search(rf"{re.escape(key)}( |$)", cmd):
            if (
                key.startswith("--test-")
                or key.startswith("--score_")
                or key.startswith("--redteam")
            ):
                args[key] = True
                continue
        # Handle key-value pairs
        m = re.search(rf"{re.escape(key)} ([^ ]+)", cmd)
        if m:
            args[key] = m.group(1)
    return args


# Collect process info
data = []
for line in lines:
    # Extract PID and command
    m = re.match(r"\s*(\d+) .*python main.py(.*)", line)
    if not m:
        continue
    pid = m.group(1)
    cmd_args = m.group(2)
    args = parse_args_from_cmd(cmd_args)
    args["pid"] = pid
    args["cmd"] = cmd_args.strip()
    data.append(args)

if not data:
    print("No running main.py jobs found.")
    exit(0)

# Group by (model, question_prompt, judge_prompt)
groups = defaultdict(list)
for d in data:
    model = d.get("--model", "?")
    qprompt = d.get("--question_prompt", "?")
    jprompt = d.get("--judge_prompt", "?")
    groups[(model, qprompt, jprompt)].append(d)

# Print summary table
print("\nSummary of running main.py jobs:\n")
header = f"{'Model':<32} {'Question Prompt':<40} {'Judge Prompt':<40} {'Count':<5}"
print(header)
print("-" * len(header))
for (model, qprompt, jprompt), procs in sorted(groups.items()):
    print(f"{model:<32} {qprompt:<40} {jprompt:<40} {len(procs):<5}")

# Print detailed table
print("\nDetailed process list:\n")
detail_header = f"{'PID':<8} {'Model':<32} {'Base Model':<32} {'QPrompt':<30} {'JPrompt':<30} {'Batch':<6} {'Temp':<6} {'Epochs':<6} {'MaxConn':<8} {'Filtered CSV':<40} {'Flags':<20}"
print(detail_header)
print("-" * len(detail_header))
for d in data:
    flags = []
    for flag in ["--test-monitor-false-positives"]:
        if d.get(flag):
            flags.append(flag)
    print(
        f"{d.get('pid', ''):<8} {d.get('--model', ''):<32} {d.get('--base_model', ''):<32} {d.get('--question_prompt', ''):<30} {d.get('--judge_prompt', ''):<30} {d.get('--batch_size', ''):<6} {d.get('--temperature', ''):<6} {d.get('--epochs', ''):<6} {d.get('--max_connections', ''):<8} {d.get('--filtered_csv', ''):<40} {' '.join(flags):<20}"
    )
