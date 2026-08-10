from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Asset:
    name: str
    type: str
    owner: str = ""
    description: str = ""
    certified: bool = False
    freshness: str = ""
    columns: list[str] = field(default_factory=list)
    sensitivity: str = "INTERNAL"


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relationship_type: str


@dataclass(frozen=True)
class ColumnEdge:
    source_asset: str
    source_column: str
    target_asset: str
    target_column: str

    @property
    def source_id(self) -> str:
        return f"{self.source_asset}.{self.source_column}"

    @property
    def target_id(self) -> str:
        return f"{self.target_asset}.{self.target_column}"


@dataclass(frozen=True)
class BusinessTerm:
    term: str
    definition: str
    domain: str = ""
    owner: str = ""
    maps_to_asset: str = ""


@dataclass
class GraphState:
    assets: dict[str, Asset]
    edges: list[Edge]
    column_edges: list[ColumnEdge]
    teams: dict[str, dict[str, str]]
    business_terms: dict[str, BusinessTerm]
    warnings: list[str]
    last_rebuilt: str

    def to_json(self) -> dict[str, Any]:
        return {
            "assets": {k: vars(v) for k, v in self.assets.items()},
            "edges": [vars(edge) for edge in self.edges],
            "column_edges": [vars(edge) for edge in self.column_edges],
            "teams": self.teams,
            "business_terms": {k: vars(v) for k, v in self.business_terms.items()},
            "warnings": self.warnings,
            "last_rebuilt": self.last_rebuilt,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "GraphState":
        return cls(
            assets={k: Asset(**v) for k, v in data.get("assets", {}).items()},
            edges=[Edge(**edge) for edge in data.get("edges", [])],
            column_edges=[ColumnEdge(**edge) for edge in data.get("column_edges", [])],
            teams=data.get("teams", {}),
            business_terms={k: BusinessTerm(**v) for k, v in data.get("business_terms", {}).items()},
            warnings=data.get("warnings", []),
            last_rebuilt=data.get("last_rebuilt", ""),
        )
