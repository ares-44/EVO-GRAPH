import json
from pathlib import Path

from app.graph_retrieval import GraphRetrieval


BASE_DIR = Path(__file__).resolve().parents[2]

GRAPH_FILE = (
    BASE_DIR
    / "data"
    / "experiment"
    / "end_to_end_graph.json"
)

RESULT_FILE = (
    BASE_DIR
    / "data"
    / "experiment"
    / "end_to_end_evolution_results.json"
)


def normalize(item):
    return {
        "id": item.get(
            "experience_id",
            item.get("id", "UNKNOWN")
        ),
        "confidence": round(
            float(item.get("confidence", 0.0)), 2
        ),
        "validated": item.get(
            "validated",
            False
        ),
        "feedback_count": int(
            item.get("feedback_count", 0)
        ),
        "text_score": round(
            float(
                item.get(
                    "text_score",
                    item.get("score", 0.0)
                )
            ),
            4
        ),
        "graph_score": round(
            float(
                item.get(
                    "graph_score",
                    item.get("score", 0.0)
                )
            ),
            4
        ),
    }


def show_results(title, results):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    for position, item in enumerate(results, 1):

        x = normalize(item)

        print(
            f"{position}. {x['id']}\n"
            f"   Confidence : {x['confidence']:.2f}\n"
            f"   Validated  : {x['validated']}\n"
            f"   Feedback   : {x['feedback_count']}\n"
            f"   Text Score : {x['text_score']:.4f}\n"
            f"   Graph Score: {x['graph_score']:.4f}"
        )


def main():

    print("\nEVO-GRAPH END-TO-END EVOLUTION TEST")

    # =========================================================
    # STEP 1 — Create the agent
    # =========================================================

    retrieval = GraphRetrieval()

    graph = retrieval.graph

    # =========================================================
    # STEP 2 — Create knowledge structure
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
    # STEP 3 — Add initial experiences
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
    # STEP 4 — FIRST QUESTION
    # =========================================================

    print("\nUSER QUESTION:")
    print(question)

    first_retrieval = retrieval.retrieve(
        question,
        limit=2
    )

    show_results(
        "BEFORE LEARNING",
        first_retrieval
    )

    first_top = normalize(
        first_retrieval[0]
    )

    print(
        "\nSelected experience:"
        f" {first_top['id']}"
    )

    # =========================================================
    # STEP 5 — Simulated user feedback
    # =========================================================

    print("\nUSER FEEDBACK:")
    print(
        "The traceback-first approach was helpful."
    )

    graph.update_experience(
        "experience_good",
        "positive"
    )

    print(
        "\nFeedback applied to "
        "experience_good."
    )

    # =========================================================
    # STEP 6 — Negative feedback on competing memory
    # =========================================================

    print(
        "\nUSER FEEDBACK:"
    )

    print(
        "The immediate-code-change approach "
        "was not helpful."
    )

    for _ in range(3):

        graph.update_experience(
            "experience_bad",
            "negative"
        )

    bad_node = graph.graph.nodes[
        "experience_bad"
    ]

    print(
        "Negative feedback applied 3 times."
    )

    print(
        f"experience_bad confidence: "
        f"{bad_node['confidence']:.2f}"
    )

    print(
        f"experience_bad validated: "
        f"{bad_node['validated']}"
    )

    # =========================================================
    # STEP 7 — Save evolved graph
    # =========================================================

    graph.save_graph(
        str(GRAPH_FILE)
    )

    print(
        f"\nEvolved graph saved to:\n"
        f"{GRAPH_FILE}"
    )

    # =========================================================
    # STEP 8 — Ask the SAME question again
    # =========================================================

    second_retrieval = retrieval.retrieve(
        question,
        limit=2
    )

    show_results(
        "AFTER LEARNING — SAME QUESTION AGAIN",
        second_retrieval
    )

    second_top = normalize(
        second_retrieval[0]
    )

    # =========================================================
    # STEP 9 — Measure evolution
    # =========================================================

    first_order = [
        normalize(x)["id"]
        for x in first_retrieval
    ]

    second_order = [
        normalize(x)["id"]
        for x in second_retrieval
    ]

    ranking_changed = (
        first_order != second_order
    )

    good_became_top = (
        second_top["id"]
        == "experience_good"
    )

    # =========================================================
    # STEP 10 — Save experiment
    # =========================================================

    results = {

        "question": question,

        "before_learning": [
            normalize(x)
            for x in first_retrieval
        ],

        "after_learning": [
            normalize(x)
            for x in second_retrieval
        ],

        "initial_top": first_top["id"],

        "final_top": second_top["id"],

        "initial_order": first_order,

        "final_order": second_order,

        "ranking_changed": ranking_changed,

        "good_experience_became_top":
            good_became_top,

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
    ) as file:

        json.dump(
            results,
            file,
            indent=2
        )

    # =========================================================
    # FINAL REPORT
    # =========================================================

    print("\n" + "=" * 70)
    print("END-TO-END EVOLUTION RESULT")
    print("=" * 70)

    print(
        f"Initial top : {first_top['id']}"
    )

    print(
        f"Final top   : {second_top['id']}"
    )

    print(
        f"Ranking changed : "
        f"{ranking_changed}"
    )

    print(
        f"Good experience became top : "
        f"{good_became_top}"
    )

    print(
        "\nGemini called : False"
    )

    print(
        f"\nResults saved to:\n"
        f"{RESULT_FILE}"
    )

    print(
        "\nEND-TO-END EVOLUTION TEST COMPLETED"
    )


if __name__ == "__main__":
    main()