from backend.config import TRAVERSABLE_RELATIONSHIPS


REQUIRED_COLUMNS = {
    "assets": {"name", "type", "owner", "description", "certified", "freshness", "columns"},
    "lineage": {"source", "target", "relationship_type"},
    "teams": {"team_name", "contact", "description"},
    "business_terms": {"term", "definition", "maps_to_asset"},
    "models": {"name", "owner", "trained_on", "description", "certified"},
    "column_lineage": {"source_asset", "source_column", "target_asset", "target_column"},
}


def validate_required_columns(filename_key: str, rows: list[dict[str, str]], errors: list[str]) -> None:
    if not rows:
        return
    missing = REQUIRED_COLUMNS[filename_key] - set(rows[0])
    if missing:
        errors.append(f"{filename_key}.csv missing required columns: {sorted(missing)}")


def validate_rows(raw: dict[str, list[dict[str, str]]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not raw["assets"]:
        errors.append("assets.csv is required and must contain at least one asset")
    if not raw["lineage"]:
        errors.append("lineage.csv is required and must contain at least one relationship")
    for key, rows in raw.items():
        validate_required_columns(key, rows, errors)

    names: set[str] = set()
    for index, row in enumerate(raw["assets"], start=2):
        name = row.get("name", "")
        if not name:
            errors.append(f"assets.csv row {index}: name is required")
        if name in names:
            errors.append(f"assets.csv row {index}: duplicate asset '{name}'")
        names.add(name)

    for index, row in enumerate(raw["models"], start=2):
        name = row.get("name", "")
        if name and name in names:
            errors.append(f"models.csv row {index}: duplicate asset/model '{name}'")
        if name:
            names.add(name)

    for index, row in enumerate(raw["lineage"], start=2):
        rel = row.get("relationship_type", "").upper()
        if row.get("source") not in names:
            errors.append(f"lineage.csv row {index}: source '{row.get('source')}' not found")
        if row.get("target") not in names:
            errors.append(f"lineage.csv row {index}: target '{row.get('target')}' not found")
        if rel not in TRAVERSABLE_RELATIONSHIPS:
            errors.append(f"lineage.csv row {index}: unsupported relationship_type '{rel}'")

    for index, row in enumerate(raw["business_terms"], start=2):
        target = row.get("maps_to_asset", "")
        if target and target not in names:
            warnings.append(f"business_terms.csv row {index}: maps_to_asset '{target}' not found")

    for index, row in enumerate(raw["column_lineage"], start=2):
        for field in ("source_asset", "target_asset"):
            if row.get(field) not in names:
                errors.append(f"column_lineage.csv row {index}: {field} '{row.get(field)}' not found")

    return errors, warnings
