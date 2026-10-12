import json
import math
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "data" / "experiment"

QUESTIONS = EXP / "questions_250_targeted.json"
TEXT_MEMORY = EXP / "text_memory_seed.json"
GRAPH = EXP / "evo_graph_seed.json"

RESULTS = EXP / "benchmark_250_results.jsonl"
SUMMARY = EXP / "benchmark_250_evaluation.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.text_memory import TextMemory
from app.graph_retrieval import GraphRetrieval


MODEL = "all-MiniLM-L6-v2"
TOP_K = 3


def canonical(x):
    if x is None:
        return None

    x = str(x)

    if x.startswith("seed_exp_"):
        try:
            return f"seed_{int(x.split('_')[-1]):03d}"
        except:
            return x

    if x.startswith("seed_"):
        try:
            return f"seed_{int(x.split('_')[-1]):03d}"
        except:
            return x

    return x


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def relevance(result, gold):
    return int(gold.get(canonical(result.get("id")), 0))


def metrics(results, gold):

    top3 = results[:3]

    p1 = (
        1.0
        if top3 and relevance(top3[0], gold) > 0
        else 0.0
    )

    p3 = sum(
        relevance(x, gold) > 0
        for x in top3
    ) / 3.0

    relevant_ids = {
        canonical(k)
        for k, v in gold.items()
        if int(v) > 0
    }

    retrieved_ids = {
        canonical(x.get("id"))
        for x in top3
    }

    recall = (
        len(relevant_ids & retrieved_ids)
        / len(relevant_ids)
        if relevant_ids else 0.0
    )

    first_rank = None

    for rank, x in enumerate(top3, 1):
        if relevance(x, gold) > 0:
            first_rank = rank
            break

    mrr = 1.0 / first_rank if first_rank else 0.0

    actual = 0.0

    for rank, x in enumerate(top3, 1):
        rel = relevance(x, gold)
        if rel:
            actual += ((2 ** rel) - 1) / math.log2(rank + 1)

    ideal_rels = sorted(
        [int(v) for v in gold.values() if int(v) > 0],
        reverse=True
    )[:3]

    ideal = sum(
        ((2 ** rel) - 1) / math.log2(rank + 1)
        for rank, rel in enumerate(ideal_rels, 1)
    )

    ndcg = actual / ideal if ideal else 0.0

    return {
        "p_at_1": p1,
        "p_at_3": p3,
        "recall_at_3": recall,
        "mrr": mrr,
        "ndcg_at_3": ndcg,
        "first_relevant_rank": first_rank,
        "retrieval_success": 1.0 if first_rank else 0.0
    }


class Benchmark:

    def __init__(self):

        print("=" * 70)
        print("EVO-GRAPH — 250 QUESTION FAIR BENCHMARK")
        print("=" * 70)

        for f in [QUESTIONS, TEXT_MEMORY, GRAPH]:
            if not f.exists():
                raise FileNotFoundError(f"Missing: {f}")

        with open(QUESTIONS, encoding="utf-8") as f:
            data = json.load(f)

        self.questions = (
            data["questions"]
            if isinstance(data, dict)
            else data
        )

        print(f"Questions: {len(self.questions)}")

        print("\nLoading MiniLM...")
        self.encoder = SentenceTransformer(MODEL)
        print("MiniLM loaded.")

        print("\nLoading Text Memory...")
        self.text = TextMemory(TEXT_MEMORY)


        print("Loading EVO-GRAPH...")
        self.graph = GraphRetrieval()

        try:
            if hasattr(self.graph, "load"):
                self.graph.load(GRAPH)
        except Exception:
            pass

        try:
            if hasattr(self.graph, "graph") and hasattr(
                self.graph.graph, "load_graph"
            ):
                self.graph.graph.load_graph(GRAPH)
        except Exception:
            pass

    def text_items(self):

        memories = getattr(
            self.text,
            "memories",
            getattr(self.text, "memory", [])
        )

        items = []

        if isinstance(memories, dict):
            iterable = memories.values()
        else:
            iterable = memories

        for i, item in enumerate(iterable):

            if isinstance(item, dict):

                item_id = (
                    item.get("id")
                    or item.get("memory_id")
                    or item.get("name")
                    or f"seed_{i+1:03d}"
                )

                text = (
                    item.get("question")
                    or item.get("source_question")
                    or item.get("text")
                    or item.get("content")
                    or item.get("experience")
                    or ""
                )

            else:
                item_id = f"seed_{i+1:03d}"
                text = str(item)

            if text:
                items.append(
                    {
                        "id": str(item_id),
                        "text": str(text)
                    }
                )

        return items

    def text_retrieve(self, question):

        items = self.text_items()

        if not items:
            return []

        q = self.encoder.encode(
            [question],
            normalize_embeddings=True
        )[0]

        docs = self.encoder.encode(
            [x["text"] for x in items],
            normalize_embeddings=True
        )

        scores = np.dot(docs, q)

        ranked = sorted(
            zip(items, scores),
            key=lambda x: float(x[1]),
            reverse=True
        )

        return [
            {
                "id": x["id"],
                "text": x["text"],
                "semantic_score": float(score)
            }
            for x, score in ranked[:TOP_K]
        ]

    def graph_retrieve(self, question):

        raw = self.graph.retrieve(
            question,
            limit=TOP_K
        )

        output = []

        for x in raw or []:

            if isinstance(x, dict):

                item_id = (
                    x.get("id")
                    or x.get("experience_id")
                    or x.get("name")
                )

                text = (
                    x.get("text")
                    or x.get("question")
                    or x.get("source_question")
                    or x.get("experience")
                    or ""
                )

                output.append({
                    "id": str(item_id),
                    "text": str(text),
                    "semantic_score": float(
                        x.get(
                            "semantic_score",
                            x.get("similarity", 0.0)
                        ) or 0
                    ),
                    "graph_score": float(
                        x.get(
                            "graph_score",
                            x.get("score", 0.0)
                        ) or 0
                    ),
                    "final_score": float(
                        x.get(
                            "final_score",
                            x.get("score", 0.0)
                        ) or 0
                    )
                })

        return output[:TOP_K]

    def run(self):

        all_records = []

        print("\nStarting benchmark...\n")

        with open(
            RESULTS,
            "w",
            encoding="utf-8"
        ) as out:

            for number, item in enumerate(
                self.questions,
                1
            ):

                qid = item.get(
                    "id",
                    f"Q{number:03d}"
                )

                question = item.get(
                    "question",
                    item.get("query", "")
                )

                category = item.get(
                    "category",
                    item.get("type", "unknown")
                )

                gold = {
                    canonical(k): int(v)
                    for k, v in item.get(
                        "relevance", {}
                    ).items()
                }

                text_results = self.text_retrieve(
                    question
                )

                graph_results = self.graph_retrieve(
                    question
                )

                record = {
                    "question_id": qid,
                    "question": question,
                    "category": category,
                    "relevance": gold,
                    "retrieval": {
                        "llm_only": [],
                        "text_memory": text_results,
                        "evo_graph": graph_results
                    },
                    "evaluation": {
                        "llm_only": metrics([], gold),
                        "text_memory": metrics(
                            text_results,
                            gold
                        ),
                        "evo_graph": metrics(
                            graph_results,
                            gold
                        )
                    }
                }

                out.write(
                    json.dumps(
                        record,
                        ensure_ascii=False
                    ) + "\n"
                )

                all_records.append(record)

                print(
                    f"[{number:03d}/{len(self.questions):03d}] "
                    f"{question}"
                )

        self.summary(all_records)

    def summary(self, records):

        approaches = [
            "llm_only",
            "text_memory",
            "evo_graph"
        ]

        summary = {
            "metadata": {
                "dataset": QUESTIONS.name,
                "questions": len(records),
                "model": MODEL,
                "top_k": TOP_K,
                "created_at": datetime.now().isoformat()
            },
            "overall": {},
            "by_category": {}
        }

        for approach in approaches:

            rows = [
                r["evaluation"][approach]
                for r in records
            ]

            ranks = [
                r["first_relevant_rank"]
                for r in rows
                if r["first_relevant_rank"] is not None
            ]

            summary["overall"][approach] = {
                "p_at_1": mean(
                    x["p_at_1"] for x in rows
                ),
                "p_at_3": mean(
                    x["p_at_3"] for x in rows
                ),
                "recall_at_3": mean(
                    x["recall_at_3"] for x in rows
                ),
                "mrr": mean(
                    x["mrr"] for x in rows
                ),
                "ndcg_at_3": mean(
                    x["ndcg_at_3"] for x in rows
                ),
                "mean_relevant_rank": (
                    mean(ranks)
                    if ranks else None
                ),
                "retrieval_success_rate": mean(
                    x["retrieval_success"]
                    for x in rows
                )
            }

        categories = sorted({
            r["category"]
            for r in records
        })

        for category in categories:

            summary["by_category"][category] = {}

            subset = [
                r for r in records
                if r["category"] == category
            ]

            for approach in approaches:

                rows = [
                    r["evaluation"][approach]
                    for r in subset
                ]

                summary["by_category"][
                    category
                ][approach] = {
                    "count": len(rows),
                    "p_at_1": mean(
                        x["p_at_1"] for x in rows
                    ),
                    "p_at_3": mean(
                        x["p_at_3"] for x in rows
                    ),
                    "recall_at_3": mean(
                        x["recall_at_3"] for x in rows
                    ),
                    "mrr": mean(
                        x["mrr"] for x in rows
                    ),
                    "ndcg_at_3": mean(
                        x["ndcg_at_3"] for x in rows
                    ),
                    "retrieval_success_rate": mean(
                        x["retrieval_success"]
                        for x in rows
                    )
                }

        with open(
            SUMMARY,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                summary,
                f,
                indent=2
            )

        print("\n")
        print("=" * 90)
        print("FINAL 250-QUESTION RESULTS")
        print("=" * 90)

        print(
            f"{'Approach':<18}"
            f"{'P@1':>10}"
            f"{'P@3':>10}"
            f"{'Recall@3':>12}"
            f"{'MRR':>10}"
            f"{'nDCG@3':>12}"
            f"{'Success':>12}"
        )

        print("-" * 90)

        for approach, x in summary["overall"].items():

            print(
                f"{approach:<18}"
                f"{x['p_at_1']*100:>9.2f}%"
                f"{x['p_at_3']*100:>9.2f}%"
                f"{x['recall_at_3']*100:>11.2f}%"
                f"{x['mrr']:>10.3f}"
                f"{x['ndcg_at_3']:>12.3f}"
                f"{x['retrieval_success_rate']*100:>11.2f}%"
            )

        print("=" * 90)
        print(f"\nResults saved to:\n{RESULTS}")
        print(f"Summary saved to:\n{SUMMARY}")


if __name__ == "__main__":
    Benchmark().run()
