from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.region import router as region_router
from app.api.routes.scenario import router as scenario_router
from app.api.routes.search import router as search_router

app = FastAPI(title="Future Cities AI API")

app.include_router(health_router)
app.include_router(search_router)
app.include_router(scenario_router)
app.include_router(region_router)
