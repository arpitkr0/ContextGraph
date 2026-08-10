import streamlit as st
from frontend.graph_render import render_graph

def render_explore_tab(api):
    try:
        graph = api("GET", "/graph/full")
        owners = sorted({node["owner"] for node in graph["nodes"] if node.get("owner")})
        types = sorted({node.get("type") for node in graph["nodes"] if node.get("type")})
        
        filters = st.columns(3)
        selected_type = filters[0].selectbox("Type", ["All"] + types)
        selected_owner = filters[1].selectbox("Owner", ["All"] + owners)
        certified_only = filters[2].checkbox("Certified only")
        
        params = {}
        if selected_type != "All":
            params["type"] = selected_type
        if selected_owner != "All":
            params["owner"] = selected_owner
        if certified_only:
            params["certified"] = "true"
            
        graph = api("GET", "/graph/full", params=params)
        
        render_graph(graph["nodes"], graph["edges"], height="600px")
        
        selected = st.selectbox("Inspect asset", [""] + [node["name"] for node in graph["nodes"]])
        if selected:
            st.json(api("GET", f"/asset/{selected}"))
    except Exception as exc:
        st.error(str(exc))
