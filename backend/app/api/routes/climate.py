from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    ClimateCellDetailResponse,
    ClimateInteractionRequest,
    ClimateInteractionResponse,
    ClimateRasterSample,
    ClimateSurfaceResponse,
    ClimateTimelineResponse,
)
from app.services.climate_data.climate_surface_service import (
    generate_climate_surface,
    get_climate_cell_detail,
)
from app.services.climate_data.climate_raster_service import sample_climate_raster
from app.services.climate_interaction_engine import compute_composite_risk
from app.services.climate_timeline import generate_climate_timeline


router = APIRouter(prefix="/api/climate", tags=["climate"])


@router.get("/raster-sample", response_model=ClimateRasterSample)
def raster_sample(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    layer_type: str = "heat_stress",
) -> ClimateRasterSample:
    sample = sample_climate_raster(
        latitude=lat,
        longitude=lon,
        layer_type=layer_type,
    )

    if not sample:
        raise HTTPException(status_code=404, detail="Climate raster layer not found")

    return sample


@router.get("/surface", response_model=ClimateSurfaceResponse)
def climate_surface(
    bbox: str = Query(
        description="Viewport bbox formatted as west,south,east,north",
    ),
    zoom: float = Query(ge=0, le=22),
    layer_type: str = "heat_risk",
    warming_level: float = Query(default=1.7, ge=1.0, le=4.0),
    year: int = Query(default=2030, ge=2025, le=2100),
    season: str = "Summer",
) -> ClimateSurfaceResponse:
    try:
        parsed_bbox = [float(value) for value in bbox.split(",")]
        return generate_climate_surface(
            bbox=parsed_bbox,
            zoom=zoom,
            layer_type=layer_type,
            warming_level=warming_level,
            year=year,
            season=season,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/cell-detail", response_model=ClimateCellDetailResponse)
def climate_cell_detail(
    grid_cell_id: str,
    layer_type: str = "heat_risk",
    year: int = Query(default=2030, ge=2025, le=2100),
    warming_level: float = Query(default=1.7, ge=1.0, le=4.0),
    season: str = "Summer",
) -> ClimateCellDetailResponse:
    return get_climate_cell_detail(
        grid_cell_id=grid_cell_id,
        layer_type=layer_type,
        year=year,
        warming_level=warming_level,
        season=season,
    )


@router.get("/timeline", response_model=ClimateTimelineResponse)
def climate_timeline(
    location: str,
    start_year: int = Query(default=2025, ge=2025, le=2100),
    end_year: int = Query(default=2100, ge=2025, le=2100),
    warming_pathway: str = "moderate",
    layer_type: str = "heat_risk",
    season: str = "Summer",
) -> ClimateTimelineResponse:
    try:
        return generate_climate_timeline(
            location=location,
            start_year=start_year,
            end_year=end_year,
            warming_pathway=warming_pathway,
            layer_type=layer_type,
            season=season,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/composite-risk", response_model=ClimateInteractionResponse)
def climate_composite_risk(
    payload: ClimateInteractionRequest,
) -> ClimateInteractionResponse:
    return compute_composite_risk(payload)
