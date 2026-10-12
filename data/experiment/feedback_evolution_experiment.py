import json
from pathlib import Path

from app.graph_retrieval import GraphRetrieval


BASE_DIR = Path(__file__).resolve().parents[2]

RESULT_FILE = (
    BASE_DIR
    / "data"
    / "experiment"
    / "feedback_evolution_results.json"
)


def get_value(item, *keys, default=None):
    """Get the first available key from a retrieval result."""
    for key in keys:
        if key in item:
            return item[key]

    return default


def normalize_result(item):
    """Convert actual retrieval output into our experiment format."""

    experience_id = get_value(
        item,
        "experience_id",
        "id",
        "node_id",
        "experience",
        default="UNKNOWN"
    )

    confidence = get_value(
        item,
        "confidence",
        default=0.0
    )

    validated = get_value(
        item,
        "validated",
        default=False
    )

    feedback_count = get_value(
        item,
        "feedback_count",
        default=0
    )

    text_score = get_value(
        item,
        "text_score",
        "score",
        default=0.0
    )

    graph_score = get_value(
        item,
        "graph_score",
        default=text_score
    )

    return {
        "experience_id": experience_id,
        "confidence": float(confidence),
        "validated": bool(validated),
        "feedback_count": int(feedback_count),
        "text_score": float(text_score),
        "graph_score": float(graph_score),
    }


def print_ranking(title, results):

    print(f"\n{'=' * 65}")
    print(title)
    print("=" * 65)

    if not results:
        print("No experiences retrieved.")
        return

    for i, item in enumerate(results, start=1):

        data = normalize_result(item)

        print(
            f"{i}. {data['experience_id']}\n"
            f"   Confidence : {data['confidence']:.2f}\n"
            f"   Validated  : {data['validated']}\n"
            f"   Feedback   : {data['feedback_count']}\n"
            f"   Text Score : {data['text_score']:.4f}\n"
            f"   Graph Score: {data['graph_score']:.4f}"
        )


def snapshot(results):

    return [
        normalize_result(item)
        for item in results
    ]


def get_order(results):

    return [
        normalize_result(item)["experience_id"]
        for item in results
    ]


def main():

    print(
        "\nEVO-GRAPH FEEDBACK → RETRIEVAL EVOLUTION TEST"
    )

    # =========================================================
    # 1. Create GraphRetrieval
    # =========================================================

    retrieval = GraphRetrieval()

    graph = retrieval.graph

    # =========================================================
    # 2. Create Python skill/topic
    # =========================================================

    retrieval.add_skill(
        "skill_python",
        "Python"
    )

    retrieval.add_topic(
        "topic_debugging",
        "Python Debugging"
    )

    retrieval.connect_topic_to_skill(
        "topic_debugging",
        "skill_python"
    )

    # =========================================================
    # 3. Create competing experiences
    # =========================================================

    graph.add_experience(
        experience_id="experience_good",
        experience=(
            "Read the Python traceback and inspect the "
            "failing line before changing code."
        ),
        skill_id="skill_python",
        confidence=0.60,
        validated=False,
    )

    graph.add_experience(
        experience_id="experience_bad",
        experience=(
            "Change the Python code immediately without "
            "inspecting the traceback."
        ),
        skill_id="skill_python",
        confidence=0.90,
        validated=True,
    )

    question = (
        "How should I troubleshoot a Python program?"
    )

    # =========================================================
    # 4. Initial retrieval
    # =========================================================

    initial = retrieval.retrieve(
        question,
        limit=2
    )

    print_ranking(
        "INITIAL RETRIEVAL",
        initial
    )

    # =========================================================
    # 5. Positive feedback on GOOD experience
    # =========================================================

    print(
        "\nApplying POSITIVE feedback "
        "to experience_good..."
    )

    graph.update_experience(
        "experience_good",
        "positive"
    )

    after_positive = retrieval.retrieve(
        question,
        limit=2
    )

    print_ranking(
        "AFTER POSITIVE FEEDBACK",
        after_positive
    )

    # =========================================================
    # 6. Negative feedback on BAD experience
    # =========================================================

    print(
        "\nApplying NEGATIVE feedback "
        "to experience_bad..."
    )

    for i in range(3):

        graph.update_experience(
            "experience_bad",
            "negative"
        )

        node = graph.graph.nodes[
            "experience_bad"
        ]

        print(
            f"Negative feedback #{i + 1}: "
            f"confidence = "
            f"{node['confidence']:.2f}, "
            f"validated = "
            f"{node['validated']}"
        )

    after_negative = retrieval.retrieve(
        question,
        limit=2
    )

    print_ranking(
        "AFTER NEGATIVE FEEDBACK",
        after_negative
    )

    # =========================================================
    # 7. Compare ranking
    # =========================================================

    initial_order = get_order(initial)

    final_order = get_order(after_negative)

    ranking_changed = (
        initial_order != final_order
    )

    if "experience_good" in final_order:

        good_final_rank = (
            final_order.index(
                "experience_good"
            ) + 1
        )

    else:

        good_final_rank = None

    if "experience_bad" in final_order:

        bad_final_rank = (
            final_order.index(
                "experience_bad"
            ) + 1
        )

    else:

        bad_final_rank = None

    # =========================================================
    # 8. Save experiment
    # =========================================================

    results = {

        "question": question,

        "initial": snapshot(initial),

        "after_positive_feedback":
            snapshot(after_positive),

        "after_negative_feedback":
            snapshot(after_negative),

        "initial_order":
            initial_order,

        "final_order":
            final_order,

        "ranking_changed":
            ranking_changed,

        "final_good_experience_rank":
            good_final_rank,

        "final_bad_experience_rank":
            bad_final_rank,

        "gemini_called": False,
    }

    RESULT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

    # =========================================================
    # 9. Final result
    # =========================================================

    print("\n" + "=" * 65)
    print("FINAL RESULT")
    print("=" * 65)

    print(
        f"Initial order : {initial_order}"
    )

    print(
        f"Final order   : {final_order}"
    )

    print(
        f"Ranking changed : {ranking_changed}"
    )

    print(
        f"Good experience final rank : "
        f"{good_final_rank}"
    )

    print(
        f"Bad experience final rank  : "
        f"{bad_final_rank}"
    )

    print(
        "\nResults saved to:"
    )

    print(RESULT_FILE)

    print(
        "\nFEEDBACK → RETRIEVAL TEST COMPLETED"
    )


if __name__ == "__main__":
    main()