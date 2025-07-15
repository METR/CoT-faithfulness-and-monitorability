import sys
import json
from collections import defaultdict

# ANSI escape code for white text on red background
RED_BG_WHITE = '\033[1;37;41m'
RESET = '\033[0m'

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <path_to_json_file>")
    sys.exit(1)

json_path = sys.argv[1]

with open(json_path, 'r') as f:
    data = json.load(f)

# For each problem_id, collect all acknowledged_clue values (in order) where state_correct is true
problem_epochs = defaultdict(list)
max_epochs = 0
for entry in data.get('detailed_data', []):
    if entry.get('state_correct'):
        pid = entry['problem_id']
        problem_epochs[pid].append(1 if entry.get('acknowledged_clue', False) else 0)
        if len(problem_epochs[pid]) > max_epochs:
            max_epochs = len(problem_epochs[pid])

problem_ids = sorted(problem_epochs.keys())

total_0s = 0
total_1s = 0

# Print header
header = ['problem_id'] + [str(i+1) for i in range(max_epochs)]
print('\t'.join(header))

# Print each row
for pid in problem_ids:
    row = [str(pid)]
    values = problem_epochs[pid]
    for v in values:
        if v == 1:
            row.append(f'{RED_BG_WHITE}1{RESET}')
            total_1s += 1
        else:
            row.append('0')
            total_0s += 1
    row += [''] * (max_epochs - len(values))
    print('\t'.join(row))

# Print totals and ratio
print(f"\nTotal 0s: {total_0s}")
print(f"Total 1s: {total_1s}")
total = total_0s + total_1s
if total > 0:
    print(f"Ratio 1s/(0s+1s): {total_1s/total:.4f}")
else:
    print("Ratio 1s/(0s+1s): N/A") 