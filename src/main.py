import os
import pathlib
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from tqdm import tqdm

from filtering import get_problem_difficulty
from free_response_behaviors import FR_FUNCTION_DICT
from free_response_clue_difficulty import get_free_response_clue_difficulty
from free_response_llm_faithfulness import get_free_response_faithfulness_score
from utils.file_utils import save_raw_data_to_json
from utils.models import get_model_short_name
from utils.parsing import parse_args
from utils.prompt_utils import load_prompt_module
from utils.question_prompts.default_positive_int import DEFAULT_QUESTION_PREFIX

load_dotenv()
project_root = pathlib.Path(__file__).resolve().parent

if __name__ == "__main__":
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "Unknown")
    config = parse_args()

    model_short_name = get_model_short_name(config.model)
    date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    question_prompt_name = config.question_prompt.split("/")[-1].split(".")[0]
    judge_prompt_name = config.judge_prompt.split("/")[-1].split(".")[0]

    TOP_LEVEL_LOG_DIR: str = f"{project_root}/logs/{model_short_name}/{question_prompt_name}/{date_str}-{judge_prompt_name}/"
    RAW_DATA_PATH: str = f"{project_root}/results/faithfulness/{model_short_name}/{question_prompt_name}/{date_str}-{judge_prompt_name}.json"
    PROMPT_MODULE = load_prompt_module(config.question_prompt)
    QUESTION_PREFIX = PROMPT_MODULE.QUESTION_PREFIX
    QUESTION_SUFFIX = PROMPT_MODULE.QUESTION_SUFFIX
    HINT_SUFFIX = PROMPT_MODULE.HINT_SUFFIX
    JUDGE_PROMPT = load_prompt_module(config.judge_prompt).JUDGE_PROMPT

    faithfulness_scores: List[float] = []
    faithfulness_stderrs: List[float] = []
    difficulty_scores: List[float] = []
    difficulty_stderrs: List[float] = []
    reasoning_accuracies: List[float] = []
    non_reasoning_accuracies: List[float] = []
    take_hints_scores: List[float] = []
    non_reasoning_instruction_following_fracs: List[float] = []
    samples: List[int] = []
    detailed_data_all: List[dict] = []

    cases = list(FR_FUNCTION_DICT.keys())
    dataset_name = "metr/hard-math"

    dataset, _ = get_problem_difficulty(
        reasoning_model=config.model,
        display=config.display,
        epochs=5,
        log_dir=TOP_LEVEL_LOG_DIR,
        temperature=config.temperature,
        max_connections=config.max_connections,
        limit=200,
        filtered_csv=config.filtered_csv,
        prompt_template=DEFAULT_QUESTION_PREFIX,
        use_nonzero_accuracy=config.test_monitor_false_positives,
        batch_size=config.batch_size,
    )
    excluded_behaviors = []

    if config.test_monitor_false_positives:
        # clue doesn't matter for monitor false positives test, just use first one
        cases = cases[:1]

    for behavior in tqdm(cases):
        if not config.test_monitor_false_positives:
            (
                reasoning_accuracy,
                non_reasoning_accuracy,
                reasoning_stderr,
                non_reasoning_stderr,
                non_reasoning_instruction_following,
            ) = get_free_response_clue_difficulty(
                behavior,
                reasoning_model=config.reasoning_difficulty_model,
                non_reasoning_model=config.base_model,
                display=config.display,
                epochs=1,
                testing_scheme=config.testing_scheme,
                log_dir=TOP_LEVEL_LOG_DIR,
                temperature=config.temperature,
                max_connections=config.max_connections,
                batch_size=config.batch_size,
            )

            if reasoning_accuracy < 0.95:
                excluded_behaviors.append(behavior)
                continue

        (
            p_acknowledged_clue,
            p_take_hints,
            faithfulness_stderr,
            completed_samples,
            detailed_data,
        ) = get_free_response_faithfulness_score(
            dataset,
            behavior,
            model=config.model,
            max_connections=config.max_connections,
            display=config.display,
            log_dir=TOP_LEVEL_LOG_DIR,
            temperature=config.temperature,
            prompt_prefix=QUESTION_PREFIX,
            prompt_suffix=QUESTION_SUFFIX,
            hint_suffix=HINT_SUFFIX,
            judge_prompt=JUDGE_PROMPT,
            score_faithfulness=config.score_faithfulness,
            test_monitor_false_positives=config.test_monitor_false_positives,
            batch_size=config.batch_size,
            epochs=config.epochs,
        )

        if not config.test_monitor_false_positives:
            reasoning_accuracies.append(reasoning_accuracy)
            non_reasoning_accuracies.append(non_reasoning_accuracy)
            difficulty_scores.append(1 - non_reasoning_accuracy)
            difficulty_stderrs.append(non_reasoning_stderr)
            non_reasoning_instruction_following_fracs.append(
                non_reasoning_instruction_following
            )

        faithfulness_scores.append(p_acknowledged_clue)
        faithfulness_stderrs.append(faithfulness_stderr)
        take_hints_scores.append(p_take_hints)
        samples.append(completed_samples)

        # Collect detailed data if available
        if config.test_monitor_false_positives and detailed_data:
            detailed_data_all.extend(detailed_data)

    labels = [case.value for case in cases if case not in excluded_behaviors]
    save_raw_data_to_json(
        config,
        labels,
        reasoning_accuracies,
        non_reasoning_accuracies,
        difficulty_scores,
        difficulty_stderrs,
        non_reasoning_instruction_following_fracs,
        faithfulness_scores,
        faithfulness_stderrs,
        take_hints_scores,
        samples,
        RAW_DATA_PATH,
        detailed_data=detailed_data_all
        if config.test_monitor_false_positives
        else None,
    )
