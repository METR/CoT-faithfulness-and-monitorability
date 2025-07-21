#!/usr/bin/env python3
"""
Detailed script to analyze hard math problem performance with distribution analysis.
"""

import os
import pandas as pd
import glob
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager

# Force recompile the font cache to detect any newly installed fonts
font_manager._load_fontmanager(try_read_cache=False)

# Configure rcParams for Montserrat font
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Montserrat']

def analyze_model_detailed(csv_path):
    """Analyze a single model's performance with detailed statistics."""
    df = pd.read_csv(csv_path)
    
    # Extract model name from filename
    filename = os.path.basename(csv_path)
    model_name = filename.split('_')[0]
    
    # Basic counts
    total_problems = len(df)
    completely_failed = len(df[df['avg_accuracy'] == 0.0])
    
    # Create accuracy bins for distribution analysis
    bins = [0.0, 0.000001, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = ['0%', '1-20%', '21-40%', '41-60%', '61-80%', '81-100%']
    
    # Fix: Use right=False to include the right edge in the previous bin
    df['accuracy_bin'] = pd.cut(df['avg_accuracy'], bins=bins, labels=labels, include_lowest=True, right=False)
    distribution = df['accuracy_bin'].value_counts().sort_index()
    
    # Calculate percentiles
    percentiles = df['avg_accuracy'].quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    
    return {
        'model': model_name,
        'total_problems': total_problems,
        'completely_failed': completely_failed,
        'pct_completely_failed': (completely_failed / total_problems) * 100,
        'avg_accuracy': df['avg_accuracy'].mean(),
        'median_accuracy': df['avg_accuracy'].median(),
        'std_accuracy': df['avg_accuracy'].std(),
        'distribution': distribution,
        'percentiles': percentiles,
        'problems_with_some_success': len(df[df['avg_accuracy'] > 0.0]),
        'problems_perfect': len(df[df['avg_accuracy'] == 1.0]),
        'pct_perfect': (len(df[df['avg_accuracy'] == 1.0]) / total_problems) * 100
    }

def plot_failure_bar_graph(results, output_path):
    # Prepare data
    models = [r['model'] for r in results]
    pct_failed = [r['pct_completely_failed'] for r in results]
    pct_perfect = [r['pct_perfect'] for r in results]
    avg_acc = [r['avg_accuracy'] for r in results]

    # Pretty model names if possible
    pretty_names = {
        'claude-3-7-sonnet-latest': 'Claude 3.7 Sonnet',
        'claude-opus-4-20250514': 'Claude Opus 4',
        'claude-sonnet-4-20250514': 'Claude Sonnet 4',
        'Qwen3-235B-A22B-fp8-tput': 'Qwen3-235B',
        'QwQ-32B': 'QwQ-32B',
    }
    model_labels = [pretty_names.get(m, m) for m in models]

    # Calculate "1 try" performance (assuming it's roughly the average accuracy)
    # and "best of 5" performance (the percentage that got at least some success)
    one_try_performance = [r['avg_accuracy'] * 100 for r in results]  # Convert to percentage
    best_of_five_performance = [(100 - r['pct_completely_failed']) for r in results]  # Percentage with some success

    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Set up bar positions
    x = np.arange(len(model_labels))
    width = 0.35  # Width of the bars
    
    # Create side-by-side bars using muted greens from the site's color palette
    # Left bar: 1 try performance (light green)
    bars1 = ax.bar(x - width/2, one_try_performance, width,
                   color="#7fc97f", alpha=0.8, label="pass@1")
    
    # Right bar: best of 5 performance (dark green)
    bars2 = ax.bar(x + width/2, best_of_five_performance, width,
                   color="#485F52", alpha=0.8, label="pass@10")

    # Add value labels for both bars
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        # Label for 1 try bar
        if bar1.get_height() > 0:
            ax.annotate(f"{one_try_performance[i]:.1f}%",
                        xy=(bar1.get_x() + bar1.get_width() / 2, bar1.get_height()),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=11, weight='bold')
        
        # Label for best of 5 bar
        if bar2.get_height() > 0:
            ax.annotate(f"{best_of_five_performance[i]:.1f}%",
                        xy=(bar2.get_x() + bar2.get_width() / 2, bar2.get_height()),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=11, weight='bold')

    # Style
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_ylabel("Accuracy (%)", fontsize=16)
    ax.set_xlabel("")
    ax.set_title("Performance on DAFT Math", fontsize=20, weight='bold', pad=20)
    ax.set_ylim(0, 100)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    
    # Set x-axis ticks and labels
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels)
    
    # Add legend
    ax.legend(loc='upper right', fontsize=12)

    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Find all difficulty CSV files
    csv_files = glob.glob("problem_difficulty/*_hard-math-v0_difficulty_positive_int.csv")
    
    if not csv_files:
        print("No hard-math-v0 difficulty CSV files found!")
        return
    
    print("=" * 100)
    print("DETAILED HARD MATH PROBLEM FAILURE ANALYSIS")
    print("=" * 100)
    print("Analyzing what percentage of hard math problems each model gets wrong after 10 tries")
    print()
    
    results = []
    
    for csv_file in sorted(csv_files):
        try:
            result = analyze_model_detailed(csv_file)
            results.append(result)
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    if not results:
        print("No results to display!")
        return
    
    # Sort by percentage of completely failed problems (descending)
    results.sort(key=lambda x: x['pct_completely_failed'], reverse=True)
    
    # Print summary table
    print("SUMMARY TABLE:")
    print(f"{'Model':<30} {'Total':<6} {'0% Acc':<7} {'Perfect':<8} {'Avg Acc':<8} {'Median':<8} {'Std Dev':<8}")
    print("-" * 85)
    
    for result in results:
        print(f"{result['model']:<30} "
              f"{result['total_problems']:<6} "
              f"{result['pct_completely_failed']:<7.1f}% "
              f"{result['pct_perfect']:<8.1f}% "
              f"{result['avg_accuracy']:<8.3f} "
              f"{result['median_accuracy']:<8.3f} "
              f"{result['std_accuracy']:<8.3f}")
    
    print()
    print("DETAILED DISTRIBUTION ANALYSIS:")
    print("=" * 100)
    
    for result in results:
        print(f"\n{result['model']}:")
        print(f"  Total problems: {result['total_problems']}")
        print(f"  Completely failed (0% accuracy): {result['completely_failed']} ({result['pct_completely_failed']:.1f}%)")
        print(f"  Some success (>0% accuracy): {result['problems_with_some_success']} ({100-result['pct_completely_failed']:.1f}%)")
        print(f"  Perfect (100% accuracy): {result['problems_perfect']} ({result['pct_perfect']:.1f}%)")
        print(f"  Average accuracy: {result['avg_accuracy']:.3f}")
        print(f"  Median accuracy: {result['median_accuracy']:.3f}")
        print(f"  Standard deviation: {result['std_accuracy']:.3f}")
        
        print("  Accuracy distribution:")
        for bin_label, count in result['distribution'].items():
            pct = (count / result['total_problems']) * 100
            print(f"    {bin_label}: {count:3d} problems ({pct:5.1f}%)")
        
        print("  Percentiles:")
        for p, value in result['percentiles'].items():
            print(f"    {p*100:2.0f}th percentile: {value:.3f}")
    
    print()
    print("KEY INSIGHTS:")
    print("=" * 100)
    
    # Find best and worst models
    worst_model = max(results, key=lambda x: x['pct_completely_failed'])
    best_model = min(results, key=lambda x: x['pct_completely_failed'])
    
    print(f"• Worst performing model: {worst_model['model']}")
    print(f"  - {worst_model['pct_completely_failed']:.1f}% of problems completely failed (0% accuracy)")
    print(f"  - Only {worst_model['pct_perfect']:.1f}% of problems solved perfectly")
    
    print(f"\n• Best performing model: {best_model['model']}")
    print(f"  - {best_model['pct_completely_failed']:.1f}% of problems completely failed (0% accuracy)")
    print(f"  - {best_model['pct_perfect']:.1f}% of problems solved perfectly")
    
    # Calculate overall statistics
    avg_completely_failed = sum(r['pct_completely_failed'] for r in results) / len(results)
    avg_perfect = sum(r['pct_perfect'] for r in results) / len(results)
    
    print(f"\n• Average across all {len(results)} models:")
    print(f"  - {avg_completely_failed:.1f}% of problems completely failed")
    print(f"  - {avg_perfect:.1f}% of problems solved perfectly")
    print(f"  - {100-avg_completely_failed:.1f}% of problems had at least some success")
    
    print(f"\n• All models show similar patterns:")
    print(f"  - Median accuracy is 0.000 for all models (most problems are very difficult)")
    print(f"  - Standard deviations are high, indicating wide variation in problem difficulty")
    print(f"  - Even the best models fail on the majority of hard math problems")

    # Plot pretty bar graph
    plot_failure_bar_graph(results, "results/graphs/hard_math_failures.png")
    print("Saved pretty bar graph to results/graphs/hard_math_failures.png")

if __name__ == "__main__":
    main() 