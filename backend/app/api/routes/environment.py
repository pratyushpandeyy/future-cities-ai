from fastapi import APIRouter, Query

from app.models.schemas import EnvironmentalContext, OvertureUrbanContext
from app.services.environmental_data import get_environmental_context
from app.services.overture_context import get_overture_urban_context


router = APIRouter(prefix="/api/environment", tags=["environment"])


@router.get("/context", response_model=EnvironmentalContext)
def environmental_context(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
) -> EnvironmentalContext:
    return get_environmental_context(latitude=lat, longitude=lon)


@router.get("/urban-context", response_model=OvertureUrbanContext)
def urban_context(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_degrees: float = Query(default=0.01, gt=0, le=0.1),
) -> OvertureUrbanContext:
    return get_overture_urban_context(
        latitude=lat,
        longitude=lon,
        radius_degrees=radius_degrees,
    )
