import json
import sys
import os
import glob
import re
from datetime import datetime
from collections import defaultdict

# ANSI escape code for white text on red background
RED_BG_WHITE = "\033[1;37;41m"
RESET = "\033[0m"

def parse_datetime_from_filename(filename):
    """Extract datetime from filename like '20250704-071728-faithfulness_narrow_0703.json'"""
    # Look for datetime pattern: YYYYMMDD-HHMMSS
    datetime_pattern = r"(\d{8}-\d{6})"
    match = re.search(datetime_pattern, filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S")
        except ValueError:
            return None
    return None

def parse_datetime(datetime_str):
    """Parse datetime string in various formats"""
    formats = [
        "%Y%m%d-%H%M%S",  # 20240115-143000 (from filename pattern)
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%Y%m%d_%H%M%S",
        "%Y%m%d-%H%M%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse datetime: {datetime_str}")

def get_file_datetime(file_path):
    """Extract datetime from filename or use file modification time"""
    filename = os.path.basename(file_path)
    
    # First try to extract datetime from filename using the pattern from check_results_jsons.py
    dt = parse_datetime_from_filename(filename)
    if dt:
        return dt
    
    # Try other common patterns
    patterns = [
        r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})',
        r'(\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2})',
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
        r'(\d{4}-\d{2}-\d{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                return parse_datetime(match.group(1))
            except ValueError:
                continue
    
    # Fall back to file modification time
    return datetime.fromtimestamp(os.path.getmtime(file_path))

def find_latest_files_in_subdirs(folder_path, min_datetime=None):
    """
    Find the latest JSON file in each subdirectory (deepest directory in the tree).
    Only considers files created on or after min_datetime if specified.
    
    Args:
        folder_path (str): Path to the root directory
        min_datetime (datetime): Only consider files created on or after this datetime (optional)
    
    Returns:
        list: List of paths to the latest files in each subdirectory
    """
    latest_files = {}
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(folder_path):
        # Only process directories that contain JSON files (deepest directories)
        json_files = [f for f in files if f.endswith('.json')]
        
        if json_files:
            # Find the latest JSON file in this directory
            latest_file = None
            latest_datetime = None
            
            for json_file in json_files:
                file_path = os.path.join(root, json_file)
                try:
                    file_datetime = get_file_datetime(file_path)
                    
                    # Skip if the file date is before min_datetime
                    if min_datetime and file_datetime < min_datetime:
                        continue
                    
                    # Update if this is the latest file in this directory
                    if latest_datetime is None or file_datetime > latest_datetime:
                        latest_datetime = file_datetime
                        latest_file = file_path
                        
                except Exception as e:
                    print(f"Warning: Could not process {file_path}: {e}")
            
            # Add the latest file from this directory
            if latest_file:
                latest_files[root] = latest_file
    
    return list(latest_files.values())

if len(sys.argv) < 3:
    print(f"Usage: python {sys.argv[0]} <folder_path> <datetime_threshold>")
    print("Example: python {sys.argv[0]} ./results 2024-01-15 14:30:00")
    print("Example: python {sys.argv[0]} ./results 2024-01-15")
    print("Example: python {sys.argv[0]} ./results 20240115-143000")
    sys.exit(1)

folder_path = sys.argv[1]
datetime_threshold_str = " ".join(sys.argv[2:])

try:
    datetime_threshold = parse_datetime(datetime_threshold_str)
except ValueError as e:
    print(f"Error parsing datetime: {e}")
    sys.exit(1)

if not os.path.isdir(folder_path):
    print(f"Error: {folder_path} is not a valid directory")
    sys.exit(1)

# Find the latest files in each subdirectory
filtered_files = find_latest_files_in_subdirs(folder_path, datetime_threshold)

if not filtered_files:
    print(f"No JSON files found after {datetime_threshold}")
    sys.exit(1)

print(f"Processing {len(filtered_files)} latest files after {datetime_threshold}:")
for f in sorted(filtered_files):
    try:
        file_dt = get_file_datetime(f)
        print(f"  - {os.path.relpath(f, folder_path)} ({file_dt.strftime('%Y-%m-%d %H:%M:%S')})")
    except:
        print(f"  - {os.path.relpath(f, folder_path)}")

# For each problem_id, collect all acknowledged_clue values (in order) where state_correct is true
problem_epochs = defaultdict(list)
max_epochs = 0
processed_files = 0

for json_file in filtered_files:
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        
        file_entries = 0
        for entry in data.get("detailed_data", []):
            if entry.get("state_correct"):
                pid = entry["problem_id"]
                problem_epochs[pid].append(1 if entry.get("acknowledged_clue", False) else 0)
                if len(problem_epochs[pid]) > max_epochs:
                    max_epochs = len(problem_epochs[pid])
                file_entries += 1
        
        if file_entries > 0:
            processed_files += 1
            
    except Exception as e:
        print(f"Warning: Error reading {json_file}: {e}")

if not problem_epochs:
    print("No valid data found in the processed files")
    sys.exit(1)

print(f"\nSuccessfully processed {processed_files} files with valid data")

problem_ids = sorted(problem_epochs.keys())

total_0s = 0
total_1s = 0

# Print header
header = ["problem_id"] + [str(i + 1) for i in range(max_epochs)]
print("\n" + "\t".join(header))

# Print each row
for pid in problem_ids:
    row = [str(pid)]
    values = problem_epochs[pid]
    for v in values:
        if v == 1:
            row.append(f"{RED_BG_WHITE}1{RESET}")
            total_1s += 1
        else:
            row.append("0")
            total_0s += 1
    row += [""] * (max_epochs - len(values))
    print("\t".join(row))

# Print totals and ratio
total = total_0s + total_1s
print(f"\nFPR: {100 * (total_1s / total):.2f}%")
print(f"Total 0s: {total_0s}")
print(f"Total 1s: {total_1s}")
if total > 0:
    print(f"Ratio 1s/(0s+1s): {total_1s / total:.4f}")
else:
    print("Ratio 1s/(0s+1s): N/A")
