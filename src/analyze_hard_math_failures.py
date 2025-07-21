#!/usr/bin/env python3
"""
Script to analyze what percentage of hard math problems each model gets wrong even after 5 tries.
"""

import os
import pandas as pd
import glob
from pathlib import Path

def analyze_model_performance(csv_path):
    """Analyze a single model's performance on hard math problems."""
    df = pd.read_csv(csv_path)
    
    # Extract model name from filename
    filename = os.path.basename(csv_path)
    model_name = filename.split('_')[0]
    
    # Count total problems
    total_problems = len(df)
    
    # Count problems with 0% accuracy (completely failed after 5 tries)
    completely_failed = len(df[df['avg_accuracy'] == 0.0])
    
    # Count problems with < 20% accuracy (mostly failed)
    mostly_failed = len(df[df['avg_accuracy'] < 0.2])
    
    # Count problems with < 50% accuracy (failed more than succeeded)
    failed_more_than_succeeded = len(df[df['avg_accuracy'] < 0.5])
    
    # Calculate percentages
    pct_completely_failed = (completely_failed / total_problems) * 100
    pct_mostly_failed = (mostly_failed / total_problems) * 100
    pct_failed_more_than_succeeded = (failed_more_than_succeeded / total_problems) * 100
    
    return {
        'model': model_name,
        'total_problems': total_problems,
        'completely_failed': completely_failed,
        'mostly_failed': mostly_failed,
        'failed_more_than_succeeded': failed_more_than_succeeded,
        'pct_completely_failed': pct_completely_failed,
        'pct_mostly_failed': pct_mostly_failed,
        'pct_failed_more_than_succeeded': pct_failed_more_than_succeeded,
        'avg_accuracy_overall': df['avg_accuracy'].mean(),
        'median_accuracy': df['avg_accuracy'].median()
    }

def main():
    # Find all difficulty CSV files
    csv_files = glob.glob("problem_difficulty/*_hard-math-v0_difficulty_positive_int.csv")
    
    if not csv_files:
        print("No hard-math-v0 difficulty CSV files found!")
        return
    
    print("=" * 80)
    print("HARD MATH PROBLEM FAILURE ANALYSIS")
    print("=" * 80)
    print("Analyzing what percentage of hard math problems each model gets wrong after 10 tries")
    print()
    
    results = []
    
    for csv_file in sorted(csv_files):
        try:
            result = analyze_model_performance(csv_file)
            results.append(result)
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Sort by percentage of completely failed problems (descending)
    results.sort(key=lambda x: x['pct_completely_failed'], reverse=True)
    
    # Print results in a nice table format
    print(f"{'Model':<30} {'Total':<6} {'0% Acc':<6} {'<20%':<6} {'<50%':<6} {'Avg Acc':<8} {'Median':<8}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['model']:<30} "
              f"{result['total_problems']:<6} "
              f"{result['pct_completely_failed']:<6.1f}% "
              f"{result['pct_mostly_failed']:<6.1f}% "
              f"{result['pct_failed_more_than_succeeded']:<6.1f}% "
              f"{result['avg_accuracy_overall']:<8.3f} "
              f"{result['median_accuracy']:<8.3f}")
    
    print()
    print("LEGEND:")
    print("- 0% Acc: Percentage of problems with 0% accuracy (completely failed after 5 tries)")
    print("- <20%: Percentage of problems with <20% accuracy (mostly failed)")
    print("- <50%: Percentage of problems with <50% accuracy (failed more than succeeded)")
    print("- Avg Acc: Average accuracy across all problems")
    print("- Median: Median accuracy across all problems")
    
    print()
    print("SUMMARY:")
    print(f"Total models analyzed: {len(results)}")
    
    # Find the worst performing model
    worst_model = max(results, key=lambda x: x['pct_completely_failed'])
    print(f"Worst performing model: {worst_model['model']} ({worst_model['pct_completely_failed']:.1f}% completely failed)")
    
    # Find the best performing model
    best_model = min(results, key=lambda x: x['pct_completely_failed'])
    print(f"Best performing model: {best_model['model']} ({best_model['pct_completely_failed']:.1f}% completely failed)")
    
    # Calculate overall statistics
    avg_completely_failed = sum(r['pct_completely_failed'] for r in results) / len(results)
    avg_mostly_failed = sum(r['pct_mostly_failed'] for r in results) / len(results)
    print(f"Average across all models: {avg_completely_failed:.1f}% completely failed, {avg_mostly_failed:.1f}% mostly failed")

if __name__ == "__main__":
    main() 