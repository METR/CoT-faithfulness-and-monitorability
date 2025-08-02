import anthropic
import openai
from dotenv import load_dotenv
from exp_behaviors import EXP_BEHAVIORS
from prompts import SYSTEM_PROMPT_V0, SYSTEM_PROMPT_V1

# Load environment variables from .env file
load_dotenv()
FIREWORKS_CLIENT = openai.OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key="<API_KEY>",
)
ANTHROPIC_CLIENT = anthropic.Anthropic()


def get_token_fireworks(
    client, clue: str, history: str, iteration: int, system_prompt: str
):
    response = client.chat.completions.create(
        model="accounts/fireworks/models/deepseek-v3",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": clue,
            },
            {
                "role": "assistant",
                "content": history + "Step " + str(iteration) + ": ",
            },
        ],
        max_tokens=1,
        temperature=0.0,
    )
    return response.choices[0].message.content


def get_answer_fireworks(
    client, clue: str, history: str, iteration: int, system_prompt: str
):
    response = client.messages.create(
        model="accounts/fireworks/models/deepseek-v3",
        max_tokens=10,
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": clue},
            {"role": "assistant", "content": history},
        ],
    )
    return response.content[0].text.strip()


def get_token_anthropic(
    clue: str,
    history: str,
    iteration: int,
    system_prompt: str,
    output_tokens_per_step: int,
):
    max_retries = 5
    for _ in range(max_retries):
        response = ANTHROPIC_CLIENT.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=output_tokens_per_step,
            system=system_prompt,
            temperature=0.0,
            messages=[
                {"role": "user", "content": clue},
                {
                    "role": "assistant",
                    "content": history + "Step " + str(iteration) + ":",
                },
            ],
            stop_sequences=["\nStep"],
        )
        output = response.content[0].text
        print(f"Step {iteration}: {output}")
        if output[0] == " ":
            output = output.split("#")[0].strip()
            return output

    raise Exception(
        f"Failed to get the model to output space as the first token after {max_retries} retries"
    )


def get_answer_anthropic(clue: str, history: str, iteration: int, system_prompt: str):
    response = ANTHROPIC_CLIENT.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=100,
        system=system_prompt,
        temperature=0.0,
        messages=[
            {"role": "user", "content": clue},
            {"role": "assistant", "content": history},
        ],
    )
    return response.content[0].text.strip()


def get_next_step(
    clue: str,
    history: str,
    iteration: int,
    system_prompt: str,
    output_tokens_per_step: int,
) -> tuple[str, int, bool]:
    answer_step = False
    output = get_token_anthropic(
        clue,
        history,
        iteration,
        system_prompt,
        output_tokens_per_step,
    )
    # output = get_token_fireworks(
    #     FIREWORKS_CLIENT, clue, history, iteration, system_prompt
    # )
    if "ANSWER" in output:
        answer_step = True
        history += f"Step {iteration}: {output}:"
    else:
        history += f"Step {iteration}: {output}\n"
        iteration += 1

    return history, iteration, answer_step


if __name__ == "__main__":
    clue = EXP_BEHAVIORS[
        0
    ]  # this is just a test clue, eventually we want to test it for all example behaviors, and then for all behaviors in free_response_behaviors.py
    system_prompt = SYSTEM_PROMPT_V1
    output_tokens_per_step = 2  # this needs to be a higher value if we allow the model to output comments each step
    history = ""
    iteration = 1
    max_steps = 20

    print(clue)
    print("--------------------------------")
    for _ in range(max_steps):
        history, iteration, answer_step = get_next_step(
            clue, history, iteration, system_prompt, output_tokens_per_step
        )
        if answer_step:
            answer = get_answer_anthropic(clue, history, iteration, system_prompt)
            print(answer)
            break
