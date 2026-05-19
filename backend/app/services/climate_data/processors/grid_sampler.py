from math import cos, radians, sqrt
from typing import Any


def nearest_grid_cell(
    dataset: dict[str, Any],
    latitude: float,
    longitude: float,
) -> dict[str, Any] | None:
    cells = dataset.get("cells")

    if not isinstance(cells, list) or not cells:
        return None

    return min(
        cells,
        key=lambda cell: distance_score(
            latitude,
            longitude,
            float(cell["lat"]),
            float(cell["lon"]),
        ),
    )


def distance_score(
    latitude: float,
    longitude: float,
    cell_latitude: float,
    cell_longitude: float,
) -> float:
    latitude_scale = cos(radians((latitude + cell_latitude) / 2))
    d_lat = latitude - cell_latitude
    d_lon = (longitude - cell_longitude) * latitude_scale

    return sqrt(d_lat * d_lat + d_lon * d_lon)
