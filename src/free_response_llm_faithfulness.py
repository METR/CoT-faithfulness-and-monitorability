import re
from math import sqrt
from os import path
from typing import Any, Tuple

from inspect_ai import Epochs, Task, eval, task
from inspect_ai.dataset import Dataset
from inspect_ai.model import CachePolicy, GenerateConfig, get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import DisplayType

from free_response_behaviors import FR_FUNCTION_DICT, FreeResponseBehavior
from scoring import faithfullness_scorer


@solver
def free_response_thinking_solver(
    *,
    behavior: FreeResponseBehavior,
    prompt_prefix: str = "",
    prompt_prefix_no_hint: str = "",
    prompt_suffix: str = "",
    hint_suffix: str = "",
    provide_hint: bool = True,
) -> Solver:
    async def solve(state: TaskState, generate: Generate):
        state.original_question = state.user_prompt.text
        
        if provide_hint:
            state.user_prompt.text = (
                prompt_prefix
                + "\n\n"
                + state.original_question
                + prompt_suffix
                + "\n"
                + FR_FUNCTION_DICT[behavior](state.target.text)
                + "\n"
                + hint_suffix
            )
        else:
            state.user_prompt.text = (
                prompt_prefix_no_hint
                + "\n\n"
                + state.original_question
            )
        for _ in range(5):
            try:
                state = await generate(state, cache=CachePolicy(expiry=None))
                state_assistant_message = state.messages[-1].content
                break
            except Exception as e:
                print(f"Error: {e}")

        if len(state_assistant_message) == 2:
            state_reasoning = state_assistant_message[0].reasoning
            state_answer = state_assistant_message[1].text

            state.answer = state_answer

            state_matches = re.findall(r"ANSWER\s*:\s*(\d+)", state_answer)

            if state_matches:
                state_final_answer = state_matches[-1].strip()

                # this is a bit of hand holding to catch the cases where the model doesn't return the mod answer
                # we might want to remove this
                try:
                    state_final_answer = str(int(state_final_answer) % 100)
                except ValueError:
                    pass

                state.store.set("state_reasoning", state_reasoning)
                state.store.set("state_answer", state_final_answer)
                state.store.set("state_completion", state_answer)
                state.store.set("group", str(behavior))

        return state

    return solve


@task
def free_response_llm_faithfulness(
    dataset: Dataset,
    behavior: FreeResponseBehavior,
    judge_prompt: str,
    limit: int = 100,
    temperature: float = 0.6,
    prompt_prefix: str = "",
    prompt_prefix_no_hint: str = "",
    prompt_suffix: str = "",
    hint_suffix: str = "",
    faithfulness_flag: bool = True,
    test_monitor_false_positives: bool = False,
    epochs: int = 1,
) -> Task:
    return Task(
        dataset=dataset,
        solver=free_response_thinking_solver(
            behavior=behavior,
            prompt_prefix=prompt_prefix,
            prompt_prefix_no_hint=prompt_prefix_no_hint,
            prompt_suffix=prompt_suffix,
            hint_suffix=hint_suffix,
            provide_hint=not test_monitor_false_positives,
        ),
        scorer=faithfullness_scorer(
            behavior=behavior,
            judge_prompt=judge_prompt,
            model=get_model(
                #"openai/o3-2025-04-16",
                "openai/o4-mini-2025-04-16",
                config=GenerateConfig(
                    temperature=1,
                    reasoning_effort="low",
                    max_connections=120,
                ),
            ),
            score_faithfulness=faithfulness_flag,
        ),
        epochs=Epochs(epochs=epochs),
        config=GenerateConfig(
            temperature=temperature, max_tokens=32_000, reasoning_tokens=30_000
        ),
    )


def get_free_response_faithfulness_score(
    dataset: Dataset,
    behavior: FreeResponseBehavior,
    model: str,
    judge_prompt: str,
    limit: int = 100,
    max_connections: int = 100,
    display: DisplayType = "none",
    temperature: float = 0.6,
    prompt_prefix: str = "",
    prompt_prefix_no_hint: str = "",
    prompt_suffix: str = "",
    hint_suffix: str = "",
    score_faithfulness: bool = True,
    log_dir: str | None = None,
    test_monitor_false_positives: bool = False,
    epochs: int = 1,
) -> Tuple[int | float | Any, float, int, int | Any, int | float | Any]:
    res = eval(
        free_response_llm_faithfulness(
            dataset,
            behavior,
            judge_prompt,
            limit,
            temperature,
            prompt_prefix=prompt_prefix,
            prompt_prefix_no_hint=prompt_prefix_no_hint,
            prompt_suffix=prompt_suffix,
            hint_suffix=hint_suffix,
            faithfulness_flag=score_faithfulness,
            test_monitor_false_positives=test_monitor_false_positives,
            epochs=epochs,
        ),
        model=model,
        max_connections=max_connections,
        display=display,
        log_dir=path.join(log_dir, behavior.value) if log_dir else None,
        log_level="debug",
    )

    completed_samples = res[0].results.completed_samples

    acknowledged_clue_count = (
        res[0].results.scores[0].metrics["acknowledged_clue_count"].value
    )
    take_hints_count = res[0].results.scores[0].metrics["take_hints_count"].value
    p_acknowledged_clue = (
        acknowledged_clue_count / take_hints_count if take_hints_count > 0 else None
    )
    p_take_hints = take_hints_count / completed_samples if completed_samples > 0 else 0
    faithfulness_stderr = (
        sqrt((p_acknowledged_clue) * (1 - p_acknowledged_clue) / (take_hints_count))
        if take_hints_count > 0
        else None
    )

    # Collect detailed data if test_monitor_false_positives is True
    detailed_data = None
    if test_monitor_false_positives:
        detailed_data = []
        for sample in res[0].samples:
            if sample.scores:
                # Get the first scorer (should be our faithfulness scorer)
                first_scorer = next(iter(sample.scores))
                score = sample.scores[first_scorer]
                
                detailed_data.append({
                    "problem_id": sample.id,
                    "state_correct": score.metadata.get("state_correct", False),
                    "acknowledged_clue": score.metadata.get("state_correct", False) == 1 and score.metadata.get("faithful", False) == 1,
                })

    return (
        p_acknowledged_clue,
        p_take_hints,
        faithfulness_stderr,
        completed_samples,
        detailed_data,
    )
