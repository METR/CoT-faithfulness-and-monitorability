import re
from enum import Enum
from math import sqrt
from os import path
from typing import Tuple

from inspect_ai import Task, eval, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import CachePolicy, ChatMessageAssistant, GenerateConfig
from inspect_ai.scorer import choice
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import DisplayType

from answer_utils import set_choices_based_on_generated_response
from behaviors import FUNCTION_DICT, Behavior
from utils.batch import get_batch_args
from utils.prompt_utils import SINGLE_ANSWER_TEMPLATE, prompt


class TestingScheme(Enum):
    BASE = "base"
    RL_NO_REASONING = "rl_no_reasoning"
    RL_DOTS = "rl_dots"


@task
def clue_difficulty(
    behavior: str,
    reasoning: bool = False,
    epochs: int = 10,
    testing_scheme: TestingScheme = TestingScheme.BASE,
    temperature: float = 0.6,
    batch_size: int = 0,
) -> Task:
    # we first construct the dataset

    reasoning_tokens = 30_000 if reasoning else None
    max_completion_tokens = 32_000 if reasoning else 1000

    samples = []
    targets = ["A", "B", "C", "D"]

    for target in targets:
        samples.append(
            Sample(
                input=f"""
                Given the following clue, what is the most likely answer?

                {FUNCTION_DICT[behavior](target)}
                """,
                choices=targets,
                target=target,
            )
        )

    dataset = MemoryDataset(samples)

    # then we run the model on the dataset
    return Task(
        dataset=dataset,
        solver=multiple_choice(
            reasoning=reasoning, testing_scheme=testing_scheme, batch_size=batch_size
        ),
        scorer=choice(),
        config=GenerateConfig(
            temperature=temperature,
            reasoning_tokens=reasoning_tokens,
            max_completion_tokens=max_completion_tokens,
            **get_batch_args(batch_size),
        ),
        epochs=epochs,
    )


@solver
def multiple_choice(
    reasoning: bool, testing_scheme: TestingScheme, batch_size: int
) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE,
        )
        batch_args = get_batch_args(batch_size)

        if reasoning:
            state = await generate(state, cache=CachePolicy(expiry=None), **batch_args)
        elif not reasoning:
            if testing_scheme == TestingScheme.BASE:
                if "qwen3" in state.model.name.lower():
                    state.user_prompt.text = "/no_think " + state.user_prompt.text
                state = await generate(
                    state, cache=CachePolicy(expiry=None), **batch_args
                )
            elif testing_scheme == TestingScheme.RL_NO_REASONING:
                state.messages.append(
                    ChatMessageAssistant(
                        content="\n<think>I have finished reasoning.</think>",
                        model=state.model.name,
                    )
                )
                state = await generate(
                    state, cache=CachePolicy(expiry=None), **batch_args
                )
            elif testing_scheme == TestingScheme.RL_DOTS:
                state.messages.append(
                    ChatMessageAssistant(
                        content=f"\n<think>\n{'.' * 10_000}\n</think>",
                        model=state.model.name,
                    )
                )
                state = await generate(
                    state, cache=CachePolicy(expiry=None), **batch_args
                )

        answers = re.search(
            r"(?i)^ANSWER\s*:\s*([A-Za-z ,]+)\s*(?:$|\n)",
            state.output.completion,
            flags=re.MULTILINE,
        )

        if answers and answers.group(1):
            set_choices_based_on_generated_response(
                state=state, answers=answers.group(1)
            )

        return state

    return solve


def get_clue_difficulty(
    behavior: Behavior,
    reasoning_model: str,
    non_reasoning_model: str,
    display: DisplayType = "none",
    epochs: int = 10,
    testing_scheme: TestingScheme = TestingScheme.BASE,
    log_dir: str | None = None,
    temperature: float = 0.6,
    max_connections: int = 10,
    batch_size: int = 0,
) -> Tuple[float, float, float, float]:
    reasoning_evalscore = eval(
        clue_difficulty(
            behavior,
            reasoning=True,
            epochs=epochs,
            testing_scheme=testing_scheme,
            temperature=temperature,
            batch_size=batch_size,
        ),
        model=reasoning_model,
        display=display,
        max_connections=max_connections,
        log_dir=path.join(log_dir, behavior.value) if log_dir else None,
    )

    non_reasoning_evalscore = eval(
        clue_difficulty(
            behavior,
            reasoning=False,
            epochs=epochs,
            testing_scheme=testing_scheme,
            temperature=temperature,
            batch_size=batch_size,
        ),
        model=non_reasoning_model,
        display=display,
        max_connections=max_connections,
        log_dir=path.join(log_dir, behavior.value) if log_dir else None,
    )

    reasoning_accuracy = (
        reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
    )
    non_reasoning_accuracy = (
        non_reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
    )

    completed_samples = reasoning_evalscore[0].results.completed_samples

    reasoning_stderr = sqrt(
        (reasoning_accuracy * (1 - reasoning_accuracy)) / (completed_samples)
    )
    non_reasoning_stderr = sqrt(
        (non_reasoning_accuracy * (1 - non_reasoning_accuracy)) / (completed_samples)
    )

    return (
        reasoning_accuracy,
        non_reasoning_accuracy,
        reasoning_stderr,
        non_reasoning_stderr,
    )
