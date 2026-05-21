from math import sin

from app.models.schemas import (
    ClimateCellDetailResponse,
    ClimateSurfaceCell,
    ClimateSurfaceResponse,
)
from app.services.climate_data.climate_raster_service import (
    normalize_layer_type,
    sample_climate_raster,
)
from app.services.climate_data.loaders.json_grid_loader import load_demo_grid


def generate_climate_surface(
    bbox: list[float],
    zoom: float,
    layer_type: str,
    warming_level: float,
    year: int,
    season: str,
) -> ClimateSurfaceResponse:
    west, south, east, north = normalize_bbox(bbox)
    normalized_layer = normalize_surface_layer(layer_type)
    columns, rows = grid_shape_for_zoom(zoom)
    lon_step = (east - west) / columns
    lat_step = (north - south) / rows
    cells: list[ClimateSurfaceCell] = []

    for row in range(rows):
        for column in range(columns):
            cell_west = west + column * lon_step
            cell_east = cell_west + lon_step
            cell_south = south + row * lat_step
            cell_north = cell_south + lat_step
            center_lon = (cell_west + cell_east) / 2
            center_lat = (cell_south + cell_north) / 2
            raster_sample = sample_climate_raster(
                latitude=center_lat,
                longitude=center_lon,
                layer_type="heat_stress",
            )
            base_value = raster_sample.sampled_value if raster_sample else 0.48
            raster_source = (
                raster_sample.raster_source if raster_sample else "formula_fallback"
            )
            confidence_level = "Medium-high" if raster_sample else "Low"
            normalized_score = surface_score(
                base_value=base_value,
                layer_type=normalized_layer,
                warming_level=warming_level,
                year=year,
                season=season,
                latitude=center_lat,
                longitude=center_lon,
                row=row,
                column=column,
            )
            base_cell_id = raster_sample.grid_cell_id if raster_sample else "FC-RAS-FALLBACK"
            polygon = [
                [round(cell_west, 5), round(cell_north, 5)],
                [round(cell_east, 5), round(cell_north, 5)],
                [round(cell_east, 5), round(cell_south, 5)],
                [round(cell_west, 5), round(cell_south, 5)],
                [round(cell_west, 5), round(cell_north, 5)],
            ]

            cells.append(
                ClimateSurfaceCell(
                    grid_cell_id=f"{base_cell_id}-{row:02d}-{column:02d}",
                    bounds=[
                        round(cell_west, 5),
                        round(cell_south, 5),
                        round(cell_east, 5),
                        round(cell_north, 5),
                    ],
                    polygon=polygon,
                    sampled_value=round(base_value, 3),
                    climate_intensity=round(normalized_score / 100, 3),
                    normalized_score=normalized_score,
                    raster_source=raster_source,
                    confidence_level=confidence_level,
                ),
            )

    return ClimateSurfaceResponse(
        layer_type=normalized_layer,
        bbox=[round(west, 5), round(south, 5), round(east, 5), round(north, 5)],
        zoom=round(zoom, 2),
        grid_resolution=f"{columns}x{rows}",
        sampled_cell_count=len(cells),
        climate_surface_source="demo_grid_sampled_surface",
        cells=cells,
        geojson=surface_geojson(cells, normalized_layer),
    )


def get_climate_cell_detail(
    grid_cell_id: str,
    layer_type: str,
    year: int,
    warming_level: float,
    season: str,
) -> ClimateCellDetailResponse:
    normalized_layer = normalize_surface_layer(layer_type)
    base_cell_id = base_grid_cell_id(grid_cell_id)
    dataset = load_demo_grid("heat_stress")
    matched_cell = None

    if dataset:
        matched_cell = next(
            (
                cell
                for cell in dataset.get("cells", [])
                if str(cell.get("id")) == base_cell_id
            ),
            None,
        )

    raw_value = float(matched_cell["value"]) if matched_cell else 0.48
    normalized_score = surface_score(
        base_value=raw_value,
        layer_type=normalized_layer,
        warming_level=warming_level,
        year=year,
        season=season,
        latitude=float(matched_cell["lat"]) if matched_cell else 0,
        longitude=float(matched_cell["lon"]) if matched_cell else 0,
        row=0,
        column=0,
    )
    confidence_level = "Medium-high" if matched_cell else "Low"
    fallback_source_used = (
        str(dataset["raster_source"])
        if matched_cell and dataset
        else "formula_fallback_no_matching_grid_cell"
    )

    return ClimateCellDetailResponse(
        grid_cell_id=grid_cell_id,
        layer_type=normalized_layer,
        year=year,
        warming_level=warming_level,
        season=season,
        raw_sampled_value=round(raw_value, 3),
        normalized_score=normalized_score,
        score_explanation=cell_score_explanation(
            layer_type=normalized_layer,
            normalized_score=normalized_score,
            raw_value=raw_value,
            warming_level=warming_level,
            year=year,
            season=season,
            matched=matched_cell is not None,
        ),
        dominant_risk_factor=dominant_cell_factor(normalized_layer, season),
        confidence_level=confidence_level,
        fallback_source_used=fallback_source_used,
    )


def normalize_bbox(bbox: list[float]) -> tuple[float, float, float, float]:
    if len(bbox) != 4:
        raise ValueError("bbox must contain west,south,east,north")

    west, south, east, north = bbox

    return (
        max(-180, min(180, west)),
        max(-90, min(90, south)),
        max(-180, min(180, east)),
        max(-90, min(90, north)),
    )


def normalize_surface_layer(layer_type: str) -> str:
    normalized = normalize_layer_type(layer_type)

    if normalized in {"heat_stress", "heat_risk"}:
        return "heat_risk"
    if normalized in {"flood", "flood_risk", "flood_exposure"}:
        return "flood_risk"
    if normalized in {"comfort", "outdoor_comfort"}:
        return "outdoor_comfort"
    if normalized in {"water", "water_stress"}:
        return "water_stress"

    return normalized


def base_grid_cell_id(grid_cell_id: str) -> str:
    parts = grid_cell_id.split("-")

    if len(parts) > 2 and parts[-1].isdigit() and parts[-2].isdigit():
        return "-".join(parts[:-2])

    return grid_cell_id


def grid_shape_for_zoom(zoom: float) -> tuple[int, int]:
    if zoom < 3:
        return 6, 4
    if zoom < 5:
        return 9, 6
    if zoom < 7:
        return 12, 8

    return 16, 10


def surface_score(
    *,
    base_value: float,
    layer_type: str,
    warming_level: float,
    year: int,
    season: str,
    latitude: float,
    longitude: float,
    row: int,
    column: int,
) -> int:
    warming_pressure = max(0, warming_level - 1.0)
    year_pressure = max(0, year - 2025) / 25
    season_name = season.strip().lower()
    spatial_texture = (
        pseudo_noise(latitude * 0.73 + row * 1.7, longitude * 0.41 + column * 2.1)
        - 0.5
    ) * 18
    base_score = base_value * 100

    if layer_type == "flood_risk":
        season_boost = 18 if season_name == "monsoon" else -4 if season_name == "winter" else 2
        score = 28 + base_score * 0.38 + warming_pressure * 7 + year_pressure * 7 + season_boost
    elif layer_type == "outdoor_comfort":
        season_boost = 12 if season_name == "winter" else -14 if season_name == "summer" else -5
        heat_pressure = base_score * 0.52 + warming_pressure * 12 + year_pressure * 8
        score = 86 - heat_pressure + season_boost - spatial_texture * 0.3
    elif layer_type == "water_stress":
        season_boost = 12 if season_name == "summer" else -8 if season_name == "monsoon" else 0
        score = 34 + base_score * 0.48 + warming_pressure * 14 + year_pressure * 7 + season_boost
    else:
        season_boost = 16 if season_name == "summer" else -10 if season_name == "winter" else 3
        score = base_score + warming_pressure * 16 + year_pressure * 9 + season_boost + spatial_texture

    return max(0, min(100, round(score)))


def pseudo_noise(x: float, y: float) -> float:
    value = abs(sin(x * 12.9898 + y * 78.233) * 43758.5453)

    return value - int(value)


def dominant_cell_factor(layer_type: str, season: str) -> str:
    season_name = season.strip().lower()

    if layer_type == "flood_risk":
        return "monsoon amplification" if season_name == "monsoon" else "surface runoff exposure"
    if layer_type == "outdoor_comfort":
        return "heat-comfort penalty"
    if layer_type == "water_stress":
        return "warming-driven water demand"

    return "heat stress anomaly"


def cell_score_explanation(
    *,
    layer_type: str,
    normalized_score: int,
    raw_value: float,
    warming_level: float,
    year: int,
    season: str,
    matched: bool,
) -> str:
    source_phrase = (
        "sampled from the demo climate grid"
        if matched
        else "estimated with formula fallback because the grid cell was not found"
    )
    layer_phrase = layer_type.replace("_", " ")

    return (
        f"This {layer_phrase} cell is {source_phrase}. A raw grid value of "
        f"{raw_value:.3f}, +{warming_level:.1f}C warming, {year}, and "
        f"{season.lower()} season produce a normalized score of {normalized_score}."
    )


def surface_geojson(cells: list[ClimateSurfaceCell], layer_type: str) -> dict[str, object]:
    def climate_properties(score: int) -> dict[str, int]:
        if layer_type == "flood_risk":
            return {
                "heat": max(0, score - 22),
                "flood": score,
                "comfort": max(0, 100 - score),
                "livability": max(0, 100 - round(score * 0.65)),
                "water": max(0, round(score * 0.45)),
            }
        if layer_type == "outdoor_comfort":
            return {
                "heat": max(0, 100 - score),
                "flood": max(0, 68 - score),
                "comfort": score,
                "livability": max(0, round(score * 0.9)),
                "water": max(0, 82 - score),
            }
        if layer_type == "water_stress":
            return {
                "heat": max(0, score - 8),
                "flood": max(0, 58 - score),
                "comfort": max(0, 100 - score),
                "livability": max(0, 100 - round(score * 0.7)),
                "water": score,
            }

        return {
            "heat": score,
            "flood": max(0, round(score * 0.45)),
            "comfort": max(0, 100 - score),
            "livability": max(0, 100 - round(score * 0.72)),
            "water": max(0, round(score * 0.58)),
        }

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": cell.grid_cell_id,
                    "gridCellId": cell.grid_cell_id,
                    "layerType": layer_type,
                    "sampledValue": cell.sampled_value,
                    "rasterSource": cell.raster_source,
                    "confidenceLevel": cell.confidence_level,
                    "intensity": cell.normalized_score,
                    "normalizedScore": cell.normalized_score,
                    **climate_properties(cell.normalized_score),
                    "alpha": 0.52,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [cell.polygon],
                },
            }
            for cell in cells
        ],
    }
