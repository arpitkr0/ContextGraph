import streamlit as st
from frontend.graph_render import render_graph

def render_chat_tab(api):
    question = st.text_input("Question", value="What could break if I change customers.customer_id?")
    if st.button("Ask", type="primary"):
        try:
            result = api("POST", "/ask", json={"question": question})
            st.subheader("Answer")
            st.write(result["answer"])
            
            st.subheader("Evidence")
            evidence_summary = (
                f"confidence: {result['confidence']['level']}\n"
                f"[OK] {result['confidence']['paths_traversed']} graph paths traversed\n"
                f"[OK] {result['confidence']['assets_verified']} assets verified\n"
            )
            if result['confidence']['missing_references'] > 0:
                evidence_summary += f"[!!] {result['confidence']['missing_references']} missing references found\n"
            else:
                evidence_summary += "[OK] 0 missing references\n"
            
            st.code(evidence_summary, language="text")
            
            paths = []
            for item in result.get("evidence", []):
                st.code(" -> ".join(node for node in item["path"] if node), language="text")
                paths.append(item["path"])
                
            if paths:
                # Get full graph to filter down to subgraph
                full_graph = api("GET", "/graph/full")
                
                # Filter for only traversed nodes/edges
                evidence_nodes = set()
                evidence_edges = set()
                for path in paths:
                    for i in range(len(path)):
                        evidence_nodes.add(path[i].split(".")[0])
                    for i in range(len(path) - 1):
                        src = path[i].split(".")[0]
                        tgt = path[i+1].split(".")[0]
                        evidence_edges.add((src, tgt))
                        
                sub_nodes = [n for n in full_graph["nodes"] if n["name"] in evidence_nodes]
                sub_edges = [e for e in full_graph["edges"] if (e["source"], e["target"]) in evidence_edges]
                
                st.subheader("Evidence Subgraph")
                render_graph(sub_nodes, sub_edges, evidence_paths=paths, height="400px")
                
        except Exception as exc:
            st.error(str(exc))
