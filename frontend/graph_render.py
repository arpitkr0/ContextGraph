import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network


TYPE_COLORS = {
    "Table": "#4CAF50",
    "Dashboard": "#2196F3",
    "MLModel": "#9C27B0",
    "Team": "#FF9800",
    "BusinessTerm": "#FFC107",
}

EVIDENCE_COLOR = "#FF4B4B"
DEFAULT_EDGE_COLOR = "#555555"


def render_graph(nodes_data, edges_data, evidence_paths=None, height="600px"):
    """Render an interactive graph using pyvis embedded in Streamlit."""

    # Collect evidence info for highlighting
    evidence_edges = set()
    evidence_nodes = set()
    if evidence_paths:
        for path in evidence_paths:
            for node in path:
                evidence_nodes.add(node.split(".")[0])
            for i in range(len(path) - 1):
                src = path[i].split(".")[0]
                tgt = path[i + 1].split(".")[0]
                evidence_edges.add((src, tgt))

    net = Network(
        height=height,
        width="100%",
        directed=True,
        bgcolor="#0E1117",
        font_color="white",
        layout="hierarchical",
    )

    # Configure hierarchical layout (Left-to-Right for lineage flow)
    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "LR",
          "sortMethod": "directed",
          "levelSeparation": 250,
          "nodeSpacing": 150
        }
      },
      "physics": {
        "enabled": false
      },
      "edges": {
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.6 } },
        "smooth": { "type": "cubicBezier", "forceDirection": "horizontal" },
        "font": { "size": 10, "color": "#AAAAAA", "strokeWidth": 0, "align": "middle" }
      },
      "nodes": {
        "font": { "size": 14, "color": "white", "strokeWidth": 0 },
        "borderWidth": 2,
        "borderWidthSelected": 3
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200
      }
    }
    """)

    # Add nodes
    for n in nodes_data:
        name = n["name"]
        ntype = n.get("type", "")
        color = TYPE_COLORS.get(ntype, "#888888")
        certified = n.get("certified", False)
        owner = n.get("owner", "")

        border_color = "#FFFFFF" if certified else color
        label = name
        title = f"<b>{name}</b><br>Type: {ntype}<br>Owner: {owner}<br>Certified: {'✓' if certified else '✗'}"

        net.add_node(
            name,
            label=label,
            title=title,
            color={
                "background": color,
                "border": border_color,
                "highlight": {"background": color, "border": "#FFFFFF"},
            },
            size=22,
            shape="dot",
        )

    # Add edges
    for e in edges_data:
        source = e["source"]
        target = e["target"]
        rel = e.get("relationship_type", "")
        is_evidence = (source, target) in evidence_edges

        net.add_edge(
            source,
            target,
            label=rel,
            color=EVIDENCE_COLOR if is_evidence else DEFAULT_EDGE_COLOR,
            width=4 if is_evidence else 1,
        )

    # Generate HTML and embed
    html = net.generate_html()
    components.html(html, height=int(height.replace("px", "")) + 20, scrolling=False)
