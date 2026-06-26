from app.models.schemas import ClimateRasterSample
from app.services.climate_data.climate_raster_service import (
    sample_worldclim_future,
)
from app.services.climate_data.providers.base import ClimateDataRequest


class LocalWorldClimProvider:
    name = "local_worldclim"

    def sample(
        self,
        request: ClimateDataRequest,
    ) -> ClimateRasterSample | None:
        return sample_worldclim_future(
            latitude=request.latitude,
            longitude=request.longitude,
            year=request.year,
            scenario=request.scenario,
            variable=request.variable,
            month=request.month,
            model=request.model,
            resolution=request.resolution,
        )
