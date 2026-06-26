from sqlalchemy.exc import SQLAlchemyError

from app.db.models import Place
from app.db.session import SessionLocal, is_database_configured
from app.models.schemas import (
    LocationResult,
    SpatialResolutionResponse,
)
from app.services.boundaries import get_region_boundary
from app.services.climate_data.climate_raster_service import sample_climate_raster
from app.services.simulation import resolve_location


def resolve_spatial_context(query: str) -> SpatialResolutionResponse:
    cleaned_query = query.strip()
    location = resolve_location(cleaned_query)
    place_id, place_persisted, persistence_note = persist_place(location)
    boundary = get_region_boundary(cleaned_query, location_result=location)
    climate_sample = sample_climate_raster(
        latitude=location.latitude,
        longitude=location.longitude,
        layer_type="heat_stress",
    )
    fallback_used = (
        location.extrapolated
        or boundary.boundary_source == "simulated_fallback"
        or climate_sample is None
    )

    notes = [
        persistence_note,
        boundary.boundary_match_reason or "Boundary match reason unavailable.",
    ]

    if climate_sample:
        notes.append(
            f"Nearest demo climate cell: {climate_sample.grid_cell_id}.",
        )
    else:
        notes.append("No climate grid sample was available; formula fallback is required.")

    return SpatialResolutionResponse(
        input_query=cleaned_query,
        place_id=place_id,
        place_persisted=place_persisted,
        resolved_location=location,
        resolution_level=resolution_level_for(location),
        boundary_id=boundary.db_boundary_id,
        boundary_name=boundary.boundary_name,
        boundary_source=boundary.boundary_source,
        boundary_match_reason=boundary.boundary_match_reason,
        climate_region_type=boundary.climate_region_type,
        climate_grid_cell_id=climate_sample.grid_cell_id if climate_sample else None,
        climate_sampled_value=climate_sample.sampled_value if climate_sample else None,
        climate_sample_source=climate_sample.raster_source if climate_sample else None,
        dataset_name=climate_sample.dataset_name if climate_sample else None,
        dataset_resolution=climate_sample.dataset_resolution if climate_sample else None,
        confidence=confidence_for(location, boundary.boundary_source, climate_sample is not None),
        fallback_used=fallback_used,
        resolution_notes=notes,
    )


def persist_place(location: LocationResult) -> tuple[int | None, bool, str]:
    if not is_database_configured() or SessionLocal is None:
        return None, False, "Place was not persisted because DATABASE_URL is not configured."

    provider_key = build_provider_key(location)

    try:
        with SessionLocal() as session:
            place = (
                session.query(Place)
                .filter(Place.provider_key == provider_key)
                .one_or_none()
            )

            if place is None:
                place = Place(provider_key=provider_key)
                session.add(place)

            update_place(place, location)
            session.commit()
            session.refresh(place)

            return place.id, True, f"Place persisted with provider key {provider_key}."
    except SQLAlchemyError:
        return None, False, "Place persistence failed; spatial resolution continued without it."


def update_place(place: Place, location: LocationResult) -> None:
    place.name = location.location_name
    place.normalized_name = location.location_name.strip().lower()
    place.place_type = location.place_type or "location"
    place.latitude = location.latitude
    place.longitude = location.longitude
    place.locality = location.locality
    place.district = location.district
    place.city = location.city
    place.region = location.region
    place.country = location.country
    place.hierarchy_label = location.hierarchy_label
    place.bbox = location.bbox
    place.geocoder_provider = location.geocoder_provider or "unknown"
    place.provider_metadata = location.geocoder_metadata
    place.point_geojson = {
        "type": "Point",
        "coordinates": [location.longitude, location.latitude],
    }


def build_provider_key(location: LocationResult) -> str:
    provider = location.geocoder_provider or "unknown"
    return f"{provider}:{location.location_id}"


def resolution_level_for(location: LocationResult) -> str:
    place_type = (location.place_type or "").lower()

    if place_type in {"poi", "address"}:
        return "poi"
    if place_type in {"neighborhood", "locality", "suburb", "quarter"}:
        return "locality"
    if place_type in {"district", "borough", "county"}:
        return "district"
    if place_type in {"place", "city", "town", "village", "municipality"}:
        return "city"
    if place_type in {"region", "state", "province"}:
        return "admin_region"
    if location.extrapolated:
        return "fallback_buffer"

    return "point"


def confidence_for(
    location: LocationResult,
    boundary_source: str,
    has_climate_sample: bool,
) -> str:
    confidence_points = 0

    if not location.extrapolated:
        confidence_points += 2
    if location.geocoder_provider in {"mapbox", "nominatim"}:
        confidence_points += 1
    if boundary_source == "database":
        confidence_points += 2
    elif boundary_source == "real_geojson":
        confidence_points += 1
    if has_climate_sample:
        confidence_points += 1

    if confidence_points >= 5:
        return "high"
    if confidence_points >= 3:
        return "medium"

    return "low"
