from pathlib import Path

from app.graph_retrieval import GraphRetrieval


GRAPH_PATH = Path(__file__).parent / "interactive_agent_graph.json"


def print_experiences(results):
    if not results:
        print("\nNo relevant experience found.")
        return

    print("\nRETRIEVED EXPERIENCES")
    print("-" * 70)

    for i, item in enumerate(results, 1):
        print(f"{i}. {item['experience']}")
        print(f"   Confidence : {item['confidence']:.2f}")
        print(f"   Validated  : {item['validated']}")
        print(f"   Feedback   : {item['feedback_count']}")
        print(f"   Graph Score: {item['graph_score']:.4f}")
        print()


def main():

    print("=" * 70)
    print("EVO-GRAPH PERSISTENT OFFLINE AGENT")
    print("=" * 70)

    graph = GraphRetrieval()

    # ---------------------------------------------------------
    # Load previous graph if available
    # ---------------------------------------------------------
    if GRAPH_PATH.exists():
        graph.load(str(GRAPH_PATH))
        print("\nExisting learned graph loaded.")
    else:
        print("\nNo previous graph found. Creating initial experiences.")

        graph.add_skill(
            "skill_python",
            "Python Debugging"
        )

        graph.add_topic(
            "topic_debugging",
            "Debugging"
        )

        graph.connect_topic_to_skill(
            "topic_debugging",
            "skill_python"
        )

        graph.learn(
            "experience_traceback",
            "Read the Python traceback and inspect the failing line before changing code.",
            "skill_python",
            confidence=0.60
        )

        graph.learn(
            "experience_print_debug",
            "Use print statements to inspect Python variables while debugging a program.",
            "skill_python",
            confidence=0.60
        )

        graph.save(str(GRAPH_PATH))

    print(f"Graph file: {GRAPH_PATH}")
    print("Gemini: DISABLED")
    print("Learning: ENABLED")
    print("-" * 70)

    while True:

        question = input(
            "\nAsk EVO-GRAPH (type 'exit' to stop): "
        ).strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        # -----------------------------------------------------
        # Retrieve
        # -----------------------------------------------------
        results = graph.retrieve(
            question,
            limit=3
        )

        print_experiences(results)

        if not results:
            continue

        # -----------------------------------------------------
        # Generate offline answer
        # -----------------------------------------------------
        top = results[0]

        print("EVO-GRAPH ANSWER")
        print("-" * 70)
        print(top["experience"])

        print("\n" + "-" * 70)
        print("Was this helpful?")
        print("1 = Helpful")
        print("2 = Not helpful")
        print("3 = Skip")

        feedback = input("Feedback: ").strip()

        # -----------------------------------------------------
        # Feedback learning
        # -----------------------------------------------------
        if feedback in ("1", "2"):

            # Extract experience ID safely
            experience_id = (
                top.get("experience_id")
                or top.get("id")
            )

            if experience_id:

                node = graph.graph.graph.nodes.get(
                    experience_id,
                    {}
                )

                if feedback == "1":

                    print("\nApplying POSITIVE feedback...")

                    graph.graph.update_experience(
                        experience_id,
                        "positive"
                    )

                else:

                    print("\nApplying NEGATIVE feedback...")

                    graph.graph.update_experience(
                        experience_id,
                        "negative"
                    )

                # Show updated state
                node = graph.graph.graph.nodes.get(
                    experience_id,
                    {}
                )

                print(
                    f"Confidence : "
                    f"{node.get('confidence', 0):.2f}"
                )

                print(
                    f"Validated  : "
                    f"{node.get('validated', False)}"
                )

                print(
                    f"Feedback   : "
                    f"{node.get('feedback_count', 0)}"
                )

                # -------------------------------------------------
                # SAVE LEARNING
                # -------------------------------------------------
                graph.save(str(GRAPH_PATH))

                print("\nGraph updated and saved.")

            else:
                print(
                    "\nCould not identify the selected "
                    "experience ID."
                )

        else:
            print("\nFeedback skipped.")

    # ---------------------------------------------------------
    # Final save
    # ---------------------------------------------------------
    graph.save(str(GRAPH_PATH))

    print("\n" + "=" * 70)
    print("FINAL GRAPH SAVED")
    print("=" * 70)
    print(f"Location: {GRAPH_PATH}")


if __name__ == "__main__":
    main()