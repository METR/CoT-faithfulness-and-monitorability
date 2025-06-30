import argparse
import json
from pathlib import Path
from typing import Any, List, Tuple

from graph_utils import (
    GraphMetadata,
    generate_boxplot,
    generate_propensity_graph,
    generate_taking_hints_graph,
    generate_taking_hints_v_difficulty_graph,
    generate_violin_plot,
)

SHOW_LABELS = False
dataset_name = "metr/hard-math"
BOXPLOT_LOWER_THRESHOLD = 0.2
BOXPLOT_UPPER_THRESHOLD = 0.8


def filter_lists_by_threshold(
    filter_list: List[float], *other_lists: List[Any], threshold: float = 0.1
) -> Tuple[Any, ...]:
    """
    Filter multiple lists based on a threshold applied to one list.

    Args:
        filter_list: The list to apply the threshold condition to
        *other_lists: Variable number of other lists to filter correspondingly
        threshold: Values below this in filter_list will be removed (default 0.1)

    Returns:
        Tuple of filtered lists (filter_list, *other_lists)
    """
    # Create mask for values >= threshold
    filtered_data = [
        (filter_val, *other_vals)
        for filter_val, *other_vals in zip(filter_list, *other_lists)
        if filter_val >= threshold
    ]

    # Unpack back into separate lists
    if filtered_data:
        return tuple(list(items) for items in zip(*filtered_data))
    else:
        # Handle empty result case
        return tuple([] for _ in range(len(other_lists) + 1))


def filter_data_by_hint_taking_threshold(
    data: dict,
    threshold: float = 0.1,
) -> dict:
    """
    Filter the data by the threshold.
    """
    filtered_data = {}
    filtered_data["metadata"] = data["metadata"]
    (
        filtered_take_hints_scores,
        filtered_labels,
        filtered_reasoning_accuracies,
        filtered_non_reasoning_accuracies,
        filtered_difficulty_scores,
        filtered_difficulty_stderrs,
        filtered_faithfulness_scores,
        filtered_faithfulness_stderrs,
        filtered_samples,
    ) = filter_lists_by_threshold(
        data["take_hints_scores"],
        data["labels"],
        data["reasoning_accuracies"],
        data["non_reasoning_accuracies"],
        data["difficulty_scores"],
        data["difficulty_stderrs"],
        data["faithfulness_scores"],
        data["faithfulness_stderrs"],
        data["samples"],
        threshold=threshold,
    )
    filtered_data["take_hints_scores"] = filtered_take_hints_scores
    filtered_data["labels"] = filtered_labels
    filtered_data["reasoning_accuracies"] = filtered_reasoning_accuracies
    filtered_data["non_reasoning_accuracies"] = filtered_non_reasoning_accuracies
    filtered_data["difficulty_scores"] = filtered_difficulty_scores
    filtered_data["difficulty_stderrs"] = filtered_difficulty_stderrs
    filtered_data["faithfulness_scores"] = filtered_faithfulness_scores
    filtered_data["faithfulness_stderrs"] = filtered_faithfulness_stderrs
    filtered_data["samples"] = filtered_samples
    return filtered_data


def find_json_files(base_directory: str) -> List[Path]:
    """
    Find all JSON files in the given directory, excluding those in 'subset' folders.

    Args:
        base_directory: The base directory to search in

    Returns:
        List of Path objects for JSON files
    """
    json_files: List[Path] = []
    base_path = Path(base_directory)

    for json_file in base_path.rglob("*.json"):
        # Skip files in subset directories
        if "subset" in json_file.parts:
            continue
        json_files.append(json_file)

    return json_files


def create_output_directory(
    json_file_path: Path, base_input_dir: Path, base_output_dir: Path, file_stem: str
) -> Path:
    """
    Create the output directory structure that mirrors the input structure.

    Args:
        json_file_path: Path to the JSON file
        base_input_dir: Base input directory (e.g., 'src/results/faithfulness')
        base_output_dir: Base output directory (e.g., 'src/results/graphs')

    Returns:
        Path object for the output directory
    """
    # Get the relative path from the base input directory
    relative_path = json_file_path.relative_to(base_input_dir)

    # Create the output path - preserve the entire directory structure
    # including the input directory name (faithfulness/monitorability)
    input_dir_name = base_input_dir.name
    output_dir = base_output_dir / input_dir_name / relative_path.parent / file_stem
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def validate_data(data: dict) -> None:
    """
    Validate the data from the JSON file.
    """
    assert "metadata" in data, f"No metadata found in {data}"
    for key in [
        "labels",
        "reasoning_accuracies",
        "non_reasoning_accuracies",
        "difficulty_scores",
        "difficulty_stderrs",
        "faithfulness_scores",
        "faithfulness_stderrs",
        "take_hints_scores",
        "samples",
    ]:
        assert key in data, f"No {key} found in {data}"


def plot_json_file(
    data: dict,
    filtered_data: dict,
    output_dir: Path,
    hint_taking_threshold: float = 0.1,
    show_color: bool = False,
) -> None:
    """
    Process a single JSON file and generate all graphs.

    Args:
        data: Data from the JSON file to process
        filtered_data: Filtered data from the JSON file to process based on the hint taking threshold
        output_dir: Directory to save the graphs in
        hint_taking_threshold: Threshold for hint taking (default 0.1)
    """
    model = data["metadata"]["model"]
    metadata = GraphMetadata(
        threshold=hint_taking_threshold,
        faithfulness=data["metadata"]["score_faithfulness"],
        question_prompt=data["metadata"]["question_prompt"],
        judge_prompt=data["metadata"]["judge_prompt"],
    )

    # Generate taking hints graph
    generate_taking_hints_graph(
        data["take_hints_scores"],
        metadata,
        labels=data["labels"],
        model=model,
        dataset=dataset_name,
        path=str(output_dir / "taking_hints.png"),
    )

    # Generate taking hints vs difficulty graph
    generate_taking_hints_v_difficulty_graph(
        data["take_hints_scores"],
        data["difficulty_scores"],
        metadata,
        labels=data["labels"],
        model=model,
        dataset=dataset_name,
        show_labels=SHOW_LABELS,
        path=str(output_dir / "taking_hints_v_difficulty.png"),
    )

    # Check if we have enough data after filtering
    if len(filtered_data.keys()) == 0:
        raise Exception(f"No data remaining after filtering for {json_file_path}")

    # Generate propensity graph
    generate_propensity_graph(
        filtered_data["faithfulness_scores"],
        filtered_data["faithfulness_stderrs"],
        filtered_data["difficulty_scores"],
        filtered_data["difficulty_stderrs"],
        metadata,
        labels=filtered_data["labels"],
        take_hints_scores=filtered_data["take_hints_scores"],
        samples=filtered_data["samples"],
        model=model,
        dataset=dataset_name,
        show_labels=SHOW_LABELS,
        show_color=show_color,
        show_shape=False,
        path=str(output_dir / f"propensity_thresh{hint_taking_threshold}.png"),
        show_dot_size=False,
    )

    # Generate boxplot
    generate_boxplot(
        filtered_data["faithfulness_scores"],
        filtered_data["difficulty_scores"],
        metadata,
        BOXPLOT_LOWER_THRESHOLD,
        BOXPLOT_UPPER_THRESHOLD,
        model,
        dataset_name,
        path=str(output_dir / f"boxplot_thresh{hint_taking_threshold}.png"),
    )

    # Generate violin plot
    generate_violin_plot(
        filtered_data["faithfulness_scores"],
        filtered_data["difficulty_scores"],
        BOXPLOT_LOWER_THRESHOLD,
        BOXPLOT_UPPER_THRESHOLD,
        metadata,
        model,
        dataset_name,
        path=str(output_dir / f"violin_plot_thresh{hint_taking_threshold}.png"),
    )

    print(f"Graphs are saved in {output_dir}")


def process_single_file(
    json_file_path: Path,
    hint_taking_threshold: float = 0.1,
    base_results_dir: Path = None,
    output_base_dir: Path = None,
    show_color: bool = False,
):
    """
    Process a single JSON file and generate all graphs.
    """
    print(f"Processing single file: {json_file_path}")
    # Load data from JSON file
    try:
        with open(json_file_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        raise Exception(f"Error loading {json_file_path}: {e}")

    # Determine which base directory this file belongs to
    if data["metadata"]["score_faithfulness"]:
        base_input_dir = base_results_dir / "faithfulness"
    else:
        base_input_dir = base_results_dir / "monitorability"

    # Create mirrored output directory structure
    filename_base = json_file_path.stem
    if not json_file_path.is_absolute():
        json_file_path = Path(__file__).parent.resolve() / json_file_path
    output_dir = create_output_directory(
        json_file_path, base_input_dir, output_base_dir, filename_base
    )
    filtered_data = filter_data_by_hint_taking_threshold(data, hint_taking_threshold)
    assert len(filtered_data["faithfulness_scores"]) <= len(
        data["faithfulness_scores"]
    ), (
        f"filtered data faithfulness scores should be less than or equal to data faithfulness scores, {len(filtered_data['faithfulness_scores'])} is not <= {len(data['faithfulness_scores'])}"
    )
    plot_json_file(data, filtered_data, output_dir, hint_taking_threshold, show_color)
    print(f"\nCompleted! Processed 1 file.")


def process_all_files(
    base_results_dir: Path,
    output_base_dir: Path,
    hint_taking_threshold: float = 0.1,
    show_color: bool = False,
):
    """
    Process all JSON files in the faithfulness and monitorability directories.
    """
    total_files = 0
    for input_dir_name in ["faithfulness", "monitorability"]:
        input_dir_path = base_results_dir / input_dir_name

        print(f"\nProcessing directory: {input_dir_name}")

        # Find all JSON files in this directory
        json_files = find_json_files(str(input_dir_path))
        print(f"Found {len(json_files)} JSON files in {input_dir_name}")

        for json_file in json_files:
            # Create mirrored output directory structure
            process_single_file(
                json_file,
                hint_taking_threshold,
                base_results_dir,
                output_base_dir,
                show_color,
            )
            total_files += 1
    print(f"\nCompleted! Processed {total_files} JSON files total.")


def main():
    """
    Main function to process all JSON files in faithfulness and monitorability directories.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate graphs from JSON data files")
    parser.add_argument(
        "--hint_taking_threshold",
        type=float,
        default=0.95,
        help="Threshold for hint taking (default: 0.1)",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to a specific JSON file to process (instead of processing all files)",
    )
    parser.add_argument(
        "--show_color",
        type=bool,
        default=False,
        help="Show color in the graphs (default: False)",
    )
    args = parser.parse_args()

    print(
        f"Starting graph generation with hint taking threshold: {args.hint_taking_threshold}, show color: {args.show_color}"
    )

    # Base directories - use current file's directory as anchor
    script_dir = Path(__file__).parent
    base_results_dir = script_dir / "results"
    output_base_dir = script_dir / "results" / "graphs"

    # If a specific file is provided, process only that file
    if args.file:
        process_single_file(
            Path(args.file),
            args.hint_taking_threshold,
            base_results_dir,
            output_base_dir,
            args.show_color,
        )
    else:
        process_all_files(
            base_results_dir,
            output_base_dir,
            args.hint_taking_threshold,
            args.show_color,
        )


if __name__ == "__main__":
    main()
