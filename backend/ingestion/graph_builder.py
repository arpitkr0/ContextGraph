from datetime import datetime, timezone
import json
from uuid import uuid4

from backend.config import GRAPH_BACKEND, GRAPH_STATE_PATH
from backend.ingestion.parsers import load_source_files, parse_bool, parse_columns
from backend.ingestion.validators import validate_rows
from backend.models import Asset, BusinessTerm, ColumnEdge, Edge, GraphState
from backend.stores import neo4j_store


def build_state_from_sources(source_path) -> GraphState:
    raw = load_source_files(source_path)
    errors, warnings = validate_rows(raw)
    if errors:
        raise ValueError("; ".join(errors))

    assets: dict[str, Asset] = {}
    for row in raw["assets"]:
        sensitivity = (row.get("sensitivity") or "INTERNAL").upper()
        assets[row["name"]] = Asset(
            name=row["name"],
            type=row.get("type", "Table"),
            owner=row.get("owner", ""),
            description=row.get("description", ""),
            certified=parse_bool(row.get("certified", "")),
            freshness=row.get("freshness", ""),
            columns=parse_columns(row.get("columns", "")),
            sensitivity=sensitivity,
        )

    for row in raw["models"]:
        trained_on = row.get("trained_on", "")
        assets[row["name"]] = Asset(
            name=row["name"],
            type="MLModel",
            owner=row.get("owner", ""),
            description=row.get("description", ""),
            certified=parse_bool(row.get("certified", "")),
            freshness=row.get("freshness", ""),
            columns=[],
            sensitivity=(row.get("sensitivity") or "INTERNAL").upper(),
        )
        if trained_on:
            raw["lineage"].append({"source": row["name"], "target": trained_on, "relationship_type": "TRAINED_ON"})

    edges = [
        Edge(source=row["source"], target=row["target"], relationship_type=row["relationship_type"].upper())
        for row in raw["lineage"]
    ]
    column_edges = [ColumnEdge(**row) for row in raw["column_lineage"]]

    connected = {item for edge in edges for item in (edge.source, edge.target)}
    for name in sorted(set(assets) - connected):
        warnings.append(f"asset '{name}' has no asset-level relationships")

    teams = {
        row["team_name"]: {"contact": row.get("contact", ""), "description": row.get("description", "")}
        for row in raw["teams"]
        if row.get("team_name")
    }
    terms = {
        row["term"].lower(): BusinessTerm(
            term=row["term"],
            definition=row.get("definition", ""),
            domain=row.get("domain", ""),
            owner=row.get("owner", ""),
            maps_to_asset=row.get("maps_to_asset", ""),
        )
        for row in raw["business_terms"]
        if row.get("term")
    }
    return GraphState(
        assets=assets,
        edges=edges,
        column_edges=column_edges,
        teams=teams,
        business_terms=terms,
        warnings=warnings,
        last_rebuilt=datetime.now(timezone.utc).isoformat(),
    )


def replace_graph_state(new_state: GraphState) -> GraphState:
    if GRAPH_BACKEND == "neo4j":
        neo4j_store.write_state(new_state)
    GRAPH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = GRAPH_STATE_PATH.with_name(f"{GRAPH_STATE_PATH.stem}.{uuid4().hex}.tmp")
    tmp_path.write_text(json.dumps(new_state.to_json(), indent=2), encoding="utf-8")
    tmp_path.replace(GRAPH_STATE_PATH)
    return new_state
