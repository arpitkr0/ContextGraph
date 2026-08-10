import re

from backend import tools


def _asset_from_question(question: str, known_assets: list[str]) -> str | None:
    normalized = question.lower().replace(" ", "_")
    for name in sorted(known_assets, key=len, reverse=True):
        if name.lower() in normalized:
            return name
    return None


def _column_from_question(question: str) -> tuple[str, str] | tuple[None, None]:
    match = re.search(r"([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", question)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _confidence(paths: list[list[str]], missing: list[str], fallback: bool) -> dict:
    if missing or not paths:
        level = "LOW"
    elif fallback:
        level = "MEDIUM"
    else:
        level = "HIGH"
    assets = {node.split(".")[0] for path in paths for node in path}
    return {
        "level": level,
        "paths_traversed": len(paths),
        "assets_verified": len(assets),
        "missing_references": len(missing),
    }


def _evidence(paths: list[list[str]], level: str) -> list[dict]:
    return [{"path": path, "level": level} for path in paths]


def answer_question(question: str) -> dict:
    q = question.lower()
    state = tools.store.load()
    known_assets = list(state.assets)
    tool_calls: list[str] = []

    if "what does" in q or "define" in q or "business term" in q:
        term = question.replace("?", "").split("does")[-1].replace("mean", "").strip() if "does" in q else question
        result = tools.get_business_term(term)
        tool_calls.append("get_business_term")
        term_data = result["business_term"]
        if not term_data:
            return _final("I cannot establish that definition from the uploaded business glossary.", tool_calls, [], "none", [term], False)
        answer = f"{term_data['term']} means: {term_data['definition']}. Domain: {term_data.get('domain') or 'unknown'}. Owner: {term_data.get('owner') or 'unknown'}."
        if term_data.get("maps_to_asset"):
            answer += f" It maps to `{term_data['maps_to_asset']}`."
        return _final(answer, tool_calls, [[term_data.get("maps_to_asset")]] if term_data.get("maps_to_asset") else [], "asset", [], False)

    if "trust" in q or "certified" in q or "quality" in q or "sensitive" in q or "pii" in q:
        if "feed" in q or "upstream" in q:
            asset = _asset_from_question(question, known_assets)
            result = tools.get_upstream(asset) if asset else {"paths": [], "level": "none", "missing": ["asset"], "fallback": False}
            tool_calls.append("get_upstream")
            pii_assets = []
            for path in result["paths"]:
                for node in path:
                    asset_name = node.split(".")[0]
                    details = tools.store.get_asset(asset_name)
                    if details and details["sensitivity"] == "PII":
                        pii_assets.append(asset_name)
            if not pii_assets:
                answer = "I cannot establish any PII upstream assets from the uploaded metadata."
            else:
                answer = f"PII upstream assets feeding `{asset}`: {', '.join(sorted(set(pii_assets)))}."
            return _final(answer, tool_calls, result["paths"], result["level"], result["missing"], result["fallback"])
        asset = _asset_from_question(question, known_assets)
        result = tools.get_quality(asset) if asset else {"missing": ["asset"]}
        tool_calls.append("get_quality")
        if result.get("missing"):
            return _final("I cannot establish trust because the asset is missing from metadata.", tool_calls, [], "none", result["missing"], False)
        answer = (
            f"`{result['name']}` is {'certified' if result['certified'] else 'not certified'}, "
            f"owned by {result['owner']}, freshness `{result['freshness']}`, "
            f"sensitivity `{result['sensitivity']}`, downstream usage {result['downstream_usage_count']}."
        )
        return _final(answer, tool_calls, [[result["name"]]], "asset", [], False)

    column_asset, column = _column_from_question(question)
    if "break" in q or "impact" in q or "downstream" in q:
        asset = column_asset or _asset_from_question(question, known_assets)
        result = tools.get_downstream(asset, column)
        tool_calls.append("get_downstream")
        if result["missing"] or not result["paths"]:
            return _final(f"I found `{asset}`, but downstream lineage is not present. I cannot reliably determine impact.", tool_calls, result["paths"], result["level"], result["missing"], result["fallback"])
        answer = f"Changing `{asset}{'.' + column if column else ''}` could affect: " + "; ".join(" -> ".join(path) for path in result["paths"]) + "."
        if result["fallback"]:
            answer += " Column-level lineage was not present, so this is asset-level impact only."
        return _final(answer, tool_calls, result["paths"], result["level"], result["missing"], result["fallback"])

    if "feed" in q or "upstream" in q or "depend" in q or "train" in q:
        asset = _asset_from_question(question, known_assets)
        result = tools.get_upstream(asset, column_asset and column)
        tool_calls.append("get_upstream")
        if result["missing"] or not result["paths"]:
            return _final(f"I found `{asset}`, but its upstream lineage is not present. I cannot reliably determine its dependencies.", tool_calls, result["paths"], result["level"], result["missing"], result["fallback"])
        answer = f"`{asset}` depends on: " + "; ".join(" -> ".join(path) for path in result["paths"]) + "."
        return _final(answer, tool_calls, result["paths"], result["level"], result["missing"], result["fallback"])

    # Off-topic guardrail: only fall back to search if the question
    # references a known asset or contains data-related keywords.
    DATA_KEYWORDS = {
        "table", "column", "dashboard", "model", "dataset", "pipeline",
        "report", "metric", "schema", "field", "source", "data", "asset",
        "lineage", "owner", "certified", "query", "etl", "warehouse",
        "database", "feed", "join", "transform", "ingest", "csv", "sql",
    }
    asset_mentioned = _asset_from_question(question, known_assets)
    has_data_keyword = any(kw in q for kw in DATA_KEYWORDS)

    if not asset_mentioned and not has_data_keyword:
        return _final(
            "I can only answer questions about data assets, lineage, and business terms in your uploaded metadata. "
            "Please ask about a specific table, dashboard, model, or business term.",
            ["off_topic_guard"], [], "none", [], False,
        )

    result = tools.search_assets(question)
    tool_calls.append("search_assets")
    if not result["assets"]:
        return _final("I cannot establish an answer from the uploaded metadata.", tool_calls, [], "none", ["no_matches"], False)
    names = ", ".join(asset["name"] for asset in result["assets"][:5])
    return _final(f"Relevant assets from metadata: {names}.", tool_calls, [[asset["name"]] for asset in result["assets"][:5]], "asset", [], False)


def _final(answer: str, tool_calls: list[str], paths: list[list[str]], level: str, missing: list[str], fallback: bool) -> dict:
    unique_paths = []
    seen = set()
    for path in paths:
        key = tuple(path)
        if key not in seen:
            seen.add(key)
            unique_paths.append(path)
    if unique_paths != paths:
        answer = answer.replace("; ".join(" -> ".join(path) for path in paths), "; ".join(" -> ".join(path) for path in unique_paths))
    return {
        "answer": answer,
        "tool_calls": tool_calls,
        "evidence": _evidence(unique_paths, level),
        "confidence": _confidence(unique_paths, missing, fallback),
    }
