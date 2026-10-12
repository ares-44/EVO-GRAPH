from graph.graph_manager import EvoGraph


class LearningEngine:

    def __init__(self):

        self.graph = EvoGraph()

    # ==========================================
    # TEXT NORMALIZATION
    # ==========================================

    def normalize_text(
        self,
        text
    ):

        return set(
            self.graph.tokenize(text)
        )

    # ==========================================
    # SIMILARITY
    # ==========================================

    def calculate_similarity(
        self,
        text1,
        text2
    ):

        words1 = self.normalize_text(
            text1
        )

        words2 = self.normalize_text(
            text2
        )

        if not words1 or not words2:

            return 0.0

        intersection = (
            words1 & words2
        )

        union = (
            words1 | words2
        )

        return (
            len(intersection)
            / len(union)
        )

    # ==========================================
    # FIND SIMILAR EXPERIENCE
    # ==========================================

    def find_similar_experience(
        self,
        experience_text,
        threshold=0.65
    ):

        best_id = None
        best_similarity = 0.0
        best_text = None

        for node_id, data in (
            self.graph.graph.nodes(
                data=True
            )
        ):

            if data.get(
                "type"
            ) != "EXPERIENCE":

                continue

            existing_text = data.get(
                "experience",
                data.get("name", "")
            )

            similarity = (
                self.calculate_similarity(
                    experience_text,
                    existing_text
                )
            )

            if similarity > best_similarity:

                best_similarity = similarity
                best_id = node_id
                best_text = existing_text

        if (
            best_id is not None
            and best_similarity >= threshold
        ):

            return {
                "id": best_id,
                "experience": best_text,
                "similarity": round(
                    best_similarity,
                    3
                )
            }

        return None

    # ==========================================
    # LEARN
    # ==========================================

    def learn(
        self,
        experience_id,
        experience_text,
        skill_id,
        confidence=0.6
    ):

        similar = (
            self.find_similar_experience(
                experience_text
            )
        )

        if similar:

            print(
                "Similar experience found:"
            )

            print(
                f"  Existing: "
                f"{similar['experience']}"
            )

            print(
                f"  Similarity: "
                f"{similar['similarity']}"
            )

            print(
                "Updated existing "
                "experience instead of "
                "creating duplicate."
            )

            return similar["id"]

        self.graph.add_experience(
            experience_id,
            experience_text,
            skill_id,
            confidence=confidence,
            validated=False
        )

        print(
            "New experience added:"
        )

        print(
            f"  {experience_text}"
        )

        return experience_id

    # ==========================================
    # FEEDBACK
    # ==========================================

    def process_feedback(
        self,
        experience_id,
        feedback
    ):

        if experience_id not in (
            self.graph.graph.nodes
        ):

            raise ValueError(
                f"Experience not found: "
                f"{experience_id}"
            )

        before = dict(
            self.graph.graph.nodes[
                experience_id
            ]
        )

        success = (
            self.graph.update_experience(
                experience_id,
                feedback
            )
        )

        if not success:

            return None

        after = dict(
            self.graph.graph.nodes[
                experience_id
            ]
        )

        print(
            "\nExperience updated:"
        )

        print(
            f"  Feedback: {feedback}"
        )

        print(
            f"  Confidence: "
            f"{before.get('confidence', 0)}"
            f" → "
            f"{after.get('confidence', 0)}"
        )

        print(
            f"  Validated: "
            f"{before.get('validated', False)}"
            f" → "
            f"{after.get('validated', False)}"
        )

        print(
            f"  Feedback count: "
            f"{after.get('feedback_count', 0)}"
        )

        return after

    # ==========================================
    # GET EXPERIENCE
    # ==========================================

    def get_experience(
        self,
        experience_id
    ):

        if experience_id not in (
            self.graph.graph.nodes
        ):

            return None

        return dict(
            self.graph.graph.nodes[
                experience_id
            ]
        )

    # ==========================================
    # SAVE
    # ==========================================

    def save(
        self,
        path
    ):

        self.graph.save_graph(
            path
        )

    # ==========================================
    # LOAD
    # ==========================================

    def load(
        self,
        path
    ):

        self.graph.load_graph(
            path
        )


# ==========================================
# SELF-EVOLUTION TEST
# ==========================================

if __name__ == "__main__":

    print(
        "\n"
        "=========================================="
    )

    print(
        "EVO-GRAPH SELF-EVOLUTION TEST"
    )

    print(
        "=========================================="
    )

    engine = LearningEngine()

    # ------------------------------------------
    # CREATE SKILL
    # ------------------------------------------

    engine.graph.add_node(
        "skill_python",
        "SKILL",
        "Python Programming"
    )

    # ------------------------------------------
    # CREATE EXPERIENCE
    # ------------------------------------------

    experience_id = engine.learn(
        "experience_001",
        "Check Python error messages before changing code",
        "skill_python",
        confidence=0.6
    )

    # ------------------------------------------
    # INITIAL STATE
    # ------------------------------------------

    print(
        "\n===== INITIAL STATE ====="
    )

    initial = engine.get_experience(
        experience_id
    )

    print(
        f"Confidence: "
        f"{initial['confidence']}"
    )

    print(
        f"Validated: "
        f"{initial['validated']}"
    )

    # ------------------------------------------
    # POSITIVE FEEDBACK
    # ------------------------------------------

    print(
        "\n===== POSITIVE FEEDBACK ====="
    )

    engine.process_feedback(
        experience_id,
        "positive"
    )

    positive = engine.get_experience(
        experience_id
    )

    # ------------------------------------------
    # SECOND POSITIVE FEEDBACK
    # ------------------------------------------

    print(
        "\n===== SECOND POSITIVE FEEDBACK ====="
    )

    engine.process_feedback(
        experience_id,
        "positive"
    )

    positive_again = engine.get_experience(
        experience_id
    )

    # ------------------------------------------
    # NEGATIVE FEEDBACK
    # ------------------------------------------

    print(
        "\n===== NEGATIVE FEEDBACK ====="
    )

    engine.process_feedback(
        experience_id,
        "negative"
    )

    final = engine.get_experience(
        experience_id
    )

    # ------------------------------------------
    # FINAL STATE
    # ------------------------------------------

    print(
        "\n===== FINAL STATE ====="
    )

    print(
        f"Confidence: "
        f"{final['confidence']}"
    )

    print(
        f"Validated: "
        f"{final['validated']}"
    )

    print(
        f"Feedback count: "
        f"{final['feedback_count']}"
    )

    # ------------------------------------------
    # SUMMARY
    # ------------------------------------------

    print(
        "\n=========================================="
    )

    print(
        "SELF-EVOLUTION TEST COMPLETED"
    )

    print(
        "=========================================="
    )