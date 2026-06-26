from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.advisor import router as advisor_router
from app.api.routes.climate import router as climate_router
from app.api.routes.data_pipeline import router as data_pipeline_router
from app.api.routes.explain import router as explain_router
from app.api.routes.environment import router as environment_router
from app.api.routes.health import router as health_router
from app.api.routes.region import router as region_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.saved_scenarios import router as saved_scenarios_router
from app.api.routes.scenario import router as scenario_router
from app.api.routes.search import router as search_router
from app.api.routes.spatial import router as spatial_router

app = FastAPI(title="Future Cities AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(advisor_router)
app.include_router(search_router)
app.include_router(spatial_router)
app.include_router(scenario_router)
app.include_router(region_router)
app.include_router(admin_router)
app.include_router(climate_router)
app.include_router(data_pipeline_router)
app.include_router(environment_router)
app.include_router(explain_router)
app.include_router(recommendations_router)
app.include_router(saved_scenarios_router)
