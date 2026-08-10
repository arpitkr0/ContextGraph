from backend.config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USERNAME, TRAVERSABLE_RELATIONSHIPS
from backend.models import Asset, BusinessTerm, ColumnEdge, Edge, GraphState


def _driver():
    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise RuntimeError("Neo4j backend selected, but the neo4j Python package is not installed.") from exc
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def _label(value: str) -> str:
    cleaned = "".join(ch for ch in value if ch.isalnum())
    return cleaned or "Asset"


def _rel(value: str) -> str:
    cleaned = "".join(ch for ch in value.upper() if ch.isalnum() or ch == "_")
    if cleaned not in TRAVERSABLE_RELATIONSHIPS and cleaned not in {"COLUMN_FEEDS", "DEFINED_BY", "OWNED_BY"}:
        raise ValueError(f"Unsupported Neo4j relationship type: {value}")
    return cleaned


def write_state(state: GraphState) -> None:
    with _driver() as driver:
        with driver.session() as session:
            session.execute_write(_write_state_tx, state)


def _write_state_tx(tx, state: GraphState) -> None:
    tx.run("MATCH (n) DETACH DELETE n")
    tx.run(
        """
        CREATE (:GraphMeta {
            id: 'current',
            last_rebuilt: $last_rebuilt,
            warnings: $warnings
        })
        """,
        last_rebuilt=state.last_rebuilt,
        warnings=state.warnings,
    )
    for asset in state.assets.values():
        props = vars(asset) | {"columns": asset.columns}
        tx.run(
            f"MERGE (a:Asset:{_label(asset.type)} {{name: $name}}) SET a += $props",
            name=asset.name,
            props=props,
        )
        if asset.owner in state.teams:
            team = state.teams[asset.owner]
            tx.run(
                """
                MERGE (t:Team {name: $team_name})
                SET t.contact = $contact, t.description = $description
                WITH t
                MATCH (a:Asset {name: $asset_name})
                MERGE (a)-[:OWNED_BY]->(t)
                """,
                team_name=asset.owner,
                contact=team.get("contact", ""),
                description=team.get("description", ""),
                asset_name=asset.name,
            )
    for edge in state.edges:
        tx.run(
            f"""
            MATCH (source:Asset {{name: $source}})
            MATCH (target:Asset {{name: $target}})
            MERGE (source)-[r:{_rel(edge.relationship_type)}]->(target)
            SET r.relationship_type = $relationship_type
            """,
            source=edge.source,
            target=edge.target,
            relationship_type=edge.relationship_type,
        )
    for edge in state.column_edges:
        tx.run(
            """
            MATCH (source_asset:Asset {name: $source_asset})
            MATCH (target_asset:Asset {name: $target_asset})
            MERGE (source_column:Column {id: $source_id})
            SET source_column.name = $source_column,
                source_column.asset_name = $source_asset
            MERGE (target_column:Column {id: $target_id})
            SET target_column.name = $target_column,
                target_column.asset_name = $target_asset
            MERGE (source_asset)-[:HAS_COLUMN]->(source_column)
            MERGE (target_asset)-[:HAS_COLUMN]->(target_column)
            MERGE (source_column)-[:COLUMN_FEEDS]->(target_column)
            """,
            source_asset=edge.source_asset,
            source_column=edge.source_column,
            target_asset=edge.target_asset,
            target_column=edge.target_column,
            source_id=edge.source_id,
            target_id=edge.target_id,
        )
    for term in state.business_terms.values():
        tx.run(
            """
            MERGE (term:BusinessTerm {term: $term})
            SET term.definition = $definition,
                term.domain = $domain,
                term.owner = $owner,
                term.maps_to_asset = $maps_to_asset
            """,
            **vars(term),
        )
        if term.maps_to_asset in state.assets:
            tx.run(
                """
                MATCH (term:BusinessTerm {term: $term})
                MATCH (asset:Asset {name: $asset})
                MERGE (term)-[:DEFINED_BY]->(asset)
                """,
                term=term.term,
                asset=term.maps_to_asset,
            )


def read_state() -> GraphState:
    with _driver() as driver:
        with driver.session() as session:
            assets = {
                record["name"]: Asset(
                    name=record["name"],
                    type=record["type"],
                    owner=record.get("owner") or "",
                    description=record.get("description") or "",
                    certified=bool(record.get("certified")),
                    freshness=record.get("freshness") or "",
                    columns=record.get("columns") or [],
                    sensitivity=record.get("sensitivity") or "INTERNAL",
                )
                for record in session.run(
                    """
                    MATCH (a:Asset)
                    RETURN a.name AS name, a.type AS type, a.owner AS owner,
                           a.description AS description, a.certified AS certified,
                           a.freshness AS freshness, a.columns AS columns,
                           a.sensitivity AS sensitivity
                    """
                )
            }
            edges = [
                Edge(source=record["source"], target=record["target"], relationship_type=record["relationship_type"])
                for record in session.run(
                    """
                    MATCH (source:Asset)-[r]->(target:Asset)
                    WHERE type(r) IN ['FEEDS', 'DERIVED_FROM', 'USED_BY', 'TRAINED_ON']
                    RETURN source.name AS source, target.name AS target, type(r) AS relationship_type
                    """
                )
            ]
            column_edges = [
                ColumnEdge(
                    source_asset=record["source_asset"],
                    source_column=record["source_column"],
                    target_asset=record["target_asset"],
                    target_column=record["target_column"],
                )
                for record in session.run(
                    """
                    MATCH (source:Column)-[:COLUMN_FEEDS]->(target:Column)
                    RETURN source.asset_name AS source_asset, source.name AS source_column,
                           target.asset_name AS target_asset, target.name AS target_column
                    """
                )
            ]
            teams = {
                record["name"]: {"contact": record.get("contact") or "", "description": record.get("description") or ""}
                for record in session.run("MATCH (t:Team) RETURN t.name AS name, t.contact AS contact, t.description AS description")
            }
            terms = {
                record["term"].lower(): BusinessTerm(
                    term=record["term"],
                    definition=record.get("definition") or "",
                    domain=record.get("domain") or "",
                    owner=record.get("owner") or "",
                    maps_to_asset=record.get("maps_to_asset") or "",
                )
                for record in session.run(
                    """
                    MATCH (term:BusinessTerm)
                    RETURN term.term AS term, term.definition AS definition,
                           term.domain AS domain, term.owner AS owner,
                           term.maps_to_asset AS maps_to_asset
                    """
                )
            }
            meta = session.run("MATCH (m:GraphMeta {id: 'current'}) RETURN m.last_rebuilt AS last_rebuilt, m.warnings AS warnings").single()
            return GraphState(
                assets=assets,
                edges=edges,
                column_edges=column_edges,
                teams=teams,
                business_terms=terms,
                warnings=(meta["warnings"] if meta else []),
                last_rebuilt=(meta["last_rebuilt"] if meta else ""),
            )
