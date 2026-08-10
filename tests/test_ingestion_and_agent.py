from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.agent import answer_question
from backend.bootstrap import main as bootstrap
from backend.config import GRAPH_STATE_PATH, UPLOAD_DIR
from backend.ingestion.file_manager import reset_to_demo
from backend.ingestion.graph_builder import build_state_from_sources
from backend.stores.graph_store import GraphStore


def setup_module():
    bootstrap()


def test_demo_graph_has_column_lineage_and_sensitivity():
    state = GraphStore().load()
    assert "customers" in state.assets
    assert state.assets["customers"].sensitivity == "PII"
    assert len(state.column_edges) >= 4


def test_column_impact_reaches_two_dashboards_and_model():
    result = answer_question("What could break if I change customers.customer_id?")
    assert result["confidence"]["level"] == "HIGH"
    assert "revenue_dashboard" in result["answer"]
    assert "customer_dashboard" in result["answer"]
    assert "customer_churn_model" in result["answer"]


def test_missing_lineage_is_low_confidence():
    result = answer_question("What feeds unknown_dashboard?")
    assert result["confidence"]["level"] == "LOW"
    assert "cannot reliably" in result["answer"]


def test_invalid_rebuild_does_not_replace_last_good_graph(tmp_path):
    reset_to_demo()
    before = GRAPH_STATE_PATH.read_text(encoding="utf-8")
    bad = tmp_path / "sources"
    bad.mkdir()
    shutil.copy2(UPLOAD_DIR / "assets.csv", bad / "assets.csv")
    (bad / "lineage.csv").write_text("source,target,relationship_type\ncustomers,missing_table,FEEDS\n", encoding="utf-8")
    try:
        build_state_from_sources(bad)
    except ValueError:
        pass
    assert GRAPH_STATE_PATH.read_text(encoding="utf-8") == before
