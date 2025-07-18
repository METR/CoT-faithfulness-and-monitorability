import argparse
import dataclasses

from clue_difficulty import TestingScheme


@dataclasses.dataclass
class EvalConfig:
    model: str
    batch_size: int
    reasoning_difficulty_model: str
    base_model: str
    display: str
    testing_scheme: TestingScheme
    redteam: bool
    temperature: float
    max_connections: int
    filtered_csv: str
    question_prompt: str
    judge_prompt: str
    score_faithfulness: bool
    test_monitor_false_positives: bool
    max_tasks: int
    epochs: int


def parse_args() -> EvalConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default="anthropic/claude-3-7-sonnet-latest",
        required=False,
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=0,
        required=False,
    )
    parser.add_argument(
        "--reasoning_difficulty_model", type=str, default=None, required=False
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default="anthropic/claude-3-7-sonnet-latest",
        required=False,
    )
    parser.add_argument("--display", type=str, default="full", required=False)
    parser.add_argument(
        "--testing_scheme",
        type=str,
        default="base",
        required=False,
        choices=TestingScheme.__members__.keys(),
    )
    parser.add_argument(
        "--redteam",
        default=False,
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        required=False,
        help="Temperature parameter for model generation (default: 0.6)",
    )
    parser.add_argument(
        "--max_connections",
        type=int,
        default=20,
        required=False,
        help="Maximum number of concurrent connections with model provider (default: 20)",
    )
    parser.add_argument(
        "--filtered_csv",
        type=str,
        required=False,
        help="Path to csv file with difficulty scores instead of re-running filtering (default: None)",
    )
    parser.add_argument(
        "--question_prompt",
        type=str,
        default="utils/prompts/default.py",
        help="Path to prompt file (default: None)",
    )
    parser.add_argument(
        "--judge_prompt",
        type=str,
        default="utils/judge_prompts/faithfulness_0611.txt",
        help="Path to judge prompt file (default: None)",
    )
    parser.add_argument(
        "--score_faithfulness",
        default=False,
        action="store_true",
        help="Whether to score faithfulness (default: False)",
    )
    parser.add_argument(
        "--test-monitor-false-positives",
        default=False,
        action="store_true",
        help="Whether to test monitor false positives (default: False)",
    )
    parser.add_argument(
        "--max_tasks",
        type=int,
        default=5,
        required=False,
        help="Maximum number of tasks to evaluate in parallel (default: 5)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        required=False,
        help="Number of epochs to run (default: 1)",
    )
    args = parser.parse_args()
    ret = EvalConfig(**vars(args))
    ret.testing_scheme = TestingScheme(ret.testing_scheme.lower())
    if ret.batch_size:
        ret.max_connections = max(ret.max_connections, ret.batch_size)

    if ret.reasoning_difficulty_model is None:
        ret.reasoning_difficulty_model = ret.model
    return ret
