from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import ClimateRasterSample
from app.services.climate_data.climate_raster_service import sample_climate_raster


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
