from app.models.schemas import ClimateRasterSample
from app.services.climate_data.loaders.json_grid_loader import load_demo_grid
from app.services.climate_data.processors.grid_sampler import nearest_grid_cell


def sample_climate_raster(
    latitude: float,
    longitude: float,
    layer_type: str = "heat_stress",
) -> ClimateRasterSample | None:
    normalized_layer = normalize_layer_type(layer_type)
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
    )


def normalize_layer_type(layer_type: str) -> str:
    normalized = layer_type.strip().lower().replace(" ", "_").replace("-", "_")

    if normalized in {"heat", "heat_risk", "temperature", "temperature_anomaly"}:
        return "heat_stress"

    return normalized or "heat_stress"
