
from pathlib import Path

from graph.graph_manager import EvoGraph


class GraphRetrieval:

    def __init__(self):

        self.graph = EvoGraph()

    # ========================================================
    # ADD SKILL
    # ========================================================

    def add_skill(
        self,
        skill_id,
        skill_name
    ):

        self.graph.add_node(
            skill_id,
            "SKILL",
            skill_name
        )

    # ========================================================
    # ADD TOPIC
    # ========================================================

    def add_topic(
        self,
        topic_id,
        topic_name
    ):

        self.graph.add_node(
            topic_id,
            "TOPIC",
            topic_name
        )

    # ========================================================
    # CONNECT TOPIC TO SKILL
    # ========================================================

    def connect_topic_to_skill(
        self,
        topic_id,
        skill_id
    ):

        self.graph.add_relationship(
            topic_id,
            skill_id,
            "RELATED_TO"
        )

    # ========================================================
    # LEARN
    # ========================================================

    def learn(
        self,
        experience_id,
        experience,
        skill_id=None,
        confidence=0.5,
        validated=False
    ):

        self.graph.add_experience(
            experience_id,
            experience,
            skill_id,
            confidence=confidence,
            validated=validated
        )

    # ========================================================
    # RETRIEVE
    # ========================================================

    def retrieve(
        self,
        question,
        limit=3
    ):

        # ----------------------------------------------------
        # Ask the graph directly.
        # ----------------------------------------------------

        results = self.graph.search_experiences(
            question,
            limit=limit,
            validated_only=False,
            min_score=0.10
        )

        if not results:
            return []

        # ----------------------------------------------------
        # Graph-aware score.
        #
        # Semantic relevance remains dominant.
        # Confidence/feedback influence ranking but
        # cannot overpower strong semantic relevance.
        # ----------------------------------------------------

        ranked = []

        for item in results:

            semantic_score = float(
                item.get(
                    "semantic_score",
                    item.get("score", 0.0)
                )
            )

            confidence = float(
                item.get(
                    "confidence",
                    0.5
                )
            )

            validated = bool(
                item.get(
                    "validated",
                    False
                )
            )

            feedback_count = int(
                item.get(
                    "feedback_count",
                    0
                )
            )

            validation_bonus = (
                0.05
                if validated
                else 0.0
            )

            feedback_bonus = min(
                feedback_count * 0.01,
                0.05
            )

            graph_score = (
                (semantic_score * 0.90)
                + (confidence * 0.03)
                + validation_bonus
                + feedback_bonus
            )

            updated = dict(item)

            updated["graph_score"] = round(
                graph_score,
                4
            )

            ranked.append(updated)

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        ranked.sort(
            key=lambda item: (
                item["semantic_score"],
                item["graph_score"],
                item["confidence"]
            ),
            reverse=True
        )

        return ranked[:limit]

    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    def build_context(
        self,
        question,
        limit=3
    ):

        results = self.retrieve(
            question,
            limit=limit
        )

        if not results:

            return (
                "No relevant learned "
                "experience was found."
            )

        context = []

        for index, item in enumerate(
            results,
            start=1
        ):

            experience = item.get(
                "experience",
                ""
            )

            confidence = item.get(
                "confidence",
                0.0
            )

            validated = item.get(
                "validated",
                False
            )

            semantic_score = item.get(
                "semantic_score",
                0.0
            )

            graph_score = item.get(
                "graph_score",
                item.get("score", 0.0)
            )

            context.append(
                f"""
Experience {index}:
{experience}

Semantic relevance: {semantic_score:.4f}
Graph score: {graph_score:.4f}
Confidence: {confidence:.2f}
Validated: {validated}
""".strip()
            )

        return "\n\n".join(context)

    # ========================================================
    # SAVE
    # ========================================================

    def save(self, path):

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.graph.save_graph(
            str(path)
        )

    # ========================================================
    # LOAD
    # ========================================================

    def load(self, path):

        self.graph.load_graph(
            str(path)
        )


# ============================================================
# OFFLINE TEST
# ============================================================

if __name__ == "__main__":

    retrieval = GraphRetrieval()

    retrieval.add_skill(
        "skill_python",
        "Python Programming"
    )

    retrieval.learn(
        "experience_001",
        "Check Python error messages before changing code",
        "skill_python",
        confidence=0.8
    )

    retrieval.learn(
        "experience_002",
        "Use print statements to inspect Python variables while debugging a program",
        "skill_python",
        confidence=0.6
    )

    print(
        "\n===== GRAPH-AWARE RETRIEVAL TEST ====="
    )

    results = retrieval.retrieve(
        "How should I debug a Python error?",
        limit=3
    )

    for index, item in enumerate(
        results,
        start=1
    ):

        print(
            f"\n{index}. {item['id']}"
        )

        print(
            f"Experience: "
            f"{item['experience']}"
        )

        print(
            f"Semantic Score: "
            f"{item['semantic_score']}"
        )

        print(
            f"Graph Score: "
            f"{item['graph_score']}"
        )

        print(
            f"Confidence: "
            f"{item['confidence']}"
        )
