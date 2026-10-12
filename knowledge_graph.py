import json
from pathlib import Path

import streamlit as st
import networkx as nx


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

GRAPH_JSON = PROJECT_ROOT / "data" / "evo_graph.json"
INITIAL_GRAPH_JSON = PROJECT_ROOT / "graph" / "initial_graph.json"


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="EVO-GRAPH | Knowledge Graph",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# FUTURISTIC UI
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
                circle at 15% 10%,
                rgba(0, 204, 255, 0.10),
                transparent 28%
            ),
            radial-gradient(
                circle at 85% 15%,
                rgba(126, 72, 255, 0.12),
                transparent 30%
            ),
            radial-gradient(
                circle at 50% 100%,
                rgba(0, 255, 170, 0.05),
                transparent 35%
            ),
            #050a13;

        color: #e8f7ff;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }

    /* ========================================================
       HEADER
       ======================================================== */

    .graph-header {
        display: flex;
        align-items: center;
        justify-content: space-between;

        padding: 18px 24px;
        margin-bottom: 14px;

        border: 1px solid rgba(58, 204, 255, 0.18);
        border-radius: 16px;

        background:
            linear-gradient(
                135deg,
                rgba(8, 24, 39, 0.96),
                rgba(5, 13, 24, 0.96)
            );

        box-shadow:
            0 15px 45px rgba(0, 0, 0, 0.35),
            inset 0 1px 0 rgba(255,255,255,0.025);
    }

    .graph-title {
        font-size: 27px;
        font-weight: 850;
        letter-spacing: 0.4px;
        color: #eafaff;

        text-shadow:
            0 0 20px rgba(39, 205, 255, 0.25);
    }

    .graph-subtitle {
        margin-top: 3px;
        font-size: 12px;
        color: #7090a7;
    }

    .live-status {
        padding: 7px 13px;
        border-radius: 20px;

        background: rgba(22, 194, 139, 0.10);
        border: 1px solid rgba(22, 194, 139, 0.30);

        color: #43e4ad;
        font-size: 11px;
        font-weight: 800;
    }

    /* ========================================================
       GRAPH CONTAINER
       ======================================================== */

    .graph-shell {
        border: 1px solid rgba(69, 190, 235, 0.16);
        border-radius: 18px;

        background:
            radial-gradient(
                circle at center,
                rgba(14, 36, 56, 0.42),
                rgba(3, 9, 17, 0.96) 72%
            );

        box-shadow:
            0 20px 60px rgba(0,0,0,0.42),
            inset 0 1px 0 rgba(255,255,255,0.025);

        padding: 12px;

        min-height: 720px;
    }

    /* ========================================================
       STATS
       ======================================================== */

    .stat-card {
        background: rgba(8, 21, 34, 0.90);

        border: 1px solid rgba(65, 187, 230, 0.14);
        border-radius: 13px;

        padding: 12px;

        text-align: center;

        box-shadow:
            0 8px 25px rgba(0,0,0,0.22);
    }

    .stat-value {
        font-size: 22px;
        font-weight: 850;
        color: #eafaff;
    }

    .stat-label {
        font-size: 9px;
        color: #6e8ca1;
        margin-top: 3px;

        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* ========================================================
       LEGEND
       ======================================================== */

    .legend {
        display: flex;
        justify-content: center;
        gap: 28px;

        margin-top: 10px;
        margin-bottom: 8px;

        font-size: 11px;
        color: #7994a8;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 7px;
    }

    .dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
    }

    .skill {
        background: #18cfff;
        box-shadow: 0 0 12px #18cfff;
    }

    .topic {
        background: #9b5cff;
        box-shadow: 0 0 12px #9b5cff;
    }

    .experience {
        background: #27d49a;
        box-shadow: 0 0 12px #27d49a;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD GRAPH
# ============================================================

def load_graph():
    graph = nx.DiGraph()

    source = None

    if GRAPH_JSON.exists():
        source = GRAPH_JSON

    elif INITIAL_GRAPH_JSON.exists():
        source = INITIAL_GRAPH_JSON

    if source is None:
        return graph, None

    try:
        with open(source, "r", encoding="utf-8") as file:
            data = json.load(file)

        nodes = data.get("nodes", [])
        relationships = data.get(
            "relationships",
            data.get("edges", [])
        )

        for node in nodes:
            node_id = node.get("id")

            if node_id:
                attributes = {
                    key: value
                    for key, value in node.items()
                    if key != "id"
                }

                graph.add_node(
                    node_id,
                    **attributes
                )

        for edge in relationships:
            source_id = edge.get(
                "source",
                edge.get("from")
            )

            target_id = edge.get(
                "target",
                edge.get("to")
            )

            if source_id and target_id:
                attributes = {
                    key: value
                    for key, value in edge.items()
                    if key not in {
                        "source",
                        "target",
                        "from",
                        "to",
                    }
                }

                graph.add_edge(
                    source_id,
                    target_id,
                    **attributes
                )

        return graph, source

    except Exception as error:
        st.error(f"Unable to load knowledge graph: {error}")
        return nx.DiGraph(), source


# ============================================================
# GRAPHVIZ
# ============================================================

def build_dot(graph):

    colors = {
        "SKILL": "#18cfff",
        "TOPIC": "#9b5cff",
        "EXPERIENCE": "#27d49a",
        "OTHER": "#71849a",
    }

    lines = [
        "digraph G {",

        'bgcolor="transparent";',

        "rankdir=LR;",

        "overlap=false;",
        "splines=true;",

        "pad=0.35;",
        "nodesep=0.55;",
        "ranksep=1.0;",

        (
            'node [shape=circle, '
            'style="filled", '
            'fontname="Arial", '
            'fontsize=11, '
            'fontcolor="white", '
            'penwidth=1.5];'
        ),

        (
            'edge [color="#526b7f", '
            'fontcolor="#8aa2b5", '
            'fontsize=8, '
            'penwidth=1.2];'
        ),
    ]

    for node_id, data in graph.nodes(data=True):

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
            [:35]
        )

        color = colors.get(
            node_type,
            colors["OTHER"]
        )

        lines.append(
            f'"{node_id}" '
            f'[label="{name}", '
            f'fillcolor="{color}", '
            f'color="{color}"];'
        )

    for source, target, data in graph.edges(data=True):

        relationship = str(
            data.get(
                "relationship",
                data.get(
                    "type",
                    "RELATED_TO"
                )
            )
        )

        relationship = (
            relationship
            .replace('"', "'")
            .replace("\n", " ")
            [:28]
        )

        lines.append(
            f'"{source}" -> "{target}" '
            f'[label="{relationship}"];'
        )

    lines.append("}")

    return "\n".join(lines)


# ============================================================
# LOAD
# ============================================================

graph, source_file = load_graph()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="graph-header">

        <div>
            <div class="graph-title">
                🧠 EVO-GRAPH KNOWLEDGE GRAPH
            </div>

            <div class="graph-subtitle">
                Dynamic Skill–Experience Graph
            </div>
        </div>

        <div class="live-status">
            ● GRAPH ONLINE
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# STATS
# ============================================================

total_nodes = graph.number_of_nodes()
total_edges = graph.number_of_edges()

skill_count = sum(
    1
    for _, data in graph.nodes(data=True)
    if str(
        data.get("type", "")
    ).upper() == "SKILL"
)

topic_count = sum(
    1
    for _, data in graph.nodes(data=True)
    if str(
        data.get("type", "")
    ).upper() == "TOPIC"
)

experience_count = sum(
    1
    for _, data in graph.nodes(data=True)
    if str(
        data.get("type", "")
    ).upper() == "EXPERIENCE"
)


col1, col2, col3, col4, col5 = st.columns(5)

stats = [
    (col1, total_nodes, "Total Nodes"),
    (col2, total_edges, "Relationships"),
    (col3, skill_count, "Skills"),
    (col4, topic_count, "Topics"),
    (col5, experience_count, "Experiences"),
]

for column, value, label in stats:

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
            unsafe_allow_html=True,
        )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# LEGEND
# ============================================================

st.markdown(
    """
    <div class="legend">

        <div class="legend-item">
            <span class="dot skill"></span>
            SKILL
        </div>

        <div class="legend-item">
            <span class="dot topic"></span>
            TOPIC
        </div>

        <div class="legend-item">
            <span class="dot experience"></span>
            EXPERIENCE
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GRAPH
# ============================================================

st.markdown(
    '<div class="graph-shell">',
    unsafe_allow_html=True,
)

if graph.number_of_nodes() > 0:

    st.graphviz_chart(
        build_dot(graph),
        use_container_width=True,
    )

else:

    st.warning(
        "Knowledge graph is currently empty."
    )

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# FOOTER
# ============================================================

if source_file:

    st.caption(
        f"Graph source: {source_file.name}"
    )