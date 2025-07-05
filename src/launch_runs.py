#!/usr/bin/env python3

import os
import subprocess
import time
from datetime import datetime

# Base configuration
BATCH_SIZE = 2000

# Define temperatures for each model
model_temperatures = {
    "anthropic/claude-3-7-sonnet-latest": 1,
    "anthropic/claude-opus-4-20250514": 1,
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": 0.6,
}

# Define models and their corresponding CSV files containing problem difficulty scores
models = {
    "anthropic/claude-3-7-sonnet-latest": "problem_difficulty/claude-3-7-sonnet-latest_hard-math-v0_difficulty.csv",
    "anthropic/claude-opus-4-20250514": "problem_difficulty/claude-opus-4-20250514_hard-math-v0_difficulty.csv",
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": "problem_difficulty/Qwen3-235B-A22B-fp8-tput_hard-math-v0_difficulty.csv",
}

# Define model short names for session naming
model_short_names = {
    "anthropic/claude-3-7-sonnet-latest": "c3.7s",
    "anthropic/claude-opus-4-20250514": "opus4",
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": "qwen3-235b",
}

# Combinations of question_prompt, judge_prompt, and score_faithfulness flag (True means the flag will be included)
model_combinations = {
    "anthropic/claude-3-7-sonnet-latest": [
        ("default.py", "faithfulness_narrow_0703.py", True),
        ("cheater_ai.py", "faithfulness_broad_0627.py", True),
        ("cheater_ai.py", "faithfulness_narrow_0703.py", True),
        ("cheater_ai.py", "monitorability_0624.py", False),
    ],
    "anthropic/claude-opus-4-20250514": [
        ("cheater_ai.py", "faithfulness_narrow_0703.py", True),
    ],
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": [
        ("moe_v4.py", "faithfulness_narrow_0627.py", True),
        ("moe_v4.py", "faithfulness_broad_0627.py", True),
        ("moe_v4.py", "monitorability_0624.py", False),
        ("grug.py", "faithfulness_broad_0627.py", True),
        ("grug.py", "faithfulness_narrow_0627.py", True),
        ("grug.py", "monitorability_0624.py", False),
        ("cheater_ai.py", "faithfulness_broad_0627.py", True),
        ("cheater_ai.py", "faithfulness_narrow_0627.py", True),
        ("cheater_ai.py", "monitorability_0624.py", False),
        ("general_instructive.py", "faithfulness_broad_0627.py", True),
        ("general_instructive.py", "faithfulness_narrow_0627.py", True),
        ("general_instructive.py", "monitorability_0624.py", False),
        ("tcgs_non_instructive.py", "faithfulness_broad_0627.py", True),
        ("tcgs_non_instructive.py", "faithfulness_narrow_0627.py", True),
        ("tcgs_non_instructive.py", "monitorability_0624.py", False),
    ],
}


def launch_screen_session(session_name: str, command: str) -> bool:
    """Launch a command in a screen session."""
    screen_cmd = [
        "screen",
        "-dmS",
        session_name,
        "bash",
        "-c",
        f"{command}; echo 'Command finished with exit code: $?'; read -p 'Press Enter to close...'",
    ]

    try:
        subprocess.run(screen_cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error launching session {session_name}: {e}")
        return False


def main():
    print("Launching runs in screen sessions...")
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Loop through each model
    for model, filtered_csv in models.items():
        if model not in model_combinations:
            print(f"Warning: No combinations defined for model {model}, skipping...")
            continue

        model_short = model_short_names.get(
            model, model.replace("/", "-").replace(".", "")
        )

        print(f"Starting runs for model: {model}")
        print(f"Using CSV: {filtered_csv}")
        print("")

        # Get temperature for this model
        temperature = model_temperatures[model]

        # Loop through each combination for this model
        for combo in model_combinations[model]:
            question_prompt, judge_prompt, score_faithfulness = combo

            # Remove .py extension for screen session naming
            question_short = os.path.splitext(os.path.basename(question_prompt))[0]
            judge_short = os.path.splitext(os.path.basename(judge_prompt))[0]

            # Create screen session name: model-question-judge
            session_name = (
                f"{datetime_str}-{model_short}-{question_short}-{judge_short}"
            )

            # Set score_faithfulness flag based on the boolean in the tuple
            score_faithfulness_flag = (
                "--score_faithfulness" if score_faithfulness else ""
            )

            # Build the full command
            cmd_parts = [
                "python main_faithfulness.py",
                f"--model {model}",
                f"--base_model {model}",
                f"--batch_size {BATCH_SIZE}",
                f"--temperature {temperature}",
                f"--filtered_csv {filtered_csv}",
                "--max_tasks 50",
                f"--question_prompt utils/question_prompts/{question_prompt}",
                f"--judge_prompt utils/judge_prompts/{judge_prompt}",
            ]

            if score_faithfulness_flag:
                cmd_parts.append(score_faithfulness_flag)

            cmd = " ".join(cmd_parts)

            print(f"Starting session: {session_name}")
            print(f"Command: {cmd}")
            print("---")

            # Launch in screen session
            success = launch_screen_session(session_name, cmd)
            if not success:
                print(f"Failed to start session: {session_name}")
                continue

            # Small delay to avoid overwhelming the system
            time.sleep(1)

        print(f"Completed launching sessions for {model}")
        print("-------------------------------------")
        print("")

    print("All sessions started!")
    print("Use 'screen -ls' to see active sessions")
    print("Use 'screen -r <session_name>' to attach to a session")


if __name__ == "__main__":
    main()
