from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    ClimateCellDetailResponse,
    ClimateDataBrokerStatus,
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
from app.services.climate_data.climate_data_broker import (
    climate_data_broker_status,
    sample_climate_data,
)
from app.services.climate_data.climate_raster_service import sample_climate_raster
from app.services.climate_interaction_engine import compute_composite_risk
from app.services.climate_timeline import generate_climate_timeline


router = APIRouter(prefix="/api/climate", tags=["climate"])


@router.get("/providers", response_model=ClimateDataBrokerStatus)
def climate_providers() -> ClimateDataBrokerStatus:
    return climate_data_broker_status()


@router.get("/raster-sample", response_model=ClimateRasterSample)
def raster_sample(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    layer_type: str = "heat_stress",
    year: int | None = Query(default=None, ge=2021, le=2100),
    scenario: str = "ssp245",
    month: int = Query(default=7, ge=1, le=12),
    model: str | None = None,
    resolution: str = "2.5m",
    source: str = Query(
        default="auto",
        pattern="^(auto|worldclim|nasa|demo)$",
    ),
) -> ClimateRasterSample:
    if source == "auto" and year is not None:
        sample = sample_climate_data(
            latitude=lat,
            longitude=lon,
            year=year,
            month=month,
            scenario=scenario,
            variable=worldclim_api_variable(layer_type),
            model=model,
            resolution=resolution,
        )
    elif source == "nasa" and year is not None:
        from app.services.climate_data.climate_data_broker import (
            ClimateDataBroker,
        )
        from app.services.climate_data.providers.base import ClimateDataRequest

        sample = ClimateDataBroker(
            provider_order=("nasa_nex_cog",),
        ).sample(
            ClimateDataRequest(
                latitude=lat,
                longitude=lon,
                year=year,
                month=month,
                scenario=scenario,
                variable=worldclim_api_variable(layer_type),
                model=model,
                resolution=resolution,
            ),
            allow_demo_fallback=False,
        )
    else:
        sample = sample_climate_raster(
            latitude=lat,
            longitude=lon,
            layer_type=layer_type,
            year=year,
            scenario=scenario,
            month=month,
            model=model,
            resolution=resolution,
            prefer_worldclim=source == "worldclim",
        )

        if source == "worldclim" and sample and sample.is_fallback:
            sample = None

    if not sample:
        raise HTTPException(status_code=404, detail="Climate raster layer not found")

    return sample


def worldclim_api_variable(layer_type: str) -> str:
    normalized = layer_type.strip().lower().replace("-", "_")

    if normalized in {"prec", "precipitation", "flood", "flood_risk"}:
        return "prec"
    if normalized in {"tmin", "minimum_temperature"}:
        return "tmin"
    if normalized in {"humidity", "relative_humidity", "hurs"}:
        return "humidity"
    if normalized in {"wind", "wind_speed", "sfcwind"}:
        return "wind_speed"
    if normalized in {"solar", "solar_radiation", "rsds"}:
        return "solar_radiation"
    if normalized in {"longwave", "longwave_radiation", "rlds"}:
        return "longwave_radiation"

    return "tmax"


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
