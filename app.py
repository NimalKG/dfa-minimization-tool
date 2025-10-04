# app.py
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="DFA Minimizer", layout="wide")
st.title("🤖 DFA Minimization & Visualization Tool")
st.write("Enter a DFA, visualize original and minimized versions. Built for FLAT (KTU).")

# ---- Inputs ----
st.sidebar.header("DFA Input")
states_txt = st.sidebar.text_input("States (comma-separated)", "A,B,C,D")
alphabet_txt = st.sidebar.text_input("Alphabet (comma-separated)", "0,1")
start_state = st.sidebar.text_input("Start state", "A")
finals_txt = st.sidebar.text_input("Final states (comma-separated)", "C,D")

st.sidebar.markdown("**Transitions** (one per line): `State,Symbol=NextState`")
transitions_txt = st.sidebar.text_area(
    "Transitions",
    value="A,0=B\nA,1=C\nB,0=A\nB,1=D\nC,0=D\nC,1=C\nD,0=C\nD,1=D",
    height=200,
)

if st.sidebar.button("Visualize & Minimize"):
    # Parse
    states = [s.strip() for s in states_txt.split(",") if s.strip()]
    alphabet = [a.strip() for a in alphabet_txt.split(",") if a.strip()]
    finals = {f.strip() for f in finals_txt.split(",") if f.strip()}

    # Build transition dict
    dfa = {s: {} for s in states}
    for line in transitions_txt.splitlines():
        line = line.strip()
        if not line: continue
        if "=" not in line or "," not in line:
            st.error(f"Ignoring invalid line: {line}")
            continue
        left, right = line.split("=")
        state, symbol = [x.strip() for x in left.split(",")]
        dfa.setdefault(state, {})[symbol] = right.strip()

    # Remove unreachable
    def reachable(start, dfa):
        seen = set()
        stack = [start]
        while stack:
            u = stack.pop()
            if u in seen: continue
            seen.add(u)
            for a in dfa.get(u, {}):
                v = dfa[u].get(a)
                if v and v not in seen:
                    stack.append(v)
        return seen

    reachable_states = reachable(start_state, dfa)
    # Filter dfa to reachable states only
    dfa = {s: dfa[s] for s in dfa if s in reachable_states}
    states = [s for s in states if s in reachable_states]

    st.subheader("Original DFA")
    col1, col2 = st.columns([1, 1])

    def draw_graph(graph_dict, title):
        # Combine multi-symbol edges
        edges = {}
        for u in graph_dict:
            for a, v in graph_dict[u].items():
                if v is None: continue
                edges.setdefault((u, v), []).append(a)
        G = nx.DiGraph()
        for (u, v), syms in edges.items():
            G.add_edge(u, v, label=",".join(syms))
        pos = nx.spring_layout(G, seed=42)
        fig, ax = plt.subplots(figsize=(6, 4))
        nx.draw(G, pos, ax=ax, with_labels=True, node_size=1600)
        edge_labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=9)
        ax.set_title(title)
        ax.set_axis_off()
        return fig

    fig_orig = draw_graph(dfa, "Original DFA")
    col1.pyplot(fig_orig)
    plt.close(fig_orig)

    # ---- Minimization: partition refinement ----
    non_final = [s for s in states if s not in finals]
    partitions = []
    if finals:
        partitions.append(set(finals & set(states)))
    if non_final:
        partitions.append(set(non_final))

    # iterative refinement
    changed = True
    while changed:
        changed = False
        new_parts = []
        for part in partitions:
            # group by signature of transitions (which partition each symbol goes to)
            groups = {}
            for s in part:
                sig = []
                for a in alphabet:
                    tgt = dfa.get(s, {}).get(a)
                    # find index of partition that contains tgt
                    idx = None
                    for i, p in enumerate(partitions):
                        if tgt in p:
                            idx = i
                            break
                    sig.append(idx)
                sig = tuple(sig)
                groups.setdefault(sig, set()).add(s)
            if len(groups) > 1:
                changed = True
            new_parts.extend(groups.values())
        partitions = new_parts

    # Build minimized DFA
    part_map = {}
    for i, p in enumerate(partitions):
        for s in p:
            part_map[s] = f"P{i}"
    minimized = {}
    labels_for_nodes = {}
    for i, p in enumerate(partitions):
        name = f"P{i}"
        labels_for_nodes[name] = "(" + ",".join(sorted(p)) + ")"
        rep = next(iter(p))
        minimized[name] = {}
        for a in alphabet:
            tgt = dfa.get(rep, {}).get(a)
            if tgt is None:
                minimized[name][a] = None
            else:
                minimized[name][a] = part_map[tgt]

    # Show minimized graph
    st.subheader("Minimized DFA")
    fig_min = draw_graph(minimized, "Minimized DFA")
    col2.pyplot(fig_min)
    plt.close(fig_min)

    # Summary
    st.markdown("### Summary")
    st.write(f"Original states (reachable): **{len(states)}**")
    st.write(f"Minimized states: **{len(minimized)}**")
    st.write("Partitions (state groups):")
    for i, p in enumerate(partitions):
        st.write(f"- P{i}: {sorted(p)}")
    start_p = part_map.get(start_state)
    st.write(f"Start partition: **{start_p}** {labels_for_nodes.get(start_p,'')}")
    final_parts = sorted({part_map[s] for s in finals if s in part_map})
    st.write(f"Final partitions: **{final_parts}**")
  Added main Streamlit app file

  
