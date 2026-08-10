from backend.stores.graph_store import GraphStore


store = GraphStore()


def search_assets(query: str) -> dict:
    return {"assets": store.search_assets(query)}


def get_asset(name: str) -> dict:
    asset = store.get_asset(name)
    return {"asset": asset, "missing": [] if asset else [name]}


def get_upstream(name: str, column: str | None = None) -> dict:
    return store.traverse(name, "upstream", column)


def get_downstream(name: str, column: str | None = None) -> dict:
    return store.traverse(name, "downstream", column)


def find_related_assets(name: str) -> dict:
    return {"assets": store.related_assets(name)}


def get_quality(name: str) -> dict:
    asset = store.get_asset(name)
    if not asset:
        return {"missing": [name]}
    usage_count = len(asset["downstream"])
    return {
        "name": name,
        "certified": asset["certified"],
        "freshness": asset["freshness"],
        "owner": asset["owner"],
        "sensitivity": asset["sensitivity"],
        "downstream_usage_count": usage_count,
    }


def get_business_term(term: str) -> dict:
    result = store.business_term(term)
    return {"business_term": result, "missing": [] if result else [term]}
