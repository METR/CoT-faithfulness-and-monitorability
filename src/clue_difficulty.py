from inspect_ai import eval
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from typing import List, Tuple
from inspect_ai.scorer import choice
from inspect_ai.solver import Solver, solver, TaskState, Generate
from behaviors import FUNCTION_DICT, Behavior
from inspect_ai.model import GenerateConfig
from tqdm import tqdm
from prompt_utils import SINGLE_ANSWER_TEMPLATE
from answer_utils import set_choices_based_on_generated_response
import re
from prompt_utils import prompt


@task
def clue_difficulty(behavior: str, reasoning: bool = False) -> float:
    # we first construct the dataset

    reasoning_tokens = 30_000 if reasoning else 0

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
        solver=multiple_choice(),
        scorer=choice(),
        config=GenerateConfig(
            temperature=0.6,
            reasoning_tokens=reasoning_tokens,
            max_tokens=32768,
        ),
        epochs=5,
    )

    ...


@solver
def multiple_choice(behavior: Behavior | None = None) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue=FUNCTION_DICT[behavior](state.target.text),
            template=SINGLE_ANSWER_TEMPLATE,
        )

        state = await generate(state, cache=True)

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


model_pairs: List[Tuple[str, str]] = [  # reasoning model, non-reasoning model
    ("together/Qwen/QwQ-32B", "together/Qwen/Qwen2.5-72B-Instruct-Turbo"),
    ("anthropic/claude-3-7-sonnet-latest", "anthropic/claude-3-7-sonnet-latest"),
    ("together/deepseek-ai/DeepSeek-R1", "openrouter/deepseek/deepseek-chat"),
]


def get_clue_difficulty(
    behavior: Behavior, reasoning_model: str, non_reasoning_model: str
) -> float:
    reasoning_evalscore = eval(
        clue_difficulty(behavior, reasoning=True), model=reasoning_model
    )
    non_reasoning_evalscore = eval(
        clue_difficulty(behavior, reasoning=False), model=non_reasoning_model
    )

    return (
        reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
        - non_reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
    )


if __name__ == "__main__":
    models = model_pairs[0]
    reasoning_results = []
    non_reasoning_results = []

    cases = list(FUNCTION_DICT.keys())

    assert isinstance(cases, list)
    assert isinstance(cases[0], Behavior)

    for behavior in tqdm(cases):
        reasoning_evalscore = eval(
            clue_difficulty(behavior, reasoning=True), model=models[0]
        )
        non_reasoning_evalscore = eval(
            clue_difficulty(behavior, reasoning=False), model=models[1]
        )
        reasoning_results.append(
            reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
        )
        non_reasoning_results.append(
            non_reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
        )

    delta = [a - b for a, b in zip(reasoning_results, non_reasoning_results)]

    # Sort behaviors by delta value
    sorted_results = sorted(zip(cases, delta), key=lambda x: x[1], reverse=True)
    for behavior, delta in sorted_results:
        print(f"{behavior}: {delta}")
