from fastapi import APIRouter, HTTPException

from backend.ingestion.file_manager import reset_to_demo, source_dir
from backend.ingestion.graph_builder import build_state_from_sources, replace_graph_state
from backend.stores.graph_store import GraphStore


router = APIRouter()
store = GraphStore()


@router.post("/reset-demo")
def reset_demo() -> dict:
    files = reset_to_demo()
    state = replace_graph_state(build_state_from_sources(source_dir()))
    return {"files": files, "status": "demo_restored", **store.status()}


@router.post("/rebuild-graph")
def rebuild_graph() -> dict:
    try:
        state = build_state_from_sources(source_dir())
        replace_graph_state(state)
        return {"status": "rebuilt", **store.status()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"status": "failed_previous_graph_preserved", "errors": str(exc).split("; ")}) from exc


@router.get("/graph/status")
def graph_status() -> dict:
    return store.status()


@router.get("/graph/full")
def graph_full(type: str | None = None, certified: bool | None = None, owner: str | None = None) -> dict:
    return store.full_graph(type, certified, owner)
