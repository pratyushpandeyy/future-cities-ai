from app.models.schemas import ClimateRasterSample
from app.services.climate_data.loaders.json_grid_loader import load_demo_grid
from app.services.climate_data.loaders.worldclim_locator import (
    find_worldclim_file,
)
from app.services.climate_data.processors.geotiff_sampler import (
    sample_geotiff_point,
)
from app.services.climate_data.processors.grid_sampler import nearest_grid_cell


def sample_climate_raster(
    latitude: float,
    longitude: float,
    layer_type: str = "heat_stress",
    *,
    year: int | None = None,
    scenario: str = "ssp245",
    month: int = 7,
    model: str | None = None,
    resolution: str = "2.5m",
    prefer_worldclim: bool = False,
) -> ClimateRasterSample | None:
    normalized_layer = normalize_layer_type(layer_type)

    if prefer_worldclim and year is not None:
        worldclim_sample = sample_worldclim_future(
            latitude=latitude,
            longitude=longitude,
            year=year,
            scenario=scenario,
            month=month,
            model=model,
            resolution=resolution,
            variable=worldclim_variable(normalized_layer),
        )

        if worldclim_sample:
            return worldclim_sample

    return sample_demo_grid(latitude, longitude, normalized_layer)


def sample_worldclim_future(
    *,
    latitude: float,
    longitude: float,
    year: int,
    scenario: str = "ssp245",
    variable: str = "tmax",
    month: int = 7,
    model: str | None = None,
    resolution: str = "2.5m",
) -> ClimateRasterSample | None:
    if not 1 <= month <= 12:
        raise ValueError("WorldClim month must be between 1 and 12")

    located = find_worldclim_file(
        year=year,
        scenario=scenario,
        variable=variable,
        model=model,
        resolution=resolution,
    )

    if not located:
        return None

    path, resolved_model, period = located
    point = sample_geotiff_point(
        path,
        latitude=latitude,
        longitude=longitude,
        band=month,
    )

    if not point:
        return None

    value, unit = normalize_worldclim_value(point.value, variable)

    return ClimateRasterSample(
        sampled_value=round(value, 3),
        grid_cell_id=(
            f"worldclim:{resolution}:{resolved_model}:{scenario}:{period}:"
            f"{variable}:m{month}:r{point.row}:c{point.column}"
        ),
        raster_source="worldclim_cmip6_geotiff",
        dataset_name="WorldClim v2.1 CMIP6 future climate",
        dataset_resolution=resolution,
        layer_type=variable,
        unit=unit,
        variable=variable,
        model=resolved_model,
        scenario=scenario,
        period=period,
        month=month,
        source_path=str(path),
        is_fallback=False,
    )


def sample_demo_grid(
    latitude: float,
    longitude: float,
    normalized_layer: str,
) -> ClimateRasterSample | None:
    dataset = load_demo_grid(normalized_layer)

    if not dataset:
        return None

    cell = nearest_grid_cell(dataset, latitude, longitude)

    if not cell:
        return None

    return ClimateRasterSample(
        sampled_value=round(float(cell["value"]), 3),
        grid_cell_id=str(cell["id"]),
        raster_source=str(dataset["raster_source"]),
        dataset_name=str(dataset["dataset_name"]),
        dataset_resolution=str(dataset["dataset_resolution"]),
        layer_type=normalized_layer,
        unit="normalized_0_1",
        variable=normalized_layer,
        is_fallback=True,
    )


def normalize_layer_type(layer_type: str) -> str:
    normalized = layer_type.strip().lower().replace(" ", "_").replace("-", "_")

    if normalized in {"heat", "heat_risk", "temperature", "temperature_anomaly"}:
        return "heat_stress"

    return normalized or "heat_stress"


def worldclim_variable(layer_type: str) -> str:
    if layer_type in {"prec", "precipitation", "flood", "flood_risk"}:
        return "prec"
    if layer_type in {"tmin", "minimum_temperature"}:
        return "tmin"

    return "tmax"


def normalize_worldclim_value(value: float, variable: str) -> tuple[float, str]:
    if variable in {"tmin", "tmax"}:
        # WorldClim temperature rasters may be encoded in tenths of a degree.
        normalized = value / 10 if abs(value) > 100 else value
        return normalized, "degC"

    if variable == "prec":
        return value, "mm_per_month"

    return value, "unknown"
