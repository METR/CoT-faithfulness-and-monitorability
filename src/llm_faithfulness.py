import re
from copy import deepcopy
from math import sqrt
from os import path
from typing import Any, Tuple

from inspect_ai import Task, eval, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.model import CachePolicy, GenerateConfig, get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import DisplayType

from answer_utils import record_to_sample, set_choices_based_on_generated_response
from behaviors import FUNCTION_DICT, Behavior
from scoring import faithfullness_scorer
from utils.batch import get_batch_args
from utils.prompt_utils import SINGLE_ANSWER_TEMPLATE, prompt


@solver
def thinking_solver(
    *, behavior: Behavior, function_dict: dict = FUNCTION_DICT, batch_size: int = 0
) -> Solver:
    batch_args = get_batch_args(batch_size)

    async def solve(state: TaskState, generate: Generate):
        curr_choice = state.target.text
        control_state = deepcopy(state)

        control_state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE,
        )

        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue=function_dict[behavior](curr_choice),
            template=SINGLE_ANSWER_TEMPLATE,
        )

        # now we generate for both
        control_state = await generate(
            control_state,
            cache=CachePolicy(expiry=None),
            **batch_args,
        )
        state = await generate(state, cache=CachePolicy(expiry=None), **batch_args)

        control_assistant_message = control_state.messages[-1].content
        state_assistant_message = state.messages[-1].content

        if len(control_assistant_message) == 2 and len(state_assistant_message) == 2:
            control_reasoning = control_assistant_message[0].reasoning
            control_answer = control_assistant_message[1].text
            state_reasoning = state_assistant_message[0].reasoning
            state_answer = state_assistant_message[1].text

            state.answer = state_answer

            state_match = re.search(
                r"(?i)ANSWER\s*:\s*([A-Za-z]+)",
                state_answer,
            )

            control_match = re.search(
                r"(?i)ANSWER\s*:\s*([A-Za-z]+)",
                control_answer,
            )

            if state_match and control_match:
                state_answer = state_match.group(1).strip()
                control_answer = control_match.group(1).strip()

                set_choices_based_on_generated_response(state, state_answer)

                state.store.set("state_reasoning", state_reasoning)
                state.store.set("state_answer", state_answer)
                state.store.set("control_reasoning", control_reasoning)
                state.store.set("control_answer", control_answer)
                state.store.set("group", str(behavior))

        return state

    return solve


@task
def llm_faithfulness(
    clue: str,
    limit: int,
    temperature: float = 0.6,
    function_dict: dict = FUNCTION_DICT,
    batch_size: int = 0,
) -> Task:
    dataset = csv_dataset(
        csv_file="https://openaipublic.blob.core.windows.net/simple-evals/gpqa_diamond.csv",
        sample_fields=record_to_sample,
        shuffle_choices=True,
        limit=limit,
    )

    assert clue in [b.value for b in Behavior], (
        f"Clue must be one of {[b.value for b in Behavior]}"
    )

    batch_args = get_batch_args(batch_size)
    return Task(
        dataset=dataset,
        solver=thinking_solver(
            behavior=Behavior(clue), function_dict=function_dict, batch_size=batch_size
        ),
        scorer=faithfullness_scorer(
            model=get_model(
                "anthropic/claude-3-5-sonnet-latest",
                config=GenerateConfig(
                    temperature=1,
                    **batch_args,
                ),
            ),
            batch_size=batch_size,
        ),
        config=GenerateConfig(
            temperature=temperature,
            max_completion_tokens=32_000,
            reasoning_tokens=30_000,
            **batch_args,
        ),
    )


def get_faithfulness_score(
    behavior: Behavior,
    model: str,
    limit: int = 100,
    max_connections: int = 100,
    display: DisplayType = "none",
    log_dir: str | None = None,
    temperature: float = 0.6,
    function_dict: dict = FUNCTION_DICT,
    batch_size: int = 0,
) -> Tuple[int | float | Any, float, int, int | Any, int | float | Any]:
    res = eval(
        llm_faithfulness(
            clue=behavior.value,
            limit=limit,
            temperature=temperature,
            function_dict=function_dict,
            batch_size=batch_size,
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
    p_acknowledged_clue = acknowledged_clue_count / take_hints_count
    p_take_hints = take_hints_count / completed_samples
    faithfulness_stderr = sqrt(
        (p_acknowledged_clue) * (1 - p_acknowledged_clue) / (take_hints_count)
    )

    return (
        p_acknowledged_clue,
        p_take_hints,
        faithfulness_stderr,
        completed_samples,
    )
