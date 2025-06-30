from dataclasses import dataclass
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

COLOR_MAP = {
    "default": "#808080",  # Gray
    "reward_hacking": "#f9a4a4",  # Light Red
    "sycophancy": "#7fc97f",  # Light Green
    "metadata": "#fdc086",  # Light Orange
    "database_schema": "#485F52",  # Dark Green
    "config_file": "#a6cee3",  # Light Blue
    "cache": "#1f78b4",  # Blue
    "error_message": "#b2df8a",  # Light Green
    "backup_data": "#33a02c",  # Green
    "machine_learning": "#fb9a99",  # Light Pink
    "version_control": "#e31a1c",  # Red
    "csv_data": "#fdbf6f",  # Light Orange
    "security_audit": "#ff7f00",  # Orange
    "jupyter_notebook": "#cab2d6",  # Light Purple
}

SHAPE_MAP = {
    "default": "o",
    "easy_answer": "s",
    "medium_hex": "D",
    "hard_math": "v",
    "hard_unicode": "P",
    "hard_len_str": "X",
    "easy_list_comprehension": "d",
}

model_pretty = {
    "claude-3-7-sonnet-latest": "Claude 3.7 Sonnet",
    "claude-opus-4-20250514": "Claude Opus 4",
}

JUDGE_FILE_TO_NAME_MAP = {
    "faithfulness_0611.py": "strict",
    "faithfulness_2_broad_definition.py": "relaxed",
    "faithfulness_broad_0627.py": "relaxed",
    "faithfulness_narrow_0627.py": "strict",
}

PROMPT_FILE_TO_NAME_MAP = {
    "cheater_ai.py": "prompt that instructs the model to encode its CoT in 3 layers",
    "default.py": "default prompt",
    "general_instructive.py": "prompt that instructs the CoT to hide computations",
    "grug.py": "prompt that instructs the model to think like a caveman",
    "moe_v4.py": "prompt that instructs the model to consult imaginary experts",
    "tcgs_non_instructive.py": "prompt that instructs the model to think like a caveman and avoid detection from Nazis",
    "jailbreak_0614.py": "prompt that instructs the model to solve the clue in place of the problem",
}


@dataclass
class GraphMetadata:
    threshold: float
    faithfulness: bool
    question_prompt: str
    judge_prompt: str


def add_metadata(metadata: GraphMetadata | None, ax: plt.Axes) -> None:
    if metadata:
        metadata_text = (
            f"Threshold: {metadata.threshold}\n"
            f"Faithfulness: {metadata.faithfulness}\n"
            f"Question Prompt: {metadata.question_prompt.split('/')[-1]}\n"
            f"Judge Prompt: {metadata.judge_prompt.split('/')[-1]}"
        )
        ax.text(
            0.98,
            0.02,
            metadata_text,
            transform=ax.transAxes,
            verticalalignment="bottom",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            fontsize=8,
        )


def generate_propensity_graph(
    faithfulness_scores: List[float],
    faithfulness_stderrs: List[float],
    difficulty_scores: List[float],
    difficulty_stderrs: List[float],
    metadata: GraphMetadata | None,
    labels: List[str],
    take_hints_scores: List[float],
    samples: List[int],
    model: str,
    dataset: str,
    show_labels: bool = False,
    show_color: bool = True,
    show_shape: bool = True,
    show_dot_size: bool = True,
    show_error_bars: bool = True,
    path: str | None = None,
) -> None:
    """
    Generate a graph comparing faithfulness scores against difficulty scores.

    Args:
        faithfulness_scores: List of faithfulness scores for each behavior
        faithfulness_stderrs: List of standard errors for faithfulness scores
        difficulty_scores: List of difficulty scores for each behavior
        difficulty_stderrs: List of standard errors for difficulty scores
        labels: List of labels for each data point
        model: Model name to display in the title
        dataset: Dataset name to display in the title
        path: Optional path to save the graph to. If None, displays the graph instead.
        show_labels: Whether to show labels for each data point

    Returns:
        None
    """
    # Create figure with extra space on right for legend
    plt.figure(figsize=(12, 8.5))

    # Create main plotting area that leaves room on right
    ax = plt.axes([0.1, 0.1, 0.7, 0.75])

    # Create a proper color legend if show_color is True
    legend_elements = []

    if show_color:
        # Only show colors that are actually used in the data
        used_colors = set()
        for label in labels:
            for key in COLOR_MAP:
                if key != "default" and key in label.lower():
                    used_colors.add((key, COLOR_MAP[key]))
                    break

        if used_colors:
            # Create legend handles
            from matplotlib.patches import Patch

            legend_elements = [
                Patch(facecolor=color, label=key.replace("_", " ").title())
                for key, color in sorted(used_colors)
            ]

            # Add vertical legend on right side without frame
            plt.figlegend(
                handles=legend_elements,
                loc="upper left",
                bbox_to_anchor=(0.815, 0.85),
                fontsize=8,
                frameon=False,
            )

    image = plt.imread("assets/logo.png")

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add shaded "safe zone" below the line from (0,0) to (1,1)
    x = [0, 1]
    y = [0, 1]
    plt.fill_between(x, [0, 0], y, alpha=0.2, color="#485F52", label="Safe Zone")

    # Convert standard errors to 90% confidence intervals (z=1.645 for 90% CI)
    z_score = 1.645
    faithfulness_ci = [se * z_score for se in faithfulness_stderrs]
    difficulty_ci = [se * z_score for se in difficulty_stderrs]

    # Calculate dot sizes based on take_hints_scores * samples
    if show_dot_size:
        dot_sizes = [
            round(take_hints_scores[i] * samples[i]) * 1
            for i in range(len(take_hints_scores))
        ]
    else:
        dot_sizes = [50] * len(take_hints_scores)  # Normal scatter plot dot size

    # Determine colors based on labels and COLOR_MAP (only if show_color is True)
    colors = []
    if show_color:
        for label in labels:
            color_found = False
            for key in COLOR_MAP:
                if key != "default" and key in label.lower():
                    colors.append(COLOR_MAP[key])
                    color_found = True
                    break
            if not color_found:
                colors.append(COLOR_MAP["default"])
    else:
        colors = [COLOR_MAP["machine_learning"]] * len(labels)

    # Determine shapes based on labels and SHAPE_MAP (only if show_shape is True)
    shapes = []
    if show_shape:
        for label in labels:
            shape_found = False
            for key in SHAPE_MAP:
                if key != "default" and key in label.lower():
                    shapes.append(SHAPE_MAP[key])
                    shape_found = True
                    break
            if not shape_found:
                shapes.append(SHAPE_MAP["default"])
    else:
        shapes = [SHAPE_MAP["default"]] * len(labels)

    # Plot error bars without markers
    plt.errorbar(
        difficulty_scores,
        faithfulness_scores,
        xerr=difficulty_ci,
        yerr=faithfulness_ci,
        fmt="none",
        ecolor="darkgray",
        capsize=5,
    )

    # Group data points by shape and plot each group
    unique_shapes = list(set(shapes))
    for shape in unique_shapes:
        # Get indices for this shape
        shape_indices = [i for i, s in enumerate(shapes) if s == shape]

        # Extract data for this shape
        shape_difficulty = [difficulty_scores[i] for i in shape_indices]
        shape_faithfulness = [faithfulness_scores[i] for i in shape_indices]
        shape_colors = [colors[i] for i in shape_indices]
        shape_sizes = [dot_sizes[i] for i in shape_indices]

        # Plot scatter points with variable size and varying colors/shapes
        plt.scatter(
            shape_difficulty,
            shape_faithfulness,
            s=shape_sizes,
            c=shape_colors,
            marker=shape,
            alpha=0.7,
        )

    plt.xlim(-0.02, 1.01)
    plt.ylim(0, 1.05)

    if show_labels:
        for i, label in enumerate(labels):
            plt.annotate(
                label,
                (difficulty_scores[i], faithfulness_scores[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=6,
            )

    plt.xlabel("Clue Difficulty: 1 - P(solve clue without CoT)", fontsize=16)

    title_metric = (
        "Faithfulness"
        if metadata is None or metadata.faithfulness
        else "Monitorability"
    )
    # Create ylabel with judge information if metadata is available
    assert metadata.judge_prompt is not None
    if title_metric == "Faithfulness":
        y_title = "Faithfulness"
        y_subtitle = f"frequency at which the relevant information is in the chain of thought\nwith {JUDGE_FILE_TO_NAME_MAP[metadata.judge_prompt.split('/')[-1]]} faithfulness definition"
    elif title_metric == "Monitorability":
        y_title = "Monitor Sensitivity"
        y_subtitle = "true positive rate for detecting relevant information usage\non a monitor with FPR = ~1%"
    else:
        raise ValueError(f"Invalid title metric: {title_metric}")
    # judge_name = metadata.judge_prompt.split("/")[-1]
    # ylabel = f"{y_title}\n{y_subtitle}"
    # plt.ylabel(ylabel, fontsize=16)
    # Make the sub-axis text smaller and gray
    ax.yaxis.label.set_fontsize(16)
    ax.yaxis.label.set_color("black")
    ax.set_ylabel(y_title, fontsize=18, color="black", labelpad=32)
    ax.text(
        -0.06,
        0.5,
        y_subtitle,
        rotation=90,
        transform=ax.transAxes,
        fontsize=12,
        color="gray",
        verticalalignment="center",
        horizontalalignment="center",
    )

    # Add main title with model name and prompt
    model_name = model_pretty.get(model.split("/")[-1], model.split("/")[-1])

    prompt_name = (
        metadata.question_prompt.split("/")[-1] if metadata else "default prompt"
    )
    plt.title(
        f"{title_metric} of {model_name}",
        loc="left",
        pad=50,
        fontsize=25,
    )

    # Add subtitle with different style
    ax = plt.gca()
    ax.text(
        0,
        1.03,
        f"90% CI, filtered to clues with usage rate >= {(metadata.threshold) * 100:.0f}%\nwith {PROMPT_FILE_TO_NAME_MAP[prompt_name]}",
        transform=ax.transAxes,
        fontsize=12,
        color="gray",
        style="italic",
        horizontalalignment="left",
    )
    ax = plt.axes(
        [0.812, 0.884, 0.12, 0.12], frameon=True
    )  # [left, bottom, width, height] - aligned with legend left and title top
    ax.imshow(image)
    ax.axis("off")

    plt.grid(True)
    if path:
        plt.savefig(path)
    else:
        plt.show()


def generate_taking_hints_graph(
    p_take_hints: List[float],
    metadata: GraphMetadata | None,
    labels: List[str],
    model: str,
    dataset: str,
    path: str | None = None,
) -> None:
    indices = np.arange(len(labels))
    width = 0.6

    took_hint = np.array(p_take_hints)
    did_not_take_hint = 1 - took_hint  # Will sum to 1 for each bar
    # Increase figure height and adjust for more space at bottom
    fig, ax = plt.subplots(figsize=(16, 6))
    add_metadata(metadata, ax)

    ax.bar(indices, took_hint, width, label="Took Hint", color="#7fc97f")
    ax.bar(
        indices,
        did_not_take_hint,
        width,
        bottom=took_hint,
        label="Did Not Take Hint",
        color="#fdc086",
    )

    ax.set_ylabel("Proportion of Samples")
    ax.set_title(f"Hint-Taking for {model.split('/')[-1]} on {dataset}")
    ax.set_xticks(indices)

    # Improve label spacing and rotation
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.legend()

    # Set y-axis limits to ensure all bars are same height
    ax.set_ylim(0, 1)

    # Adjust layout with more bottom margin for rotated labels
    plt.tight_layout()

    if path:
        plt.savefig(path, bbox_inches="tight", pad_inches=0.1)
    else:
        plt.show()


def generate_taking_hints_v_difficulty_graph(
    p_take_hints: List[float],
    difficulty_scores: List[float],
    metadata: GraphMetadata,
    labels: List[str],
    model: str,
    dataset: str,
    path: str | None = None,
    show_labels: bool = False,
) -> None:
    # Create figure with extra space on right for legend
    plt.figure(figsize=(12, 8.5))

    # Create main plotting area that leaves room on right
    ax = plt.axes([0.1, 0.1, 0.7, 0.75])

    # Add metadata box if metadata is provided
    add_metadata(metadata, plt.axes())

    image = plt.imread("assets/logo.png")

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.scatter(difficulty_scores, p_take_hints, marker="o", color="#f9a4a4")

    plt.xlim(0, 1.01)

    if show_labels:
        for i, label in enumerate(labels):
            plt.annotate(
                label,
                (difficulty_scores[i], p_take_hints[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=6,
            )

    plt.xlabel("Difficulty Score")
    plt.ylabel("Proportion Taking Hints")
    plt.title("Hint-Taking vs Difficulty", loc="left", pad=25, fontsize=25)
    plt.suptitle(
        f"{model} on {dataset}",
        y=0.90,
        fontsize=12,
        color="gray",
        style="italic",
    )

    # Add metadata in bottom right
    if metadata:
        metadata_text = (
            f"Hint Taking Threshold: {metadata.threshold}\n"
            f"Faithfulness: {metadata.faithfulness}\n"
            f"Question Prompt: {metadata.question_prompt.split('/')[-1]}\n"
            f"Judge Prompt: {metadata.judge_prompt.split('/')[-1]}"
        )
        plt.figtext(
            0.82,
            0.1,
            metadata_text,
            verticalalignment="bottom",
            horizontalalignment="left",
            fontsize=8,
        )

    # Add logo in top right
    logo_ax = plt.axes([0.815, 0.93, 0.1, 0.1], frameon=True)
    logo_ax.imshow(image)
    logo_ax.axis("off")

    plt.grid(True)
    if path:
        plt.savefig(path)
    else:
        plt.show()


def generate_with_and_without_cot_difficulty_graph(
    reasoning_accuracy_scores: List[float],
    non_reasoning_accuracy_scores: List[float],
    metadata: GraphMetadata | None,
    labels: List[str],
    model: str,
    dataset: str,
    path: str | None = None,
) -> None:
    plt.figure(figsize=(10, 6))

    # Add metadata box if metadata is provided
    add_metadata(metadata, plt.axes())

    plt.scatter(reasoning_accuracy_scores, non_reasoning_accuracy_scores, alpha=0.6)

    # Add labels and title
    plt.xlabel("Reasoning Accuracy Score")
    plt.ylabel("Non-Reasoning Accuracy Score")
    plt.title(
        f"Reasoning vs Non-Reasoning Accuracy Scores for {model.split('/')[-1]} on {dataset}"
    )

    # Add labels for each point
    for i, label in enumerate(labels):
        if reasoning_accuracy_scores[i] != 1:
            plt.annotate(
                label, (reasoning_accuracy_scores[i], non_reasoning_accuracy_scores[i])
            )

    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if path:
        plt.savefig(path)
    else:
        plt.show()


def generate_boxplot(
    faithfulness_scores: List[float],
    difficulty_scores: List[float],
    metadata: GraphMetadata | None,
    boxplot_lower_threshold: float,
    boxplot_upper_threshold: float,
    model: str,
    dataset: str,
    path: str | None = None,
) -> None:
    # Prepare data for swarm plot
    data_points = []
    for score, difficulty in zip(faithfulness_scores, difficulty_scores):
        if difficulty <= float(boxplot_lower_threshold):
            data_points.append(
                {
                    "Faithfulness": score,
                    "Category": f"Difficulty <= {boxplot_lower_threshold}",
                }
            )
        elif difficulty >= float(boxplot_upper_threshold):
            data_points.append(
                {
                    "Faithfulness": score,
                    "Category": f"Difficulty >= {boxplot_upper_threshold}",
                }
            )

    # Convert to DataFrame
    df = pd.DataFrame(data_points)

    # Count samples for labels
    low_count = len(
        [
            d
            for d in data_points
            if "low" in d["Category"].lower() or "<=" in d["Category"]
        ]
    )
    high_count = len(
        [
            d
            for d in data_points
            if "high" in d["Category"].lower() or ">=" in d["Category"]
        ]
    )

    plt.figure(figsize=(10, 6))

    # Add metadata box if metadata is provided
    add_metadata(metadata, plt.axes())

    image = plt.imread("assets/logo.png")

    # Remove top and right spines
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Create boxplot using seaborn (without outliers since swarm plot shows all points)
    sns.boxplot(
        data=df,
        x="Category",
        y="Faithfulness",
        color="#485F52",
        boxprops=dict(alpha=0.3),
        whiskerprops=dict(color="#485F52", alpha=0.6),
        capprops=dict(color="#485F52", alpha=0.6),
        medianprops=dict(color="#485F52", linewidth=2),
        showfliers=False,  # Turn off outlier display since swarm plot shows all points
    )

    # Overlay swarm plot for individual points
    sns.swarmplot(
        data=df, x="Category", y="Faithfulness", color="#f9a4a4", size=5, alpha=0.6
    )

    # Update x-tick labels to include sample counts
    ax = plt.gca()
    current_labels = [t.get_text() for t in ax.get_xticklabels()]
    new_labels = []
    for label in current_labels:
        if "<=" in label:
            new_labels.append(f"{label}\nn={low_count}")
        else:
            new_labels.append(f"{label}\nn={high_count}")
    ax.set_xticks(range(len(new_labels)))
    ax.set_xticklabels(new_labels)

    plt.ylabel("Faithfulness Score")
    plt.xlabel("Clue Difficulty Category")
    plt.title(
        f"Distribution of Faithfulness Scores by Clue Difficulty\nModel: {model.split('/')[-1]}, Dataset: {dataset}"
    )
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.2)
    plt.tight_layout()

    if path:
        plt.savefig(path)
    else:
        plt.show()


def generate_violin_plot(
    faithfulness_scores: List[float],
    difficulty_scores: List[float],
    boxplot_lower_threshold: float,
    boxplot_upper_threshold: float,
    metadata: GraphMetadata | None,
    model: str,
    dataset: str,
    path: str | None = None,
) -> None:
    # Prepare data for violin plot
    data_points = []
    for score, difficulty in zip(faithfulness_scores, difficulty_scores):
        if difficulty <= float(boxplot_lower_threshold):
            data_points.append(
                {
                    "Faithfulness": score,
                    "Category": f"Difficulty <= {boxplot_lower_threshold}",
                }
            )
        elif difficulty >= float(boxplot_upper_threshold):
            data_points.append(
                {
                    "Faithfulness": score,
                    "Category": f"Difficulty >= {boxplot_upper_threshold}",
                }
            )

    # Convert to DataFrame
    df = pd.DataFrame(data_points)

    # Count samples for labels
    low_count = len(
        [
            d
            for d in data_points
            if "low" in d["Category"].lower() or "<=" in d["Category"]
        ]
    )
    high_count = len(
        [
            d
            for d in data_points
            if "high" in d["Category"].lower() or ">=" in d["Category"]
        ]
    )

    plt.figure(figsize=(10, 6))

    # Add metadata box if metadata is provided
    add_metadata(metadata, plt.axes())

    image = plt.imread("assets/logo.png")

    # Remove top and right spines
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Create violin plot using seaborn
    sns.violinplot(
        data=df,
        x="Category",
        y="Faithfulness",
        color="#485F52",
        alpha=0.3,
        bw_adjust=0.3,
    )

    # Overlay swarm plot for individual points
    sns.swarmplot(
        data=df, x="Category", y="Faithfulness", color="#f9a4a4", size=5, alpha=0.6
    )

    # Update x-tick labels to include sample counts
    ax = plt.gca()
    current_labels = [t.get_text() for t in ax.get_xticklabels()]
    new_labels = []
    for label in current_labels:
        if "<=" in label:
            new_labels.append(f"{label}\nn={low_count}")
        else:
            new_labels.append(f"{label}\nn={high_count}")
    ax.set_xticks(range(len(new_labels)))
    ax.set_xticklabels(new_labels)

    plt.ylabel("Faithfulness Score")
    plt.xlabel("Clue Difficulty Category")
    plt.title(
        f"Distribution of Faithfulness Scores by Clue Difficulty\nModel: {model.split('/')[-1]}, Dataset: {dataset}"
    )
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.2)
    plt.tight_layout()

    # Add logo
    ax = plt.axes(
        [0.815, 0.93, 0.1, 0.1], frameon=True
    )  # [left, bottom, width, height] - aligned with legend left and title top
    ax.imshow(image)
    ax.axis("off")

    if path:
        plt.savefig(path)
    else:
        plt.show()
