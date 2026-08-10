from fastapi import APIRouter, HTTPException

from backend.stores.graph_store import GraphStore


router = APIRouter()
store = GraphStore()


@router.get("/asset/{name}")
def asset(name: str) -> dict:
    result = store.get_asset(name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Asset '{name}' not found")
    return result


@router.get("/business-term/{term}")
def business_term(term: str) -> dict:
    result = store.business_term(term)
    if not result:
        raise HTTPException(status_code=404, detail=f"Business term '{term}' not found")
    return result
