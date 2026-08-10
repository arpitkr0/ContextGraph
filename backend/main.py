from fastapi import FastAPI

from backend.routes.ask import router as ask_router
from backend.routes.asset import router as asset_router
from backend.routes.upload import router as upload_router
from backend.routes.graph import router as graph_router
from backend.routes.health import router as health_router


app = FastAPI(title="ContextGraph")

app.include_router(health_router)
app.include_router(ask_router)
app.include_router(asset_router)
app.include_router(upload_router)
app.include_router(graph_router)
