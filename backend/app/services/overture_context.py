import os

from app.models.schemas import OvertureUrbanContext


DEFAULT_RADIUS_DEGREES = 0.01


def get_overture_urban_context(
    *,
    latitude: float,
    longitude: float,
    radius_degrees: float = DEFAULT_RADIUS_DEGREES,
) -> OvertureUrbanContext:
    if not overture_enabled():
        return unavailable_context(
            latitude,
            longitude,
            "Overture access is disabled. Set OVERTURE_ENABLED=true.",
        )

    try:
        from overturemaps import record_batch_reader
    except ImportError:
        return unavailable_context(
            latitude,
            longitude,
            "Install the overturemaps package to query buildings and POIs.",
        )

    bbox = (
        longitude - radius_degrees,
        latitude - radius_degrees,
        longitude + radius_degrees,
        latitude + radius_degrees,
    )

    try:
        building_count = read_count(record_batch_reader, "building", bbox)
        place_count = read_count(record_batch_reader, "place", bbox)
    except Exception as exc:
        return unavailable_context(
            latitude,
            longitude,
            f"Overture query failed: {exc}",
            bbox=bbox,
        )

    area_km2 = approximate_bbox_area_km2(
        latitude,
        radius_degrees,
    )

    return OvertureUrbanContext(
        latitude=latitude,
        longitude=longitude,
        bbox=list(bbox),
        building_count=building_count,
        place_count=place_count,
        building_density_per_km2=round(building_count / area_km2, 3),
        place_density_per_km2=round(place_count / area_km2, 3),
        provider="overture_maps",
        available=True,
        note="Queried remotely from Overture cloud-hosted GeoParquet.",
    )


def read_count(record_batch_reader, theme_type: str, bbox: tuple[float, ...]) -> int:
    reader = record_batch_reader(
        theme_type,
        bbox=bbox,
        connect_timeout=10,
        request_timeout=30,
        stac=True,
    )
    return reader.read_all().num_rows if reader is not None else 0


def overture_enabled() -> bool:
    return os.getenv("OVERTURE_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
    }


def approximate_bbox_area_km2(
    latitude: float,
    radius_degrees: float,
) -> float:
    north_south_km = radius_degrees * 2 * 111.32
    east_west_km = (
        radius_degrees
        * 2
        * 111.32
        * max(0.1, abs(math_cos_degrees(latitude)))
    )
    return max(0.01, north_south_km * east_west_km)


def math_cos_degrees(value: float) -> float:
    from math import cos, radians

    return cos(radians(value))


def unavailable_context(
    latitude: float,
    longitude: float,
    note: str,
    *,
    bbox: tuple[float, ...] | None = None,
) -> OvertureUrbanContext:
    return OvertureUrbanContext(
        latitude=latitude,
        longitude=longitude,
        bbox=list(bbox) if bbox else [],
        building_count=0,
        place_count=0,
        building_density_per_km2=0,
        place_density_per_km2=0,
        provider="overture_maps",
        available=False,
        note=note,
    )
