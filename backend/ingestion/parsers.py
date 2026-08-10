import csv
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key.strip(): (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "y", "1", "certified"}


def parse_columns(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def load_source_files(directory: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        "assets": read_csv(directory / "assets.csv"),
        "lineage": read_csv(directory / "lineage.csv"),
        "teams": read_csv(directory / "teams.csv"),
        "business_terms": read_csv(directory / "business_terms.csv"),
        "models": read_csv(directory / "models.csv"),
        "column_lineage": read_csv(directory / "column_lineage.csv"),
    }
