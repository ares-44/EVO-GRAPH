import json
from pathlib import Path


DATASET_PATH = Path("data/humaneval/HumanEvalPlus.jsonl")


def load_humaneval():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    problems = []

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                problems.append(json.loads(line))

    return problems


if __name__ == "__main__":
    problems = load_humaneval()

    print("\n===== HUMAN EVAL+ DATASET =====")
    print(f"Total problems: {len(problems)}")

    print("\nFirst problem:")
    print("Task ID:", problems[0]["task_id"])
    print("Entry point:", problems[0]["entry_point"])

    print("\nPrompt:")
    print(problems[0]["prompt"])