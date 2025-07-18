#!/usr/bin/env python3

import os
import subprocess
import time
from datetime import datetime

BATCH_SIZE = 0
MAX_CONNECTIONS = 80
EPOCHS = 1

# Models and their filtered CSVs
models = {
    # "anthropic/claude-3-7-sonnet-latest": "problem_difficulty/claude-3-7-sonnet-latest_hard-math-v0_difficulty_positive_int.csv",
    # "anthropic/claude-opus-4-20250514": "problem_difficulty/claude-opus-4-20250514_hard-math-v0_difficulty_positive_int.csv",
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": "problem_difficulty/Qwen3-235B-A22B-fp8-tput_hard-math-v0_difficulty_positive_int.csv",
}

# Model short names for session naming
model_short_names = {
    # "anthropic/claude-3-7-sonnet-latest": "c3.7s",
    # "anthropic/claude-opus-4-20250514": "opus4",
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": "qwen3-235b",
}

# Question prompts to use
question_prompts = [
    "true_negative_prompts/ani.py",
    "true_negative_prompts/claude.py",
    "true_negative_prompts/deepseek.py",
    "true_negative_prompts/default.py",
    "true_negative_prompts/grug.py",
    "true_negative_prompts/pirate.py",
    "true_negative_prompts/shy.py",
    "true_negative_prompts/sydney.py",
    "true_negative_prompts/tutor.py",
    "true_negative_prompts/v0.py",
]

# Judge prompt
judge_prompt = "monitorability_0716.py"


# Launch a command in a screen session
def launch_screen_session(session_name: str, command: str) -> bool:
    if len(session_name) > 80:
        session_name = session_name[:80]
    screen_cmd = [
        "screen",
        "-dmS",
        session_name,
        "bash",
        "-c",
        f"{command}; echo 'Command finished with exit code:' $?; read -p 'Press Enter to close...'",
    ]
    try:
        subprocess.run(screen_cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error launching session {session_name}: {e}")
        return False


def main():
    print("Launching FPR runs in screen sessions...")
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    for model, filtered_csv in models.items():
        model_short = model_short_names.get(
            model, model.replace("/", "-").replace(".", "")
        )
        for question_prompt in question_prompts:
            question_short = os.path.splitext(os.path.basename(question_prompt))[0]
            session_name = f"{datetime_str}-fpr-{model_short}-{question_short}"
            cmd_parts = [
                "python main.py",
                f"--model {model}",
                f"--base_model {model}",
                f"--question_prompt utils/question_prompts/{question_prompt}",
                f"--judge_prompt utils/judge_prompts/{judge_prompt}",
                f"--filtered_csv {filtered_csv}",
                "--test-monitor-false-positives",
                f"--temperature 1",
                f"--batch_size {BATCH_SIZE}",
                f"--max_connections {MAX_CONNECTIONS}",
                f"--epochs {EPOCHS}",
            ]
            cmd = " ".join(cmd_parts)
            print(f"Starting session: {session_name}")
            print(f"Command: {cmd}")
            print("---")
            success = launch_screen_session(session_name, cmd)
            if not success:
                print(f"Failed to start session: {session_name}")
                continue
            time.sleep(1)
        print(f"Completed launching FPR sessions for {model}")
        print("-------------------------------------")
        print("")


if __name__ == "__main__":
    main()
