from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", ROOT_DIR / "uploads"))
DEMO_DATA_DIR = Path(os.getenv("DEMO_DATA_DIR", ROOT_DIR / "demo_data"))
DATA_DIR = ROOT_DIR / "data"
GRAPH_STATE_PATH = Path(os.getenv("GRAPH_STATE_PATH", DATA_DIR / "graph_state.json"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
GRAPH_BACKEND = os.getenv("GRAPH_BACKEND", "local").lower()
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

ALLOWED_FILES = {
    "assets.csv",
    "lineage.csv",
    "teams.csv",
    "business_terms.csv",
    "models.csv",
    "column_lineage.csv",
}

DEPENDENCY_RELATIONSHIPS = {"FEEDS", "DERIVED_FROM", "USED_BY"}
MODEL_RELATIONSHIPS = {"TRAINED_ON"}
TRAVERSABLE_RELATIONSHIPS = DEPENDENCY_RELATIONSHIPS | MODEL_RELATIONSHIPS
