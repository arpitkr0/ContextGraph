import json
from collections import deque

from backend.config import GRAPH_BACKEND, GRAPH_STATE_PATH, TRAVERSABLE_RELATIONSHIPS
from backend.models import GraphState
from backend.stores import neo4j_store


class GraphStore:
    def __init__(self, path=GRAPH_STATE_PATH):
        self.path = path

    def load(self) -> GraphState:
        if GRAPH_BACKEND == "neo4j":
            return neo4j_store.read_state()
        if not self.path.exists():
            raise RuntimeError("Graph has not been built. Run POST /rebuild-graph or python -m backend.bootstrap.")
        return GraphState.from_json(json.loads(self.path.read_text(encoding="utf-8")))

    def status(self) -> dict:
        state = self.load()
        return {
            "assets": len(state.assets),
            "relationships": len(state.edges),
            "column_lineage_edges": len(state.column_edges),
            "last_rebuilt": state.last_rebuilt,
            "warnings": state.warnings,
        }

    def get_asset(self, name: str) -> dict | None:
        state = self.load()
        asset = state.assets.get(name)
        if not asset:
            return None
        upstream = [edge.source for edge in state.edges if edge.target == name and edge.relationship_type != "TRAINED_ON"]
        downstream = [edge.target for edge in state.edges if edge.source == name and edge.relationship_type != "TRAINED_ON"]
        trained_on = [edge.target for edge in state.edges if edge.source == name and edge.relationship_type == "TRAINED_ON"]
        return vars(asset) | {"upstream": upstream, "downstream": downstream, "trained_on": trained_on}

    def search_assets(self, query: str) -> list[dict]:
        state = self.load()
        terms = query.lower().split()
        matches = []
        for asset in state.assets.values():
            haystack = f"{asset.name} {asset.type} {asset.owner} {asset.description} {asset.sensitivity}".lower()
            if all(term in haystack for term in terms) or any(term in haystack for term in terms):
                matches.append(vars(asset))
        return matches[:10]

    def business_term(self, term: str) -> dict | None:
        state = self.load()
        key = term.lower()
        if key in state.business_terms:
            return vars(state.business_terms[key])
        for value in state.business_terms.values():
            if key in value.term.lower():
                return vars(value)
        return None

    def _asset_paths(self, name: str, direction: str) -> list[list[str]]:
        state = self.load()
        paths: list[list[str]] = []
        queue = deque([[name]])
        while queue:
            path = queue.popleft()
            current = path[-1]
            next_nodes = []
            for edge in state.edges:
                if edge.relationship_type not in TRAVERSABLE_RELATIONSHIPS:
                    continue
                if edge.relationship_type == "TRAINED_ON":
                    if direction == "downstream" and edge.target == current:
                        next_nodes.append(edge.source)
                    if direction == "upstream" and edge.source == current:
                        next_nodes.append(edge.target)
                    continue
                if direction == "downstream" and edge.source == current:
                    next_nodes.append(edge.target)
                if direction == "upstream" and edge.target == current:
                    next_nodes.append(edge.source)
            if not next_nodes and len(path) > 1:
                paths.append(path)
            for nxt in next_nodes:
                if nxt not in path:
                    queue.append(path + [nxt])
        return paths

    def _column_paths(self, asset: str, column: str, direction: str) -> list[list[str]]:
        state = self.load()
        start = f"{asset}.{column}"
        paths: list[list[str]] = []
        queue = deque([[start]])
        while queue:
            path = queue.popleft()
            current = path[-1]
            current_asset = current.split(".")[0]
            next_edges = [
                edge for edge in state.column_edges
                if (direction == "downstream" and edge.source_id == current)
                or (direction == "upstream" and edge.target_id == current)
            ]
            if direction == "downstream":
                for edge in state.edges:
                    if edge.source == current_asset and edge.relationship_type == "USED_BY":
                        paths.append(path + [edge.target])
            if not next_edges and len(path) > 1:
                leaf_asset = current_asset
                for asset_path in self._asset_paths(leaf_asset, "downstream" if direction == "downstream" else "upstream"):
                    paths.append(path + asset_path[1:])
                if not any(p[: len(path)] == path for p in paths):
                    paths.append(path)
            for edge in next_edges:
                nxt = edge.target_id if direction == "downstream" else edge.source_id
                if nxt not in path:
                    queue.append(path + [nxt])
        return paths

    def traverse(self, name: str, direction: str, column: str | None = None) -> dict:
        state = self.load()
        if name not in state.assets:
            return {"paths": [], "level": "none", "missing": [name], "fallback": False}
        if column:
            paths = self._column_paths(name, column, direction)
            if paths:
                return {"paths": paths, "level": "column", "missing": [], "fallback": False}
            return {"paths": self._asset_paths(name, direction), "level": "asset", "missing": [], "fallback": True}
        return {"paths": self._asset_paths(name, direction), "level": "asset", "missing": [], "fallback": False}

    def related_assets(self, name: str) -> list[str]:
        paths = self._asset_paths(name, "upstream") + self._asset_paths(name, "downstream")
        return sorted({node for path in paths for node in path if node != name})

    def full_graph(self, asset_type: str | None = None, certified: bool | None = None, owner: str | None = None) -> dict:
        state = self.load()
        nodes = []
        allowed = set()
        for asset in state.assets.values():
            if asset_type and asset.type != asset_type:
                continue
            if certified is not None and asset.certified != certified:
                continue
            if owner and asset.owner != owner:
                continue
            allowed.add(asset.name)
            nodes.append(vars(asset))
        edges = [vars(edge) for edge in state.edges if edge.source in allowed and edge.target in allowed]
        return {"nodes": nodes, "edges": edges}
