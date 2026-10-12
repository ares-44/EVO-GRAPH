# ============================================================
# EVO-GRAPH
# FAIR RETRIEVAL BENCHMARK
# ============================================================

import sys
import json
import math
from pathlib import Path
from datetime import datetime

# ------------------------------------------------------------
# PROJECT ROOT
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ------------------------------------------------------------
# PROJECT IMPORTS
# ------------------------------------------------------------

from app.text_memory import TextMemory
from app.graph_retrieval import GraphRetrieval


# ============================================================
# PATHS
# ============================================================

BASE_DIR = PROJECT_ROOT / "data" / "experiment"

QUESTIONS_PATH = BASE_DIR / "questions.json"
TEXT_MEMORY_PATH = BASE_DIR / "text_memory_seed.json"
GRAPH_PATH = BASE_DIR / "evo_graph_seed.json"

RESULTS_PATH = BASE_DIR / "fair_experiment_results.jsonl"
EVALUATION_PATH = BASE_DIR / "fair_retrieval_evaluation.json"


# ============================================================
# SEMANTIC MODEL
# Same model for both retrieval systems
# ============================================================

class SemanticEncoder:

    def __init__(self):
        print("\nLoading SentenceTransformer...")

        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("Semantic model loaded.")


    def encode(self, texts):

        return self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        )


    def similarity(self, query, documents):

        if not documents:
            return []

        query_embedding = self.encode([query])[0]

        document_embeddings = self.encode(
            documents
        )

        scores = document_embeddings @ query_embedding

        return [
            float(max(0.0, min(1.0, score)))
            for score in scores
        ]


# ============================================================
# EXPERIMENT RUNNER
# ============================================================

class ExperimentRunner:

    def __init__(self):

        self.check_files()

        self.questions = self.load_questions()

        print(
            f"\nQuestions loaded: {len(self.questions)}"
        )

        # ----------------------------------------------------
        # Existing Text Memory
        # ----------------------------------------------------

        self.text_memory = TextMemory(
            str(TEXT_MEMORY_PATH)
        )

        # ----------------------------------------------------
        # EVO-GRAPH
        # ----------------------------------------------------

        self.graph_memory = GraphRetrieval()

        self.graph_memory.graph.load_graph(
            str(GRAPH_PATH)
        )

        # ----------------------------------------------------
        # SAME SEMANTIC MODEL
        # ----------------------------------------------------

        self.encoder = SemanticEncoder()


    # ========================================================
    # FILE CHECK
    # ========================================================

    def check_files(self):

        required = [
            QUESTIONS_PATH,
            TEXT_MEMORY_PATH,
            GRAPH_PATH
        ]

        for path in required:

            if not path.exists():

                raise FileNotFoundError(
                    f"Required file not found:\n{path}"
                )


    # ========================================================
    # LOAD QUESTIONS
    # ========================================================

    def load_questions(self):

        with open(
            QUESTIONS_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)


    # ========================================================
    # BASELINE A
    # LLM ONLY
    # ========================================================

    def baseline_a(self, question):

        return {
            "approach": "A_LLM_ONLY",
            "question": question,
            "retrieved_items": []
        }


    # ========================================================
    # BASELINE B
    # TEXT MEMORY
    #
    # IMPORTANT:
    # The production TextMemory implementation is NOT changed.
    #
    # For the FAIR benchmark, we apply the SAME MiniLM model
    # used by EVO-GRAPH to the Text Memory questions.
    # ========================================================

    def baseline_b(self, question):

        memories = self.text_memory.memories

        if not memories:

            return {
                "approach": "B_TEXT_MEMORY",
                "question": question,
                "retrieved_items": []
            }

        documents = [
            memory.get("question", "")
            for memory in memories
        ]

        scores = self.encoder.similarity(
            question,
            documents
        )

        results = []

        for memory, score in zip(
            memories,
            scores
        ):

            results.append(
                {
                    "id": memory["id"],
                    "question": memory["question"],
                    "answer": memory["answer"],
                    "semantic_score": round(
                        score,
                        4
                    ),
                    "score": round(
                        score,
                        4
                    )
                }
            )

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return {
            "approach": "B_TEXT_MEMORY",
            "question": question,
            "retrieved_items": results[:3]
        }


    # ========================================================
    # BASELINE C
    # EVO-GRAPH
    #
    # Uses the SAME MiniLM semantic foundation internally,
    # plus graph metadata.
    # ========================================================

    def baseline_c(self, question):

        results = self.graph_memory.retrieve(
            question,
            limit=3
        )

        return {
            "approach": "C_EVO_GRAPH",
            "question": question,
            "retrieved_items": results
        }


    # ========================================================
    # GET ITEM ID
    # ========================================================

    def get_item_id(self, item):

        return item.get("id")


    # ========================================================
    # GOLD ID
    # ========================================================

    def get_gold_id(
        self,
        question_id,
        approach
    ):

        number = question_id.replace(
            "Q",
            ""
        )

        if approach == "B_TEXT_MEMORY":

            return f"seed_{int(number):03d}"

        if approach == "C_EVO_GRAPH":

            return f"seed_exp_{int(number):02d}"

        return None


    # ========================================================
    # PRECISION @ K
    #
    # STANDARD FIXED-K FORM:
    #
    # relevant items in top K / K
    #
    # NOT / number of returned items.
    # ========================================================

    def precision_at_k(
        self,
        retrieved_items,
        gold_id,
        k
    ):

        if k <= 0 or gold_id is None:

            return 0.0

        retrieved = retrieved_items[:k]

        relevant_count = sum(
            1
            for item in retrieved
            if self.get_item_id(item) == gold_id
        )

        return relevant_count / k


    # ========================================================
    # RECALL @ K
    # ========================================================

    def recall_at_k(
        self,
        retrieved_items,
        gold_id,
        k
    ):

        if gold_id is None:

            return 0.0

        retrieved = retrieved_items[:k]

        for item in retrieved:

            if self.get_item_id(item) == gold_id:

                return 1.0

        return 0.0


    # ========================================================
    # MRR
    #
    # Reciprocal rank of the first relevant result.
    # ========================================================

    def reciprocal_rank(
        self,
        retrieved_items,
        gold_id
    ):

        if gold_id is None:

            return 0.0

        for rank, item in enumerate(
            retrieved_items,
            start=1
        ):

            if self.get_item_id(item) == gold_id:

                return 1.0 / rank

        return 0.0


    # ========================================================
    # nDCG @ 3
    #
    # Single known relevant item:
    #
    # rank 1 = 1.0
    # rank 2 = 1/log2(3)
    # rank 3 = 1/log2(4)
    # not retrieved = 0
    # ========================================================

    def ndcg_at_3(
        self,
        retrieved_items,
        gold_id
    ):

        if gold_id is None:

            return 0.0

        for rank, item in enumerate(
            retrieved_items[:3],
            start=1
        ):

            if self.get_item_id(item) == gold_id:

                dcg = 1.0 / math.log2(
                    rank + 1
                )

                ideal_dcg = 1.0

                return dcg / ideal_dcg

        return 0.0


    # ========================================================
    # RELEVANT RANK
    # ========================================================

    def relevant_rank(
        self,
        retrieved_items,
        gold_id
    ):

        if gold_id is None:

            return None

        for rank, item in enumerate(
            retrieved_items,
            start=1
        ):

            if self.get_item_id(item) == gold_id:

                return rank

        return None


    # ========================================================
    # EVALUATE
    # ========================================================

    def evaluate_approach(
        self,
        question_id,
        approach,
        retrieved_items
    ):

        gold_id = self.get_gold_id(
            question_id,
            approach
        )

        return {
            "gold_id": gold_id,

            "precision_at_1": round(
                self.precision_at_k(
                    retrieved_items,
                    gold_id,
                    1
                ),
                4
            ),

            "precision_at_3": round(
                self.precision_at_k(
                    retrieved_items,
                    gold_id,
                    3
                ),
                4
            ),

            "recall_at_3": round(
                self.recall_at_k(
                    retrieved_items,
                    gold_id,
                    3
                ),
                4
            ),

            "mrr": round(
                self.reciprocal_rank(
                    retrieved_items,
                    gold_id
                ),
                4
            ),

            "ndcg_at_3": round(
                self.ndcg_at_3(
                    retrieved_items,
                    gold_id
                ),
                4
            ),

            "relevant_rank":
                self.relevant_rank(
                    retrieved_items,
                    gold_id
                )
        }


    # ========================================================
    # COMPARE ONE QUESTION
    # ========================================================

    def compare(self, item):

        question_id = item["id"]
        question = item["question"]

        results = [

            self.baseline_a(
                question
            ),

            self.baseline_b(
                question
            ),

            self.baseline_c(
                question
            )
        ]

        for result in results:

            result["evaluation"] = (
                self.evaluate_approach(
                    question_id,
                    result["approach"],
                    result["retrieved_items"]
                )
            )

        return results


    # ========================================================
    # RUN DATASET
    # ========================================================

    def run_dataset(self):

        all_results = []

        print(
            "\n=================================================="
        )

        print(
            "EVO-GRAPH FAIR RETRIEVAL BENCHMARK"
        )

        print(
            "=================================================="
        )

        print(
            f"Questions: {len(self.questions)}"
        )

        print(
            "Text Memory: SAME MiniLM semantic encoder"
        )

        print(
            "EVO-GRAPH: MiniLM + graph metadata"
        )

        print(
            "Metrics: P@1, P@3, Recall@3, MRR, nDCG@3"
        )

        print(
            "=================================================="
        )


        for item in self.questions:

            question_id = item["id"]
            category = item["category"]
            question = item["question"]

            results = self.compare(
                item
            )

            record = {

                "timestamp":
                    datetime.now().isoformat(),

                "question_id":
                    question_id,

                "category":
                    category,

                "question":
                    question,

                "reference_points":
                    item["reference_points"],

                "results":
                    results
            }

            all_results.append(
                record
            )


            # ------------------------------------------------
            # DISPLAY QUESTION
            # ------------------------------------------------

            print(
                f"\n[{question_id}] "
                f"{category}"
            )

            print(
                f"Question: {question}"
            )


            # ------------------------------------------------
            # DISPLAY RANKING
            # ------------------------------------------------

            for result in results:

                approach = result["approach"]

                retrieved = result[
                    "retrieved_items"
                ]

                evaluation = result[
                    "evaluation"
                ]

                print(
                    f"\n  {approach}"
                )

                print(
                    f"    Gold: "
                    f"{evaluation['gold_id']}"
                )

                print(
                    f"    P@1: "
                    f"{evaluation['precision_at_1']}"
                )

                print(
                    f"    P@3: "
                    f"{evaluation['precision_at_3']}"
                )

                print(
                    f"    Recall@3: "
                    f"{evaluation['recall_at_3']}"
                )

                print(
                    f"    MRR: "
                    f"{evaluation['mrr']}"
                )

                print(
                    f"    nDCG@3: "
                    f"{evaluation['ndcg_at_3']}"
                )

                print(
                    f"    Relevant rank: "
                    f"{evaluation['relevant_rank']}"
                )


                if retrieved:

                    print(
                        "    Ranking:"
                    )

                    for rank, retrieved_item in enumerate(
                        retrieved,
                        start=1
                    ):

                        item_id = (
                            retrieved_item.get("id")
                        )

                        score = (
                            retrieved_item.get(
                                "score",
                                0.0
                            )
                        )

                        if approach == "B_TEXT_MEMORY":

                            print(
                                f"      {rank}. "
                                f"{item_id} "
                                f"(semantic={score:.4f})"
                            )

                        elif approach == "C_EVO_GRAPH":

                            semantic = (
                                retrieved_item.get(
                                    "semantic_score",
                                    0.0
                                )
                            )

                            graph = (
                                retrieved_item.get(
                                    "graph_score",
                                    0.0
                                )
                            )

                            print(
                                f"      {rank}. "
                                f"{item_id} "
                                f"(semantic={semantic:.4f}, "
                                f"graph={graph:.4f}, "
                                f"final={score:.4f})"
                            )

                        else:

                            print(
                                f"      {rank}. "
                                f"{item_id}"
                            )


        # ====================================================
        # SAVE RAW RESULTS
        # ====================================================

        self.save_results(
            all_results
        )


        # ====================================================
        # SUMMARY
        # ====================================================

        summary = self.calculate_summary(
            all_results
        )

        self.save_evaluation(
            summary
        )

        self.display_summary(
            summary
        )

        return all_results


    # ========================================================
    # SUMMARY
    # ========================================================

    def calculate_summary(
        self,
        records
    ):

        approaches = [
            "A_LLM_ONLY",
            "B_TEXT_MEMORY",
            "C_EVO_GRAPH"
        ]

        summary = {}


        for approach in approaches:

            p1 = []
            p3 = []
            recall3 = []
            mrr = []
            ndcg3 = []
            ranks = []


            for record in records:

                for result in record["results"]:

                    if result["approach"] != approach:

                        continue

                    evaluation = result[
                        "evaluation"
                    ]

                    p1.append(
                        evaluation[
                            "precision_at_1"
                        ]
                    )

                    p3.append(
                        evaluation[
                            "precision_at_3"
                        ]
                    )

                    recall3.append(
                        evaluation[
                            "recall_at_3"
                        ]
                    )

                    mrr.append(
                        evaluation[
                            "mrr"
                        ]
                    )

                    ndcg3.append(
                        evaluation[
                            "ndcg_at_3"
                        ]
                    )

                    rank = evaluation[
                        "relevant_rank"
                    ]

                    if rank is not None:

                        ranks.append(
                            rank
                        )


            count = len(p1)


            if count == 0:

                summary[approach] = {
                    "questions": 0,
                    "mean_precision_at_1": 0.0,
                    "mean_precision_at_3": 0.0,
                    "mean_recall_at_3": 0.0,
                    "mean_mrr": 0.0,
                    "mean_ndcg_at_3": 0.0,
                    "retrieval_success_rate": 0.0,
                    "mean_relevant_rank": None
                }

                continue


            summary[approach] = {

                "questions":
                    count,

                "mean_precision_at_1":
                    round(
                        sum(p1) / count,
                        4
                    ),

                "mean_precision_at_3":
                    round(
                        sum(p3) / count,
                        4
                    ),

                "mean_recall_at_3":
                    round(
                        sum(recall3) / count,
                        4
                    ),

                "mean_mrr":
                    round(
                        sum(mrr) / count,
                        4
                    ),

                "mean_ndcg_at_3":
                    round(
                        sum(ndcg3) / count,
                        4
                    ),

                "retrieval_success_rate":
                    round(
                        sum(recall3) / count,
                        4
                    ),

                "mean_relevant_rank":
                    round(
                        sum(ranks) / len(ranks),
                        4
                    )
                    if ranks
                    else None
            }


        return summary


    # ========================================================
    # SAVE RESULTS
    # ========================================================

    def save_results(
        self,
        records
    ):

        RESULTS_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            RESULTS_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            for record in records:

                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False
                    )
                    + "\n"
                )

        print(
            f"\nRaw results saved to:"
            f"\n{RESULTS_PATH}"
        )


    # ========================================================
    # SAVE SUMMARY
    # ========================================================

    def save_evaluation(
        self,
        summary
    ):

        output = {

            "generated_at":
                datetime.now().isoformat(),

            "evaluation_type":
                "fair_semantic_graph_retrieval",

            "semantic_model":
                "sentence-transformers/all-MiniLM-L6-v2",

            "metrics": [

                "precision_at_1",
                "precision_at_3",
                "recall_at_3",
                "mrr",
                "ndcg_at_3",
                "retrieval_success_rate",
                "mean_relevant_rank"
            ],

            "summary":
                summary
        }


        with open(
            EVALUATION_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output,
                file,
                indent=2
            )


        print(
            f"\nEvaluation saved to:"
            f"\n{EVALUATION_PATH}"
        )


    # ========================================================
    # DISPLAY SUMMARY
    # ========================================================

    def display_summary(
        self,
        summary
    ):

        print(
            "\n\n=================================================="
        )

        print(
            "FINAL FAIR BENCHMARK"
        )

        print(
            "=================================================="
        )


        for approach, metrics in summary.items():

            print(
                f"\n{approach}"
            )

            print(
                f"  P@1: "
                f"{metrics['mean_precision_at_1']}"
            )

            print(
                f"  P@3: "
                f"{metrics['mean_precision_at_3']}"
            )

            print(
                f"  Recall@3: "
                f"{metrics['mean_recall_at_3']}"
            )

            print(
                f"  MRR: "
                f"{metrics['mean_mrr']}"
            )

            print(
                f"  nDCG@3: "
                f"{metrics['mean_ndcg_at_3']}"
            )

            print(
                f"  Success: "
                f"{metrics['retrieval_success_rate']}"
            )

            print(
                f"  Mean rank: "
                f"{metrics['mean_relevant_rank']}"
            )


        print(
            "\n=================================================="
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    runner = ExperimentRunner()

    runner.run_dataset()