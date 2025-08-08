import io
import math
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image


def _add_metr_watermark(fig: plt.Figure) -> None:
    """Add METR logo and text watermark to the top right of the figure."""
    logo_path = Path("assets/METR_logo_colors_high_res.png")
    logo = Image.open(logo_path).convert("RGBA")
    logo_array = np.array(logo)
    # Move logo further to the upper right
    imagebox = OffsetImage(logo_array, zoom=0.047, alpha=0.6)
    ab = AnnotationBbox(
        imagebox,
        (1.00, 1.05),  # moved a bit to the left
        xycoords="figure fraction",
        frameon=False,
        box_alignment=(1, 1),
    )
    fig.add_artist(ab)
    # fig.text(
    #     0.995,  # further upper right
    #     0.995,
    #     "METR",
    #     fontsize=15,
    #     fontweight="normal",
    #     ha="right",
    #     va="top",
    #     alpha=0.6,
    #     color="black",
    # )
    # Add "metr.org" text to the bottom left
    fig.text(
        0.115,
        0.12,
        "metr.org  |  CC-BY",
        fontsize=8,
        fontweight="normal",
        ha="right",
        va="top",
        alpha=0.6,
        color="black",
    )

    # Add footnote text to the bottom right
    fig.text(
        0.99,
        0.12,
        "The behavior we studied was whether models use a clue to solve a hard question, since this is the setting other\nresearchers have used to demonstrate unfaithful reasoning. It's not clear how well this generalizes to other settings.",
        fontsize=10,
        fontweight="normal",
        ha="right",
        va="top",
        alpha=0.8,
        color="black",
    )
    fig.text(
        0.99,
        0.055,
        "¹ For a specific definition of faithfulness defined in our writeup.",
        fontsize=8,
        fontweight="normal",
        ha="right",
        va="top",
        alpha=0.6,
        color="black",
    )


def create_bar_chart(
    use_min_values: bool,
    use_difficulty_as_subplots: bool,
    invert_values: bool,
) -> None:
    """Create a bar chart with four separate bars and a dashed vertical separator, using the same data as bar_chart.py."""

    # Set up the figure with two subplots sharing y-axis (16:9 aspect ratio)
    plt.style.use("default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.67, 6), sharey=True)
    # Load data from CSV
    data_path = Path("twitter_images/twitter_data.csv")
    df = pd.read_csv(data_path)

    # Map model names to display names
    model_mapping = {
        "c3.7s": "Claude 3.7 Sonnet",
        "c4o": "Claude Opus 4",
        "qwen": "Qwen 3-235B",
    }

    # Get unique models and their order
    models = [model_mapping[model] for model in df["model"].unique()]

    # Separate data by difficulty
    trivial_data = df[df["difficulty"] == "trivial"]
    complex_data = df[df["difficulty"] == "complex"]

    # Choose metric based on toggle
    faithfulness_metric = "min_faithfulness" if use_min_values else "avg_faithfulness"
    monitorability_metric = (
        "min_monitorability" if use_min_values else "avg_monitorability"
    )

    # Heights for each model in each category using actual data
    bar_heights = [
        [
            trivial_data[trivial_data["model"] == "c3.7s"][faithfulness_metric].iloc[0],
            trivial_data[trivial_data["model"] == "c4o"][faithfulness_metric].iloc[0],
            trivial_data[trivial_data["model"] == "qwen"][faithfulness_metric].iloc[0],
        ],  # Trivial faithfulness
        [
            complex_data[complex_data["model"] == "c3.7s"][faithfulness_metric].iloc[0],
            complex_data[complex_data["model"] == "c4o"][faithfulness_metric].iloc[0],
            complex_data[complex_data["model"] == "qwen"][faithfulness_metric].iloc[0],
        ],  # Complex faithfulness
        [
            trivial_data[trivial_data["model"] == "c3.7s"][monitorability_metric].iloc[
                0
            ],
            trivial_data[trivial_data["model"] == "c4o"][monitorability_metric].iloc[0],
            trivial_data[trivial_data["model"] == "qwen"][monitorability_metric].iloc[
                0
            ],
        ],  # Trivial detection
        [
            complex_data[complex_data["model"] == "c3.7s"][monitorability_metric].iloc[
                0
            ],
            complex_data[complex_data["model"] == "c4o"][monitorability_metric].iloc[0],
            complex_data[complex_data["model"] == "qwen"][monitorability_metric].iloc[
                0
            ],
        ],  # Complex detection
    ]

    if invert_values:
        bar_heights = [
            [1 - height for height in bar_height] for bar_height in bar_heights
        ]

    # Colors for each model
    model_colors = ["#A8CDC1", "#5CA68F", "#0C7C59"]  # Red, Teal, Blue

    # Bar positions - 3 bars per category
    category_centers = np.array(
        [0.3, 0.7]
    )  # Two categories per subplot (reduced spacing, moved left)
    bar_width = 0.10  # Width of individual bars (made thinner for 16:9)
    bar_spacing = 0.10  # Space between bars within a category (slight gap)

    # Choose layout based on toggle
    if use_difficulty_as_subplots:
        # Layout: trivial vs complex as separate plots
        left_categories = ["Faithfulness", "Detection"]
        right_categories = ["Faithfulness", "Detection"]
        left_title = "Trivial reasoning"
        right_title = "Complex reasoning"
        left_data_indices = [0, 2]  # Trivial faithfulness, trivial detection
        right_data_indices = [1, 3]  # Complex faithfulness, complex detection
    else:
        # Layout: faithfulness vs detection as separate plots
        left_categories = [
            "Reasoning that can\noccur in a forward pass",
            "Reasoning that\nmust use the CoT",
        ]
        right_categories = left_categories
        left_title = "Faithfulness"
        right_title = "Detection"
        left_data_indices = [0, 1]  # Trivial faithfulness, complex faithfulness
        right_data_indices = [2, 3]  # Trivial detection, complex detection

    # Create bars for left subplot
    left_bars = []
    for cat_idx, category_center in enumerate(category_centers):
        category_bars = []
        for model_idx in range(3):
            # Calculate position for this bar within the category
            bar_x = category_center - bar_spacing + model_idx * bar_spacing
            bar_height = bar_heights[left_data_indices[cat_idx]][model_idx]
            bar_color = model_colors[model_idx]

            # Create the bar
            bar = ax1.bar(
                bar_x,
                bar_height,
                bar_width,
                color=bar_color,
                alpha=1.0,
                label=models[model_idx] if cat_idx == 0 else "",  # Only label once
            )
            category_bars.append(bar[0])

            # Add value label on top of each bar
            ax1.text(
                bar_x,
                bar_height + 0.02 if not invert_values else bar_height + 0.002,
                f"{bar_height * 100:.2f}%",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        left_bars.append(category_bars)

    # Create bars for right subplot
    right_bars = []
    for cat_idx, category_center in enumerate(category_centers):
        category_bars = []
        for model_idx in range(3):
            # Calculate position for this bar within the category
            bar_x = category_center - bar_spacing + model_idx * bar_spacing
            bar_height = bar_heights[right_data_indices[cat_idx]][model_idx]
            bar_color = model_colors[model_idx]

            # Create the bar
            bar = ax2.bar(
                bar_x,
                bar_height,
                bar_width,
                color=bar_color,
                alpha=1.0,
                label=models[model_idx] if cat_idx == 0 else "",  # Only label once
            )
            category_bars.append(bar[0])

            # Add value label on top of each bar
            ax2.text(
                bar_x,
                bar_height + 0.02 if not invert_values else bar_height + 0.002,
                f"{bar_height * 100:.2f}%",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        right_bars.append(category_bars)
    # Customize both subplots
    for ax in [ax1, ax2]:
        # Set y-axis limits based on invert_values toggle
        if invert_values:
            ax.set_ylim(0, 0.14)  # 0-14% when values are inverted
        else:
            ax.set_ylim(0, 1.0)  # 0-100% for normal values
        ax.set_xlim(0.08, category_centers[-1] + 0.22)
        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y * 100:.0f}%"))
        # Add dashed grid for better readability
        ax.grid(True, alpha=0.3, axis="y", linestyle="--")
        ax.set_axisbelow(True)
        # Remove top and right spines for cleaner look
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#333333")
        ax.spines["bottom"].set_color("#333333")
        ax.tick_params(colors="#333333")

    # Show left spine (y-axis line) on right subplot but keep ticks hidden
    ax2.spines["left"].set_visible(True)
    ax2.spines["left"].set_color("#333333")
    ax2.tick_params(
        left=False, labelleft=False
    )  # Remove y-axis ticks and labels from right subplot

    # Set x-axis labels for each subplot
    ax1.set_xticks(category_centers)
    ax1.set_xticklabels(
        left_categories,
        fontsize=10,
        linespacing=1.2,  # fontweight=500
        color="black",
    )

    ax2.set_xticks(category_centers)
    ax2.set_xticklabels(
        right_categories,
        fontsize=10,
        linespacing=1.2,  # fontweight=500
        color="black",
    )

    # Add y-axis label to the left subplot
    # ax1.set_ylabel("Percentage detected or faithful", fontsize=12)

    # Add group labels above the subplots
    if use_difficulty_as_subplots:
        ax1.text(
            -0.1,
            1.08,
            f"{left_title}\n(Worst-case over all settings)¹",
            fontsize=13,
            ha="left",
            va="bottom",
            transform=ax1.get_xaxis_transform(),
            color="#666666",
        )
        ax2.text(
            -0.1,
            1.08,
            f"{right_title}\n(Worst-case over all settings)²",
            fontsize=13,
            ha="left",
            va="bottom",
            transform=ax2.get_xaxis_transform(),
            color="#666666",
        )
        ax2.text(
            -0.1,
            1.02,
            "At specificity TODO%",
            fontsize=9,
            ha="left",
            va="bottom",
            transform=ax2.get_xaxis_transform(),
            alpha=0.7,
        )
    else:
        ax1.text(
            0.08,
            1.12,
            "How often was the reasoning of interest $\mathit{not}$\n$\mathit{faithfully¹}$ $\mathit{represented}$ in the CoT?",
            fontsize=14,
            ha="left",
            va="bottom",
            transform=ax1.get_xaxis_transform(),
            color="#666666",
        )
        ax2.text(
            0.08,
            1.12,
            "How often did we $\mathit{fail}$ $\mathit{to}$ $\mathit{detect}$ reasoning of\ninterest in the CoT?",
            fontsize=14,
            ha="left",
            va="bottom",
            transform=ax2.get_xaxis_transform(),
            color="#666666",
        )
        ax2.text(
            0.08,
            1.06,
            "At 96.2% specificity",
            fontsize=8,
            ha="left",
            va="bottom",
            transform=ax2.get_xaxis_transform(),
            alpha=0.7,
        )
    # Add legend to the right subplot
    ax2.legend(loc="upper right", fontsize=10)
    # Add title with extra space above
    fig.suptitle(
        "Complex reasoning was easier to detect in CoT",
        fontsize=19,
        fontweight="bold",
        y=1.03,  # Move further up from subtitles
        ha="left",  # Left align title
        x=0.05,  # Align with left subplot title
    )
    # Add the METR watermark
    _add_metr_watermark(fig)
    # Adjust layout with extra space below x tick labels and reduced subplot spacing
    plt.tight_layout(rect=[0, 0.08, 1, 0.92])
    plt.subplots_adjust(top=0.82, bottom=0.22, wspace=0.05)
    # Save the plot
    output_path = Path(
        f"twitter_images/bar_chart_invert_{invert_values}_use_min_{use_min_values}.png"
    )
    plt.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.2)
    print(f"Bar chart saved to {output_path}")
    # plt.show()


if __name__ == "__main__":
    # Toggle between 'min' and 'avg' values
    use_min_values = False  # Set to True for min values, False for average values

    # Toggle between layout modes:
    # False: faithfulness vs detection as separate plots (trivial/complex side by side)
    # True: trivial vs complex as separate plots (faithfulness/detection side by side)
    use_difficulty_as_subplots = False

    # Set to True if we want to invert 99% to 1%
    invert_values = True
    create_bar_chart(use_min_values, use_difficulty_as_subplots, invert_values)
