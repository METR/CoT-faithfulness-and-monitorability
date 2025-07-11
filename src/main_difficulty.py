import os
import pathlib
from datetime import datetime
from math import sqrt

from dotenv import load_dotenv
from inspect_ai import eval_set
from inspect_ai.util import DisplayType

from free_response_behaviors import FR_FUNCTION_DICT, FreeResponseBehavior
from free_response_clue_difficulty import (
    TestingScheme,
    free_response_clue_difficulty,
)
from utils.file_utils import save_clue_difficulty_data_to_json
from utils.models import get_model_short_name
from utils.parsing import parse_args

load_dotenv()
project_root = pathlib.Path(__file__).resolve().parent

if __name__ == "__main__":
    config = parse_args()

    model_short_name = get_model_short_name(config.model)
    date_str = datetime.now().strftime("%Y%m%d-%H%M%S")

    TOP_LEVEL_LOG_DIR: str = f"{project_root}/logs/{model_short_name}/clue_difficulty-positive-int/{date_str}/"
    RAW_DATA_DIR = (
        f"{project_root}/results/clue_difficulty-positive-int/{model_short_name}/"
    )
    RAW_DATA_PATH: str = f"{RAW_DATA_DIR}/{date_str}.json"

    cases: list[FreeResponseBehavior] = list(FR_FUNCTION_DICT.keys())

    reasoning_clue_difficulty_tasks = [
        free_response_clue_difficulty(
            config.reasoning_difficulty_model,
            behavior,
            reasoning=True,
            epochs=1,
            testing_scheme=TestingScheme(config.testing_scheme.value),
            temperature=config.temperature,
            batch_size=config.batch_size,
        )
        for behavior in cases
    ]

    non_reasoning_clue_difficulty_tasks = [
        free_response_clue_difficulty(
            config.base_model,
            behavior,
            reasoning=False,
            epochs=1,
            testing_scheme=TestingScheme(config.testing_scheme.value),
            temperature=config.temperature,
            batch_size=config.batch_size,
        )
        for behavior in cases
    ]

    print(
        f"len(reasoning_clue_difficulty_tasks): {len(reasoning_clue_difficulty_tasks)}"
    )
    print(
        f"len(non_reasoning_clue_difficulty_tasks): {len(non_reasoning_clue_difficulty_tasks)}"
    )

    # Convert display string to DisplayType - DisplayType is a string literal type
    display_type: DisplayType = config.display  # type: ignore

    reasoning_completed, reasoning_clue_difficulty_results = eval_set(
        tasks=reasoning_clue_difficulty_tasks,
        max_tasks=config.max_tasks,
        model=config.reasoning_difficulty_model,
        display=display_type,
        max_connections=config.max_connections,
        log_dir=f"{TOP_LEVEL_LOG_DIR}/reasoning",
    )

    non_reasoning_completed, non_reasoning_clue_difficulty_results = eval_set(
        tasks=non_reasoning_clue_difficulty_tasks,
        max_tasks=config.max_tasks,
        model=config.base_model,
        display=display_type,
        max_connections=config.max_connections,
        log_dir=f"{TOP_LEVEL_LOG_DIR}/non_reasoning",
    )

    assert reasoning_completed, "Reasoning eval failed"
    assert non_reasoning_completed, "Non-reasoning eval failed"

    reasoning_accuracies = [
        result.results.scores[0].metrics["accuracy"].value
        for result in reasoning_clue_difficulty_results
        if result.results is not None
    ]
    non_reasoning_accuracies = [
        result.results.scores[0].metrics["accuracy"].value
        for result in non_reasoning_clue_difficulty_results
        if result.results is not None
    ]
    difficulty_scores = [
        1 - non_reasoning_accuracy
        for non_reasoning_accuracy in non_reasoning_accuracies
    ]
    completed_samples = [
        result.results.completed_samples
        for result in reasoning_clue_difficulty_results
        if result.results is not None
    ]

    difficulty_stderrs = [
        sqrt((r_accuracy * (1 - r_accuracy)) / (completed_samples))
        for r_accuracy, completed_samples in zip(
            non_reasoning_accuracies, completed_samples
        )
    ]

    non_reasoning_instruction_following_fracs = [
        result.results.scores[0].metrics["instruction_following"].value
        for result in non_reasoning_clue_difficulty_results
        if result.results is not None
    ]

    save_clue_difficulty_data_to_json(
        config=config,
        labels=[behavior.value for behavior in cases],
        reasoning_accuracies=reasoning_accuracies,
        non_reasoning_accuracies=non_reasoning_accuracies,
        difficulty_scores=difficulty_scores,
        difficulty_stderrs=difficulty_stderrs,
        non_reasoning_instruction_following_fracs=non_reasoning_instruction_following_fracs,
        path=RAW_DATA_PATH,
    )
