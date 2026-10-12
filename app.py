# ============================================================

# EVO-GRAPH

# Professional Comparison + Learning Dashboard

# ============================================================

import sys

import uuid

import json

import gzip

from pathlib import Path

import graphviz

import streamlit as st

# ============================================================

# PROJECT PATHS

# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(0, str(PROJECT_ROOT))

GRAPH_PATH = PROJECT_ROOT / "data" / "evo_graph.json"

TEXT_MEMORY_PATH = (

    PROJECT_ROOT

    / "data"

    / "experiment"

    / "text_memory_seed.json"

)

# ============================================================

# EXISTING EVO-GRAPH BACKEND

# ============================================================

from main import (

    initialize_graph,

    create_llm,

    retrieve_learning,

    build_learning_context,

    generate_answer,

    analyze_feedback,

    add_learned_experience,

    save_graph,

    generate_with_backup,

)

# ============================================================

# TEXT MEMORY

# ============================================================

try:

    from app.text_memory import TextMemory

    TEXT_MEMORY_AVAILABLE = True

except Exception:

    TextMemory = None

    TEXT_MEMORY_AVAILABLE = False

# ============================================================

# PAGE

# ============================================================

st.set_page_config(

    page_title="EVO-GRAPH",

    page_icon="🧠",

    layout="wide",

    initial_sidebar_state="expanded",

)

# ============================================================

# CSS

# ============================================================

st.markdown(

    """

<style>

html, body, [class*="css"] {

    font-family: Inter, -apple-system, BlinkMacSystemFont,

                 "Segoe UI", sans-serif;

}

.stApp {

    background:

        radial-gradient(

            circle at 10% 0%,

            rgba(28, 151, 255, 0.12),

            transparent 25%

        ),

        radial-gradient(

            circle at 90% 8%,

            rgba(123, 74, 255, 0.12),

            transparent 27%

        ),

        #f5f8fc;

    color: #132238;

}

/* Hide Streamlit branding */

#MainMenu {

    visibility: hidden;

}

footer {

    visibility: hidden;

}

header {

    background: transparent !important;

}

/* =========================================================

   SIDEBAR

   ========================================================= */

section[data-testid="stSidebar"] {

    background:

        linear-gradient(

            180deg,

            #101a2b 0%,

            #0b1423 100%

        );

    border-right: 1px solid rgba(255,255,255,0.08);

}

section[data-testid="stSidebar"] * {

    color: #e9f1fb;

}

.sidebar-brand {

    font-size: 22px;

    font-weight: 800;

    margin-bottom: 2px;

}

.sidebar-sub {

    color: #8fa6bf;

    font-size: 12px;

}

.sidebar-section {

    color: #54c8ff;

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 1.2px;

    margin-top: 22px;

    margin-bottom: 8px;

}

/* =========================================================

   HERO

   ========================================================= */

.hero {

    background:

        linear-gradient(

            115deg,

            #ffffff 0%,

            #f2f7ff 55%,

            #eef0ff 100%

        );

    border: 1px solid #d9e5f3;

    border-radius: 22px;

    padding: 22px 28px;

    box-shadow:

        0 10px 35px rgba(38, 73, 112, 0.08);

    margin-bottom: 18px;

}

.hero-title {

    font-size: 40px;

    line-height: 1;

    font-weight: 850;

    color: #14233d;

}

.hero-subtitle {

    margin-top: 7px;

    color: #62748b;

    font-size: 14px;

}

.hero-pills {

    display: flex;

    gap: 8px;

    flex-wrap: wrap;

    margin-top: 14px;

}

.pill {

    background: #edf4ff;

    border: 1px solid #d6e6fa;

    color: #28527d;

    padding: 6px 11px;

    border-radius: 999px;

    font-size: 11px;

    font-weight: 700;

}

/* =========================================================

   SECTION

   ========================================================= */

.section-title {

    font-size: 21px;

    font-weight: 800;

    color: #172943;

    margin-top: 16px;

    margin-bottom: 9px;

}

.section-subtitle {

    color: #71839a;

    font-size: 12px;

    margin-bottom: 12px;

}

/* =========================================================

   COMPARISON CARDS

   ========================================================= */

.compare-card {

    background: rgba(255,255,255,0.96);

    border-radius: 18px;

    border: 1px solid #dce6f1;

    padding: 18px;

    min-height: 565px;

    box-shadow:

        0 8px 25px rgba(40, 70, 100, 0.07);

}

.card-red {

    border-top: 4px solid #f46b82;

}

.card-yellow {

    border-top: 4px solid #e7ad28;

}

.card-green {

    border-top: 4px solid #19b88a;

}

.card-title {

    font-size: 18px;

    font-weight: 850;

    color: #182943;

}

.card-subtitle {

    color: #7b8ca1;

    font-size: 11px;

    margin-top: 2px;

    margin-bottom: 15px;

}

.badge {

    display: inline-block;

    padding: 5px 9px;

    border-radius: 999px;

    font-size: 10px;

    font-weight: 800;

    margin-bottom: 10px;

}

.badge-red {

    background: #fff0f3;

    color: #d74a66;

}

.badge-yellow {

    background: #fff8df;

    color: #a87900;

}

.badge-green {

    background: #e7faf4;

    color: #078a66;

}

/* =========================================================

   PROCESS

   ========================================================= */

.process-box {

    background: #f7f9fc;

    border: 1px solid #e6edf5;

    border-radius: 13px;

    padding: 11px;

    margin-bottom: 14px;

}

.process-title {

    font-size: 12px;

    font-weight: 800;

    color: #44566e;

    margin-bottom: 7px;

}

.process-step {

    font-size: 11px;

    color: #566a82;

    padding: 3px 0;

}

/* =========================================================

   RETRIEVAL

   ========================================================= */

.retrieval-title {

    font-size: 12px;

    font-weight: 800;

    color: #31455e;

    margin-bottom: 7px;

}

.retrieve-item {

    background: #f8fafc;

    border: 1px solid #e5ebf2;

    border-radius: 10px;

    padding: 8px 9px;

    margin-bottom: 6px;

}

.retrieve-name {

    font-size: 11px;

    font-weight: 750;

    color: #2d4059;

}

.retrieve-meta {

    font-size: 9px;

    color: #7d8ea2;

    margin-top: 3px;

}

/* =========================================================

   ANSWER

   ========================================================= */

.answer-title {

    font-size: 12px;

    font-weight: 800;

    color: #31455e;

    margin-top: 13px;

    margin-bottom: 7px;

}

.answer-box {

    background: #f8fafc;

    border: 1px solid #e2e9f1;

    border-radius: 11px;

    padding: 11px;

    color: #344861;

    font-size: 11px;

    line-height: 1.55;

}

/* =========================================================

   GRAPH PANEL

   ========================================================= */

.graph-panel {

    background: #ffffff;

    border: 1px solid #dce6f1;

    border-radius: 18px;

    padding: 15px;

    box-shadow:

        0 8px 25px rgba(40,70,100,0.06);

}

.graph-title {

    font-size: 18px;

    font-weight: 850;

    color: #172943;

}

.graph-sub {

    color: #7c8ca0;

    font-size: 11px;

    margin-bottom: 10px;

}

/* =========================================================

   LEARNING LOOP

   ========================================================= */

.learning-panel {

    background:

        linear-gradient(

            120deg,

            #ffffff,

            #f4fbf8

        );

    border: 1px solid #d5e9e2;

    border-radius: 18px;

    padding: 18px;

    box-shadow:

        0 8px 25px rgba(30,90,70,0.06);

}

.loop-step {

    text-align: center;

    background: #ffffff;

    border: 1px solid #e0ebe7;

    border-radius: 13px;

    padding: 12px 7px;

}

.loop-icon {

    font-size: 24px;

}

.loop-name {

    font-size: 10px;

    font-weight: 750;

    color: #3c5360;

    margin-top: 5px;

}

/* =========================================================

   METRICS

   ========================================================= */

.stat-card {

    background: #ffffff;

    border: 1px solid #dce6f1;

    border-radius: 15px;

    padding: 13px;

    text-align: center;

    box-shadow:

        0 6px 20px rgba(40,70,100,0.05);

}

.stat-value {

    font-size: 24px;

    font-weight: 850;

    color: #182943;

}

.stat-label {

    font-size: 10px;

    color: #7c8da1;

    margin-top: 2px;

}

/* =========================================================

   STATUS

   ========================================================= */

.status-box {

    background: #effaf5;

    border: 1px solid #ccefe0;

    border-radius: 13px;

    padding: 10px;

    color: #147653;

    font-size: 11px;

    font-weight: 700;

}

/* =========================================================

   BENCHMARK

   ========================================================= */

.benchmark-card {

    background: #ffffff;

    border: 1px solid #dce6f1;

    border-radius: 15px;

    padding: 12px;

}

.benchmark-title {

    font-size: 13px;

    font-weight: 800;

    margin-bottom: 8px;

}

/* =========================================================

   FOOTER

   ========================================================= */

.footer {

    text-align: center;

    color: #91a0b1;

    font-size: 10px;

    padding: 20px;

}

</style>

""",

    unsafe_allow_html=True,

)

# ============================================================

# SESSION STATE

# ============================================================

if "graph" not in st.session_state:

    st.session_state.graph = initialize_graph()

if "llm" not in st.session_state:

    st.session_state.llm = create_llm()

if "comparison" not in st.session_state:

    st.session_state.comparison = None

if "last_question" not in st.session_state:

    st.session_state.last_question = ""

if "last_answer" not in st.session_state:

    st.session_state.last_answer = ""

if "last_retrieved" not in st.session_state:

    st.session_state.last_retrieved = []

if "reflection" not in st.session_state:

    st.session_state.reflection = None

if "feedback_done" not in st.session_state:

    st.session_state.feedback_done = False

# ============================================================

# GRAPH STATS

# ============================================================

def graph_stats():

    counts = {

        "SKILL": 0,

        "TOPIC": 0,

        "EXPERIENCE": 0,

        "OTHER": 0,

    }

    confidence_values = []

    validated = 0

    feedback = 0

    for _, data in (

        st.session_state.graph.graph.nodes(

            data=True

        )

    ):

        node_type = str(

            data.get("type", "OTHER")

        ).upper()

        if node_type not in counts:

            node_type = "OTHER"

        counts[node_type] += 1

        if node_type == "EXPERIENCE":

            confidence_values.append(

                float(

                    data.get(

                        "confidence",

                        0

                    ) or 0

                )

            )

            if data.get(

                "validated",

                False

            ):

                validated += 1

            feedback += int(

                data.get(

                    "feedback_count",

                    0

                ) or 0

            )

    average = (

        sum(confidence_values)

        / len(confidence_values)

        if confidence_values

        else 0

    )

    return (

        counts,

        validated,

        feedback,

        average

    )

# ============================================================

# TEXT MEMORY

# ============================================================

def text_memory_search(question):

    if not TEXT_MEMORY_AVAILABLE:

        return [], ""

    if not TEXT_MEMORY_PATH.exists():

        return [], ""

    try:

        memory = TextMemory(

            str(TEXT_MEMORY_PATH)

        )

        results = memory.search(

            question,

            limit=3

        )

        context = memory.build_context(

            question,

            limit=3

        )

        return results, context

    except Exception as error:

        print(

            "Text memory error:",

            error

        )

        return [], ""

# ============================================================

# LLM ONLY

# ============================================================

def run_llm_only(question):

    prompt = f"""

You are a general AI assistant.

Answer the following technical question.

Do not use previous memory.

Do not use EVO-GRAPH.

Do not use stored experiences.

QUESTION:

{question}

Give a clear, accurate and useful answer.

"""

    return generate_with_backup(

        st.session_state.llm,

        prompt

    )

# ============================================================

# TEXT MEMORY ANSWER

# ============================================================

def run_text_memory(

    question,

    context

):

    prompt = f"""

You are an AI assistant using text-based memory.

Use the retrieved memories when relevant.

Do not blindly copy them.

Use your own reasoning.

RETRIEVED TEXT MEMORY:

\\---------------------

{context}

\\---------------------

QUESTION:

{question}

Give the best technically correct answer.

"""

    return generate_with_backup(

        st.session_state.llm,

        prompt

    )

# ============================================================

# EVO-GRAPH

# ============================================================

def run_evo_graph(question):

    graph = st.session_state.graph

    retrieved = retrieve_learning(graph, question)

    # Prioritize a previously successful answer for the exact same question.

    normalized_q = " ".join(question.lower().split())

    successful_memory = None

    for node_id, data in graph.graph.nodes(data=True):

        if str(data.get("type", "")).upper() != "EXPERIENCE":

            continue

        if data.get("feedback_type") != "positive":

            continue

        stored_q = str(data.get("source_question", ""))

        if normalized_q == " ".join(stored_q.lower().split()):

            successful_memory = {

                "id": node_id,

                "experience": data.get("experience", data.get("name", "")),

                "semantic_score": 1.0,

                "score": 1.0,

                "confidence": data.get("confidence", 0.95),

                "validated": True,

                "feedback_count": data.get("feedback_count", 1),

                "feedback_type": "positive",

            }

            break

    if successful_memory:

        retrieved = [successful_memory] + [

            item for item in retrieved if item.get("id") != successful_memory["id"]

        ]

    context = build_learning_context(retrieved)

    answer = generate_answer(st.session_state.llm, question, context)

    return retrieved, context, answer

# RUN COMPARISON

# ============================================================

def run_comparison(question):

    with st.spinner(

        "Running all three AI approaches..."

    ):

        # A

        llm_answer = run_llm_only(

            question

        )

        # B

        memory_items, memory_context = (

            text_memory_search(question)

        )

        memory_answer = run_text_memory(

            question,

            memory_context

        )

        # C

        graph_items, graph_context, graph_answer = (

            run_evo_graph(question)

        )

    st.session_state.comparison = {

        "question": question,

        "llm": {

            "answer": llm_answer

        },

        "memory": {

            "items": memory_items,

            "context": memory_context,

            "answer": memory_answer

        },

        "graph": {

            "items": graph_items,

            "context": graph_context,

            "answer": graph_answer

        }

    }

    st.session_state.last_question = (

        question

    )

    st.session_state.last_answer = (

        graph_answer

    )

    st.session_state.last_retrieved = (

        graph_items

    )

    st.session_state.reflection = None

    st.session_state.feedback_done = False

# ============================================================

# FEEDBACK

# ============================================================

def process_feedback(feedback_type):

    question = st.session_state.last_question

    answer = st.session_state.last_answer

    retrieved = st.session_state.last_retrieved

    graph = st.session_state.graph

    if not question or not answer:

        return

    # Positive feedback preserves the actual successful answer.

    if feedback_type == "positive":

        experience_id = f"successful_{uuid.uuid4().hex[:8]}"

        experience_text = (

            f"Question: {question}\n\n"

            f"Successful Answer:\n{answer}\n\n"

            f"Learning Rule: Preserve this successful answer style and useful content for similar questions."

        )

        try:

            graph.add_experience(

                experience_id=experience_id,

                experience=experience_text,

                skill_id=None,

                confidence=0.95,

                validated=True

            )

        except TypeError:

            graph.add_experience(

                experience_id, experience_text, "skill_python",

                confidence=0.95, validated=True

            )

        if experience_id in graph.graph.nodes:

            node = graph.graph.nodes[experience_id]

            node["feedback_type"] = "positive"

            node["source_question"] = question

            node["source_answer"] = answer

            node["feedback_count"] = 1

            node["confidence"] = 0.95

            node["validated"] = True

        st.session_state.reflection = {

            "correction": "No correction required.",

            "learning_rule": "Preserve this successful answer style and useful content for similar questions.",

            "reason": "The user marked the answer as useful.",

            "applies_to": "Similar future questions."

        }

        print(f"Successful answer learned: {experience_id}")

        save_graph(graph)

        st.session_state.feedback_done = True

        return

    # Negative feedback keeps the existing reflection-based learning path.

    reflection = analyze_feedback(st.session_state.llm, question, answer, feedback_type)

    st.session_state.reflection = reflection

    if retrieved:

        experience_id = retrieved[0].get("id")

        if experience_id and experience_id in graph.graph.nodes:

            try:

                graph.update_experience(experience_id, feedback_type)

            except Exception as error:

                print("Experience update error:", error)

    try:

        add_learned_experience(graph, question, reflection)

    except Exception as error:

        print("Learning creation error:", error)

    save_graph(graph)

    st.session_state.feedback_done = True

# GRAPH DOT

# ============================================================

def graph_dot():

    colors = {

        "SKILL": "#18aeea",

        "TOPIC": "#9b59ff",

        "EXPERIENCE": "#28c994",

        "OTHER": "#7c8da3"

    }

    lines = [

        "digraph G {",

        'bgcolor="transparent";',

        "dpi=200;",

        "rankdir=LR;",

        (

            'node [shape=circle, '

            'style="filled", '

            'fontname="Arial", '

            'fontsize=10, '

            'fontcolor="white"];'

        ),

        (

            'edge [color="#8ca3ba", '

            'fontcolor="#62758b", '

            'fontsize=8];'

        )

    ]

    for node_id, data in (

        st.session_state.graph.graph.nodes(

            data=True

        )

    ):

        node_type = str(

            data.get(

                "type",

                "OTHER"

            )

        ).upper()

        name = str(

            data.get(

                "name",

                node_id

            )

        )

        name = (

            name

            .replace('"', "'")

            .replace("\n", " ")

            [:32]

        )

        color = colors.get(

            node_type,

            colors["OTHER"]

        )

        lines.append(

            f'"{node_id}" '

            f'[label="{name}", '

            f'fillcolor="{color}"];'

        )

    for source, target, data in (

        st.session_state.graph.graph.edges(

            data=True

        )

    ):

        relationship = str(

            data.get(

                "relationship",

                "RELATED_TO"

            )

        )

        lines.append(

            f'"{source}" -> "{target}" '

            f'[label="{relationship}"];'

        )

    lines.append("}")

    return "\n".join(lines)

# ============================================================

# SIDEBAR

# ============================================================

counts, validated, feedback_total, average = (

    graph_stats()

)

with st.sidebar:

    st.markdown(

        '<div class="sidebar-brand">'

        '🧠 EVO-GRAPH'

        '</div>',

        unsafe_allow_html=True

    )

    st.markdown(

        '<div class="sidebar-sub">'

        'Self-Evolving AI Learning Agent'

        '</div>',

        unsafe_allow_html=True

    )

    st.divider()

    st.markdown(

        '<div class="sidebar-section">'

        'GRAPH STATISTICS'

        '</div>',

        unsafe_allow_html=True

    )

    st.metric(

        "🧩 Skills",

        counts["SKILL"]

    )

    st.metric(

        "🎯 Topics",

        counts["TOPIC"]

    )

    st.metric(

        "🧠 Experiences",

        counts["EXPERIENCE"]

    )

    st.metric(

        "✓ Validated",

        validated

    )

    st.metric(

        "💬 Feedback",

        feedback_total

    )

    st.write(

        f"Avg. Confidence: "

        f"**{average:.2f}**"

    )

    st.progress(

        min(

            max(

                average,

                0

            ),

            1

        )

    )

    st.divider()

    st.markdown(

        '<div class="sidebar-section">'

        'AI ENGINE'

        '</div>',

        unsafe_allow_html=True

    )

    st.markdown(

        """

<div class="status-box">

🟢 Ollama / Qwen 2.5:3B<br>

🟢 Primary Model Online<br>

🟢 Gemini Backup Ready

</div>

""",

        unsafe_allow_html=True

    )

    st.caption(

        f"Graph: {GRAPH_PATH}"

    )

    st.divider()

    if st.button(

        "🔄 Reload Graph",

        use_container_width=True

    ):

        st.session_state.graph = (

            initialize_graph()

        )

        st.rerun()

    if st.button(

        "💾 Save Graph",

        use_container_width=True

    ):

        save_graph(

            st.session_state.graph

        )

        st.success(

            "Graph saved."

        )

# ============================================================



# ============================================================

# QUESTION AREA

# ============================================================

st.markdown(

    '<div class="section-title">'

    '⚔️ Three Approaches. One Question.'

    '</div>',

    unsafe_allow_html=True

)

input_col, run_col, sample_col, clear_col = (

    st.columns(

        [5.5, 1.4, 1.7, 0.8]

    )

)

with input_col:

    question = st.text_input(

        "Question",

        placeholder=(

            "How should I debug a Python error?"

        ),

        label_visibility="collapsed"

    )

with run_col:

    run = st.button(

        "▶ Run Comparison",

        type="primary",

        use_container_width=True

    )

with sample_col:

    sample = st.selectbox(

        "Sample",

        [

            "Sample Questions",

            "How should I debug a Python error?",

            "What is the difference between a stack and a queue?",

            "What is the time complexity of binary search?",

            "What is the difference between a primary key and foreign key?"

        ],

        label_visibility="collapsed"

    )

with clear_col:

    clear = st.button(

        "✕",

        use_container_width=True

    )

if sample != "Sample Questions":

    question = sample

if clear:

    st.session_state.comparison = None

    st.session_state.reflection = None

    st.session_state.last_question = ""

    st.session_state.last_answer = ""

    st.session_state.last_retrieved = []

    st.rerun()

if run:

    if not question.strip():

        st.warning(

            "Enter a question first."

        )

    else:

        run_comparison(

            question.strip()

        )

        st.rerun()

# ============================================================

# COMPARISON

# ============================================================

comparison = (

    st.session_state.comparison

)

if comparison:

    st.markdown(

        f"""

<div class="question-box">

<b>QUESTION</b><br>

{comparison["question"]}

</div>

""",

        unsafe_allow_html=True

    )

    # ========================================================

    # MAIN THREE COLUMNS

    # ========================================================

    left, middle, right = st.columns(

        [1.05, 1.05, 1.05],

        gap="small"

    )

    # ========================================================

    # A. LLM ONLY

    # ========================================================

    with left:

        st.markdown(

            '<div class="card-title">'

            '🤖 A. LLM ONLY'

            '</div>',

            unsafe_allow_html=True

        )

        st.caption(

            "General Knowledge"

        )

        st.markdown(

            '<span class="badge badge-red">'

            'NO MEMORY'

            '</span>',

            unsafe_allow_html=True

        )

        st.markdown(

            "#### Process"

        )

        with st.container(

            border=True

        ):

            st.write(

                "① 👤 User Question"

            )

            st.write(

                "② 🧠 Qwen / LLM"

            )

            st.write(

                "③ 💬 Generate Answer"

            )

            st.write(

                "④ 🚫 No Previous Memory"

            )

        st.markdown(

            "#### Retrieved Knowledge"

        )

        st.info(

            "No previous experience is retrieved."

        )

        st.markdown(

            "#### Answer"

        )

        with st.container(

            border=True

        ):

            st.write(

                comparison["llm"]["answer"]

            )

    # ========================================================

    # B. TEXT MEMORY

    # ========================================================

    with middle:

        st.markdown(

            '<div class="card-title">'

            '📄 B. TEXT MEMORY'

            '</div>',

            unsafe_allow_html=True

        )

        st.caption(

            "Stored Similar Experiences"

        )

        st.markdown(

            '<span class="badge badge-yellow">'

            'SIMILARITY SEARCH'

            '</span>',

            unsafe_allow_html=True

        )

        st.markdown(

            "#### Process"

        )

        with st.container(

            border=True

        ):

            st.write(

                "① 👤 User Question"

            )

            st.write(

                "② 🔎 Search Text Memory"

            )

            st.write(

                "③ 📄 Retrieve Similar Text"

            )

            st.write(

                "④ 🧠 Send Context → LLM"

            )

        st.markdown(

            "#### Retrieved Memory"

        )

        memory_items = (

            comparison["memory"]["items"]

        )

        if memory_items:

            for index, item in enumerate(

                memory_items,

                start=1

            ):

                text = str(

                    item.get(

                        "text",

                        item.get(

                            "experience",

                            item.get(

                                "question",

                                item.get(

                                    "name",

                                    str(item)

                                )

                            )

                        )

                    )

                )

                score = item.get(

                    "score",

                    item.get(

                        "similarity",

                        None

                    )

                )

                if score is not None:

                    try:

                        score_text = (

                            f"{float(score):.2f}"

                        )

                    except Exception:

                        score_text = "-"

                else:

                    score_text = "-"

                with st.container(

                    border=True

                ):

                    st.write(

                        f"📄 **{index}.** "

                        f"{text[:90]}"

                    )

                    st.caption(

                        f"Similarity: {score_text}"

                    )

        else:

            st.info(

                "No similar text memory found."

            )

        st.markdown(

            "#### Answer"

        )

        with st.container(

            border=True

        ):

            st.write(

                comparison["memory"]["answer"]

            )

    # ========================================================

    # C. EVO-GRAPH

    # ========================================================

    with right:

        st.markdown(

            '<div class="card-title">'

            '🕸️ C. EVO-GRAPH'

            '</div>',

            unsafe_allow_html=True

        )

        st.caption(

            "Graph + Skills + Experiences"

        )

        st.markdown(

            '<span class="badge badge-green">'

            'GRAPH RETRIEVAL'

            '</span>',

            unsafe_allow_html=True

        )

        st.markdown(

            "#### Process"

        )

        with st.container(

            border=True

        ):

            st.write(

                "① 👤 User Question"

            )

            st.write(

                "② 🕸️ Search Skill–Experience Graph"

            )

            st.write(

                "③ 📊 Score Relevance + Confidence"

            )

            st.write(

                "④ 🧠 Send Graph Context → LLM"

            )

        st.markdown(

            "#### Retrieved Graph Knowledge"

        )

        graph_items = (

            comparison["graph"]["items"]

        )

        if graph_items:

            for index, item in enumerate(

                graph_items,

                start=1

            ):

                experience = str(

                    item.get(

                        "experience",

                        item.get(

                            "description",

                            item.get(

                                "name",

                                ""

                            )

                        )

                    )

                )

                score = float(

                    item.get(

                        "score",

                        item.get(

                            "final_score",

                            0

                        )

                    ) or 0

                )

                confidence = float(

                    item.get(

                        "confidence",

                        0

                    ) or 0

                )

                validated = item.get(

                    "validated",

                    False

                )

                with st.container(

                    border=True

                ):

                    st.write(

                        f"🕸️ **{index}.** "

                        f"{experience[:85]}"

                    )

                    st.caption(

                        f"Graph Score: {score:.2f}  •  "

                        f"Confidence: {confidence:.2f}  •  "

                        f"{'✓ Validated' if validated else '○ Unvalidated'}"

                    )

        else:

            st.info(

                "No relevant graph experience found."

            )

        st.markdown(

            "#### Answer"

        )

        with st.container(

            border=True

        ):

            st.write(

                comparison["graph"]["answer"]

            )

# ============================================================



# LEARNING LOOP

# ============================================================

if comparison:

    st.divider()

    st.markdown(

        '<div class="section-title">'

        '🧠 EVO-GRAPH LEARNING LOOP'

        '</div>',

        unsafe_allow_html=True

    )

    st.caption(

        "Only EVO-GRAPH participates in "

        "feedback-driven evolution."

    )

    loop1, arrow1, loop2, arrow2, loop3, arrow3, loop4, arrow4, loop5 = (

        st.columns(

            [

                1.1,

                0.25,

                1.1,

                0.25,

                1.1,

                0.25,

                1.1,

                0.25,

                1.1

            ]

        )

    )

    with loop1:

        st.markdown(

            """

<div class="loop-step">

<div class="loop-icon">👍</div>

<div class="loop-name">USER FEEDBACK</div>

</div>

""",

            unsafe_allow_html=True

        )

    with arrow1:

        st.markdown("### →")

    with loop2:

        st.markdown(

            """

<div class="loop-step">

<div class="loop-icon">🔍</div>

<div class="loop-name">REFLECTION</div>

</div>

""",

            unsafe_allow_html=True

        )

    with arrow2:

        st.markdown("### →")

    with loop3:

        st.markdown(

            """

<div class="loop-step">

<div class="loop-icon">🧠</div>

<div class="loop-name">NEW EXPERIENCE</div>

</div>

""",

            unsafe_allow_html=True

        )

    with arrow3:

        st.markdown("### →")

    with loop4:

        st.markdown(

            """

<div class="loop-step">

<div class="loop-icon">🕸️</div>

<div class="loop-name">GRAPH UPDATE</div>

</div>

""",

            unsafe_allow_html=True

        )

    with arrow4:

        st.markdown("### →")

    with loop5:

        st.markdown(

            """

<div class="loop-step">

<div class="loop-icon">📈</div>

<div class="loop-name">EVOLVES OVER TIME</div>

</div>

""",

            unsafe_allow_html=True

        )

    st.write("")

    feedback1, feedback2, feedback3 = st.columns(

        [1, 1, 1]

    )

    if not st.session_state.feedback_done:

        with feedback1:

            if st.button(

                "👍 Positive Feedback",

                use_container_width=True

            ):

                with st.spinner(

                    "Reflecting and learning..."

                ):

                    process_feedback(

                        "positive"

                    )

                st.rerun()

        with feedback2:

            if st.button(

                "👎 Negative Feedback",

                use_container_width=True

            ):

                with st.spinner(

                    "Reflecting and learning..."

                ):

                    process_feedback(

                        "negative"

                    )

                st.rerun()

        with feedback3:

            if st.button(

                "⏭️ Skip",

                use_container_width=True

            ):

                st.session_state.feedback_done = (

                    True

                )

                st.rerun()

    else:

        st.success(

            "✓ Feedback processed and graph updated."

        )

# ============================================================

# REFLECTION

# ============================================================

if st.session_state.reflection:

    reflection = (

        st.session_state.reflection

    )

    st.markdown(

        "### 🔄 Reflection Result"

    )

    r1, r2 = st.columns(2)

    with r1:

        st.info(

            "Correction\n\n"

            + reflection.get(

                "correction",

                "Not available"

            )

        )

        st.info(

            "Learning Rule\n\n"

            + reflection.get(

                "learning_rule",

                "Not available"

            )

        )

    with r2:

        st.info(

            "Reason\n\n"

            + reflection.get(

                "reason",

                "Not available"

            )

        )

        st.info(

            "Applies To\n\n"

            + reflection.get(

                "applies_to",

                "Not available"

            )

        )

# ============================================================

# LIVE GRAPH STATISTICS

# ============================================================

st.divider()

st.markdown(

    '<div class="section-title">'

    '📊 Live Graph Statistics'

    '</div>',

    unsafe_allow_html=True

)

counts, validated, feedback_total, average = (

    graph_stats()

)

s1, s2, s3, s4, s5, s6 = st.columns(6)

stats_data = [

    (

        s1,

        counts["SKILL"],

        "Skills"

    ),

    (

        s2,

        counts["TOPIC"],

        "Topics"

    ),

    (

        s3,

        counts["EXPERIENCE"],

        "Experiences"

    ),

    (

        s4,

        validated,

        "Validated"

    ),

    (

        s5,

        feedback_total,

        "Feedback"

    ),

    (

        s6,

        f"{average:.2f}",

        "Avg Confidence"

    )

]

for column, value, label in stats_data:

    with column:

        st.markdown(

            f"""

<div class="stat-card">

<div class="stat-value">

{value}

</div>

<div class="stat-label">

{label}

</div>

</div>

""",

            unsafe_allow_html=True

        )

# ============================================================

# BENCHMARK

# ============================================================

st.divider()

st.markdown(

    '<div class="section-title">'

    '📊 Retrieval Benchmark'

    '</div>',

    unsafe_allow_html=True

)

st.caption(

    "Existing controlled 12-question retrieval benchmark."

)

b1, b2, b3 = st.columns(3)

with b1:

    st.markdown(

        """

<div class="benchmark-card">

<div class="benchmark-title">

🤖 A. LLM Only

</div>

| Metric | Result |

|---|---:|

| P\\@1 | 0.000 |

| P\\@3 | 0.000 |

| Recall\\@3 | 0.000 |

| Success | 0.000 |

</div>

""",

        unsafe_allow_html=True

    )

with b2:

    st.markdown(

        """

<div class="benchmark-card">

<div class="benchmark-title">

📄 B. Text Memory

</div>

| Metric | Result |

|---|---:|

| P\\@1 | 1.000 |

| P\\@3 | 0.738 |

| Recall\\@3 | 1.000 |

| Success | 1.000 |

</div>

""",

        unsafe_allow_html=True

    )

with b3:

    st.markdown(

        """

<div class="benchmark-card">

<div class="benchmark-title">

🕸️ C. EVO-GRAPH

</div>

| Metric | Result |

|---|---:|

| P\\@1 | 1.000 |

| P\\@3 | 0.996 |

| Recall\\@3 | 1.000 |

| Success | 1.000 |

</div>

""",

        unsafe_allow_html=True

    )

# ============================================================

# FEATURE COMPARISON

# ============================================================

st.markdown(

    '<div class="section-title">'

    '⚖️ Feature Comparison'

    '</div>',

    unsafe_allow_html=True

)

st.markdown(

    """

| Capability | 🤖 LLM Only | 📄 Text Memory | 🕸️ EVO-GRAPH |

|---|:---:|:---:|:---:|

| Previous knowledge | ❌ | ✅ | ✅ |

| Similarity retrieval | ❌ | ✅ | ✅ |

| Structured relationships | ❌ | ❌ | ✅ |

| Skill awareness | ❌ | ❌ | ✅ |

| Topic awareness | ❌ | ❌ | ✅ |

| Confidence | ❌ | Limited | ✅ |

| Validation | ❌ | Limited | ✅ |

| Feedback learning | ❌ | ❌ | ✅ |

| Persistent graph | ❌ | ❌ | ✅ |

| Evolves over time | ❌ | ❌ | ✅ |

"""

)

# ============================================================

# FINAL FOOTER

# ============================================================

st.markdown(

    """

<div class="footer">

    EVO-GRAPH • Dynamic Skill–Experience Graph

    • Ollama / Qwen 2.5:3B

    • Gemini Backup

</div>

""",

    unsafe_allow_html=True

)
