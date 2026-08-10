# ContextGraph

ContextGraph is a local AI data-context prototype: uploaded metadata CSVs become a deterministic graph, tools query that graph, and the `/ask` endpoint answers only from evidence it can prove.

## What It Builds

- CSV ingestion for `assets.csv`, `lineage.csv`, optional `teams.csv`, `business_terms.csv`, `models.csv`, and `column_lineage.csv`
- Atomic rebuild behavior: invalid uploads never destroy the last known-good graph
- Column-aware upstream/downstream tools with explicit fallback when column lineage is missing
- Sensitivity metadata (`PUBLIC`, `INTERNAL`, `PII`, `CONFIDENTIAL`) as queryable governance context
- Evidence summaries and `HIGH` / `MEDIUM` / `LOW` confidence on every answer
- FastAPI backend and Streamlit UI with upload, chat, full graph, and evidence graph views

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/generate_assets.py
python -m backend.bootstrap
uvicorn backend.api:app --reload
```

In another terminal:

```powershell
streamlit run frontend/app.py
```

Backend: `http://127.0.0.1:8000`

Frontend: `http://localhost:8501`

## Neo4j Mode

The app can run against Neo4j instead of the local JSON graph store.

```powershell
docker compose up neo4j -d
$env:GRAPH_BACKEND="neo4j"
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USERNAME="neo4j"
$env:NEO4J_PASSWORD="contextgraph-password"
python -m backend.bootstrap
uvicorn backend.api:app --reload
```

## Demo Questions

- `What tables feed the revenue dashboard?`
- `What could break if I change customers.customer_id?`
- `Can I trust churn_features?`
- `What does Revenue mean?`
- `Which PII tables feed the revenue dashboard?`
- `What trains customer_churn_model?`

## API

- `POST /ask`
- `GET /asset/{name}`
- `GET /business-term/{term}`
- `POST /upload`
- `DELETE /upload/{filename}`
- `GET /sources`
- `POST /rebuild-graph`
- `POST /reset-demo`
- `GET /graph/status`
- `GET /graph/full`
- `GET /health`

## Notes

The default graph store is local JSON so the project runs immediately without external services. Set `GRAPH_BACKEND=neo4j` to make rebuilds write to Neo4j and make graph tools read from Neo4j.
