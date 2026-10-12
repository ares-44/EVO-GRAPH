import json
from pathlib import Path

from app.graph_retrieval import GraphRetrieval


BASE_DIR = Path(__file__).resolve().parents[2]

GRAPH_FILE = (
    BASE_DIR
    / "data"
    / "experiment"
    / "offline_agent_graph.json"
)


def show_memory(results):
    print("\n===== RETRIEVED EXPERIENCES =====")

    if not results:
        print("No relevant experience found.")
        return

    for i, item in enumerate(results, 1):

        experience_id = item.get(
            "experience_id",
            item.get("id", "UNKNOWN")
        )

        experience = item.get(
            "experience",
            "No experience text"
        )

        confidence = float(
            item.get("confidence", 0)
        )

        graph_score = float(
            item.get(
                "graph_score",
                item.get("score", 0)
            )
        )

        print(f"\n{i}. {experience_id}")
        print(f"   Experience : {experience}")
        print(f"   Confidence : {confidence:.2f}")
        print(f"   Graph Score: {graph_score:.4f}")


def get_id(item):
    return item.get(
        "experience_id",
        item.get("id", "UNKNOWN")
    )


def create_agent():
    retrieval = GraphRetrieval()

    graph = retrieval.graph

    retrieval.add_skill(
        "skill_python",
        "Python"
    )

    retrieval.add_skill(
        "skill_dsa",
        "Data Structures"
    )

    retrieval.add_topic(
        "topic_debugging",
        "Python Debugging"
    )

    retrieval.add_topic(
        "topic_dsa",
        "Data Structures"
    )

    retrieval.connect_topic_to_skill(
        "topic_debugging",
        "skill_python"
    )

    retrieval.connect_topic_to_skill(
        "topic_dsa",
        "skill_dsa"
    )

    # ---------------------------------------------------------
    # Python experience
    # ---------------------------------------------------------

    graph.add_experience(
        experience_id="exp_python_traceback",
        experience=(
            "When debugging Python, read the traceback and "
            "inspect the failing line before changing code."
        ),
        skill_id="skill_python",
        confidence=0.60,
        validated=False,
    )

    # ---------------------------------------------------------
    # DSA experience
    # ---------------------------------------------------------

    graph.add_experience(
        experience_id="exp_dsa_real_example",
        experience=(
            "When explaining data structures, keep the explanation "
            "short and include a simple real-world example."
        ),
        skill_id="skill_dsa",
        confidence=0.60,
        validated=False,
    )

    return retrieval


def answer_from_memory(question, results):

    if not results:
        return (
            "I don't have a learned experience for this "
            "question yet."
        )

    top = results[0]

    experience = top.get(
        "experience",
        ""
    )

    return (
        "Based on my learned experience:\n\n"
        f"{experience}"
    )


def apply_feedback(graph, results, feedback):

    if not results:
        print(
            "\nNo experience available to update."
        )
        return None

    selected = results[0]

    experience_id = get_id(selected)

    print(
        f"\nUpdating experience: "
        f"{experience_id}"
    )

    graph.update_experience(
        experience_id,
        feedback
    )

    node = graph.graph.nodes[
        experience_id
    ]

    print(
        f"Confidence : "
        f"{node['confidence']:.2f}"
    )

    print(
        f"Validated  : "
        f"{node['validated']}"
    )

    print(
        f"Feedback   : "
        f"{node['feedback_count']}"
    )

    return experience_id


def save_graph(graph):

    graph.save_graph(
        str(GRAPH_FILE)
    )

    print(
        f"\nGraph saved to:\n"
        f"{GRAPH_FILE}"
    )


def main():

    print("\n")
    print("=" * 70)
    print("EVO-GRAPH OFFLINE SELF-EVOLVING AGENT")
    print("=" * 70)

    print(
        "\nGemini: DISABLED"
    )

    print(
        "Mode: Offline graph + feedback learning"
    )

    retrieval = create_agent()

    graph = retrieval.graph

    # =========================================================
    # SESSION 1
    # =========================================================

    question = (
        "How should I debug a Python error?"
    )

    print("\n" + "=" * 70)
    print("SESSION 1")
    print("=" * 70)

    print(
        f"\nUSER:\n{question}"
    )

    results_before = retrieval.retrieve(
        question,
        limit=3
    )

    show_memory(results_before)

    answer = answer_from_memory(
        question,
        results_before
    )

    print(
        "\n===== EVO-GRAPH ANSWER ====="
    )

    print(answer)

    # =========================================================
    # USER FEEDBACK
    # =========================================================

    print(
        "\nUSER FEEDBACK:"
    )

    print(
        "positive"
    )

    selected_id = apply_feedback(
        graph,
        results_before,
        "positive"
    )

    # =========================================================
    # SAVE LEARNING
    # =========================================================

    save_graph(graph)

    # =========================================================
    # SESSION 2 — SAME QUESTION
    # =========================================================

    print("\n" + "=" * 70)
    print("SESSION 2 — SAME QUESTION")
    print("=" * 70)

    print(
        f"\nUSER:\n{question}"
    )

    results_after = retrieval.retrieve(
        question,
        limit=3
    )

    show_memory(results_after)

    answer_after = answer_from_memory(
        question,
        results_after
    )

    print(
        "\n===== EVO-GRAPH ANSWER AFTER LEARNING ====="
    )

    print(answer_after)

    # =========================================================
    # COMPARE
    # =========================================================

    before_top = (
        get_id(results_before[0])
        if results_before
        else None
    )

    after_top = (
        get_id(results_after[0])
        if results_after
        else None
    )

    print("\n" + "=" * 70)
    print("EVOLUTION SUMMARY")
    print("=" * 70)

    print(
        f"Before feedback : {before_top}"
    )

    print(
        f"After feedback  : {after_top}"
    )

    print(
        f"Top experience changed : "
        f"{before_top != after_top}"
    )

    print(
        "\nFeedback successfully entered "
        "the graph learning loop."
    )

    print(
        "\nOFFLINE AGENT TEST COMPLETED"
    )


if __name__ == "__main__":
    main()