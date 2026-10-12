import json
import os
import re
import uuid
from pathlib import Path

from app.llm_adapter import LLMAdapter
from graph.graph_manager import EvoGraph


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

GRAPH_PATH = (
    PROJECT_ROOT /
    "data" /
    "evo_graph.json"
)

PRIMARY_PROVIDER = os.getenv(
    "EVO_LLM_PROVIDER",
    "ollama"
)

OLLAMA_MODEL = "qwen2.5:3b"


# ============================================================
# LLM
# ============================================================

def create_llm():

    return LLMAdapter(
        provider=PRIMARY_PROVIDER,
        ollama_model=OLLAMA_MODEL
    )


def generate_with_backup(
    llm,
    prompt
):

    try:

        response = llm.generate(
            prompt
        )

        if response and response.strip():
            return response.strip()

    except Exception as e:

        print(
            f"\n⚠️ Primary LLM failed: {e}"
        )

        print(
            "🔄 Trying Gemini backup..."
        )

    # Gemini backup

    try:

        backup_llm = LLMAdapter(
            provider="gemini",
            ollama_model=OLLAMA_MODEL
        )

        response = backup_llm.generate(
            prompt
        )

        if response and response.strip():
            return response.strip()

    except Exception as e:

        print(
            f"❌ Gemini backup failed: {e}"
        )

    return (
        "I could not generate a response right now."
    )


# ============================================================
# GRAPH INITIALIZATION
# ============================================================

def initialize_graph():

    evo_graph = EvoGraph()

    if GRAPH_PATH.exists():

        try:

            evo_graph.load_graph(
                str(GRAPH_PATH)
            )

            print(
                "✅ Persistent EVO-GRAPH loaded."
            )

        except Exception as e:

            print(
                f"⚠️ Could not load graph: {e}"
            )

            print(
                "Creating a fresh graph..."
            )

    # Python skill

    if "skill_python" not in evo_graph.graph:

        evo_graph.add_node(
            "skill_python",
            "SKILL",
            "Python Programming"
        )

    # Debugging topic

    if "topic_debugging" not in evo_graph.graph:

        evo_graph.add_node(
            "topic_debugging",
            "TOPIC",
            "Python Debugging"
        )

    # Topic → Skill

    if not evo_graph.graph.has_edge(
        "topic_debugging",
        "skill_python"
    ):

        evo_graph.add_relationship(
            "topic_debugging",
            "skill_python",
            "RELATED_TO"
        )

    return evo_graph


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_learning(
    evo_graph,
    question
):

    try:

        return evo_graph.search_experiences(
            question,
            limit=3,
            validated_only=False,
            min_score=0.10
        )

    except Exception as e:

        print(
            f"⚠️ Graph retrieval failed: {e}"
        )

        return []


def build_learning_context(
    results
):

    if not results:

        return (
            "No previous learned experience "
            "is relevant."
        )

    context = []

    for i, item in enumerate(
        results,
        start=1
    ):

        experience = item.get(
            "experience",
            item.get(
                "description",
                ""
            )
        )

        semantic_score = item.get(
            "semantic_score",
            0.0
        )

        final_score = item.get(
            "score",
            item.get(
                "final_score",
                0.0
            )
        )

        confidence = item.get(
            "confidence",
            0.0
        )

        validated = item.get(
            "validated",
            False
        )

        feedback_count = item.get(
            "feedback_count",
            0
        )

        context.append(
            f"""
Experience {i}:
{experience}

Semantic relevance: {semantic_score:.4f}
Final graph score: {final_score:.4f}
Confidence: {confidence:.2f}
Validated: {validated}
Feedback count: {feedback_count}
""".strip()
        )

    return "\n\n".join(
        context
    )


# ============================================================
# ANSWER GENERATION
# ============================================================

def generate_answer(
    llm,
    question,
    learned_context
):

    prompt = f"""
You are EVO-GRAPH, a self-evolving AI learning agent.

Answer the user's question accurately.

Use the learned experiences below only when they
are genuinely relevant.

IMPORTANT:

1. Answer the actual question.
2. Do not blindly copy learned experiences.
3. Do not use irrelevant experiences.
4. If an experience conflicts with correct reasoning,
   prefer correct reasoning.
5. Give a clear and technically correct answer.
6. Do not mention graph scores unless asked.
7. Do not claim that you learned something unless
   feedback has actually been processed.

LEARNED EXPERIENCES
-------------------
{learned_context}
-------------------

USER QUESTION
-------------
{question}

Provide the best answer.
"""

    return generate_with_backup(
        llm,
        prompt
    )


# ============================================================
# FEEDBACK REFLECTION
# ============================================================

def analyze_feedback(
    llm,
    question,
    answer,
    feedback
):

    prompt = f"""
You are the reflection module of EVO-GRAPH.

Analyze the user's feedback about the AI answer.

USER QUESTION:
{question}

AI ANSWER:
{answer}

USER FEEDBACK:
{feedback}

Return ONLY valid JSON.

Use exactly:

{{
    "correction": "...",
    "learning_rule": "...",
    "reason": "...",
    "applies_to": "..."
}}

Rules:

correction:
State what should be corrected or improved.
If the answer was correct, state what should be preserved.

learning_rule:
Write a reusable behavioral rule for future answers.
It must be an actual improvement rule.

reason:
Explain why the change is useful.

applies_to:
Describe future questions where this experience applies.

Do NOT use markdown.
Do NOT use ```json.
Return JSON only.
"""

    raw_response = generate_with_backup(
        llm,
        prompt
    )

    cleaned = raw_response.strip()

    # Remove markdown fences if Qwen adds them

    cleaned = re.sub(
        r"^```json\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r"^```\s*",
        "",
        cleaned
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned
    )

    try:

        return json.loads(
            cleaned
        )

    except json.JSONDecodeError:

        pass

    # Extract JSON object

    match = re.search(
        r"\{.*\}",
        cleaned,
        flags=re.DOTALL
    )

    if match:

        try:

            return json.loads(
                match.group(0)
            )

        except json.JSONDecodeError:

            pass

    # Safe fallback

    return {
        "correction": cleaned,
        "learning_rule": (
            "Use explicit user feedback to "
            "improve future answers."
        ),
        "reason": (
            "The user provided feedback."
        ),
        "applies_to": (
            "Similar future questions."
        )
    }


# ============================================================
# EXPERIENCE CREATION
# ============================================================

def build_experience(
    question,
    reflection
):

    correction = reflection.get(
        "correction",
        ""
    ).strip()

    learning_rule = reflection.get(
        "learning_rule",
        ""
    ).strip()

    reason = reflection.get(
        "reason",
        ""
    ).strip()

    applies_to = reflection.get(
        "applies_to",
        ""
    ).strip()

    return (
        f"Question context: {question}\n"
        f"Correction: {correction}\n"
        f"Learning rule: {learning_rule}\n"
        f"Reason: {reason}\n"
        f"Applies to: {applies_to}"
    )


# ============================================================
# SAVE GRAPH
# ============================================================

def save_graph(
    evo_graph
):

    GRAPH_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    evo_graph.save_graph(
        str(GRAPH_PATH)
    )

    print(
        f"💾 Graph saved: {GRAPH_PATH}"
    )


# ============================================================
# ADD LEARNED EXPERIENCE
# ============================================================

def add_learned_experience(
    evo_graph,
    question,
    reflection
):

    experience_text = build_experience(
        question,
        reflection
    )

    experience_id = (
        f"learned_{uuid.uuid4().hex[:8]}"
    )

    evo_graph.add_experience(
        experience_id,
        experience_text,
        confidence=0.60,
        validated=False
    )

    # Connect to Python skill

    if "skill_python" in evo_graph.graph:

        evo_graph.add_relationship(
            experience_id,
            "skill_python",
            "IMPROVES"
        )

    # Connect to debugging topic

    if "topic_debugging" in evo_graph.graph:

        evo_graph.add_relationship(
            experience_id,
            "topic_debugging",
            "RELATED_TO"
        )

    print(
        f"🧠 New experience learned: "
        f"{experience_id}"
    )

    return experience_id


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n" + "=" * 60
    )

    print(
        "                 EVO-GRAPH"
    )

    print(
        "       Self-Evolving AI Learning Agent"
    )

    print(
        "=" * 60
    )

    print(
        f"\nPrimary LLM: {PRIMARY_PROVIDER}"
    )

    print(
        f"Ollama model: {OLLAMA_MODEL}"
    )

    print(
        f"Graph: {GRAPH_PATH}"
    )

    # --------------------------------------------------------
    # Initialize
    # --------------------------------------------------------

    evo_graph = initialize_graph()

    llm = create_llm()

    print(
        "\n✅ EVO-GRAPH ready."
    )

    # --------------------------------------------------------
    # Interactive loop
    # --------------------------------------------------------

    while True:

        print(
            "\n" + "-" * 60
        )

        question = input(
            "\nChief, ask your question "
            "(type 'exit' to quit):\n> "
        ).strip()

        if not question:
            continue

        if question.lower() in {
            "exit",
            "quit",
            "q"
        }:

            save_graph(
                evo_graph
            )

            print(
                "\n👋 EVO-GRAPH session ended."
            )

            break

        # ----------------------------------------------------
        # Retrieval
        # ----------------------------------------------------

        print(
            "\n🔎 Searching EVO-GRAPH..."
        )

        retrieved = retrieve_learning(
            evo_graph,
            question
        )

        if retrieved:

            print(
                f"📚 Retrieved "
                f"{len(retrieved)} "
                f"experience(s)."
            )

            for i, item in enumerate(
                retrieved,
                start=1
            ):

                print(
                    f"\n{i}. "
                    f"{item.get('experience', '')}"
                )

                print(
                    f"   Semantic: "
                    f"{item.get('semantic_score', 0.0):.4f}"
                )

                print(
                    f"   Final: "
                    f"{item.get('score', 0.0):.4f}"
                )

                print(
                    f"   Confidence: "
                    f"{item.get('confidence', 0.0):.2f}"
                )

        else:

            print(
                "📭 No relevant previous "
                "experience found."
            )

        learned_context = (
            build_learning_context(
                retrieved
            )
        )

        # ----------------------------------------------------
        # Answer
        # ----------------------------------------------------

        print(
            "\n🤖 Generating answer..."
        )

        answer = generate_answer(
            llm,
            question,
            learned_context
        )

        print(
            "\n" + "=" * 60
        )

        print(
            "ANSWER"
        )

        print(
            "=" * 60
        )

        print(
            answer
        )

        # ----------------------------------------------------
        # Feedback
        # ----------------------------------------------------

        print(
            "\n" + "-" * 60
        )

        feedback = input(
            "\nWas this answer useful?\n"
            "Enter positive, negative, or skip:\n> "
        ).strip().lower()

        if feedback in {
            "",
            "skip",
            "s"
        }:

            continue

        # ----------------------------------------------------
        # Reflection
        # ----------------------------------------------------

        print(
            "\n🧠 Reflecting on feedback..."
        )

        reflection = analyze_feedback(
            llm,
            question,
            answer,
            feedback
        )

        print(
            "\nREFLECTION"
        )

        print(
            "-" * 60
        )

        print(
            "Correction:",
            reflection.get(
                "correction",
                ""
            )
        )

        print(
            "Learning rule:",
            reflection.get(
                "learning_rule",
                ""
            )
        )

        print(
            "Reason:",
            reflection.get(
                "reason",
                ""
            )
        )

        print(
            "Applies to:",
            reflection.get(
                "applies_to",
                ""
            )
        )

        # ----------------------------------------------------
        # Graph learning
        # ----------------------------------------------------

        add_learned_experience(
            evo_graph,
            question,
            reflection
        )

        save_graph(
            evo_graph
        )

        print(
            "\n✅ Feedback converted into "
            "graph learning."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()