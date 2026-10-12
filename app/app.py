import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
GRAPH_PATH = PROJECT_ROOT / "data" / "evo_graph.json"

from main import (
    initialize_graph, create_llm, retrieve_learning,
    build_learning_context, generate_answer, analyze_feedback,
    add_learned_experience, save_graph,
)

st.set_page_config(page_title="EVO-GRAPH", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 15% 10%,rgba(0,190,255,.10),transparent 28%),radial-gradient(circle at 85% 20%,rgba(150,70,255,.10),transparent 28%),#07101f;color:#f4f7fb}
.hero{padding:22px 28px;border:1px solid rgba(0,220,255,.45);border-radius:20px;background:linear-gradient(120deg,rgba(0,170,255,.16),rgba(120,50,255,.13));margin-bottom:18px}
.hero-title{font-size:42px;font-weight:800;letter-spacing:1px}.hero-subtitle{color:#a9c8df;font-size:16px}
.card{border:1px solid rgba(0,220,255,.25);border-radius:15px;padding:14px;background:rgba(9,22,39,.85);margin-bottom:10px}
.metric{border:1px solid rgba(0,220,255,.25);border-radius:15px;padding:14px;background:rgba(10,25,45,.75);text-align:center}.value{font-size:28px;font-weight:800}.label{color:#9fb5c8;font-size:13px}
</style>
""", unsafe_allow_html=True)

if "graph" not in st.session_state: st.session_state.graph = initialize_graph()
if "llm" not in st.session_state: st.session_state.llm = create_llm()
if "messages" not in st.session_state: st.session_state.messages = []
if "last_question" not in st.session_state: st.session_state.last_question = ""
if "last_answer" not in st.session_state: st.session_state.last_answer = ""
if "last_retrieved" not in st.session_state: st.session_state.last_retrieved = []
if "reflection" not in st.session_state: st.session_state.reflection = None
if "feedback_done" not in st.session_state: st.session_state.feedback_done = False

def counts():
    c={"SKILL":0,"TOPIC":0,"EXPERIENCE":0,"OTHER":0}; vals=[]; validated=feedback=0
    for _,d in st.session_state.graph.graph.nodes(data=True):
        t=str(d.get("type","OTHER")).upper(); c[t if t in c else "OTHER"]+=1
        if t=="EXPERIENCE":
            vals.append(float(d.get("confidence",0) or 0)); validated += bool(d.get("validated",False)); feedback += int(d.get("feedback_count",0) or 0)
    return c,validated,feedback,(sum(vals)/len(vals) if vals else 0)

def dot_graph():
    colors={"SKILL":"#18b7ff","TOPIC":"#b36cff","EXPERIENCE":"#52e08a"}; lines=['digraph G {','bgcolor="transparent";','rankdir=LR;','node [shape=box,style="rounded,filled",fontname="Arial",fontsize=10,fontcolor="white"];','edge [color="#6d8ba5",fontcolor="#a8bed0",fontsize=8];']
    for nid,d in st.session_state.graph.graph.nodes(data=True):
        t=str(d.get("type","OTHER")).upper(); name=str(d.get("name",nid)).replace('"',"'")[:42]; lines.append(f'"{nid}" [label="{t}\\n{name}",fillcolor="{colors.get(t,"#46586b")}"];')
    for s,t,d in st.session_state.graph.graph.edges(data=True): lines.append(f'"{s}" -> "{t}" [label="{str(d.get("relationship","RELATED_TO"))}"];')
    return "\n".join(lines+['}'])

def ask(q):
    g=st.session_state.graph; r=retrieve_learning(g,q); ctx=build_learning_context(r); a=generate_answer(st.session_state.llm,q,ctx)
    st.session_state.last_question=q; st.session_state.last_answer=a; st.session_state.last_retrieved=r; st.session_state.reflection=None; st.session_state.feedback_done=False
    st.session_state.messages += [{"role":"user","content":q},{"role":"assistant","content":a}]

def feedback(kind):
    g=st.session_state.graph; q=st.session_state.last_question; a=st.session_state.last_answer; r=st.session_state.last_retrieved
    if not q or not a: return
    if r:
        eid=r[0].get("id")
        if eid in g.graph.nodes:
            try: g.update_experience(eid,kind)
            except Exception: pass
    ref=analyze_feedback(st.session_state.llm,q,a,kind); st.session_state.reflection=ref
    try:
        learned=add_learned_experience(g,q,ref)
    except Exception:
        import uuid
        learned=f"learned_{uuid.uuid4().hex[:8]}"
        text=(f"Question context: {q}\nCorrection: {ref.get('correction','')}\nLearning rule: {ref.get('learning_rule','')}\nReason: {ref.get('reason','')}\nApplies to: {ref.get('applies_to','')}")
        try: g.add_experience(learned,text,"skill_python",confidence=.6,validated=False)
        except TypeError: g.add_experience(experience_id=learned,experience=text,skill_id="skill_python",confidence=.6,validated=False)
    save_graph(g); st.session_state.feedback_done=True

c,validated,feedback_total,avg=counts()
with st.sidebar:
    st.markdown("## 🧠 EVO-GRAPH")
    st.caption("Self-Evolving AI Learning Agent")
    st.metric("Experiences",c["EXPERIENCE"]); st.metric("Validated",validated); st.metric("Feedback",feedback_total)
    st.progress(min(max(avg,0),1),text=f"Avg. confidence: {avg:.2f}")
    st.divider(); st.success("Ollama / Qwen 2.5:3B"); st.caption("Gemini configured as backup")
    st.caption(f"Graph: {GRAPH_PATH}")
    if st.button("🔄 Reload Graph"): st.session_state.graph=initialize_graph(); st.rerun()
    if st.button("💾 Save Graph"): save_graph(st.session_state.graph); st.success("Graph saved")

st.markdown('<div class="hero"><div class="hero-title">🧠 EVO-GRAPH</div><div class="hero-subtitle">A self-evolving AI agent powered by a dynamic Skill–Experience Graph</div></div>',unsafe_allow_html=True)
cols=st.columns(5)
for col,val,label in zip(cols,[c["SKILL"],c["TOPIC"],c["EXPERIENCE"],validated,feedback_total],["Skills","Topics","Experiences","Validated","Feedback"]):
    col.markdown(f'<div class="metric"><div class="value">{val}</div><div class="label">{label}</div></div>',unsafe_allow_html=True)

left,right=st.columns([1.15,.85])
with left:
    st.subheader("💬 Ask EVO-GRAPH")
    q=st.chat_input("Ask a technical question...")
    if q:
        with st.spinner("EVO-GRAPH is thinking..."): ask(q)
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if st.session_state.last_answer and not st.session_state.feedback_done:
        st.markdown("### Was this answer useful?")
        b1,b2,b3=st.columns(3)
        if b1.button("👍 Positive",use_container_width=True):
            with st.spinner("Reflecting and learning..."): feedback("positive")
            st.rerun()
        if b2.button("👎 Negative",use_container_width=True):
            with st.spinner("Reflecting and learning..."): feedback("negative")
            st.rerun()
        if b3.button("⏭️ Skip",use_container_width=True): st.session_state.feedback_done=True; st.rerun()
    if st.session_state.reflection:
        r=st.session_state.reflection
        with st.expander("🧠 What EVO-GRAPH learned",expanded=True):
            st.write("**Correction:**",r.get("correction","")); st.write("**Learning rule:**",r.get("learning_rule","")); st.write("**Reason:**",r.get("reason","")); st.write("**Applies to:**",r.get("applies_to",""))

with right:
    st.subheader("🔎 Retrieved Experiences")
    if not st.session_state.last_retrieved: st.info("Ask a question to retrieve relevant graph experiences.")
    for i,item in enumerate(st.session_state.last_retrieved,1):
        exp=item.get("experience",item.get("description",item.get("name",""))); score=float(item.get("score",item.get("final_score",0)) or 0); sem=float(item.get("semantic_score",0) or 0); conf=float(item.get("confidence",0) or 0); val=bool(item.get("validated",False)); fb=int(item.get("feedback_count",0) or 0)
        st.markdown(f'<div class="card"><b>{i}. {item.get("id","experience")}</b><br>{exp[:500]}<br><br><b>Graph:</b> {score:.3f} &nbsp; <b>Semantic:</b> {sem:.3f}<br>Confidence: {conf:.2f} &nbsp; | &nbsp; {"Validated" if val else "Unvalidated"} &nbsp; | &nbsp; Feedback: {fb}</div>',unsafe_allow_html=True)

st.divider(); gcol,acol=st.columns([1.35,.65])
with gcol:
    st.subheader("🕸️ Live Knowledge Graph")
    st.graphviz_chart(dot_graph(),use_container_width=True)
with acol:
    st.subheader("📊 Graph Analytics")
    st.metric("Total Nodes",st.session_state.graph.graph.number_of_nodes()); st.metric("Relationships",st.session_state.graph.graph.number_of_edges()); st.metric("Average Confidence",f"{avg:.2f}")
    st.write(f"🟦 Skills: **{c['SKILL']}**"); st.write(f"🟪 Topics: **{c['TOPIC']}**"); st.write(f"🟩 Experiences: **{c['EXPERIENCE']}**")
    if feedback_total: st.success("Graph has evolved through feedback.")
    else: st.info("No feedback-driven evolution yet.")

st.divider(); st.caption("EVO-GRAPH • Dynamic Skill–Experience Graph • Ollama/Qwen + Gemini Backup")
