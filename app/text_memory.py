import json
import re
from pathlib import Path


class TextMemory:

    def __init__(
        self,
        memory_path="data/text_memory.json"
    ):
        self.memory_path = Path(
            memory_path
        )

        self.memories = []

        self.load()

    # ==========================================
    # TEXT NORMALIZATION
    # ==========================================

    def normalize_text(self, text):

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            "",
            text
        )

        stop_words = {
            "the",
            "a",
            "an",
            "to",
            "of",
            "in",
            "on",
            "for",
            "and",
            "before",
            "after",
            "when",
            "is",
            "are",
            "with",
            "how",
            "should",
            "can",
            "do",
            "i",
            "my"
        }

        words = [
            word
            for word in text.split()
            if word not in stop_words
        ]

        return set(words)

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

        intersection = words1.intersection(
            words2
        )

        union = words1.union(
            words2
        )

        return (
            len(intersection)
            / len(union)
        )

    # ==========================================
    # ADD MEMORY
    # ==========================================

    def add_memory(
        self,
        memory_id,
        question,
        answer
    ):

        memory = {
            "id": memory_id,
            "question": question,
            "answer": answer
        }

        self.memories.append(
            memory
        )

        self.save()

        print(
            "\nMemory added:"
        )

        print(
            f"  ID: {memory_id}"
        )

        print(
            f"  Question: {question}"
        )

    # ==========================================
    # SEARCH MEMORY
    # ==========================================

    def search(
        self,
        query,
        limit=3,
        threshold=0.15
    ):

        results = []

        for memory in self.memories:

            similarity = self.calculate_similarity(
                query,
                memory["question"]
            )

            if similarity < threshold:
                continue

            results.append(
                {
                    "id": memory["id"],
                    "question": memory["question"],
                    "answer": memory["answer"],
                    "score": round(
                        similarity,
                        3
                    )
                }
            )

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:limit]

    # ==========================================
    # BUILD CONTEXT
    # ==========================================

    def build_context(
        self,
        query,
        limit=3
    ):

        results = self.search(
            query,
            limit=limit
        )

        if not results:

            return (
                "No relevant previous "
                "memories found."
            )

        context = []

        for item in results:

            context.append(
                f"Previous Question: "
                f"{item['question']}"
            )

            context.append(
                f"Previous Answer: "
                f"{item['answer']}"
            )

            context.append(
                f"Similarity: "
                f"{item['score']:.3f}"
            )

            context.append("")

        return "\n".join(
            context
        )

    # ==========================================
    # SAVE
    # ==========================================

    def save(self):

        self.memory_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            self.memory_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.memories,
                file,
                indent=2,
                ensure_ascii=False
            )

    # ==========================================
    # LOAD
    # ==========================================

    def load(self):

        if not self.memory_path.exists():

            self.memories = []

            return False

        with open(
            self.memory_path,
            "r",
            encoding="utf-8"
        ) as file:

            self.memories = json.load(
                file
            )

        return True

    # ==========================================
    # MEMORY COUNT
    # ==========================================

    def count(self):

        return len(
            self.memories
        )

    # ==========================================
    # CLEAR MEMORY
    # ==========================================

    def clear(self):

        self.memories = []

        self.save()

        print(
            "\nText memory cleared."
        )


# ==========================================
# OFFLINE TEST
# ==========================================

if __name__ == "__main__":

    print(
        "\n===== TEXT MEMORY TEST ====="
    )

    memory = TextMemory(
        "data/text_memory_test.json"
    )

    # --------------------------------------
    # CLEAR OLD TEST DATA
    # --------------------------------------

    memory.clear()

    # --------------------------------------
    # ADD MEMORIES
    # --------------------------------------

    memory.add_memory(
        "memory_001",
        "How should I debug a Python error?",
        "First read the error message carefully, "
        "then inspect the relevant line and variables."
    )

    memory.add_memory(
        "memory_002",
        "How can I debug Python variables?",
        "Use print statements or a debugger "
        "to inspect variable values."
    )

    memory.add_memory(
        "memory_003",
        "What is a Python list?",
        "A Python list is an ordered, mutable collection."
    )

    # --------------------------------------
    # MEMORY COUNT
    # --------------------------------------

    print(
        "\n===== MEMORY COUNT ====="
    )

    print(
        f"Total memories: "
        f"{memory.count()}"
    )

    # --------------------------------------
    # SEARCH
    # --------------------------------------

    question = (
        "How do I debug a Python problem?"
    )

    print(
        "\n===== MEMORY SEARCH ====="
    )

    print(
        f"Query: {question}"
    )

    results = memory.search(
        question,
        limit=3
    )

    for result in results:

        print(
            f"\nMemory ID: "
            f"{result['id']}"
        )

        print(
            f"Question: "
            f"{result['question']}"
        )

        print(
            f"Score: "
            f"{result['score']:.3f}"
        )

    # --------------------------------------
    # CONTEXT
    # --------------------------------------

    print(
        "\n===== GENERATED CONTEXT ====="
    )

    print(
        memory.build_context(
            question
        )
    )

    # --------------------------------------
    # PERSISTENCE TEST
    # --------------------------------------

    print(
        "\n===== PERSISTENCE TEST ====="
    )

    new_memory = TextMemory(
        "data/text_memory_test.json"
    )

    print(
        f"Loaded memories: "
        f"{new_memory.count()}"
    )

    print(
        "\nText memory test completed."
    )