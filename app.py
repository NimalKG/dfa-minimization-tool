import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.set_page_config(page_title="DFA Minimization Tool", layout="wide")
st.title("🤖 DFA Minimization & Visualization Tool")
st.write("Enter a DFA, visualize original and minimized versions.")

# ---- Step 1: Input Section ----
st.header("Enter DFA Details")

st.write("**Input format for transitions:** `State,Symbol=NextState`")
st.write("Example (for understanding only): `A,0=B  A,1=C  B,0=A  B,1=D`")

# Input boxes
states_txt = st.text_input("States (comma-separated):")
alphabet_txt = st.text_input("Alphabet (comma-separated):")
start_state = st.text_input("Start state:")
finals_txt = st.text_input("Final states (comma-separated):")
transition_input = st.text_area("Enter transitions (one per line):")

# ---- Step 2: Button to run visualization ----
if st.button("Visualize & Minimize DFA"):
    states = [s.strip() for s in states_txt.split(",") if s.strip()]
    alphabet = [a.strip() for a in alphabet_txt.split(",") if a.strip()]
    finals = {f.strip() for f in finals_txt.split(",") if f.strip()}

    # Build DFA dictionary
    dfa = {s: {} for s in states}
    for line in transition_input.splitlines():
        line = line.strip()
        if not line or "=" not in line or "," not in line:
            st.error(f"Ignoring invalid line: {line}")
            continue
        left, right = line.split("=")
        state, symbol = [x.strip() for x in left.split(",")]
        dfa.setdefault(state, {})[symbol] = right.strip()

    # Remove unreachable states
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
    dfa = {s: dfa[s] for s in dfa if s in reachable_states}
    states = [s for s in states if s in reachable_states]

    # --- Function to draw DFA with arrows, self-loops, and start arrow ---
    def draw_dfa_graph(dfa_dict, title, start_state=None, part_map=None):
        G = nx.DiGraph()
        edges = {}
        for u in dfa_dict:
            for a, v in dfa_dict[u].items():
                if v is None: continue
                edges.setdefault((u, v), [])
                if a in alphabet:
                    edges[(u, v)].append(a)

        for (u, v), syms in edges.items():
            sorted_syms = [sym for sym in alphabet if sym in syms]
            G.add_edge(u, v, label=",".join(sorted_syms))

        pos = nx.circular_layout(G)

        fig, ax = plt.subplots(figsize=(8,6))
        nx.draw_networkx_nodes(G, pos, node_size=2000, node_color="lightblue")
        nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")

        # Draw edges
        for (u, v, d) in G.edges(data=True):
            if u == v:
                # Self-loop
                x, y = pos[u]
                loop = mpatches.FancyArrowPatch(
                    (x, y+0.1), (x, y+0.1),
                    connectionstyle="arc3,rad=0.5",
                    arrowstyle='-|>',
                    mutation_scale=20,
                    color='black'
                )
                ax.add_patch(loop)
                ax.text(x, y+0.18, d['label'], fontsize=10, ha='center')
            else:
                rad = 0.1
                nx.draw_networkx_edges(
                    G, pos, edgelist=[(u,v)],
                    connectionstyle=f"arc3,rad={rad}",
                    arrows=True,
                    arrowstyle='-|>',
                    arrowsize=25,
                    edge_color='black'
                )

        # Edge labels for non self-loop edges
        edge_labels = {(u,v): d['label'] for u,v,d in G.edges(data=True) if u != v}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

        # Draw start arrow
        if start_state:
            if part_map:  # minimized DFA: get corresponding partition node
                start_node = part_map[start_state]
            else:
                start_node = start_state
            if start_node in pos:
                x, y = pos[start_node]
                ax.annotate("",
                            xy=(x, y),
                            xytext=(x-0.6, y+0.6),
                            arrowprops=dict(arrowstyle='-|>', color='green', lw=2))
                ax.text(x-0.65, y+0.65, "Start", color='green', fontsize=10, fontweight='bold')

        ax.set_title(title, fontsize=14)
        ax.set_axis_off()
        return fig

    # Draw Original DFA
    st.subheader("Original DFA")
    col1, col2 = st.columns([1, 1])
    fig_orig = draw_dfa_graph(dfa, "Original DFA", start_state=start_state)
    col1.pyplot(fig_orig)
    plt.close(fig_orig)

    # --- DFA Minimization ---
    non_final = [s for s in states if s not in finals]
    partitions = []
    if finals:
        partitions.append(set(finals & set(states)))
    if non_final:
        partitions.append(set(non_final))

    changed = True
    while changed:
        changed = False
        new_parts = []
        for part in partitions:
            groups = {}
            for s in part:
                sig = []
                for a in alphabet:
                    tgt = dfa.get(s, {}).get(a)
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

    part_map = {}
    for i, p in enumerate(partitions):
        for s in p:
            part_map[s] = f"P{i}"
    minimized = {}
    for i, p in enumerate(partitions):
        name = f"P{i}"
        rep = next(iter(p))
        minimized[name] = {}
        for a in alphabet:
            tgt = dfa.get(rep, {}).get(a)
            minimized[name][a] = part_map[tgt] if tgt else None

    # Draw Minimized DFA with start arrow
    st.subheader("Minimized DFA")
    fig_min = draw_dfa_graph(minimized, "Minimized DFA", start_state=start_state, part_map=part_map)
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
    st.write(f"Start partition: **{start_p}**")
    final_parts = sorted({part_map[s] for s in finals if s in part_map})
    st.write(f"Final partitions: **{final_parts}**")
