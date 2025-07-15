import os
from datetime import datetime
from typing import List
from math import sqrt

from dotenv import load_dotenv
from tqdm import tqdm

from filtering import get_problem_difficulty
from free_response_behaviors import FreeResponseBehavior, FR_FUNCTION_DICT
from free_response_clue_difficulty import get_free_response_clue_difficulty
from free_response_llm_faithfulness import get_free_response_faithfulness_score
from graph_utils import (
    save_raw_data_to_json,
)
from parsing import parse_args
from utils.prompt_utils import load_prompt_module
from utils.question_prompts.default import DEFAULT_QUESTION_PREFIX

load_dotenv()

if __name__ == "__main__":
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "Unknown")
    print(f"Anthropic API Key: {anthropic_api_key}")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "Unknown")
    print(f"OpenAI API Key: {openai_api_key}")
    config = parse_args()

    TOP_LEVEL_LOG_DIR: str = f"./logs/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{''.join([j[0] for j in config.model.replace('/', '-').split('-')])}-F_{config.score_faithfulness}-Q_{config.question_prompt.split('/')[-1].split('.')[0]}-J_{config.judge_prompt.split('/')[-1].split('.')[0]}/"
    RAW_DATA_PATH: str = f"./results/faithfulness/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{''.join([j[0] for j in config.model.replace('/', '-').split('-')])}-F_{config.score_faithfulness}-Q_{config.question_prompt.split('/')[-1].split('.')[0]}-J_{config.judge_prompt.split('/')[-1].split('.')[0]}.json"
    PROMPT_MODULE = load_prompt_module(config.question_prompt)
    QUESTION_PREFIX = PROMPT_MODULE.QUESTION_PREFIX
    QUESTION_SUFFIX = PROMPT_MODULE.QUESTION_SUFFIX
    HINT_SUFFIX = PROMPT_MODULE.HINT_SUFFIX
    JUDGE_PROMPT = load_prompt_module(config.judge_prompt).JUDGE_PROMPT
    QUESTION_PREFIX_NO_HINT = getattr(PROMPT_MODULE, 'QUESTION_PREFIX_NO_HINT', QUESTION_PREFIX)

    faithfulness_scores: List[float] = []
    faithfulness_stderrs: List[float] = []
    difficulty_scores: List[float] = []
    difficulty_stderrs: List[float] = []
    reasoning_accuracies: List[float] = []
    non_reasoning_accuracies: List[float] = []
    take_hints_scores: List[float] = []
    samples: List[int] = []
    detailed_data_all: List[dict] = []

    cases = [FreeResponseBehavior.SYCOPHANCY_HARD_MATH]#, FreeResponseBehavior.REWARD_HACKING, FreeResponseBehavior.MACHINE_LEARNING_EASY_ANSWER, FreeResponseBehavior.JUPYTER_NOTEBOOK_HARD_UNICODE, FreeResponseBehavior.REWARD_HACKING_I_READ_ONLINE_AMC_8_2022_7, FreeResponseBehavior.REWARD_HACKING_EMAIL_CHAIN__AMC_8_2020_1,  FreeResponseBehavior.CSV_DATA_MEDIUM_HEX]
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
            dataset[:1],
            behavior,
            model=config.model,
            max_connections=config.max_connections,
            limit=100,
            display=config.display,
            log_dir=TOP_LEVEL_LOG_DIR,
            temperature=config.temperature,
            prompt_prefix=QUESTION_PREFIX,
            prompt_prefix_no_hint=QUESTION_PREFIX_NO_HINT,
            prompt_suffix=QUESTION_SUFFIX,
            hint_suffix=HINT_SUFFIX,
            judge_prompt=JUDGE_PROMPT,
            score_faithfulness=config.score_faithfulness,
            test_monitor_false_positives=config.test_monitor_false_positives,
            epochs=config.epochs,
            scorer_model=config.scorer_model,
        )
        
        if not config.test_monitor_false_positives:
            reasoning_accuracies.append(reasoning_accuracy)
            non_reasoning_accuracies.append(non_reasoning_accuracy)
            difficulty_scores.append(1 - non_reasoning_accuracy)
            difficulty_stderrs.append(non_reasoning_stderr)
        
        faithfulness_scores.append(p_acknowledged_clue)
        faithfulness_stderrs.append(faithfulness_stderr)
        take_hints_scores.append(p_take_hints)
        samples.append(completed_samples)
        
        # Collect detailed data if available
        if config.test_monitor_false_positives and detailed_data:
            detailed_data_all.extend(detailed_data)

    labels = [case.value for case in cases if case not in excluded_behaviors]
    
    # Calculate and print statistics for "Of the cases where state_correct = True, % acknowledged_clue"
    if config.test_monitor_false_positives and detailed_data_all:
        # Filter for cases where state_correct = True
        correct_cases = [data for data in detailed_data_all if data.get("state_correct", False)]
        
        if correct_cases:
            # Calculate percentage of acknowledged_clue for correct cases
            acknowledged_count = sum(1 for data in correct_cases if data.get("acknowledged_clue", False))
            total_correct = len(correct_cases)
            percentage_acknowledged = acknowledged_count / total_correct
            
            # Calculate standard error
            stderr = sqrt((percentage_acknowledged * (1 - percentage_acknowledged)) / total_correct)
            
            print(f"\n=== Statistics for cases where state_correct = True ===")
            print(f"Total correct cases: {total_correct}")
            print(f"Cases that acknowledged clue: {acknowledged_count}")
            print(f"Percentage acknowledged clue: {percentage_acknowledged:.4f} ({percentage_acknowledged*100:.2f}%)")
            print(f"Standard error: {stderr:.4f}")
            print(f"95% confidence interval: [{percentage_acknowledged - 1.96*stderr:.4f}, {percentage_acknowledged + 1.96*stderr:.4f}]")
        else:
            print(f"\n=== Statistics for cases where state_correct = True ===")
            print("No cases found where state_correct = True")
    
    save_raw_data_to_json(
        config,
        labels,
        reasoning_accuracies,
        non_reasoning_accuracies,
        difficulty_scores,
        difficulty_stderrs,
        faithfulness_scores,
        faithfulness_stderrs,
        take_hints_scores,
        samples,
        RAW_DATA_PATH,
        detailed_data=detailed_data_all if config.test_monitor_false_positives else None,
    )
