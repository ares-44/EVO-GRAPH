import json
from pathlib import Path

from graph.graph_manager import EvoGraph

BASE = Path("data/experiment")
QUESTIONS = BASE / "questions.json"
OUTPUT = BASE / "evo_graph_seed.json"


def build_seed_graph():
    with open(QUESTIONS, "r", encoding="utf-8") as file:
        questions = json.load(file)

    graph = EvoGraph()

    categories = sorted({item["category"] for item in questions})

    for index, category in enumerate(categories, start=1):
        graph.add_node(
            f"skill_{index:02d}",
            "SKILL",
            category
        )

    category_to_skill = {
        category: f"skill_{index:02d}"
        for index, category in enumerate(categories, start=1)
    }

    for index, item in enumerate(questions, start=1):
        skill_id = category_to_skill[item["category"]]
        experience_text = (
            f"For {item['question']} use the key concepts: "
            + "; ".join(item["reference_points"])
        )

        graph.add_experience(
            f"seed_exp_{index:02d}",
            experience_text,
            skill_id,
            confidence=0.8,
            validated=True
        )

    graph.save_graph(str(OUTPUT))
    print(f"Seed graph created: {OUTPUT}")
    print(f"Nodes: {graph.graph.number_of_nodes()}")
    print(f"Relationships: {graph.graph.number_of_edges()}")


if __name__ == "__main__":
    build_seed_graph()
